"""
获取海淀区小学点位数据（高德API）
- 读取Excel名单中的小学名称和坐标
- 通过高德逆地理编码API（坐标→地址信息）获取高德官方数据
- 输出JSON和SHP格式
- 最终坐标以Excel原始坐标为准（已验证准确）
"""

import os
import json
import time
import requests
import pandas as pd
from pathlib import Path

# 高德API配置
AMAP_KEY = os.environ.get('AMAP_WEB_KEY', '')  # 请设置环境变量 AMAP_WEB_KEY
# 逆地理编码API（通过坐标获取地址信息）
REGEOCODE_URL = "https://restapi.amap.com/v3/geocode/regeo"
# 关键词搜索API（备用，用于没有坐标的情况）
SEARCH_URL = "https://restapi.amap.com/v3/place/text"

# 输出目录
OUTPUT_DIR = Path("e:/学习资料/景观规划/海淀小学绿地")
OUTPUT_JSON = OUTPUT_DIR / "海淀小学_高德API.json"
OUTPUT_GEOJSON = OUTPUT_DIR / "海淀小学_高德API.geojson"
OUTPUT_SHP_DIR = OUTPUT_DIR / "海淀小学_高德API_SHP"

# Excel名单路径（坐标来源）
XLSX_PATH = os.environ.get("SCHOOLS_FILE", "./北京海淀小学_TableToExcel.xlsx")  # 学校名单Excel

# 高德请求头
HEADERS = {"User-Agent": "Mozilla/5.0"}


def regeocode(lon, lat):
    """调用高德逆地理编码API，通过坐标获取地址信息"""
    params = {
        "key": AMAP_KEY,
        "location": f"{lon},{lat}",
        "extensions": "all",
        "output": "json",
        "radius": 100
    }
    try:
        resp = requests.get(REGEOCODE_URL, params=params, headers=HEADERS, timeout=10)
        data = resp.json()
        if data.get("status") == "1" and data.get("regeocode"):
            rg = data["regeocode"]
            addr = rg.get("addressComponent", {})
            road = rg.get("roads", [])
            poi = rg.get("pois", [])
            return {
                "province": addr.get("province", ""),
                "city": addr.get("city", ""),
                "district": addr.get("district", ""),
                "township": addr.get("township", ""),
                "neighborhood": addr.get("neighborhood", ""),
                "building": addr.get("building", ""),
                "streetNumber": addr.get("streetNumber", ""),
                "formatted_address": rg.get("formatted_address", ""),
                "nearest_road": road[0]["name"] if road else "",
                "nearest_poi": poi[0]["name"] if poi else "",
            }
    except Exception as e:
        print(f"  [ERROR regeocode] ({lon},{lat}): {e}")
    return {}


def search_school_exact(name):
    """精确搜索学校POI，优先返回POI类型为"小学"的结果"""
    params = {
        "key": AMAP_KEY,
        "keywords": name,
        "city": "海淀区",
        "citylimit": "true",
        "output": "json",
        "offset": 10,
        "page": 1,
        "types": "141201"  # 小学
    }
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
        data = resp.json()
        if data.get("status") == "1" and data.get("pois"):
            for poi in data["pois"]:
                if poi["name"] == name or name in poi["name"]:
                    return poi
            return data["pois"][0]
    except Exception:
        pass
    return None


def main():
    # 1. 读取Excel名单（坐标来源）
    print("=" * 60)
    print("读取Excel名单（坐标来源）...")
    df = pd.read_excel(XLSX_PATH)
    print(f"共 {len(df)} 所小学，坐标完整性检查:")
    print(f"  经度缺失: {df['经度'].isna().sum()}")
    print(f"  纬度缺失: {df['纬度'].isna().sum()}")
    print(f"  名称缺失: {df['名称'].isna().sum()}")

    results = []
    api_hits = 0
    
    print(f"\n{'=' * 60}")
    print(f"开始处理（共{len(df)}所）...")
    print(f"策略: Excel坐标 + 高德逆地理编码API补全地址信息")
    print(f"{'=' * 60}\n")

    for idx, row in df.iterrows():
        name = row["名称"]
        lon = float(row["经度"])
        lat = float(row["纬度"])
        
        # 高德逆地理编码：坐标→地址信息
        geo_info = regeocode(lon, lat)
        api_hits += 1
        
        # 格式化地址
        street_num = geo_info.get("streetNumber", {})
        street = street_num.get("street", "") if isinstance(street_num, dict) else ""
        number = street_num.get("number", "") if isinstance(street_num, dict) else ""
        
        record = {
            "id": int(row["OBJECTID"]),
            "名称": name,
            "经度": lon,
            "纬度": lat,
            "省份": geo_info.get("province", "北京市"),
            "城市": geo_info.get("city", "北京市"),
            "区县": geo_info.get("district", "海淀区"),
            "街道": geo_info.get("township", ""),
            "formatted_address": geo_info.get("formatted_address", ""),
            "nearest_road": geo_info.get("nearest_road", ""),
            "nearest_poi": geo_info.get("nearest_poi", ""),
            "坐标系": "GCJ-02"
        }
        results.append(record)
        
        print(f"[{idx+1:3d}/{len(df)}] {name:<30s} → {geo_info.get('formatted_address', 'N/A')}")
        
        # 限速：每秒最多5次
        time.sleep(0.2)
    
    print(f"\n{'=' * 60}")
    print(f"完成！API调用次数: {api_hits}，记录总数: {len(results)}")
    print(f"{'=' * 60}")
    
    # 2. 输出JSON
    print("\n[输出] JSON...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  → {OUTPUT_JSON}")
    
    # 3. 输出GeoJSON
    print("[输出] GeoJSON...")
    features = []
    for r in results:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [r["经度"], r["纬度"]]
            },
            "properties": {
                "id": r["id"],
                "name": r["名称"],
                "district": r["区县"],
                "formatted_address": r["formatted_address"],
                "street": r["街道"],
                "nearest_road": r["nearest_road"],
                "nearest_poi": r["nearest_poi"],
                "coord_sys": r["坐标系"]
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "name": "海淀区小学点位",
        "count": len(features),
        "properties": {
            "description": "海淀区全部小学点位数据，坐标来源为Excel原始数据（经验证准确），地址信息来自高德逆地理编码API"
        },
        "features": features
    }
    with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"  → {OUTPUT_GEOJSON}")
    
    # 4. 输出SHP（使用geopandas）
    print("[输出] SHP (ESRI Shapefile)...")
    OUTPUT_SHP_DIR.mkdir(exist_ok=True)
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        
        gdf = gpd.GeoDataFrame(
            [{
                "id": r["id"],
                "name": r["名称"],
                "district": r["区县"],
                "address": r["formatted_address"],
                "street": r["街道"][:100] if r["街道"] else "",
                "nearest_rd": r["nearest_road"][:100] if r["nearest_road"] else "",
                "nearest_poi": r["nearest_poi"][:100] if r["nearest_poi"] else "",
                "lon": r["经度"],
                "lat": r["纬度"],
                "coord_sys": r["坐标系"]
            } for r in results],
            geometry=[Point(r["经度"], r["纬度"]) for r in results],
            crs="EPSG:4326"
        )
        
        shp_base = str(OUTPUT_SHP_DIR / "海淀小学_高德API")
        gdf.to_file(shp_base, driver="ESRI Shapefile", encoding="utf-8")
        print(f"  → {shp_base}.shp")
        
        # 输出.prj（WGS84）
        prj_path = str(OUTPUT_SHP_DIR / "海淀小学_高德API.prj")
        with open(prj_path, "w", encoding="utf-8") as f:
            f.write(
                'GEOGCS["GCS_WGS_1984",'
                'DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                'PRIMEM["Greenwich",0.0],'
                'UNIT["Degree",0.0174532925199433]]'
            )
        print(f"  → {prj_path}")
        
    except Exception as e:
        print(f"  [ERROR] SHP输出失败: {e}")
    
    print(f"\n{'=' * 60}")
    print("=== 全部完成 ===")
    print(f"  JSON:     {OUTPUT_JSON}")
    print(f"  GeoJSON: {OUTPUT_GEOJSON}")
    print(f"  SHP:     {OUTPUT_SHP_DIR}/")
    print(f"  总计:    {len(results)} 所小学")
    print(f"{'=' * 60}")
    
    return results


if __name__ == "__main__":
    main()
