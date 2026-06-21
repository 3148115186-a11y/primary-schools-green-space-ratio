# -*- coding: utf-8 -*-
"""
批量绿地率计算工具
==================
读取三组QGIS导出的截图（校内/外围/完整），检测绿色像素，
计算三个绿地率指标，输出Excel表格。

使用方式：python 绿地率计算.py
"""

import os
import cv2
import numpy as np
from PIL import Image

# =============================================
#  ⚙️ 配置
# =============================================

# 三组截图文件夹路径
FOLDER_INTERNAL = os.environ.get("FOLDER_INTERNAL", "./校内_导出截图")  # 校内截图文件夹
FOLDER_EXTERNAL = os.environ.get("FOLDER_EXTERNAL", "./外围_导出截图")  # 外围截图文件夹
FOLDER_COMBINED = os.environ.get("FOLDER_COMBINED", "./完整_导出截图")  # 完整截图文件夹

# 输出Excel路径
OUTPUT_EXCEL = os.environ.get("OUTPUT_EXCEL", "./绿地率计算结果.xlsx")  # 输出Excel

# 灰色遮罩颜色 RGB(150,150,150)
GRAY_RGB = np.array([150, 150, 150])
GRAY_TOLERANCE = 15

# 绿色检测HSV参数
GREEN_LOWER = (25, 18, 8)
GREEN_UPPER = (100, 255, 220)


# =============================================
#  核心函数
# =============================================

def load_and_detect(img_path):
    """
    读取截图，返回 (绿色掩膜, 有效掩膜, 有效像素数, 绿色像素数)
    绿色掩膜: bool数组，True=绿地
    有效掩膜: bool数组，True=非灰色（有效卫星影像区域）
    """
    img_pil = Image.open(img_path)
    img = np.array(img_pil)

    # 如果是RGBA，只取RGB
    if img.shape[2] == 4:
        img = img[:, :, :3]

    # BGR for OpenCV
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # 有效掩膜 = 非灰色遮罩
    mask_valid = ~np.all(np.abs(img.astype(int) - GRAY_RGB) < GRAY_TOLERANCE, axis=2)

    # 绿色检测 (HSV)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, GREEN_LOWER, GREEN_UPPER) > 0

    valid_count = np.sum(mask_valid)
    green_count = np.sum(mask_green & mask_valid)

    return mask_green, mask_valid, valid_count, green_count


def calc_ratio(green_count, valid_count):
    """计算绿地率，返回百分比字符串"""
    if valid_count == 0:
        return "N/A"
    ratio = green_count / valid_count * 100
    return f"{ratio:.1f}%"


# =============================================
#  主程序
# =============================================

def main():
    print("=" * 60)
    print("  批量绿地率计算")
    print("=" * 60)

    # ---------- 1. 读取文件列表 ----------
    internal_files = {os.path.splitext(f)[0]: f for f in os.listdir(FOLDER_INTERNAL) if f.endswith('.png')}
    external_files = {os.path.splitext(f)[0]: f for f in os.listdir(FOLDER_EXTERNAL) if f.endswith('.png')}
    combined_files = {os.path.splitext(f)[0]: f for f in os.listdir(FOLDER_COMBINED) if f.endswith('.png')}

    # 以完整截图的文件名为基准
    all_schools = sorted(combined_files.keys())
    print(f"校内截图: {len(internal_files)}张")
    print(f"外围截图: {len(external_files)}张")
    print(f"完整截图: {len(combined_files)}张")
    print(f"学校总数: {len(all_schools)}")

    # ---------- 2. 逐校计算 ----------
    results = []
    error_count = 0

    print("-" * 60)
    print("开始计算...\n")

    for i, school_name in enumerate(all_schools, 1):
        row = {"学校名称": school_name}

        # --- 完整（总体）绿地率 ---
        if school_name in combined_files:
            try:
                path = os.path.join(FOLDER_COMBINED, combined_files[school_name])
                _, _, valid, green = load_and_detect(path)
                row["总绿地率"] = calc_ratio(green, valid)
                row["总有效像素"] = int(valid)
                row["总绿色像素"] = int(green)
            except Exception as e:
                row["总绿地率"] = f"错误: {e}"
                error_count += 1
        else:
            row["总绿地率"] = "无截图"

        # --- 校内绿地率 ---
        if school_name in internal_files:
            try:
                path = os.path.join(FOLDER_INTERNAL, internal_files[school_name])
                _, _, valid, green = load_and_detect(path)
                row["校内绿地率"] = calc_ratio(green, valid)
                row["校内有效像素"] = int(valid)
                row["校内绿色像素"] = int(green)
            except Exception as e:
                row["校内绿地率"] = f"错误: {e}"
                error_count += 1
        else:
            row["校内绿地率"] = "无截图"

        # --- 外围绿地率 ---
        if school_name in external_files:
            try:
                path = os.path.join(FOLDER_EXTERNAL, external_files[school_name])
                _, _, valid, green = load_and_detect(path)
                row["外围绿地率"] = calc_ratio(green, valid)
                row["外围有效像素"] = int(valid)
                row["外围绿色像素"] = int(green)
            except Exception as e:
                row["外围绿地率"] = f"错误: {e}"
                error_count += 1
        else:
            row["外围绿地率"] = "无截图"

        results.append(row)

        # 进度显示
        if i % 20 == 0 or i == len(all_schools):
            print(f"  已处理 {i}/{len(all_schools)}")

    # ---------- 3. 输出Excel ----------
    print("\n保存Excel...")
    try:
        import pandas as pd
        df = pd.DataFrame(results)

        # 重新排列列顺序
        cols = ["学校名称", "校内绿地率", "外围绿地率", "总绿地率",
                "校内有效像素", "校内绿色像素",
                "外围有效像素", "外围绿色像素",
                "总有效像素", "总绿色像素"]
        cols = [c for c in cols if c in df.columns]
        df = df[cols]

        df.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')
        print(f"✓ 已保存: {OUTPUT_EXCEL}")

    except ImportError:
        # 没有pandas，输出CSV
        import csv
        csv_path = OUTPUT_EXCEL.replace('.xlsx', '.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"✓ 已保存(CSV): {csv_path}")

    # ---------- 4. 汇总 ----------
    print("")
    print("=" * 60)
    print(f"  计算完成！")
    print(f"  学校总数: {len(all_schools)}")
    print(f"  错误数: {error_count}")

    # 快速统计
    valid_results = [r for r in results if "%" in str(r.get("总绿地率", ""))]
    if valid_results:
        ratios = [float(r["总绿地率"].replace("%", "")) for r in valid_results]
        print(f"  总绿地率: 均值={np.mean(ratios):.1f}%, 中位数={np.median(ratios):.1f}%, 范围={np.min(ratios):.1f}%~{np.max(ratios):.1f}%")

    print(f"  输出: {OUTPUT_EXCEL}")
    print("=" * 60)


if __name__ == "__main__":
    main()
