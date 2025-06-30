# -*- coding: utf-8 -*-
"""
生成产销率分析报告页面 (ratio.html)。
"""

import os
import pandas as pd
from datetime import datetime
from html_utils import generate_header, generate_navigation, generate_footer, write_html_report, generate_image_tag

def _generate_product_sales_ratio_detail_panel(date_str, data):
    """生成每日产品产销率明细面板 (移植自原 _generate_product_sales_ratio_detail_panel)

    Args:
        date_str (str): 日期字符串 (YYYY-MM-DD).
        data (pd.DataFrame): 当日的产品产销明细数据。

    Returns:
        str: 单个面板的HTML代码。
    """
    # Add data validation check
    if data is None or data.empty:
        print(f"警告: {date_str} 的产品产销率明细数据为空，跳过该面板生成")
        # Return an empty div or a message panel
        return f'''
        <div id="ratioPanel_{date_str}" class="ratio-panel" style="display: none;">
            <div class="ratio-panel-header">
                 <h4>产销率明细 - {date_str}</h4>
                 <button onclick="toggleRatioPanel('{date_str}', event)" class="close-button"><i class="bi bi-x-lg"></i></button>
            </div>
            <div class="ratio-panel-body"><p>当日无详细产品产销数据。</p></div>
        </div>
        '''

    panel_html = f'''
    <div id="ratioPanel_{date_str}" class="ratio-panel" style="display: none;">
        <div class="ratio-panel-header">
            <h4>产销率明细 - {date_str}</h4>
            <div class="ratio-panel-controls">
                <input type="text" id="ratioSearch_{date_str}" onkeyup="searchTableInPanel('ratio', '{date_str}')" placeholder="搜索产品..." class="search-input">
                <button onclick="toggleRatioPanel('{date_str}', event)" class="close-button">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
        </div>
        <div class="ratio-panel-body">
            <div class="sales-table-container"> <!-- Reusing sales table container style -->
                <table id="ratioTable_{date_str}">
                    <thead>
                        <tr>
                            <th>产品名称</th>
                            <th>销量</th>
                            <th>产量</th>
                            <th>产销率</th>
                        </tr>
                    </thead>
                    <tbody>
    '''

    # Sort data by '产销率' descending, handle potential errors
    try:
        # Ensure '产销率' column exists and is numeric before sorting
        if '产销率' in data.columns and pd.api.types.is_numeric_dtype(data['产销率']):
            data_sorted = data.sort_values(by='产销率', ascending=False, na_position='last')
        else:
            print(f"警告: {date_str} 的 '产销率' 列不存在或非数值，无法排序。")
            data_sorted = data # Use original data if sorting fails
    except Exception as e:
        print(f"排序产销率明细时出错 ({date_str}): {e}")
        data_sorted = data # Fallback to original data

    # Add product data rows
    required_cols = ['品名', '销量', '产量', '产销率']
    if not all(col in data_sorted.columns for col in required_cols):
         panel_html += "<tr><td colspan='4'>数据列不完整。</td></tr>"
    else:
        for _, row in data_sorted.iterrows():
            # Safely get values
            prod_name = row.get('品名', 'N/A')
            sales_val = row.get('销量')
            prod_val = row.get('产量')
            ratio_val = row.get('产销率')

            # Format numeric values safely
            try:
                sales_display = f"{int(sales_val):,}" if pd.notna(sales_val) else "-"
            except (ValueError, TypeError):
                sales_display = str(sales_val)
            try:
                prod_display = f"{int(prod_val):,}" if pd.notna(prod_val) else "-"
            except (ValueError, TypeError):
                prod_display = str(prod_val)

            ratio_class = ""
            ratio_display = "-"
            if pd.notna(ratio_val):
                 try:
                     ratio_float = float(ratio_val)
                     ratio_display = f"{int(ratio_float)}%"
                     if ratio_float > 100:
                         ratio_class = "high-value" # Shortage
                     elif ratio_float < 90: # Adjusted threshold slightly for low value emphasis
                         ratio_class = "low-value"  # Surplus
                     # else: implicitly balanced, no class needed
                 except (ValueError, TypeError):
                      ratio_display = str(ratio_val) # Display as is if not convertible to float

            panel_html += f'''
                        <tr>
                            <td>{prod_name}</td>
                            <td class="text-right">{sales_display}</td>
                            <td class="text-right">{prod_display}</td>
                            <td class="{ratio_class} text-right">{ratio_display}</td>
                        </tr>
            '''

        # Calculate and add total row safely
        try:
            total_sales = data['销量'].sum() if '销量' in data.columns and pd.api.types.is_numeric_dtype(data['销量']) else 0
            total_production = data['产量'].sum() if '产量' in data.columns and pd.api.types.is_numeric_dtype(data['产量']) else 0
            total_ratio = (total_sales / total_production * 100) if total_production > 0 else 0

            total_ratio_class = ""
            if total_ratio > 100:
                total_ratio_class = "high-value"
            elif total_ratio < 90:
                total_ratio_class = "low-value"

            panel_html += f'''
                    <tr class="total-row">
                        <td><strong>合计</strong></td>
                        <td class="text-right"><strong>{int(total_sales):,}</strong></td>
                        <td class="text-right"><strong>{int(total_production):,}</strong></td>
                        <td class="{total_ratio_class} text-right"><strong>{int(total_ratio)}%</strong></td>
                    </tr>
            '''
        except Exception as e:
            print(f"计算合计行时出错 ({date_str}): {e}")
            panel_html += "<tr><td colspan='4'>计算合计时出错。</td></tr>"

    panel_html += '''
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    '''
    return panel_html

def _generate_product_sales_ratio_detail(product_sales_ratio_data):
    """生成产品产销率明细部分 (卡片 + 面板) - MODIFIED: Only generates title and link.

    Args:
        product_sales_ratio_data (list): 包含每日产品明细数据的列表 (used only to check if data exists).

    Returns:
        str: 产品产销率明细部分的HTML代码 (title + link or no data message).
    """
    # Check data validity
    if not product_sales_ratio_data or len(product_sales_ratio_data) == 0:
        print("警告: 产品产销率明细数据为空，跳过明细部分生成")
        return """
        <div class="data-card">
            <div class="data-card-header"><h3 class="data-card-title">每日产品产销率明细</h3></div>
            <div class="data-card-body"><p>无产品产销率明细数据。</p></div>
        </div>
        """

    detail_html = '''
    <div class="data-card">
        <div class="data-card-header">
            <h3 class="data-card-title">每日产品产销率明细</h3>
        </div>
        <div class="data-card-body">
            <p>每日各产品的详细产销率数据已移至详细数据页面。</p>
            <p><a href="details.html#daily-ratio-details" class="btn btn-primary">点击查看每日明细数据</a></p>
             <!-- Removed the grid of cards and panel generation -->
        </div> <!-- Close data-card-body -->
    </div> <!-- Close data-card -->
    '''
    return detail_html

def _generate_ratio_content(production_sales_ratio, product_sales_ratio_data, output_dir):
    """生成产销率分析部分的HTML内容 (移植自原 _generate_production_sales_ratio_section)

    Args:
        production_sales_ratio (dict): 每日总体产销率数据, {date: {'ratio': val, ...}}
        product_sales_ratio_data (list): 每日产品明细数据列表, [{'date': dt, 'data': df}, ...]
        output_dir (str): 输出目录，用于检查图片文件。

    Returns:
        str: 产销率分析部分的HTML代码。
    """
    # Check data validity
    has_summary_data = production_sales_ratio is not None and isinstance(production_sales_ratio, dict) and len(production_sales_ratio) > 0
    has_detail_data = product_sales_ratio_data is not None and isinstance(product_sales_ratio_data, list) and len(product_sales_ratio_data) > 0

    if not has_summary_data and not has_detail_data:
        print("警告: 产销率汇总和明细数据均为空，跳过产销率部分生成")
        return """
        <div class="section">
            <div class="section-header"><h2>产销率分析</h2></div>
            <div class="section-body"><p>无产销率数据可供显示。</p></div>
        </div>
        """

    ratio_section_html = '''
    <div class="section">
        <div class="section-header">
            <h2>产销率分析</h2>
        </div>
        <div class="section-body">
    '''

    # Ratio Overview Card
    if has_summary_data:
        try:
            valid_ratios = [data.get('ratio', 0) for data in production_sales_ratio.values() if isinstance(data.get('ratio'), (int, float))]
            if not valid_ratios:
                raise ValueError("无有效的比率数据")

            avg_ratio = sum(valid_ratios) / len(valid_ratios)
            max_ratio_item = max(production_sales_ratio.items(), key=lambda x: x[1].get('ratio', -1) if isinstance(x[1].get('ratio'), (int, float)) else -1)
            min_ratio_item = min(production_sales_ratio.items(), key=lambda x: x[1].get('ratio', float('inf')) if isinstance(x[1].get('ratio'), (int, float)) else float('inf'))

            max_date = max_ratio_item[0].strftime('%Y-%m-%d') if hasattr(max_ratio_item[0], 'strftime') else str(max_ratio_item[0])
            max_ratio = max_ratio_item[1].get('ratio', 0)
            min_date = min_ratio_item[0].strftime('%Y-%m-%d') if hasattr(min_ratio_item[0], 'strftime') else str(min_ratio_item[0])
            min_ratio = min_ratio_item[1].get('ratio', 0)

            avg_status = "balanced"
            avg_status_text = "平衡"
            if avg_ratio < 90:
                avg_status = "surplus"
                avg_status_text = "产品积压"
            elif avg_ratio > 110:
                avg_status = "shortage"
                avg_status_text = "库存消耗"

            ratio_section_html += f'''
            <div class="data-card">
                <div class="data-card-header">
                    <h3 class="data-card-title">产销率概览</h3>
                </div>
                <div class="data-card-body">
                    <p>产销率是衡量企业生产与销售平衡性的重要指标，计算公式为：<strong>产销率 = 销量 / 产量 × 100%</strong>。</p>
                    <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">注：产量销量均不包含副产品和鲜品</p>
                    <div class="inventory-summary"> <!-- Reusing inventory card style -->
                        <div class="inventory-card">
                            <h4><i class="bi bi-speedometer2"></i> 平均产销率</h4>
                            <div class="value {avg_status}">{avg_ratio:.0f}%</div>
                            <div class="ratio-date">整体状态: {avg_status_text}</div>
                        </div>
                        <div class="inventory-card">
                            <h4><i class="bi bi-arrow-up-circle"></i> 最高产销率</h4>
                            <div class="value shortage">{max_ratio:.0f}%</div>
                            <div class="ratio-date">日期: {max_date}</div>
                        </div>
                        <div class="inventory-card">
                            <h4><i class="bi bi-arrow-down-circle"></i> 最低产销率</h4>
                            <div class="value surplus">{min_ratio:.0f}%</div>
                            <div class="ratio-date">日期: {min_date}</div>
                        </div>
                    </div>
                </div>
            </div>
            '''
        except Exception as e:
             print(f"生成产销率概览时出错: {e}")
             ratio_section_html += '<div class="data-card"><div class="data-card-body"><p>生成产销率概览时出错。</p></div></div>'
    else:
         ratio_section_html += '<div class="data-card"><div class="data-card-body"><p>无产销率概览数据。</p></div></div>'

    # Add production sales ratio trend chart
    ratio_chart_filename = "production_sales_ratio.png"
    ratio_chart_path = os.path.join(output_dir, ratio_chart_filename)
    if os.path.exists(ratio_chart_path):
        ratio_section_html += f'''
        <div class="data-card">
            <div class="data-card-header">
                <h3 class="data-card-title">产销率趋势分析</h3>
            </div>
            <div class="data-card-body">
                <p>下图展示了每日产销率的变化趋势，以及对应的销量和产量数据。产销率接近100%表示生产与销售较为平衡；低于100%表示产品积压；高于100%表示消耗了库存。</p>
                {generate_image_tag(ratio_chart_filename, alt_text='产销率趋势图')}
            </div>
        </div>
        '''
    else:
        print(f"产销率趋势图未找到: {ratio_chart_path}")

    # Generate Product Sales Ratio Detail section (now just title and link)
    ratio_section_html += _generate_product_sales_ratio_detail(product_sales_ratio_data)

    ratio_section_html += '''
        </div> <!-- Close section-body -->
    </div> <!-- Close section -->
    '''
    return ratio_section_html

def generate_ratio_page(production_sales_ratio, product_sales_ratio_data, output_dir):
    """生成 ratio.html 页面

    Args:
        production_sales_ratio (dict): 每日总体产销率数据。
        product_sales_ratio_data (list): 每日产品明细数据列表。
        output_dir (str): HTML 文件输出目录。
    """
    print("开始生成 ratio.html 页面...")
    page_title = "春雪食品生品产销分析报告 - 产销率分析"
    header_html = generate_header(title=page_title, output_dir=output_dir)
    nav_html = generate_navigation(active_page="ratio")
    ratio_content_html = _generate_ratio_content(production_sales_ratio, product_sales_ratio_data, output_dir)
    footer_html = generate_footer()

    full_html = header_html + nav_html + ratio_content_html + footer_html

    write_html_report(full_html, "ratio.html", output_dir)

# # --- Example Usage (for testing) ---
# if __name__ == '__main__':
#     # Create dummy data
#     dummy_ratio_summary = {
#         datetime(2023, 10, 25): {'ratio': 95.5, 'sales': 1000, 'production': 1047},
#         datetime(2023, 10, 26): {'ratio': 105.2, 'sales': 1200, 'production': 1141},
#         datetime(2023, 10, 27): {'ratio': 88.0, 'sales': 900, 'production': 1023}
#     }
#     dummy_product_details = [
#         {
#             'date': datetime(2023, 10, 25),
#             'data': pd.DataFrame({
#                 '品名': ['鸡腿', '鸡胸', '鸡翅'],
#                 '销量': [500, 300, 200],
#                 '产量': [520, 310, 217],
#                 '产销率': [96.15, 96.77, 92.16]
#             })
#         },
#         {
#             'date': datetime(2023, 10, 26),
#             'data': pd.DataFrame({
#                 '品名': ['鸡腿', '鸡胸', '鸡翅', '鸡爪'],
#                 '销量': [600, 350, 220, 30],
#                 '产量': [580, 330, 200, 31],
#                 '产销率': [103.45, 106.06, 110.00, 96.77]
#             })
#         },
#         {
#              'date': datetime(2023, 10, 27),
#              'data': pd.DataFrame({
#                  '品名': ['鸡腿', '鸡胸', '鸡翅'],
#                  '销量': [450, 280, 170],
#                  '产量': [510, 320, 193],
#                  '产销率': [88.24, 87.50, 88.08]
#              })
#         }
#     ]

#     output_directory = './test_report_output'
#     # Create a dummy image file for testing
#     os.makedirs(output_directory, exist_ok=True)
#     try:
#         with open(os.path.join(output_directory, "production_sales_ratio.png"), 'w') as f:
#             f.write("dummy image content")
#     except OSError as e:
#          print(f"无法创建测试图片: {e}")

#     generate_ratio_page(dummy_ratio_summary, dummy_product_details, output_directory)
#     print(f"测试 ratio.html 已生成在 {output_directory}") 