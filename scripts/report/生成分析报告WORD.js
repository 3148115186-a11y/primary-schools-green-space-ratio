const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, TableOfContents
} = require("docx");

const cellM = { top: 60, bottom: 60, left: 100, right: 100 };
const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };

function cell(text, opts) {
  opts = opts || {};
  return new TableCell({
    borders, width: { size: opts.w || 2000, type: WidthType.DXA },
    shading: opts.fill ? { fill: opts.fill, type: ShadingType.CLEAR } : undefined,
    margins: cellM, verticalAlign: "center",
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.CENTER,
      children: [new TextRun({ text, bold: !!opts.bold, size: opts.size || 20, font: "Microsoft YaHei", color: opts.color || "333333" })]
    })]
  });
}

function P(text, opts) {
  opts = opts || {};
  return new Paragraph({
    spacing: { after: opts.after || 80 },
    children: [new TextRun({ text, size: opts.size || 22, bold: !!opts.bold, italics: !!opts.italics, color: opts.color, font: "Microsoft YaHei" })]
  });
}

function H1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, font: "Microsoft YaHei" })] });
}
function H2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, font: "Microsoft YaHei" })] });
}
function H3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, font: "Microsoft YaHei" })] });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 40 },
    children: [new TextRun({ text, size: 22, font: "Microsoft YaHei" })]
  });
}

function numItem(text) {
  return new Paragraph({
    numbering: { reference: "numbers", level: 0 },
    spacing: { after: 60 },
    children: [new TextRun({ text, size: 22, font: "Microsoft YaHei" })]
  });
}

function makeTable(headers, rows) {
  const headerRow = new TableRow({
    children: headers.map(h =>
      cell(h.text, { w: h.w, bold: true, fill: "1B5E20", color: "FFFFFF", size: 20, align: h.align || AlignmentType.CENTER })
    )
  });
  const dataRows = rows.map((row, i) =>
    new TableRow({
      children: row.map(v => {
        const colIdx = row.indexOf(v);
        const w = headers[colIdx] ? headers[colIdx].w : 2000;
        return cell(v.text, { w, fill: i % 2 === 0 ? "F8F4EF" : "FFFFFF", size: v.size || 20, bold: v.bold, color: v.color, align: v.align || AlignmentType.CENTER });
      })
    })
  );
  const fullWidth = headers.reduce((s, h) => s + h.w, 0);
  return new Table({ width: { size: fullWidth, type: WidthType.DXA }, columnWidths: headers.map(h => h.w), rows: [headerRow, ...dataRows] });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Microsoft YaHei", size: 22, color: "333333" } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Microsoft YaHei", color: "1B5E20" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Microsoft YaHei", color: "388E3C" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Microsoft YaHei", color: "1B5E20" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 },
          margin: { top: 1440, right: 1440, bottom:1440, left:1440 }
        }
      },
      children: [
        new Paragraph({ spacing: { before: 4000 } }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
          children: [new TextRun({ text: "\u6d77\u6dc0\u533a\u5c0f\u5b66\u7eff\u5730\u8986\u76d6\u60c5\u51b5\u5206\u6790", size: 52, bold: true, color: "1B5E20", font: "Microsoft YaHei" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
          children: [new TextRun({ text: "\u57fa\u4e8e GeoScene Pro + \u901a\u4e49\u5343\u95ee\u89c6\u89c9\u5927\u6a21\u578b\u7684\u81ea\u52a8\u5316\u5206\u6790", size: 26, color: "666666", font: "Microsoft YaHei" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 600 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "D4A843", space: 1 } },
          children: [new TextRun({ text: " ", size: 12 })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
          children: [new TextRun({ text: "\u8fdb\u5ea6\u6c47\u62a5", size: 28, color: "388E3C", font: "Microsoft YaHei" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "2026\u5e745\u6708", size: 22, color: "999999", font: "Microsoft YaHei" })] }),
        new Paragraph({ children: [new PageBreak()] }),
      ]
    },
    {
      properties: {
        page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D4A843", space: 4 } },
            children: [new TextRun({ text: "\u6d77\u6dc0\u5c0f\u5b66\u7eff\u5730\u666f\u89c2\u89c4\u5212\u9879\u76ee\u7ec4", size: 16, color: "999999", font: "Microsoft YaHei" })]
          })]
        })
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: "D4A843", space: 4 } },
            children: [
              new TextRun({ text: "\u7b2c ", size: 18, color: "999999", font: "Microsoft YaHei" }),
              new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "999999" }),
              new TextRun({ text: " \u9875", size: 18, color: "999999", font: "Microsoft YaHei" }),
            ]
          })]
        })
      },
      children: [
        // TOC
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: "\u76ee\u5f55", font: "Microsoft YaHei" })] }),
        new TableOfContents("\u76ee\u5f55", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({ children: [new PageBreak()] }),

        // Chapter 1: Data Acquisition
        H1("\u4e00\u3001\u6570\u636e\u83b7\u53d6\u2014\u2014\u5b66\u6821POI\u8fb9\u754c\u7684\u524d\u4e16\u4eca\u751f"),

        H2("1.1 \u6570\u636e\u83b7\u53d6\u7684\u63a2\u7d22\u8def\u5f84"),

        P("\u8981\u5206\u6790\u6d77\u6dc0\u533a\u5c0f\u5b66\u7684\u7eff\u5730\u8986\u76d6\u60c5\u51b5\uff0c\u9996\u5148\u9700\u8981\u6bcf\u6240\u5c0f\u5b66\u7684\u7528\u5730\u8fb9\u754c\u6570\u636e\uff08AOI\uff09\u3002\u6211\u4eec\u5148\u540e\u5c1d\u8bd5\u4e86\u4e09\u79cd\u6570\u636e\u6e90\uff1a"),

        H3("\u65b9\u6cd5\u4e00\uff1a\u9ad8\u5fb7\u5730\u56fe API"),

        P("\u9ad8\u5fb7\u5730\u56fe\u63d0\u4f9b\u4e86 Web API \u63a5\u53e3\uff0c\u53ef\u4ee5\u901a\u8fc7 POI \u641c\u7d22\u63a5\u53e3\u83b7\u53d6\u5b66\u6821\u7684\u57fa\u7840\u4fe1\u606f\u3002\u8fd9\u4e2a\u65b9\u6848\u4e0a\u624b\u5feb\u3001\u6587\u6863\u9f50\u5168\uff0c\u7b2c\u4e00\u6b21\u8c03\u7528\u5c31\u6210\u529f\u8fd4\u56de\u4e86\u6570\u636e\u5217\u8868\u3002\u4f46\u95ee\u9898\u5f88\u5feb\u5c31\u66b4\u9732\u4e86\uff1a\u5b98\u65b9 API \u53ea\u8fd4\u56de\u5750\u6807\u70b9\uff08Point\uff09\uff0c\u4e0d\u8fd4\u56de\u7528\u5730\u8fb9\u754c\u591a\u8fb9\u5f62\uff08Polygon\uff09\u3002\u6ca1\u6709\u8fb9\u754c\u5c31\u65e0\u6cd5\u8ba1\u7b97\u7eff\u5730\u7387\u2014\u2014\u6211\u4eec\u9700\u8981\u77e5\u9053\u5b66\u6821\u201c\u5360\u4e86\u591a\u5c11\u5730\u201d\uff0c\u800c\u4e0d\u662f\u53ea\u77e5\u9053\u5b66\u6821\u201c\u5728\u54ea\u4e2a\u4f4d\u7f6e\u201d"),

        H3("\u65b9\u6cd5\u4e8c\uff1a\u767e\u5ea6\u5730\u56fe\u722c\u53d6"),

        P("\u9ad8\u5fb7\u4e0d\u884c\uff0c\u6211\u4eec\u8f6c\u5411\u4e86\u767e\u5ea6\u5730\u56fe\u3002\u767e\u5ea6\u5730\u56fe\u5728\u67d0\u4e9b POI \u8be6\u60c5\u9875\u4e2d\u4f1a\u8fd4\u56de\u4e00\u4e2a\u53eb profile_geo \u7684\u5b57\u6bb5\uff0c\u91cc\u9762\u5305\u542b\u4e86\u7528\u5730\u8fb9\u754c\u5750\u6807\u3002\u6211\u4eec\u7528 Playwright\uff08\u6d4f\u89c8\u5668\u81ea\u52a8\u5316\u6846\u67b6\uff09\u52a0\u4e0a Chrome DevTools Protocol\uff08CDP\uff09\uff0c\u5199\u4e86\u4e00\u4e2a\u722c\u866b\u53bb\u81ea\u52a8\u641c\u7d22\u6bcf\u6240\u5b66\u6821\u3001\u63d0\u53d6\u8fd9\u4e2a\u5b57\u6bb5\u3002"),

        P("\u8fd9\u4e2a\u65b9\u6848\u786e\u5b9e\u62ff\u5230\u4e86\u4e00\u90e8\u5206\u6570\u636e\uff1a\u6211\u4eec\u8dd1\u4e86 143 \u6240\u5b66\u6821\uff0c\u6210\u529f\u83b7\u53d6\u4e86 66 \u6240\u7684\u8fb9\u754c\uff08\u547d\u4e2d\u7387\u7ea6 46%\uff09\u3002\u4f46\u5269\u4e0b\u7684\u5927\u591a\u6570\u5b66\u6821\u5728\u767e\u5ea6\u5730\u56fe\u4e0a\u6ca1\u6709 profile_geo \u5b57\u6bb5\uff0c\u6216\u8005\u5b57\u6bb5\u4e3a\u7a7a\u3002\u8986\u76d6\u7387\u592a\u4f4e\uff0c\u4e0d\u8db3\u4ee5\u652f\u6491\u540e\u7eed\u5206\u6790\u3002\u66f4\u9ebb\u70e6\u7684\u662f\uff0c\u65e0\u6cd5\u5224\u65ad\u62ff\u5230\u7684\u8fb9\u754c\u6570\u636e\u662f\u5426\u51c6\u786e\u2014\u2014\u6709\u4e9b\u8fb9\u754c\u660e\u663e\u504f\u79fb\u4e86\u5b9e\u9645\u7528\u5730\u8303\u56f4\u3002"),

        H3("\u65b9\u6cd5\u4e09\uff1aOpenStreetMap \u5f00\u6e90\u6570\u636e"),

        P("OpenStreetMap\uff08OSM\uff09\u662f\u4e00\u4e2a\u5168\u7403\u6027\u7684\u5f00\u6e90\u5730\u56fe\u9879\u76ee\uff0c\u7406\u8bba\u4e0a\u53ef\u4ee5\u4e0b\u8f7d\u4efb\u610f\u533a\u57df\u7684\u5b66\u6821\u7528\u5730\u9762\u6570\u636e\u3002\u4f46\u5728\u5317\u4eac\u8fd9\u6837\u7684\u5927\u57ce\u5e02\uff0cOSM \u7684\u8986\u76d6\u7387\u5e76\u4e0d\u7406\u60f3\u2014\u2014\u6d77\u6dc0\u533a\u4ec5\u8986\u76d6\u4e86\u7ea6 40% \u7684\u5b66\u6821\uff0c\u800c\u4e14\u51e0\u4f55\u7cbe\u5ea6\u53c2\u5dee\u4e0d\u9f50\uff0c\u90e8\u5206\u8fb9\u754c\u660e\u663e\u504f\u79fb\u4e86\u5b9e\u9645\u4f4d\u7f6e\u3002"),

        H2("1.2 \u6700\u7ec8\u65b9\u6848\uff1a\u6dd8\u5b9d\u8d2d\u4e70\u73b0\u6210\u6570\u636e"),

        P("\u4e09\u6761\u8def\u90fd\u8d70\u4e0d\u901a\u4e4b\u540e\uff0c\u6211\u4eec\u60f3\u5230\u4e86\u4e00\u6761\u201c\u6377\u5f84\u201d\uff1a\u65e2\u7136\u514d\u8d39\u6570\u636e\u5404\u6709\u7f3a\u9677\uff0c\u4e3a\u4ec0\u4e48\u4e0d\u8bd5\u8bd5\u82b1\u94b1\u4e70\uff1f\u5728\u6dd8\u5b9d\u4e0a\u641c\u7d22\u201c\u5317\u4eac \u4e2d\u5c0f\u5b66 \u7528\u5730 \u8fb9\u754c \u6570\u636e\u201d\uff0c\u82b1\u4e86 10 \u5757\u94b1\uff0c\u4e0b\u8f7d\u4e86\u4e00\u4efd\u73b0\u6210\u7684\u6570\u636e\u96c6\u3002"),

        P("\u6536\u5230\u6570\u636e\u540e\u7684\u5904\u7406\u6d41\u7a0b\u5982\u4e0b\uff1a", { bold: true }),
        numItem("\u7b5b\u9009\u51fa\u6d77\u6dc0\u533a\u7684\u8bb0\u5f55\uff0c\u5171 277 \u6240\u4e2d\u5c0f\u5b66"),
        numItem("\u9010\u4e00\u6838\u5bf9\u5b66\u6821\u7684\u540d\u79f0\u3001\u5730\u5740\uff0c\u5254\u9664\u91cd\u590d\u9879\u548c\u7591\u4f3c\u9519\u8bef\u7684\u6570\u636e"),
        numItem("\u5bfc\u51fa\u4e3a Shapefile\uff08.shp\uff09\u683c\u5f0f\uff0c\u4f5c\u4e3a AOI \u56fe\u5c42\u5bfc\u5165 GeoScene Pro"),
        numItem("\u786e\u8ba4 AOI \u56fe\u5c42\u5305\u542b name \u5b57\u6bb5\uff0c\u5b57\u6bb5\u503c\u4e3a\u5b66\u6821\u540d\u79f0\uff0c\u53ef\u76f4\u63a5\u7528\u4e8e\u540e\u7eed\u5206\u6790"),

        H3("\u7ed9\u540e\u6765\u8005\u7684\u7ecf\u9a8c"),
        P("\u9ad8\u5fb7/\u767e\u5ea6 API \u53ea\u8fd4\u56de\u5750\u6807\u70b9\uff0c\u60f3\u8981\u8fb9\u754c\u591a\u8fb9\u5f62\u9700\u8981\u989d\u5916\u5904\u7406\uff1bOSM \u5728\u56fd\u5185\u57ce\u5e02\u8986\u76d6\u4e0d\u5b8c\u6574\uff0c\u4e0d\u9002\u5408\u505a\u7cbe\u7ec6\u5206\u6790\uff1b\u767e\u5ea6\u5730\u56fe\u7684 profile_geo \u5b57\u6bb5\u867d\u6709\u8fb9\u754c\uff0c\u4f46\u547d\u4e2d\u7387\u4ec5 46%\uff1b\u6dd8\u5b9d\u8d2d\u4e70\u7684\u6570\u636e\u6027\u4ef7\u6bd4\u8f83\u9ad8\uff0810 \u5143\uff09\uff0c\u4f46\u6536\u5230\u540e\u9700\u4eba\u5de5\u6838\u5bf9\u8d28\u91cf\u3002"),

        new Paragraph({ children: [new PageBreak()] }),

        // Chapter 2: Statistics
        H1("\u4e8c\u3001\u6570\u636e\u6478\u5e95\u2014\u2014\u5317\u4eac\u4e2d\u5c0f\u5b66\u6570\u91cf\u5206\u5e03"),

        P("\u62ff\u5230\u6570\u636e\u540e\uff0c\u6211\u4eec\u9996\u5148\u5bf9\u5317\u4eac\u5404\u533a\u53bf\u7684\u4e2d\u5c0f\u5b66\u6570\u91cf\u8fdb\u884c\u4e86\u7edf\u8ba1\u6478\u5e95\u3002\u8fd9\u4efd\u7edf\u8ba1\u57fa\u4e8e\u8d2d\u4e70\u7684\u73b0\u6210\u6570\u636e\u96c6\uff0c\u6db5\u76d6\u6240\u6709\u516c\u529e\u548c\u6c11\u529e\u4e2d\u5c0f\u5b66"),

        makeTable(
          [ { text: "\u533a\u53bf", w: 2500 }, { text: "\u4e2d\u5c0f\u5b66\u6570\u91cf", w: 2000 }, { text: "\u5360\u6bd4(%)", w: 2000 }, { text: "\u6392\u540d", w: 1200 } ],
          [
            [{ text: "\u671d\u9633\u533a" }, { text: "345" }, { text: "18.22" }, { text: "1" }],
            [{ text: "\u6d77\u6dc0\u533a", bold: true, color: "1B5E20" }, { text: "277", bold: true, color: "1B5E20" }, { text: "14.63", bold: true, color: "1B5E20" }, { text: "2", bold: true, color: "1B5E20" }],
            [{ text: "\u4e30\u53f0\u533a" }, { text: "164" }, { text: "8.66" }, { text: "3" }],
            [{ text: "\u897f\u57ce\u533a" }, { text: "145" }, { text: "7.66" }, { text: "4" }],
            [{ text: "\u901a\u5dde\u533a" }, { text: "131" }, { text: "6.92" }, { text: "5" }],
            [{ text: "\u660c\u5e73\u533a" }, { text: "124" }, { text: "6.55" }, { text: "6" }],
            [{ text: "\u5927\u5174\u533a" }, { text: "119" }, { text: "6.28" }, { text: "7" }],
            [{ text: "\u623f\u5c71\u533a" }, { text: "116" }, { text: "6.12" }, { text: "8" }],
            [{ text: "\u4e1c\u57ce\u533a" }, { text: "109" }, { text: "5.76" }, { text: "9" }],
            [{ text: "\u987a\u4e49\u533a" }, { text: "78" }, { text: "4.12" }, { text: "10" }],
            [{ text: "\u5bc6\u4e91\u533a" }, { text: "66" }, { text: "3.48" }, { text: "11" }],
            [{ text: "\u77f3\u666f\u5c71\u533a" }, { text: "55" }, { text: "2.90" }, { text: "12" }],
            [{ text: "\u5ef6\u5e86\u533a" }, { text: "54" }, { text: "2.85" }, { text: "13" }],
            [{ text: "\u6000\u67d4\u533a" }, { text: "48" }, { text: "2.53" }, { text: "14" }],
            [{ text: "\u95e8\u5934\u6c9f\u533a" }, { text: "38" }, { text: "2.01" }, { text: "15" }],
            [{ text: "\u5e73\u8c37\u533a" }, { text: "25" }, { text: "1.32" }, { text: "16" }],
          ]
        ),

        new Paragraph({ spacing: { before: 200 } }),
        P("\u6d77\u6dc0\u533a\u6392\u540d\u5206\u6790\uff1a\u6d77\u6dc0\u533a\u4ee5 277 \u6240\u4e2d\u5c0f\u5b66\u4f4d\u5217\u5168\u5e02\u7b2c\u4e8c\uff0c\u4ec5\u6b21\u4e8e\u671d\u9633\u533a\u7684 345 \u6240\uff0c\u5360\u6bd4 14.63%\u3002\u4f5c\u4e3a\u5317\u4eac\u7684\u6559\u80b2\u5927\u533a\uff0c\u6d77\u6dc0\u533a\u4e2d\u5c0f\u5b66\u5bc6\u5ea6\u9ad8\u3001\u5206\u5e03\u96c6\u4e2d\uff0c\u8fd9\u4e3a\u540e\u7eed\u7eff\u5730\u5206\u6790\u63d0\u4f9b\u4e86\u5145\u8db3\u7684\u6837\u672c\u57fa\u7840\u3002\u6211\u4eec\u4ece\u4e2d\u9009\u53d6\u4e86 156 \u6240\u5c0f\u5b66\u4f5c\u4e3a\u672c\u6b21\u7814\u7a76\u7684\u5206\u6790\u5bf9\u8c61\u3002"),

        new Paragraph({ children: [new PageBreak()] }),

        // Chapter 3: GIS
        H1("\u4e09\u3001GIS \u81ea\u52a8\u5316\u2014\u2014\u7f13\u51b2\u533a\u5236\u4f5c\u4e0e\u536b\u661f\u622a\u56fe\u5bfc\u51fa"),

        H2("3.1 \u7f13\u51b2\u533a\uff08Buffer\uff09\u8bbe\u8ba1"),
        P("\u4e3a\u4e86\u5168\u9762\u8bc4\u4f30\u5b66\u6821\u7eff\u5730\u60c5\u51b5\uff0c\u6211\u4eec\u8bbe\u8ba1\u4e86\u53cc\u91cd\u7f13\u51b2\u533a\u7ed3\u6784\uff1a"),
        P("\u5185\u8fb9\u754c\uff08\u7eff\u7ebf\uff09\uff1a\u5b66\u6821\u7528\u5730\u8fb9\u754c\uff08AOI\uff09\u672c\u8eab\uff0c\u7528\u4e8e\u8ba1\u7b97\u5b66\u6821\u5185\u90e8\u7684\u7eff\u5730\u7387", { bold: true, color: "2D8A4E" }),
        P("\u5916\u7f13\u51b2\u533a\uff08\u7ea2\u7ebf\uff09\uff1a\u5b66\u6821\u5916\u6269 100 \u7c73\u7684\u8303\u56f4\uff0c\u7528\u4e8e\u5206\u6790\u5b66\u6821\u4e0e\u5468\u8fb9\u73af\u5883\u7684\u7eff\u5730\u8854\u63a5\u60c5\u51b5", { bold: true, color: "C0392B" }),
        P("\u901a\u8fc7\u5bf9\u6bd4\u7eff\u7ebf\u5185\u4fa7\uff08\u6821\u56ed\u5185\u90e8\uff09\u3001\u7ea2\u7eff\u7ebf\u4e4b\u95f4\uff08\u6821\u56ed\u5916\u56f4\uff09\u4ee5\u53ca\u7ea2\u7ebf\u5185\u4fa7\uff08\u5b66\u6821+100m \u7f13\u51b2\uff09\u8fd9\u4e09\u4e2a\u533a\u57df\u7684\u7eff\u5730\u7387\u5dee\u5f02\uff0c\u53ef\u4ee5\u66f4\u5168\u9762\u5730\u8bc4\u4ef7\u5b66\u6821\u7684\u7eff\u5316\u6c34\u5e73\u3002"),

        H2("3.2 ArcPy \u81ea\u52a8\u5316\u5bfc\u51fa\u811a\u672c"),
        P("\u624b\u52a8\u4e00\u5f20\u5f20\u5bfc\u51fa 156 \u5f20\u536b\u661f\u622a\u56fe\u662f\u4e0d\u73b0\u5b9e\u7684\u3002\u6211\u4eec\u7f16\u5199\u4e86\u4e00\u4e2a ArcPy \u81ea\u52a8\u5316\u811a\u672c\uff0c\u5728 GeoScene Pro 5.0 \u73af\u5883\u4e2d\u8fd0\u884c\u3002\u811a\u672c\u7684\u6838\u5fc3\u903b\u8f91\u5206\u4e94\u6b65\uff1a"),

        numItem("\u5efa\u7acb Mapping \u8868\uff1a\u904d\u5386 Buffer \u56fe\u5c42\u7684\u6bcf\u4e2a\u8981\u7d20\uff0c\u901a\u8fc7\u8d28\u5fc3\u5750\u6807\u5bf9\u6bd4\uff0c\u5c06 Buffer \u4e0e AOI \u7684 name \u5b57\u6bb5\u5339\u914d\u8d77\u6765\u3002\u6700\u521d\u7528\u4e86 Python \u5c42\u7684 within() \u65b9\u6cd5\u505a\u7a7a\u95f4\u5339\u914d\uff0c156 \u4e2a\u8981\u7d20\u9700\u8981\u51e0\u5206\u949f\u624d\u80fd\u5339\u914d\u5b8c\uff1b\u540e\u6765\u6539\u7528 extent \u5750\u6807\u6bd4\u8f83\u6cd5\uff08\u7eaf\u7cb9\u7684\u6570\u503c\u6bd4\u8f83\uff09\uff0c\u4e00\u79d2\u4e0d\u5230\u5c31\u5b8c\u6210\u4e86"),
        numItem("\u9010\u8981\u7d20\u904d\u5386\uff1a\u5bf9 Buffer \u7684\u6bcf\u4e2a\u591a\u8fb9\u5f62\u8981\u7d20\uff0c\u83b7\u53d6\u5176\u8303\u56f4\uff08extent\uff09\u5e76\u5916\u6269 15%\uff0c\u907f\u514d\u7ea2\u7ebf\u7d27\u8d34\u56fe\u7247\u8fb9\u7f18\u5f71\u54cd\u89c6\u89c9\u5224\u65ad"),
        numItem("\u8bbe\u7f6e\u76f8\u673a\uff1a\u901a\u8fc7 map_frame.camera.setExtent() \u5c06\u89c6\u56fe\u7f29\u653e\u81f3\u5bf9\u5e94\u8303\u56f4\u3002\u8fd9\u91cc\u8e29\u4e86\u4e00\u4e2a\u5751\uff1aGeoScene Pro 5.0 \u6ca1\u6709 arcpy.mp.Rectangle \u5bf9\u8c61\uff0c\u5fc5\u987b\u6539\u7528\u624b\u52a8\u8bbe\u7f6e\u76f8\u673a\u53c2\u6570\u7684\u65b9\u5f0f"),
        numItem("\u7b49\u5f85\u74e6\u7247\u52a0\u8f7d\uff1a\u536b\u661f\u5e95\u56fe\u7684\u74e6\u7247\u662f\u5f02\u6b65\u52a0\u8f7d\u7684\uff0c\u5982\u679c\u7acb\u523b\u622a\u56fe\u4f1a\u770b\u5230\u7070\u8272\u7a7a\u6d1e\u3002\u811a\u672c\u8bbe\u7f6e\u4e86 3 \u79d2\u7684\u5ef6\u8fdf\uff0c\u9996\u5f20\u5bfc\u51fa\u540e\u6682\u505c 30 \u79d2\u4f9b\u4eba\u5de5\u68c0\u67e5\u74e6\u7247\u662f\u5426\u5b8c\u6574"),
        numItem("\u5bfc\u51fa\u56fe\u7247\uff1a\u901a\u8fc7 exportToPNG() \u4ee5 resolution=200 \u8f93\u51fa PNG \u56fe\u7247\u3002\u6ce8\u610f\u8fd9\u91cc\u7684\u53c2\u6570\u540d\u53eb resolution \u800c\u4e0d\u662f dpi\u2014\u2014\u8fd9\u662f GeoScene Pro 5.0 \u548c ArcGIS Pro \u7684 API \u5dee\u5f02\u4e4b\u4e00"),

        P("\u6700\u7ec8\u8fd0\u884c\u7684\u56fe\u5c42\u7ed3\u6784\uff1a\u5e95\u56fe\u4e3a\u5929\u5730\u56fe\u536b\u661f\u5f71\u50cf\uff1b\u7eff\u7ebf\u56fe\u5c42\u4e3a\u201c\u6d77\u6dc0\u533a\u5c0f\u5b66AOI_POI\u8fb9\u754c\u201d\uff1b\u7ea2\u7ebf\u56fe\u5c42\u4e3a\u201c\u5c0f\u5b66buffer\u201d\uff08100m \u7f13\u51b2\uff09\u3002\u5bfc\u51fa\u7684 PNG \u56fe\u7247\u4e2d\u540c\u65f6\u4fdd\u7559\u4e86\u7eff\u7ebf\u548c\u7ea2\u7ebf\uff0c\u4f9b\u540e\u7eed AI \u6a21\u578b\u8bc6\u522b"),

        new Paragraph({ children: [new PageBreak()] }),

        // Chapter 4: AI
        H1("\u56db\u3001AI \u89c6\u89c9\u5206\u6790\u2014\u2014\u901a\u4e49\u5343\u95ee\u5927\u6a21\u578b\u8bc6\u522b\u7eff\u5730"),

        H2("4.1 \u6a21\u578b\u9009\u62e9\u4e0e\u8c03\u7528\u6d41\u7a0b"),

        P("\u5bfc\u51fa 156 \u5f20\u536b\u661f\u622a\u56fe\u540e\uff0c\u6211\u4eec\u9700\u8981\u4e00\u79cd\u81ea\u52a8\u5316\u7684\u65b9\u5f0f\u6765\u89e3\u8bfb\u8fd9\u4e9b\u56fe\u7247\uff0c\u63d0\u53d6\u7eff\u5730\u8986\u76d6\u4fe1\u606f\u3002\u6211\u4eec\u9009\u62e9\u4e86\u963f\u91cc\u5df4\u5df4 DashScope \u5e73\u53f0\u4e0a\u7684\u901a\u4e49\u5343\u95ee\u89c6\u89c9\u6a21\u578b\uff08Qwen-VL-Max\uff09\uff0c\u5b83\u80fd\u540c\u65f6\u7406\u89e3\u56fe\u50cf\u5185\u5bb9\u5e76\u8f93\u51fa\u7ed3\u6784\u5316\u7684\u6587\u672c\u7ed3\u679c"),

        P("\u8c03\u7528\u6d41\u7a0b\u5206\u4e3a\u56db\u6b65\uff1a", { bold: true }),
        numItem("\u56fe\u7247\u7f16\u7801\uff1a\u5c06\u6bcf\u5f20 PNG \u622a\u56fe\u8f6c\u4e3a Base64 \u7f16\u7801\u7684 Data URI \u683c\u5f0f\uff0c\u901a\u8fc7 API \u4f20\u8f93\u7ed9\u6a21\u578b"),
        numItem("\u591a\u6a21\u6001\u7406\u89e3\uff1aQwen-VL \u540c\u65f6\u8bc6\u522b\u56fe\u50cf\u4e2d\u7684\u7eff\u7ebf\u533a\u57df\uff08\u5b66\u6821\u8fb9\u754c\uff09\u3001\u7ea2\u7ebf\u533a\u57df\uff08100m \u7f13\u51b2\uff09\uff0c\u4ee5\u53ca\u5176\u4e2d\u7684\u7eff\u5730\u8986\u76d6\u60c5\u51b5"),
        numItem("\u7ed3\u6784\u5316\u8f93\u51fa\uff1a\u6a21\u578b\u6309\u9884\u8bbe\u7684 JSON \u683c\u5f0f\u8f93\u51fa\u5206\u6790\u7ed3\u679c\uff0c\u5305\u542b 8 \u4e2a\u5206\u6790\u7ef4\u5ea6"),
        numItem("\u6301\u4e45\u5316\u5b58\u50a8\uff1a\u6bcf\u5b8c\u6210 1 \u5f20\u56fe\u7247\u7684\u5206\u6790\uff0c\u7ed3\u679c\u7acb\u5373\u5199\u5165\u786c\u76d8\uff08\u539f\u5b50\u66ff\u6362\uff0c\u4e0d\u4f1a\u56e0\u4e2d\u65ad\u4e22\u5931\u6570\u636e\uff09\uff0c\u652f\u6301\u65ad\u70b9\u7eed\u4f20"),

        H2("4.2 \u4ee3\u7801\u601d\u8def"),
        P("\u6a21\u578b\u9009\u62e9\uff1aqwen-vl-max-latest\uff08\u7cbe\u5ea6\u6700\u4f18\uff09\uff0c\u5907\u9009 qwen-vl-plus\uff08\u901f\u5ea6\u66f4\u5feb\uff09\u3002\u5e76\u53d1\u7b56\u7565\uff1a3 \u7ebf\u7a0b\u5e76\u53d1\uff0c\u6bcf\u8bf7\u6c42\u95f4\u9694 1 \u79d2\uff0c\u9632\u6b62\u89e6\u53d1 API \u7684 QPS \u9650\u5236\u3002\u91cd\u8bd5\u673a\u5236\uff1a\u6700\u591a\u91cd\u8bd5 3 \u6b21\uff0c\u9047\u5230\u9650\u6d41\u65f6\u81ea\u52a8\u52a0\u500d\u7b49\u5f85\uff08\u6307\u6570\u9000\u907f\uff09"),

        H2("4.3 \u5206\u6790\u7ef4\u5ea6\u8bf4\u660e"),
        P("\u6a21\u578b\u5bf9\u6bcf\u5f20\u56fe\u7247\u7684\u5206\u6790\u8986\u76d6\u4e86\u4ee5\u4e0b 8 \u4e2a\u7ef4\u5ea6\uff1a"),
        bullet("\u5b66\u6821\u5185\u90e8\uff08\u7eff\u7ebf\u4ee5\u5185\uff09\u7684\u7eff\u5730\u7387\u4f30\u7b97"),
        bullet("\u5b66\u6821\u53ca\u5468\u8fb9 100m\uff08\u7ea2\u7ebf\u4ee5\u5185\uff09\u7684\u603b\u7eff\u5730\u7387"),
        bullet("\u5b66\u6821\u5916\u56f4\uff08\u7ea2\u7ebf\u4ee5\u5185\u3001\u7eff\u7ebf\u4ee5\u5916\uff09\u7684\u7eff\u5730\u7387"),
        bullet("\u7eff\u5730\u8986\u76d6\u60c5\u51b5\u7684\u7efc\u5408\u63cf\u8ff0\u4e0e\u8bc4\u4ef7"),
        bullet("\u5b66\u6821\u5468\u8fb9\u73af\u5883\u7684\u536b\u661f\u56fe\u8bc6\u522b\uff08\u9053\u8def\u3001\u5efa\u7b51\u3001\u516c\u56ed\u3001\u519c\u7530\u7b49\uff09"),
        bullet("\u4f9d\u636e\u7eff\u8272\u6821\u56ed\u6807\u51c6\u7684\u8bc4\u5206\uff08\u6ee1\u5206 10 \u5206\uff09"),
        bullet("\u5b66\u6821\u4f4d\u7f6e\uff08\u8857\u9053\u7ea7\u522b\uff09"),
        bullet("\u5176\u4ed6\u5907\u6ce8"),

        H2("4.4 \u5355\u6240\u5b66\u6821\u8f93\u51fa\u793a\u4f8b"),
        P("\u4ee5\u4e0a\u5730\u5b9e\u9a8c\u5c0f\u5b66\u4e3a\u4f8b\uff0c\u6a21\u578b\u8f93\u51fa\u7684\u5206\u6790\u7ed3\u679c\u5982\u4e0b\uff1a"),

        P("\u5b66\u6821\u540d\u79f0\uff1a\u4e0a\u5730\u5b9e\u9a8c\u5c0f\u5b66", { bold: true }),
        P("\u5185\u90e8\u7eff\u5730\u7387\uff1a35% | \u603b\u7eff\u5730\u7387\uff08\u542b 100m \u7f13\u51b2\u533a\uff09\uff1a20% | \u5916\u56f4\u7eff\u5730\u7387\uff1a15%"),
        P("\u7efc\u5408\u8bc4\u5206\uff1a7/10 | \u56fd\u6807\u8bc4\u5206\uff1a8/10"),
        P("\u7efc\u5408\u63cf\u8ff0\uff1a\u6821\u56ed\u5185\u7eff\u5730\u8986\u76d6\u8f83\u597d\uff0c\u4e3b\u8981\u96c6\u4e2d\u5728\u64cd\u573a\u5468\u8fb9\u53ca\u6559\u5b66\u697c\u4e4b\u95f4\u533a\u57df\uff0c\u5305\u62ec\u8fd0\u52a8\u573a\u8349\u76ae\u3001\u7eff\u5316\u5e26\u548c\u7a3d\u91cf\u6811\u6728\u3002\u6574\u4f53\u5e03\u5c40\u8f83\u4e3a\u89c4\u6574\uff0c\u7eff\u5730\u5206\u5e03\u5747\u5300\uff0c\u4f46\u5efa\u7b51\u5bc6\u5ea6\u8f83\u9ad8\uff0c\u786c\u8d28\u94fa\u88c5\u9762\u79ef\u8f83\u5927\u3002"),
        P("\u5468\u8fb9\u73af\u5883\uff1a\u4f4d\u4e8e\u6d77\u6dc0\u533a\u4e0a\u5730\u8857\u9053\uff0c\u5468\u8fb9\u4e3a\u5bc6\u96c6\u7684\u5c45\u6c11\u5c0f\u533a\uff08\u5982\u4e0a\u5730\u4e1c\u91cc\uff09\uff0c\u5317\u4fa7\u6709\u793e\u533a\u670d\u52a1\u7ad9\u548c\u836f\u5e97\uff0c\u897f\u4fa7\u4e34\u8fd1\u533b\u836f\u4e2d\u5fc3\u548c\u8d85\u5e02\uff0c\u5357\u4fa7\u4e3a\u94f6\u884c\u53ca\u79d1\u8d38\u5927\u53a6\u3002\u9053\u8def\u7f51\u7edc\u53d1\u8fbe\uff0c\u4f46\u516c\u5171\u7eff\u5730\u8f83\u5c11"),

        P("\u56fd\u6807\u8bc4\u5206\u4f9d\u636e\uff1a\u4f9d\u636e GB/T 51356-2019\u300a\u7eff\u8272\u6821\u56ed\u8bc4\u4ef7\u6807\u51c6\u300b\uff0c\u8be5\u6821\u6821\u56ed\u7eff\u5730\u7387\u8fbe 35%\uff0c\u6ee1\u8db3\u7eff\u5730\u7387\u4e0d\u4f4e\u4e8e 30% \u7684\u8981\u6c42\uff1b\u5b66\u6821\u5e03\u5c40\u5408\u7406\uff0c\u6709\u8fd0\u52a8\u573a\u5730\u548c\u7eff\u5316\u7a7a\u95f4\uff0c\u4f46\u5916\u90e8\u7f13\u51b2\u533a\u7eff\u5730\u4e0d\u8db3\u3002"),

        new Paragraph({ children: [new PageBreak()] }),

        // Chapter 5: Results
        H1("\u4e94\u3001\u7ed3\u679c\u89e3\u8bfb\u2014\u2014\u6d77\u6dc0\u5c0f\u5b66\u7eff\u5730\u8bc4\u4ef7\u4e0e\u5efa\u8bae"),

        H2("5.1 \u603b\u4f53\u60c5\u51b5"),
        P("\u5bf9 156 \u6240\u5c0f\u5b66\u7684 AI \u5206\u6790\u7ed3\u679c\u8fdb\u884c\u6c47\u603b\u7edf\u8ba1\uff0c\u5f97\u5230\u4ee5\u4e0b\u6838\u5fc3\u6570\u636e\uff1a"),

        makeTable(
          [ { text: "\u6307\u6807", w: 4000, align: AlignmentType.LEFT },
            { text: "\u6570\u503c", w: 2000 },
            { text: "\u8bf4\u660e", w: 3026, align: AlignmentType.LEFT } ],
          [
            [{ text: "\u5e73\u5747\u6821\u5185\u7eff\u5730\u7387", align: AlignmentType.LEFT },
             { text: "27.3%", bold: true, color: "1B5E20", size: 24 },
             { text: "156 \u6240\u5c0f\u5b66\u7684\u5e73\u5747\u503c", align: AlignmentType.LEFT }],
            [{ text: "\u5e73\u5747\u603b\u7eff\u5730\u7387\uff08\u542b 100m \u7f13\u51b2\uff09", align: AlignmentType.LEFT },
             { text: "20.2%", bold: true, color: "388E3C", size: 24 },
             { text: "\u5305\u542b\u5b66\u6821\u5916\u56f4 100m \u8303\u56f4", align: AlignmentType.LEFT }],
            [{ text: "\u5185\u90e8\u7eff\u5730\u7387\u8fbe\u6807\u7387\uff08\u226530%\uff09", align: AlignmentType.LEFT },
             { text: "66.0%", bold: true, color: "1B5E20", size: 24 },
             { text: "103 \u6240\u5b66\u6821\u8fbe\u6807\uff0c53 \u6240\u672a\u8fbe\u6807", align: AlignmentType.LEFT }],
            [{ text: "\u56fd\u6807\u8bc4\u5206\u5747\u503c", align: AlignmentType.LEFT },
             { text: "7.17/10", bold: true, color: "388E3C", size: 24 },
             { text: "\u6ee1\u5206 10 \u5206", align: AlignmentType.LEFT }],
          ]
        ),

        new Paragraph({ spacing: { before: 200 } }),
        H2("5.2 \u8bc4\u4ef7\u6807\u51c6"),
        P("GB/T 51356-2019\u300a\u7eff\u8272\u6821\u56ed\u8bc4\u4ef7\u6807\u51c6\u300b\uff1a\u65b0\u5efa\u5b66\u6821\u7eff\u5730\u7387\u4e0d\u4f4e\u4e8e 30%\uff0c\u6539\u5efa\u9879\u76ee\u4e0d\u4f4e\u4e8e 30%\uff08\u6b63\u5728\u4fee\u8ba2\u4e2d\uff0c\u65b0\u7248\u53ef\u80fd\u8981\u6c42\u65b0\u533a\u226535%\uff09", { size: 20 }),
        P("GB 50099-2011\u300a\u4e2d\u5c0f\u5b66\u6821\u8bbe\u8ba1\u89c4\u8303\u300b\uff1a\u5b66\u6821\u5e94\u8bbe\u7f6e\u96c6\u4e2d\u7eff\u5730\uff0c\u5bbd\u5ea6\u4e0d\u5c0f\u4e8e 8 \u7c73", { size: 20 }),

        H2("5.3 \u7814\u7a76\u80cc\u666f\u7ed3\u5408\u5206\u6790"),
        P("\u4ece\u653f\u7b56\u5c42\u9762\u770b\uff0c2021 \u5e74\u56fd\u5bb6\u53d1\u6539\u59d4\u7b49 23 \u90e8\u95e8\u8054\u5408\u5370\u53d1\u4e86\u300a\u5173\u4e8e\u63a8\u8fdb\u513f\u7ae5\u53cb\u597d\u57ce\u5e02\u5efa\u8bbe\u7684\u6307\u5bfc\u610f\u89c1\u300b\uff0c2022 \u5e74\u4f4f\u5efa\u90e8\u53d1\u5e03\u4e86\u300a\u57ce\u5e02\u513f\u7ae5\u53cb\u597d\u7a7a\u95f4\u5efa\u8bbe\u5bfc\u5219\uff08\u8bd5\u884c\uff09\u300b\uff0c\u660e\u786e\u63d0\u51fa\u63a8\u8fdb\u57ce\u5e02\u516c\u56ed\u7eff\u5730\u9002\u513f\u5316\u6539\u9020\u3001\u589e\u52a0\u513f\u7ae5\u6237\u5916\u6d3b\u52a8\u7a7a\u95f4\u3002\u4e16\u754c\u536b\u751f\u7ec4\u7ec7\u5efa\u8bae\u57ce\u5e02\u5c45\u6c11\u4eba\u5747\u7eff\u5730\u4e0d\u4f4e\u4e8e 9 \u5e73\u65b9\u7c73"),

        P("\u5df2\u6709\u7814\u7a76\u8868\u660e\uff0c\u6d77\u6dc0\u533a\u73b0\u6709\u7eff\u5730\u4f9b\u7ed9\u4e0e\u513f\u7ae5\u5b9e\u9645\u9700\u8981\u4e4b\u95f4\u5b58\u5728\u4e0d\u5339\u914d\uff08\u5362\u53ef\u53ef\uff0c2021\uff09\u3002\u6d77\u6dc0\u533a 8 \u4e2a\u5c0f\u533a\u7684\u8c03\u7814\u53d1\u73b0\uff0c\u793e\u533a\u516c\u5171\u7a7a\u95f4\u5728\u7eff\u5730\u7cfb\u7edf\u3001\u513f\u7ae5\u6d3b\u52a8\u573a\u5730\u7b49\u65b9\u9762\u666e\u904d\u5b58\u5728\u4e0d\u8db3\uff0c\u513f\u7ae5\u53cb\u597d\u7a0b\u5ea6\u504f\u4f4e"),

        P("\u6211\u4eec\u7684\u5206\u6790\u8fdb\u4e00\u6b65\u8bc1\u5b9e\u4e86\u8fd9\u4e00\u5224\u65ad\uff1a\u6d77\u6dc0\u533a\u5c0f\u5b66\u5e73\u5747\u7eff\u5730\u7387 27.3%\uff0c\u867d 66% \u7684\u5b66\u6821\u8fbe\u5230 30% \u7684\u57fa\u672c\u6807\u51c6\uff0c\u4ecd\u6709\u7ea6 1/3 \u7684\u5c0f\u5b66\u7eff\u5730\u7387\u4e0d\u8db3 30%\u3002\u6821\u56ed\u7eff\u5730\u4f9b\u7ed9\u5b58\u5728\u663e\u8457\u7684\u6821\u9645\u4e0d\u5747\u8861\u73b0\u8c61", { bold: true }),

        new Paragraph({ children: [new PageBreak()] }),

        H2("5.4 \u7eff\u5730\u6700\u597d\u7684 3 \u6240\u5c0f\u5b66"),
        P("\u6839\u636e\u56fd\u6807\u8bc4\u5206\uff08\u6ee1\u5206 10 \u5206\uff09\uff0c\u4ee5\u4e0b\u4e09\u6240\u5b66\u6821\u8868\u73b0\u6700\u4f73\uff1a"),

        makeTable(
          [ { text: "\u5b66\u6821", w: 2500, align: AlignmentType.LEFT },
            { text: "\u8bc4\u5206", w: 1200 },
            { text: "\u7eff\u5730\u7387", w: 1200 },
            { text: "\u4e3b\u8981\u8bc4\u4ef7", w: 4126, align: AlignmentType.LEFT } ],
          [
            [{ text: "\u548c\u5e73\u5c0f\u5b66", align: AlignmentType.LEFT },
             { text: "10\u5206", bold: true, color: "1B5E20" },
             { text: "45%", bold: true, color: "2D8A4E" },
             { text: "\u6821\u56ed\u5185\u7eff\u5730\u4ee5\u64cd\u573a\u8349\u76ae\u548c\u5468\u8fb9\u7eff\u5316\u5e26\u4e3a\u4e3b\uff0c\u7eff\u5730\u8986\u76d6\u826f\u597d\uff0c\u5468\u8fb9\u6709\u4e30\u5bcc\u5c71\u6797\u690d\u88ab\uff0c\u5f62\u6210\u826f\u597d\u7684\u751f\u6001\u57fa\u5e95\u3002\u603b\u7eff\u5730\u7387\u8fbe 65%", align: AlignmentType.LEFT, size: 18 }],
            [{ text: "\u4e2d\u56fd\u4eba\u6c11\u5927\u5b66\u9644\u5c5e\u5c0f\u5b66", align: AlignmentType.LEFT },
             { text: "9\u5206", bold: true, color: "1B5E20" },
             { text: "35%", bold: true, color: "2D8A4E" },
             { text: "\u7eff\u5730\u5e03\u5c40\u5747\u8861\uff0c\u690d\u7269\u79cd\u7c7b\u4e30\u5bcc\uff0c\u4e54\u704c\u6728\u7ed3\u5408\uff0c\u8bbe\u6709\u6807\u51c6\u64cd\u573a\u548c\u591a\u4e2a\u5c0f\u578b\u7eff\u5730\u7a7a\u95f4", align: AlignmentType.LEFT, size: 18 }],
            [{ text: "\u5317\u4eac\u5927\u5b66\u9644\u5c5e\u5c0f\u5b66", align: AlignmentType.LEFT },
             { text: "9\u5206", bold: true, color: "1B5E20" },
             { text: "35%", bold: true, color: "2D8A4E" },
             { text: "\u7eff\u5316\u8986\u76d6\u4f18\u826f\uff0c\u7eff\u5316\u5c42\u6b21\u4e30\u5bcc\uff0c\u4e0e\u5468\u8fb9\u9890\u548c\u56ed\u3001\u5706\u660e\u56ed\u7684\u751f\u6001\u7eff\u5eca\u5f62\u6210\u8054\u52a8", align: AlignmentType.LEFT, size: 18 }],
          ]
        ),

        P("\u8fd9\u4e09\u6240\u5b66\u6821\u6216\u5468\u8fb9\u6709\u5927\u578b\u516c\u56ed/\u5c71\u6797\uff0c\u6216\u6821\u5185\u7eff\u5730\u8bbe\u8ba1\u6c34\u5e73\u8f83\u9ad8\uff0c\u503c\u5f97\u4f5c\u4e3a\u6807\u6746\u6848\u4f8b\u6df1\u5165\u7814\u7a76", { italics: true, color: "388E3C" }),

        new Paragraph({ children: [new PageBreak()] }),

        H2("5.5 \u7eff\u5730\u6700\u9700\u6539\u5584\u7684 3 \u6240\u5c0f\u5b66"),
        P("\u4ee5\u4e0b\u4e09\u6240\u5b66\u6821\u8bc4\u5206\u6700\u4f4e\uff0c\u7eff\u5730\u7387\u4e25\u91cd\u4e0d\u8db3\uff1a"),

        makeTable(
          [ { text: "\u5b66\u6821", w: 2500, align: AlignmentType.LEFT },
            { text: "\u8bc4\u5206", w: 1200 },
            { text: "\u7eff\u5730\u7387", w: 1200 },
            { text: "\u4e3b\u8981\u8bc4\u4ef7", w: 4126, align: AlignmentType.LEFT } ],
          [
            [{ text: "\u5317\u5b89\u6cb3\u4e2d\u5fc3\u5c0f\u5b66\uff08\u5468\u5bb6\u5df7\u6821\u533a\uff09", align: AlignmentType.LEFT },
             { text: "4\u5206", bold: true, color: "C0392B" },
             { text: "10%", bold: true, color: "C0392B" },
             { text: "\u7528\u5730\u5185\u4ee5\u5efa\u7b51\u548c\u786c\u8d28\u94fa\u88c5\u4e3a\u4e3b\uff0c\u4ec5\u64cd\u573a\u6709\u7a3d\u91cf\u690d\u88ab\u3002\u5468\u8fb9\u4e3a\u519c\u7530\u548c\u8352\u5730\uff0c\u7f3a\u4e4f\u516c\u56ed\u6216\u96c6\u4e2d\u7eff\u5730", align: AlignmentType.LEFT, size: 18 }],
            [{ text: "\u548c\u5e73\u5c0f\u5b66\uff08\u4e1c\u57e0\u5934\u6821\u533a\uff09", align: AlignmentType.LEFT },
             { text: "4\u5206", bold: true, color: "C0392B" },
             { text: "10-15%", bold: true, color: "C0392B", size: 18 },
             { text: "\u6821\u56ed\u4ee5\u5927\u578b\u5efa\u7b51\u548c\u786c\u5316\u5e7f\u573a\u4e3a\u4e3b\u4f53\uff0c\u7f3a\u4e4f\u5927\u9762\u79ef\u8349\u576a\u3002\u5916\u90e8\u7f13\u51b2\u533a\u591a\u4e3a\u88f8\u5730\uff0c\u65e0\u660e\u663e\u7eff\u5730\u7a7a\u95f4", align: AlignmentType.LEFT, size: 18 }],
            [{ text: "\u7b2c\u4e8c\u5b9e\u9a8c\u5c0f\u5b66\uff08\u6c47\u7f18\u6821\u533a\uff09", align: AlignmentType.LEFT },
             { text: "4\u5206", bold: true, color: "C0392B" },
             { text: "10%", bold: true, color: "C0392B" },
             { text: "\u7eff\u5730\u96c6\u4e2d\u5728\u5efa\u7b51\u5468\u8fb9\u7a3d\u91cf\u7eff\u5316\u5e26\uff0c\u6821\u5185\u4ee5\u6559\u5b66\u697c\u548c\u8fd0\u52a8\u573a\u4e3a\u4e3b\u3002\u5916\u90e8\u7f13\u51b2\u533a\u5927\u90e8\u5206\u4e3a\u786c\u5316\u5730\u9762", align: AlignmentType.LEFT, size: 18 }],
          ]
        ),

        P("\u8fd9\u4e09\u6240\u5b66\u6821\u7eff\u5730\u7387\u4e0d\u8db3 15%\uff0c\u8fdc\u4f4e\u4e8e\u56fd\u6807\u8981\u6c42\u7684 30%\uff0c\u5efa\u8bae\u4f18\u5148\u7eb3\u5165\u6821\u56ed\u7eff\u5316\u6539\u9020\u8ba1\u5212", { italics: true, color: "C0392B" }),

        new Paragraph({ children: [new PageBreak()] }),

        H2("5.6 \u603b\u7ed3\u4e0e\u6539\u5584\u5efa\u8bae"),

        H3("\u5f53\u524d\u7eff\u5730\u60c5\u51b5\u603b\u7ed3"),
        bullet("\u5e73\u5747\u6821\u5185\u7eff\u5730\u7387 27.3%\uff0c\u8ddd 35% \u7684\u65b0\u533a\u6807\u51c6\u4ecd\u6709\u5dee\u8ddd"),
        bullet("66% \u7684\u5b66\u6821\u8fbe\u6807\uff08\u7eff\u5730\u7387 \u2265 30%\uff09\uff0c\u4f46\u7ea6 1/3 \u4e0d\u5408\u683c"),
        bullet("\u5f97\u5206\u6700\u9ad8\u7684\u5b66\u6821\uff08\u548c\u5e73\u5c0f\u5b66 10 \u5206\uff09\u5f97\u76ca\u4e8e\u5468\u8fb9\u5c71\u6797"),
        bullet("\u5f97\u5206\u6700\u4f4e\u7684\u5b66\u6821\uff084 \u5206\uff09\u5747\u4e3a\u57ce\u90ca\u6216\u7d27\u51d1\u578b\u6821\u533a"),
        bullet("\u6821\u9645\u5dee\u5f02\u663e\u8457\uff0c\u5448\u73b0\u201c\u57ce\u91cc\u4e0d\u5747\u8861\u3001\u57ce\u5916\u4e24\u6781\u5316\u201d\u7684\u7279\u5f81"),

        H3("\u6539\u5584\u5efa\u8bae"),
        numItem("\u5bf9\u7eff\u5730\u7387\u4f4e\u4e8e 15% \u7684\u5b66\u6821\u4f18\u5148\u8fdb\u884c\u7eff\u5316\u6539\u9020"),
        numItem("\u9f13\u52b1\u6821\u56ed\u7eff\u5316\u4e0e\u5468\u8fb9\u516c\u56ed/\u7eff\u9053\u8fde\u901a\uff0c\u5f62\u6210\u57ce\u5e02\u7eff\u7f51"),
        numItem("\u65b0\u5efa\u6821\u533a\u5e94\u4e25\u683c\u6267\u884c\u7eff\u5730\u7387 \u2265 35% \u7684\u6807\u51c6"),
        numItem("\u8001\u65e7\u6821\u533a\u901a\u8fc7\u7acb\u4f53\u7eff\u5316\uff08\u5c4b\u9876\u7eff\u5316\u3001\u5782\u76f4\u7eff\u5316\uff09\u589e\u52a0\u6709\u6548\u7eff\u91cf"),
        numItem("\u7ed3\u5408\u513f\u7ae5\u53cb\u597d\u57ce\u5e02\u653f\u7b56\uff0c\u63a8\u52a8\u5b66\u5f84\u7eff\u9053\u5efa\u8bbe"),

        H3("\u4e0b\u4e00\u6b65\u5de5\u4f5c\u5c55\u671b"),
        numItem("\u5c06\u7eff\u5730\u7387\u6570\u636e\u56de\u586b\u81f3 GIS \u5c5e\u6027\u8868\uff0c\u5236\u4f5c\u6d77\u6dc0\u533a\u5c0f\u5b66\u7eff\u5730\u7387\u5206\u5e03\u70ed\u529b\u56fe"),
        numItem("\u7ed3\u5408\u5b66\u6821\u5468\u8fb9\u7528\u5730\u7c7b\u578b\uff08\u516c\u56ed\u3001\u9053\u8def\u3001\u5c45\u4f4f\u533a\uff09\uff0c\u5206\u6790\u5f71\u54cd\u7eff\u5730\u7387\u7684\u5173\u952e\u56e0\u7d20"),
        numItem("\u5bf9\u6bd4\u4e0d\u540c\u8857\u9053/\u5b66\u533a\u7684\u7eff\u5730\u4f9b\u7ed9\u5dee\u5f02\uff0c\u8bc6\u522b\u7eff\u5730\u670d\u52a1\u76f2\u533a"),
        numItem("\u53c2\u7167\u513f\u7ae5\u53cb\u597d\u57ce\u5e02\u6807\u51c6\uff0c\u63d0\u51fa\u5206\u7ea7\u5206\u7c7b\u7684\u6821\u56ed\u7eff\u5316\u6539\u9020\u7b56\u7565"),

        new Paragraph({ spacing: { before: 200 }, border: { top: { style: BorderStyle.SINGLE, size: 4, color: "D4A843", space: 8 } } }),
        P("\u53c2\u8003\u6587\u732e", { bold: true, color: "1B5E20", size: 22 }),
        P("Louv, R. (2005). Last Child in the Woods: Saving Our Children from Nature-Deficit Disorder.", { size: 18 }),
        P("\u5362\u53ef\u53ef. (2021). \u6d77\u6dc0\u533a\u513f\u7ae5\u53cb\u597d\u578b\u793e\u533a\u516c\u5171\u7a7a\u95f4\u7814\u7a76.", { size: 18 }),
        P("GB/T 51356-2019\u300a\u7eff\u8272\u6821\u56ed\u8bc4\u4ef7\u6807\u51c6\u300b.", { size: 18 }),
        P("GB 50099-2011\u300a\u4e2d\u5c0f\u5b66\u6821\u8bbe\u8ba1\u89c4\u8303\u300b.", { size: 18 }),
        P("\u4f4f\u5efa\u90e8. (2022). \u300a\u57ce\u5e02\u513f\u7ae5\u53cb\u597d\u7a7a\u95f4\u5efa\u8bbe\u5bfc\u5219\uff08\u8bd5\u884c\uff09\u300b.", { size: 18 }),
      ]
    }
  ]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("E:/学习资料/景观规划/海淀小学绿地/海淀区小学绿地覆盖情况分析报告.docx", buffer);
  console.log("Word \u6587\u6863\u751f\u6210\u6210\u529f\uff01");
}).catch(err => console.error("Word \u751f\u6210\u5931\u8d25:", err));
