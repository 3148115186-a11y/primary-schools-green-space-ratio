# -*- coding: utf-8 -*-
"""
绿地率批量分析（高德地图版）
============================
HSV绿色检测，v7参数
输出：学校详情文件夹 + 3个可视化文件夹 + CSV统计表

使用方式：
1. 修改下方 CONFIG 中的路径配置
2. python 绿地率分析_高德地图.py
"""

import os
import csv
import cv2
import numpy as np
from PIL import Image

# =============================================
#  ⚙️ 配置（使用前请修改以下路径）
# =============================================

CONFIG = {
    # 输入：三组截图文件夹
    "folder_internal": "./高德地图_校内截图_原图",
    "folder_external": "./高德地图_外围截图_原图",
    "folder_combined": "./高德地图_总体截图_原图",

    # 输出目录
    "output_dir": "./output",

    # HSV v7参数
    "hsv_lower": (25, 25, 20),
    "hsv_upper": (95, 255, 215),

    # 灰色遮罩参数
    "gray_rgb": (150, 150, 150),
    "gray_tolerance": 15,
}


# =============================================
#  核心函数
# =============================================

def load_img(img_path):
    """读取图片，返回RGB numpy数组"""
    img = np.array(Image.open(img_path))
    if img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def detect_and_calc(img_rgb, hsv_lower, hsv_upper, gray_rgb, gray_tolerance):
    """HSV绿色检测，返回掩膜和绿地率"""
    gray = np.array(gray_rgb)
    mask_valid = ~np.all(np.abs(img_rgb.astype(int) - gray) < gray_tolerance, axis=2)
    bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, hsv_lower, hsv_upper) > 0

    valid = int(np.sum(mask_valid))
    green = int(np.sum(mask_green & mask_valid))
    ratio = green / valid * 100 if valid > 0 else 0.0
    return mask_valid, mask_green, ratio, valid, green


def create_overlay(img_rgb, mask_green, mask_valid):
    """绿色高亮叠加在原图上"""
    overlay = img_rgb.copy().astype(np.float64)
    non_green_valid = mask_valid & ~mask_green
    overlay[non_green_valid] = overlay[non_green_valid] * 0.6
    overlay[mask_green] = overlay[mask_green] * 0.4 + np.array([0, 255, 0]) * 0.6
    return np.clip(overlay, 0, 255).astype(np.uint8)


# =============================================
#  主程序
# =============================================

def main():
    cfg = CONFIG
    base_dir = cfg["output_dir"]
    hsv_lower = tuple(cfg["hsv_lower"])
    hsv_upper = tuple(cfg["hsv_upper"])
    gray_rgb = np.array(cfg["gray_rgb"])
    gray_tolerance = cfg["gray_tolerance"]

    print("=" * 60)
    print("  绿地率批量分析（HSV v7）")
    print("=" * 60)

    # 创建输出文件夹
    detail_dir = os.path.join(base_dir, "学校详情")
    viz_internal = os.path.join(base_dir, "校内_可视化")
    viz_external = os.path.join(base_dir, "外围_可视化")
    viz_combined = os.path.join(base_dir, "总体_可视化")
    for d in [detail_dir, viz_internal, viz_external, viz_combined]:
        os.makedirs(d, exist_ok=True)
    print("[OK] 输出文件夹就绪")

    # 读取文件列表
    internal_files = {os.path.splitext(f)[0]: f for f in os.listdir(cfg["folder_internal"]) if f.endswith('.png')}
    external_files = {os.path.splitext(f)[0]: f for f in os.listdir(cfg["folder_external"]) if f.endswith('.png')}
    combined_files = {os.path.splitext(f)[0]: f for f in os.listdir(cfg["folder_combined"]) if f.endswith('.png')}

    all_schools = sorted(combined_files.keys())
    print(f"\n校内: {len(internal_files)}张 | 外围: {len(external_files)}张 | 完整: {len(combined_files)}张")
    print(f"学校总数: {len(all_schools)}")

    # 逐校处理
    results = []
    total = len(all_schools)
    print("-" * 60)
    print("开始处理...\n")

    for i, school_name in enumerate(all_schools, 1):
        row = {"学校名称": school_name}
        school_detail = os.path.join(detail_dir, school_name)
        os.makedirs(school_detail, exist_ok=True)

        scenarios = [
            ("校内", internal_files, cfg["folder_internal"], viz_internal),
            ("外围", external_files, cfg["folder_external"], viz_external),
            ("总体", combined_files, cfg["folder_combined"], viz_combined),
        ]

        for prefix, file_dict, src_folder, vf in scenarios:
            if school_name not in file_dict:
                row[f"{prefix}绿地率"] = "无截图"
                row[f"{prefix}有效像素"] = ""
                row[f"{prefix}绿色像素"] = ""
                continue

            img_path = os.path.join(src_folder, file_dict[school_name])
            try:
                img_rgb = load_img(img_path)
                mask_valid, mask_green, ratio, valid, green = detect_and_calc(
                    img_rgb, hsv_lower, hsv_upper, gray_rgb, gray_tolerance
                )
                row[f"{prefix}绿地率"] = f"{ratio:.1f}%"
                row[f"{prefix}有效像素"] = valid
                row[f"{prefix}绿色像素"] = green

                overlay = create_overlay(img_rgb, mask_green, mask_valid)
                Image.fromarray(overlay).save(os.path.join(vf, f"{prefix}_{school_name}.png"))
                Image.fromarray(img_rgb).save(os.path.join(school_detail, f"{prefix}_原图.png"))
                Image.fromarray(overlay).save(os.path.join(school_detail, f"{prefix}_绿地识别.png"))
            except Exception as e:
                row[f"{prefix}绿地率"] = f"错误: {e}"

        results.append(row)
        if i % 20 == 0 or i == total:
            print(f"  已处理 {i}/{total}")

    # 输出CSV
    csv_path = os.path.join(base_dir, "绿地率统计结果.csv")
    cols = [
        "学校名称",
        "校内绿地率", "校内有效像素", "校内绿色像素",
        "外围绿地率", "外围有效像素", "外围绿色像素",
        "总体绿地率", "总体有效像素", "总体绿色像素",
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {csv_path}")

    # 汇总
    ratios = [float(r["总体绿地率"].replace("%", ""))
              for r in results if "%" in str(r.get("总体绿地率", ""))]
    if ratios:
        print(f"\n  总体绿地率: 均值{np.mean(ratios):.1f}%  中位数{np.median(ratios):.1f}%  "
              f"范围{np.min(ratios):.1f}%~{np.max(ratios):.1f}%")


if __name__ == "__main__":
    main()
