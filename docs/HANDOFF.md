# HANDOFF — 海淀小学绿地空间分析项目交接文档

> 生成时间：2026-05-27
> 项目路径：`E:\学习资料\景观规划\海淀小学绿地\`

---

## 一、项目概述

### 研究主题
北京市海淀区小学绿地空间覆盖率分析——基于卫星遥感图像与AI视觉模型（Qwen VL），结合GIS空间分析，依据 GB/T 51356-2019《绿色校园评价标准》与 GB 50099-2011《中小学校设计规范》进行评价。

### 核心结论

| 指标 | v1 (qwen-vl-max-latest) | v2 (qwen3-vl-plus + CoT) |
|------|--------------------------|---------------------------|
| 分析学校数 | 156所，零失败 | 156所，零失败 |
| 平均校内绿地率 | 27.3% | 36.9% |
| 平均总绿地率 | 20.2% | 30.5% |
| 平均外围绿地率 | — | 26.4% |
| 达标率（校内≥30%） | 66.0%（103所） | 89.7%（v2趋同问题严重） |
| 国标评分均值 | 7.17/10 | 7.7/10 |
| 5的倍数占比 | 94% | 0% |

### 关键发现：VLM趋同问题
**v2最大的问题是校内绿地率趋同**——137/156所学校给了38%，16所给了28%，3所给了32%，标准差仅3.1。根本原因：VLM不是逐像素计算，而是用"典型小学模板"套每张图。即使加了CoT区域分解提示词，reasoning质量不错但最终数值仍趋同。这是VLM的根本局限，不是提示词能解决的。

### 项目定位
这是一个风景园林专业的课程/论文项目，最终目标是产出海淀小学绿地空间分析的研究成果。

---

## 二、完整技术路线时间线

### Phase 1：高德API获取小学POI（4/22）
- **方法**：高德 Place Text API，`city=110108`（海淀区adcode）+ 关键词"小学"
- **结果**：224所小学POI，EPSG:4326
- **输出**：`海淀小学_高德.geojson`、`海淀小学_SHP/海淀小学_高德.shp`
- **脚本**：`获取高德小学点位.py`、`获取海淀小学边界.py`
- **注意**：高德免费Web Key无法获取面状边界（polyline字段），仅能获取点位

### Phase 2：OSM/Overpass API获取学校边界（4/23）
- **方法**：直接调Overpass API（绕过osmnx 2.1.0的投影NaN bug），查`amenity=school` + `building=school`
- **原始结果**：1751个面状要素
- **后处理**：500m阈值空间过滤 → 344个多边形 → 与GDB 180所点位匹配
- **覆盖率**：106/180 = 58.9%有面状多边形
- **输出**：`海淀小学_OSM边界_精炼.geojson`、`海淀小学_OSM_SHP/`
- **脚本**：`获取OSM学校边界.py`、`后处理_筛选小学多边形.py`
- **参考数据**：`E:\学习资料\景观规划\北京\北京.gdb` → `北京海淀小学`图层（180所Point）

### Phase 3：百度地图Playwright获取边界（4/29）
- **方法**：Playwright + CDP网络拦截捕获百度地图 qt=s 接口响应，提取profile_geo字段
- **结果**：143所学校中66所有边界（46.2%），20所无边界
- **输出**：`百度小学边界/海淀小学_百度边界_合并.geojson`（BD-09坐标系）
- **脚本**：`批量获取百度小学边界_v2.py`（支持断点续传）
- **配套**：`转换坐标.py`（BD-09→WGS84）、`生成预览.py`（Leaflet预览地图）

### Phase 4：最终数据来源——淘宝购买
- 三种API路线（高德/OSM/百度）均无法完整覆盖，最终通过淘宝10元购买了完整的AOI边界数据
- 导入GeoScene Pro后图层名：`海淀区小学AOI_POI边界`

### Phase 5：GeoScene Pro Buffer与截图导出（5/5）
- **Buffer设计**：红线=学校边界外扩100m，绿线=学校边界
- **截图导出**：ArcPy布局导出法，遍历"小学buffer"图层每个要素
- **导出参数**：DPI=200，EXPAND_RATIO=1.15，瓦片加载等待3秒
- **输出**：`导出截图/` 文件夹，156张PNG
- **脚本**：`批量导出Buffer截图.py`（v4版本，经多次bug修复）
- **GeoScene Pro项目图层**：
  - Buffer图层：`小学buffer`
  - AOI图层：`海淀区小学AOI_POI边界`
  - AOI名称字段：`name`
  - 布局名称：`布局`

### Phase 6：Qwen VL v1分析（5/5）
- **模型**：qwen-vl-max-latest
- **方法**：base64 data URI传图（DashScope不支持file:// URI）
- **输出**：`绿地分析结果.json`
- **问题**：94%结果为5的倍数（35%出现66次，15%出现47次，30%出现34次），精度不足
- **脚本**：`分析小学绿地覆盖.py`
- **并发**：3线程，断点续传

### Phase 7：Qwen VL v2精确分析（5/20）
- **模型**：qwen3-vl-plus
- **改进**：CoT区域分解估算法——强制模型将区域划分为8-12子区块，逐块估算绿地占比再加权求和
- **输出**：`绿地分析结果_v2.json`
- **全量运行**：分8轮跑完156张（免费额度中途耗尽，开启付费补跑剩余14所）
- **最终结果**：156/156全部成功，0失败
- **核心问题**：校内绿地率趋同严重（137/156给了38%），模型仍未真正逐像素计算
- **脚本**：`分析小学绿地覆盖_v2.py`

### Phase 8：可视化与文档（5/5-5/20）
- **散点分布图**：`绿地率分布图.png`（v1版）、`绿地率分布图_v2.png`（v2版）
  - 校内绿地率 vs 缓冲区绿地率，颜色=综合评分
  - 含防重叠标签算法，标注13-15所关键学校
  - 四象限分类：双优型/自足型/外部补偿型/双低型
- **截图分类**：`截图分类/` 文件夹，按四象限分类复制
  - 高高(65张)、高低(72张)、低高(14张)、低低(0张)
- **脚本**：`plot_green_rates_v2.py`、`classify_screenshots.py`
- **进度汇报PPT**：`海淀小学绿地进度汇报.pptx`（13页，深海蓝#122E8A+柔奶白#F5EFEA配色）

---

## 三、核心数据文件清单

### 分析结果
| 文件 | 说明 |
|------|------|
| `绿地分析结果.json` | v1分析结果（qwen-vl-max-latest，含%号和区间） |
| `绿地分析结果_v2.json` | v2分析结果（qwen3-vl-plus，纯整数，含reasoning字段） |
| `绿地分析结果_位置补全.json` | v1 + 百度搜索补全地址后的版本 |

### 空间数据
| 文件/目录 | 说明 |
|-----------|------|
| `海淀小学_高德.geojson` | 高德API点位数据，224所，EPSG:4326 |
| `海淀小学_高德API.geojson` | 高德API + 逆地理编码，180所，GCJ-02 |
| `海淀小学_OSM边界_精炼.geojson` | OSM面状边界，344个Polygon，EPSG:4326 |
| `海淀小学_OSM_SHP/` | OSM边界Shapefile版本 |
| `海淀小学_GDB参考点位.geojson` | GDB 180所参考点位 |
| `海淀小学_OSM未覆盖点位.geojson` | 74所无OSM多边形的小学 |
| `百度小学边界/海淀小学_百度边界_合并.geojson` | 百度边界，66所，BD-09 |
| `百度小学边界/海淀小学_百度边界_WGS84.geojson` | 百度边界转WGS84 |
| `百度小学边界/获取进度.json` | 百度边界断点续传记录 |

### 截图与分类
| 文件/目录 | 说明 |
|-----------|------|
| `导出截图/` | GeoScene Pro导出的156张PNG卫星截图（2339×1654 RGBA） |
| `截图分类/` | 按四象限分类的截图（高高/高低/低高/低低） |
| `绿地率分布图.png` | v1散点分布图 |
| `绿地率分布图_v2.png` | v2散点分布图 |

### PPT与文档
| 文件 | 说明 |
|------|------|
| `海淀小学绿地进度汇报.pptx` | 13页进度汇报PPT |
| `社媒评论与优秀案例参考.pptx` | 社媒评论PPT（非本核心项目） |

---

## 四、关键配置与API密钥

### DashScope（阿里云通义千问）
- **API Key**：`sk-651e731dc3ec488daa05bb29cd5f30ff`（硬编码在脚本CONFIG中）
- **v1模型**：`qwen-vl-max-latest`
- **v2模型**：`qwen3-vl-plus`
- **注意**：v2运行时免费额度中途耗尽，需开启付费模式
- **传图方式**：base64 data URI（`data:image/png;base64,xxx`），DashScope不支持`file://`URI

### 高德地图
- **Web API Key**：`c66216a7f29a3317b9489aab2ed24acc`
- **坐标系**：GCJ-02
- **逆地理编码API**：`https://restapi.amap.com/v3/geocode/regeo`
- **关键词搜索API**：`https://restapi.amap.com/v3/place/text`

### GeoScene Pro / ArcGIS Pro
- 项目使用 GeoScene Pro 5.0
- Buffer图层名：`小学buffer`
- AOI图层名：`海淀区小学AOI_POI边界`
- AOI名称字段：`name`
- 布局名称：`布局`
- Buffer图层字段：OBJECTID, Shape, osm_id, code, fclass, name(空), ref, oneway, maxspeed, layer, bridge, tunnel, Shape_Length

### 坐标系
- **WGS-84 / EPSG:4326**：高德API、OSM、最终分析用
- **GCJ-02**：高德原始坐标（需注意偏移）
- **BD-09**：百度地图坐标（需转换为WGS84后使用）
- **UTM 50N / EPSG:32650**：距离计算投影坐标系
- 转换工具：`转换坐标.py`（使用coordTransform库，BD-09→GCJ-02→WGS84）

---

## 五、脚本清单与功能说明

| 脚本 | 功能 | 运行方式 |
|------|------|----------|
| `获取高德小学点位.py` | 高德API获取小学POI + 逆地理编码补全地址 | `python 获取高德小学点位.py` |
| `获取OSM学校边界.py` | Overpass API获取学校面状边界 + GDB名称匹配 | `python 获取OSM学校边界.py` |
| `后处理_筛选小学多边形.py` | 从1751个OSM要素中筛选小学相关多边形 | `python 后处理_筛选小学多边形.py` |
| `批量导出Buffer截图.py` | ArcPy遍历Buffer图层导出截图（需在GeoScene Pro中运行） | Pro Python窗口 |
| `分析小学绿地覆盖.py` | Qwen VL v1批量分析绿地率 | `python 分析小学绿地覆盖.py` |
| `分析小学绿地覆盖_v2.py` | Qwen VL v2精确分析（CoT区域分解法） | `python 分析小学绿地覆盖_v2.py` |
| `plot_green_rates_v2.py` | 生成散点分布图 | `python plot_green_rates_v2.py` |
| `classify_screenshots.py` | 按四象限分类截图 | `python classify_screenshots.py` |
| `补全学校位置.py` | 百度搜索补全学校地址 | `python 补全学校位置.py` |
| `转换坐标.py` | BD-09→WGS84坐标转换 | `python 转换坐标.py` |
| `生成预览.py` | 生成Leaflet预览地图 | `python 生成预览.py` |

---

## 六、待办/下一步建议

### 最紧迫：VLM趋同问题解决方案
v2的校内绿地率87.8%都给了38%，基本失去区分度。可选方案：

1. **像素级语义分割（最推荐）**：用SAM+SegFormer等模型做真正的绿地/非绿地像素分类
   - 之前评估过本地无GPU，建议用Google Colab免费T4 GPU
   - 需要：PyTorch + segment_anything + transformers + opencv
   - 优势：真正的定量分析，精度远高于VLM估算

2. **HSV色彩分割+形态学（轻量方案）**：在本地用OpenCV做绿色像素检测
   - 优势：无需GPU，速度快
   - 劣势：精度一般，受阴影/季节/色差影响大

3. **Hugging Face Inference API（云端方案）**：调用云端分割模型
   - 优势：无需本地GPU
   - 劣势：有速率限制，大量图片处理慢

4. **接受VLM定性结果**：将绿地率作为定性/半定量指标，搭配描述性分析
   - 保留v1的数据分布更合理（27.3%均值），但精度低
   - v2的reasoning字段（逐区块分析过程）质量不错，可以提取定性信息

### 其他优化项
- [ ] 补全v2数据的学校地址（目前v1有位置补全版，v2没有）
- [ ] 将v2的reasoning字段提取为定性评价指标（如"操场为主型""教学楼密集型"等）
- [ ] 制作最终论文级图表（空间分布热力图、分区统计等）
- [ ] 撰写论文正文

---

## 七、用户偏好与注意事项

### 数字准确性
- 对数字准确性极其敏感，错误必须立即核实修改
- 无法确认的数据要求删除，不留"大约""可能"的模糊表述
- 对学术工作要求极高标准：逻辑、证据、事实、引文均不能有任何瑕疵

### 写作风格
- 偏好人类化写作风格，无AI痕迹
- 中文标点用弯引号
- 简短回复，对多个问题常只回应部分
- 偏好实际解决方案，快速在选项间做决定

### 可视化偏好
- 迭代优化：关注颜色对比度和标签可读性，要求标签不重叠
- 偏好深色系专业配色（如PPT用深海蓝+柔奶白）

### 工作习惯
- 偏好先做后说，不要反复确认
- 偏好系统化的表格总结和结构化报告

---

## 八、踩坑经验汇总

### ArcPy / GeoScene Pro
- `arcpy.mp.Rectangle` 在 GeoScene Pro 5.0 不存在 → 用 `arcpy.Extent` 替代
- Python层 `within()` 多边形空间匹配 O(N²) → 卡死数分钟 → 改用 extent 坐标比较法（纯数值运算<1秒）
- `input()` 在 Pro Python窗口不支持交互 → 改用 `time.sleep()` 暂停
- `SpatialJoin_analysis` 在 GeoScene Pro 中 field_map 参数不兼容 → 放弃SpatialJoin
- `exportToPNG()` 参数名是 `resolution` 不是 `dpi`（GeoScene Pro API差异）
- Buffer图层的 `name` 字段值可能全空（OSM继承），需检测非空率再决定是否使用

### DashScope / Qwen VL
- DashScope API 不接受 `file://` URI，报 400 InvalidParameter → 改用 base64 data URI
- VLM对绿地率有整5%偏好（v1: 94%为5的倍数），即使CoT提示词也无法消除趋同倾向
- 免费额度有限，156张图用v2模型跑了8轮才完成，中途需开启付费
- `NoneType.__format__` 会导致失败项线程崩溃 → 改用安全格式化函数

### OSM / Overpass
- osmnx 2.1.0 的 `features_from_place/bbox` 存在投影NaN bug → 直接调 Overpass API
- OSM数据覆盖率有限：海淀区仅58.9%的小学有面状边界
- 需要后处理过滤非小学要素（原始1751个→精炼344个）

### 坐标系
- 高德坐标是GCJ-02，百度是BD-09，分析时需统一为WGS84
- 转换链：BD-09 → GCJ-02 → WGS84（使用coordTransform库）
- 在QGIS/ArcGIS中使用百度数据前必须先转换坐标系

### 百度地图Playwright
- 百度地图 qt=s 接口的 profile_geo 字段是百度墨卡托坐标，需用百度内置的 `mercatorToLnglat()` 转换
- 支持断点续传（`获取进度.json`记录已处理学校）
- 覆盖率46.2%，不如OSM

---

## 九、建议接手Agent使用的技能

1. **qwen-vision**：如需继续使用Qwen VL分析图片
2. **mineru / pdf**：如需解析论文PDF
3. **pptx-generator / pptx**：如需修改PPT
4. **agent-browser**：如需爬取网页数据
5. **scholar-search-skills**：如需搜索学术文献

---

## 十、参考数据源

| 数据 | 路径 |
|------|------|
| 北京GDB（含海淀小学参考点位） | `E:\学习资料\景观规划\北京\北京.gdb` → 图层`北京海淀小学` |
| 海淀小学Excel名单 | `E:\WeChat\xwechat_files\wxid_m764tm39behb22_2b0b\msg\file\2026-04\北京海淀小学_TableToExcel.xlsx` |
