# -*- coding: utf-8 -*-
"""
生成行业数据报告页面 (industry.html)，展示"卓创资讯"相关数据。
处理三个Excel文件：
- 板冻大胸历史价格.xlsx
- 鸡苗历史价格.xlsx
- 琵琶腿历史价格.xlsx
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime
from matplotlib.ticker import FuncFormatter
import matplotlib.font_manager as fm
from html_utils import generate_header, generate_navigation, generate_footer, write_html_report, generate_image_tag

# 检查并配置中文字体
def setup_chinese_font():
    """检查并配置中文字体，返回可用的字体名称"""
    # 检查常见的中文字体路径
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/msyh.ttc",     # 微软雅黑
        "C:/Windows/Fonts/msyh.ttf"      # 微软雅黑备选路径
    ]
    
    available_font = None
    
    # 检查是否有可用的中文字体
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font_prop = fm.FontProperties(fname=font_path)
                available_font = font_prop
                print(f"已加载中文字体: {font_path}")
                break
            except Exception as e:
                print(f"加载字体 {font_path} 失败: {e}")
    
    if available_font is None:
        print("警告: 未找到可用的中文字体，将使用系统默认字体")
        available_font = fm.FontProperties(family="sans-serif")
    
    return available_font

# 配置文件和路径
def generate_industry_charts(industry_data, output_dir):
    """
    生成行业价格趋势图
    
    参数:
        industry_data (dict): 包含各个产品价格数据的字典
        output_dir (str): 输出目录
        
    返回:
        list: 生成的图表文件路径列表
    """
    # 预先定义可能会使用到的变量
    salesTotal = 0  # 避免引用错误
    productionTotal = 0  # 避免引用错误
    
    chart_paths = []
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置seaborn样式
    sns.set_theme(style="whitegrid")
    
    # 配置中文字体
    chinese_font = setup_chinese_font()
    
    # 定义产品的显示顺序
    product_order = ['鸡苗', '毛鸡', '板冻大胸', '琵琶腿']
    
    # 定义专业配色方案
    color_palette = {
        '鸡苗': '#1976D2',
        '毛鸡': '#2E7D32',
        '板冻大胸': '#C62828',
        '琵琶腿': '#7B1FA2'
    }
    
    # 按照指定顺序生成趋势图
    for product_name in product_order:
        if product_name in industry_data:
            data = industry_data[product_name]
            if data is not None and not data.empty:
                try:
                    # 创建更大的图表
                    plt.figure(figsize=(18, 8))
                    ax = plt.gca()
                    
                    # 确保日期列格式正确
                    if 'date' in data.columns:
                        # 尝试将日期转换为datetime格式
                        data['date'] = pd.to_datetime(data['date'], errors='coerce')
                        
                        # 排序数据确保时间线一致性
                        data = data.sort_values('date')
                        
                        # 计算价格变化率（用于后续分析）
                        data['price_pct_change'] = data['price'].pct_change() * 100
                        
                        # 找出最高价和最低价
                        max_price_idx = data['price'].idxmax()
                        min_price_idx = data['price'].idxmin()
                        max_price_row = data.loc[max_price_idx]
                        min_price_row = data.loc[min_price_idx]
                        
                        # 计算合适的数据点抽样间隔（避免拥挤）
                        total_points = len(data)
                        sample_interval = max(1, total_points // 30)  # 最多显示约30个点
                        
                        # 绘制价格趋势线，使用透明度和更细的线条
                        ax.plot(data['date'], data['price'], 
                               color=color_palette.get(product_name, '#1976D2'),
                               linewidth=2.5, alpha=0.85)
                        
                        # 添加稀疏的数据点标记
                        ax.scatter(data['date'][::sample_interval], 
                                  data['price'][::sample_interval],
                                  color=color_palette.get(product_name, '#1976D2'),
                                  s=60, zorder=5, alpha=0.8)
                        
                        # 突出显示最高和最低价格点
                        ax.scatter(max_price_row['date'], max_price_row['price'], 
                                  color='#D32F2F', s=120, zorder=6, 
                                  edgecolor='white', linewidth=2)
                        ax.scatter(min_price_row['date'], min_price_row['price'], 
                                  color='#388E3C', s=120, zorder=6, 
                                  edgecolor='white', linewidth=2)
                        
                        # 为最高点和最低点添加标签
                        ax.annotate(f"最高: ¥{max_price_row['price']:.2f}",
                                   xy=(max_price_row['date'], max_price_row['price']),
                                   xytext=(15, 15), textcoords='offset points',
                                   fontsize=14, fontweight='bold', fontproperties=chinese_font,
                                   arrowprops=dict(arrowstyle='->', color='#D32F2F', lw=1.5))
                        
                        ax.annotate(f"最低: ¥{min_price_row['price']:.2f}",
                                   xy=(min_price_row['date'], min_price_row['price']),
                                   xytext=(15, -25), textcoords='offset points',
                                   fontsize=14, fontweight='bold', fontproperties=chinese_font,
                                   arrowprops=dict(arrowstyle='->', color='#388E3C', lw=1.5))
                        
                        # 设置图表标题和轴标签
                        plt.title(f'{product_name}历史价格趋势', fontsize=36, fontweight='bold', pad=20, 
                                  fontproperties=chinese_font, color='#222222',
                                  bbox=dict(facecolor='#f9f9f9', edgecolor='#dddddd', boxstyle='round,pad=0.5',
                                           alpha=0.9))
                        plt.xlabel('日期', fontsize=16, labelpad=10, fontproperties=chinese_font)
                        plt.ylabel('价格 (元/kg)', fontsize=16, labelpad=10, fontproperties=chinese_font)
                        
                        # 增大轴刻度标签字体
                        ax.tick_params(axis='both', labelsize=14)
                        
                        # 格式化y轴为货币格式
                        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f"¥{x:.2f}"))
                        
                        # 优化x轴日期格式
                        # 主刻度 - 年份
                        ax.xaxis.set_major_locator(mdates.YearLocator())
                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y年'))
                        
                        # 次刻度 - 每3个月
                        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
                        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%m月'))
                        
                        # 强调主刻度网格线
                        ax.grid(which='major', linestyle='-', linewidth=0.7, alpha=0.3)
                        ax.grid(which='minor', linestyle=':', linewidth=0.5, alpha=0.2)
                        
                        # 设置x轴标签的旋转角度
                        plt.setp(ax.get_xticklabels(which='both'), rotation=45, ha='right', fontproperties=chinese_font)
                        
                        # 如果数据点超过365个（大约一年），添加30日移动平均线
                        if len(data) > 365:
                            data['MA30'] = data['price'].rolling(window=30).mean()
                            ax.plot(data['date'], data['MA30'], 
                                   color='#FF6F00', linewidth=2, 
                                   linestyle='--', alpha=0.7,
                                   label='30日移动平均')
                            plt.legend(loc='upper left', frameon=True, framealpha=0.9,
                                      prop={'size': 14, 'family': chinese_font.get_name()})
                        
                        # 调整纵轴范围，留出标注空间
                        y_min, y_max = ax.get_ylim()
                        y_range = y_max - y_min
                        ax.set_ylim(y_min - y_range * 0.05, y_max + y_range * 0.1)
                        
                        # 添加数据来源注释
                        plt.figtext(0.99, 0.01, '数据来源: 卓创资讯', 
                                    horizontalalignment='right', fontsize=12, 
                                    style='italic', alpha=0.7, fontproperties=chinese_font)
                        
                        # 使用紧凑布局防止元素溢出
                        plt.tight_layout()
                        
                        # 保存图表，增加DPI提高清晰度
                        chart_filename = f"{product_name}_price_trend.png"
                        chart_path = os.path.join(output_dir, chart_filename)
                        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
                        plt.close()
                        
                        print(f"已生成{product_name}价格趋势图: {chart_path}")
                        chart_paths.append(chart_filename)
                    else:
                        print(f"警告: {product_name}数据缺少日期列")
                except Exception as e:
                    print(f"生成{product_name}价格趋势图时出错: {str(e)}")
            else:
                print(f"警告: {product_name}数据为空或无效")
    
    return chart_paths

def _generate_industry_content(industry_data, chart_paths, output_dir):
    """生成行业数据部分的HTML内容
    
    Args:
        industry_data (dict): 行业价格数据字典
        chart_paths (list): 图表文件路径列表
        output_dir (str): 输出目录，用于检查图片文件
        
    Returns:
        str: 行业数据部分的HTML代码
    """
    # 预先定义可能会使用到的变量
    salesTotal = 0  # 避免引用错误
    productionTotal = 0  # 避免引用错误
    
    # 检查是否有有效数据
    has_data = industry_data and any(data is not None and not data.empty for data in industry_data.values())
    
    if not has_data:
        return """
        <div class="section">
            <div class="section-header"><h2>行业价格趋势</h2></div>
            <div class="section-body"><p>无行业价格数据可供显示。</p></div>
        </div>
        """
    
    html = '''
    <div class="section">
        <div class="section-header">
            <h2>行业价格趋势</h2>
        </div>
        <div class="section-body">
            <div class="data-card">
                <div class="data-card-header">
                    <h3 class="data-card-title">卓创资讯价格监测</h3>
                </div>
                <div class="data-card-body">
                    <p>以下是卓创资讯监测的主要农产品价格趋势，数据定期更新。</p>
    '''
    
    # 定义产品的显示顺序
    product_order = ['鸡苗', '毛鸡', '板冻大胸', '琵琶腿']
    
    # 创建一个图表路径的字典，方便按顺序查找
    chart_dict = {}
    
    # 基于文件名推断产品名称，确保正确的产品-图表匹配
    for chart_filename in chart_paths:
        # 从文件名推断产品名称，例如从"毛鸡_price_trend.png"提取"毛鸡"
        for product_name in product_order:
            if chart_filename.startswith(product_name):
                chart_dict[product_name] = chart_filename
                break
    
    # 按照指定顺序添加趋势图
    for product_name in product_order:
        if product_name in industry_data and product_name in chart_dict:
            chart_filename = chart_dict[product_name]
            chart_path = os.path.join(output_dir, chart_filename)
            if os.path.exists(chart_path):
                html += f'''
                <div class="subsection">
                    <h4>{product_name}价格趋势</h4>
                    <div class="chart-container">
                        {generate_image_tag(chart_filename, alt_text=f"{product_name}价格趋势图", css_class="chart")}
                    </div>
                </div>
                '''
            else:
                print(f"警告: {product_name}趋势图未找到: {chart_path}")
    
    # 删除数据表格部分
    
    html += '''
                </div> <!-- Close data-card-body -->
            </div> <!-- Close data-card -->
        </div> <!-- Close section-body -->
    </div> <!-- Close section -->
    '''
    
    return html

def generate_industry_page(industry_data, output_dir):
    """生成 industry.html 页面
    
    Args:
        industry_data (dict): 行业价格数据字典，格式为 {产品名: 数据DataFrame}
        output_dir (str): HTML 文件输出目录
    """
    print(f"{'='*20} 开始生成 industry.html 页面 {'='*20}")
    print(f"接收到的industry_data中的键: {list(industry_data.keys() if industry_data else [])}")
    
    # 避免引用未定义的变量
    # 定义可能会使用到的变量
    salesTotal = 0  # 预先定义，防止引用错误
    
    # 生成各个产品的价格趋势图
    chart_paths = generate_industry_charts(industry_data, output_dir)
    print(f"生成的chart_paths: {chart_paths}")
    
    # 生成页面
    page_title = "春雪食品生品产销分析报告 - 行业价格"
    header_html = generate_header(title=page_title, output_dir=output_dir)
    nav_html = generate_navigation(active_page="industry")
    industry_content_html = _generate_industry_content(industry_data, chart_paths, output_dir)
    footer_html = generate_footer()
    
    full_html = header_html + "<div class='container'>" + nav_html + industry_content_html + "</div>" + footer_html
    
    write_html_report(full_html, "industry.html", output_dir)
    print(f"industry.html 页面已生成在 {output_dir}")
    
    # 检查生成的文件
    with open(os.path.join(output_dir, "industry.html"), 'r', encoding='utf-8') as f:
        html_content = f.read()
        for product_name in ['鸡苗', '毛鸡', '板冻大胸', '琵琶腿']:
            if f'{product_name}价格趋势' in html_content:
                print(f"确认: {product_name}价格趋势已包含在HTML中")
            else:
                print(f"警告: {product_name}价格趋势未包含在HTML中")
    
    print(f"{'='*20} industry.html 页面生成完成 {'='*20}")

# 示例使用（用于测试）
if __name__ == '__main__':
    # 创建测试数据
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='W')
    
    # 鸡苗价格数据
    chicken_data = pd.DataFrame({
        'date': dates,
        'price': [2.5 + i*0.1 + abs(i % 10 - 5)*0.2 for i in range(len(dates))],
        'change': [0.1 if i % 3 == 0 else -0.05 if i % 3 == 1 else 0 for i in range(len(dates))]
    })
    
    # 毛鸡价格数据
    raw_chicken_data = pd.DataFrame({
        'date': dates,
        'price': [12 + i*0.15 + abs(i % 9 - 4)*0.4 for i in range(len(dates))],
        'change': [0.12 if i % 3 == 0 else -0.08 if i % 3 == 1 else 0 for i in range(len(dates))]
    })
    
    # 板冻大胸价格数据
    breast_data = pd.DataFrame({
        'date': dates,
        'price': [15 + i*0.2 - abs(i % 8 - 4)*0.5 for i in range(len(dates))],
        'change': [-0.2 if i % 4 == 0 else 0.1 if i % 4 == 1 else 0 for i in range(len(dates))]
    })
    
    # 琵琶腿价格数据
    leg_data = pd.DataFrame({
        'date': dates,
        'price': [18 + i*0.15 + abs(i % 12 - 6)*0.3 for i in range(len(dates))],
        'change': [0.15 if i % 5 == 0 else -0.1 if i % 5 == 1 else 0 for i in range(len(dates))]
    })
    
    # 创建行业数据字典
    test_industry_data = {
        '鸡苗': chicken_data,
        '毛鸡': raw_chicken_data,
        '板冻大胸': breast_data,
        '琵琶腿': leg_data
    }
    
    # 测试生成页面
    output_directory = './test_output'
    os.makedirs(output_directory, exist_ok=True)
    generate_industry_page(test_industry_data, output_directory)
    print(f"测试 industry.html 已生成在 {output_directory}") 