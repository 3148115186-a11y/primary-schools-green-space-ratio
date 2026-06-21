# -*- coding: utf-8 -*-
"""生成海淀小学边界预览地图"""
import json
import os

OUTPUT_DIR = r"e:\学习资料\景观规划\海淀小学绿地\百度小学边界"

with open(os.path.join(OUTPUT_DIR, "海淀小学_百度边界_合并.geojson"), "r", encoding="utf-8") as f:
    geojson = json.load(f)

features = geojson["features"]
total_points = sum(f["properties"].get("point_count", 0) for f in features)
avg_points = total_points / len(features) if features else 0

# 生成学校列表HTML
school_items = ""
for i, f in enumerate(sorted(features, key=lambda x: x["properties"].get("original_name", ""))):
    props = f["properties"]
    coords = f["geometry"]["coordinates"][0][0] if f["geometry"]["coordinates"] and f["geometry"]["coordinates"][0] else [0, 0]
    school_items += f'''<div class="school-item" onclick="map.setView([{coords[1]}, {coords[0]}], 16); polygons[{i}].openPopup();">
        {props.get("original_name", "未知")} ({props.get("point_count", 0)}点)
    </div>'''

features_json = json.dumps(geojson, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>海淀小学边界预览 - 百度地图</title>
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
        .info-panel h3 {{ margin: 0 0 10px 0; color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 8px; }}
        .stat {{ display: flex; justify-content: space-between; }}
        .stat-label {{ color: #666; }}
        .stat-value {{ color: #4CAF50; font-weight: bold; }}
        #school-list {{
            max-height: 350px; overflow-y: auto; margin-top: 10px;
            border-top: 1px solid #eee; padding-top: 10px;
        }}
        .school-item {{
            padding: 5px 8px; margin: 2px 0; border-radius: 4px; cursor: pointer;
            font-size: 12px; transition: background 0.2s;
        }}
        .school-item:hover {{ background: #e8f5e9; }}
        .note {{ font-size: 11px; color: #999; margin-top: 5px; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>海淀小学边界数据</h3>
        <div class="stat"><span class="stat-label">获取学校:</span><span class="stat-value">{len(features)} 所</span></div>
        <div class="stat"><span class="stat-label">总坐标点:</span><span class="stat-value">{total_points} 点</span></div>
        <div class="stat"><span class="stat-label">平均点数:</span><span class="stat-value">{avg_points:.1f} 点/校</span></div>
        <div class="stat"><span class="stat-label">坐标系:</span><span class="stat-value">BD-09</span></div>
        <div class="stat"><span class="stat-label">数据来源:</span><span class="stat-value">百度地图</span></div>
        <div class="note">坐标系为BD-09（百度坐标系），在QGIS中使用需转换为WGS84</div>
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
            var color = '#4CAF50';
            var polygon = L.polygon(feature.geometry.coordinates[0], {{
                color: color,
                fillColor: color,
                fillOpacity: 0.3,
                weight: 2
            }}).addTo(map);
            
            polygon.bindPopup(
                '<b>' + (feature.properties.original_name || '未知') + '</b><br>' +
                '百度名称: ' + (feature.properties.name || '未知') + '<br>' +
                '坐标点: ' + (feature.properties.point_count || 0) + '<br>' +
                '地址: ' + (feature.properties.address || '未知') + '<br>' +
                '坐标系: BD-09'
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

with open(os.path.join(OUTPUT_DIR, "海淀小学_百度边界_预览.html"), "w", encoding="utf-8") as f:
    f.write(html)

print(f"预览已生成: {len(features)} 所学校的边界预览")
