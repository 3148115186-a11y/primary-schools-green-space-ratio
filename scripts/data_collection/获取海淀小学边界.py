"""
获取北京市海淀区小学 POI 数据（高德地图 API 最终版）
--------------------------------------------------
已验证参数：
  - city=110108（海淀区adcode），返回194条，全部为海淀区数据
  - typecode 不限定（因小学分布在141200/141202/141203，不限更全）
  - 用关键词"小学"匹配，并以adname包含"海淀"做二次过滤

面状边界：
  - 高德 PlaceDetail API extensions=all 提供 polyline 字段
  - 若无多边形，退回到点位（中心点坐标）

输出：
  - 海淀小学_高德.geojson（WGS-84，EPSG:4326）
  - 海淀小学_SHP/ 目录下的 Shapefile
"""

import os, sys, io, math, time, subprocess
import requests
import geopandas as gpd
from shapely.geometry import Point, Polygon

# 强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ────────────────────────────────────────────
# 配置
# ────────────────────────────────────────────
def _get_key():
    k = os.environ.get("AMAP_WEB_KEY", "")
    if k: return k
    try:
        return subprocess.check_output(
            ['powershell', '-NoProfile', '-Command',
             '[System.Environment]::GetEnvironmentVariable("AMAP_WEB_KEY","User")'],
            text=True, encoding='utf-8').strip()
    except Exception:
        return ""

AMAP_KEY   = _get_key()
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./海淀小学绿地")  # 输出目录

PLACE_TEXT_URL   = "https://restapi.amap.com/v3/place/text"
PLACE_DETAIL_URL = "https://restapi.amap.com/v3/place/detail"
DISTRICT_URL     = "https://restapi.amap.com/v3/config/district"

HAIDIAN_ADCODE = "110108"   # 海淀区行政区划代码（已验证有效）
PAGE_SIZE      = 25         # 每页最大25条（高德限制）

# ────────────────────────────────────────────
# GCJ-02 → WGS-84 坐标转换
# ────────────────────────────────────────────
def gcj02_to_wgs84(lng, lat):
    """高德/腾讯 GCJ-02 坐标 → 国际标准 WGS-84 坐标"""
    a, ee = 6378245.0, 0.00669342162296594323
    def tlat(lo, la):
        r = -100.0+2*lo+3*la+0.2*la*la+0.1*lo*la+0.2*math.sqrt(abs(lo))
        r += (20*math.sin(6*lo*math.pi)+20*math.sin(2*lo*math.pi))*2/3
        r += (20*math.sin(la*math.pi)+40*math.sin(la/3*math.pi))*2/3
        r += (160*math.sin(la/12*math.pi)+320*math.sin(la*math.pi/30))*2/3
        return r
    def tlng(lo, la):
        r = 300+lo+2*la+0.1*lo*lo+0.1*lo*la+0.1*math.sqrt(abs(lo))
        r += (20*math.sin(6*lo*math.pi)+20*math.sin(2*lo*math.pi))*2/3
        r += (20*math.sin(lo*math.pi)+40*math.sin(lo/3*math.pi))*2/3
        r += (150*math.sin(lo/12*math.pi)+300*math.sin(lo/30*math.pi))*2/3
        return r
    dlat = tlat(lng-105, lat-35)
    dlng = tlng(lng-105, lat-35)
    rlat = lat/180*math.pi
    m = math.sin(rlat); m = 1-ee*m*m; sq = math.sqrt(m)
    dlat = dlat*180/((a*(1-ee))/(m*sq)*math.pi)
    dlng = dlng*180/(a/sq*math.cos(rlat)*math.pi)
    return lng-dlng, lat-dlat

def parse_location(loc_str):
    """解析 'lng,lat' 字符串，返回 (float,float) 或 None"""
    try:
        p = loc_str.strip().split(",")
        return float(p[0]), float(p[1])
    except Exception:
        return None

def parse_polyline(poly_str):
    """
    解析高德 polyline 字符串（格式: lng,lat;lng,lat;...|ring2...）
    返回 Shapely Polygon (WGS-84) 或 None
    """
    if not poly_str:
        return None
    try:
        rings = []
        for ring_str in poly_str.split("|"):
            pts = []
            for pt in ring_str.split(";"):
                c = parse_location(pt)
                if c:
                    pts.append(gcj02_to_wgs84(*c))
            if len(pts) >= 3:
                rings.append(pts)
        if not rings:
            return None
        poly = Polygon(rings[0], rings[1:])
        return poly if poly.is_valid else poly.buffer(0)
    except Exception:
        return None

# ────────────────────────────────────────────
# 获取海淀区行政边界（用于最终空间校验）
# ────────────────────────────────────────────
def get_haidian_boundary():
    """获取海淀区行政区划边界多边形（WGS-84）"""
    print("[步骤1] 获取海淀区行政边界...")
    params = {
        "key":         AMAP_KEY,
        "keywords":    "海淀区",
        "subdistrict": "0",
        "extensions":  "all",
        "output":      "json",
    }
    try:
        resp = requests.get(DISTRICT_URL, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "1":
            for d in data.get("districts", []):
                if d.get("adcode") == HAIDIAN_ADCODE:
                    poly = parse_polyline(d.get("polyline",""))
                    if poly:
                        print(f"   边界顶点数: {len(poly.exterior.coords)}")
                        return poly
    except Exception as e:
        print(f"   获取边界出错: {e}")
    print("   无法获取行政边界，跳过空间过滤。")
    return None

# ────────────────────────────────────────────
# 分页搜索所有小学 POI
# ────────────────────────────────────────────
def search_all_schools():
    """
    用高德 PlaceText API，city=110108（海淀区adcode），关键词=小学。
    已验证：此参数组合返回194条，全部属于海淀区。
    """
    print("[步骤2] 搜索海淀区小学 POI（关键词=小学, city=110108）...")
    all_pois = []
    page = 1

    while True:
        params = {
            "key":        AMAP_KEY,
            "keywords":   "小学",           # 关键词匹配名称
            "city":       HAIDIAN_ADCODE,   # 110108 = 海淀区，已验证精确有效
            "citylimit":  "true",           # 严格限定城市范围
            "output":     "json",
            "offset":     PAGE_SIZE,
            "page":       page,
            "extensions": "base",           # 先获取列表，边界在detail接口取
        }
        try:
            resp = requests.get(PLACE_TEXT_URL, params=params, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"   第{page}页请求异常: {e}")
            break

        if data.get("status") != "1":
            print(f"   API错误: {data.get('info')}")
            break

        pois  = data.get("pois", [])
        total = int(data.get("count", 0))

        # 保留海淀区内的记录（二次过滤）
        valid = [p for p in pois if "海淀" in p.get("adname","")]
        all_pois.extend(valid)

        print(f"   第{page}页: 返回{len(pois)}条 | 海淀={len(valid)}条 | 累计={len(all_pois)} / {total}")

        # 判断是否已翻完所有页
        if not pois or len(pois) < PAGE_SIZE or len(all_pois) >= total:
            break
        page += 1
        time.sleep(0.3)   # 避免触发限流

    print(f"   共获取海淀区小学 {len(all_pois)} 所\n")
    return all_pois

# ────────────────────────────────────────────
# 获取单个 POI 的边界（PlaceDetail）
# ────────────────────────────────────────────
def get_poi_detail(poi_id):
    """
    调用高德 PlaceDetail，extensions=all，尝试获取 polyline 字段。
    返回 detail 字典，或 None。
    """
    try:
        resp = requests.get(PLACE_DETAIL_URL, params={
            "key":        AMAP_KEY,
            "id":         poi_id,
            "output":     "json",
            "extensions": "all",
        }, timeout=10)
        data = resp.json()
        if data.get("status") == "1" and data.get("pois"):
            return data["pois"][0]
    except Exception:
        pass
    return None

# ────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  北京市海淀区小学矢量数据提取（高德地图 API）")
    print("  输出：GeoJSON + Shapefile（WGS-84）")
    print("=" * 60 + "\n")

    if not AMAP_KEY:
        print("ERROR: 未找到 AMAP_WEB_KEY 环境变量！")
        return
    print(f"API Key: {AMAP_KEY[:8]}...\n")

    # 步骤1：获取行政边界（用于最终校验）
    haidian_poly = get_haidian_boundary()

    # 步骤2：搜索所有小学
    pois = search_all_schools()
    if not pois:
        print("未获取到有效 POI，请检查 API Key 和网络。")
        return

    # 步骤3：逐一获取详情，尝试提取面状边界
    print(f"[步骤3] 获取各小学边界详情（共{len(pois)}所）...")
    records   = []
    poly_cnt  = 0
    point_cnt = 0

    for i, poi in enumerate(pois):
        poi_id = poi.get("id","")
        name   = poi.get("name","")
        addr   = poi.get("address","")
        adname = poi.get("adname","")
        tc     = poi.get("typecode","")
        loc    = poi.get("location","")

        print(f"  [{i+1:>3}/{len(pois)}] {name}", end="", flush=True)

        # 解析中心点坐标
        point_geom = None
        if loc:
            c = parse_location(loc)
            if c:
                point_geom = Point(gcj02_to_wgs84(*c))

        # 尝试获取多边形边界
        poly_geom = None
        detail = get_poi_detail(poi_id)
        if detail:
            polyline = detail.get("polyline","")
            if polyline:
                poly_geom = parse_polyline(polyline)

        # 优先面状边界，其次点位
        if poly_geom and not poly_geom.is_empty:
            geom = poly_geom
            gtype = "polygon"
            poly_cnt += 1
            print(" -> [面状边界]")
        elif point_geom:
            geom = point_geom
            gtype = "point"
            point_cnt += 1
            print(" -> [点位]")
        else:
            geom = None
            gtype = "none"
            print(" -> [无坐标]")

        records.append({
            "poi_id":    poi_id,
            "name":      name,
            "address":   addr,
            "district":  adname,
            "typecode":  tc,
            "geom_type": gtype,
            "geometry":  geom,
        })
        time.sleep(0.15)  # 礼貌性延迟

    # 过滤无效记录，创建 GeoDataFrame
    valid = [r for r in records if r["geometry"] is not None]
    gdf = gpd.GeoDataFrame(valid, geometry="geometry", crs="EPSG:4326")

    # 空间过滤（若有行政边界）
    if haidian_poly is not None:
        before = len(gdf)
        # 使用 intersects 而非 contains，避免误删跨边界学校
        mask = gdf.geometry.apply(lambda g: haidian_poly.intersects(g))
        gdf = gdf[mask]
        removed = before - len(gdf)
        if removed:
            print(f"\n空间过滤: 移除了{removed}个不在海淀区内的要素")

    # 去重（同名+同位置）
    gdf_dedup = gdf.drop_duplicates(subset=["poi_id"])
    if len(gdf_dedup) < len(gdf):
        print(f"去重: {len(gdf)} -> {len(gdf_dedup)}")
    gdf = gdf_dedup

    # ──── 保存输出 ────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # GeoJSON
    geojson_path = os.path.join(OUTPUT_DIR, "海淀小学_高德.geojson")
    gdf.to_file(geojson_path, driver="GeoJSON", encoding="utf-8")

    # Shapefile
    shp_dir  = os.path.join(OUTPUT_DIR, "海淀小学_SHP")
    os.makedirs(shp_dir, exist_ok=True)
    shp_path = os.path.join(shp_dir, "海淀小学_高德.shp")
    gdf.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")

    # 打印统计
    print("\n" + "=" * 60)
    print(f"  完成！共处理 {len(gdf)} 所海淀区小学")
    print(f"  面状边界: {(gdf['geom_type']=='polygon').sum()} 所")
    print(f"  点位数据: {(gdf['geom_type']=='point').sum()} 所")
    print(f"  坐标系  : EPSG:4326 (WGS-84)")
    print(f"  GeoJSON : {geojson_path}")
    print(f"  SHP目录 : {shp_dir}")
    print("=" * 60)

    print("\n前15条数据预览:")
    print(gdf[["name","district","typecode","geom_type"]].head(15).to_string(index=False))

if __name__ == "__main__":
    main()
