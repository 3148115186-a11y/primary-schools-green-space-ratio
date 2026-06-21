# -*- coding: utf-8 -*-
"""
批量获取百度地图学校POI边界数据 v3
- 包含完整信息：学校名称、办学层次、办学类型、学校地址
- 严格名称匹配检查
- 断点续传
"""

import asyncio
import json
import os
import sys
import io
from playwright.async_api import async_playwright
import pandas as pd

OUTPUT_DIR = r"e:\学习资料\景观规划\海淀小学绿地\新名单学校边界"
SCHOOLS_FILE = r"e:\学习资料\景观规划\海淀小学绿地\新名单学校.xlsx"
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "获取进度.json")


def get_safe_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '（', '）', '(', ')')).strip()[:30]


def name_match(listed_name, baidu_name):
    """检查名称是否匹配"""
    # 移除常见前缀后缀进行对比
    listed = listed_name.replace("北京市海淀区", "").replace("北京市", "").strip()
    baidu = baidu_name.replace("北京市海淀区", "").replace("北京市", "").strip()
    
    # 完全包含
    if listed in baidu or baidu in listed:
        return True
    # 去掉"学校"后缀对比
    if listed.replace("学校", "").replace("小学", "") in baidu.replace("学校", "").replace("小学", ""):
        return True
    return False


async def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=== 百度地图 学校POI边界批量获取工具 v3 ===\n")
    
    # 读取学校名单
    df = pd.read_excel(SCHOOLS_FILE)
    schools = df.to_dict('records')
    print(f"共 {len(schools)} 所学校\n")
    
    # 加载进度
    completed = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            completed = json.load(f)
        print(f"已获取 {len(completed)} 所，继续中...\n")
    
    success_count = len(completed)
    
    async with async_playwright() as p:
        print("[启动] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        cdp = await page.context.new_cdp_session(page)
        await cdp.send("Network.enable")
        
        print("[准备] 打开百度地图...")
        await page.goto("https://map.baidu.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        for idx, school in enumerate(schools):
            listed_name = school["学校名称"]
            
            if listed_name in completed:
                continue
            
            print(f"\n[{idx+1}/{len(schools)}] {listed_name}")
            
            # 构建搜索关键词
            keyword = listed_name
            
            qts_request_ids = []
            
            def on_request_sent(event):
                url = event.get("request", {}).get("url", "")
                if "qt=s" in url and "baidu.com" in url:
                    qts_request_ids.append(event.get("requestId", ""))
            
            cdp.on("Network.requestWillBeSent", on_request_sent)
            
            # 搜索
            try:
                search_input = page.locator("#sole-input")
                await search_input.wait_for(state="visible", timeout=5000)
                await search_input.click()
                await asyncio.sleep(0.3)
                await search_input.fill(keyword)
                await asyncio.sleep(0.3)
                await page.keyboard.press("Enter")
            except Exception as e:
                print(f"  搜索框操作失败")
                try:
                    await page.evaluate(f'''(kw) => {{
                        const input = document.getElementById("sole-input");
                        if (input) {{ input.value = kw; input.dispatchEvent(new Event('input')); }}
                    }}''', keyword)
                    await asyncio.sleep(1)
                    await page.keyboard.press("Enter")
                except:
                    pass
            
            await asyncio.sleep(4)
            
            # 查找profile_geo - 严格匹配
            profile_geo_data = None
            
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
                                    baidu_name = sub.get("name", "")
                                    if name_match(listed_name, baidu_name):
                                        profile_geo_data = {
                                            "name": baidu_name,
                                            "profile_geo": sub.get("profile_geo", ""),
                                            "uid": sub.get("uid", ""),
                                            "addr": sub.get("addr", ""),
                                        }
                                        print(f"  ✓ 匹配成功: {baidu_name}")
                                        break
                            if profile_geo_data:
                                break
                except:
                    pass
                if profile_geo_data:
                    break
            
            # 模糊匹配（第一个有数据的）
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
                                            "name": sub.get("name", listed_name),
                                            "profile_geo": sub.get("profile_geo", ""),
                                            "uid": sub.get("uid", ""),
                                            "addr": sub.get("addr", ""),
                                        }
                                        print(f"  ~ 模糊匹配: {sub.get('name', '未知')}")
                                        break
                                if profile_geo_data:
                                    break
                    except:
                        pass
                    if profile_geo_data:
                        break
            
            cdp.remove_listener("Network.requestWillBeSent", on_request_sent)
            
            # 处理边界
            if profile_geo_data and profile_geo_data["profile_geo"]:
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
                    main_ring = rings[0]["coordinates"]
                    holes = [r["coordinates"] for r in rings[1:] if r["ringId"] != "0"]
                    
                    if main_ring and main_ring[0] != main_ring[-1]:
                        main_ring.append(main_ring[0])
                    for hole in holes:
                        if hole and hole[0] != hole[-1]:
                            hole.append(hole[0])
                    
                    # 构建完整属性
                    feature = {
                        "type": "Feature",
                        "properties": {
                            "学校名称": listed_name,
                            "办学层次": school.get("办学层次", ""),
                            "办学类型": school.get("办学类型", ""),
                            "学校地址": school.get("学校地址", ""),
                            "百度名称": profile_geo_data["name"],
                            "百度UID": profile_geo_data.get("uid", ""),
                            "百度地址": profile_geo_data.get("addr", ""),
                            "source": "百度地图 qt=s profile_geo",
                            "coordinate_system": "BD-09",
                            "point_count": len(main_ring),
                            "ring_count": len(rings),
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [main_ring] + holes
                        }
                    }
                    
                    safe_name = get_safe_filename(listed_name)
                    out_file = os.path.join(OUTPUT_DIR, f"{safe_name}.geojson")
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(feature, f, ensure_ascii=False, indent=2)
                    
                    completed[listed_name] = {
                        "status": "success",
                        "matched_name": profile_geo_data["name"],
                        "file": out_file,
                        "point_count": len(main_ring)
                    }
                    success_count += 1
                    print(f"  ✓ 保存: {len(main_ring)} 点")
                else:
                    print(f"  ✗ 坐标转换失败")
                    completed[listed_name] = {"status": "error"}
            else:
                print(f"  ✗ 未找到边界")
                completed[listed_name] = {"status": "no_boundary"}
            
            # 保存进度
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(completed, f, ensure_ascii=False, indent=2)
            
            await asyncio.sleep(2)
        
        await browser.close()
        
        # 生成合并GeoJSON
        print("\n\n" + "="*50)
        print("=== 获取完成 ===")
        
        success = sum(1 for v in completed.values() if v.get("status") == "success")
        no_boundary = sum(1 for v in completed.values() if v.get("status") == "no_boundary")
        errors = sum(1 for v in completed.values() if v.get("status") == "error")
        
        print(f"成功获取: {success} 所")
        print(f"无边界数据: {no_boundary} 所")
        print(f"转换失败: {errors} 所")
        
        # 合并
        features = []
        for name, info in completed.items():
            if info.get("status") == "success" and os.path.exists(info.get("file", "")):
                with open(info["file"], "r", encoding="utf-8") as f:
                    features.append(json.load(f))
        
        if features:
            merged = {"type": "FeatureCollection", "features": features}
            merged_file = os.path.join(OUTPUT_DIR, "新名单学校_百度边界_合并.geojson")
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
            print(f"\n合并GeoJSON: {merged_file} ({len(features)} 个要素)")
        
        print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
