# -*- coding: utf-8 -*-
"""
生成销售情况报告页面 (sales.html)。
"""

import os
import pandas as pd
from html_utils import generate_header, generate_navigation, generate_footer, write_html_report, generate_image_tag
from collections import OrderedDict # 导入OrderedDict

def _generate_sales_content(daily_sales, comprehensive_price_file, output_dir):
    """生成销售情况部分的HTML内容

    Args:
        daily_sales (dict): 每日销售数据, {date: {'volume': v, 'avg_price': p, 'product_count': c, 'data': df, 'quantity_column': qc}}
        comprehensive_price_file (str): 综合售价Excel文件路径
        output_dir (str): 输出目录

    Returns:
        str: 销售情况部分的HTML代码。
    """
    if not daily_sales or len(daily_sales) == 0:
        print("警告: 每日销售数据为空，跳过销售情况部分生成")
        return """
        <div class="section">
            <div class="section-header"><h2>销售情况分析</h2></div>
            <div class="section-body"><p>无销售数据可供显示。</p></div>
        </div>
        """

    html = '''
    <div class="section">
        <div class="section-header">
            <h2>销售情况分析</h2>
        </div>
        <div class="section-body">
    '''

    # 添加综合售价表格
    if comprehensive_price_file and os.path.exists(comprehensive_price_file):
        try:
            import pandas as pd
            import re
            
            file_name = os.path.basename(comprehensive_price_file)
            match = re.search(r"综合售价(\\d+\\.\\d+)\\.xlsx", file_name)
            date_str = match.group(1) if match else "最新"
            
            print(f"处理综合售价文件: {comprehensive_price_file}")
            df = pd.read_excel(comprehensive_price_file, header=None)
            
            explanation_text = ""
            for r_idx in range(len(df)):
                for c_idx in range(len(df.columns)):
                    cell_val = df.iloc[r_idx, c_idx]
                    if pd.notna(cell_val) and isinstance(cell_val, str) and "说明" in cell_val:
                        explanation_text = cell_val if cell_val.startswith("说明：") else "说明：" + cell_val
                        df.iloc[r_idx, c_idx] = "" 
                        break 
                if explanation_text: break
            
            if not explanation_text:
                explanation_text = "说明：加工一二厂实际为：去毛、血、肠后调整加工产品价格的综合价格。与真实行业价格也相甚相符。"
            
            html += f'''
            <div class="subsection">
                <h3>综合售价 ({date_str})</h3>
                <div class="table-responsive" id="comp-price-table-container">
                    <table class="table table-bordered table-striped price-table" style="text-align: center;">
            '''
            html += '''
            <style>
                .price-table th, .price-table td { text-align: center; vertical-align: middle; }
                .price-table th { background-color: #f2f2f2; font-weight: bold; }
                .price-table .price-category { background-color: #f0f4f8; font-weight: bold; }
                .price-table .price-value { text-align: right; font-family: Arial, sans-serif; }
                .empty-cell { background-color: #fafafa; }
                .calculation-method { background-color: #f5f5f5; font-weight: 500; }
                .swipe-hint { text-align: center; color: #666; font-size: 0.8em; padding: 5px; margin-bottom: 5px; }
            </style>
            '''
            
            html += "<thead>"
            html += '<tr><th colspan="3" style="background-color: #e6f2ff;">类别</th>'
            # 日期列标题 (从第4列到最后1列)
            for col_idx in range(3, len(df.columns)):
                header_val = df.iloc[1, col_idx] # 第2行是日期/均价标题
                html += f'<th style="background-color: #e6f2ff;">{str(header_val) if pd.notna(header_val) else ""}</th>'
            html += "</tr></thead>"
            
            html += "<tbody>"
            
            categories = OrderedDict()
            current_main_category_name = None
            current_main_category_last_calc_method = ""

            for r_idx in range(2, len(df)): # 从Excel的第3行开始数据
                main_cat_val_raw = df.iloc[r_idx, 0]
                main_cat_val = str(main_cat_val_raw).strip() if pd.notna(main_cat_val_raw) else ""
                
                factory_val_raw = df.iloc[r_idx, 1]
                factory_val = str(factory_val_raw).strip() if pd.notna(factory_val_raw) else ""
                
                calc_method_val_raw = df.iloc[r_idx, 2]
                calc_method_val = str(calc_method_val_raw).strip() if pd.notna(calc_method_val_raw) else ""

                is_genuine_data_row = False
                if factory_val != "" or calc_method_val != "":
                    is_genuine_data_row = True
                else:
                    for c_idx_check in range(3, len(df.columns)):
                        if pd.notna(df.iloc[r_idx, c_idx_check]):
                            is_genuine_data_row = True
                            break
                if not is_genuine_data_row:
                    continue

                if main_cat_val != "":
                    current_main_category_name = main_cat_val
                    if current_main_category_name not in categories:
                        categories[current_main_category_name] = OrderedDict()
                    current_main_category_last_calc_method = "" 
                
                if current_main_category_name is None: continue

                effective_calc_method = calc_method_val
                if effective_calc_method == "":
                    effective_calc_method = current_main_category_last_calc_method
                else:
                    current_main_category_last_calc_method = effective_calc_method
                
                if effective_calc_method not in categories[current_main_category_name]:
                    categories[current_main_category_name][effective_calc_method] = []
                categories[current_main_category_name][effective_calc_method].append(r_idx)

            # 渲染HTML表格
            for main_cat_name, calc_methods_dict in categories.items():
                total_rows_for_main_cat = sum(len(idx_list) for idx_list in calc_methods_dict.values())
                if total_rows_for_main_cat == 0: continue

                is_first_html_row_for_main_cat = True
                
                avg_price_cell_html = ""
                # 确定均价列 (最后一列)
                avg_price_col_idx = len(df.columns) - 1
                if avg_price_col_idx >= 3: #确保有均价列
                    # 从这个主分类的第一个实际数据行获取均价
                    first_data_row_original_idx = -1
                    for _, row_idx_list_for_calc_method in calc_methods_dict.items():
                        if row_idx_list_for_calc_method:
                            first_data_row_original_idx = row_idx_list_for_calc_method[0]
                            break
                    
                    if first_data_row_original_idx != -1:
                        avg_price_val = df.iloc[first_data_row_original_idx, avg_price_col_idx]
                        cell_content = f"{int(avg_price_val):,}" if pd.notna(avg_price_val) and isinstance(avg_price_val, (int, float)) else (str(avg_price_val) if pd.notna(avg_price_val) else "")
                        avg_price_cell_html = f'<td rowspan="{total_rows_for_main_cat}" class="price-value { "empty-cell" if cell_content == "" else ""}">{cell_content}</td>'
                    else: # Should not happen if total_rows_for_main_cat > 0
                        avg_price_cell_html = f'<td rowspan="{total_rows_for_main_cat}" class="empty-cell"></td>'


                for calc_method_name, row_indices_list in calc_methods_dict.items():
                    rows_for_this_calc_method = len(row_indices_list)
                    if rows_for_this_calc_method == 0: continue

                    for i, current_row_original_idx in enumerate(row_indices_list):
                        html += "<tr>"
                        
                        if is_first_html_row_for_main_cat:
                            html += f'<td rowspan="{total_rows_for_main_cat}" class="price-category">{main_cat_name}</td>'
                        
                        factory_val_on_row = df.iloc[current_row_original_idx, 1]
                        html += f'<td>{str(factory_val_on_row) if pd.notna(factory_val_on_row) else ""}</td>'
                        
                        if i == 0: # First row for this specific calc_method_name group
                            html += f'<td rowspan="{rows_for_this_calc_method}" class="calculation-method { "empty-cell" if calc_method_name == "" else ""}">{calc_method_name}</td>'
                        
                        # 数据值 (从第4列到倒数第2列)
                        for data_col_df_idx in range(3, len(df.columns) - 1):
                            data_val = df.iloc[current_row_original_idx, data_col_df_idx]
                            cell_content = f"{int(data_val):,}" if pd.notna(data_val) and isinstance(data_val, (int, float)) else (str(data_val) if pd.notna(data_val) else "")
                            html += f'<td class="price-value { "empty-cell" if cell_content == "" else ""}">{cell_content}</td>'
                        
                        if is_first_html_row_for_main_cat:
                            html += avg_price_cell_html
                        
                        html += "</tr>"
                        is_first_html_row_for_main_cat = False
            
            html += "</tbody>"
            html += '''
                    </table>
                </div>
                <div class="swipe-hint"><i class="bi bi-arrow-left-right"></i> 左右滑动查看更多</div>
                <div class="description">
                    <p style="text-align: left; font-size: 13px; color: #666; margin-top: 10px; border-left: 3px solid #1976D2; padding-left: 10px; background-color: #f9f9f9; padding: 8px;">
                        <strong>说明：</strong>''' + explanation_text.replace("说明：", "") + '''
                    </p>
                </div>
            </div>
            '''
        except Exception as e:
            print(f"处理综合售价文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            html += f'<div class="subsection"><h3>综合售价</h3><p>无法加载综合售价数据: {str(e)}</p></div>'
    else:
        print(f"综合售价文件未找到或无效: {comprehensive_price_file}")
        html += '<div class="subsection"><h3>综合售价</h3><p>未找到综合售价数据文件</p></div>'

    # Add sales trend chart
    sales_trend_chart_filename = "daily_sales_trend.png"
    sales_trend_chart_path = os.path.join(output_dir, sales_trend_chart_filename)
    if os.path.exists(sales_trend_chart_path):
        html += f'''
        <div class="subsection">
            <h3>销售趋势</h3>
            <div class="chart-container">
                 {generate_image_tag(sales_trend_chart_filename, alt_text="每日销量和实际销售均价趋势", css_class="chart")}
            </div>
            <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">注：销量去除副产品和鲜品，销售均价为实际总金额/总重量得到的含税价格</p>
            <p style="text-align: right; font-size: 12px; color: #666; margin-top: 2px;">数据来源：销售发票执行查询（排除客户名称为空、副产品、鲜品的记录）</p>
        </div>
        '''
    else:
        print(f"销售趋势图未找到: {sales_trend_chart_path}")


    html += '''
        <div class="subsection">
            <h3>销售明细</h3>
            <p>每日各产品的详细销售数据已移至详细数据页面。</p>
            <p><a href="details.html#daily-sales-details" class="btn btn-primary">点击查看每日明细数据</a></p>
            <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">数据来源：销售发票执行查询（排除客户名称为空、副产品、鲜品的记录）</p>
        </div>
        </div> <!-- Close section-body -->
    </div> <!-- Close section -->
    '''
    return html

def generate_sales_page(daily_sales, comprehensive_price_file, output_dir):
    """生成 sales.html 页面

    Args:
        daily_sales (dict): 每日销售数据。
        comprehensive_price_file (str): 综合售价文件路径。
        output_dir (str): HTML 文件输出目录。
    """
    print("开始生成 sales.html 页面...")
    page_title = "春雪食品生品产销分析报告 - 销售情况"
    header_html = generate_header(title=page_title, output_dir=output_dir)
    nav_html = generate_navigation(active_page="sales")
    sales_content_html = _generate_sales_content(daily_sales, comprehensive_price_file, output_dir)
    footer_html = generate_footer()

    full_html = header_html + nav_html + sales_content_html + footer_html

    write_html_report(full_html, "sales.html", output_dir)

# # --- Example Usage (for testing) ---
# if __name__ == '__main__':
#     from datetime import datetime
#     # Create dummy data
#     dummy_sales_data = {
#         datetime(2023, 10, 25): {
#             'volume': 5000, 'avg_price': 15000, 'product_count': 3,
#             'quantity_column': '销售量',
#             'data': pd.DataFrame({
#                 '物料名称': ['冻鸡腿A', '冻鸡胸B', '鲜鸡翅C'],
#                 '销售量': [2500, 1500, 1000],
#                 '本币无税金额': [30000, 25000, 20000],
#                 '含税单价': [15000, 16000, 21000]
#             })
#         },
#         datetime(2023, 10, 26): {
#             'volume': 6200, 'avg_price': 15200, 'product_count': 2,
#             'quantity_column': '实际重量',
#             'data': pd.DataFrame({
#                 '物料名称': ['冻鸡腿A', '鲜鸡翅C'],
#                 '实际重量': [4000, 2200],
#                 '本币无税金额': [48000, 44000],
#                 '含税单价': [15100, 20500]
#             })
#         },
#          datetime(2023, 10, 27): {
#              'volume': 0, 'avg_price': None, 'product_count': 0,
#              'quantity_column': '销售量',
#              'data': pd.DataFrame(columns=['物料名称', '销售量', '本币无税金额', '含税单价'])
#          }
#     }
#     dummy_comp_chart = "comprehensive_price_chart.png"

#     output_directory = './test_report_output'
#     os.makedirs(output_directory, exist_ok=True)
#     # Create dummy image files
#     try:
#         with open(os.path.join(output_directory, dummy_comp_chart), 'w') as f: f.write("comp price chart")
#         with open(os.path.join(output_directory, "daily_sales_trend.png"), 'w') as f: f.write("sales trend chart")
#     except OSError as e:
#         print(f"无法创建测试图片: {e}")

#     generate_sales_page(dummy_sales_data, dummy_comp_chart, output_directory)
#     print(f"测试 sales.html 已生成在 {output_directory}") 