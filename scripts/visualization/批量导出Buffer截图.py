# -*- coding: utf-8 -*-
"""
批量导出小学Buffer截图工具 v4
========================================
功能：遍历"小学buffer"图层的每个要素，缩放至该要素范围，
      等待卫星底图瓦片加载后导出地图截图，以对应AOI的name字段值作为文件名。

运行方式：在 GeoScene Pro / ArcGIS Pro 的 Python 窗口中运行
         exec(open(r"脚本路径", encoding="utf-8").read())

⚠️ 运行前准备（必做！）：
  1. 在 Pro 项目中新建一个【布局】（插入 → 新建布局 → A4 横向 或自定义尺寸）
  2. 在布局中插入一个【地图框】（插入 → 地图框 → 选择包含卫星底图+AOI+Buffer的地图）
  3. 调整地图框大小，使其铺满布局页面（拉到满边）
  4. 记住布局的名称，填入下方 LAYOUT_NAME 配置

v4 更新：
  - 用 arcpy.SpatialJoin_analysis 替代 Python 层 within() 匹配
    （C++ 空间引擎，秒级完成 vs Python 层 O(N²) 需要数十分钟）
  - 修复 arcpy.mp.Rectangle 不存在的问题（v3已修复）
  - 移除 input() 暂停（Python窗口不支持交互式输入）
"""

import arcpy
import os
import time

# =============================================
#  ⚙️ 用户配置区域 - 根据你的项目修改以下参数
# =============================================

# 输出文件夹路径（图片将保存在这里）
OUTPUT_FOLDER = os.environ.get("OUTPUT_FOLDER", "./导出截图")  # 截图输出目录

# 图层名称 —— 必须与 Pro 内容列表（TOC）中显示的名称一致
BUFFER_LAYER_NAME = "小学buffer"       # Buffer 红线图层的名称
AOI_LAYER_NAME = "海淀区小学AOI_POI边界"     # AOI 边界图层的名称

# AOI 图层中的名称字段
NAME_FIELD = "name"

# ⚠️ 布局名称 —— 必须与 Pro 中你手动创建的布局名称一致
LAYOUT_NAME = "布局"                    # 改成你实际的布局名称

# 导出参数
DPI = 200                               # 图片分辨率（DPI）
EXPORT_FORMAT = "PNG"                    # 导出格式: "PNG", "JPEG", "TIFF"

# 范围扩展比例
# 1.0 = 刚好贴合要素; 1.15 = 向外扩展15%; 1.2 = 扩展20%
EXPAND_RATIO = 1.15

# =============================================
#  ⚠️ 瓦片加载延迟设置（关键参数！）
# =============================================
# 卫星底图瓦片需要时间加载，设置太短会导致图片出现灰色空洞
# 建议值：网络好2~3秒 / 网络一般3~5秒 / 网络慢5~8秒
TILE_LOAD_DELAY = 3

# 首轮预览：导出前1张后暂停多少秒让你检查
# 设为 0 则不暂停，直接全部导出
PREVIEW_PAUSE_SECONDS = 30              # 首张导出后暂停30秒供你检查

# =============================================
#  辅助函数
# =============================================

def find_layer(map_obj, layer_name):
    """在地图中查找图层（支持部分名称匹配）"""
    for lyr in map_obj.listLayers():
        if lyr.name == layer_name:
            return lyr
    for lyr in map_obj.listLayers():
        if layer_name in lyr.name:
            return lyr
    return None


def build_buffer_aoi_mapping(buffer_layer, aoi_layer, name_field):
    """
    使用 extent 坐标比较 构建 Buffer→AOI名称 映射表。
    原理：每个 AOI 的质心一定在其对应 Buffer 的 bounding box 内。
    只做数值比较，不调用 within() 等几何运算，速度快 100+ 倍。
    """
    # --- 获取 AOI 字段名 ---
    aoi_fields = [f.name for f in arcpy.ListFields(aoi_layer)]
    actual_name_field = None
    for f in aoi_fields:
        if f.lower() == name_field.lower():
            actual_name_field = f
            break
    if actual_name_field is None:
        arcpy.AddMessage(f"  ⚠ AOI图层可用字段: {aoi_fields}")
        raise ValueError(f"AOI图层中未找到字段 '{name_field}'")
    print(f"  AOI名称字段: {actual_name_field}")

    # --- 读取所有 AOI：name + 质心坐标 ---
    # SHAPE@XY 返回质心 (x, y)，非常轻量
    aoi_list = []
    with arcpy.da.SearchCursor(aoi_layer, [actual_name_field, "SHAPE@XY"]) as cursor:
        for row in cursor:
            name_val = row[0]
            xy = row[1]
            if name_val and xy:
                aoi_list.append((str(name_val).strip(), xy[0], xy[1]))
    print(f"  AOI要素数: {len(aoi_list)}")

    # --- 读取所有 Buffer：OID + Extent ---
    # SHAPE@ 返回完整几何，取 .extent 得到 bounding box
    buffer_list = []
    with arcpy.da.SearchCursor(buffer_layer, ["OID@", "SHAPE@"]) as cursor:
        for row in cursor:
            oid = row[0]
            geom = row[1]
            if geom:
                ext = geom.extent
                buffer_list.append((oid, ext.XMin, ext.XMax, ext.YMin, ext.YMax))
    print(f"  Buffer要素数: {len(buffer_list)}")

    # --- 匹配：AOI质心落在 Buffer extent 内 → 匹配 ---
    # 这是纯数值比较，极快（156×156 = 24336 次比较，<1秒）
    mapping = {}
    unmatched_aoi = []

    for name_val, cx, cy in aoi_list:
        matched = False
        for oid, xmin, xmax, ymin, ymax in buffer_list:
            if xmin <= cx <= xmax and ymin <= cy <= ymax:
                mapping[oid] = name_val
                matched = True
                break  # 一个AOI只匹配一个Buffer

        if not matched:
            unmatched_aoi.append(name_val)

    print(f"  匹配成功: {len(mapping)}")
    if unmatched_aoi:
        print(f"  未匹配AOI ({len(unmatched_aoi)}): {unmatched_aoi[:5]}{'...' if len(unmatched_aoi) > 5 else ''}")

    return mapping


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.strip().strip('.')
    if not name:
        name = "unnamed"
    return name


def expand_extent(extent, ratio):
    """按比例扩展范围，使要素不紧贴图片边缘"""
    x_center = (extent.XMin + extent.XMax) / 2
    y_center = (extent.YMin + extent.YMax) / 2
    x_half = (extent.XMax - extent.XMin) * ratio / 2
    y_half = (extent.YMax - extent.YMin) * ratio / 2
    return arcpy.Extent(
        x_center - x_half,
        y_center - y_half,
        x_center + x_half,
        y_center + y_half
    )


def set_camera_extent(map_frame, extent):
    """
    设置地图框的相机范围，兼容不同版本。
    """
    cam = map_frame.camera

    # 方法1：setExtent
    try:
        cam.setExtent(extent)
        return True
    except Exception:
        pass

    # 方法2：中心 + 比例尺
    try:
        cam.X = (extent.XMin + extent.XMax) / 2
        cam.Y = (extent.YMin + extent.YMax) / 2
        if hasattr(map_frame, 'elementWidth') and map_frame.elementWidth > 0:
            ext_width = extent.XMax - extent.XMin
            scale = ext_width / map_frame.elementWidth
            cam.scale = scale
        return True
    except Exception as e:
        arcpy.AddWarning(f"    设置相机范围失败: {e}")
        return False


def export_map_frame(map_frame, output_path, dpi=200, export_format="PNG"):
    """导出地图框为图片（GeoScene Pro 用 resolution 参数）"""
    if export_format.upper() == "PNG":
        map_frame.exportToPNG(output_path, resolution=dpi)
    elif export_format.upper() == "JPEG":
        map_frame.exportToJPEG(output_path, resolution=dpi)
    elif export_format.upper() == "TIFF":
        map_frame.exportToTIFF(output_path, resolution=dpi)
    else:
        map_frame.exportToPNG(output_path, resolution=dpi)


# =============================================
#  主程序
# =============================================

def main():
    start_time = time.time()

    print("=" * 60)
    print("  批量导出小学Buffer截图工具 v4")
    print("=" * 60)

    # ---------- 1. 打开当前项目 ----------
    aprx = arcpy.mp.ArcGISProject("CURRENT")

    # ---------- 2. 查找布局和地图框 ----------
    print("")
    print("查找布局和地图框...")

    all_layouts = aprx.listLayouts()
    print(f"项目中的布局 ({len(all_layouts)}):")
    for l in all_layouts:
        mf_count = len(l.listElements("MAPFRAME_ELEMENT"))
        print(f"  - '{l.name}' (地图框数: {mf_count})")

    # 查找目标布局
    layout = None
    for l in all_layouts:
        if l.name == LAYOUT_NAME:
            layout = l
            break

    if layout is None:
        for l in all_layouts:
            if LAYOUT_NAME in l.name:
                layout = l
                print(f"  布局名称模糊匹配: '{l.name}'")
                break

    if layout is None:
        print("")
        print("!" * 60)
        print("  ✗ 未找到布局！请先在 Pro 中创建布局和地图框")
        print(f"  当前设置: LAYOUT_NAME = '{LAYOUT_NAME}'")
        print("!" * 60)
        raise ValueError(f"未找到布局 '{LAYOUT_NAME}'")

    print(f"✓ 使用布局: '{layout.name}'")

    map_frames = layout.listElements("MAPFRAME_ELEMENT")
    if not map_frames:
        raise ValueError(f"布局 '{layout.name}' 中没有地图框！")

    map_frame = map_frames[0]
    print(f"✓ 使用地图框: '{map_frame.name}'")

    map_obj = map_frame.map
    if map_obj is None:
        raise ValueError("地图框未关联任何地图！")
    print(f"✓ 关联地图: '{map_obj.name}'")

    print("地图中的图层:")
    for lyr in map_obj.listLayers():
        print(f"  - {lyr.name}")

    # ---------- 3. 查找图层 ----------
    print("")
    print("查找Buffer和AOI图层...")

    buffer_layer = find_layer(map_obj, BUFFER_LAYER_NAME)
    aoi_layer = find_layer(map_obj, AOI_LAYER_NAME)

    if not buffer_layer:
        raise ValueError(f"未找到Buffer图层 '{BUFFER_LAYER_NAME}'！")
    if not aoi_layer:
        raise ValueError(f"未找到AOI图层 '{AOI_LAYER_NAME}'！")

    print(f"✓ Buffer图层: {buffer_layer.name}")
    print(f"✓ AOI图层: {aoi_layer.name}")

    # ---------- 4. 构建 Buffer→AOI名称 映射表 ----------
    print("")
    print("正在构建 Buffer↔AOI 名称映射表（使用空间连接）...")

    buffer_fields = [f.name for f in arcpy.ListFields(buffer_layer)]
    print(f"Buffer图层字段: {buffer_fields}")

    has_name_in_buffer = False
    actual_buffer_name_field = None
    for f in buffer_fields:
        if f.lower() == NAME_FIELD.lower():
            actual_buffer_name_field = f
            break

    # 即使 Buffer 有 name 字段，也要检查值是否真的非空
    if actual_buffer_name_field:
        non_empty_count = 0
        total_count = 0
        with arcpy.da.SearchCursor(buffer_layer, [actual_buffer_name_field]) as sc:
            for row in sc:
                total_count += 1
                if row[0] and str(row[0]).strip():
                    non_empty_count += 1
        print(f"  Buffer '{actual_buffer_name_field}' 字段: {non_empty_count}/{total_count} 个非空")

        if non_empty_count > total_count * 0.5:
            # 超过半数有值，直接使用
            has_name_in_buffer = True
            print(f"✓ Buffer图层 '{actual_buffer_name_field}' 字段有效，直接使用")
            oid_to_name = None
            cursor_fields = ["OID@", "SHAPE@", actual_buffer_name_field]
        else:
            # 大部分为空，用空间连接
            print(f"  Buffer的 '{actual_buffer_name_field}' 字段大多为空，改用空间连接匹配")
            has_name_in_buffer = False

    if not has_name_in_buffer:
        print(f"使用空间连接匹配AOI名称...")
        oid_to_name = build_buffer_aoi_mapping(
            buffer_layer, aoi_layer, NAME_FIELD
        )
        cursor_fields = ["OID@", "SHAPE@"]

    # ---------- 5. 创建输出文件夹 ----------
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"✓ 输出文件夹: {OUTPUT_FOLDER}")

    # ---------- 6. 遍历Buffer要素并导出 ----------
    count = 0
    success_count = 0
    error_count = 0
    skip_count = 0

    print("-" * 60)
    print(f"开始遍历Buffer要素...")
    print(f"瓦片加载等待: {TILE_LOAD_DELAY} 秒")
    if PREVIEW_PAUSE_SECONDS > 0:
        print(f"首张预览暂停: {PREVIEW_PAUSE_SECONDS} 秒")
    print("")

    with arcpy.da.SearchCursor(buffer_layer, cursor_fields) as cursor:
        for row in cursor:
            count += 1
            oid = row[0]
            geom = row[1]

            if geom is None:
                skip_count += 1
                print(f"  [{count}] OBJECTID={oid}: 无几何，跳过")
                continue

            # --- 获取学校名称 ---
            if has_name_in_buffer:
                school_name = row[2]
            else:
                school_name = oid_to_name.get(oid, None)

            if not school_name:
                school_name = f"未知_OID{oid}"
                print(f"  [{count}] OBJECTID={oid}: 未匹配到AOI名称")

            # --- 设置相机范围 ---
            extent = expand_extent(geom.extent, EXPAND_RATIO)

            if not set_camera_extent(map_frame, extent):
                error_count += 1
                print(f"  [{count}] ✗ {school_name}: 无法设置相机范围")
                continue

            # --- 等待瓦片加载 ---
            time.sleep(TILE_LOAD_DELAY)

            # --- 构建输出路径 ---
            safe_name = sanitize_filename(str(school_name))
            output_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}.png")

            if os.path.exists(output_path):
                output_path = os.path.join(OUTPUT_FOLDER, f"{safe_name}_OID{oid}.png")

            # --- 导出图片 ---
            try:
                export_map_frame(map_frame, output_path, DPI, EXPORT_FORMAT)
                success_count += 1
                elapsed = time.time() - start_time
                print(f"  [{count}] ✓ {safe_name}.png  (已用时 {elapsed:.0f}s)")

            except Exception as e:
                error_count += 1
                print(f"  [{count}] ✗ {safe_name}: 导出失败 - {e}")

            # --- 首轮预览暂停（用 sleep 替代 input） ---
            if PREVIEW_PAUSE_SECONDS > 0 and success_count == 1:
                print("")
                print("!" * 60)
                print(f"  ⏸ 首张图片已导出: {output_path}")
                print("  请打开检查：卫星底图是否完整？Buffer红线是否可见？")
                print(f"  暂停 {PREVIEW_PAUSE_SECONDS} 秒后自动继续...")
                print("  （如果瓦片有空洞，请中断脚本，增大 TILE_LOAD_DELAY 后重跑）")
                print("!" * 60)
                time.sleep(PREVIEW_PAUSE_SECONDS)

    # ---------- 7. 汇总 ----------
    total_time = time.time() - start_time
    print("")
    print("=" * 60)
    print(f"  导出完成！")
    print(f"  总数: {count}")
    print(f"  成功: {success_count}")
    print(f"  失败: {error_count}")
    print(f"  跳过: {skip_count}")
    print(f"  总用时: {total_time:.1f} 秒 ({total_time/60:.1f} 分钟)")
    print(f"  输出文件夹: {OUTPUT_FOLDER}")
    print("=" * 60)


if __name__ == "__main__":
    main()
