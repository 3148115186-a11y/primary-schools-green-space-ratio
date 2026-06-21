# -*- coding: utf-8 -*-
"""
批量获取百度地图海淀小学 POI 边界数据

基于 fetch_yesanpo_boundary.py 的经验，批量处理180所小学：
1. Playwright + CDP 捕获 qt=s 响应
2. 提取 profile_geo 字段
3. mercatorToLnglat 转换坐标
4. 输出 GeoJSON
"""

import asyncio
import json
import os
import sys
import io
import time
from playwright.async_api import async_playwright
import pandas as pd

# 配置
OUTPUT_DIR = r"e:\学习资料\景观规划\海淀小学绿地\百度小学边界"
SCHOOLS_FILE = os.environ.get("SCHOOLS_FILE", "./北京海淀小学_TableToExcel.xlsx")  # 学校名单Excel

# 搜索关键词前缀（提高搜索精度）
SEARCH_PREFIX = "北京海淀"  # 或 "北京市海淀区"
SEARCH_SUFFIX = "小学"


async def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取学校名单
    print("=== 百度地图 海淀小学边界批量获取工具 ===\n")
    df = pd.read_excel(SCHOOLS_FILE)
    schools = df["名称"].tolist()
    print(f"共加载 {len(schools)} 所学校\n")
    
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
        
        # 结果统计
        success_count = 0
        fail_count = 0
        no_boundary_count = 0
        results = []
        
        for idx, school_name in enumerate(schools):
            keyword = f"{SEARCH_PREFIX}{school_name}{SEARCH_SUFFIX}"
            print(f"\n[{idx+1}/{len(schools)}] 搜索: {keyword}")
            
            # 清空CDP记录
            qts_request_ids = []
            cdp_data_file = os.path.join(OUTPUT_DIR, f"cdp_{idx}_{school_name[:8]}.json")
            
            def on_request_sent(event):
                url = event.get("request", {}).get("url", "")
                if "qt=s" in url and "baidu.com" in url:
                    req_id = event.get("requestId", "")
                    qts_request_ids.append(req_id)
            
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
                print(f"  搜索框操作失败: {e}")
                search_url = f"https://map.baidu.com/search/{keyword}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            
            await asyncio.sleep(4)
            
            # 尝试获取CDP数据
            profile_geo_data = None
            
            for req_id in qts_request_ids:
                try:
                    body = await cdp.send("Network.getResponseBody", {"requestId": req_id})
                    body_text = body.get("body", "")
                    
                    try:
                        data = json.loads(body_text)
                        content = data.get("content", [])
                        
                        if isinstance(content, list):
                            # 遍历查找 profile_geo
                            for item in content:
                                if isinstance(item, list):
                                    for sub in item:
                                        if isinstance(sub, dict) and sub.get("profile_geo"):
                                            # 名称匹配检查
                                            name = sub.get("name", "")
                                            if school_name in name or name in keyword:
                                                profile_geo_data = {
                                                    "name": name,
                                                    "profile_geo": sub.get("profile_geo", ""),
                                                    "uid": sub.get("uid", ""),
                                                    "addr": sub.get("addr", ""),
                                                }
                                                break
                                elif isinstance(item, dict) and item.get("profile_geo"):
                                    name = item.get("name", "")
                                    if school_name in name or name in keyword:
                                        profile_geo_data = {
                                            "name": name,
                                            "profile_geo": item.get("profile_geo", ""),
                                            "uid": item.get("uid", ""),
                                            "addr": item.get("addr", ""),
                                        }
                                        break
                                if profile_geo_data:
                                    break
                    except json.JSONDecodeError:
                        pass
                except Exception as e:
                    pass
            
            cdp.remove_listener("Network.requestWillBeSent", on_request_sent)
            
            # 如果没找到，尝试模糊匹配任意有profile_geo的结果
            if not profile_geo_data:
                for req_id in qts_request_ids:
                    try:
                        body = await cdp.send("Network.getResponseBody", {"requestId": req_id})
                        body_text = body.get("body", "")
                        try:
                            data = json.loads(body_text)
                            content = data.get("content", [])
                            
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, list):
                                        for sub in item:
                                            if isinstance(sub, dict) and sub.get("profile_geo"):
                                                profile_geo_data = {
                                                    "name": sub.get("name", school_name),
                                                    "profile_geo": sub.get("profile_geo", ""),
                                                    "uid": sub.get("uid", ""),
                                                    "addr": sub.get("addr", ""),
                                                }
                                                break
                                    elif isinstance(item, dict) and item.get("profile_geo"):
                                        profile_geo_data = {
                                            "name": item.get("name", school_name),
                                            "profile_geo": item.get("profile_geo", ""),
                                            "uid": item.get("uid", ""),
                                            "addr": item.get("addr", ""),
                                        }
                                        break
                                    if profile_geo_data:
                                        break
                        except:
                            pass
                    except:
                        pass
                    if profile_geo_data:
                        break
            
            # 处理profile_geo
            if profile_geo_data and profile_geo_data["profile_geo"]:
                print(f"  找到边界数据: {profile_geo_data['name']}")
                
                # 坐标转换
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
                        
                        if (semicolonCount === 0 || commaCount / (semicolonCount + 1) > 3) {
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
                    print(f"  转换成功: {len(rings)} 个环")
                    
                    # 构建 GeoJSON
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
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [main_ring] + holes
                        }
                    }
                    
                    # 保存单个文件
                    safe_name = "".join(c for c in school_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    out_file = os.path.join(OUTPUT_DIR, f"{safe_name}.geojson")
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(geojson, f, ensure_ascii=False, indent=2)
                    
                    success_count += 1
                    results.append({
                        "name": school_name,
                        "status": "success",
                        "matched_name": profile_geo_data["name"],
                        "point_count": len(main_ring),
                        "file": out_file
                    })
                    print(f"  已保存: {safe_name}.geojson")
                else:
                    print(f"  坐标转换失败")
                    no_boundary_count += 1
                    results.append({"name": school_name, "status": "no_boundary"})
            else:
                print(f"  未找到边界数据")
                no_boundary_count += 1
                results.append({"name": school_name, "status": "no_boundary"})
            
            # 反爬间隔
            await asyncio.sleep(2)
        
        await browser.close()
        
        # 生成汇总报告
        print("\n\n=== 获取完成 ===")
        print(f"成功获取: {success_count} 所")
        print(f"无边界数据: {no_boundary_count} 所")
        print(f"总计处理: {len(schools)} 所")
        
        # 保存汇总
        summary_file = os.path.join(OUTPUT_DIR, "获取汇总.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "total": len(schools),
                "success": success_count,
                "no_boundary": no_boundary_count,
                "results": results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n汇总已保存: {summary_file}")
        
        # 生成合并的GeoJSON
        merged_features = []
        for r in results:
            if r["status"] == "success" and os.path.exists(r["file"]):
                with open(r["file"], "r", encoding="utf-8") as f:
                    feature = json.load(f)
                    merged_features.append(feature)
        
        if merged_features:
            merged_geojson = {"type": "FeatureCollection", "features": merged_features}
            merged_file = os.path.join(OUTPUT_DIR, "海淀小学_百度边界_合并.geojson")
            with open(merged_file, "w", encoding="utf-8") as f:
                json.dump(merged_geojson, f, ensure_ascii=False, indent=2)
            print(f"合并GeoJSON已保存: {merged_file}")


if __name__ == "__main__":
    asyncio.run(main())
