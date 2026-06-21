"""
路线C：直接调用 Overpass API 获取海淀区学校边界
（绕过 osmnx 2.x features_from_* 中的投影NaN bug）
结合 GDB 参考点位做名称匹配，输出 GeoJSON + Shapefile
"""

import io, sys, os, math, time, warnings
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Point, Polygon, MultiPolygon
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
warnings.filterwarnings('ignore')

# ────────────────────────────────────────────
# 配置
# ────────────────────────────────────────────
GDB_PATH   = os.environ.get("GDB_PATH", "./北京.gdb")  # GDB数据库路径
GDB_LAYER  = '北京海淀小学'
OUTPUT_DIR = r'e:\学习资料\景观规划\海淀小学绿地'

# Overpass API 端点（多备选，按顺序尝试）
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# 海淀区精确 bbox（south, west, north, east）
HAIDIAN_BBOX = (39.87, 116.08, 40.18, 116.44)

MATCH_DIST_M = 300   # 名称匹配距离阈值（米）

# ────────────────────────────────────────────
# Overpass 查询
# ────────────────────────────────────────────
def build_overpass_query(bbox):
    """
    构造 Overpass QL 查询语句，获取海淀区内：
    - amenity=school（学校用地范围）
    - building=school（学校建筑）
    仅请求 way 和 relation（面状），out geom 获取坐标
    """
    s, w, n, e = bbox
    query = f"""
[out:json][timeout:180];
(
  way["amenity"="school"]({s},{w},{n},{e});
  relation["amenity"="school"]({s},{w},{n},{e});
  way["building"="school"]({s},{w},{n},{e});
  relation["building"="school"]({s},{w},{n},{e});
);
out body geom;
"""
    return query.strip()

def fetch_overpass(query, endpoints=OVERPASS_ENDPOINTS):
    """发送 Overpass 查询，自动重试多个端点"""
    for endpoint in endpoints:
        print(f"   尝试端点: {endpoint}")
        try:
            resp = requests.post(
                endpoint,
                data={"data": query},
                timeout=180,
                headers={"User-Agent": "landscape-research/1.0"}
            )
            if resp.status_code == 200:
                data = resp.json()
                n = len(data.get("elements", []))
                print(f"   成功！返回 {n} 个要素")
                return data
            else:
                print(f"   HTTP {resp.status_code}: {resp.text[:100]}")
        except requests.exceptions.Timeout:
            print(f"   超时，尝试下一个端点...")
        except Exception as e:
            print(f"   错误: {e}")
        time.sleep(2)
    return None

# ────────────────────────────────────────────
# 解析 Overpass JSON → GeoDataFrame
# ────────────────────────────────────────────
def parse_way(element):
    """解析 Overpass way 元素为 Shapely Polygon"""
    geometry = element.get("geometry", [])
    if len(geometry) < 3:
        return None
    coords = [(pt["lon"], pt["lat"]) for pt in geometry]
    try:
        poly = Polygon(coords)
        return poly if poly.is_valid else poly.buffer(0)
    except Exception:
        return None

def parse_relation(element):
    """
    解析 Overpass relation 元素为 Shapely Polygon/MultiPolygon。
    关系中的 outer ring 组成外轮廓，inner ring 组成孔。
    """
    members = element.get("members", [])
    outer_rings = []
    inner_rings = []

    for member in members:
        if member.get("type") != "way":
            continue
        geom = member.get("geometry", [])
        if len(geom) < 3:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in geom]
        role = member.get("role", "")
        if role == "inner":
            inner_rings.append(coords)
        else:
            outer_rings.append(coords)  # outer 或空 role

    if not outer_rings:
        return None

    try:
        # 多个 outer ring → MultiPolygon
        polys = []
        for ring in outer_rings:
            # 找属于此 outer 的 inner holes（简化：全部inner作为第一个outer的孔）
            poly = Polygon(ring)
            polys.append(poly)

        if len(polys) == 1 and inner_rings:
            poly = Polygon(outer_rings[0], inner_rings)
            return poly if poly.is_valid else poly.buffer(0)
        elif len(polys) == 1:
            return polys[0] if polys[0].is_valid else polys[0].buffer(0)
        else:
            mp = MultiPolygon(polys)
            return mp if mp.is_valid else mp.buffer(0)
    except Exception as e:
        return None

def overpass_to_geodataframe(data):
    """将 Overpass 原始 JSON 转换为 GeoDataFrame"""
    elements = data.get("elements", [])
    records = []
    way_cnt = rel_cnt = skip_cnt = 0

    for elem in elements:
        etype = elem.get("type")
        tags  = elem.get("tags", {})
        osmid = elem.get("id")

        if etype == "way":
            geom = parse_way(elem)
            way_cnt += 1
        elif etype == "relation":
            geom = parse_relation(elem)
            rel_cnt += 1
        else:
            skip_cnt += 1
            continue

        if geom is None or geom.is_empty:
            skip_cnt += 1
            continue

        record = {
            "osmid":      osmid,
            "osm_type":   etype,
            "name":       tags.get("name", ""),
            "name_zh":    tags.get("name:zh", ""),
            "amenity":    tags.get("amenity", ""),
            "building":   tags.get("building", ""),
            "operator":   tags.get("operator", ""),
            "addr_street": tags.get("addr:street", ""),
            "osm_tag":    ("amenity=school" if tags.get("amenity")=="school"
                           else "building=school"),
            "geometry":   geom,
        }
        records.append(record)

    print(f"   解析完成: way={way_cnt}, relation={rel_cnt}, 跳过={skip_cnt}")
    print(f"   有效要素: {len(records)} 个")

    if not records:
        return gpd.GeoDataFrame(columns=["geometry"], crs="EPSG:4326")

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    return gdf

# ────────────────────────────────────────────
# 空间匹配：GDB点位名称 → OSM多边形
# ────────────────────────────────────────────
def match_names(gdf_osm, gdf_ref):
    """
    对每个OSM多边形，找距质心最近的GDB参考点（投影坐标距离）。
    若距离 < MATCH_DIST_M，将GDB学校名赋给该多边形。
    """
    print(f"\n[步骤3] 空间匹配（阈值={MATCH_DIST_M}m）...")

    # 投影到 EPSG:32650（UTM 50N，适合北京，单位：米）
    gdf_osm_utm = gdf_osm.to_crs(epsg=32650)
    gdf_ref_utm = gdf_ref.to_crs(epsg=32650)
    centroids   = gdf_osm_utm.geometry.centroid

    names, dists, matched_flags = [], [], []

    for centroid in centroids:
        d = gdf_ref_utm.geometry.distance(centroid)
        min_d   = d.min()
        min_idx = d.idxmin()
        dists.append(round(float(min_d), 1))

        if min_d <= MATCH_DIST_M:
            names.append(gdf_ref.iloc[min_idx]["名称"])
            matched_flags.append(True)
        else:
            # 超出阈值 → 用OSM自带name
            osm_n = str(gdf_osm.iloc[centroids.index.tolist().index(centroid.wkt)
                                     if False else
                                     list(centroids).index(centroid)
                                     ]["name"] if False else
                        gdf_osm.loc[gdf_osm.index[list(centroids).index(centroid)], "name"] or "")
            names.append("")
            matched_flags.append(False)

    # 更简洁的写法
    names2, dists2, flags2 = [], [], []
    for i, centroid in enumerate(gdf_osm_utm.geometry.centroid):
        d = gdf_ref_utm.geometry.distance(centroid)
        min_d   = d.min()
        min_idx = d.idxmin()
        dists2.append(round(float(min_d), 1))
        if min_d <= MATCH_DIST_M:
            names2.append(gdf_ref.iloc[min_idx]["名称"])
            flags2.append(True)
        else:
            names2.append("")
            flags2.append(False)

    gdf_osm = gdf_osm.copy()
    gdf_osm["matched_name"] = names2
    gdf_osm["match_dist_m"] = dists2
    gdf_osm["gdb_matched"]  = flags2

    n_ok = sum(flags2)
    print(f"   成功匹配: {n_ok}/{len(gdf_osm)} 条")
    print(f"   未匹配  : {len(gdf_osm)-n_ok} 条（保留OSM原始名称）")
    return gdf_osm

# ────────────────────────────────────────────
# 输出
# ────────────────────────────────────────────
def export_results(gdf, gdf_ref):
    print("\n[步骤4] 整理字段并导出...")

    gdf = gdf.copy()

    # 最终名称：GDB匹配名 > OSM name:zh > OSM name > "未知"
    def final_name(row):
        if row.get("matched_name"):
            return row["matched_name"]
        if row.get("name_zh"):
            return str(row["name_zh"])
        if row.get("name"):
            return str(row["name"])
        return "未知学校"

    gdf["school_name"] = gdf.apply(final_name, axis=1)

    # 计算面积（m²）
    gdf_utm = gdf.to_crs(epsg=32650)
    gdf["area_m2"] = gdf_utm.geometry.area.round(1)

    # 简化字段顺序
    out_cols = ["school_name", "matched_name", "match_dist_m", "gdb_matched",
                "name", "name_zh", "amenity", "building", "osmid",
                "osm_type", "osm_tag", "area_m2", "geometry"]
    out_cols = [c for c in out_cols if c in gdf.columns]
    gdf_out = gdf[out_cols]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # GeoJSON
    gj = os.path.join(OUTPUT_DIR, "海淀小学_OSM边界.geojson")
    gdf_out.to_file(gj, driver="GeoJSON", encoding="utf-8")
    print(f"   GeoJSON  已保存: {gj}")

    # Shapefile
    shp_dir = os.path.join(OUTPUT_DIR, "海淀小学_OSM_SHP")
    os.makedirs(shp_dir, exist_ok=True)
    shp = os.path.join(shp_dir, "海淀小学_OSM.shp")
    gdf_out.to_file(shp, driver="ESRI Shapefile", encoding="utf-8")
    print(f"   Shapefile已保存: {shp}")

    # 导出GDB参考点位（方便在QGIS中对比）
    ref_out = os.path.join(OUTPUT_DIR, "海淀小学_GDB参考点位.geojson")
    gdf_ref.to_file(ref_out, driver="GeoJSON", encoding="utf-8")
    print(f"   GDB点位  已保存: {ref_out}")

    return gdf_out

# ────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  路线C：Overpass API 获取海淀区小学建筑边界（WGS-84）")
    print("  参考：北京.gdb / 北京海淀小学（180所）")
    print("=" * 65 + "\n")

    # 步骤1：加载GDB参考点位
    print("[步骤1] 读取GDB参考点位...")
    gdf_ref = gpd.read_file(GDB_PATH, layer=GDB_LAYER)
    if gdf_ref.crs and gdf_ref.crs.to_epsg() != 4326:
        gdf_ref = gdf_ref.to_crs(epsg=4326)
    print(f"   {GDB_LAYER}: {len(gdf_ref)} 所小学，CRS={gdf_ref.crs}")

    # 步骤2：Overpass查询
    print("\n[步骤2] 通过 Overpass API 查询海淀区学校面状边界...")
    query = build_overpass_query(HAIDIAN_BBOX)
    print(f"   查询范围: bbox={HAIDIAN_BBOX}")

    data = fetch_overpass(query)
    if data is None:
        print("ERROR: 所有Overpass端点均失败，请检查网络连接。")
        return

    gdf_osm = overpass_to_geodataframe(data)
    if gdf_osm.empty:
        print("ERROR: 未解析到任何有效面状要素。")
        return

    print(f"   几何类型: {gdf_osm.geom_type.value_counts().to_dict()}")

    # 步骤3：名称匹配
    gdf_matched = match_names(gdf_osm, gdf_ref)

    # 步骤4：导出
    gdf_final = export_results(gdf_matched, gdf_ref)

    # 汇总
    print("\n" + "=" * 65)
    print(f"  完成！OSM面状边界共 {len(gdf_final)} 个要素")
    print(f"  成功匹配GDB名称: {gdf_final['gdb_matched'].sum()} 个")
    print(f"  面积范围: {gdf_final['area_m2'].min():.0f} ~ {gdf_final['area_m2'].max():.0f} m²")
    print(f"  坐标系: EPSG:4326 (WGS-84)")
    print("=" * 65)

    print("\n前15条预览:")
    prev = ["school_name", "match_dist_m", "gdb_matched", "osm_tag", "area_m2"]
    prev = [c for c in prev if c in gdf_final.columns]
    print(gdf_final[prev].head(15).to_string(index=False))

    n_matched = int(gdf_final['gdb_matched'].sum())
    total_ref = len(gdf_ref)
    print(f"\nGDB覆盖率: {n_matched}/{total_ref} = {n_matched/total_ref*100:.1f}%")
    print(f"未在OSM中找到多边形: {total_ref - n_matched} 所")

if __name__ == "__main__":
    main()
