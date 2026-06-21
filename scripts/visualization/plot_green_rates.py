import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

# ---------- Font Setup ----------
font_path = None
candidates = [
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/simsun.ttc',
    'C:/Windows/Fonts/msyhbd.ttc',
]
for p in candidates:
    if os.path.exists(p):
        font_path = p
        break

if font_path:
    font_prop = fm.FontProperties(fname=font_path)
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_prop.get_name()
    plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

# ---------- Data Loading ----------
with open('E:/学习资料/景观规划/海淀小学绿地/绿地分析结果.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def parse_rate(val_str):
    s = val_str.strip().replace(' ', '')
    if '%' in s:
        s = s.replace('%', '')
    if '-' in s:
        parts = s.split('-')
        return (float(parts[0]) + float(parts[1])) / 2.0
    return float(s)

inside_rates = []
outside_rates = []
names = []
scores = []

for r in data['results']:
    inside = parse_rate(r['green_rate_inside'])
    outside = parse_rate(r['green_rate_outside'])
    inside_rates.append(inside)
    outside_rates.append(outside)
    names.append(r['school_name'])
    scores.append(r['overall_score'])

inside_rates = np.array(inside_rates)
outside_rates = np.array(outside_rates)
scores = np.array(scores)

# ---------- Create the Plot (bigger canvas) ----------
fig, ax = plt.subplots(figsize=(14, 10), dpi=150)

# Subtle light grid background for contrast
ax.set_facecolor('#F9F9F9')

# ---------- Improved Scatter ----------
# Use a sequential colormap with high contrast: "viridis" or custom
# Or stick with RdYlGn but add strong black edges
sc = ax.scatter(inside_rates, outside_rates, c=scores, cmap='RdYlGn',
                s=80, alpha=0.85, edgecolors='#2C3E50', linewidth=0.8, zorder=5)

# Add colorbar
cbar = plt.colorbar(sc, ax=ax, shrink=0.72, pad=0.02)
cbar.set_label('综合评分', fontsize=12, labelpad=8)
cbar.ax.tick_params(labelsize=10)

# ---------- Reference Lines ----------
ax.axvline(x=30, color='#C0392B', linestyle='--', linewidth=1.5, alpha=0.6, label='校内绿地率达标线 (30%)')
ax.axhline(y=15, color='#D35400', linestyle='--', linewidth=1.5, alpha=0.6, label='校外绿地率参考线 (15%)')

# Diagonal line where inside == outside
max_val = max(inside_rates.max(), outside_rates.max()) + 5
ax.plot([0, max_val], [0, max_val], color='#7F8C8D', linestyle=':', linewidth=1.2, alpha=0.4, label='校内=校外')

# ---------- Quadrant Labels (more subtle) ----------
ax.text(12, 55, '高校外·低校内\n(外部补偿型)', fontsize=9, ha='center', color='#95A5A6', alpha=0.55, style='italic')
ax.text(42, 55, '高校外·高校内\n(双优型)', fontsize=9, ha='center', color='#27AE60', alpha=0.55, style='italic')
ax.text(12, 3, '低校外·低校内\n(双低型)', fontsize=9, ha='center', color='#E74C3C', alpha=0.55, style='italic')
ax.text(42, 3, '高校内·低校外\n(自足型)', fontsize=9, ha='center', color='#2980B9', alpha=0.55, style='italic')

# ---------- Labels & Titles ----------
ax.set_xlabel('校内绿地率 (%)', fontsize=14, labelpad=8)
ax.set_ylabel('缓冲区（校外）绿地率 (%)', fontsize=14, labelpad=8)
ax.set_title('海淀区小学绿地率分布图\n校内绿地率 vs 缓冲区绿地率', fontsize=16, fontweight='bold', pad=15)

# Axis limits
ax.set_xlim(-1, 63)
ax.set_ylim(-1, 85)
ax.set_xticks(np.arange(0, 61, 10))
ax.set_yticks(np.arange(0, 81, 10))

# Grid
ax.grid(True, linestyle='--', alpha=0.25, linewidth=0.5, color='#BDC3C7')
ax.set_axisbelow(True)

# ---------- Stats Annotations ----------
inside_std = (inside_rates >= 30).sum()
stats_text = (
    f'学校数量: {len(inside_rates)}\n'
    f'平均校内绿地率: {inside_rates.mean():.1f}%\n'
    f'平均校外绿地率: {outside_rates.mean():.1f}%\n'
    f'校内达标率 (≥30%): {inside_std}所 ({inside_std/len(inside_rates)*100:.1f}%)'
)
ax.annotate(stats_text, xy=(0.02, 0.97), xycoords='axes fraction',
            fontsize=10, ha='left', va='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#BDC3C7', alpha=0.92))

# ---------- Legend ----------
legend = ax.legend(loc='lower right', fontsize=9, framealpha=0.9, edgecolor='#BDC3C7')
legend.get_frame().set_linewidth(0.8)

# ========== LABEL ANNOTATION ==========
# Schools to annotate with priority ranking
annotate_list = [
    # (name_contains, priority, label_short)
    # High score + high rates
    ('和平小学', 1, '和平小学\n(最高分)'),
    # High outside
    ('香山小学', 2, '香山小学'),
    ('四王府小学', 3, '四王府小学'),
    ('中关村一小科学城分校', 4, '中关村一小\n科学城分校'),
    ('教师进修学校附属实验小学（西冉校区）', 5, '教师进修学校\n西冉校区'),
    # Low score + low rates
    ('北安河中心小学（周家巷校区）', 6, '北安河中心\n周家巷校区'),
    ('第二实验小学（汇缘校区）', 7, '二小汇缘校区'),
    ('和平小学（东埠头校区）', 8, '和平小学\n东埠头校区'),
    ('清华大学附属小学清河分校（朱房校区）', 9, '清华附小\n朱房校区'),
    ('翠微小学（白家疃校区）', 10, '翠微小学\n白家疃校区'),
    # High inside
    ('台头小学', 11, '台头小学'),
    ('石油学院附属实验小学', 12, '石油附小\n实验小学'),
    # High score
    ('中国人民大学附属小学', 13, '人大附小'),
    ('北京大学附属小学', 14, '北大附小'),
]

# Build lookup dict: full_name -> (inside, outside, score)
school_data = {}
for r in data['results']:
    school_data[r['school_name']] = {
        'inside': parse_rate(r['green_rate_inside']),
        'outside': parse_rate(r['green_rate_outside']),
        'score': r['overall_score']
    }

# Find matching schools from annotate_list
labels_to_place = []
for search_key, priority, label_text in annotate_list:
    for full_name, sd in school_data.items():
        if search_key in full_name:
            labels_to_place.append({
                'name': full_name,
                'inside': sd['inside'],
                'outside': sd['outside'],
                'score': sd['score'],
                'label': label_text,
                'priority': priority
            })
            break

# Sort by priority
labels_to_place.sort(key=lambda x: x['priority'])

# Remove duplicates - keep only highest priority
seen = set()
unique_labels = []
for item in labels_to_place:
    key = f"{item['inside']:.1f}_{item['outside']:.1f}"
    if key not in seen:
        seen.add(key)
        unique_labels.append(item)
labels_to_place = unique_labels

# Candidate label offsets (dx, dy) in data coords, tried in order
# For each point, we try positions in order until we find one that doesn't overlap
offset_candidates = [
    (1.8, 2.5),   # top-right (primary)
    (-1.5, 2.5),  # top-left
    (1.8, -2.0),  # bottom-right
    (-1.5, -2.0), # bottom-left
]

def check_overlap(x1, y1, x2, y2, min_dist=4.0):
    """Check if two label positions are too close"""
    return np.sqrt((x1 - x2)**2 + (y1 - y2)**2) < min_dist

def check_overlap_with_points(label_x, label_y, point_x, point_y, min_dist=1.0):
    """Check if label position is too close to any scatter point (excluding its own)"""
    return abs(label_x - point_x) < min_dist and abs(label_y - point_y) < min_dist

placed_positions = []  # (x, y) of placed labels

for item in labels_to_place:
    ix = item['inside']
    iy = item['outside']
    label = item['label']
    
    # Restrict short label names for display
    display_label = label
    
    placed = False
    for dx, dy in offset_candidates:
        lx = ix + dx
        ly = iy + dy
        
        # Check collision with already placed labels
        collision = False
        for px, py in placed_positions:
            if check_overlap(lx, ly, px, py, min_dist=5.0):
                collision = True
                break
        
        if not collision:
            # Place label here
            ax.annotate(display_label,
                        xy=(ix, iy),
                        xytext=(lx, ly),
                        fontsize=7.5,
                        ha='center', va='center',
                        color='#2C3E50',
                        fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color='#7F8C8D', lw=0.8, alpha=0.7),
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#BDC3C7', alpha=0.85),
                        zorder=20)
            placed_positions.append((lx, ly))
            placed = True
            break
    
    if not placed:
        # Fallback: offset more aggressively
        for angle in [45, 135, 225, 315, 0, 90, 180, 270]:
            rad = np.deg2rad(angle)
            lx = ix + 5.0 * np.cos(rad)
            ly = iy + 5.0 * np.sin(rad)
            collision = False
            for px, py in placed_positions:
                if check_overlap(lx, ly, px, py, min_dist=5.0):
                    collision = True
                    break
            if not collision:
                ax.annotate(display_label,
                            xy=(ix, iy),
                            xytext=(lx, ly),
                            fontsize=7.5,
                            ha='center', va='center',
                            color='#2C3E50',
                            fontweight='bold',
                            arrowprops=dict(arrowstyle='->', color='#7F8C8D', lw=0.8, alpha=0.7),
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#BDC3C7', alpha=0.85),
                            zorder=20)
                placed_positions.append((lx, ly))
                break

# ---------- Save ----------
output_path = 'E:/学习资料/景观规划/海淀小学绿地/绿地率分布图.png'
plt.tight_layout()
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Chart saved to: {output_path}')
print(f'Labels placed: {len(labels_to_place)}')
