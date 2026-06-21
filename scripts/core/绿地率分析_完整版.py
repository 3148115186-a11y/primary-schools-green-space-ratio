# -*- coding: utf-8 -*-
"""
绿地率批量分析 + 双方法可视化
================================
两种检测方法：HSV颜色检测 + ExG植被指数
输出：Excel结果 + 可视化图片 + 学校详情文件夹

使用方式：python 绿地率分析_完整版.py
"""

import os
import cv2
import numpy as np
from PIL import Image

# =============================================
#  ⚙️ 配置
# =============================================

BASE_DIR = os.environ.get("BASE_DIR", ".")  # 基础目录，包含校内/外围/完整截图文件夹

FOLDER_INTERNAL = os.path.join(BASE_DIR, "校内_导出截图")
FOLDER_EXTERNAL = os.path.join(BASE_DIR, "外围_导出截图")
FOLDER_COMBINED = os.path.join(BASE_DIR, "完整_导出截图")

OUTPUT_EXCEL = os.path.join(BASE_DIR, "绿地率计算结果_双方法.xlsx")

# 可视化输出文件夹（6个）
VIZ_FOLDERS = {
    ("校内", "HSV"): os.path.join(BASE_DIR, "校内_可视化_HSV"),
    ("外围", "HSV"): os.path.join(BASE_DIR, "外围_可视化_HSV"),
    ("总体", "HSV"): os.path.join(BASE_DIR, "总体_可视化_HSV"),
    ("校内", "ExG"): os.path.join(BASE_DIR, "校内_可视化_ExG"),
    ("外围", "ExG"): os.path.join(BASE_DIR, "外围_可视化_ExG"),
    ("总体", "ExG"): os.path.join(BASE_DIR, "总体_可视化_ExG"),
}

# 学校详情文件夹
DETAIL_DIR = os.path.join(BASE_DIR, "学校详情")

# 灰色遮罩
GRAY_RGB = np.array([150, 150, 150])
GRAY_TOLERANCE = 15

# HSV绿色检测参数（v4验证通过）
HSV_LOWER = (25, 18, 8)
HSV_UPPER = (100, 255, 220)

# ExG阈值（原始值范围-1~2，绿地通常>0.04）
EXG_THRESHOLD = 0.05


# =============================================
#  检测方法
# =============================================

def detect_hsv(img_rgb):
    """HSV颜色空间绿色检测"""
    bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, HSV_LOWER, HSV_UPPER) > 0
    return mask


def detect_exg(img_rgb):
    """
    超绿指数（Excess Green Index）
    ExG = 2*G - R - B （归一化到[-1,2]范围）
    """
    img = img_rgb.astype(np.float64)
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    total = r + g + b + 1e-10  # 防止除零
    rn, gn, bn = r / total, g / total, b / total
    exg = 2 * gn - rn - bn
    mask = exg > EXG_THRESHOLD
    return mask


# =============================================
#  可视化
# =============================================

def create_overlay(img_rgb, mask_green, mask_valid):
    """
    在原图上叠加绿色高亮
    绿地像素 → 半透明亮绿色
    非绿地有效像素 → 稍暗的原图
    灰色遮罩 → 保持灰色
    """
    overlay = img_rgb.copy().astype(np.float64)

    # 非绿地有效区域：稍微变暗
    non_green_valid = mask_valid & ~mask_green
    overlay[non_green_valid] = overlay[non_green_valid] * 0.6

    # 绿地区域：叠加亮绿色
    overlay[mask_green] = overlay[mask_green] * 0.4 + np.array([0, 255, 0]) * 0.6

    # 灰色区域：保持不变
    return np.clip(overlay, 0, 255).astype(np.uint8)


# =============================================
#  工具函数
# =============================================

def get_valid_and_green(img_rgb, method="hsv"):
    """获取有效掩膜和绿色掩膜"""
    mask_valid = ~np.all(np.abs(img_rgb.astype(int) - GRAY_RGB) < GRAY_TOLERANCE, axis=2)

    if method == "hsv":
        mask_green = detect_hsv(img_rgb)
    elif method == "exg":
        mask_green = detect_exg(img_rgb)
    else:
        raise ValueError(f"未知方法: {method}")

    return mask_valid, mask_green


def load_img(img_path):
    """读取图片，返回RGB numpy数组"""
    img_pil = Image.open(img_path)
    img = np.array(img_pil)
    if img.shape[2] == 4:
        img = img[:, :, :3]
    return img


def calc_ratio(mask_green, mask_valid):
    """计算绿地率"""
    valid_count = np.sum(mask_valid)
    if valid_count == 0:
        return 0.0, 0, 0
    green_count = np.sum(mask_green & mask_valid)
    ratio = green_count / valid_count * 100
    return ratio, int(valid_count), int(green_count)


# =============================================
#  主程序
# =============================================

def main():
    print("=" * 60)
    print("  绿地率批量分析（HSV + ExG 双方法）")
    print("=" * 60)

    # ---------- 1. 创建输出文件夹 ----------
    print("\n创建输出文件夹...")
    for path in VIZ_FOLDERS.values():
        os.makedirs(path, exist_ok=True)
    os.makedirs(DETAIL_DIR, exist_ok=True)
    print(f"[OK] 6个可视化文件夹 + 学校详情文件夹")

    # ---------- 2. 读取文件列表 ----------
    internal_files = {os.path.splitext(f)[0]: f for f in os.listdir(FOLDER_INTERNAL) if f.endswith('.png')}
    external_files = {os.path.splitext(f)[0]: f for f in os.listdir(FOLDER_EXTERNAL) if f.endswith('.png')}
    combined_files = {os.path.splitext(f)[0]: f for f in os.listdir(FOLDER_COMBINED) if f.endswith('.png')}

    all_schools = sorted(combined_files.keys())
    print(f"\n校内: {len(internal_files)}张 | 外围: {len(external_files)}张 | 完整: {len(combined_files)}张")
    print(f"学校总数: {len(all_schools)}")

    # ---------- 3. 逐校处理 ----------
    results = []
    total = len(all_schools)

    print("-" * 60)
    print("开始处理...\n")

    for i, school_name in enumerate(all_schools, 1):
        row = {"学校名称": school_name}

        # 创建学校详情文件夹
        school_detail = os.path.join(DETAIL_DIR, school_name)
        os.makedirs(school_detail, exist_ok=True)

        # 三种情形
        scenarios = [
            ("校内", internal_files, "校内"),
            ("外围", external_files, "外围"),
            ("总体", combined_files, "总体"),
        ]

        for scenario_name, file_dict, prefix in scenarios:
            if school_name not in file_dict:
                row[f"{prefix}_校内HSV"] = "无截图"
                row[f"{prefix}_ExG"] = "无截图"
                continue

            img_path = os.path.join(
                FOLDER_INTERNAL if scenario_name == "校内" else
                FOLDER_EXTERNAL if scenario_name == "外围" else
                FOLDER_COMBINED,
                file_dict[school_name]
            )

            try:
                img_rgb = load_img(img_path)
                mask_valid, mask_hsv = get_valid_and_green(img_rgb, "hsv")
                _, mask_exg = get_valid_and_green(img_rgb, "exg")

                # 计算比率
                ratio_hsv, valid, green_hsv = calc_ratio(mask_hsv, mask_valid)
                ratio_exg, _, green_exg = calc_ratio(mask_exg, mask_valid)

                row[f"{prefix}绿地率_HSV"] = f"{ratio_hsv:.1f}%"
                row[f"{prefix}绿地率_ExG"] = f"{ratio_exg:.1f}%"
                row[f"{prefix}有效像素"] = valid
                row[f"{prefix}绿色像素_HSV"] = green_hsv
                row[f"{prefix}绿色像素_ExG"] = green_exg

                # --- 保存可视化 ---
                overlay_hsv = create_overlay(img_rgb, mask_hsv, mask_valid)
                overlay_exg = create_overlay(img_rgb, mask_exg, mask_valid)

                viz_name = f"{prefix}_{school_name}.png"

                # 方法文件夹（使用PIL保存，避免cv2对中文路径写入失败）
                folder_key_hsv = ("校内" if scenario_name == "校内" else "外围" if scenario_name == "外围" else "总体", "HSV")
                folder_key_exg = ("校内" if scenario_name == "校内" else "外围" if scenario_name == "外围" else "总体", "ExG")
                Image.fromarray(overlay_hsv).save(
                    os.path.join(VIZ_FOLDERS[folder_key_hsv], viz_name)
                )
                Image.fromarray(overlay_exg).save(
                    os.path.join(VIZ_FOLDERS[folder_key_exg], viz_name)
                )

                # --- 保存学校详情 ---
                # 原图
                orig_name = f"{prefix}_原图.png"
                Image.fromarray(img_rgb).save(
                    os.path.join(school_detail, orig_name)
                )
                # HSV可视化
                Image.fromarray(overlay_hsv).save(
                    os.path.join(school_detail, f"{prefix}_绿地识别_HSV.png")
                )
                # ExG可视化
                Image.fromarray(overlay_exg).save(
                    os.path.join(school_detail, f"{prefix}_绿地识别_ExG.png")
                )

            except Exception as e:
                row[f"{prefix}绿地率_HSV"] = f"错误: {e}"
                row[f"{prefix}绿地率_ExG"] = f"错误: {e}"

        results.append(row)

        if i % 20 == 0 or i == total:
            print(f"  已处理 {i}/{total}")

    # ---------- 4. 输出Excel ----------
    print("\n保存Excel...")
    try:
        import pandas as pd
        df = pd.DataFrame(results)

        # 列顺序
        desired_cols = [
            "学校名称",
            "校内绿地率_HSV", "校内绿地率_ExG",
            "外围绿地率_HSV", "外围绿地率_ExG",
            "总体绿地率_HSV", "总体绿地率_ExG",
            "校内有效像素", "校内绿色像素_HSV", "校内绿色像素_ExG",
            "外围有效像素", "外围绿色像素_HSV", "外围绿色像素_ExG",
            "总体有效像素", "总体绿色像素_HSV", "总体绿色像素_ExG",
        ]
        cols = [c for c in desired_cols if c in df.columns]
        df = df[cols]
        df.to_excel(OUTPUT_EXCEL, index=False, engine='openpyxl')
        print(f"[OK] 已保存: {OUTPUT_EXCEL}")

    except ImportError:
        import csv
        csv_path = OUTPUT_EXCEL.replace('.xlsx', '.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"[OK] 已保存(CSV): {csv_path}")

    # ---------- 5. 汇总统计 ----------
    print("\n" + "=" * 60)
    print("  处理完成！")
    print(f"  学校总数: {total}")
    print(f"  输出文件夹:")
    print(f"    可视化(HSV): 校内/外围/总体 各{total}张")
    print(f"    可视化(ExG): 校内/外围/总体 各{total}张")
    print(f"    学校详情: {total}个文件夹, 每个6张图")
    print(f"    Excel: {OUTPUT_EXCEL}")
    print("=" * 60)

    # 快速统计
    for method in ["HSV", "ExG"]:
        ratios = [float(r[f"总体绿地率_{method}"].replace("%", ""))
                  for r in results if "%" in str(r.get(f"总体绿地率_{method}", ""))]
        if ratios:
            print(f"\n  {method} 总绿地率统计:")
            print(f"    均值: {np.mean(ratios):.1f}%")
            print(f"    中位数: {np.median(ratios):.1f}%")
            print(f"    范围: {np.min(ratios):.1f}% ~ {np.max(ratios):.1f}%")


if __name__ == "__main__":
    main()
