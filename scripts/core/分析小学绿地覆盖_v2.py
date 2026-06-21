# -*- coding: utf-8 -*-
"""
海淀小学绿地覆盖精确分析工具 v2
========================================
改进点：
  - 使用 qwen3-vl-plus 模型
  - 全新提示词，要求绿地率精确到1%（如27%、33%，而非25%、35%）
  - 强制模型按步骤分析，避免整5%偏好
  - 输出JSON中绿地率为纯数字（不带%），便于后续统计

运行方式：
  python "E:/学习资料/景观规划/海淀小学绿地/分析小学绿地覆盖_v2.py"
  python "E:/学习资料/景观规划/海淀小学绿地/分析小学绿地覆盖_v2.py" --test 3
  python "E:/学习资料/景观规划/海淀小学绿地/分析小学绿地覆盖_v2.py" --no-skip
"""

import os
import json
import time
import base64
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ============================================================
#  ⚙️ 用户配置区
# ============================================================

CONFIG = {
    "IMAGE_FOLDER": os.environ.get("IMAGE_FOLDER", "./导出截图"),
    "OUTPUT_JSON":  os.environ.get("OUTPUT_JSON", "./绿地分析结果_v2.json"),

    "API_KEY": os.environ.get("DASHSCOPE_API_KEY", ""),  # 请设置环境变量 DASHSCOPE_API_KEY

    # qwen3-vl-plus：通义千问最新视觉模型，精度更高
    "MODEL": "qwen3-vl-plus",

    "CONCURRENT_WORKERS": 2,
    "RETRY_TIMES": 5,
    "RETRY_DELAY": 15,
    "REQUEST_TIMEOUT": 120,
    "REQUEST_INTERVAL": 1.0,

    "SKIP_EXISTING": True,

    "IMG_EXTENSIONS": [".png", ".jpg", ".jpeg", ".tiff", ".tif"],

    "LOG_FILE": os.environ.get("LOG_FILE", "./绿地分析_v2.log"),
}

# ============================================================
#  Prompt 模板 v2 —— 精确到1%的绿地率分析
# ============================================================

SYSTEM_PROMPT = """你是一位严谨的城市绿地定量分析师，你需要对卫星截图进行精确的绿地覆盖面积估算。

【图像说明】
- 图像中心为目标小学（当图中出现两所学校时，分析更靠近图像中心的那所）
- 绿色线框出的是学校用地边界（内边界，简称"绿线"）
- 红色线框出的是学校外扩100m的缓冲区边界（外边界，简称"红线"）
- 若图中有两所学校，请正确识别属于中心学校的那圈红线

【绿地定义】
绿地包括：草地、树木/林地、花坛、绿化带、运动场草皮、菜地、农田等有植被覆盖的区域。
不包括：硬质铺装、建筑屋顶、水泥/沥青地面、水体、裸土。

【核心方法论——区域分解估算法】
你必须把每个分析区域划分为8-12个子区块，分别判断每块中绿地占比，再按面积加权求和。
这是唯一能保证精度到1%的方法。不要凭整体印象给数字！

具体步骤（必须严格执行，并在reasoning字段中呈现）：

第一步：识别绿线和红线
- 定位中心学校的绿线边界和红线边界

第二步：将校内区域（绿线内）划分为8-12个子区块
- 按照自然边界划分（如：操场区、教学楼A区、教学楼B区、校门区、绿化带区等）
- 对每个子区块，估算：①该区块占校内总面积的比例 ②该区块内绿地占该区块面积的比例

第三步：加权计算校内绿地率
- 校内绿地率 = Σ(子区块面积占比 × 子区块绿地占比)
- 例：操场占校内30%，操场绿地占60%；教学楼区占校内25%，绿地占10%……加权求和

第四步：同样方法估算外围区域（红线内绿线外）绿地率

第五步：计算总绿地率

【关键要求】
1. 绿地率必须精确到个位数（1%精度），如27%、33%、18%、42%
2. 严禁整体印象式估算！你必须先逐区块分析，再汇总
3. 不同学校的绿地率值应该不同——如果两所学校绿地率相同，说明你没有认真分析
4. 绿地率字段输出纯整数（不带%号）

【评分标准】
依据《绿色校园评价标准》（GB/T 51356-2019）和《中小学校设计规范》（GB 50099-2011）：
- 新区绿地率≥35% → 满分10分
- 改建项目绿地率≥30% → 满分10分
- 绿地率每降低5%，扣1分
- 设置集中绿地（宽度≥8m）可酌情加分
- 满分10分，最低1分，必须是整数

【输出格式——严格遵守】
输出纯JSON，不含markdown代码块，不含注释，格式如下：
{
  "school_name": "学校名称",
  "image_file": "图片文件名",
  "analysis_time": "分析时间",
  "green_rate_inside": 数字（1-100的整数，校内绿地率）,
  "green_rate_total": 数字（1-100的整数，红线内总绿地率）,
  "green_rate_outside": 数字（1-100的整数，外围绿地率）,
  "reasoning": "逐区块分析过程：1.操场区(占校内X%)内绿地约Y%；2.教学楼区(占校内X%)内绿地约Y%；...加权求和得校内绿地率Z%",
  "overall_description": "综合描述（100-200字）：绿地布局特征、绿地类型构成、显著特征",
  "overall_score": 数字（1-10整数，综合绿地质量评分）,
  "surroundings": "周边环境描述（100-200字）：各方位的土地利用/建筑/自然景观",
  "standard_score": 数字（1-10整数，依据国标打分）,
  "standard_score_reason": "打分依据",
  "location": "学校所在街道/地区",
  "notes": "备注（无则填空字符串）"
}"""

USER_PROMPT_TEMPLATE = """请分析这张北京海淀区小学卫星截图。
学校名称（文件名）：{school_name}

重要提醒：
1. 必须使用"区域分解估算法"——先划分8-12个子区块，逐块估算绿地占比，再加权求和
2. 不要凭整体印象直接给数字！先在reasoning字段中写出逐区块分析过程
3. 绿地率精确到1%（个位数），不同学校应该有不同的绿地率值

输出纯JSON，不要输出任何JSON之外的内容。"""


# ============================================================
#  日志配置
# ============================================================

def setup_logging(log_file: str):
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )
    return logging.getLogger(__name__)


# ============================================================
#  图片工具
# ============================================================

def load_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


def get_image_mime(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return mime_map.get(ext, "image/png")


# ============================================================
#  Qwen VL 调用核心
# ============================================================

def call_qwen_vl(image_path: str, school_name: str, api_key: str, model: str,
                 timeout: int = 120, logger=None) -> dict:
    from dashscope import MultiModalConversation
    import dashscope

    dashscope.api_key = api_key

    mime = get_image_mime(image_path)
    b64_data = load_image_base64(image_path)
    image_data_uri = f"data:{mime};base64,{b64_data}"

    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": SYSTEM_PROMPT}]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image_data_uri,
                },
                {
                    "type": "text",
                    "text": USER_PROMPT_TEMPLATE.format(school_name=school_name)
                }
            ]
        }
    ]

    response = MultiModalConversation.call(
        model=model,
        messages=messages,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"API 错误 {response.status_code}: {response.message}"
        )

    raw_text = response.output.choices[0].message.content[0]["text"]

    # 提取 JSON
    json_text = raw_text.strip()
    if "```" in json_text:
        start = json_text.find("{")
        end = json_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_text = json_text[start:end]
    elif json_text.startswith("{"):
        pass
    else:
        start = json_text.find("{")
        end = json_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_text = json_text[start:end]

    result = json.loads(json_text)

    # 确保绿地率字段为整数
    for key in ["green_rate_inside", "green_rate_total", "green_rate_outside",
                "overall_score", "standard_score"]:
        if key in result:
            val = result[key]
            if isinstance(val, str):
                # 去掉%号和空格
                val = val.replace("%", "").replace("％", "").strip()
                # 处理区间如 "25-30"，取中值
                if "-" in val and not val.startswith("-"):
                    parts = val.split("-")
                    try:
                        val = round((float(parts[0]) + float(parts[1])) / 2)
                    except:
                        val = int(float(parts[0]))
                try:
                    val = int(float(val))
                except:
                    val = None
            elif isinstance(val, (int, float)):
                val = int(val)
            result[key] = val

    # 补充元信息
    result["image_file"] = Path(image_path).name
    result["analysis_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "school_name" not in result or not result["school_name"]:
        result["school_name"] = school_name

    return result


# ============================================================
#  带重试的封装
# ============================================================

def analyze_image_with_retry(
        image_path: str,
        school_name: str,
        api_key: str,
        model: str,
        retry_times: int = 3,
        retry_delay: int = 10,
        request_interval: float = 1.0,
        timeout: int = 120,
        logger=None
) -> dict:
    last_error = None
    for attempt in range(1, retry_times + 1):
        try:
            result = call_qwen_vl(image_path, school_name, api_key, model, timeout, logger)
            time.sleep(request_interval)
            return result
        except json.JSONDecodeError as e:
            last_error = e
            if logger:
                logger.warning(f"  [{school_name}] JSON解析失败（尝试{attempt}/{retry_times}）: {e}")
            if attempt < retry_times:
                time.sleep(retry_delay)
        except RuntimeError as e:
            last_error = e
            err_str = str(e)
            if logger:
                logger.warning(f"  [{school_name}] API错误（尝试{attempt}/{retry_times}）: {e}")
            if "429" in err_str or "throttl" in err_str.lower() or "rate" in err_str.lower():
                wait = retry_delay * attempt * 2
                if logger:
                    logger.info(f"  触发限流，等待 {wait} 秒...")
                time.sleep(wait)
            elif attempt < retry_times:
                time.sleep(retry_delay)
        except Exception as e:
            last_error = e
            if logger:
                logger.warning(f"  [{school_name}] 未知错误（尝试{attempt}/{retry_times}）: {e}")
                logger.debug(traceback.format_exc())
            if attempt < retry_times:
                time.sleep(retry_delay)

    return {
        "school_name": school_name,
        "image_file": Path(image_path).name,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error": str(last_error),
        "status": "failed",
        "green_rate_inside": None,
        "green_rate_total": None,
        "green_rate_outside": None,
        "overall_description": "",
        "overall_score": None,
        "surroundings": "",
        "standard_score": None,
        "standard_score_reason": "",
        "location": "待查",
        "notes": f"分析失败: {last_error}"
    }


# ============================================================
#  结果持久化（线程安全）
# ============================================================

class ResultStore:
    def __init__(self, output_path: str, skip_existing: bool = True, logger=None):
        self.output_path = output_path
        self.skip_existing = skip_existing
        self.logger = logger
        self._lock = Lock()
        self.results = {}

        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if isinstance(existing, list):
                    for item in existing:
                        if "image_file" in item:
                            self.results[item["image_file"]] = item
                elif isinstance(existing, dict) and "results" in existing:
                    for item in existing["results"]:
                        if "image_file" in item:
                            self.results[item["image_file"]] = item
                if logger:
                    logger.info(f"断点续传：已加载 {len(self.results)} 条已有结果")
            except Exception as e:
                if logger:
                    logger.warning(f"加载已有结果失败: {e}")

    def is_done(self, image_file: str) -> bool:
        if not self.skip_existing:
            return False
        item = self.results.get(image_file)
        if item is None:
            return False
        if item.get("status") == "failed" or item.get("error"):
            return False
        return True

    def add(self, result: dict):
        with self._lock:
            self.results[result["image_file"]] = result
            self._save()

    def _save(self):
        output = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": "qwen3-vl-plus",
            "version": "v2-precision1pct",
            "total_count": len(self.results),
            "results": sorted(self.results.values(), key=lambda x: x.get("school_name", ""))
        }
        tmp_path = self.output_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.output_path)

    def save_final(self):
        with self._lock:
            self._save()

    def all_results(self):
        with self._lock:
            return list(self.results.values())


# ============================================================
#  主流程
# ============================================================

def collect_images(image_folder: str, extensions: list) -> list:
    folder = Path(image_folder)
    images = []
    for ext in extensions:
        images.extend(folder.glob(f"*{ext}"))
        images.extend(folder.glob(f"*{ext.upper()}"))
    images = sorted(set(images))
    return images


def run_analysis(config: dict, api_key: str):
    logger = setup_logging(config["LOG_FILE"])
    logger.info("=" * 60)
    logger.info("  海淀小学绿地覆盖精确分析 v2（qwen3-vl-plus）")
    logger.info("=" * 60)

    images = collect_images(config["IMAGE_FOLDER"], config["IMG_EXTENSIONS"])
    logger.info(f"发现图片总数: {len(images)}")

    if not images:
        logger.error(f"未在 {config['IMAGE_FOLDER']} 找到任何图片！")
        return

    store = ResultStore(config["OUTPUT_JSON"], config["SKIP_EXISTING"], logger)

    pending = [img for img in images if not store.is_done(img.name)]
    skipped = len(images) - len(pending)
    logger.info(f"跳过（已有结果）: {skipped}")
    logger.info(f"待分析: {len(pending)}")
    logger.info(f"使用模型: {config['MODEL']}")
    logger.info(f"并发数: {config['CONCURRENT_WORKERS']}")
    logger.info("")

    if not pending:
        logger.info("所有图片均已分析完毕！")
        store.save_final()
        return

    done_count = skipped
    fail_count = 0
    total = len(images)
    count_lock = Lock()

    def process_one(img_path):
        nonlocal done_count, fail_count
        school_name = img_path.stem

        result = analyze_image_with_retry(
            image_path=str(img_path),
            school_name=school_name,
            api_key=api_key,
            model=config["MODEL"],
            retry_times=config["RETRY_TIMES"],
            retry_delay=config["RETRY_DELAY"],
            request_interval=config["REQUEST_INTERVAL"],
            timeout=config["REQUEST_TIMEOUT"],
            logger=logger
        )

        store.add(result)

        with count_lock:
            done_count += 1
            if result.get("status") == "failed" or result.get("error"):
                fail_count += 1
                status_icon = "✗"
            else:
                status_icon = "✓"

            progress = done_count / total * 100
            inside = result.get('green_rate_inside')
            total_rate = result.get('green_rate_total')
            outside = result.get('green_rate_outside')
            score = result.get('standard_score')
            # 安全格式化：None → 'N/A'
            def fmt(v, w=4):
                return f"{v:>{w}}" if v is not None else f"{'N/A':>{w}}"
            logger.info(
                f"[{done_count}/{total}] {status_icon} {school_name[:25]:<25} "
                f"内:{fmt(inside)}% "
                f"总:{fmt(total_rate)}% "
                f"外:{fmt(outside)}% "
                f"分:{score if score is not None else 'N/A'} "
                f"| {progress:.1f}%"
            )
        return result

    start_time = time.time()

    if config["CONCURRENT_WORKERS"] == 1:
        for img in pending:
            process_one(img)
    else:
        with ThreadPoolExecutor(max_workers=config["CONCURRENT_WORKERS"]) as executor:
            futures = {executor.submit(process_one, img): img for img in pending}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    img = futures[future]
                    logger.error(f"  线程异常 [{img.stem}]: {e}")

    store.save_final()

    elapsed = time.time() - start_time
    all_results = store.all_results()
    success = [r for r in all_results if not r.get("error") and r.get("status") != "failed"]
    failed = [r for r in all_results if r.get("error") or r.get("status") == "failed"]

    logger.info("")
    logger.info("=" * 60)
    logger.info("  分析完成！")
    logger.info(f"  总数: {total}")
    logger.info(f"  成功: {len(success)}")
    logger.info(f"  失败: {len(failed)}")
    logger.info(f"  总用时: {elapsed:.1f}s ({elapsed/60:.1f} 分钟)")
    logger.info(f"  结果文件: {config['OUTPUT_JSON']}")

    # 精度统计
    if success:
        from collections import Counter
        inside_vals = [r['green_rate_inside'] for r in success if r.get('green_rate_inside') is not None]
        total_vals = [r['green_rate_total'] for r in success if r.get('green_rate_total') is not None]

        inside_5x = sum(1 for v in inside_vals if v % 5 == 0)
        total_5x = sum(1 for v in total_vals if v % 5 == 0)

        logger.info("")
        logger.info("  ── 精度统计 ──")
        logger.info(f"  校内绿地率: 均值={sum(inside_vals)/len(inside_vals):.1f}%, 5的倍数占比={inside_5x}/{len(inside_vals)} ({inside_5x/len(inside_vals)*100:.0f}%)")
        logger.info(f"  总绿地率:   均值={sum(total_vals)/len(total_vals):.1f}%, 5的倍数占比={total_5x}/{len(total_vals)} ({total_5x/len(total_vals)*100:.0f}%)")

    logger.info("=" * 60)

    if failed:
        logger.warning("失败的学校列表：")
        for r in failed:
            logger.warning(f"  - {r.get('school_name', r.get('image_file'))} | {r.get('error','')[:80]}")


# ============================================================
#  入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="海淀小学绿地覆盖精确分析 v2（qwen3-vl-plus）")
    parser.add_argument("--api-key", default="", help="DashScope API Key")
    parser.add_argument("--model", default="", help="模型名称")
    parser.add_argument("--workers", type=int, default=0, help="并发线程数")
    parser.add_argument("--image-folder", default="", help="图片文件夹路径")
    parser.add_argument("--output", default="", help="输出 JSON 路径")
    parser.add_argument("--no-skip", action="store_true", help="强制重新分析所有图片")
    parser.add_argument("--test", type=int, default=0, help="测试模式：只分析前N张")
    args = parser.parse_args()

    config = CONFIG.copy()
    if args.model:
        config["MODEL"] = args.model
    if args.workers > 0:
        config["CONCURRENT_WORKERS"] = args.workers
    if args.image_folder:
        config["IMAGE_FOLDER"] = args.image_folder
    if args.output:
        config["OUTPUT_JSON"] = args.output
    if args.no_skip:
        config["SKIP_EXISTING"] = False

    api_key = args.api_key or config["API_KEY"]
    if not api_key:
        print("=" * 60)
        print("  ❌ 未找到 DASHSCOPE_API_KEY！")
        print("  请设置环境变量或在脚本CONFIG中填写API Key")
        print("=" * 60)
        return

    if args.test > 0:
        print(f"[测试模式] 仅分析前 {args.test} 张图片")
        images = collect_images(config["IMAGE_FOLDER"], config["IMG_EXTENSIONS"])
        test_images = images[:args.test]
        import tempfile, shutil
        tmp_folder = os.path.join(tempfile.gettempdir(), "qwen3_vl_test")
        os.makedirs(tmp_folder, exist_ok=True)
        for img in test_images:
            shutil.copy(str(img), os.path.join(tmp_folder, img.name))
        config["IMAGE_FOLDER"] = tmp_folder
        config["OUTPUT_JSON"] = os.path.join(
            os.path.dirname(config["OUTPUT_JSON"]), "绿地分析结果_v2_测试.json"
        )
        print(f"测试图片临时目录: {tmp_folder}")
        print(f"测试输出: {config['OUTPUT_JSON']}")

    run_analysis(config, api_key)


if __name__ == "__main__":
    main()
