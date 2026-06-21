# -*- coding: utf-8 -*-
"""
批量获取百度地图海淀小学 POI 边界数据 v2
- 支持断点续传
- 优化关键词匹配
- 去重处理
"""

import asyncio
import json
import os
import sys
import io
from playwright.async_api import async_playwright
import pandas as pd

OUTPUT_DIR = r"e:\学习资料\景观规划\海淀小学绿地\百度小学边界"
SCHOOLS_FILE = os.environ.get("SCHOOLS_FILE", "./北京海淀小学_TableToExcel.xlsx")  # 学校名单Excel
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "获取进度.json")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, "获取汇总.json")


def get_safe_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '（', '）', '(', ')')).strip()[:30]


async def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取学校名单
    print("=== 百度地图 海淀小学边界批量获取工具 v2 ===\n")
    df = pd.read_excel(SCHOOLS_FILE)
    
    # 去重并记录原始序号
    seen = set()
    schools = []
    for idx, row in df.iterrows():
        name = row["名称"]
        if name not in seen:
            seen.add(name)
            schools.append({
                "name": name,
                "lon": row["经度"],
                "lat": row["纬度"],
                "idx": len(schools) + 1
            })
    
    print(f"去重后共 {len(schools)} 所学校\n")
    
    # 加载进度（断点续传）
    completed = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            completed = json.load(f)
        print(f"已获取 {len(completed)} 所，继续中...\n")
    
    # 统计
    success_count = len(completed)
    fail_count = 0
    results = []
    
    async with async_playwright() as p:
        print("[启动] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        cdp = await page.context.new_cdp_session(page)
        await cdp.send("Network.enable")
        
        # 打开百度地图
        print("[准备] 打开百度地图...")
        await page.goto("https://map.baidu.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        for school in schools:
            school_name = school["name"]
            safe_name = get_safe_filename(school_name)
            
            # 跳过已完成的
            if school_name in completed:
                continue
            
            print(f"\n[{school['idx']}/{len(schools)}] 搜索: {school_name}")
            
            # 关键词优化：不用重复的"小学"
            keyword = f"北京海淀{school_name}"
            if not school_name.endswith("小学"):
                keyword += "小学"
            
            qts_request_ids = []
            
            def on_request_sent(event):
                url = event.get("request", {}).get("url", "")
                if "qt=s" in url and "baidu.com" in url:
                    qts_request_ids.append(event.get("requestId", ""))
            
            cdp.on("Network.requestWillBeSent", on_request_sent)
            
            # 执行搜索
            try:
                search_input = page.locator("#sole-input")
                await search_input.wait_for(state="visible", timeout=5000)
                await search_input.click()
                await asyncio.sleep(0.3)
                await search_input.fill(keyword)
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
            except Exception as e:
                print(f"  搜索框操作失败，尝试备用方式...")
                try:
                    await page.evaluate(f'''(kw) => {{
                        const input = document.getElementById("sole-input");
                        if (input) {{
                            input.value = kw;
                            input.dispatchEvent(new Event('input'));
                        }}
                    }}''', keyword)
                    await asyncio.sleep(1)
                    await page.keyboard.press("Enter")
                except:
                    pass
            
            await asyncio.sleep(4)
            
            # 查找profile_geo
            profile_geo_data = None
            
            for req_id in qts_request_ids:
                try:
                    body = await cdp.send("Network.getResponseBody", {"requestId": req_id})
                    body_text = body.get("body", "")
                    data = json.loads(body_text)
                    content = data.get("content", [])
                    
                    if isinstance(content, list):
                        # 优先找名称匹配的
                        for item in content:
                            items = item if isinstance(item, list) else [item]
                            for sub in items:
                                if isinstance(sub, dict) and sub.get("profile_geo"):
                                    name = sub.get("name", "")
                                    # 严格匹配：原始名称在百度名称中
                                    if school_name in name or name.replace("北京市海淀区", "").replace("小学", "") in school_name.replace("小学", ""):
                                        profile_geo_data = {
                                            "name": name,
                                            "profile_geo": sub.get("profile_geo", ""),
                                            "uid": sub.get("uid", ""),
                                            "addr": sub.get("addr", ""),
                                        }
                                        break
                            if profile_geo_data:
                                break
                except:
                    pass
                if profile_geo_data:
                    break
            
            # 如果没严格匹配，尝试模糊匹配第一个有数据的
            if not profile_geo_data:
                for req_id in qts_request_ids:
                    try:
                        body = await cdp.send("Network.getResponseBody", {"requestId": req_id})
                        body_text = body.get("body", "")
                        data = json.loads(body_text)
                        content = data.get("content", [])
                        
                        if isinstance(content, list):
                            for item in content:
                                items = item if isinstance(item, list) else [item]
                                for sub in items:
                                    if isinstance(sub, dict) and sub.get("profile_geo"):
                                        profile_geo_data = {
                                            "name": sub.get("name", school_name),
                                            "profile_geo": sub.get("profile_geo", ""),
                                            "uid": sub.get("uid", ""),
                                            "addr": sub.get("addr", ""),
                                        }
                                        break
                                if profile_geo_data:
                                    break
                    except:
                        pass
                    if profile_geo_data:
                        break
            
            cdp.remove_listener("Network.requestWillBeSent", on_request_sent)
            
            # 处理边界数据
            if profile_geo_data and profile_geo_data["profile_geo"]:
                print(f"  找到: {profile_geo_data['name']}")
                
                convert_result = await page.evaluate('''(profileGeo) => {
                    if (!window.map || typeof window.map.mercatorToLnglat !== 'function') {
                        return { error: 'mercatorToLnglat not available' };
                    }
                    
                    const parts = profileGeo.split("|");
                    const rings = [];
                    
                    for (let i = 2; i < parts.length; i++) {
                        const ringData = parts[i];
                        const dashIdx = ringData.indexOf('-');
                        if (dashIdx === -1) continue;
                        
                        const ringId = ringData.substring(0, dashIdx);
                        const coordsStr = ringData.substring(dashIdx + 1);
                        if (!coordsStr.trim()) continue;
                        
                        const lnglatCoords = [];
                        const semicolonCount = coordsStr.split(';').length - 1;
                        const commaCount = coordsStr.split(',').length - 1;
                        
                        if (semicolonCount === 0 || commaCount / Math.max(1, semicolonCount) > 3) {
                            const nums = coordsStr.split(',').map(s => s.trim()).filter(s => s);
                            for (let k = 0; k + 1 < nums.length; k += 2) {
                                const mcX = parseFloat(nums[k]);
                                const mcY = parseFloat(nums[k + 1]);
                                if (isNaN(mcX) || isNaN(mcY)) continue;
                                try {
                                    const result = window.map.mercatorToLnglat(mcX, mcY);
                                    const lng = Array.isArray(result) ? result[0] : result.lng;
                                    const lat = Array.isArray(result) ? result[1] : result.lat;
                                    if (lng != null && lat != null) {
                                        lnglatCoords.push([lng, lat]);
                                    }
                                } catch(e) {}
                            }
                        } else {
                            const pairs = coordsStr.split(";");
                            for (const pair of pairs) {
                                const commaIdx = pair.indexOf(',');
                                if (commaIdx === -1) continue;
                                const mcX = parseFloat(pair.substring(0, commaIdx));
                                const mcY = parseFloat(pair.substring(commaIdx + 1));
                                if (isNaN(mcX) || isNaN(mcY)) continue;
                                try {
                                    const result = window.map.mercatorToLnglat(mcX, mcY);
                                    const lng = Array.isArray(result) ? result[0] : result.lng;
                                    const lat = Array.isArray(result) ? result[1] : result.lat;
                                    if (lng != null && lat != null) {
                                        lnglatCoords.push([lng, lat]);
                                    }
                                } catch(e) {}
                            }
                        }
                        
                        if (lnglatCoords.length > 0) {
                            rings.push({ ringId: ringId, coordinates: lnglatCoords });
                        }
                    }
                    return { rings: rings, error: null };
                }''', profile_geo_data["profile_geo"])
                
                if not convert_result.get("error") and convert_result.get("rings"):
                    rings = convert_result["rings"]
                    print(f"  转换成功: {len(rings)} 个环, {len(rings[0]['coordinates'])} 点")
                    
                    main_ring = rings[0]["coordinates"]
                    holes = [r["coordinates"] for r in rings[1:] if r["ringId"] != "0"]
                    
                    if main_ring and main_ring[0] != main_ring[-1]:
                        main_ring.append(main_ring[0])
                    for hole in holes:
                        if hole and hole[0] != hole[-1]:
                            hole.append(hole[0])
                    
                    geojson = {
                        "type": "Feature",
                        "properties": {
                            "name": profile_geo_data["name"],
                            "original_name": school_name,
                            "uid": profile_geo_data.get("uid", ""),
                            "address": profile_geo_data.get("addr", ""),
                            "source": "百度地图 qt=s profile_geo",
                            "coordinate_system": "BD-09",
                            "point_count": len(main_ring),
                            "ring_count": len(rings),
                            "gdb_lon": school["lon"],
                            "gdb_lat": school["lat"],
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [main_ring] + holes
                        }
                    }
                    
                    out_file = os.path.join(OUTPUT_DIR, f"{safe_name}.geojson")
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(geojson, f, ensure_ascii=False, indent=2)
                    
                    completed[school_name] = {
                        "matched_name": profile_geo_data["name"],
                        "file": out_file,
                        "point_count": len(main_ring),
                        "status": "success"
                    }
                    success_count += 1
                    print(f"  已保存: {safe_name}.geojson")
                else:
                    print(f"  坐标转换失败")
                    completed[school_name] = {"status": "no_boundary"}
                    fail_count += 1
            else:
                print(f"  未找到边界数据")
                completed[school_name] = {"status": "no_boundary"}
                fail_count += 1
            
            # 保存进度
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(completed, f, ensure_ascii=False, indent=2)
            
            await asyncio.sleep(2)
        
        await browser.close()
        
        # 汇总
        print("\n\n" + "="*50)
        print("=== 获取完成 ===")
        print(f"成功获取: {sum(1 for v in completed.values() if v.get('status') == 'success')} 所")
        print(f"无边界数据: {sum(1 for v in completed.values() if v.get('status') == 'no_boundary')} 所")
        print(f"总计处理: {len(schools)} 所")
        
        # 生成合并GeoJSON
        merged_features = []
        for name, info in completed.items():
            if info.get("status") == "success" and os.path.exists(info.get("file", "")):
                with open(info["file"], "r", encoding="utf-8") as f:
                    merged_features.append(json.load(f))
        
        if merged_features:
            merged_geojson = {"type": "FeatureCollection", "features": merged_features}
            merged_file = os.path.join(OUTPUT_DIR, "海淀小学_百度边界_合并.geojson")
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(merged_geojson, f, ensure_ascii=False, indent=2)
            print(f"\n合并GeoJSON: {merged_file} ({len(merged_features)} 个要素)")
        
        print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
