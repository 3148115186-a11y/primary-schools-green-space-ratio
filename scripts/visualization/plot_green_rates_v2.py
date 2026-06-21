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
with open('E:/学习资料/景观规划/海淀小学绿地/绿地分析结果_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

inside_rates = np.array([r['green_rate_inside'] for r in data['results']])
outside_rates = np.array([r['green_rate_outside'] for r in data['results']])
names = [r['school_name'] for r in data['results']]
scores = np.array([r['overall_score'] for r in data['results']])

print(f"Total schools: {len(inside_rates)}")
print(f"Inside: min={inside_rates.min()}, max={inside_rates.max()}, mean={inside_rates.mean():.1f}")
print(f"Outside: min={outside_rates.min()}, max={outside_rates.max()}, mean={outside_rates.mean():.1f}")

# ---------- Classification thresholds ----------
INSIDE_TH = 30  # national standard
OUTSIDE_TH = 24  # median of outside rates

# ---------- Create the Plot ----------
fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
ax.set_facecolor('#F9F9F9')

# Jitter the data slightly for visibility (since many points overlap)
np.random.seed(42)
jitter_inside = inside_rates + np.random.normal(0, 0.3, len(inside_rates))
jitter_outside = outside_rates + np.random.normal(0, 0.3, len(outside_rates))

sc = ax.scatter(jitter_inside, jitter_outside, c=scores, cmap='RdYlGn',
                s=80, alpha=0.75, edgecolors='#2C3E50', linewidth=0.8, zorder=5)

cbar = plt.colorbar(sc, ax=ax, shrink=0.72, pad=0.02)
cbar.set_label('综合评分', fontsize=12, labelpad=8)
cbar.ax.tick_params(labelsize=10)

# ---------- Reference Lines ----------
ax.axvline(x=INSIDE_TH, color='#C0392B', linestyle='--', linewidth=1.5, alpha=0.6, label=f'校内绿地率达标线 ({INSIDE_TH}%)')
ax.axhline(y=OUTSIDE_TH, color='#D35400', linestyle='--', linewidth=1.5, alpha=0.6, label=f'校外绿地率分割线 ({OUTSIDE_TH}%)')

# Diagonal line
max_val = max(inside_rates.max(), outside_rates.max()) + 5
ax.plot([0, max_val], [0, max_val], color='#7F8C8D', linestyle=':', linewidth=1.2, alpha=0.4, label='校内=校外')

# ---------- Quadrant Labels ----------
q_inside_high_low = [
    (f'校外高·校内低\n(外部补偿型)', 14, 55, '#95A5A6'),
    (f'校外高·校内高\n(双优型)', 36, 55, '#27AE60'),
    (f'校外低·校内低\n(双低型)', 14, 2, '#E74C3C'),
    (f'校外低·校内高\n(自足型)', 36, 2, '#2980B9'),
]
for text, x, y, color in q_inside_high_low:
    ax.text(x, y, text, fontsize=9, ha='center', color=color, alpha=0.55, style='italic')

# ---------- Labels & Titles ----------
ax.set_xlabel('校内绿地率 (%)', fontsize=14, labelpad=8)
ax.set_ylabel('缓冲区（校外）绿地率 (%)', fontsize=14, labelpad=8)
ax.set_title('海淀区小学绿地率分布图 (v2)\n校内绿地率 vs 缓冲区绿地率', fontsize=16, fontweight='bold', pad=15)

# Axis limits (adjusted for v2 data range)
ax.set_xlim(24, 41)
ax.set_ylim(18, 66)
ax.set_xticks(np.arange(25, 41, 5))
ax.set_yticks(np.arange(20, 66, 5))

ax.grid(True, linestyle='--', alpha=0.25, linewidth=0.5, color='#BDC3C7')
ax.set_axisbelow(True)

# ---------- Stats Annotations ----------
inside_std = (inside_rates >= INSIDE_TH).sum()
outside_high = (outside_rates >= OUTSIDE_TH).sum()
stats_text = (
    f'学校数量: {len(inside_rates)}\n'
    f'平均校内绿地率: {inside_rates.mean():.1f}%\n'
    f'平均校外绿地率: {outside_rates.mean():.1f}%\n'
    f'校内达标率 (\u2265{INSIDE_TH}%): {inside_std}所 ({inside_std/len(inside_rates)*100:.1f}%)\n'
    f'校外高绿率 (\u2265{OUTSIDE_TH}%): {outside_high}所 ({outside_high/len(outside_rates)*100:.1f}%)'
)
ax.annotate(stats_text, xy=(0.02, 0.97), xycoords='axes fraction',
            fontsize=10, ha='left', va='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#BDC3C7', alpha=0.92))

# ---------- Legend ----------
legend = ax.legend(loc='lower right', fontsize=9, framealpha=0.9, edgecolor='#BDC3C7')
legend.get_frame().set_linewidth(0.8)

# ========== LABEL ANNOTATION with collision avoidance ==========
annotate_list = [
    (1, '和平小学', '和平小学\n(校外最高)'),
    (2, '四王府小学', '四王府小学'),
    (3, '中关村一小科学城分校', '中关村一小\n科学城分校'),
    (4, '香山小学', '香山小学'),
    (5, '苏家坨中心小学（西小营校区）', '苏家坨中心\n西小营校区'),
    (6, '教师进修学校附属实验小学（西冉校区）', '进修附小\n西冉校区'),
    (7, '和平小学（东埠头校区）', '和平小学\n东埠头校区'),
    (8, '中关村第三小学（红山校区）', '中关村三小\n红山校区'),
    (9, '翠微小学（北校区）', '翠微小学\n北校区'),
    (10, '清华大学附属小学清河分校（朱房校区）', '清华附小\n朱房校区'),
    (11, '海淀区八里庄小学', '八里庄小学'),
    (12, '海淀区北安河中心小学（周家巷校区）', '北安河中心\n周家巷校区'),
    (13, '海淀第二实验小学安宁分校', '实验二小\n安宁分校'),
    (14, '海淀区上庄中心小学（东马坊校区）', '上庄中心\n东马坊校区'),
    (15, '海淀区培星小学（北校区）', '培星小学\n北校区'),
    (16, '海淀区翠微小学（东校区）', '翠微小学\n东校区'),
]

# Build school lookup
school_lookup = {}
for r in data['results']:
    school_lookup[r['school_name']] = {
        'inside': r['green_rate_inside'],
        'outside': r['green_rate_outside'],
        'score': r['overall_score']
    }

labels_found = []
for priority, search_key, label_text in annotate_list:
    for full_name, sd in school_lookup.items():
        if search_key in full_name:
            labels_found.append({
                'name': full_name,
                'inside': sd['inside'],
                'outside': sd['outside'],
                'score': sd['score'],
                'label': label_text,
                'priority': priority
            })
            break

labels_found.sort(key=lambda x: x['priority'])

# Remove duplicates by (inside, outside) pair
seen_pts = set()
unique_labels = []
for item in labels_found:
    key = (item['inside'], item['outside'])
    if key not in seen_pts:
        seen_pts.add(key)
        unique_labels.append(item)
labels_found = unique_labels

offset_candidates = [
    (1.5, 2.0),   # top-right
    (-2.0, 2.0),  # top-left
    (1.5, -2.0),  # bottom-right
    (-2.0, -2.0), # bottom-left
    (3.0, 0),     # right
    (-3.0, 0),    # left
    (0, 3.0),     # top
    (0, -3.0),    # bottom
]

def overlap_dist(x1, y1, x2, y2):
    return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)

placed_positions = []

for item in labels_found:
    ix = item['inside']
    iy = item['outside']
    display_label = item['label']
    
    placed = False
    # Try offset candidates with increasing distance
    for scale in [1.0, 1.5, 2.0]:
        for dx, dy in offset_candidates:
            lx = ix + dx * scale
            ly = iy + dy * scale
            
            collision = False
            for px, py in placed_positions:
                if overlap_dist(lx, ly, px, py) < 5.0:
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
                placed = True
                break
        if placed:
            break
    
    if not placed:
        # Fallback: radial search
        for r in [4, 5, 6]:
            for angle in np.arange(0, 360, 30):
                rad = np.deg2rad(angle)
                lx = ix + r * np.cos(rad)
                ly = iy + r * np.sin(rad)
                collision = False
                for px, py in placed_positions:
                    if overlap_dist(lx, ly, px, py) < 5.0:
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
                    placed = True
                    break
            if placed:
                break

# ---------- Save ----------
output_path = 'E:/学习资料/景观规划/海淀小学绿地/绿地率分布图_v2.png'
plt.tight_layout()
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.close()
print(f'Chart saved to: {output_path}')
print(f'Labels placed: {len(labels_found)}')
