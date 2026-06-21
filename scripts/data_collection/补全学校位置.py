# -*- coding: utf-8 -*-
"""
补全学校位置信息脚本 v2
========================================
功能：读取「绿地分析结果.json」，对每条记录的 location 字段，
      通过百度搜索查询更具体的地址（街道门牌号级别），写回 JSON。

方法：
  - 用百度搜索（urllib + 正则提取搜索结果摘要中的地址）
  - 无需 Baidu API Key，直接抓取搜索结果页面（法律允许的研究用途）

运行：
  python 补全学校位置.py
"""

import json
import re
import time
import logging
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ============================================================
#  配置
# ============================================================
INPUT_JSON  = os.environ.get("INPUT_JSON", "./绿地分析结果.json")  # 输入JSON
OUTPUT_JSON = os.environ.get("OUTPUT_JSON", "./绿地分析结果_位置补全.json")  # 输出JSON
LOG_FILE   = os.environ.get("LOG_FILE", "./位置补全.log")  # 日志文件

CONCURRENT  = 5        # 并发数（百度对我爬虫不友好，别太高）
RETRY       = 2
TIMEOUT     = 15        # 单次请求超时（秒）
REQUEST_GAP = 0.8      # 每次请求间隔（秒）

# ============================================================
#  日志
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
#  百度搜索抓取
# ============================================================

def fetch_baidu_address(school_name: str, logger=None) -> str:
    """
    用百度搜索「学校名 + 地址」，从搜索结果摘要里提取具体地址。
    返回地址字符串，查不到返回 ""。
    """
    queries = [
        f"{school_name} 地址 海淀区",
        f"{school_name} 海淀区 位置",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "close",
    }

    # 地址匹配正则（覆盖常见中文地址格式）
    addr_patterns = [
        # 北京市海淀区xx街道xx号 / 北京市海淀区xx路xx号
        r"北京市海淀区[\u4e00-\u9fa5]{1,20}?(?:街道|镇|乡|地区)?[\u4e00-\u9fa5]{1,30}?(?:路|街|大道|胡同|巷)\d{1,5}(?:号|弄|号院)?(?:-\d+)?",
        # 海淀区xx街道xx号
        r"海淀区[\u4e00-\u9fa5]{1,20}?(?:街道|镇|乡|地区)[\u4e00-\u9fa5\d]{1,30}",
        # xxxxx路xx号
        r"[\u4e00-\u9fa5]{1,20}路\d{1,5}(?:号|弄|号院)",
        # xxxxx街xx号
        r"[\u4e00-\u9fa5]{1,20}街\d{1,5}(?:号|弄)",
        # 海淀区xx镇xx村
        r"海淀区[\u4e00-\u9fa5]{1,10}(?:镇|乡)[\u4e00-\u9fa5]{1,10}村",
    ]

    for query in queries:
        try:
            url = f"https://www.baidu.com/s?wd={quote(query)}&rn=5"
            req = Request(url, headers=headers)
            with urlopen(req, timeout=TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # 从搜索结果摘要（class="c-abstract" 或 content 属性）提取
            # 百度新版页面结构：<span class="content-right_8Zs40"> 或直接嵌在 <em> 周围
            # 兜底：在整个 html 里搜索地址模式
            found = []
            for pat in addr_patterns:
                hits = re.findall(pat, html)
                for h in hits:
                    h = h.strip().strip("。，,；;")
                    if 8 <= len(h) <= 60:
                        found.append(h)

            if found:
                # 取最短的非重复结果（通常最精确）
                found = list(dict.fromkeys(found))  # 去重保序
                best = min(found, key=len)
                if logger:
                    logger.debug(f"  [{school_name}] 百度找到: {best}")
                return best

        except Exception as e:
            if logger:
                logger.debug(f"  [{school_name}] 百度抓取失败({query}): {e}")

        time.sleep(REQUEST_GAP)

    return ""


# ============================================================
#  调用高德地图 API（可选，需配置 API Key）
# ============================================================

GAODE_API_KEY = ""   # ← 在此填写高德 Web API Key（可选，留空则跳过）


def fetch_gaode_address(school_name: str, logger=None) -> str:
    """调用高德地图 Web API 地理编码，返回具体地址"""
    if not GAODE_API_KEY:
        return ""
    try:
        from urllib.parse import quote as q
        url = (
            f"https://restapi.amap.com/v3/geocode/geo?"
            f"address={q(school_name + ' 海淀区')}"
            f"&city=北京&key={GAODE_API_KEY}"
        )
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "1" and data.get("geocodes"):
            return data["geocodes"][0].get("formatted_address", "")
    except Exception as e:
        if logger:
            logger.debug(f"  [{school_name}] 高德API失败: {e}")
    return ""


# ============================================================
#  单条处理函数
# ============================================================

def process_one(item: dict, lock: Lock, logger=None) -> dict:
    """对一条记录补全 location"""
    school = item.get("school_name", "")
    current_loc = item.get("location", "").strip()

    # 已有较精确地址（含「号」或「村」或长度>15）→ 跳过
    if ("号" in current_loc or "村" in current_loc or len(current_loc) > 18):
        if logger:
            logger.info(f"↩  {school[:25]:<25} 已有精确位置，跳过: {current_loc}")
        return item

    # 1. 先试高德 API
    new_addr = fetch_gaode_address(school, logger)

    # 2. 没有再试百度搜索
    if not new_addr:
        new_addr = fetch_baidu_address(school, logger)
        time.sleep(REQUEST_GAP)

    if new_addr and new_addr != current_loc:
        item["location_original"] = current_loc
        item["location"] = new_addr
        if logger:
            logger.info(f"✓  {school[:25]:<25} {current_loc} → {new_addr}")
    else:
        if logger:
            logger.info(f"—  {school[:25]:<25} 未找到更精确位置（当前: {current_loc}）")

    return item


# ============================================================
#  主流程
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("  补全学校位置信息 - v2")
    logger.info("=" * 60)

    # 读取 JSON
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    total = len(results)
    logger.info(f"读取记录数: {total}")
    logger.info(f"并发数: {CONCURRENT}")
    logger.info("")

    lock = Lock()
    updated = []

    if CONCURRENT <= 1:
        for item in results:
            updated.append(process_one(item, lock, logger))
    else:
        with ThreadPoolExecutor(max_workers=CONCURRENT) as ex:
            futures = {ex.submit(process_one, item, lock, logger): item for item in results}
            for future in as_completed(futures):
                updated.append(future.result())

    # 按学校名排序恢复顺序
    updated.sort(key=lambda x: x.get("school_name", ""))

    # 写盘
    data["results"] = updated
    data["location_enriched_at"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 统计
    enriched = sum(1 for r in updated if r.get("location_original"))
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"  补全完成！")
    logger.info(f"  总数: {total}")
    logger.info(f"  成功补全: {enriched}")
    logger.info(f"  输出文件: {OUTPUT_JSON}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
