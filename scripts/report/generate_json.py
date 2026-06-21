#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os

OUTPUT = "/sessions/focused-wonderful-lovelace/mnt/景观规划/校外改造方案/校外改造措施-结构化.json"

data = {
    "title": "校外绿色通学路径改造措施",
    "description": "城市小学校外通学路径的环境改造方案结构化数据",
    "categories": [
        {
            "id": "cat_01",
            "name": "道路空间",
            "image": "cat_01.png",
            "conditions": [
                {"id": "cond_01", "name": "窄人行道（<1.5m）", "image": "cond_01.png", "measures": ["m01"]},
                {"id": "cond_02", "name": "宽人行道（≥2m）", "image": "cond_02.png", "measures": ["m02", "m03"]},
                {"id": "cond_03", "name": "道路有绿化隔离带", "image": "cond_03.png", "measures": ["m04"]},
                {"id": "cond_04", "name": "道路为居住区内部路", "image": "cond_04.png", "measures": ["m05"]}
            ]
        },
        {
            "id": "cat_02",
            "name": "道路边界",
            "image": "cat_02.png",
            "conditions": [
                {"id": "cond_05", "name": "边界为实墙", "image": "cond_05.png", "measures": ["m06", "m07", "m08"]},
                {"id": "cond_06", "name": "边界为绿篱（高＞1m）", "image": "cond_06.png", "measures": ["m09"]},
                {"id": "cond_07", "name": "边界为绿篱（密实）", "image": "cond_07.png", "measures": ["m10"]},
                {"id": "cond_08", "name": "边界为围栏（透空）", "image": "cond_08.png", "measures": ["m11"]}
            ]
        },
        {
            "id": "cat_03",
            "name": "交通环境",
            "image": "cat_03.png",
            "conditions": [
                {"id": "cond_09", "name": "交通流量大、车速快", "image": "cond_09.png", "measures": ["m12"]},
                {"id": "cond_10", "name": "交通流量大、无信号灯", "image": "cond_10.png", "measures": ["m13"]},
                {"id": "cond_11", "name": "车流密集、道路宽阔", "image": "cond_11.png", "measures": ["m14"]},
                {"id": "cond_12", "name": "交通静稳化需求高", "image": "cond_12.png", "measures": ["m15"]}
            ]
        },
        {
            "id": "cat_04",
            "name": "周边业态",
            "image": "cat_04.png",
            "conditions": [
                {"id": "cond_13", "name": "沿街商铺密集", "image": "cond_13.png", "measures": ["m16", "m17"]},
                {"id": "cond_14", "name": "周边为住宅小区、有围墙", "image": "cond_14.png", "measures": ["m18"]},
                {"id": "cond_15", "name": "周边有空闲地或待开发地块", "image": "cond_15.png", "measures": ["m19"]},
                {"id": "cond_16", "name": "学校门口缓冲区", "image": "cond_16.png", "measures": ["m20"]}
            ]
        },
        {
            "id": "cat_05",
            "name": "绿化设施",
            "image": "cat_05.png",
            "conditions": [
                {"id": "cond_17", "name": "行道树稀疏或缺失", "image": "cond_17.png", "measures": ["m21"]},
                {"id": "cond_18", "name": "行道树存在但树冠高", "image": "cond_18.png", "measures": ["m22"]},
                {"id": "cond_19", "name": "街旁绿地存在但不可进入", "image": "cond_19.png", "measures": ["m23"]},
                {"id": "cond_20", "name": "绿化覆盖率低、硬化率高", "image": "cond_20.png", "measures": ["m24"]},
                {"id": "cond_21", "name": "有立体绿化潜力", "image": "cond_21.png", "measures": ["m25"]}
            ]
        },
        {
            "id": "cat_06",
            "name": "特殊场景",
            "image": "cat_06.png",
            "conditions": [
                {"id": "cond_16", "name": "学校门口缓冲区", "image": "cond_16.png", "measures": ["m20"]},
                {"id": "cond_22", "name": "通学路径跨越公园/绿地", "image": "cond_22.png", "measures": ["m26"]},
                {"id": "cond_23", "name": "高密度老城区（无改造空间）", "image": "cond_23.png", "measures": ["m27"]},
                {"id": "cond_24", "name": "冬季寒冷地区", "image": "cond_24.png", "measures": ["m28"]},
                {"id": "cond_25", "name": "夏季炎热地区", "image": "cond_25.png", "measures": ["m29"]}
            ]
        }
    ],
    "measures": [
        {
            "id": "m01", "name": "垂直绿化与悬挂花箱",
            "description": "在沿街墙面、栏杆、灯柱上安装悬挂花箱或攀爬网，种植藤本植物（爬山虎、凌霄）或季节性花卉，增加儿童视野范围内绿量。",
            "tags": ["历史街区", "老城区狭窄街道", "商业街"],
            "cases": [
                {"city": "中国杭州", "name": "朝晖实验小学周边", "image": "case_01.jpg"},
                {"city": "荷兰阿姆斯特丹", "name": "Aldo van Eyck游乐场周边街道", "image": "case_02.jpg"}
            ],
            "refs": ["李淑楠（2023）", "Khanian等（2026）"]
        },
        {
            "id": "m02", "name": "儿童专用步行道分隔",
            "description": "用绿化带、低矮灌木或彩色铺装将人行道划分为成人步行区和儿童专用区（宽度≥1.2m），儿童区域设置地面图案和标识。",
            "tags": ["校园周边主路", "新建社区主干道"],
            "cases": [
                {"city": "中国深圳", "name": "红荔社区通学路", "image": "case_03.jpg"},
                {"city": "荷兰代尔夫特", "name": "儿童出行路径项目", "image": "case_04.jpg"}
            ],
            "refs": ["翟翊彤等（2026）", "Gill（2021）"]
        },
        {
            "id": "m03", "name": "行道树+可移动花箱组合",
            "description": "在行道树之间增设高度0.3-0.6m的可移动花箱，种植芳香植物或可触摸草本（迷迭香、薄荷），儿童可近距离接触自然。",
            "tags": ["学校正门道路", "社区主要通学路"],
            "cases": [
                {"city": "中国西安", "name": "沣西新城创新港小学周边", "image": "case_05.jpg"},
                {"city": "英国伦敦", "name": "School Street项目", "image": "case_06.jpg"}
            ],
            "refs": ["陈钊（2023）", "李淑楠（2023）"]
        },
        {
            "id": "m04", "name": "隔离带开放性改造",
            "description": "将封闭式绿篱（黄杨、冬青）降低高度至0.4m以下或改为透空围栏，使儿童在步行时能透过隔离带看到对面绿化，增强安全感和自然体验。",
            "tags": ["双向道路中间绿化带", "机非隔离带"],
            "cases": [
                {"city": "中国天津", "name": "睦南公园周边道路", "image": "case_07.jpg"},
                {"city": "瑞典斯德哥尔摩", "name": "Green Walk项目", "image": "case_08.jpg"}
            ],
            "refs": ["高昕蕊等（2026）", "刘堃等（2022）"]
        },
        {
            "id": "m05", "name": "共享街道（Woonerf）设计",
            "description": "取消路缘石，采用抬升路面、蜿蜒车道、窄化通行空间、设置低矮花坛和座椅，使机动车自然降速，儿童可在街道上安全行走和游戏。",
            "tags": ["封闭社区内部道路", "学校周边住宅区"],
            "cases": [
                {"city": "荷兰代尔夫特", "name": "Woonerf发源地", "image": "case_09.jpg"},
                {"city": "英国伦敦", "name": "Home Zones项目", "image": "case_10.jpg"}
            ],
            "refs": ["Gill（2021）", "杨婷婷（2021）"]
        },
        {
            "id": "m06", "name": "墙面垂直绿化系统",
            "description": "在围墙或建筑墙面安装攀爬网或模块化种植盒，种植常春藤、凌霄、藤本月季，形成绿色墙面；在儿童视线高度（0.8-1.2m）设置可触摸的植物展示区。",
            "tags": ["学校围墙", "小区围墙", "地下车库出入口侧面"],
            "cases": [
                {"city": "中国深圳", "name": "坪山儿童公园外围墙", "image": "case_11.jpg"},
                {"city": "日本东京", "name": "绿色围墙项目", "image": "case_12.jpg"}
            ],
            "refs": ["李淑楠（2023）", "王霞等（2020）"]
        },
        {
            "id": "m07", "name": "艺术彩绘+植物组合",
            "description": "在墙面上绘制自然主题壁画（森林、动物、植物生命周期），并结合底部花坛种植真实植物，虚实结合引导儿童观察自然。",
            "tags": ["缺乏绿化空间的狭窄街道", "临时工地围挡"],
            "cases": [
                {"city": "中国青岛", "name": "城阳山火主题公园围墙", "image": "case_13.jpg"},
                {"city": "巴西累西腓", "name": "儿童友好壁画项目", "image": "case_14.jpg"}
            ],
            "refs": ["Agarwal等（2021）", "王娴等（2024）"]
        },
        {
            "id": "m08", "name": "围墙内绿地外透",
            "description": "将校园围墙内的绿地通过透空围栏或降低围栏高度向外部开放视觉，儿童在围墙外行走时可看见校园内的树木花草。",
            "tags": ["中小学围墙外侧人行道"],
            "cases": [
                {"city": "中国北京", "name": "蓝靛厂小学", "image": "case_15.jpg"},
                {"city": "美国波特兰", "name": "Green Schoolyard项目", "image": "case_16.jpg"}
            ],
            "refs": ["方文楚等（2024）"]
        },
        {
            "id": "m09", "name": "绿篱降高与透空化",
            "description": "将原有高于1m的密实绿篱修剪至0.6-0.8m，或改为间隔式种植（每隔2-3m留出透空缺口），使儿童视线可穿透绿篱，增强空间感知。",
            "tags": ["学校围墙外侧", "公园边界", "居住区临街绿篱"],
            "cases": [
                {"city": "中国北京", "name": "蓝靛厂公园边界改造", "image": "case_17.jpg"},
                {"city": "加拿大温哥华", "name": "Open Edge策略", "image": "case_18.jpg"}
            ],
            "refs": ["高昕蕊等（2026）", "方文楚等（2024）"]
        },
        {
            "id": "m10", "name": "开敞式草坪界面",
            "description": "拆除部分绿篱，改为缓坡草坪直接延伸到人行道边缘，儿童可自由进入草地；在草坡上放置可移动的石头、木桩，增加互动性。",
            "tags": ["校园与道路之间的缓冲绿地", "街角口袋公园"],
            "cases": [
                {"city": "中国深圳", "name": "红荔社区公园", "image": "case_19.jpg"},
                {"city": "丹麦哥本哈根", "name": "草坪广场项目", "image": "case_20.jpg"}
            ],
            "refs": ["刘堃等（2022）", "杨婷婷（2021）"]
        },
        {
            "id": "m11", "name": "围栏挂篮与爬藤植物",
            "description": "在铁艺或金属围栏上悬挂种植篮，种植垂吊植物（矮牵牛、常春藤）；或种植攀爬植物（蔷薇、铁线莲）使其缠绕围栏，软化硬质边界。",
            "tags": ["学校运动场围栏", "小区入口围栏", "公园边界"],
            "cases": [
                {"city": "中国杭州", "name": "胜利实验学校通学路", "image": "case_21.jpg"},
                {"city": "德国柏林", "name": "绿色围栏项目", "image": "case_22.jpg"}
            ],
            "refs": ["李淑楠（2023）"]
        },
        {
            "id": "m12", "name": "限速区与减速带设置",
            "description": "在学校周边300m范围内设置限速30km/h标志，并配合抬升式人行横道、减速丘、彩色铺装等物理措施，强制降低车速。",
            "tags": ["城市主干道旁的学校", "跨社区通学路径"],
            "cases": [
                {"city": "荷兰鹿特丹", "name": "School Zone限速区", "image": "case_23.jpg"},
                {"city": "英国", "name": "20mph Zone全国推广", "image": "case_24.jpg"}
            ],
            "refs": ["Gill（2021）", "翟翊彤等（2026）"]
        },
        {
            "id": "m13", "name": "儿童安全过街设施包",
            "description": "在人行横道处设置儿童高度（0.65m）扶手、地面LED警示灯、彩色斑马线；路缘做斜坡处理便于婴儿车和轮椅通行。",
            "tags": ["学校门口", "十字路口", "公交站旁"],
            "cases": [
                {"city": "中国武汉", "name": "常青花园四小区", "image": "case_25.jpg"},
                {"city": "美国", "name": "Safe Routes to School标准", "image": "case_26.jpg"}
            ],
            "refs": ["翟翊彤等（2026）", "李爽（2019）"]
        },
        {
            "id": "m14", "name": "安全岛与二次过街",
            "description": "在宽度大于15m的道路中央设置安全岛，岛上种植遮阴乔木并设置休息座椅，儿童可在岛上停留观察，分两次完成过街。",
            "tags": ["城市主干道", "学校与社区之间的宽阔道路"],
            "cases": [
                {"city": "日本", "name": "通学路安全岛系统", "image": "case_27.jpg"},
                {"city": "荷兰乌得勒支", "name": "儿童安全过街项目", "image": "case_28.jpg"}
            ],
            "refs": ["Gill（2021）"]
        },
        {
            "id": "m15", "name": "共享街道与交通稳静化",
            "description": "采用抬升交叉口、弯曲车道、路缘延伸、环形交叉等措施降低车速；地面铺装采用砖石拼花，暗示机动车减速通行。",
            "tags": ["居住区内部", "学校周边次级道路"],
            "cases": [
                {"city": "荷兰", "name": "Woonerf社区", "image": "case_29.jpg"},
                {"city": "德国弗莱堡", "name": "Vauban区", "image": "case_30.jpg"}
            ],
            "refs": ["Gill（2021）", "杨婷婷（2021）"]
        },
        {
            "id": "m16", "name": "商铺前可移动花箱",
            "description": "在商铺门口与人行道之间摆放高度0.4-0.6m的可移动花箱，种植季相变化明显的植物（春季樱花、秋季红枫），美化商业界面。",
            "tags": ["商业街", "学校周边早餐店/文具店聚集路段"],
            "cases": [
                {"city": "中国杭州", "name": "朝晖实验小学周边", "image": "case_31.jpg"},
                {"city": "英国伦敦", "name": "Green Street项目", "image": "case_32.jpg"}
            ],
            "refs": ["李淑楠（2023）"]
        },
        {
            "id": "m17", "name": "商铺立面绿植点缀",
            "description": "鼓励商铺在门头、窗台、雨棚下方悬挂盆栽或种植垂吊植物；设置「最美上学路」标识，奖励积极参与绿化的商户。",
            "tags": ["城市更新区", "老城区商业街"],
            "cases": [
                {"city": "中国宁波", "name": "最美上学路项目", "image": "case_33.jpg"},
                {"city": "日本东京", "name": "街道绿化认养制度", "image": "case_34.jpg"}
            ],
            "refs": ["李淑楠（2023）"]
        },
        {
            "id": "m18", "name": "小区围墙外侧绿化带",
            "description": "在小区围墙与人行道之间设置宽度0.5-1m的种植带，种植低矮灌木和花卉，既美化街道又软化硬质界面。",
            "tags": ["居住区外围道路"],
            "cases": [
                {"city": "中国天津", "name": "土山公园周边", "image": "case_35.jpg"},
                {"city": "新加坡", "name": "Park Connector Network", "image": "case_36.jpg"}
            ],
            "refs": ["高昕蕊等（2026）"]
        },
        {
            "id": "m19", "name": "临时自然游戏点",
            "description": "利用闲置地块设置临时性自然游戏区（如沙坑、木桩阵、草地迷宫），定期更换主题，由社区或学校共同维护。",
            "tags": ["待开发空地", "拆除临时建筑后的地块"],
            "cases": [
                {"city": "荷兰鹿特丹", "name": "Ravottuh项目", "image": "case_37.jpg"},
                {"city": "中国深圳", "name": "UABB临时公园", "image": "case_38.jpg"}
            ],
            "refs": ["Meijer等（2024）"]
        },
        {
            "id": "m20", "name": "校前区「绿伞」空间",
            "description": "在校门口设置可移动的绿植伞、花架、遮阳藤蔓廊架，形成过渡性自然空间，供家长等候和儿童放学后短暂游戏。",
            "tags": ["小学校园正门口", "放学家长等待区域"],
            "cases": [
                {"city": "中国天津", "name": "睦南公园校前区", "image": "case_39.jpg"},
                {"city": "荷兰乌得勒支", "name": "Green Schoolyard项目", "image": "case_40.jpg"}
            ],
            "refs": ["杨婷婷（2021）", "陈钊（2023）"]
        },
        {
            "id": "m21", "name": "补充行道树并控制分枝高度",
            "description": "种植分支点低于1.5m的乔木（如海棠、紫叶李、樱花），使树冠覆盖人行道，儿童可触摸树叶、观察花果；间距控制在5-8m。",
            "tags": ["新建道路", "绿化改造路段"],
            "cases": [
                {"city": "中国西安", "name": "沣西新城创新港小学周边", "image": "case_41.jpg"},
                {"city": "德国", "name": "City Trees项目", "image": "case_42.jpg"}
            ],
            "refs": ["全磊等（2022）", "高昕蕊等（2026）"]
        },
        {
            "id": "m22", "name": "林下低矮灌木层补植",
            "description": "在行道树下补充种植耐荫灌木（绣球、八角金盘、南天竹）或草本（玉簪、麦冬），形成乔灌草复层结构，提升近人尺度的绿色体验。",
            "tags": ["老旧道路绿化提升", "校园周边林荫道"],
            "cases": [
                {"city": "中国天津", "name": "解放南园周边", "image": "case_43.jpg"},
                {"city": "日本", "name": "街路绿化多层化技术", "image": "case_44.jpg"}
            ],
            "refs": ["全磊等（2022）"]
        },
        {
            "id": "m23", "name": "街旁绿地可进入化改造",
            "description": "将原有封闭绿篱打开，增设汀步、沙坑、木桩等低干预设施，使儿童可在放学途中短暂停留、探索自然。",
            "tags": ["街角绿地", "社区口袋公园", "道路附属绿地"],
            "cases": [
                {"city": "中国深圳", "name": "红荔社区公园（改造后）", "image": "case_45.jpg"},
                {"city": "美国纽约", "name": "Greenstreets项目", "image": "case_46.jpg"}
            ],
            "refs": ["李淑楠（2023）", "刘堃等（2022）"]
        },
        {
            "id": "m24", "name": "地面透水铺装+嵌草",
            "description": "将部分硬质铺装改造为透水混凝土或嵌草砖，缝隙中种植耐践踏草坪（狗牙根、结缕草），增加接触自然的机会。",
            "tags": ["学校门前广场", "人行道拓宽区域"],
            "cases": [
                {"city": "中国天津", "name": "风湖公园地面改造", "image": "case_47.jpg"},
                {"city": "丹麦哥本哈根", "name": "Blue-Green街道", "image": "case_48.jpg"}
            ],
            "refs": ["翟翊彤等（2026）"]
        },
        {
            "id": "m25", "name": "建筑立面、桥墩、灯柱立体绿化",
            "description": "对高架桥墩、路灯杆、建筑外墙等垂直界面安装攀爬网或植物模块，形成「绿色立柱」，增加街道的垂直绿量。",
            "tags": ["高架桥下通学路", "地铁站出口", "人行天桥"],
            "cases": [
                {"city": "中国杭州", "name": "通学径试点", "image": "case_49.jpg"},
                {"city": "新加坡", "name": "Green Lanes计划", "image": "case_50.jpg"}
            ],
            "refs": ["李淑楠（2023）"]
        },
        {
            "id": "m26", "name": "路径穿园设计",
            "description": "将通学路径有意引入邻近公园或绿地内部，使用曲线小径、木质栈道，沿途设置植物标识牌和观察点，使通学过程本身成为自然教育体验。",
            "tags": ["学校与居住区之间有公园或大型绿地的区域"],
            "cases": [
                {"city": "波兰罗兹市", "name": "公园通学路", "image": "case_51.jpg"},
                {"city": "美国波特兰", "name": "Green School Routes计划", "image": "case_52.jpg"}
            ],
            "refs": ["Gill（2021）", "Khanian等（2026）"]
        },
        {
            "id": "m27", "name": "微型「口袋绿」介入",
            "description": "在消防栓旁、电箱周围、建筑凹口等极小空间植入单株观赏树木或一组可移动花箱，形成「点状」绿色节点，串联成线性绿色通学网络。",
            "tags": ["历史文化街区", "胡同/里弄区域"],
            "cases": [
                {"city": "中国北京", "name": "胡同微花园项目", "image": "case_53.jpg"},
                {"city": "英国伦敦", "name": "Pocket Parks计划", "image": "case_54.jpg"}
            ],
            "refs": ["翟翊彤等（2026）", "李淑楠（2023）"]
        },
        {
            "id": "m28", "name": "冬季常绿植物配置",
            "description": "选择松柏、冬青、南天竹等常绿植物作为背景，配合红色枝条植物（红瑞木）和冬季观赏果实（火棘、金银木），保证通学路四季有景。",
            "tags": ["北方城市", "寒冷气候区通学路"],
            "cases": [
                {"city": "中国西安", "name": "严寒气候区中小学", "image": "case_55.jpg"},
                {"city": "加拿大埃德蒙顿", "name": "Winter City策略", "image": "case_56.jpg"}
            ],
            "refs": ["全磊等（2022）"]
        },
        {
            "id": "m29", "name": "遮阴廊架+攀爬植物",
            "description": "在缺乏行道树的路段设置钢结构廊架，种植紫藤、葡萄、凌霄等攀爬植物，形成绿色遮阳通道，降低体感温度。",
            "tags": ["南方城市", "夏季高温多日照区域的通学路"],
            "cases": [
                {"city": "中国青岛", "name": "城阳山火主题公园入口廊道", "image": "case_57.jpg"},
                {"city": "西班牙巴塞罗那", "name": "Green Axis项目", "image": "case_58.jpg"}
            ],
            "refs": ["王娴等（2024）"]
        }
    ]
}

# Integrity checks
assert len(data["categories"]) == 6, f"Expected 6 categories, got {len(data['categories'])}"
assert len(data["measures"]) == 29, f"Expected 29 measures, got {len(data['measures'])}"

measure_ids = {m["id"] for m in data["measures"]}
for cat in data["categories"]:
    for cond in cat["conditions"]:
        for mid in cond["measures"]:
            assert mid in measure_ids, f"Measure {mid} referenced in {cat['id']}/{cond['id']} not found"

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Written {os.path.getsize(OUTPUT)} bytes to {OUTPUT}")
print("Validation OK: 6 categories, 29 measures, all references valid.")
