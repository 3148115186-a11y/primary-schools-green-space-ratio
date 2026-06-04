# -*- coding: utf-8 -*-
"""
学校周边公园绿地可达性分析
==========================
1. WGS84坐标转GCJ02
2. 高德周边搜索3000m内公园(110101|110103)，本地筛选500m内数量
3. 高德步行路径规划计算实际距离和时间
4. 输出汇总表 + 明细表

使用方式：
1. 设置环境变量 AMAP_API_KEY 或修改下方 CONFIG
2. python 学校周边公园分析.py
"""

import csv, json, time, math, os, urllib.request

# =============================================
#  ⚙️ 配置
# =============================================

CONFIG = {
    # 高德地图API Key（优先读取环境变量）
    "api_key": os.environ.get("AMAP_API_KEY", "YOUR_AMAP_API_KEY_HERE"),

    # 输入：学校坐标CSV（需含 学校名称, 经度, 纬度 列）
    "school_csv": "../data/绿地率GIS数据.csv",

    # 输出目录
    "output_dir": "../data",

    # 搜索参数
    "search_radius": 3000,    # 搜索半径（米）
    "near_radius": 500,       # 500m筛选阈值（米）
    "max_walk_calc": 5,       # 每校最多计算步行距离的公园数
    "poi_types": "110101|110103",  # 公园|植物园

    # API调用间隔（秒），不超过3次/秒
    "api_delay": 0.35,
}


# =============================================
#  WGS84 → GCJ02 坐标转换
# =============================================

_a = 6378245.0
_ee = 0.00669342162296594323

def _out_of_china(lng, lat):
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)

def _transform_lat(x, y):
    ret = (-100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x)))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def _transform_lng(x, y):
    ret = (300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x)))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

def wgs84_to_gcj02(lng, lat):
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - _ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((_a * (1 - _ee)) / (magic * sqrtmagic) * math.pi)
    dlng = (dlng * 180.0) / (_a / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat


# =============================================
#  高德API调用
# =============================================

def gaode_get(url):
    """调用高德API，返回JSON"""
    time.sleep(CONFIG["api_delay"])
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  API错误: {e}")
        return None

def search_parks(api_key, lng, lat, radius, poi_types):
    """周边搜索公园"""
    url = (f"https://restapi.amap.com/v3/place/around"
           f"?key={api_key}&location={lng},{lat}&radius={radius}"
           f"&types={poi_types}&extensions=all")
    data = gaode_get(url)
    if data and data.get('status') == '1' and data.get('pois'):
        return data['pois']
    return []

def walking_distance(api_key, origin_lng, origin_lat, dest_lng, dest_lat):
    """步行路径规划"""
    url = (f"https://restapi.amap.com/v3/direction/walking"
           f"?key={api_key}"
           f"&origin={origin_lng},{origin_lat}"
           f"&destination={dest_lng},{dest_lat}")
    data = gaode_get(url)
    if data and data.get('status') == '1' and data.get('route'):
        paths = data['route'].get('paths', [])
        if paths:
            return int(paths[0].get('distance', 0)), int(paths[0].get('duration', 0))
    return None, None


# =============================================
#  主程序
# =============================================

def main():
    cfg = CONFIG
    api_key = cfg["api_key"]

    if api_key == "YOUR_AMAP_API_KEY_HERE":
        print("错误：请设置高德地图API Key")
        print("方式1：设置环境变量 AMAP_API_KEY")
        print("方式2：修改脚本中 CONFIG 的 api_key 字段")
        return

    print("=" * 60)
    print("  学校周边公园绿地可达性分析")
    print("=" * 60)

    # 读取学校坐标
    print("\n读取学校坐标...")
    schools = []
    with open(cfg["school_csv"], encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            wgs_lng = float(row['经度'])
            wgs_lat = float(row['纬度'])
            gcj_lng, gcj_lat = wgs84_to_gcj02(wgs_lng, wgs_lat)
            schools.append({
                'name': row['学校名称'],
                'wgs_lng': wgs_lng, 'wgs_lat': wgs_lat,
                'gcj_lng': gcj_lng, 'gcj_lat': gcj_lat,
                'rate_internal': row.get('校内绿地率', ''),
                'rate_external': row.get('外围绿地率', ''),
                'rate_combined': row.get('总体绿地率', ''),
                'category': row.get('所属类别', ''),
            })
    print(f"  共 {len(schools)} 所学校")

    # 逐校搜索 + 计算
    print(f"\n搜索半径{cfg['search_radius']}m，500m内筛选，每校最多{cfg['max_walk_calc']}个公园计算步行距离\n")
    all_details = []
    summary_rows = []

    for i, school in enumerate(schools, 1):
        gcj_lng, gcj_lat = school['gcj_lng'], school['gcj_lat']

        parks_raw = search_parks(api_key, gcj_lng, gcj_lat, cfg['search_radius'], cfg['poi_types'])

        parks = []
        for park in parks_raw:
            park_location = park.get('location', '')
            if not park_location:
                continue
            p_lng, p_lat = map(float, park_location.split(','))
            parks.append({
                'name': park.get('name', ''), 'type': park.get('type', ''),
                'lng': p_lng, 'lat': p_lat,
                'straight_dist': int(park.get('distance', 0)),
            })
        parks.sort(key=lambda x: x['straight_dist'])

        near_count = sum(1 for p in parks if p['straight_dist'] <= cfg['near_radius'])
        park_names_500 = [p['name'] for p in parks if p['straight_dist'] <= cfg['near_radius']]

        calc_parks = parks[:cfg['max_walk_calc']]
        park_details = []

        for park in calc_parks:
            dist, dur = walking_distance(api_key, gcj_lng, gcj_lat, park['lng'], park['lat'])
            is_near = park['straight_dist'] <= cfg['near_radius']
            park_details.append({
                'park_name': park['name'], 'distance': dist, 'duration': dur,
            })
            all_details.append({
                '学校名称': school['name'],
                '经度_GCJ02': f"{gcj_lng:.6f}", '纬度_GCJ02': f"{gcj_lat:.6f}",
                '公园名称': park['name'], '公园类型': park['type'],
                '公园经度': f"{park['lng']:.6f}", '公园纬度': f"{park['lat']:.6f}",
                '直线距离_米': park['straight_dist'],
                '步行距离_米': dist if dist is not None else '',
                '步行时间_秒': dur if dur is not None else '',
                '是否500m内': '是' if is_near else '否',
            })

        valid_parks = [p for p in park_details if p['distance'] is not None]
        if valid_parks:
            nearest = min(valid_parks, key=lambda x: x['distance'])
            nearest_name, nearest_dist, nearest_dur = nearest['park_name'], nearest['distance'], nearest['duration']
        else:
            nearest_name, nearest_dist, nearest_dur = '', '', ''

        summary_rows.append({
            '学校名称': school['name'],
            '经度_WGS84': f"{school['wgs_lng']:.6f}", '纬度_WGS84': f"{school['wgs_lat']:.6f}",
            '经度_GCJ02': f"{gcj_lng:.6f}", '纬度_GCJ02': f"{gcj_lat:.6f}",
            '500m内公园数量': near_count,
            '500m内公园名称': '; '.join(park_names_500) if park_names_500 else '',
            '最近公园名称': nearest_name,
            '最近公园步行距离_米': nearest_dist,
            '最近公园步行时间_秒': nearest_dur,
            '校内绿地率': school['rate_internal'],
            '外围绿地率': school['rate_external'],
            '总体绿地率': school['rate_combined'],
            '所属类别': school['category'],
        })

        if i % 20 == 0 or i == len(schools):
            print(f"  已处理 {i}/{len(schools)}")

    # 输出
    out = cfg['output_dir']
    summary_path = os.path.join(out, "学校公园汇总.csv")
    detail_path = os.path.join(out, "学校公园明细.csv")

    summary_cols = [
        '学校名称', '经度_WGS84', '纬度_WGS84', '经度_GCJ02', '纬度_GCJ02',
        '500m内公园数量', '500m内公园名称', '最近公园名称',
        '最近公园步行距离_米', '最近公园步行时间_秒',
        '校内绿地率', '外围绿地率', '总体绿地率', '所属类别',
    ]
    with open(summary_path, 'w', newline='', encoding='utf-8-sig') as f:
        csv.DictWriter(f, fieldnames=summary_cols, extrasaction='ignore').writerows(summary_rows)

    detail_cols = [
        '学校名称', '经度_GCJ02', '纬度_GCJ02',
        '公园名称', '公园类型', '公园经度', '公园纬度',
        '直线距离_米', '步行距离_米', '步行时间_秒', '是否500m内',
    ]
    with open(detail_path, 'w', newline='', encoding='utf-8-sig') as f:
        csv.DictWriter(f, fieldnames=detail_cols, extrasaction='ignore').writerows(all_details)

    print(f"\n[OK] {summary_path} ({len(summary_rows)}条)")
    print(f"[OK] {detail_path} ({len(all_details)}条)")

    has_park = sum(1 for r in summary_rows if r['500m内公园数量'] > 0)
    print(f"\n  500m内有公园: {has_park}/{len(schools)}所 ({has_park/len(schools)*100:.1f}%)")


if __name__ == "__main__":
    main()
