import json
import os
import shutil
from collections import defaultdict

# Load v2 data
with open('E:/学习资料/景观规划/海淀小学绿地/绿地分析结果_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Thresholds
INSIDE_TH = 30   # inside >= 30% = 高
OUTSIDE_TH = 24  # outside >= 24% = 高

# Source screenshots folder
src_dir = 'E:/学习资料/景观规划/海淀小学绿地/导出截图'

# Target root folder
target_root = 'E:/学习资料/景观规划/海淀小学绿地/截图分类'
os.makedirs(target_root, exist_ok=True)

# Category definitions: folder_name -> description
categories = [
    ('高高-高校内-高校外', lambda inside, outside: inside >= INSIDE_TH and outside >= OUTSIDE_TH),
    ('高低-高校内-低校外', lambda inside, outside: inside >= INSIDE_TH and outside < OUTSIDE_TH),
    ('低高-低校内-高校外', lambda inside, outside: inside < INSIDE_TH and outside >= OUTSIDE_TH),
    ('低低-低校内-低校外', lambda inside, outside: inside < INSIDE_TH and outside < OUTSIDE_TH),
]

# Create subfolders
for folder_name, _ in categories:
    os.makedirs(os.path.join(target_root, folder_name), exist_ok=True)

# Build school -> (inside, outside) lookup
school_info = {}
for r in data['results']:
    school_info[r['school_name']] = (r['green_rate_inside'], r['green_rate_outside'])

# Classify and copy
counts = defaultdict(int)
not_found = []
copied = defaultdict(list)

# List all PNGs in source dir
all_files = [f for f in os.listdir(src_dir) if f.endswith('.png')]
print(f'Total PNGs in export folder: {len(all_files)}')

for filename in all_files:
    # Extract school name by removing .png extension
    school_name = filename[:-4]  # remove '.png'
    
    if school_name not in school_info:
        not_found.append(school_name)
        continue
    
    inside, outside = school_info[school_name]
    
    # Find matching category
    matched = False
    for folder_name, condition in categories:
        if condition(inside, outside):
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(target_root, folder_name, filename)
            shutil.copy2(src_path, dst_path)
            counts[folder_name] += 1
            copied[folder_name].append(school_name)
            matched = True
            break
    
    if not matched:
        print(f'WARNING: {school_name} (inside={inside}, outside={outside}) matched no category!')

print()
print(f'=== Classification Summary ===')
print(f'Inside threshold: >= {INSIDE_TH}% = 高, < {INSIDE_TH}% = 低')
print(f'Outside threshold: >= {OUTSIDE_TH}% = 高, < {OUTSIDE_TH}% = 低')
print()
for folder_name, _ in categories:
    print(f'{folder_name}: {counts[folder_name]}张')

print()
if not_found:
    print(f'Unmatched screenshots (no data found): {len(not_found)}')
    for n in not_found[:10]:
        print(f'  - {n}')
    if len(not_found) > 10:
        print(f'  ... and {len(not_found)-10} more')

print()
print(f'All files copied to: {target_root}')
