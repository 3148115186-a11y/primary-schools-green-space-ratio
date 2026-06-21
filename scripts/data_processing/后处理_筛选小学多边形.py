"""
路线C后处理：筛选小学相关多边形 + 优化名称匹配
在原始1751个OSM要素基础上，做以下优化：
  1. 按GDB点位做"空间关联过滤"：只保留与GDB小学点位距离<500m的OSM多边形
  2. 同一GDB小学可能对应多个OSM多边形（校园+建筑），全部保留，标注来源
  3. 统计12所未覆盖的小学（仅点位，无多边形）
  4. 输出最终精炼版 GeoJSON + Shapefile
"""

import io, sys, os, warnings
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

GDB_PATH   = os.environ.get("GDB_PATH", "./北京.gdb")  # GDB数据库路径
GDB_LAYER  = '北京海淀小学'
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./海淀小学绿地")  # 输出目录
OSM_GEOJSON = os.path.join(OUTPUT_DIR, "海淀小学_OSM边界.geojson")

# 与GDB小学点位关联的最大距离阈值（米）
# 300m精确匹配 → 500m宽松过滤，确保校园边界范围内的building也被保留
FILTER_DIST_M = 500

def main():
    print("=" * 65)
    print("  后处理：从1751个OSM要素中筛选海淀区小学相关多边形")
    print("=" * 65 + "\n")

    # 读取原始OSM结果
    print("[1] 读取原始OSM要素...")
    gdf_osm = gpd.read_file(OSM_GEOJSON)
    print(f"   原始要素: {len(gdf_osm)} 个")

    # 读取GDB参考点位
    print("[2] 读取GDB参考小学点位...")
    gdf_ref = gpd.read_file(GDB_PATH, layer=GDB_LAYER)
    if gdf_ref.crs.to_epsg() != 4326:
        gdf_ref = gdf_ref.to_crs(epsg=4326)
    print(f"   GDB小学: {len(gdf_ref)} 所")

    # 投影到UTM 50N做距离计算
    print(f"\n[3] 空间关联过滤（每个OSM多边形距任意GDB点位 < {FILTER_DIST_M}m）...")
    gdf_osm_utm = gdf_osm.to_crs(epsg=32650)
    gdf_ref_utm = gdf_ref.to_crs(epsg=32650)

    # 对每个OSM要素，计算到最近GDB点的距离
    min_dists = []
    nearest_names = []
    nearest_idxs  = []

    for i, row_osm in enumerate(gdf_osm_utm.geometry):
        # 用质心做距离计算（避免大多边形被远处点选中）
        centroid = row_osm.centroid
        dists = gdf_ref_utm.geometry.distance(centroid)
        min_d   = dists.min()
        min_idx = dists.idxmin()
        min_dists.append(round(float(min_d), 1))
        nearest_names.append(gdf_ref.iloc[min_idx]["名称"])
        nearest_idxs.append(min_idx)

    gdf_osm = gdf_osm.copy()
    gdf_osm["nearest_name"] = nearest_names
    gdf_osm["nearest_dist"] = min_dists
    gdf_osm["ref_idx"]      = nearest_idxs

    # 筛选：只保留距任意GDB小学点位 < FILTER_DIST_M 的要素
    gdf_filtered = gdf_osm[gdf_osm["nearest_dist"] <= FILTER_DIST_M].copy()
    print(f"   过滤后: {len(gdf_filtered)} 个（删除了{len(gdf_osm)-len(gdf_filtered)}个非小学要素）")

    # 整理最终名称字段
    def final_name(row):
        # 优先：GDB精确匹配名称（已在school_name中）
        if row.get("school_name") and row.get("gdb_matched"):
            return row["school_name"]
        # 次选：nearest_name（最近GDB点名称）
        if row.get("nearest_dist", 9999) <= FILTER_DIST_M:
            return row["nearest_name"]
        # 最后：OSM自带名称
        if row.get("name"):
            return str(row["name"])
        return "未知"

    gdf_filtered["school_name"] = gdf_filtered.apply(final_name, axis=1)

    # 重新计算面积
    gdf_utm_f = gdf_filtered.to_crs(epsg=32650)
    gdf_filtered["area_m2"] = gdf_utm_f.geometry.area.round(1)

    # 统计：哪些GDB小学在OSM中有多边形，哪些没有
    ref_idxs_with_polygon = set(gdf_filtered["ref_idx"].tolist())
    covered_schools = gdf_ref.iloc[list(ref_idxs_with_polygon)]["名称"].tolist()
    uncovered_schools = gdf_ref[~gdf_ref.index.isin(ref_idxs_with_polygon)][["名称","经度","纬度"]]

    print(f"\n[4] 覆盖统计:")
    print(f"   OSM有多边形的小学: {len(ref_idxs_with_polygon)} 所")
    print(f"   仅有GDB点位（无多边形）: {len(uncovered_schools)} 所")
    if len(uncovered_schools) > 0:
        print(f"\n   以下小学在OSM中未找到边界多边形：")
        for _, row in uncovered_schools.iterrows():
            print(f"     - {row['名称']} ({row['经度']:.4f}, {row['纬度']:.4f})")

    # 保存精炼版输出
    print(f"\n[5] 导出精炼版数据...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # GeoJSON（精炼版，仅小学相关多边形）
    out_cols = ["school_name", "nearest_dist", "name", "name_zh",
                "amenity", "building", "osmid", "osm_type", "osm_tag",
                "area_m2", "geometry"]
    out_cols = [c for c in out_cols if c in gdf_filtered.columns]
    gdf_out = gdf_filtered[out_cols]

    gj_out = os.path.join(OUTPUT_DIR, "海淀小学_OSM边界_精炼.geojson")
    gdf_out.to_file(gj_out, driver="GeoJSON", encoding="utf-8")
    print(f"   精炼GeoJSON: {gj_out}")

    # Shapefile
    shp_dir = os.path.join(OUTPUT_DIR, "海淀小学_OSM_SHP")
    os.makedirs(shp_dir, exist_ok=True)
    shp_out = os.path.join(shp_dir, "海淀小学_OSM_精炼.shp")
    gdf_out.to_file(shp_out, driver="ESRI Shapefile", encoding="utf-8")
    print(f"   精炼Shapefile: {shp_out}")

    # 导出未覆盖小学为单独文件（仅点位）
    if len(uncovered_schools) > 0:
        unc_gdf = gdf_ref[~gdf_ref.index.isin(ref_idxs_with_polygon)].copy()
        unc_path = os.path.join(OUTPUT_DIR, "海淀小学_OSM未覆盖点位.geojson")
        unc_gdf.to_file(unc_path, driver="GeoJSON", encoding="utf-8")
        print(f"   未覆盖点位: {unc_path}")

    print("\n" + "=" * 65)
    print(f"  处理完成！")
    print(f"  小学相关OSM多边形: {len(gdf_out)} 个")
    print(f"  对应GDB小学数: {len(ref_idxs_with_polygon)} 所 / 180所")
    print(f"  覆盖率: {len(ref_idxs_with_polygon)/180*100:.1f}%")
    print(f"  面积范围: {gdf_out['area_m2'].min():.0f} ~ {gdf_out['area_m2'].max():.0f} m²")
    print("=" * 65)

    # 按学校分组统计多边形数量（即每所学校有几个OSM多边形）
    poly_count = gdf_filtered.groupby("school_name").size().sort_values(ascending=False)
    print(f"\n多边形数量TOP 10（每所学校对应的OSM多边形数）:")
    print(poly_count.head(10).to_string())

if __name__ == "__main__":
    main()
