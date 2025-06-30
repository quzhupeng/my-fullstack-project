# -*- coding: utf-8 -*-
"""
生成库存情况报告页面 (inventory.html)。
"""

import os
import pandas as pd
# --- 修正导入 ---
# 从 html_utils 导入基础 HTML 生成函数
from html_utils import (
    generate_header,
    generate_navigation,
    generate_footer,
    write_html_report,
    generate_image_tag
    # 移除了 format_dataframe, format_currency, format_number
)
# 从 utils.report_utils 导入格式化函数 (假设它们在这里)
try:
    from utils.report_utils import format_number # 只导入实际用到的
    # 如果还需要 format_dataframe 或 format_currency，也在这里导入
    # from utils.report_utils import format_dataframe, format_currency
except ModuleNotFoundError:
    print("错误：无法从 'utils.report_utils' 导入格式化函数。请确保 'utils' 目录存在，包含 '__init__.py' 和 'report_utils.py' 文件，且后者定义了所需函数。")
    # 提供一个临时的、基本的 format_number 函数以避免完全崩溃
    def format_number(value, precision=0):
        if pd.isna(value):
            return "-"
        try:
            return f"{float(value):,.{precision}f}"
        except (ValueError, TypeError):
            return str(value)
# ----------------

def _generate_inventory_content(inventory_data, output_dir):
    """生成库存情况部分的HTML内容 (移植自原 _generate_inventory_section)

    Args:
        inventory_data (pd.DataFrame): 库存数据。
        output_dir (str): 输出目录，用于检查图片文件。

    Returns:
        str: 库存部分的HTML代码。
    """
    # Handle cases where inventory_data might be None or empty
    if inventory_data is None or inventory_data.empty:
        return """
        <div class="section">
            <div class="section-header"><h2>库存情况</h2></div>
            <div class="section-body"><p>无库存数据可供显示。</p></div>
        </div>
        """

    # Inventory summary cards
    total_inventory_kg = inventory_data['库存量'].sum() if '库存量' in inventory_data.columns else 0
    total_production_kg = inventory_data['产量'].sum() if '产量' in inventory_data.columns else 0
    total_sales_kg = inventory_data['销量'].sum() if '销量' in inventory_data.columns else 0

    # Convert to Tons
    total_inventory_tons = total_inventory_kg / 1000.0
    total_production_tons = total_production_kg / 1000.0
    total_sales_tons = total_sales_kg / 1000.0

    inventory_section = f"""
    <div class="section">
        <div class="section-header">
            <h2>库存情况</h2>
        </div>
        <div class="section-body">
            <div class="inventory-summary">
                <div class="inventory-card">
                    <h4><i class="bi bi-box-seam"></i> 总库存量 (吨)</h4>
                    <div class="value">{format_number(total_inventory_tons, precision=1)}</div>
                </div>
                <div class="inventory-card">
                    <h4><i class="bi bi-gear"></i> 总产量 (入库, 吨)</h4>
                    <div class="value">{format_number(total_production_tons, precision=1)}</div>
                </div>
                <div class="inventory-card">
                    <h4><i class="bi bi-cart"></i> 总销量 (出库, 吨)</h4>
                    <div class="value">{format_number(total_sales_tons, precision=1)}</div>
                </div>
            </div>
            <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">注：库存口径为去除鲜品、副产品后。产量为入库量，销量为出库量。卡片数值单位为吨。</p>
    """

    # Inventory visualization chart
    inventory_chart_filename = "inventory_top_items.png"
    inventory_chart_path = os.path.join(output_dir, inventory_chart_filename)
    if os.path.exists(inventory_chart_path):
        print(f"DEBUG: Inventory chart found: {inventory_chart_path}") # 保留调试信息
        inventory_section += f"""
            <div class="data-card">
                <div class="data-card-header">
                    <h3 class="data-card-title">库存可视化</h3>
                </div>
                <div class="data-card-body">
                    <div>
                        <h4>库存量TOP15产品</h4>
                        {generate_image_tag(inventory_chart_filename, alt_text="库存量TOP15产品", css_class="img-fluid")}
                    </div>
                </div>
            </div>
        """
    else:
        print(f"WARNING: Inventory chart NOT found at: {inventory_chart_path}") # 保留警告信息
        # 可以选择性地添加占位符或提示
        inventory_section += """
            <div class="data-card">
                <div class="data-card-header"><h3 class="data-card-title">库存可视化</h3></div>
                <div class="data-card-body"><p>库存量TOP15产品图表未生成或未找到。</p></div>
            </div>
        """

    # Inventory detail table
    inventory_section += """
        <div class="data-card">
            <div class="data-card-header">
                <h3 class="data-card-title">库存明细表</h3>
            </div>
            <div class="data-card-body">
                <div class="inventory-search">
                    <input type="text" id="inventorySearch" placeholder="输入关键字搜索库存..." onkeyup="searchTable('inventoryTable', 'inventorySearch')">
                </div>
                <div class="inventory-table-container detail-table-container">
                    <table id="inventoryTable">
                        <thead>
                            <tr>
                                <th>品名</th>
                                <th class="text-right">产量</th>
                                <th class="text-right">销量</th>
                                <th class="text-right">库存量</th>
                            </tr>
                        </thead>
                        <tbody>
    """

    # Add data rows - sort by inventory quantity descending
    display_columns = ['品名', '产量', '销量', '库存量']
    if all(col in inventory_data.columns for col in display_columns):
        # 确保在排序前处理 NaN 值，否则可能导致错误
        sorted_inventory = inventory_data[display_columns].fillna({'库存量': -float('inf')}).sort_values(by='库存量', ascending=False).replace({-float('inf'): pd.NA})

        for _, row in sorted_inventory.iterrows():
            inventory_section += "<tr>"
            # 品名列
            inventory_section += f"<td>{row.get('品名', 'N/A')}</td>"
            # 数值列格式化
            for col in ['产量', '销量', '库存量']:
                value = row.get(col)
                # 使用 format_number 处理 NaN 和数字
                value_display = format_number(value, precision=0) # 假设 format_number 能处理 NaN/None
                inventory_section += f"<td class=\"text-right\">{value_display}</td>"
            inventory_section += "</tr>"
    else:
        missing_cols = [col for col in display_columns if col not in inventory_data.columns]
        inventory_section += f"<tr><td colspan='4'>库存明细列不完整 (缺少: {', '.join(missing_cols)}) 或数据格式错误。</td></tr>"

    inventory_section += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div> <!-- Close section-body -->
</div> <!-- Close section -->
    """

    return inventory_section

def generate_inventory_page(inventory_data, output_dir):
    """生成 inventory.html 页面

    Args:
        inventory_data (pd.DataFrame): 库存数据。
        output_dir (str): HTML 文件输出目录。
    """
    print("开始生成 inventory.html 页面...")
    page_title = "春雪食品生品产销分析报告 - 库存情况"
    header_html = generate_header(title=page_title, output_dir=output_dir)
    nav_html = generate_navigation(active_page="inventory")
    inventory_content_html = _generate_inventory_content(inventory_data, output_dir)
    footer_html = generate_footer()

    full_html = header_html + "<div class='container'>" + nav_html + inventory_content_html + "</div>" + footer_html

    write_html_report(full_html, "inventory.html", output_dir)

# # --- Example Usage (for testing) ---
# if __name__ == '__main__':
#     # Create dummy inventory data
#     dummy_data = {
#         '品名': [f'Product {i}' for i in range(20)],
#         '产量': [1000 + i * 50 for i in range(20)],
#         '销量': [800 + i * 40 for i in range(20)],
#         '库存量': [2000 - i * 100 for i in range(20)]
#     }
#     dummy_inventory_df = pd.DataFrame(dummy_data)
#     dummy_inventory_df.loc[3, '库存量'] = None # Add a NaN value for testing

#     output_directory = './test_report_output'
#     # Create a dummy image file for testing
#     os.makedirs(output_directory, exist_ok=True)
#     try:
#         with open(os.path.join(output_directory, "top15_inventory_qty.png"), 'w') as f:
#             f.write("dummy image content")
#     except OSError as e:
#         print(f"无法创建测试图片: {e}")

#     generate_inventory_page(dummy_inventory_df, output_directory)
#     print(f"测试 inventory.html 已生成在 {output_directory}") 