# -*- coding: utf-8 -*-
"""
生成价格波动分析报告页面 (price_volatility.html)。
包含价格对比和调价记录。
"""

import pandas as pd
from datetime import datetime # Added for get_date helper
from html_utils import generate_header, generate_navigation, generate_footer, write_html_report

# --- CSS Styles (Copied from details_report.py for consistency) ---
CSS_STYLES = """
<style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f4f4f4;
        color: #333;
        line-height: 1.6;
    }
    .container {
        max-width: 1200px;
        margin: 20px auto;
        padding: 0 20px;
        background-color: #fff;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    nav {
        background-color: #333;
        color: #fff;
        padding: 10px 0;
        text-align: center;
    }
    nav ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    nav ul li {
        display: inline;
        margin: 0 15px;
    }
    nav ul li a {
        color: #fff;
        text-decoration: none;
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 4px;
        transition: background-color 0.3s ease;
    }
    nav ul li a.active,
    nav ul li a:hover {
        background-color: #555;
    }
    .section {
        margin-bottom: 30px;
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: #fff;
    }
    .section-header {
        border-bottom: 2px solid #eee;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .section-header h2 {
        color: #333;
        margin: 0;
    }
    .section-body p, .section-body ul {
        margin-bottom: 15px;
    }
     .section-body ul {
        padding-left: 20px;
    }
    .data-card {
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        overflow: hidden; /* Ensure border-radius clips content */
    }
    .data-card-header {
        background-color: #f8f8f8;
        padding: 10px 15px;
        border-bottom: 1px solid #e0e0e0;
    }
    .data-card-title {
        margin: 0;
        font-size: 1.1em;
        color: #444;
    }
    .data-card-body {
        padding: 15px;
    }
    .detail-search {
        margin-bottom: 15px;
    }
    .detail-search input {
        padding: 8px 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
        width: 100%; /* Full width */
        box-sizing: border-box; /* Include padding in width */
        padding-left: 35px; /* Space for the icon */
        background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="%23888" viewBox="0 0 16 16"><path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/></svg>'); /* Basic SVG search icon */
        background-repeat: no-repeat;
        background-position: 10px center; /* Position icon inside padding */
    }
    .detail-table-container {
        width: 100%;
        overflow-x: auto; /* Allow horizontal scrolling for wide tables */
        min-height: 400px; /* Ensure it's not too short */
        max-height: 75vh;  /* Limit height to 75% of viewport height */
        overflow-y: auto;  /* Add vertical scroll when exceeding max-height */
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
    }
    tbody tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    tbody tr:hover {
        background-color: #f1f1f1;
    }
    .warning {
        color: #dc3545; /* Red for warnings */
        font-weight: bold;
    }
    .high-value {
        color: #28a745; /* Green for positive changes */
    }
    .low-value {
        color: #dc3545; /* Red for negative changes */
    }
    footer {
        text-align: center;
        margin-top: 30px;
        padding: 15px;
        background-color: #333;
        color: #fff;
        font-size: 0.9em;
    }
    a {
        color: #007bff;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .text-right {
        text-align: right;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        nav ul li {
            display: block;
            margin: 10px 0;
        }
        .container {
            margin: 10px auto;
            padding: 0 10px;
        }
        .section {
            padding: 15px;
        }
        body {
            font-size: 16px;
        }
        h2 {
            font-size: 1.5em;
        }
        h3.data-card-title {
             font-size: 1.0em;
        }
        th, td {
             padding: 6px 8px;
             font-size: 0.9em;
        }
        .detail-search input {
            padding: 6px 8px;
            padding-left: 30px; /* Adjust padding for mobile */
            background-position: 8px center; /* Adjust icon position */
        }
    }
</style>
"""

# --- Helper function copied from details_report.py ---
def get_date(record):
    date_val = record.get('日期')
    if isinstance(date_val, datetime):
        return date_val
    try:
        return pd.to_datetime(str(date_val)).to_pydatetime()
    except (ValueError, TypeError):
        return datetime.min

# --- Function to generate adjustment table (copied & adapted from details_report.py) ---
def _generate_adjustment_table(conflict_records):
    """生成调价记录表格 (冲突记录)"""
    print(f"_generate_adjustment_table - 收到的记录数: {len(conflict_records) if conflict_records else 0}")
    adjustment_html = '''
        <div class="data-card">
            <div class="data-card-header">
                <h3 class="data-card-title">调价记录</h3>
            </div>
            <div class="data-card-body">
    '''
    if conflict_records and len(conflict_records) > 0:
        # Sort records by date descending
        try:
            sorted_records = sorted(conflict_records, key=lambda x: datetime.strptime(x.get('日期', '1900-01-01'), '%Y-%m-%d'), reverse=True)
            print(f"调价记录排序后的记录数: {len(sorted_records)}")
        except Exception as e:
            print(f"调价记录排序错误: {e}")
            sorted_records = conflict_records # Fallback if date format is unexpected

        adjustment_html += '''
                <p>以下为系统记录的价格调整信息（仅显示价格有变动的记录），按日期降序排列。</p>
                <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">注：数据来源：调价表。价格差异 = 价格 - 前价格。</p>
                <div class="detail-search">
                    <input type="text" id="conflictSearch" placeholder="输入关键字搜索调价记录..." onkeyup="searchTable('conflictTable', 'conflictSearch')">
                </div>
                <div class="table-responsive detail-table-container">
                    <table id="conflictTable" class="mobile-friendly-table stacking-table-mobile">
                        <thead>
                            <tr>
                                <th>日期</th>
                                <th>品名</th>
                                <th>规格</th>
                                <th>前价格</th>
                                <th>价格</th>
                                <th>价格差异</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        for record in sorted_records:
            date_str = record.get('日期', 'N/A')
            name = record.get('品名', 'N/A')
            spec = record.get('规格', 'N/A')
            prev_price = record.get('前价格', '-')
            curr_price = record.get('价格', '-')
            diff = record.get('价格差异', '-')

            # Format numbers (Get display versions first)
            try: 
                prev_price_float = float(prev_price) if pd.notna(prev_price) and prev_price != '-' else None
                prev_price_display = f"{prev_price_float:,.0f}" if prev_price_float is not None else '-'
            except: 
                prev_price_display = str(prev_price)
                
            try: 
                curr_price_float = float(curr_price) if pd.notna(curr_price) and curr_price != '-' else None
                curr_price_display = f"{curr_price_float:,.0f}" if curr_price_float is not None else '-'
            except: 
                curr_price_display = str(curr_price)

            # --- Recalculate difference for styling --- START ---
            diff_display = "-" # Default display
            diff_class = ""   # Default class

            # 直接使用原始的价格差异值
            try:
                diff_float = float(diff) if pd.notna(diff) and diff != '-' else None
                if diff_float is not None:
                    diff_display = f"{diff_float:,.0f}"
                    
                    # 设置样式和符号
                    if diff_float < 0:  # 降价
                        diff_class = "low-value"  # 红色
                    elif diff_float > 0:  # 涨价
                        diff_class = "high-value"  # 绿色
                        diff_display = f"+{diff_display}"  # 添加正号
                else:
                    diff_display = '-'
            except (ValueError, TypeError):
                diff_display = str(diff)  # 显示原始值
            # --- 结束价格差异处理 --- END ---
            
            adjustment_html += f'''
                            <tr>
                                <td data-label="日期">{date_str}</td>
                                <td data-label="品名">{name}</td>
                                <td data-label="规格">{spec}</td>
                                <td data-label="前价格" class="text-right">{prev_price_display}</td>
                                <td data-label="价格" class="text-right">{curr_price_display}</td>
                                <td data-label="价格差异" class="text-right {diff_class}">{diff_display}</td>
                            </tr>
            '''
        adjustment_html += '''
                        </tbody>
                    </table>
                </div> <!-- Close table-responsive -->
            </div>
        '''
    else:
        adjustment_html += "<p>无价格调整记录可显示。</p></div>"

    adjustment_html += "</div>" # Close data-card
    return adjustment_html

def _generate_comparison_content(price_comparison_data, conflict_records):
    """生成价格对比和调价记录部分的HTML内容"

    Args:
        price_comparison_data (pd.DataFrame): 价格对比数据。
        conflict_records (list): 调价记录列表。

    Returns:
        str: 包含两个部分的HTML代码。
        """
    print(f"_generate_comparison_content - 收到的冲突记录数: {len(conflict_records) if conflict_records else 0}")

    comparison_section = '''
    <div class="section">
        <div class="section-header">
             <h2>价格波动分析</h2> <!-- Changed Title -->
        </div>
        <div class="section-body">
    '''

    # --- Price Comparison Table ---
    if price_comparison_data is None or price_comparison_data.empty:
        comparison_section += """
             <div class="data-card">
                 <div class="data-card-header"><h3 class="data-card-title">春雪与小明农牧价格对比</h3></div>
                 <div class="data-card-body"><p>无价格对比数据可供显示。</p></div>
             </div>
        """
    else:
        comparison_section += '''
             <div class="data-card">
                 <div class="data-card-header">
                     <h3 class="data-card-title">春雪与小明农牧价格对比</h3>
                 </div>
                 <div class="data-card-body">
                    <p>以下是春雪食品与小明农牧的价格对比数据，中间价差为负数表示春雪价格低于小明农牧。</p>
                    <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">注：春雪价格为调价表最新价格，小明农牧取中间价</p>
                    <div class="detail-search">
                        <input type="text" id="comparisonSearch" placeholder="输入关键字搜索对比..." onkeyup="searchTable('comparisonTable', 'comparisonSearch')"> <!-- Adjusted JS call -->
                    </div>
                    <div class="table-responsive detail-table-container">
                        <table id="comparisonTable" class="mobile-friendly-table stacking-table-mobile">
                            <thead>
                                <tr>
                                    <th>品名</th>
                                    <th>规格</th>
                                    <th>春雪价格</th>
                                    <th>小明中间价</th>
                                    <th>中间价差</th>
                                </tr>
                            </thead>
                            <tbody>
    '''
    required_cols = ['品名', '规格', '春雪价格', '小明中间价', '中间价差']
    if not all(col in price_comparison_data.columns for col in required_cols):
        comparison_section += "<tr><td colspan='5'>价格对比数据列不完整。</td></tr>"
    else:
        sorted_data = price_comparison_data
        for _, row in sorted_data.iterrows():
            prod_name = row.get('品名', 'N/A')
            spec = row.get('规格', '')
            spring_price_val = row.get('春雪价格')
            xiaoming_price_val = row.get('小明中间价')
            price_diff_val = row.get('中间价差')
            spring_price_display = "-"
            if pd.notna(spring_price_val):
                try: spring_price_display = f"{float(spring_price_val):,.0f}"
                except (ValueError, TypeError): spring_price_display = str(spring_price_val)
            xiaoming_price_display = "-"
            if pd.notna(xiaoming_price_val):
                 try: xiaoming_price_display = f"{float(xiaoming_price_val):,.0f}"
                 except (ValueError, TypeError): xiaoming_price_display = str(xiaoming_price_val)
            price_diff_display = "-"
            price_diff_class = ""
            if pd.notna(price_diff_val):
                try:
                    price_diff_float = float(price_diff_val)
                    price_diff_display = f"{price_diff_float:,.0f}"
                    if price_diff_float < 0:
                        price_diff_class = "warning" # Negative difference highlighted
                except (ValueError, TypeError):
                    price_diff_display = str(price_diff_val)
            comparison_section += f'''
                <tr>
                    <td data-label="品名">{prod_name}</td>
                    <td data-label="规格">{spec}</td>
                    <td data-label="春雪价格" class="text-right">{spring_price_display}</td>
                    <td data-label="小明中间价" class="text-right">{xiaoming_price_display}</td>
                    <td data-label="中间价差" class="text-right {price_diff_class}">{price_diff_display}</td>
                </tr>
            '''
    comparison_section += '''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        '''

    # --- Adjustment Table (Moved from details) ---
    comparison_section += _generate_adjustment_table(conflict_records)

    comparison_section += '''
        </div> <!-- Close section-body -->
    </div> <!-- Close section -->
    '''
    return comparison_section

def generate_comparison_page(price_comparison_data, conflict_records, output_dir):
    """生成 price_volatility.html 页面 (原 comparison.html)

    Args:
        price_comparison_data (pd.DataFrame): 价格对比数据。
        conflict_records (list): 调价记录列表。
        output_dir (str): HTML 文件输出目录。
    """
    print("开始生成 price_volatility.html 页面...")
    print(f"generate_comparison_page - 收到的冲突记录数: {len(conflict_records) if conflict_records else 0}")
    page_title = "春雪食品生品产销分析报告 - 价格波动分析" # Changed Title
    header_html = generate_header(title=page_title, output_dir=output_dir)
    # Changed active_page identifier
    nav_html = generate_navigation(active_page="price_volatility")
    comparison_content_html = _generate_comparison_content(price_comparison_data, conflict_records)
    footer_html = generate_footer()

    # Add CSS Styles to the beginning of the body or within the head if possible
    # Assuming header_html contains <head>...</head><body>, inject CSS after </head>
    # Or better, modify generate_header if possible. For now, inject after header.
    full_html = header_html + CSS_STYLES + "<div class='container'>" + nav_html + comparison_content_html + "</div>" + footer_html

    # Changed output filename
    write_html_report(full_html, "price_volatility.html", output_dir)
    print(f"price_volatility.html generated in {output_dir}")

# --- Example Usage (Updated for testing) ---
if __name__ == '__main__':
    # Create dummy comparison data
    dummy_comp_data = pd.DataFrame({
        '品名': ['鸡大胸', '鸡翅中', '琵琶腿', '鸡爪'],
        '规格': ['A', 'B', 'C', 'D'],
        '春雪价格': [10000, 15000, 9000, 12000],
        '小明中间价': [10200, 14800, 9500, 12000],
        '中间价差': [-200, 200, -500, 0]
    })
    dummy_comp_data.loc[4] = ['鸡心', 'E', 8000, None, None]

    # Create dummy conflict (adjustment) data
    dummy_conflict = [
        {'日期': '2023-10-27', '品名': 'Product F', '规格': 'Spec2', '前价格': 7000, '价格': 7250},
        {'日期': '2023-10-27', '品名': 'Product F', '规格': 'Spec2', '前价格': 7250, '价格': 7100},
        {'日期': '2023-10-26', '品名': 'Product G', '规格': 'Spec1', '前价格': 8000, '价格': 8000}, # Zero diff
        {'日期': '2023-10-28', '品名': 'Product H', '规格': None, '前价格': 9000, '价格': 8800},
    ]

    output_directory = './test_report_output'
    import os
    os.makedirs(output_directory, exist_ok=True)

    # Call the updated function with both datasets
    generate_comparison_page(dummy_comp_data, dummy_conflict, output_directory)
    print(f"测试 price_volatility.html 已生成在 {output_directory}") 