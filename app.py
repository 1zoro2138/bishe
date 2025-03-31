from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import io
import chardet
import base64
import numpy as np
from datetime import datetime

app = Flask(__name__)

# 数据根目录（热力图数据）
DATA_ROOT = r"D:\movie_box_office\static\data"

# 折线图和柱状图数据路径
TREND_DATA_PATH = r"D:\movie_box_office\static\data\Province_Analysis"

# 电影封面图片列表
POSTERS = [
    'nezha2.jpg', 'tangtan1900.jpg', 'wusha3.jpg',
    'xiaoxiaodewo.jpg', 'xiongchumo.jpg', 'xiongshishaonian2.jpg'
]

# 月份名称到数字的映射（热力图用）
MONTH_MAP = {
    'January': '01', 'February': '02', 'March': '03', 'April': '04',
    'May': '05', 'June': '06', 'July': '07', 'August': '08',
    'September': '09', 'October': '10', 'November': '11', 'December': '12'
}

# 新增 ECharts 图表数据路径
ECHARTS_ROOT = r"D:\movie_box_office\templates"

# 省份周边省份映射
PROVINCE_NEIGHBORS = {
    '北京市': ['天津市', '河北省', '山西省', '内蒙古自治区'],
    '天津市': ['北京市', '河北省', '山东省'],
    '河北省': ['北京市', '天津市', '山西省', '内蒙古自治区', '辽宁省', '山东省', '河南省'],
    '山西省': ['河北省', '内蒙古自治区', '陕西省', '河南省'],
    '内蒙古自治区': ['黑龙江省', '吉林省', '辽宁省', '河北省', '山西省', '陕西省', '宁夏回族自治区', '甘肃省'],
    '辽宁省': ['内蒙古自治区', '吉林省', '河北省'],
    '吉林省': ['黑龙江省', '内蒙古自治区', '辽宁省'],
    '黑龙江省': ['内蒙古自治区', '吉林省'],
    '上海市': ['江苏省', '浙江省'],
    '江苏省': ['上海市', '浙江省', '安徽省', '山东省'],
    '浙江省': ['上海市', '江苏省', '安徽省', '江西省', '福建省'],
    '安徽省': ['江苏省', '浙江省', '江西省', '河南省', '湖北省'],
    '福建省': ['浙江省', '江西省', '广东省'],
    '江西省': ['浙江省', '安徽省', '福建省', '湖北省', '湖南省', '广东省'],
    '山东省': ['河北省', '河南省', '江苏省'],
    '河南省': ['河北省', '山西省', '安徽省', '山东省', '湖北省', '陕西省'],
    '湖北省': ['河南省', '安徽省', '江西省', '湖南省', '重庆市', '陕西省'],
    '湖南省': ['江西省', '湖北省', '广东省', '广西壮族自治区', '贵州省', '重庆市'],
    '广东省': ['福建省', '江西省', '湖南省', '广西壮族自治区', '海南省'],
    '广西壮族自治区': ['广东省', '湖南省', '贵州省', '云南省'],
    '海南省': ['广东省'],
    '重庆市': ['湖北省', '湖南省', '贵州省', '四川省', '陕西省'],
    '四川省': ['重庆市', '贵州省', '云南省', '西藏自治区', '青海省', '甘肃省', '陕西省'],
    '贵州省': ['湖南省', '广西壮族自治区', '云南省', '四川省', '重庆市'],
    '云南省': ['四川省', '贵州省', '广西壮族自治区', '西藏自治区'],
    '西藏自治区': ['新疆维吾尔自治区', '青海省', '四川省', '云南省'],
    '陕西省': ['山西省', '河南省', '湖北省', '重庆市', '四川省', '甘肃省', '宁夏回族自治区', '内蒙古自治区'],
    '甘肃省': ['内蒙古自治区', '宁夏回族自治区', '陕西省', '四川省', '青海省', '新疆维吾尔自治区'],
    '青海省': ['新疆维吾尔自治区', '甘肃省', '四川省', '西藏自治区'],
    '宁夏回族自治区': ['内蒙古自治区', '甘肃省', '陕西省'],
    '新疆维吾尔自治区': ['西藏自治区', '青海省', '甘肃省']
}

# 中国传统文化电影分类数据
traditional_culture_films = {
    "武侠功夫": [
        {
            "title": "卧虎藏龙",
            "year": "2000",
            "director": "李安",
            "cultural_elements": "太极拳 | 道家思想 | 古典园林美学",
            "impact": "首部获得奥斯卡最佳外语片的华语电影，向世界展现中国武侠精神，李慕白与玉娇龙的师徒情与江湖恩怨成为经典",
            "image": "wohucanglong.jpg"
        },
        {
            "title": "一代宗师",
            "year": "2013",
            "director": "王家卫",
            "cultural_elements": "咏春拳 | 八卦掌 | 民国武林文化",
            "impact": "王家卫以诗意镜头刻画叶问与宫二的传奇，获奥斯卡最佳摄影提名，推动传统武术文化的国际化表达",
            "image": "yidaizongshi.jpg"
        },
        {
            "title": "叶问系列",
            "year": "2008-2019",
            "director": "叶伟信",
            "cultural_elements": "咏春拳 | 武德精神 | 家国情怀",
            "impact": "甄子丹塑造的叶问成为文化符号，系列票房破30亿，带动传统武术题材复兴",
            "image": "yewen.jpg"
        }
    ],
    "历史史诗": [
        {
            "title": "英雄",
            "year": "2002",
            "director": "张艺谋",
            "cultural_elements": "秦代书法 | 古琴乐 | 刺客文化",
            "impact": "开创中国商业大片时代，以'天下'为核的历史观引发争议与讨论",
            "image": "yingxiong.jpg"
        },
        {
            "title": "孔子",
            "year": "2010",
            "director": "胡玫",
            "cultural_elements": "儒家思想 | 春秋礼制 | 古琴与诗经",
            "impact": "周润发主演的孔子形象获国际认可，推动传统文化在当代的反思",
            "image": "kongzi.jpg"
        },
        {
            "title": "鸿门宴传奇",
            "year": "2011",
            "director": "李仁港",
            "cultural_elements": "楚汉相争 | 汉服礼仪 | 权谋博弈",
            "impact": "以戏剧化手法重现历史名局，服饰与场景考据严谨",
            "image": "hongmenyanchuanqi.jpg"
        }
    ],
    "神话传说": [
        {
            "title": "大闹天宫",
            "year": "1961",
            "director": "万籁鸣/唐澄",
            "cultural_elements": "孙悟空 | 道教神话 | 传统壁画风格",
            "impact": "中国动画史上的里程碑，获伦敦国际电影节最佳影片奖，影响后世神话改编作品",
            "image": "danaotiangong.jpg"
        },
        {
            "title": "哪吒之魔童降世",
            "year": "2019",
            "director": "饺子",
            "cultural_elements": "哪吒传说 | 阴阳五行 | 道教符咒",
            "impact": "票房破50亿，重塑传统神话IP，探讨'打破偏见'的现代主题",
            "image": "nezha.jpg"
        },
        {
            "title": "白蛇：缘起",
            "year": "2019",
            "director": "黄家康/赵霁",
            "cultural_elements": "白蛇传 | 水墨画风 | 古典音乐",
            "impact": "国产动画技术突破，将民间传说与东方美学结合",
            "image": "baishe.jpg"
        }
    ],
    "戏曲艺术": [
        {
            "title": "霸王别姬",
            "year": "1993",
            "director": "陈凯歌",
            "cultural_elements": "京剧程派艺术 | 性别认同 | 历史变迁",
            "impact": "戛纳电影节金棕榈奖，张国荣饰演的程蝶衣成为影史经典，推动京剧文化的全球关注",
            "image": "bawangbieji.jpg"
        },
        {
            "title": "梅兰芳",
            "year": "2008",
            "director": "陈凯歌",
            "cultural_elements": "京剧表演 | 民国梨园行规",
            "impact": "黎明演绎京剧大师梅兰芳，展现传统艺术在时代变革中的坚守",
            "image": "meilanfang.jpg"
        },
        {
            "title": "游园惊梦",
            "year": "2001",
            "director": "白先勇",
            "cultural_elements": "昆曲《牡丹亭》 | 江南园林 | 民国贵族生活",
            "impact": "以昆曲为线索，探讨情欲与封建礼教的冲突",
            "image": "youyuanjingmeng.jpg"
        }
    ],
    "民俗非遗": [
        {
            "title": "百鸟朝凤",
            "year": "2013",
            "director": "吴天明",
            "cultural_elements": "唢呐艺术 | 关中民俗 | 师徒传承",
            "impact": "引发对非遗保护的社会讨论，吴天明导演遗作，催生出'下跪式营销'事件",
            "image": "bainiaochaofeng.jpg"
        },
        {
            "title": "变脸",
            "year": "1995",
            "director": "谢洪",
            "cultural_elements": "川剧变脸 | 江湖艺人文化",
            "impact": "谢洪导演作品，通过江湖艺人的命运折射传统技艺的濒危处境",
            "image": "bianlian.jpg"
        },
        {
            "title": "阿诗玛",
            "year": "1964",
            "director": "刘贤明",
            "cultural_elements": "彝族撒尼族传说 | 民族服饰与音乐",
            "impact": "中国首部彩色宽银幕音乐歌舞片，被列为'20世纪经典民族电影'",
            "image": "ashima.jpg"
        }
    ],
    "哲学生活美学": [
        {
            "title": "饮食男女",
            "year": "1994",
            "director": "李安",
            "cultural_elements": "中华饮食文化 | 儒家家庭伦理",
            "impact": "李安以烹饪隐喻亲情，获奥斯卡最佳外语片提名",
            "image": "yinshinannv.jpg"
        },
        {
            "title": "推手",
            "year": "1991",
            "director": "李安",
            "cultural_elements": "太极拳 | 中西文化冲突",
            "impact": "李安'父亲三部曲'开篇，探讨传统与现代的代际矛盾",
            "image": "tuishou.jpg"
        },
        {
            "title": "春江水暖",
            "year": "2019",
            "director": "顾晓刚",
            "cultural_elements": "江南水乡 | 家族伦理 | 东方哲学",
            "impact": "以江南水乡为背景，表达中国传统家族伦理与美学，获柏林电影节最佳摄影奖",
            "image": "chunjiangshuinuan.jpg"
        }
    ]
}

# 获取热力图数据
def load_all_data():
    all_data = []
    for year in ['2024', '2025']:
        year_path = os.path.join(DATA_ROOT, year)
        if os.path.exists(year_path):
            for filename in os.listdir(year_path):
                if filename.endswith('.csv'):
                    file_path = os.path.join(year_path, filename)
                    df = pd.read_csv(file_path)
                    for month_name, month_num in MONTH_MAP.items():
                        if month_name in filename and year in filename:
                            df['月份'] = f"{year}-{month_num}"
                            break
                    else:
                        df['月份'] = '未知'
                        print(f"警告: 文件 {filename} 未匹配到月份")
                    all_data.append(df)
    combined_data = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    months = [f"{year}.{month:02d}" for year in [2024, 2025] for month in range(1, 13 if year == 2024 else 2)]
    time_range = "2024.1 - 2025.1"
    return combined_data, time_range, months


# 数据加载和处理函数
def read_and_combine_trend_data(file_path):
    print(f"开始加载数据，目录: {file_path}")
    if not os.path.exists(file_path):
        print(f"错误: 目录 {file_path} 不存在")
        return pd.DataFrame()
    dfs = []
    files = os.listdir(file_path)
    print(f"目录中找到 {len(files)} 个文件: {files}")
    for file in files:
        if file.endswith('.csv'):
            try:
                file_path_full = os.path.join(file_path, file)
                with open(file_path_full, 'rb') as f:
                    rawdata = f.read()
                    result = chardet.detect(rawdata)
                    encoding = result['encoding']
                province = file.split('数据汇总.csv')[0]
                df = pd.read_csv(file_path_full, encoding=encoding)
                df['省份'] = province
                dfs.append(df)
                print(f"成功加载文件: {file}, 行数: {len(df)}")
            except Exception as e:
                print(f"读取文件 {file} 时出错: {e}")
    combined_df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
    print(f"数据加载完成，总行数: {len(combined_df)}")
    return combined_df


def convert_box_office(value):
    try:
        if isinstance(value, str):
            if '亿' in value:
                return float(value.replace('亿', '')) * 10000
            elif '万' in value:
                return float(value.replace('万', ''))  # 统一单位为"万元"
            else:
                # 尝试将其他字符串直接转换为浮点数
                return float(value)
        elif isinstance(value, (int, float)):
            return float(value)
        return 0.0  # 如果无法转换，返回0
    except (ValueError, TypeError):
        print(f"无法转换值: {value}，类型: {type(value)}")
        return 0.0


def convert_person(value):
    try:
        if isinstance(value, str):
            if '万' in value:
                return float(value.replace('万', '')) * 10  # 将万人次转换为千人次
            else:
                # 尝试将其他字符串直接转换为浮点数
                return float(value)
        elif isinstance(value, (int, float)):
            return float(value)
        return 0.0  # 如果无法转换，返回0
    except (ValueError, TypeError):
        print(f"无法转换人次值: {value}，类型: {type(value)}")
        return 0.0


def preprocess_data(combined_df):
    if combined_df.empty:
        print("预处理失败: 数据为空")
        return combined_df
    try:
        combined_df['综合票房（万）'] = combined_df['综合票房'].apply(convert_box_office)
        combined_df['分账票房（万）'] = combined_df['分账票房'].apply(convert_box_office)
        combined_df['人次（千）'] = combined_df['人次'].apply(convert_person)  # 改为人次（千）
        combined_df['综合票房（万）'] = pd.to_numeric(combined_df['综合票房（万）'], errors='coerce').fillna(0)
        combined_df['分账票房（万）'] = pd.to_numeric(combined_df['分账票房（万）'], errors='coerce').fillna(0)
        combined_df['人次（千）'] = pd.to_numeric(combined_df['人次（千）'], errors='coerce').fillna(0)  # 改为人次（千）
        print(f"预处理完成，列名: {combined_df.columns.tolist()}")
        return combined_df
    except Exception as e:
        print(f"预处理数据时出错: {e}")
        return combined_df


# 格式化数字，添加千位分隔符
def format_number(value):
    if value >= 10000:
        return f"{value/10000:.2f}亿"
    return f"{value:,.0f}"


# 首页 - 电影封面轮播和导航
@app.route('/')
def index():
    return render_template('index.html', posters=POSTERS)


# 全国票房分析-热力图
@app.route('/heatmap')
def heatmap():
    movie_data, time_range, months = load_all_data()
    selected_month = request.args.get('month')
    if not movie_data.empty:
        try:
            if '月份' in movie_data.columns:
                print(f"月份列样本: {movie_data['月份'].head().tolist()}")
                print(f"月份列唯一值: {sorted(movie_data['月份'].unique().tolist())}")
                print(f"数据总行数: {len(movie_data)}")
            else:
                print("数据中无'月份'列")
            if selected_month and '月份' in movie_data.columns:
                internal_month = selected_month.replace('.', '-')
                filtered_data = movie_data[movie_data['月份'] == internal_month]
            else:
                filtered_data = movie_data
            heatmap_data = filtered_data.groupby('省区市')['票房（万元）'].sum().to_dict()
            print(f"Heatmap Data ({selected_month or 'All'}):", heatmap_data)
        except KeyError as e:
            return render_template('heatmap.html', heatmap_data=json.dumps({}), error=f"数据中缺少列: {e}",
                                   time_range=time_range, months=months, selected_month=selected_month)
        except Exception as e:
            return render_template('heatmap.html', heatmap_data=json.dumps({}), error=f"筛选错误: {str(e)}",
                                   time_range=time_range, months=months, selected_month=selected_month)
    else:
        heatmap_data = {}
        print("No data loaded")
    return render_template('heatmap.html', heatmap_data=json.dumps(heatmap_data), time_range=time_range, months=months,
                           selected_month=selected_month)


# 省份票房分析详情
@app.route('/province_analysis/<province_name>')
def province_analysis(province_name):
    try:
        # 处理省份名称，确保与文件名匹配
        # 如果省份名称不包含"省"、"市"或"自治区"，则添加适当的后缀
        if not any(suffix in province_name for suffix in ['省', '市', '自治区']):
            # 检查是否为直辖市
            if province_name in ['北京', '上海', '天津', '重庆']:
                province_name = f"{province_name}市"
            # 检查是否为自治区
            elif province_name in ['内蒙古', '广西', '西藏', '宁夏', '新疆']:
                if province_name == '广西':
                    province_name = "广西壮族自治区"
                elif province_name == '宁夏':
                    province_name = "宁夏回族自治区"
                elif province_name == '新疆':
                    province_name = "新疆维吾尔自治区"
                else:
                    province_name = f"{province_name}自治区"
            else:
                # 其他情况为普通省份
                province_name = f"{province_name}省"
        
        print(f"处理后的省份名称: {province_name}")
        
        # 获取省份完整CSV文件路径
        province_file = f"{province_name}数据汇总.csv"
        province_file_path = os.path.join(TREND_DATA_PATH, province_file)
        
        if not os.path.exists(province_file_path):
            return render_template('error.html', error=f"未找到{province_name}的数据文件")
        
        # 读取省份数据 - 尝试多种编码方式
        try:
            with open(province_file_path, 'rb') as f:
                rawdata = f.read()
                result = chardet.detect(rawdata)
                encoding = result['encoding']
                if not encoding or encoding == 'ascii':
                    encoding = 'utf-8'  # 使用默认编码
                    
            # 尝试读取数据
            try:
                province_df = pd.read_csv(province_file_path, encoding=encoding)
            except:
                # 如果失败，尝试其它常见编码
                for enc in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        province_df = pd.read_csv(province_file_path, encoding=enc)
                        print(f"成功使用 {enc} 编码读取文件")
                        break
                    except:
                        continue
                else:
                    # 所有编码都失败的情况
                    return render_template('error.html', error=f"无法读取{province_name}的数据文件，编码问题")
        except Exception as e:
            print(f"读取文件时出错: {str(e)}")
            return render_template('error.html', error=f"读取{province_name}数据文件时出错: {str(e)}")
        
        # 检查并清理数据列 
        # 清理列名中可能的BOM或不可见字符
        province_df.columns = [col.strip().replace('\ufeff', '') for col in province_df.columns]
        
        # 重命名与预期不符的列名
        column_mapping = {
            '综合票房（万）': '综合票房（万）', 
            '综合票房': '综合票房',
            '分账票房（万）': '分账票房（万）',
            '分账票房': '分账票房',
            '人次（千）': '人次（千）',
            '人次': '人次'
        }
        
        # 对照映射更新列名
        for expected_col, actual_col in column_mapping.items():
            if expected_col in province_df.columns:
                # 列名已正确
                pass
            elif actual_col in province_df.columns:
                # 将实际列名映射到预期列名
                province_df[expected_col] = province_df[actual_col]
        
        # 预处理数据 - 确保存在必要的列
        if '综合票房' not in province_df.columns and '综合票房（万）' not in province_df.columns:
            province_df['综合票房'] = 0
        if '分账票房' not in province_df.columns and '分账票房（万）' not in province_df.columns:
            province_df['分账票房'] = 0
        if '人次' not in province_df.columns and '人次（千）' not in province_df.columns:
            province_df['人次'] = 0
        
        # 转换票房和人次数据
        if '综合票房（万）' not in province_df.columns:
            province_df['综合票房（万）'] = province_df['综合票房'].apply(convert_box_office)
        if '分账票房（万）' not in province_df.columns:
            province_df['分账票房（万）'] = province_df['分账票房'].apply(convert_box_office)
        if '人次（千）' not in province_df.columns:
            province_df['人次（千）'] = province_df['人次'].apply(convert_person)
        
        # 确保数据为数值类型，非数值替换为0
        province_df['综合票房（万）'] = pd.to_numeric(province_df['综合票房（万）'], errors='coerce').fillna(0)
        province_df['分账票房（万）'] = pd.to_numeric(province_df['分账票房（万）'], errors='coerce').fillna(0)
        province_df['人次（千）'] = pd.to_numeric(province_df['人次（千）'], errors='coerce').fillna(0)
        
        # 处理山东省特殊格式 - 检查"亿"单位并转换
        if province_name == "山东省":
            for idx, row in province_df.iterrows():
                for col in ['综合票房（万）', '分账票房（万）', '人次（千）']:
                    if col in province_df.columns:
                        val = province_df.at[idx, col]
                        # 转换类型
                        if isinstance(val, str):
                            if '亿' in val:
                                try:
                                    new_val = float(val.replace('亿', '')) * 10000  # 亿转万
                                    province_df.at[idx, col] = new_val
                                except:
                                    province_df.at[idx, col] = 0
        
        # 计算总统计数据
        total_box_office = float(province_df['综合票房（万）'].astype(float).sum())
        total_share_box_office = float(province_df['分账票房（万）'].astype(float).sum())
        total_audience = float(province_df['人次（千）'].astype(float).sum())
        
        # 准备图表数据
        dates = province_df['时间范围'].tolist()
        box_office_data = province_df['综合票房（万）'].astype(float).tolist()
        share_box_office_data = province_df['分账票房（万）'].astype(float).tolist()
        audience_data = province_df['人次（千）'].astype(float).tolist()
        
        # 将数据转换为简单的Python基本类型
        box_office_data = [float(x) for x in box_office_data]
        share_box_office_data = [float(x) for x in share_box_office_data]
        audience_data = [float(x) for x in audience_data]
        
        # 获取周边省份数据
        neighbor_provinces = PROVINCE_NEIGHBORS.get(province_name, [])[:5]  # 最多取5个周边省份
        neighbor_data = []
        
        # 读取所有周边省份的数据
        for neighbor in neighbor_provinces:
            neighbor_file = f"{neighbor}数据汇总.csv"
            neighbor_file_path = os.path.join(TREND_DATA_PATH, neighbor_file)
            
            if os.path.exists(neighbor_file_path):
                try:
                    # 尝试多种编码方式读取
                    with open(neighbor_file_path, 'rb') as f:
                        rawdata = f.read()
                        result = chardet.detect(rawdata)
                        encoding = result['encoding']
                        if not encoding or encoding == 'ascii':
                            encoding = 'utf-8'  # 使用默认编码
                    
                    try:
                        neighbor_df = pd.read_csv(neighbor_file_path, encoding=encoding)
                    except:
                        # 如果失败，尝试其它常见编码
                        for enc in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                            try:
                                neighbor_df = pd.read_csv(neighbor_file_path, encoding=enc)
                                break
                            except:
                                continue
                        else:
                            # 所有编码都失败，跳过这个省份
                            print(f"无法读取周边省份 {neighbor} 的数据文件")
                            continue
                    
                    # 清理列名
                    neighbor_df.columns = [col.strip().replace('\ufeff', '') for col in neighbor_df.columns]
                    
                    # 预处理数据 - 确保存在必要的列
                    if '综合票房' not in neighbor_df.columns and '综合票房（万）' not in neighbor_df.columns:
                        neighbor_df['综合票房'] = 0
                    if '分账票房' not in neighbor_df.columns and '分账票房（万）' not in neighbor_df.columns:
                        neighbor_df['分账票房'] = 0
                    if '人次' not in neighbor_df.columns and '人次（千）' not in neighbor_df.columns:
                        neighbor_df['人次'] = 0
                    
                    # 转换票房和人次数据
                    if '综合票房（万）' not in neighbor_df.columns:
                        neighbor_df['综合票房（万）'] = neighbor_df['综合票房'].apply(convert_box_office)
                    if '分账票房（万）' not in neighbor_df.columns:
                        neighbor_df['分账票房（万）'] = neighbor_df['分账票房'].apply(convert_box_office)
                    if '人次（千）' not in neighbor_df.columns:
                        neighbor_df['人次（千）'] = neighbor_df['人次'].apply(convert_person)
                    
                    # 确保数据为数值类型
                    neighbor_df['综合票房（万）'] = pd.to_numeric(neighbor_df['综合票房（万）'], errors='coerce').fillna(0)
                    neighbor_df['分账票房（万）'] = pd.to_numeric(neighbor_df['分账票房（万）'], errors='coerce').fillna(0)
                    neighbor_df['人次（千）'] = pd.to_numeric(neighbor_df['人次（千）'], errors='coerce').fillna(0)
                    
                    # 处理特殊格式
                    if neighbor == "山东省":
                        for idx, row in neighbor_df.iterrows():
                            for col in ['综合票房（万）', '分账票房（万）', '人次（千）']:
                                if col in neighbor_df.columns:
                                    val = neighbor_df.at[idx, col]
                                    if isinstance(val, str):
                                        if '亿' in val:
                                            try:
                                                new_val = float(val.replace('亿', '')) * 10000  # 亿转万
                                                neighbor_df.at[idx, col] = new_val
                                            except:
                                                neighbor_df.at[idx, col] = 0
                    
                    # 计算总票房和观影人次
                    total_n_box_office = float(neighbor_df['综合票房（万）'].astype(float).sum())
                    total_n_share_box_office = float(neighbor_df['分账票房（万）'].astype(float).sum())
                    total_n_audience = float(neighbor_df['人次（千）'].astype(float).sum())
                    
                    neighbor_data.append({
                        '省份': neighbor,
                        '综合票房（万）': total_n_box_office,
                        '分账票房（万）': total_n_share_box_office,
                        '人次（千）': total_n_audience
                    })
                except Exception as e:
                    print(f"处理周边省份 {neighbor} 数据时出错: {str(e)}")
                    continue
        
        # 添加当前省份进行对比
        neighbor_data.append({
            '省份': province_name,
            '综合票房（万）': total_box_office,
            '分账票房（万）': total_share_box_office,
            '人次（千）': total_audience
        })
        
        # 准备与周边省份对比数据
        neighbor_provinces_chart = [item['省份'] for item in neighbor_data]
        neighbor_box_office = [float(item['综合票房（万）']) for item in neighbor_data]
        neighbor_share_box_office = [float(item['分账票房（万）']) for item in neighbor_data]
        neighbor_audience = [float(item['人次（千）']) for item in neighbor_data]
        
        # 获取时间范围
        time_range = "2024.1 - 2025.1"
        
        # 传递数据到模板
        return render_template('province_analysis.html',
                              province=province_name,
                              time_range=time_range,
                              total_box_office=total_box_office,
                              total_share_box_office=total_share_box_office,
                              total_audience=total_audience,
                              dates=dates,
                              box_office_data=box_office_data,
                              share_box_office_data=share_box_office_data,
                              audience_data=audience_data,
                              neighbor_provinces=neighbor_provinces_chart,
                              neighbor_box_office=neighbor_box_office,
                              neighbor_share_box_office=neighbor_share_box_office,
                              neighbor_audience=neighbor_audience,
                              data=province_df.to_dict('records'),
                              format_number=format_number)
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"生成省份分析详情时出错: {str(e)}")
        print(f"错误详情: {error_trace}")
        return render_template('error.html', error=f"生成{province_name}分析详情时出错: {str(e)}")


# 全国票房分析 - 各月票房TOP15
@app.route('/monthly_top15')
def monthly_top15():
    return render_template('monthly_top15.html')


# 各月票房TOP15数据API接口
@app.route('/monthly_top15_data')
def monthly_top15_data():
    try:
        # 读取movie_box_office.html文件中的图表数据
        file_path = os.path.join(ECHARTS_ROOT, 'movie_box_office.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取ECharts配置数据
        start_index = content.find('option_')
        start_index = content.find('= {', start_index)
        end_index = content.find('};', start_index)
        
        # 提取JSON数据
        chart_json = content[start_index+2:end_index+1]
        
        return chart_json
    except Exception as e:
        print(f"加载月度票房TOP15数据出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 各省份票房月展示
@app.route('/province_monthly')
def province_monthly():
    return render_template('province_monthly.html')


# 各省份票房月展示数据API接口
@app.route('/province_monthly_data')
def province_monthly_data():
    try:
        # 读取province_city_box_office_2024_2025.html文件中的图表数据
        file_path = os.path.join(ECHARTS_ROOT, 'province_city_box_office_2024_2025.html')
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取ECharts配置数据
        start_index = content.find('option_')
        start_index = content.find('= {', start_index)
        end_index = content.find('};', start_index)
        
        # 提取JSON数据
        chart_json = content[start_index+2:end_index+1]
        
        return chart_json
    except Exception as e:
        print(f"加载省份月度数据出错: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 城市票房详情
@app.route('/city/<city_name>')
def city_detail(city_name):
    movie_data, _, _ = load_all_data()
    city_data = movie_data[movie_data.get('城市', movie_data['省区市']) == city_name]
    total_box_office = city_data['票房（万元）'].sum()
    return render_template('city_detail.html', city=city_name, total_box_office=total_box_office)


# 哪吒 2 单独分析
@app.route('/nezha2')
def nezha2():
    # 直接渲染优化后的哪吒2分析页面，该页面现已包含所有相关数据
    return render_template('nezha2.html')


# 系列电影分析 -> 传统文化电影分析
@app.route('/traditional_culture')
def traditional_culture():
    # 传递数据到模板
    return render_template('traditional_culture.html', film_categories=traditional_culture_films)


# 各省份综合票房趋势折线图（Chart.js 版本）
@app.route('/trend')
def trend():
    print("收到 /trend 请求，开始处理")
    try:
        combined_df = read_and_combine_trend_data(TREND_DATA_PATH)
        if combined_df.empty:
            print("折线图数据加载失败，返回错误页面")
            return render_template('trend.html',
                                   error="无法加载折线图数据，请检查目录 D:\movie_box_office\static\data\Province_Analysis 是否包含有效的 CSV 文件")

        combined_df = preprocess_data(combined_df)
        chart_data = {}
        for province, group in combined_df.groupby('省份'):
            chart_data[province] = {
                'labels': group['时间范围'].tolist(),
                'data': group['综合票房（万）'].tolist()
            }
        return render_template('trend.html', chart_data=json.dumps(chart_data))
    except Exception as e:
        print(f"/trend 处理出错: {str(e)}")
        return render_template('trend.html', error=f"生成折线图时发生错误: {str(e)}")


# 各省对比柱状图
@app.route('/bar', methods=['GET', 'POST'])
def bar():
    print("收到 /bar 请求，开始处理")
    try:
        combined_df = read_and_combine_trend_data(TREND_DATA_PATH)
        if combined_df.empty:
            print("柱状图数据加载失败，返回错误页面")
            return render_template('bar.html',
                                   error="无法加载柱状图数据，请检查目录 D:\movie_box_office\static\data\Province_Analysis 是否包含有效的 CSV 文件")

        combined_df = preprocess_data(combined_df)
        provinces = sorted(combined_df['省份'].unique().tolist())

        # 获取用户选择的省份
        selected_province1 = request.form.get('province1') if request.method == 'POST' else None
        selected_province2 = request.form.get('province2') if request.method == 'POST' else None

        # 按省份汇总数据
        grouped_df = combined_df.groupby('省份')[['综合票房（万）', '分账票房（万）', '人次（千）']].sum().reset_index()  # 改为人次（千）

        # 如果用户选择了两个省份，过滤数据
        if selected_province1 and selected_province2 and selected_province1 != selected_province2:
            filtered_df = grouped_df[grouped_df['省份'].isin([selected_province1, selected_province2])]
            title = f"{selected_province1} 和 {selected_province2} 对比"
        else:
            filtered_df = grouped_df
            title = "各省不同指标对比"

        # 绘图设置
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        plt.figure(figsize=(10 if len(filtered_df) <= 2 else 18, 10))

        num_regions = len(filtered_df)
        width = 0.25
        x = np.arange(num_regions)

        plt.bar(x - width, filtered_df['综合票房（万）'], width, label='综合票房（万）')
        plt.bar(x, filtered_df['分账票房（万）'], width, label='分账票房（万）')
        plt.bar(x + width, filtered_df['人次（千）'], width, label='人次（千）')  # 改为人次（千）

        plt.xticks(x, filtered_df['省份'], rotation=45)
        plt.ylabel('数值')
        plt.title(title)
        plt.legend()

        # 生成图片
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        image_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        print("柱状图生成成功")
        return render_template('bar.html', image_data=image_base64, provinces=provinces,
                               selected_province1=selected_province1, selected_province2=selected_province2)
    except Exception as e:
        print(f"/bar 处理出错: {str(e)}")
        return render_template('bar.html', error=f"生成柱状图时发生错误: {str(e)}", provinces=[])


# 电影详情页面
@app.route('/film_detail/<film_title>')
def film_detail(film_title):
    # 电影票房和评分数据
    film_data = {
        "一代宗师": {
            "box_office": {
                "total": "3.96亿人民币",
                "first_week": "1.37亿人民币",
                "highest_single_day": "0.39亿人民币"
            },
            "ratings": {
                "douban": "8.2",
                "douban_votes": "663458",
                "imdb": "7.9",
                "imdb_votes": "28700"
            },
            "analysis": """《一代宗师》是王家卫导演2013年推出的武侠电影，以咏春宗师叶问为主线，展现了20世纪初的武林变迁与民国风云。影片以诗意化的视觉语言，讲述叶问与宫二的武道交集与情感纠葛，呈现出"一个时代的终结，一代宗师的孤独"。影片特别注重对咏春拳、八卦掌等武术流派的深入展现，通过精心设计的动作场景与哲学对白，探讨了武术精神的本质与传承。王家卫独特的美学风格与徐浩峰对武术的专业解读相结合，使影片既具有艺术性，又保持了武术的真实性。《一代宗师》获得香港电影金像奖最佳电影奖，并入围奥斯卡最佳摄影提名，是近年来最具影响力的武侠题材电影之一。"""
        },
        "鸿门宴传奇": {
            "box_office": {
                "total": "2.2亿人民币",
                "first_week": "0.8亿人民币",
                "highest_single_day": "0.21亿人民币"
            },
            "ratings": {
                "douban": "6.4",
                "douban_votes": "108853",
                "imdb": "6.1",
                "imdb_votes": "1872"
            },
            "analysis": """《鸿门宴传奇》是李仁港导演的历史战争片，通过项羽与刘邦的对决，展现了秦末楚汉相争的历史风云。影片将历史故事戏剧化处理，以鸿门宴和范增、张良的谋士对弈为核心，辅以项羽与虞姬的爱情故事，呈现了一个情感与权谋交织的历史画卷。在文化表现上，影片重现了秦末汉初的服饰、兵器和战争场面，以及古代权谋政治的运作方式。尽管在历史准确性上有所取舍，但透过项羽性格中的刚烈与仁慈、张良与范增的智谋较量，以及楚汉争霸中的权力游戏，电影体现了中国古代"义"与"利"的文化冲突，以及英雄在命运与选择面前的挣扎。"""
        },
        "卧虎藏龙": {
            "box_office": {
                "total": "2.13亿美元",
                "first_week": "660万美元",
                "highest_single_day": "120万美元"
            },
            "ratings": {
                "douban": "8.4",
                "douban_votes": "517548",
                "imdb": "7.9",
                "imdb_votes": "287000"
            },
            "analysis": """《卧虎藏龙》是李安导演的武侠代表作，以精致的影像语言和深厚的文化内涵，向世界展示了东方美学的独特魅力。该片融合了武侠、爱情与哲学思考，通过李慕白、俞秀莲、玉娇龙等人物的命运，探讨了东方传统文化中的情感克制、道德规范与个人自由的矛盾。影片中的武术场景被赋予了诗意化的表达，尤其是竹林打斗和屋顶轻功等段落，既展示了中国武术的美感，又将其提升为精神层面的象征。"""
        },
        "英雄": {
            "box_office": {
                "total": "1.77亿美元",
                "first_week": "1800万美元",
                "highest_single_day": "580万美元"
            },
            "ratings": {
                "douban": "8.1",
                "douban_votes": "875000",
                "imdb": "7.9",
                "imdb_votes": "188000"
            },
            "analysis": """《英雄》是张艺谋导演的视觉盛宴之作，以"刺客与秦王"的历史故事为线索，通过不同颜色的叙事段落，呈现出多角度的"真相"探寻。影片利用色彩象征手法构建叙事，红色代表激情与仇恨，蓝色象征追忆与冷静，白色寓意纯洁与牺牲，黑色暗示权力与死亡，绿色则暗喻和平与希望。在文化表达上，《英雄》将中国传统书法、音乐、武术、绘画等艺术形式完美融入电影语言中。"""
        },
        "霸王别姬": {
            "box_office": {
                "total": "5700万美元",
                "first_week": "180万美元",
                "highest_single_day": "45万美元"
            },
            "ratings": {
                "douban": "9.6",
                "douban_votes": "2322866",
                "imdb": "8.5",
                "imdb_votes": "42000"
            },
            "analysis": """《霸王别姬》通过几十年的历史变迁，展现了中国传统京剧艺术的魅力和命运。影片以程蝶衣和段小楼这对京剧搭档为核心，通过他们的人生际遇，折射出中国现代史的动荡与变革。程蝶衣的角色塑造尤为精彩，其对艺术的执着和对角色的痴迷，使他在现实与舞台之间的界限逐渐模糊，最终走向悲剧结局。电影中的京剧表演不仅仅是艺术展示，更是人物命运的象征和隐喻。"""
        },
        "叶问系列": {
            "box_office": {
                "total": "3亿美元(系列总和)",
                "first_week": "500万美元",
                "highest_single_day": "80万美元"
            },
            "ratings": {
                "douban": "8.0",
                "douban_votes": "750000",
                "imdb": "7.5",
                "imdb_votes": "220000"
            },
            "analysis": """《叶问》系列电影以咏春拳大师叶问的传奇人生为蓝本，展现了中国传统武术的精髓和民族精神。系列影片通过叶问面对外敌入侵、民族危机的种种挑战，彰显了中国武术的博大精深和武者的品格操守。甄子丹的精湛演技和扎实的武术功底，使叶问这一形象栩栩如生，成为华语功夫电影的经典角色。影片中的动作场面不仅追求视觉震撼，更注重表现武术的实用性和哲学内涵。"""
        },
        "大闹天宫": {
            "box_office": {
                "total": "无精确数据",
                "first_week": "-",
                "highest_single_day": "-"
            },
            "ratings": {
                "douban": "9.3",
                "douban_votes": "258760",
                "imdb": "7.9",
                "imdb_votes": "6200"
            },
            "analysis": """《大闹天宫》是中国动画史上的里程碑之作，以独特的中国美术风格演绎西游记故事。影片采用传统中国绘画与民间艺术相结合的表现手法，将京剧脸谱、敦煌壁画、古代版画等元素融入角色设计与场景构图中。尤其是孙悟空形象的塑造，集勇敢、机智、反抗精神于一身，成为几代中国人深刻的文化记忆。作为中国首部彩色长篇动画电影，《大闹天宫》奠定了"中国学派"动画的艺术风格，在国际舞台上获得广泛赞誉，被誉为中国动画的"黄金时代"经典之作。"""
        },
        "白蛇：缘起": {
            "box_office": {
                "total": "4.5亿人民币",
                "first_week": "9500万人民币",
                "highest_single_day": "2200万人民币"
            },
            "ratings": {
                "douban": "7.8",
                "douban_votes": "382451",
                "imdb": "7.5",
                "imdb_votes": "4500"
            },
            "analysis": """《白蛇：缘起》以中国传统民间传说《白蛇传》为蓝本，讲述了白蛇与许仙前世的爱情故事。影片突破传统动画表现形式，采用水墨写意的美术风格，将中国传统文化中的道家思想、人妖恋题材以现代动画技术重新演绎。故事主题聚焦于"爱与执念"，探讨了因执念而生的爱情，以及记忆与身份认同的关系。作为国产动画电影的代表作，该片在视觉效果与叙事深度上均有出色表现，展现了中国动画工业的创新与进步。"""
        },
        "姜子牙": {
            "box_office": {
                "total": "16.03亿人民币",
                "first_week": "13亿人民币",
                "highest_single_day": "3.2亿人民币"
            },
            "ratings": {
                "douban": "6.9",
                "douban_votes": "516728",
                "imdb": "6.7",
                "imdb_votes": "3100"
            },
            "analysis": """《姜子牙》改编自中国神话《封神演义》，聚焦封神大战之后的姜子牙，探讨命运、选择与救赎的主题。影片保持了中国神话的壮阔背景，同时融入现代价值观的思考，让传统神话人物姜子牙呈现出全新的精神面貌。在美术设计上，影片借鉴了中国传统绘画与古代建筑风格，创造出独特的东方神话视觉世界。这部作品是近年来中国动画"神话宇宙"构建的重要一环，既传承了中国传统文化，又以当代视角重新诠释经典故事，推动了国产动画电影的工业化与艺术性发展。"""
        },
        "梅兰芳": {
            "box_office": {
                "total": "7000万人民币",
                "first_week": "1800万人民币",
                "highest_single_day": "430万人民币"
            },
            "ratings": {
                "douban": "7.1",
                "douban_votes": "108576",
                "imdb": "6.8",
                "imdb_votes": "2800"
            },
            "analysis": """《梅兰芳》以京剧大师梅兰芳的艺术人生为主线，展现了二十世纪前半叶京剧艺术的发展与传承。影片刻画了梅兰芳如何突破传统，革新京剧艺术，特别是其对"旦角"表演艺术的卓越贡献。通过梅兰芳的故事，电影深入探讨了艺术与人生、传统与创新的关系，以及中国传统文化在现代社会的价值与意义。影片在舞台表演场景中，精心还原了梅派艺术的精髓，包括其独特的身段、唱腔与扮相，为观众呈现了一场视听盛宴，也成为记录和传承中国传统戏曲艺术的重要影像作品。"""
        },
        "饮食男女": {
            "box_office": {
                "total": "3200万美元",
                "first_week": "280万美元",
                "highest_single_day": "70万美元"
            },
            "ratings": {
                "douban": "9.1",
                "douban_votes": "428965",
                "imdb": "8.1",
                "imdb_votes": "73000"
            },
            "analysis": """《饮食男女》通过精致的烹饪场景展现中华饮食文化与家庭关系的微妙联系。李安导演将中国传统烹饪艺术作为情感传递的媒介，展示了食物在中国文化中超越简单营养需求的深层意义。影片中老朱一家四口的故事，折射出台湾社会现代化进程中家庭结构与价值观的变迁，以及传统与现代、东方与西方文化碰撞下的代际冲突与和解。片中令人垂涎的烹饪段落不仅是视觉享受，更是情感表达的载体，厨房成为家庭情感交流的中心空间。这部作品被视为李安"家庭三部曲"的收官之作，既具东方文化特色，又有普遍的人性关怀，成为华语电影中展现中国生活美学的经典之作。"""
        },
        "长城": {
            "box_office": {
                "total": "3.32亿美元",
                "first_week": "6600万美元",
                "highest_single_day": "2100万美元"
            },
            "ratings": {
                "douban": "5.0",
                "douban_votes": "375281",
                "imdb": "6.1",
                "imdb_votes": "127000"
            },
            "analysis": """《长城》以中国古代长城为背景，融合了中国历史文化元素与好莱坞特效大片风格。影片展现了古代中国军事文化、兵法与防御工事，尤其是长城这一世界奇迹的军事用途与文化象征。影片通过外国雇佣兵与中国军队共同抵抗怪兽入侵的故事，探讨了信任、勇气与文化碰撞的主题。虽然在叙事深度上有所欠缺，但影片在视觉呈现上颇具特色，尤其是色彩鲜明的军团服饰、精巧的武器设计与宏伟的长城场景，展示了东方军事美学的独特魅力，为国际观众提供了一个了解中国古代军事文化的窗口。"""
        },
        "孔子": {
            "box_office": {
                "total": "1.54亿人民币",
                "first_week": "2700万人民币",
                "highest_single_day": "600万人民币"
            },
            "ratings": {
                "douban": "5.4",
                "douban_votes": "78392",
                "imdb": "5.6",
                "imdb_votes": "2200"
            },
            "analysis": """《孔子》以中国古代思想家孔子的生平事迹为主线，展现了先秦时期的社会状况和儒家思想的形成过程。影片通过孔子周游列国、教书育人的经历，表现了儒家"仁、义、礼、智、信"等核心价值观。尽管在艺术表达上略显平淡，但影片对孔子形象的塑造和儒家思想的阐释具有一定的文化传播价值。作为一部聚焦中国传统文化核心人物的作品，该片为国际观众提供了了解孔子及儒家思想的窗口，展现了中华文明的精神根基。"""
        },
        "哪吒之魔童降世": {
            "box_office": {
                "total": "50.36亿人民币",
                "first_week": "20亿人民币",
                "highest_single_day": "3.4亿人民币"
            },
            "ratings": {
                "douban": "8.4",
                "douban_votes": "2017935",
                "imdb": "7.8",
                "imdb_votes": "10627"
            },
            "analysis": """《哪吒之魔童降世》创新性地改编了中国传统神话《封神演义》中哪吒的故事，将"天生魔丸"的设定与"我命由我不由天"的现代价值观完美结合。影片在视觉呈现上融合了中国传统美学与现代动画技术，打造出独特的东方神话世界。哪吒与敖丙的关系重塑，从传统的敌对变为理解与救赎，展现了当代人文关怀。电影不仅在中国创造了50亿人民币的票房奇迹，成为中国影史票房亚军和全球单一市场票房最高的动画电影，还在海外市场获得广泛认可，被誉为中国动画产业的里程碑之作。影片的成功标志着中国动画电影打破了"动画天花板"，推动了国产动画向工业化、成人化方向发展。"""
        },
        "推手": {
            "box_office": {
                "total": "797万新台币",
                "first_week": "125万新台币",
                "highest_single_day": "30万新台币"
            },
            "ratings": {
                "douban": "8.2",
                "douban_votes": "87451",
                "imdb": "7.5",
                "imdb_votes": "6780"
            },
            "analysis": """《推手》作为李安的导演处女作，以精致的叙事手法展现了东西方文化碰撞下的代际冲突与和解。影片通过郎雄饰演的太极大师朱时进移居美国后面临的文化适应问题，深入探讨了中国传统家庭价值观与美国个人主义之间的矛盾。太极"推手"作为中国传统武术技巧，在片中成为文化沟通的隐喻，既是保持平衡又是化解冲突的哲学表达。影片细腻刻画人物内心世界，展现了华人移民在异国他乡的孤独、怀旧与坚持，以及东方文化中"忍"与"让"的处世哲学。作为李安"父亲三部曲"之首，该片奠定了导演探索文化冲突与家庭情感的创作基调，荣获亚太影展最佳影片奖，开启了李安日后国际电影事业的辉煌。"""
        },
        "游园惊梦": {
            "box_office": {
                "total": "无精确数据",
                "first_week": "-",
                "highest_single_day": "-"
            },
            "ratings": {
                "douban": "7.8",
                "douban_votes": "5429",
                "imdb": "7.3",
                "imdb_votes": "1240"
            },
            "analysis": """《游园惊梦》是汤显祖著名昆曲《牡丹亭》的重要片段，被誉为昆曲艺术的精华所在。影片以精美的舞台表演为主，展现了杜丽娘游园、梦幻与柳梦梅相会的经典段落，昆曲"水磨腔"的优美唱腔与精致的身段表演相得益彰。影片保留了昆曲的传统表演形式，包括程式化的动作、脸谱与服饰，展现了这一"百戏之祖"的独特美学风格。作为中国戏曲电影的代表作，该片不仅记录了珍贵的非物质文化遗产，也通过电影媒介向更广泛的观众传播了昆曲艺术。影片中女主角对爱情的追求与自由意志的表达，超越了时代局限，展现了中国古典文学中浪漫主义精神的闪光点，成为戏曲电影传承传统文化的典范之作。"""
        },
        "变脸": {
            "box_office": {
                "total": "无精确数据",
                "first_week": "-",
                "highest_single_day": "-"
            },
            "ratings": {
                "douban": "8.4",
                "douban_votes": "7892",
                "imdb": "7.6",
                "imdb_votes": "1527"
            },
            "analysis": """《变脸》以四川传统川剧的独特技艺"变脸"为核心，展现了这一被列入国家级非物质文化遗产的绝技。影片既是艺术表演的记录，也融入了川剧故事情节，通过老艺人与年轻传人的关系，探讨传统艺术的传承与创新。变脸技艺在影片中展现出惊人的视觉效果，演员在瞬间切换不同的脸谱，象征人物心理与情感的变化。除变脸外，影片还展示了川剧中的吐火、滚灯等绝活，以及川剧特有的音乐风格和表演程式。作为中国戏曲电影的代表作，该片不仅向世界展示了中国传统戏曲艺术的魅力，也记录了濒临失传的民间艺术，对推动川剧保护与传承具有重要意义，展现了中国传统表演艺术中的技巧精湛与美学追求。"""
        },
        "阿诗玛": {
            "box_office": {
                "total": "无精确数据",
                "first_week": "-",
                "highest_single_day": "-"
            },
            "ratings": {
                "douban": "7.9",
                "douban_votes": "5931",
                "imdb": "7.0",
                "imdb_votes": "336"
            },
            "analysis": """《阿诗玛》改编自云南石林彝族撒尼人的民间叙事长诗，是新中国早期优秀的民族歌舞片。影片真实记录了撒尼族的传统服饰、歌舞与生活习俗，展现了云南石林独特的喀斯特地貌景观。故事讲述了美丽善良的撒尼族姑娘阿诗玛与勇敢的青年阿黑相爱，却遭到头人之子阿支的阻挠与迫害的悲剧。影片由杨丽坤主演，其充满活力的表演和民族特色的歌舞成为经典。作为一部展现少数民族文化的重要电影，《阿诗玛》记录了珍贵的民族艺术形式，荣获1982年西班牙桑坦德国际音乐电影节最佳舞蹈片奖。时至今日，阿诗玛的形象已成为云南石林的文化符号，成为彝族撒尼人文化的重要代表，对宣传与保护少数民族文化起到了积极作用。"""
        },

        "百鸟朝凤": {
            "box_office": {
                "total": "8000万人民币",
                "first_week": "1600万人民币",
                "highest_single_day": "390万人民币"
            },
            "ratings": {
                "douban": "8.1",
                "douban_votes": "186043",
                "imdb": "7.6",
                "imdb_votes": "2400"
            },
            "analysis": """《百鸟朝凤》以陕西关中地区的唢呐艺术为核心，讲述了老艺人游天鸣传授技艺、坚守传统的故事。影片深入展现了中国传统葬礼文化中唢呐艺术的地位与意义，特别是具有地方特色的"百鸟朝凤"曲目所承载的文化内涵。通过师徒间的传承与矛盾，影片探讨了非物质文化遗产在现代社会中面临的生存危机与传承困境。导演吴天明以质朴的手法记录了乡村生活与民间艺术的点滴细节，展现了传统音乐文化的独特魅力。作为一部关注中国传统音乐遗产的影片，《百鸟朝凤》不仅是对唢呐艺术的致敬，也是对中国乡土文化与非物质文化遗产保护的深刻思考，引发了社会对传统文化传承问题的广泛关注。"""
        },

        "春江水暖": {
            "box_office": {
                "total": "1.6亿人民币",
                "first_week": "2800万人民币",
                "highest_single_day": "650万人民币"
            },
            "ratings": {
                "douban": "7.9",
                "douban_votes": "179465",
                "imdb": "7.4",
                "imdb_votes": "3700"
            },
            "analysis": """《春江水暖》以江南水乡为背景，通过一个普通家族四代人的生活片段，展现了中国传统家族伦理与现代生活的交融。影片借鉴中国传统绘画审美，采用长镜头与精心构图，将江南水乡的自然风光与人文景观融为一体，创造出独特的东方美学空间。故事围绕家族成员间的微妙情感与代际关系展开，细腻刻画了中国式家庭中的矛盾与和解、传统与变迁。影片富含东方哲学思想，尤其是对生命流转、自然循环的思考，以及对中国传统"和合"理念的现代诠释。作为一部充满生活智慧与美学追求的作品，《春江水暖》展现了中国当代电影对传统文化的创新表达，其对江南水乡生活美学的细腻捕捉，获得柏林电影节最佳摄影奖，成为展现中国传统生活美学的代表作品。"""
        }
    }

    # 在传统文化电影数据中查找匹配的电影
    for category, films in traditional_culture_films.items():
        for film in films:
            if film['title'] == film_title:
                # 准备电影数据
                movie_data = {
                    'category': category,
                    'film': film,
                    'box_office': {
                        'total': '数据获取中...',
                        'first_week': '数据获取中...',
                        'highest_single_day': '数据获取中...'
                    },
                    'ratings': {
                        'douban': '暂无',
                        'douban_votes': '0',
                        'imdb': '暂无',
                        'imdb_votes': '0'
                    },
                    'analysis': '该电影的详细分析正在整理中，敬请期待...',
                    'related_films': []
                }

                # 如果有电影数据，则更新
                if film_title in film_data:
                    movie_data['box_office'] = film_data[film_title]['box_office']
                    movie_data['ratings'] = film_data[film_title]['ratings']
                    movie_data['analysis'] = film_data[film_title]['analysis']

                # 确保电影数据包含cultural_elements字段
                if 'elements' in film and 'cultural_elements' not in film:
                    film['cultural_elements'] = film['elements']

                # 添加同类型的相关电影（最多3部）
                count = 0
                for related_film in films:
                    if related_film['title'] != film_title and count < 3:
                        # 确保相关电影也具有cultural_elements字段
                        if 'elements' in related_film and 'cultural_elements' not in related_film:
                            related_film['cultural_elements'] = related_film['elements']
                        movie_data['related_films'].append(related_film)
                        count += 1

                return render_template('film_detail.html', **movie_data)

    # 如果没有找到匹配的电影，返回错误页面
    return render_template('error.html', error=f"未找到电影: {film_title}")

if __name__ == '__main__':
    app.run(debug=True)
