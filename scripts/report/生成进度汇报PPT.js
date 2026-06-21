const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "海淀小学绿地景观规划项目组";
pres.title = "海淀区小学绿地覆盖情况分析 - 进度汇报";

// ============================================================
// 配色（森林自然主题）
// ============================================================
const C = {
  forestGreen: "1B5E20",
  leafGreen: "388E3C",
  warmCream: "F8F4EF",
  white: "FFFFFF",
  dark: "2D2D2D",
  gray: "5A6A5A",
  lightGray: "9AAA9A",
  warmGold: "D4A843",
  redAccent: "C0392B",
  shadow: "000000",
};

// 工具函数
function mks() {
  return { type: "outer", blur: 6, offset: 2, angle: 135, opacity: 0.12, color: C.shadow };
}

// ============================================================
// 封面页
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.forestGreen };

  // 左上装饰圆
  s.addShape(pres.shapes.OVAL, { x: -0.8, y: -0.8, w: 3, h: 3, fill: { color: C.leafGreen, transparency: 50 } });
  // 右下装饰圆
  s.addShape(pres.shapes.OVAL, { x: 8, y: 3.5, w: 3.5, h: 3.5, fill: { color: C.leafGreen, transparency: 50 } });

  s.addText("海淀区小学绿地覆盖情况分析", {
    x: 0.8, y: 1.2, w: 8.5, h: 1.2,
    fontSize: 36, fontFace: "Microsoft YaHei", bold: true,
    color: C.white, align: "center",
  });
  s.addText("基于 GeoScene Pro + 通义千问视觉大模型的自动化分析", {
    x: 0.8, y: 2.5, w: 8.5, h: 0.5,
    fontSize: 16, fontFace: "Microsoft YaHei", color: C.lightGray, align: "center",
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 3.4, w: 3, h: 0.04, fill: { color: C.warmGold },
  });
  s.addText("进度汇报", {
    x: 0.8, y: 3.8, w: 8.5, h: 0.5,
    fontSize: 20, fontFace: "Microsoft YaHei", color: C.warmGold, align: "center",
  });
  s.addText("2026年5月", {
    x: 0.8, y: 4.8, w: 8.5, h: 0.4,
    fontSize: 14, fontFace: "Microsoft YaHei", color: C.lightGray, align: "center",
  });
}

// ============================================================
// 目录页
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.warmCream };

  s.addText("内容目录", {
    x: 0.8, y: 0.5, w: 8, h: 0.7,
    fontSize: 28, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: 1.15, w: 1.2, h: 0.04, fill: { color: C.warmGold },
  });

  const items = [
    { num: "01", title: "数据获取 —— 学校POI边界的前世今生" },
    { num: "02", title: "数据摸底 —— 北京中小学数量分布" },
    { num: "03", title: "GIS自动化 —— 缓冲区制作与批量截图" },
    { num: "04", title: "AI视觉分析 —— 千问大模型识别绿地" },
    { num: "05", title: "结果解读 —— 海淀小学绿地评价与建议" },
  ];

  items.forEach((item, i) => {
    const yBase = 1.6 + i * 0.75;
    s.addShape(pres.shapes.OVAL, {
      x: 1, y: yBase, w: 0.5, h: 0.5, fill: { color: C.forestGreen },
    });
    s.addText(item.num, {
      x: 1, y: yBase, w: 0.5, h: 0.5,
      fontSize: 14, fontFace: "Microsoft YaHei", bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(item.title, {
      x: 1.7, y: yBase + 0.02, w: 7, h: 0.5,
      fontSize: 16, fontFace: "Microsoft YaHei", color: C.dark, valign: "middle", margin: 0,
    });
  });
}

// ============================================================
// 第一章 数据获取
// ============================================================
// Slide 1.1: 数据获取方法探索
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("01  数据获取 — 学校POI边界的前世今生", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  s.addText("我们尝试了多种方法获取海淀区小学的用地边界数据：", {
    x: 0.6, y: 1.3, w: 8.8, h: 0.4,
    fontSize: 14, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  const cards = [
    {
      title: "方法一：高德API",
      sub: "Amap Web API",
      body: "通过POI搜索接口获取学校点位数据，但官方API只返回坐标点（Point），不返回用地边界多边形（Polygon），无法直接用于面域分析。",
      status: "❌ 只有点",
    },
    {
      title: "方法二：百度地图",
      sub: "Playwright + CDP 爬取",
      body: "利用 Playwright 浏览器自动化框架，从百度地图详情页的 profile_geo 字段中提取边界坐标。跑了143所学校，成功获取66所（46.2%），但大量学校无边界数据。",
      status: "⚠️ 部分成功",
    },
    {
      title: "方法三：OSM开源数据",
      sub: "OpenStreetMap",
      body: "从 OpenStreetMap 下载学校面数据，但缺失量大（海淀区仅覆盖约40%的学校），且几何精度参差不齐，部分边界明显偏移。",
      status: "⚠️ 覆盖不全",
    },
  ];

  cards.forEach((card, i) => {
    const xBase = 0.4 + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: xBase, y: 1.9, w: 2.9, h: 3.2, fill: { color: C.warmCream }, rectRadius: 0.15,
    });
    s.addText(card.title, {
      x: xBase + 0.2, y: 2.0, w: 2.5, h: 0.35,
      fontSize: 15, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
    });
    s.addText(card.sub, {
      x: xBase + 0.2, y: 2.3, w: 2.5, h: 0.3,
      fontSize: 11, fontFace: "Microsoft YaHei", color: C.lightGray, margin: 0,
    });
    s.addText(card.body, {
      x: xBase + 0.2, y: 2.7, w: 2.5, h: 1.7,
      fontSize: 11, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
    });
    s.addText(card.status, {
      x: xBase + 0.2, y: 4.55, w: 2.5, h: 0.35,
      fontSize: 12, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
    });
  });
}

// Slide 1.2: 淘宝购买 + AOI提取
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("01  数据获取 — 最终方案：购买现成数据", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  s.addText("免费数据源各自存在明显缺陷。最终我们在淘宝上花了10元购买了一份北京市中小学用地边界数据。", {
    x: 0.6, y: 1.3, w: 8.5, h: 0.5,
    fontSize: 14, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  const steps = [
    { label: "第1步", txt: "收到数据后，筛选出海淀区的记录，共277所中小学" },
    { label: "第2步", txt: "逐一核对学校的名称、地址，剔除重复项和疑似错误数据" },
    { label: "第3步", txt: "导出为 Shapefile 格式，作为 AOI 图层导入 GeoScene Pro" },
    { label: "第4步", txt: "确认 AOI 包含 name 字段，字段值为学校名称，可直接用于后续分析" },
  ];

  steps.forEach((st, i) => {
    const yBase = 2.0 + i * 0.7;
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: yBase + 0.05, w: 0.4, h: 0.4, fill: { color: C.forestGreen },
    });
    s.addText(st.label, {
      x: 0.6, y: yBase + 0.05, w: 0.4, h: 0.4,
      fontSize: 10, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.txt, {
      x: 1.2, y: yBase, w: 5.5, h: 0.5,
      fontSize: 13, fontFace: "Microsoft YaHei", color: C.dark, valign: "middle", margin: 0,
    });
  });

  // 右侧提示框
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.8, y: 1.8, w: 2.8, h: 3.2, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("给后来者的经验", {
    x: 7.0, y: 1.9, w: 2.4, h: 0.35,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "1. 高德/百度API只返回坐标点，想要边界多边形需要额外处理", options: { breakLine: true, fontSize: 11 } },
    { text: "2. OSM数据在国内城市覆盖不完整，不适合做精细分析", options: { breakLine: true, fontSize: 11 } },
    { text: "3. 百度地图 Profile_geo 字段虽有边界，但命中率仅46%", options: { breakLine: true, fontSize: 11 } },
    { text: "4. 淘宝数据性价比高，但需人工核对数据质量", options: { fontSize: 11 } },
  ], {
    x: 7.0, y: 2.3, w: 2.4, h: 2.5,
    fontFace: "Microsoft YaHei", color: C.gray, valign: "top", paraSpaceAfter: 6, margin: 0,
  });
}

// ============================================================
// 第二章 数量分布
// ============================================================
// Slide 2.1: 北京各区中小学数量表
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("02  数据摸底 — 北京中小学数量分布", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  s.addText("基于购买的现成数据，统计北京各区中小学数量如下：", {
    x: 0.6, y: 1.2, w: 8.5, h: 0.35,
    fontSize: 13, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  const tableRows = [
    [
      { text: "区县", options: { bold: true, color: C.white, fill: { color: C.forestGreen }, align: "center", fontSize: 11 } },
      { text: "中小学数量", options: { bold: true, color: C.white, fill: { color: C.forestGreen }, align: "center", fontSize: 11 } },
      { text: "占比(%)", options: { bold: true, color: C.white, fill: { color: C.forestGreen }, align: "center", fontSize: 11 } },
      { text: "排名", options: { bold: true, color: C.white, fill: { color: C.forestGreen }, align: "center", fontSize: 11 } },
    ],
    ["朝阳区", "345", "18.22", "1"],
    ["海淀区", "277", "14.63", "2"],
    ["丰台区", "164", "8.66", "3"],
    ["西城区", "145", "7.66", "4"],
    ["通州区", "131", "6.92", "5"],
    ["昌平区", "124", "6.55", "6"],
    ["大兴区", "119", "6.28", "7"],
    ["房山区", "116", "6.12", "8"],
    ["东城区", "109", "5.76", "9"],
    ["顺义区", "78", "4.12", "10"],
    ["密云区", "66", "3.48", "11"],
    ["石景山区", "55", "2.90", "12"],
    ["延庆区", "54", "2.85", "13"],
    ["怀柔区", "48", "2.53", "14"],
    ["门头沟区", "38", "2.01", "15"],
    ["平谷区", "25", "1.32", "16"],
    [
      { text: "合计", options: { bold: true } },
      { text: "1894", options: { bold: true } },
      { text: "100.00", options: { bold: true } },
      { text: "", options: { bold: true } },
    ],
  ];

  const fmtRows = tableRows.map((row, i) => {
    if (i === 0) return row;
    const bg = i % 2 === 0 ? { color: "F0EBE6" } : { color: C.warmCream };
    const isLast = i === tableRows.length - 1;
    return row.map(cell => {
      if (typeof cell === "string") {
        return { text: cell, options: { align: "center", fontSize: 10.5, fill: isLast ? { color: "E0D8CC" } : bg, color: isLast ? C.forestGreen : C.dark, bold: isLast } };
      }
      return { ...cell, options: { ...cell.options, align: "center", fontSize: 10.5, fill: bg } };
    });
  });

  s.addTable(fmtRows, {
    x: 0.6, y: 1.7, w: 5.5,
    colW: [1.5, 1.3, 1.2, 1.0],
    border: { pt: 0.5, color: "D0C8BC" },
    rowH: [0.4, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.4],
  });

  // 右侧分析框
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 6.4, y: 1.7, w: 3.2, h: 3.2, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("海淀区排名分析", {
    x: 6.6, y: 1.8, w: 2.8, h: 0.35,
    fontSize: 15, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "海淀区以277所中小学位列全市第二", options: { breakLine: true, bold: true, fontSize: 12 } },
    { text: "仅次于朝阳区（345所），占比14.63%", options: { breakLine: true, color: C.gray, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "海淀区作为北京的教育大区，中小学密度高、分布集中，这为我们后续的绿地分析提供了充足的样本基础", options: { breakLine: true, color: C.gray, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 6 } },
    { text: "我们选取了其中156所小学作为分析对象", options: { breakLine: true, bold: true, color: C.forestGreen, fontSize: 12 } },
  ], {
    x: 6.6, y: 2.2, w: 2.8, h: 2.5,
    fontFace: "Microsoft YaHei", valign: "top", paraSpaceAfter: 4, margin: 0,
  });

  s.addText("数据来源：淘宝购买的北京市中小学用地边界数据集 | 统计口径：含所有公/民办中小学", {
    x: 0.6, y: 5.0, w: 8.8, h: 0.3,
    fontSize: 10, fontFace: "Microsoft YaHei", color: C.lightGray, margin: 0,
  });
}

// ============================================================
// 第三章 GIS自动化
// ============================================================
// Slide 3.1: 缓冲区分析
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("03  GIS自动化 — 缓冲区制作与卫星截图导出", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  // 左：缓冲区说明
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.3, w: 4.5, h: 1.8, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("缓冲区（Buffer）设计", {
    x: 0.6, y: 1.4, w: 4, h: 0.3,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "内边界（绿线）", options: { bold: true, color: "2D8A4E", breakLine: true, fontSize: 12 } },
    { text: "学校用地边界（AOI）本身", options: { breakLine: true, color: C.gray, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 5 } },
    { text: "外缓冲（红线）", options: { bold: true, color: "C0392B", breakLine: true, fontSize: 12 } },
    { text: "学校外扩100米的范围，分析学校与周边环境的绿地衔接", options: { breakLine: true, color: C.gray, fontSize: 11 } },
    { text: "", options: { breakLine: true, fontSize: 5 } },
    { text: "分析目标", options: { bold: true, color: C.forestGreen, breakLine: true, fontSize: 12 } },
    { text: "对比绿线内侧、红绿线之间、红线内侧的绿地率差异", options: { color: C.gray, fontSize: 11 } },
  ], {
    x: 0.6, y: 1.75, w: 4.1, h: 1.3,
    fontFace: "Microsoft YaHei", valign: "top", paraSpaceAfter: 2, margin: 0,
  });

  // 右：GIS截图示例图
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.2, y: 1.3, w: 4.4, h: 1.8, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("卫星截图示意", {
    x: 5.4, y: 1.35, w: 4, h: 0.3,
    fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText("图层结构：\n底图：天地图卫星影像\n绿线：海淀区小学AOI_POI边界\n红线：小学buffer（100m缓冲）\n\n导出的 PNG 图片中同时保留\n绿线和红线，供 AI 识别", {
    x: 5.4, y: 1.7, w: 4, h: 1.3,
    fontSize: 11, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  // 下：ArcPy代码思路
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 3.3, w: 9.2, h: 2.1, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("ArcPy 自动化脚本代码思路（批量导出Buffer截图.py）", {
    x: 0.6, y: 3.4, w: 8.5, h: 0.3,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });

  const steps2 = [
    { title: "1. 建立映射表", desc: "遍历Buffer图层，通过质心坐标比较法（O(N²)→纯数值比较<1秒），将Buffer要素匹配到AOI的name字段" },
    { title: "2. 逐要素遍历", desc: "遍历Buffer的每个多边形，获取其extent并用expand_extent()外扩15%，避免红线紧贴图片边缘" },
    { title: "3. 设置相机", desc: "通过map_frame.camera.setExtent()将视图缩放至Buffer范围，适配GeoScene Pro 5.0的API差异" },
    { title: "4. 等待瓦片", desc: "卫星底图瓦片需异步加载，设置3秒延迟（TILE_LOAD_DELAY），首张导出后暂停30秒供人工检查" },
    { title: "5. 导出图片", desc: "exportToPNG()以 resolution=200 输出PNG，以学校名称命名，支持断点续传" },
  ];

  steps2.forEach((st, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const xBase = 0.6 + col * 3.05;
    const yBase = 3.8 + row * 0.85;
    s.addShape(pres.shapes.OVAL, {
      x: xBase, y: yBase + 0.05, w: 0.3, h: 0.3, fill: { color: C.leafGreen },
    });
    s.addText(String(i + 1), {
      x: xBase, y: yBase + 0.05, w: 0.3, h: 0.3,
      fontSize: 10, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.title, {
      x: xBase + 0.4, y: yBase + 0.03, w: 2.6, h: 0.3,
      fontSize: 11, fontFace: "Microsoft YaHei", bold: true, color: C.dark, valign: "middle", margin: 0,
    });
    s.addText(st.desc, {
      x: xBase + 0.4, y: yBase + 0.35, w: 2.6, h: 0.4,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
    });
  });

  s.addText("踩坑记录：arcpy.mp.Rectangle不存在 → 改用手动布局 | Python层 within() 太慢 → 改用extent坐标比较 | exportToPNG参数名是resolution而非dpi", {
    x: 0.6, y: 5.15, w: 8.5, h: 0.3,
    fontSize: 9, fontFace: "Microsoft YaHei", color: C.lightGray, margin: 0,
  });
}

// ============================================================
// 第四章 AI视觉分析
// ============================================================
// Slide 4.1: Qwen VL API 调用
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("04  AI视觉分析 — 通义千问大模型识别绿地", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  s.addText("调用阿里巴巴 DashScope 平台的 Qwen-VL-Max 视觉模型，对156张卫星截图进行批量分析。", {
    x: 0.6, y: 1.2, w: 8.8, h: 0.35,
    fontSize: 13, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  const flowSteps = [
    { title: "图片编码", desc: "将PNG截图转为Base64\nData URI格式传给API" },
    { title: "多模态理解", desc: "Qwen-VL同时识别\n图像中的绿线/红线区域" },
    { title: "结构化输出", desc: "模型返回JSON格式\n包含8个分析维度" },
    { title: "持久化存储", desc: "每完成1张即写盘\n支持断点续传" },
  ];
  flowSteps.forEach((st, i) => {
    const xBase = 0.4 + i * 2.4;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: xBase, y: 1.7, w: 2.2, h: 1.5, fill: { color: C.warmCream }, rectRadius: 0.12,
    });
    s.addText(st.title, {
      x: xBase + 0.15, y: 1.8, w: 1.9, h: 0.3,
      fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
    });
    s.addText(st.desc, {
      x: xBase + 0.15, y: 2.15, w: 1.9, h: 0.8,
      fontSize: 11, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
    });
    if (i < 3) {
      s.addText("→", {
        x: xBase + 2.2, y: 2.0, w: 0.3, h: 0.4,
        fontSize: 18, fontFace: "Microsoft YaHei", color: C.warmGold, align: "center", valign: "middle", margin: 0,
      });
    }
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 3.5, w: 9.2, h: 1.9, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("调用代码思路", {
    x: 0.6, y: 3.6, w: 3, h: 0.3,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "模型选择：", options: { bold: true, breakLine: true, fontSize: 11, color: C.dark } },
    { text: "qwen-vl-max-latest（精度最优），备选 qwen-vl-plus（速度更快）", options: { breakLine: true, fontSize: 10, color: C.gray } },
    { text: "并发策略：", options: { bold: true, breakLine: true, fontSize: 11, color: C.dark } },
    { text: "3线程并发，每请求间隔1秒，防止触发API QPS限制", options: { breakLine: true, fontSize: 10, color: C.gray } },
    { text: "重试机制：", options: { bold: true, breakLine: true, fontSize: 11, color: C.dark } },
    { text: "最多重试3次，限流时自动加长等待时间（指数退避）", options: { breakLine: true, fontSize: 10, color: C.gray } },
    { text: "耗时统计：", options: { bold: true, breakLine: true, fontSize: 11, color: C.dark } },
    { text: "156张图片共耗时约5分钟，全程零失败", options: { fontSize: 10, bold: true, color: C.forestGreen } },
  ], {
    x: 0.6, y: 3.95, w: 8.5, h: 1.3,
    fontFace: "Microsoft YaHei", valign: "top", margin: 0,
  });
}

// Slide 4.2: 示例输出
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("04  AI分析结果 — 单所学校输出示例", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  s.addText("以上地实验小学为例，模型输出的JSON结构如下：", {
    x: 0.6, y: 1.2, w: 8.5, h: 0.35,
    fontSize: 13, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.7, w: 5.5, h: 3.6, fill: { color: C.warmCream }, rectRadius: 0.12,
  });

  const jsonExample = `{
  "school_name": "上地实验小学",
  "green_rate_inside": "35%",
  "green_rate_total": "20%",
  "green_rate_outside": "15%",
  "overall_description": "校园内绿地覆盖较好，主要集中在操
    场周边及教学楼之间…",
  "overall_score": 7,
  "surroundings": "位于上地街道，周边为密集
    居民小区（上地东里）…",
  "standard_score": 8,
  "standard_score_reason": "依据GB/T 51356-2019，
    绿地率35%达标…",
  "location": "北京市海淀区上地街道",
  "notes": ""
}`;

  s.addText(jsonExample, {
    x: 0.55, y: 1.75, w: 5.2, h: 3.4,
    fontSize: 9.5, fontFace: "Consolas", color: C.dark, margin: 0,
  });

  const fields = [
    { label: "绿色率指标", items: ["green_rate_inside: 绿线内绿地率", "green_rate_total: 红线内总绿地率", "green_rate_outside: 红线内绿线外"] },
    { label: "评价与评分", items: ["overall_description: 综合描述", "overall_score: 直观评分(1-10)", "standard_score: 国标评分(1-10)"] },
    { label: "周边与备注", items: ["surroundings: 周边环境描述", "location: 学校位置（街道级）", "notes: 其他备注"] },
  ];

  fields.forEach((f, i) => {
    const yBase = 1.7 + i * 1.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 6.2, y: yBase, w: 3.4, h: 1.1, fill: { color: C.warmCream }, rectRadius: 0.1,
    });
    s.addText(f.label, {
      x: 6.35, y: yBase + 0.05, w: 3, h: 0.3,
      fontSize: 12, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
    });
    s.addText(f.items.join("\n"), {
      x: 6.35, y: yBase + 0.35, w: 3, h: 0.7,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
    });
  });
}

// ============================================================
// 第五章 结果分析
// ============================================================
// Slide 5.1: 总体评估
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("05  结果解读 — 海淀小学绿地总体情况", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  const kpis = [
    { val: "27.3%", label: "平均校内绿地率", sub: "（156所小学）", color: C.forestGreen },
    { val: "20.2%", label: "平均总体绿地率", sub: "（含100m缓冲区）", color: C.leafGreen },
    { val: "66.0%", label: "达标率", sub: "（绿地率≥30%的小学）", color: C.forestGreen },
  ];

  kpis.forEach((k, i) => {
    const xBase = 0.5 + i * 3.2;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: xBase, y: 1.3, w: 2.9, h: 1.3, fill: { color: C.warmCream }, rectRadius: 0.15,
    });
    s.addText(k.val, {
      x: xBase, y: 1.35, w: 2.9, h: 0.7,
      fontSize: 36, fontFace: "Microsoft YaHei", bold: true, color: k.color, align: "center", valign: "middle", margin: 0,
    });
    s.addText(k.label, {
      x: xBase, y: 2.05, w: 2.9, h: 0.3,
      fontSize: 12, fontFace: "Microsoft YaHei", color: C.dark, align: "center", margin: 0,
    });
    s.addText(k.sub, {
      x: xBase, y: 2.3, w: 2.9, h: 0.25,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.lightGray, align: "center", margin: 0,
    });
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 2.9, w: 9, h: 1.0, fill: { color: C.warmCream }, rectRadius: 0.12,
  });
  s.addText("评价标准", {
    x: 0.7, y: 2.95, w: 2, h: 0.3,
    fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "GB/T 51356-2019", options: { bold: true, breakLine: true, fontSize: 11 } },
    { text: "《绿色校园评价标准》：新建学校绿地率不低于30%，改建项目不低于30%（该标准要求新区≥35%正在征求意见中）", options: { breakLine: true, fontSize: 10, color: C.gray } },
    { text: "GB 50099-2011", options: { bold: true, breakLine: true, fontSize: 11 } },
    { text: "《中小学校设计规范》：学校应设置集中绿地，宽度不小于8米", options: { fontSize: 10, color: C.gray } },
  ], {
    x: 0.7, y: 3.25, w: 8.5, h: 0.6,
    fontFace: "Microsoft YaHei", valign: "top", paraSpaceAfter: 2, margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 4.1, w: 9, h: 1.3, fill: { color: C.warmCream }, rectRadius: 0.12,
  });
  s.addText("研究背景结合分析", {
    x: 0.7, y: 4.15, w: 3, h: 0.3,
    fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "国家政策层面：", options: { bold: true, fontSize: 10, color: C.dark } },
    { text: "2021年发改委等23部门联合发布《关于推进儿童友好城市建设的指导意见》，2022年住建部发布《城市儿童友好空间建设导则》，明确提出公园绿地适儿化改造。", options: { fontSize: 9.5, color: C.gray, breakLine: true } },
    { text: "已有研究表明海淀区绿地供给与儿童需求存在不匹配（卢可可，2021），社区公共空间在绿地系统方面普遍不足。我们的分析进一步证实：", options: { fontSize: 9.5, color: C.gray, breakLine: true } },
    { text: "海淀区小学平均绿地率27.3%，虽66%的学校达标，但仍有约1/3的小学绿地率不足30%，校园绿地供给存在显著的校际不均衡。", options: { fontSize: 9.5, bold: true, color: C.forestGreen } },
  ], {
    x: 0.7, y: 4.45, w: 8.5, h: 0.85,
    fontFace: "Microsoft YaHei", valign: "top", paraSpaceAfter: 2, margin: 0,
  });
}

// ============================================================
// Slide 5.2: 最好的学校 + 大图
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.warmCream };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("05  结果解读 — 绿地最好的3所小学", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  const bestSchools = [
    { name: "和平小学", score: 10, inside: "45%", total: "65%", desc: "绿地覆盖良好，周边有山林植被，形成良好生态基底" },
    { name: "中国人民大学附属小学", score: 9, inside: "35%", total: "28%", desc: "绿地布局均衡，植物种类丰富，乔灌木结合" },
    { name: "北京大学附属小学", score: 9, inside: "35%", total: "28%", desc: "绿化层次丰富，与颐和园、圆明园绿廊联动" },
  ];

  s.addText("📷 将对应学校的卫星截图拖入下方框内（共3张）", {
    x: 0.6, y: 1.1, w: 8.8, h: 0.3,
    fontSize: 11, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  // 每所学校一行：左侧信息 + 右侧大方图
  bestSchools.forEach((school, i) => {
    const yBase = 1.5 + i * 1.3;

    // 信息卡片（左侧）
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.3, y: yBase, w: 3.2, h: 1.1, fill: { color: C.white }, rectRadius: 0.12,
    });
    // 分数圆（左置）
    s.addShape(pres.shapes.OVAL, {
      x: 0.45, y: yBase + 0.1, w: 0.65, h: 0.65, fill: { color: C.forestGreen },
    });
    s.addText(String(school.score), {
      x: 0.45, y: yBase + 0.1, w: 0.65, h: 0.65,
      fontSize: 22, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    // 名称和绿地在分数圆旁边
    s.addText(school.name, {
      x: 1.2, y: yBase + 0.05, w: 2.1, h: 0.35,
      fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
    });
    s.addText("内 " + school.inside + " | 总 " + school.total, {
      x: 1.2, y: yBase + 0.4, w: 2.1, h: 0.3,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.leafGreen, margin: 0,
    });
    s.addText(school.desc, {
      x: 1.2, y: yBase + 0.7, w: 2.1, h: 0.35,
      fontSize: 9, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
    });

    // 右侧大方图（约原来的3倍大）
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 3.6, y: yBase, w: 6.0, h: 1.1, fill: { color: "E8E0D0" }, rectRadius: 0.12,
    });
    s.addText("📷 卫星截图待插入", {
      x: 3.6, y: yBase, w: 6.0, h: 1.1,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.lightGray, align: "center", valign: "middle", margin: 0,
    });
  });

  // 底部条
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.2, w: 10, h: 0.4, fill: { color: C.forestGreen } });
  s.addText("💡 这三所学校或周边有大型公园/山林，或校内绿地设计水平较高，值得作为标杆案例深入研究", {
    x: 0.6, y: 5.2, w: 8.8, h: 0.4,
    fontSize: 11, fontFace: "Microsoft YaHei", color: C.white, valign: "middle", margin: 0,
  });
}

// ============================================================
// Slide 5.3: 最差的学校 + 大图
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.warmCream };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("05  结果解读 — 绿地最需改善的3所小学", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  const worstSchools = [
    { name: "北安河中心小学（周家巷校区）", score: 4, inside: "10%", total: "5%-8%", desc: "建筑和硬质铺装为主，仅操场有少量植被" },
    { name: "和平小学（东埠头校区）", score: 4, inside: "10-15%", total: "5%-10%", desc: "硬化广场为主体，缺大面积草坪和林地" },
    { name: "第二实验小学（汇缘校区）", score: 4, inside: "10%", total: "5%-10%", desc: "绿地仅在建筑周边，外部为硬化地面" },
  ];

  s.addText("📷 将对应学校的卫星截图拖入下方框内（共3张）", {
    x: 0.6, y: 1.1, w: 8.8, h: 0.3,
    fontSize: 11, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
  });

  worstSchools.forEach((school, i) => {
    const yBase = 1.5 + i * 1.3;
    const isGreen = school.score >= 8;
    const scoreColor = C.forestGreen;
    const scoreBadge = C.redAccent;

    // 信息卡片
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.3, y: yBase, w: 3.2, h: 1.1, fill: { color: C.white }, rectRadius: 0.12,
    });
    s.addShape(pres.shapes.OVAL, {
      x: 0.45, y: yBase + 0.1, w: 0.65, h: 0.65, fill: { color: scoreBadge },
    });
    s.addText(String(school.score), {
      x: 0.45, y: yBase + 0.1, w: 0.65, h: 0.65,
      fontSize: 22, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(school.name, {
      x: 1.2, y: yBase + 0.05, w: 2.1, h: 0.35,
      fontSize: 12, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0,
    });
    s.addText("内 " + school.inside + " | 总 " + school.total, {
      x: 1.2, y: yBase + 0.4, w: 2.1, h: 0.3,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.redAccent, margin: 0,
    });
    s.addText(school.desc, {
      x: 1.2, y: yBase + 0.7, w: 2.1, h: 0.35,
      fontSize: 9, fontFace: "Microsoft YaHei", color: C.gray, margin: 0,
    });

    // 右侧大方图
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 3.6, y: yBase, w: 6.0, h: 1.1, fill: { color: "E8E0D0" }, rectRadius: 0.12,
    });
    s.addText("📷 卫星截图待插入", {
      x: 3.6, y: yBase, w: 6.0, h: 1.1,
      fontSize: 10, fontFace: "Microsoft YaHei", color: C.lightGray, align: "center", valign: "middle", margin: 0,
    });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.2, w: 10, h: 0.4, fill: { color: C.redAccent } });
  s.addText("💡 这三所学校绿地率不足15%，远低于国标要求的30%，建议优先纳入校园绿化改造计划", {
    x: 0.6, y: 5.2, w: 8.8, h: 0.4,
    fontSize: 11, fontFace: "Microsoft YaHei", color: C.white, valign: "middle", margin: 0,
  });
}

// ============================================================
// Slide 5.4: 改善建议
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.white };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 1, fill: { color: C.forestGreen } });
  s.addText("05  结果解读 — 总结与改善建议", {
    x: 0.6, y: 0.15, w: 8.5, h: 0.7,
    fontSize: 20, fontFace: "Microsoft YaHei", bold: true, color: C.white, margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 1.3, w: 4.5, h: 1.5, fill: { color: C.warmCream }, rectRadius: 0.12,
  });
  s.addText("当前绿地情况总结", {
    x: 0.6, y: 1.35, w: 4, h: 0.3,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "平均校内绿地率27.3%，距35%的新区标准仍有差距", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "66%的学校达标（绿地率≥30%），但约1/3不合格", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "得分最高的学校（和平小学10分）得益于周边山林", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "得分最低的学校（4分）均为城郊或紧凑型校区", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "校际差异显著，呈现\"城里不均衡、城外两极化\"", options: { fontSize: 11, bold: true, color: C.forestGreen } },
  ], {
    x: 0.6, y: 1.65, w: 4.1, h: 1.1,
    fontFace: "Microsoft YaHei", valign: "top", paraSpaceAfter: 3, margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.1, y: 1.3, w: 4.5, h: 1.5, fill: { color: C.warmCream }, rectRadius: 0.12,
  });
  s.addText("改善建议", {
    x: 5.3, y: 1.35, w: 4, h: 0.3,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });
  s.addText([
    { text: "对绿地率<15%的学校优先进行绿化改造", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "鼓励校园绿化与周边公园/绿道连通，形成绿网", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "新建校区应严格执行绿地率≥35%的标准", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "老旧校区通过立体绿化（屋顶、墙面）增加绿量", options: { breakLine: true, fontSize: 11, color: C.gray } },
    { text: "结合儿童友好城市政策，推动学径绿道建设", options: { fontSize: 11, bold: true, color: C.forestGreen } },
  ], {
    x: 5.3, y: 1.65, w: 4.1, h: 1.1,
    fontFace: "Microsoft YaHei", valign: "top", paraSpaceAfter: 3, margin: 0,
  });

  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.4, y: 3.1, w: 9.2, h: 1.6, fill: { color: C.warmCream }, rectRadius: 0.15,
  });
  s.addText("下一步工作展望", {
    x: 0.6, y: 3.15, w: 3, h: 0.3,
    fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.forestGreen, margin: 0,
  });

  const nextSteps = [
    { num: "1", txt: "将绿地率数据回填至GIS属性表，制作海淀区小学绿地率分布热力图" },
    { num: "2", txt: "结合学校周边用地类型（公园、道路、居住区），分析影响绿地率的关键因素" },
    { num: "3", txt: "对比不同街道/学区的绿地供给差异，识别绿地服务盲区" },
    { num: "4", txt: "参照儿童友好城市标准，提出分级分类的校园绿化改造策略" },
  ];

  nextSteps.forEach((st, i) => {
    const yBase = 3.55 + i * 0.28;
    s.addShape(pres.shapes.OVAL, {
      x: 0.6, y: yBase + 0.02, w: 0.22, h: 0.22, fill: { color: C.leafGreen },
    });
    s.addText(st.num, {
      x: 0.6, y: yBase + 0.02, w: 0.22, h: 0.22,
      fontSize: 9, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0,
    });
    s.addText(st.txt, {
      x: 1.0, y: yBase, w: 8.3, h: 0.28,
      fontSize: 11, fontFace: "Microsoft YaHei", color: C.dark, valign: "middle", margin: 0,
    });
  });

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.15, w: 10, h: 0.45, fill: { color: C.forestGreen } });
  s.addText("参考文献：Louv(2005)「自然缺失症」| 卢可可(2021)海淀区儿童友好研究 | GB/T 51356-2019《绿色校园评价标准》| GB 50099-2011《中小学校设计规范》", {
    x: 0.6, y: 5.15, w: 8.8, h: 0.45,
    fontSize: 9, fontFace: "Microsoft YaHei", color: C.white, valign: "middle", margin: 0,
  });
}

// ============================================================
// 结尾页
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.forestGreen };

  s.addShape(pres.shapes.OVAL, { x: -1, y: -0.5, w: 3, h: 3, fill: { color: C.leafGreen, transparency: 50 } });
  s.addShape(pres.shapes.OVAL, { x: 7.5, y: 3, w: 4, h: 4, fill: { color: C.leafGreen, transparency: 50 } });

  s.addText("谢谢！", {
    x: 0.8, y: 1.5, w: 8.5, h: 1,
    fontSize: 48, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center",
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 4, y: 2.6, w: 2, h: 0.04, fill: { color: C.warmGold },
  });
  s.addText("用数据 + AI 为儿童友好城市建设添砖加瓦", {
    x: 0.8, y: 3.0, w: 8.5, h: 0.5,
    fontSize: 16, fontFace: "Microsoft YaHei", color: C.lightGray, align: "center",
  });
}

// ============================================================
// 输出
// ============================================================
pres.writeFile({ fileName: "E:/学习资料/景观规划/海淀小学绿地/海淀小学绿地进度汇报.pptx" })
  .then(() => console.log("PPT 生成成功！"))
  .catch(err => console.error("PPT 生成失败:", err));
