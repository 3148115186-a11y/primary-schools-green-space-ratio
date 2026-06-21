# -*- coding: utf-8 -*-
"""
将百度地图边界数据(BD-09)转换为WGS84坐标系
使用coordTransform库进行转换
"""
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 尝试导入坐标转换库
try:
    from coordTransform.py_coord_transform import gcj02_to_wgs84, bd09_to_gcj02
    HAS_TRANSFORM = True
except ImportError:
    try:
        from coordTransform import gcj02_to_wgs84, bd09_to_gcj02
        HAS_TRANSFORM = True
    except ImportError:
        print("未找到coordTransform库，尝试安装...")
        os.system("pip install coordTransform -q")
        try:
            from coordTransform.py_coord_transform import gcj02_to_wgs84, bd09_to_gcj02
            HAS_TRANSFORM = True
        except:
            print("安装失败，将输出原始BD-09坐标")
            HAS_TRANSFORM = False

def bd09_to_wgs84(bd_lng, bd_lat):
    """BD-09转WGS84"""
    if not HAS_TRANSFORM:
        return bd_lng, bd_lat
    # BD-09 -> GCJ-02 -> WGS84
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    wgs_lng, wgs_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
    return wgs_lng, wgs_lat

def convert_feature_coords(feature):
    """转换单个要素的坐标"""
    if feature["geometry"]["type"] == "Polygon":
        new_coords = []
        for ring in feature["geometry"]["coordinates"]:
            new_ring = []
            for coord in ring:
                wgs_lng, wgs_lat = bd09_to_wgs84(coord[0], coord[1])
                new_ring.append([wgs_lng, wgs_lat])
            new_coords.append(new_ring)
        feature["geometry"]["coordinates"] = new_coords
        
    feature["properties"]["coordinate_system"] = "WGS84"
    feature["properties"]["original_coordinate_system"] = "BD-09"
    return feature

OUTPUT_DIR = r"e:\学习资料\景观规划\海淀小学绿地\百度小学边界"
INPUT_FILE = os.path.join(OUTPUT_DIR, "海淀小学_百度边界_合并.geojson")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "海淀小学_百度边界_WGS84.geojson")

print("=== 坐标转换: BD-09 → WGS84 ===\n")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    geojson = json.load(f)

converted_features = []
for feature in geojson["features"]:
    converted = convert_feature_coords(feature)
    converted_features.append(converted)

converted_geojson = {
    "type": "FeatureCollection",
    "features": converted_features
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(converted_geojson, f, ensure_ascii=False, indent=2)

print(f"转换完成: {len(converted_features)} 个要素")
print(f"输出文件: {OUTPUT_FILE}")

if HAS_TRANSFORM:
    # 生成WGS84预览
    import re
    
    school_items = ""
    for i, f in enumerate(sorted(converted_features, key=lambda x: x["properties"].get("original_name", ""))):
        props = f["properties"]
        coords = f["geometry"]["coordinates"][0][0] if f["geometry"]["coordinates"] and f["geometry"]["coordinates"][0] else [0, 0]
        school_items += f'''<div class="school-item" onclick="map.setView([{coords[1]}, {coords[0]}], 16); polygons[{i}].openPopup();">
            {props.get("original_name", "未知")} ({props.get("point_count", 0)}点)
        </div>'''
    
    features_json = json.dumps(converted_geojson, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>海淀小学边界预览 - WGS84</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: "Microsoft YaHei", sans-serif; }}
        #map {{ width: 100vw; height: 100vh; }}
        .info-panel {{
            position: absolute; top: 10px; right: 10px; z-index: 1000;
            background: white; padding: 15px 20px; border-radius: 10px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.25); max-width: 300px;
            font-size: 13px; line-height: 1.8;
        }}
        .info-panel h3 {{ margin: 0 0 10px 0; color: #333; border-bottom: 2px solid #2196F3; padding-bottom: 8px; }}
        .stat {{ display: flex; justify-content: space-between; }}
        .stat-label {{ color: #666; }}
        .stat-value {{ color: #2196F3; font-weight: bold; }}
        #school-list {{
            max-height: 350px; overflow-y: auto; margin-top: 10px;
            border-top: 1px solid #eee; padding-top: 10px;
        }}
        .school-item {{
            padding: 5px 8px; margin: 2px 0; border-radius: 4px; cursor: pointer;
            font-size: 12px; transition: background 0.2s;
        }}
        .school-item:hover {{ background: #e3f2fd; }}
        .note {{ font-size: 11px; color: #999; margin-top: 5px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>海淀小学边界数据 (WGS84)</h3>
        <div class="stat"><span class="stat-label">获取学校:</span><span class="stat-value">{len(converted_features)} 所</span></div>
        <div class="stat"><span class="stat-label">坐标系:</span><span class="stat-value">WGS84</span></div>
        <div class="note">已从BD-09转换为WGS84，可直接叠加卫星影像和OSM底图</div>
        <div id="school-list">
            <div style="color:#666;font-size:11px;margin-bottom:5px;">点击学校名称定位:</div>
{school_items}
        </div>
    </div>
    <script>
        var geojsonData = {features_json};
        var polygons = [];
        
        var map = L.map('map').setView([39.98, 116.31], 12);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap',
            maxZoom: 18
        }}).addTo(map);
        
        geojsonData.features.forEach(function(feature, idx) {{
            var color = '#2196F3';
            var polygon = L.polygon(feature.geometry.coordinates[0], {{
                color: color,
                fillColor: color,
                fillOpacity: 0.3,
                weight: 2
            }}).addTo(map);
            
            polygon.bindPopup(
                '<b>' + (feature.properties.original_name || '未知') + '</b><br>' +
                '坐标点: ' + (feature.properties.point_count || 0) + '<br>' +
                '地址: ' + (feature.properties.address || '未知') + '<br>' +
                '坐标系: WGS84'
            );
            polygons.push(polygon);
        }});
        
        if (polygons.length > 0) {{
            var group = L.featureGroup(polygons);
            map.fitBounds(group.getBounds().pad(0.1));
        }}
    </script>
</body>
</html>'''
    
    preview_file = os.path.join(OUTPUT_DIR, "海淀小学_百度边界_预览_WGS84.html")
    with open(preview_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"预览已生成: {preview_file}")
else:
    print("\n注意: 未安装coordTransform库，无法转换坐标")
    print("请手动安装: pip install coordTransform")
