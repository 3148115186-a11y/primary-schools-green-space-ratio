# -*- coding: utf-8 -*-
"""
海淀小学绿地覆盖分析工具
========================================
功能：调用通义千问视觉语言模型（Qwen-VL），批量分析 GeoScene Pro 导出的
      小学及周边100m缓冲区卫星截图，输出结构化JSON分析报告。

分析维度：
  1. 学校内部（绿线内）绿地率估算
  2. 学校+周边100m（红线内）绿地率估算
  3. 学校外围（红线内、绿线外）绿地率
  4. 总体绿地情况描述及评价
  5. 周边环境识别
  6. 绿地评分（依据 GB/T 51356-2019 + GB 50099-2011）
  7. 学校位置（街道级别，模型无法联网时留空）
  8. 备注

运行方式：在 PowerShell / CMD 中直接运行
  python 分析小学绿地覆盖.py

配置说明：
  1. 设置环境变量 DASHSCOPE_API_KEY，或在脚本 CONFIG 区块中直接填写
  2. 调整 CONCURRENT_WORKERS、RETRY_TIMES 等参数

输出：
  - 主结果文件：OUTPUT_JSON（默认 绿地分析结果.json）
  - 每处理完一批即写盘，支持断点续传
  - 控制台实时显示进度

依赖：dashscope >= 1.14  （pip install dashscope）
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
    # ------ 路径 ------
    "IMAGE_FOLDER": os.environ.get("IMAGE_FOLDER", "./导出截图"),
    "OUTPUT_JSON":  os.environ.get("OUTPUT_JSON", "./绿地分析结果.json"),

    # ------ API ------
    # 优先读环境变量 DASHSCOPE_API_KEY；若未配置，可直接在此填写，例如：
    #   "API_KEY": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    # 或在 PowerShell 中运行前先执行：$env:DASHSCOPE_API_KEY='sk-xxx'
    # 或在 CMD 中运行前先执行：   set DASHSCOPE_API_KEY=sk-xxx
    "API_KEY": os.environ.get("DASHSCOPE_API_KEY", ""),  # 请设置环境变量 DASHSCOPE_API_KEY

    # 使用的模型（推荐 qwen-vl-max-latest 精度最高；qwen-vl-plus 速度较快）
    # 可选：qwen-vl-max-latest / qwen-vl-max / qwen-vl-plus / qwen2-vl-72b-instruct
    "MODEL": "qwen-vl-max-latest",

    # ------ 并发 & 重试 ------
    # 注意：视觉模型 QPS 限制通常为 5，并发不要太高
    "CONCURRENT_WORKERS": 3,
    "RETRY_TIMES": 3,
    "RETRY_DELAY": 10,          # 重试间隔（秒）
    "REQUEST_TIMEOUT": 120,     # 单次请求超时（秒）
    "REQUEST_INTERVAL": 1.0,    # 每次请求后的最小间隔（秒），防止触发 QPS 限制

    # ------ 断点续传 ------
    "SKIP_EXISTING": True,      # True=跳过已有结果；False=强制重新分析

    # ------ 图片格式 ------
    "IMG_EXTENSIONS": [".png", ".jpg", ".jpeg", ".tiff", ".tif"],

    # ------ 日志 ------
    "LOG_FILE": os.environ.get("LOG_FILE", "./绿地分析.log"),
}

# ============================================================
#  Prompt 模板
# ============================================================

SYSTEM_PROMPT = """你是一位专业的城市绿地景观分析师，熟悉《绿色校园评价标准》（GB/T 51356-2019）和
《中小学校设计规范》（GB 50099-2011）。你将基于卫星遥感图像，对北京市海淀区的小学绿地覆盖情况
进行定量估算和定性评价。

图像说明：
- 图像中心为目标小学（当图中出现两所学校时，分析更靠近图像中心的那所）
- 绿色线框出的是学校用地边界（内边界）
- 红色线框出的是学校外扩100m的缓冲区边界（外边界）
- 若图中有两所学校，请正确识别属于中心学校的那圈红线（距离中心绿线约等距的那圈）

分析要求：
- 绿地率 = 绿地覆盖面积 / 对应区域总面积 × 100%，给出整数百分比估算
- 绿地包括：草地、树木/林地、花坛、绿化带、运动场草皮等，不包括硬质铺装、建筑屋顶
- 如无法准确判断，给出估算区间（如 "25%-35%"）
- 依据国家标准对学校绿地进行评分（满分10分）
- 输出必须是合法 JSON，不含 markdown 代码块，不含注释

输出格式（严格遵守）：
{
  "school_name": "学校名称（从图中标注或文件名推断）",
  "image_file": "图片文件名",
  "analysis_time": "分析时间",
  "green_rate_inside": "XX%（或区间 XX%-XX%）",
  "green_rate_total": "XX%（或区间）",
  "green_rate_outside": "XX%（或区间）",
  "overall_description": "综合描述，含绿地总体评价、绿地布局特征、显著特征等（100-200字）",
  "overall_score": 数字（1-10的整数，综合绿地质量评分）,
  "surroundings": "周边环境描述，含各方位的土地利用/建筑情况（100-200字）",
  "standard_score": 数字（依据GB/T 51356-2019和GB 50099-2011打分，满分10分的整数）,
  "standard_score_reason": "打分依据说明",
  "location": "学校所在街道/地区（如模型无法判断请填 '待查'）",
  "notes": "其他备注（如识别困难、图像质量、特殊情况等，无则填空字符串）"
}"""

USER_PROMPT_TEMPLATE = """请分析这张北京海淀区小学卫星截图。
图片对应的学校名称（文件名）：{school_name}

请严格按照系统提示中的 JSON 格式输出分析结果，不要输出任何 JSON 之外的内容。"""


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
    """将图片编码为 base64 字符串"""
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
    """
    调用 Qwen VL 模型分析单张图片，返回解析后的 dict。
    使用 base64 编码传图（DashScope 不支持 file:// URI）。
    异常时 raise，由调用方重试。
    """
    from dashscope import MultiModalConversation
    import dashscope

    dashscope.api_key = api_key

    # 读取图片并转为 base64 data URI
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

    # 提取 JSON（模型可能在 ```json ... ``` 中输出）
    json_text = raw_text.strip()
    if "```" in json_text:
        # 提取代码块内容
        start = json_text.find("{")
        end = json_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_text = json_text[start:end]
    elif json_text.startswith("{"):
        pass
    else:
        # 尝试从文本中找到 JSON 对象
        start = json_text.find("{")
        end = json_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_text = json_text[start:end]

    result = json.loads(json_text)

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
    """带重试逻辑的单图分析"""
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
            # 限流错误等待更长时间
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

    # 所有重试均失败
    return {
        "school_name": school_name,
        "image_file": Path(image_path).name,
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error": str(last_error),
        "status": "failed",
        "green_rate_inside": "N/A",
        "green_rate_total": "N/A",
        "green_rate_outside": "N/A",
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
    """线程安全的结果存储，支持断点续传"""

    def __init__(self, output_path: str, skip_existing: bool = True, logger=None):
        self.output_path = output_path
        self.skip_existing = skip_existing
        self.logger = logger
        self._lock = Lock()
        self.results = {}  # image_file -> result

        # 加载已有结果
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
        # 如果之前失败了，重新分析
        if item.get("status") == "failed" or item.get("error"):
            return False
        return True

    def add(self, result: dict):
        with self._lock:
            self.results[result["image_file"]] = result
            self._save()

    def _save(self):
        """写盘（已持有锁）"""
        output = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
    """收集所有待分析的图片路径"""
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
    logger.info("  海淀小学绿地覆盖分析 - 千问视觉版")
    logger.info("=" * 60)

    # 收集图片
    images = collect_images(config["IMAGE_FOLDER"], config["IMG_EXTENSIONS"])
    logger.info(f"发现图片总数: {len(images)}")

    if not images:
        logger.error(f"未在 {config['IMAGE_FOLDER']} 找到任何图片！")
        return

    # 初始化结果存储
    store = ResultStore(config["OUTPUT_JSON"], config["SKIP_EXISTING"], logger)

    # 筛选待处理
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

    # 统计
    done_count = skipped
    fail_count = 0
    total = len(images)
    count_lock = Lock()

    def process_one(img_path):
        nonlocal done_count, fail_count
        school_name = img_path.stem  # 去掉扩展名作为学校名

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
            logger.info(
                f"[{done_count}/{total}] {status_icon} {school_name[:30]:<30} "
                f"内:{result.get('green_rate_inside','N/A'):>8} "
                f"总:{result.get('green_rate_total','N/A'):>8} "
                f"得分:{result.get('standard_score','N/A')} "
                f"| 进度 {progress:.1f}%"
            )
        return result

    start_time = time.time()

    if config["CONCURRENT_WORKERS"] == 1:
        # 单线程，便于调试
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
    logger.info("=" * 60)

    if failed:
        logger.warning("失败的学校列表：")
        for r in failed:
            logger.warning(f"  - {r.get('school_name', r.get('image_file'))} | {r.get('error','')[:80]}")


# ============================================================
#  入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="海淀小学绿地覆盖分析（千问视觉版）")
    parser.add_argument("--api-key", default="", help="DashScope API Key（优先级高于环境变量）")
    parser.add_argument("--model", default="", help="模型名称，如 qwen-vl-max-latest")
    parser.add_argument("--workers", type=int, default=0, help="并发线程数（0=使用配置值）")
    parser.add_argument("--image-folder", default="", help="图片文件夹路径")
    parser.add_argument("--output", default="", help="输出 JSON 路径")
    parser.add_argument("--no-skip", action="store_true", help="强制重新分析所有图片（忽略已有结果）")
    parser.add_argument("--test", type=int, default=0,
                        help="测试模式：只分析前N张图片（0=全量）")
    args = parser.parse_args()

    # 合并配置
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

    # 确定 API Key
    api_key = args.api_key or config["API_KEY"]
    if not api_key:
        print("=" * 60)
        print("  ❌ 未找到 DASHSCOPE_API_KEY！")
        print("")
        print("  请通过以下任一方式提供 API Key：")
        print("  1. 设置环境变量：")
        print("       Windows CMD:  set DASHSCOPE_API_KEY=sk-xxxxxxx")
        print("       PowerShell:   $env:DASHSCOPE_API_KEY='sk-xxxxxxx'")
        print("       bash/zsh:     export DASHSCOPE_API_KEY=sk-xxxxxxx")
        print("  2. 在脚本 CONFIG 区块中直接填写：")
        print("       \"API_KEY\": \"sk-xxxxxxx\"")
        print("  3. 命令行参数：")
        print("       python 分析小学绿地覆盖.py --api-key sk-xxxxxxx")
        print("=" * 60)
        return

    # 测试模式：限制图片数量
    if args.test > 0:
        print(f"[测试模式] 仅分析前 {args.test} 张图片")
        images = collect_images(config["IMAGE_FOLDER"], config["IMG_EXTENSIONS"])
        test_images = images[:args.test]
        import tempfile, shutil
        tmp_folder = os.path.join(tempfile.gettempdir(), "qwen_vl_test")
        os.makedirs(tmp_folder, exist_ok=True)
        for img in test_images:
            shutil.copy(str(img), os.path.join(tmp_folder, img.name))
        config["IMAGE_FOLDER"] = tmp_folder
        config["OUTPUT_JSON"] = os.path.join(
            os.path.dirname(config["OUTPUT_JSON"]), "绿地分析结果_测试.json"
        )
        print(f"测试图片临时目录: {tmp_folder}")
        print(f"测试输出: {config['OUTPUT_JSON']}")

    run_analysis(config, api_key)


if __name__ == "__main__":
    main()
