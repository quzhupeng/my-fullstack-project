# -*- coding: utf-8 -*-
"""
生成详细数据分析报告页面 (details.html)。
包含每日产销率明细和每日销售明细。
"""

import pandas as pd
from datetime import datetime
from html_utils import generate_header, generate_navigation, generate_footer, write_html_report

# --- CSS Styles (Combined and refined) ---
CSS_STYLES = """
<style>
    /* General */
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; color: #333; line-height: 1.6; }
    .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; background-color: #fff; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    a { color: #007bff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .text-right { text-align: right; }

    /* Navigation */
    nav { background-color: #333; color: #fff; padding: 10px 0; text-align: center; }
    nav ul { list-style: none; padding: 0; margin: 0; }
    nav ul li { display: inline; margin: 0 15px; }
    nav ul li a { color: #fff; text-decoration: none; font-weight: bold; padding: 5px 10px; border-radius: 4px; transition: background-color 0.3s ease; }
    nav ul li a.active, nav ul li a:hover { background-color: #555; }

    /* Section Layout */
    .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #fff; }
    .section-header { border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; /* Allow wrapping for button */ }
    .section-header h2 { color: #333; margin: 0; }
    .section-body p, .section-body ul { margin-bottom: 15px; }
    .section-body ul { padding-left: 20px; }

    /* Data Cards (General) */
    .data-card { margin-bottom: 20px; border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden; }
    .data-card-header { background-color: #f8f8f8; padding: 10px 15px; border-bottom: 1px solid #e0e0e0; }
    .data-card-title { margin: 0; font-size: 1.1em; color: #444; }
    .data-card-body { padding: 15px; }

    /* --- Vertical Scrolling Thin Card Container --- */
    .sales-container {
        margin-top: 20px;
        max-height: 350px; /* Adjust max height for desired scroll area */
        overflow-y: auto; /* Enable vertical scroll */
        padding-right: 5px; /* Space for scrollbar */
        border: 1px solid #eee; /* Optional border */
        border-radius: 4px;
    }
    .sales-flex { /* This div now just holds the stacked items */
        /* Remove previous flex/horizontal scroll styles */
    }
    .sales-flex-item {
        /* Remove inline-block/fixed width */
        width: 100%; /* Each item takes full width */
        box-sizing: border-box;
        margin-bottom: 4px; /* Space between stacked cards */
    }
    .sales-flex-item:last-child {
        margin-bottom: 0;
    }
    .sales-card {
        border: 1px solid #ddd;
        border-radius: 3px;
        padding: 5px 10px; /* Adjust padding for thin strip */
        background-color: #fff;
        cursor: pointer;
        transition: background-color 0.2s ease;
        position: relative;
        overflow: hidden;
        display: flex; /* Use flex to align items horizontally within the thin strip */
        align-items: center; /* Vertically center items in the flex row */
        justify-content: space-between; /* Space out header and body */
        height: 40px; /* Set the fixed height for the thin strip */
        box-sizing: border-box;
    }
    /* --- End Vertical Scrolling Thin Card Container --- */

    .sales-card:hover { background-color: #f0f0f0; }
    .sales-card-header { 
        /* Adjustments for horizontal layout */
        margin: 0;
        padding: 0;
        border: none;
        display: flex; /* Align icon and date */
        align-items: center;
        flex-shrink: 0; /* Prevent header from shrinking */
    }
    .sales-card-header h4 { 
        margin: 0;
        font-size: 0.9em; 
        color: #333; 
        white-space: nowrap;
        margin-left: 5px; /* Space between icon and date */
    }
    .sales-card-header h4 i { /* Icon style within header */
        font-size: 1em; 
        color: #555;
    }
    .toggle-icon { 
        color: #888; 
        font-size: 0.9em; 
        margin-left: 10px; /* Space before toggle icon */
        flex-shrink: 0; /* Prevent icon from shrinking */
    }
    .sales-card-body { 
        /* Adjustments for horizontal layout */
        padding: 0;
        margin: 0 10px; /* Space between header/toggle icon and body */
        display: flex; /* Arrange body items horizontally */
        align-items: center;
        flex-grow: 1; /* Allow body to take remaining space */
        overflow: hidden; /* Hide overflow */
        white-space: nowrap; /* Prevent wrapping */
    }
    .sales-card-body p { 
        margin: 0 8px; /* Space between body items */
        font-size: 0.8em; 
        color: #555; 
        display: inline-flex; /* Use inline-flex for icon and text */
        align-items: center; 
        line-height: 1.2;
        white-space: nowrap;
    }
    .sales-card-body p:first-child {
        margin-left: 0;
    }
    .sales-card-body p i { 
        margin-right: 3px; 
        color: #888; 
        font-size: 0.9em; 
        flex-shrink: 0;
    }
    .sales-card-body strong { color: #333; font-weight: 600; }
    .card-hint { display: none; /* Still hidden */ }

    /* Detail Panels (Sales/Ratio) */
    .sales-panel, .ratio-panel { display: none; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; background-color: #fdfdfd; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .sales-panel-header, .ratio-panel-header { background-color: #eee; padding: 10px 15px; border-bottom: 1px solid #ccc; display: flex; justify-content: space-between; align-items: center; }
    .sales-panel-header h4, .ratio-panel-header h4 { margin: 0; font-size: 1.1em; }
    .sales-panel-controls, .ratio-panel-controls { display: flex; align-items: center; gap: 10px; }
    .search-input { padding: 5px 8px; border: 1px solid #ccc; border-radius: 3px; font-size: 0.9em; }
    .close-button { background: none; border: none; font-size: 1.2em; cursor: pointer; color: #666; padding: 0 5px; }
    .close-button:hover { color: #333; }
    .sales-panel-body, .ratio-panel-body { padding: 15px; }
    .sales-table-container { max-height: 400px; overflow-y: auto; width: 100%; }

    /* Tables */
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; vertical-align: top; }
    th { background-color: #f2f2f2; font-weight: bold; position: sticky; top: 0; z-index: 1; }
    tbody tr:nth-child(even) { background-color: #f9f9f9; }
    tbody tr:hover { background-color: #f1f1f1; }
    .total-row td { font-weight: bold; background-color: #f0f0f0; }

    /* --- Center align table cells except first column in panels --- */
    .ratio-panel .sales-table-container th:nth-child(n+2),
    .ratio-panel .sales-table-container td:not(:first-child),
    .sales-panel .sales-table-container th:nth-child(n+2),
    .sales-panel .sales-table-container td:not(:first-child) {
        text-align: center;
    }
    /* --- End Center align --- */

    /* Value Highlighting */
    .warning { color: #dc3545; font-weight: bold; }
    .high-value { color: #28a745; }
    .low-value { color: #dc3545; }

    /* Buttons */
    .btn { display: inline-block; font-weight: 400; color: #212529; text-align: center; vertical-align: middle; cursor: pointer; user-select: none; background-color: transparent; border: 1px solid transparent; padding: 0.375rem 0.75rem; font-size: 1rem; line-height: 1.5; border-radius: 0.25rem; transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out; }
    .btn-primary { color: #fff; background-color: #007bff; border-color: #007bff; }
    .btn-primary:hover { color: #fff; background-color: #0069d9; border-color: #0062cc; }
    .btn-secondary { color: #fff; background-color: #6c757d; border-color: #6c757d; }
    .btn-secondary:hover { color: #fff; background-color: #5a6268; border-color: #545b62; }
    .btn-sm { padding: 0.25rem 0.5rem; font-size: .875rem; line-height: 1.5; border-radius: 0.2rem; }
    .back-button { margin-left: auto; /* Pushes button to the right in flex container */ }

    /* Footer */
    footer { text-align: center; margin-top: 30px; padding: 15px; background-color: #333; color: #fff; font-size: 0.9em; }

    /* Responsive Design */
    @media (max-width: 767.98px) { /* Small screens */
        nav ul li { display: block; margin: 10px 0; }
        .container { margin: 10px auto; padding: 0 10px; }
        .section { padding: 15px; }
        body { font-size: 16px; }
        h2 { font-size: 1.5em; }
        th, td { padding: 6px 8px; font-size: 0.9em; }
        .search-input { padding: 6px 8px; font-size: 0.9em; }
        
        /* Adjust thin card layout for very small screens if needed */
        .sales-card {
            height: auto; /* Allow height to adjust */
            flex-direction: column; /* Stack header and body vertically */
            align-items: flex-start; /* Align items to start */
            padding: 8px;
        }
        .sales-card-body {
            margin: 5px 0 0 0; /* Add space above body */
            white-space: normal; /* Allow body content to wrap */
             flex-wrap: wrap; /* Allow p tags to wrap */
        }
         .sales-card-body p {
             margin: 2px 8px 2px 0; /* Adjust spacing for wrapping */
         }
        .toggle-icon {
            position: absolute; /* Position toggle icon */
            top: 8px;
            right: 10px;
        }
        .sales-container { max-height: 300px; } /* Adjust scroll height */
        .section-header { flex-direction: column; align-items: flex-start; }
        .back-button { margin-left: 0; margin-top: 10px; }
    }
</style>
"""

# --- Copied and adapted from ratio_report.py --- START ---
# Panel generation function (used by _generate_ratio_detail_section)
def _generate_product_sales_ratio_detail_panel(date_str, data):
    """生成每日产品产销率明细面板"""
    if data is None or data.empty:
        # Return an empty div with the panel ID so JS doesn't break
        return f'''<div id="ratioPanel_{date_str}" class="ratio-panel" style="display: none;">
                 <div class="ratio-panel-header"><h4>产销率明细 - {date_str}</h4><button onclick="togglePanel('ratioPanel_{date_str}', event)" class="close-button"><i class="bi bi-x-lg"></i></button></div>
                 <div class="ratio-panel-body"><p>当日无详细产品产销数据。</p></div>
               </div>'''

    panel_html = f'''
    <div id="ratioPanel_{date_str}" class="ratio-panel" style="display: none;">
        <div class="ratio-panel-header">
            <h4>产销率明细 - {date_str}</h4>
            <div class="ratio-panel-controls">
                <input type="text" id="ratioSearch_{date_str}" onkeyup="searchTableInPanel('ratioTable_{date_str}', 'ratioSearch_{date_str}')" placeholder="搜索产品..." class="search-input">
                <button onclick="togglePanel('ratioPanel_{date_str}', event)" class="close-button"><i class="bi bi-x-lg"></i></button>
            </div>
        </div>
        <div class="ratio-panel-body">
            <div class="sales-table-container table-responsive">
                <table id="ratioTable_{date_str}" class="mobile-friendly-table">
                    <thead><tr><th>产品名称</th><th>销量</th><th>产量</th><th>产销率</th></tr></thead>
                    <tbody>
    '''
    try:
        if '产销率' in data.columns and pd.api.types.is_numeric_dtype(data['产销率']):
            data_sorted = data.sort_values(by='产销率', ascending=False, na_position='last')
        else: data_sorted = data
    except Exception: data_sorted = data

    required_cols = ['品名', '销量', '产量', '产销率']
    if not all(col in data_sorted.columns for col in required_cols):
        panel_html += "<tr><td colspan='4'>数据列不完整。</td></tr>"
    else:
        for _, row in data_sorted.iterrows():
            prod_name = row.get('品名', 'N/A')
            sales_val = row.get('销量'); prod_val = row.get('产量'); ratio_val = row.get('产销率')
            try: sales_display = f"{float(sales_val):,.0f}" if pd.notna(sales_val) else "-"
            except: sales_display = str(sales_val)
            try: prod_display = f"{float(prod_val):,.0f}" if pd.notna(prod_val) else "-"
            except: prod_display = str(prod_val)
            ratio_class = ""; ratio_display = "-"
            if pd.notna(ratio_val):
                 try:
                     ratio_float = float(ratio_val); ratio_display = f"{ratio_float:.0f}%"
                     if ratio_float > 100: ratio_class = "high-value"
                     elif ratio_float < 90: ratio_class = "low-value"
                 except: ratio_display = str(ratio_val)
            panel_html += f'''<tr><td>{prod_name}</td><td class="text-right">{sales_display}</td><td class="text-right">{prod_display}</td><td class="{ratio_class} text-right">{ratio_display}</td></tr>'''
        try:
            total_sales = data['销量'].sum() if '销量' in data.columns and pd.api.types.is_numeric_dtype(data['销量']) else 0
            total_production = data['产量'].sum() if '产量' in data.columns and pd.api.types.is_numeric_dtype(data['产量']) else 0
            total_ratio = (total_sales / total_production * 100) if total_production > 0 else 0
            total_ratio_class = ""
            if total_ratio > 100: total_ratio_class = "high-value"
            elif total_ratio < 90: total_ratio_class = "low-value"
            panel_html += f'''<tr class="total-row"><td><strong>合计</strong></td><td class="text-right"><strong>{total_sales:,.0f}</strong></td><td class="text-right"><strong>{total_production:,.0f}</strong></td><td class="{total_ratio_class} text-right"><strong>{total_ratio:.0f}%</strong></td></tr>'''
        except Exception: panel_html += "<tr><td colspan='4'>计算合计时出错。</td></tr>"
    panel_html += '''</tbody></table></div></div></div>'''
    return panel_html

# Section generation function for Ratio details
def _generate_ratio_detail_section(product_sales_ratio_data):
    """生成每日产品产销率明细部分 (卡片 + 面板)"""
    if not product_sales_ratio_data or len(product_sales_ratio_data) == 0:
        return '''<div id="daily-ratio-details" class="section"><div class="section-header"><h2>每日产品产销率明细</h2><a href="ratio.html" class="btn btn-secondary btn-sm back-button">返回产销率总览</a></div><div class="section-body"><p>无产品产销率明细数据。</p></div></div>'''

    detail_html = '''
    <div id="daily-ratio-details" class="section">
        <div class="section-header">
            <h2>每日产品产销率明细</h2>
            <a href="ratio.html" class="btn btn-secondary btn-sm back-button">返回产销率总览</a>
        </div>
        <div class="section-body">
            <p>点击下方卡片查看当日各产品的产销率详情 (产销率 = 销量 / 产量 × 100%)。</p>
            <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">数据来源：产成品入库列表 & 销售发票执行查询（排除客户名称为空、副产品、鲜品的记录）</p>
            <div class="sales-container"><div class="sales-flex">
    '''
    processed_dates = set(); panel_html_parts = []
    # Sort data by date before generating cards
    try:
        # Ensure dates are comparable (e.g., datetime objects)
        sorted_data_items = sorted(product_sales_ratio_data, key=lambda x: x.get('date', datetime.min))
    except TypeError:
        # Fallback if dates are strings or mixed types
        sorted_data_items = sorted(product_sales_ratio_data, key=lambda x: str(x.get('date', '')))
    except Exception:
        sorted_data_items = product_sales_ratio_data # General fallback

    for day_data_item in sorted_data_items:
        if not isinstance(day_data_item, dict) or 'date' not in day_data_item or 'data' not in day_data_item: continue
        date = day_data_item['date']; data_df = day_data_item['data']
        try: date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
        except Exception: date_str = str(date)
        if date_str in processed_dates: continue
        processed_dates.add(date_str)
        avg_ratio = 0; product_count = 0
        if data_df is not None and not data_df.empty and '销量' in data_df.columns and '产量' in data_df.columns:
            try:
                total_sales = data_df['销量'].sum(); total_production = data_df['产量'].sum()
                avg_ratio = (total_sales / total_production * 100) if total_production > 0 else 0
                product_count = len(data_df)
            except Exception: pass
        detail_html += f'''
            <div class="sales-flex-item">
                <div class="sales-card" onclick="toggleRatioPanel('{date_str}', event)">
                    <div class="sales-card-header"><h4><i class="bi bi-calendar3"></i> {date_str}</h4><i class="bi bi-chevron-down toggle-icon"></i></div>
                    <div class="sales-card-body"><p><i class="bi bi-speedometer2"></i> 平均: <strong>{avg_ratio:.1f}%</strong></p><p><i class="bi bi-collection"></i> 产品数: <strong>{product_count}</strong></p></div>
                    <div class="card-hint">点击查看详情</div>
                </div>
                </div>
        '''
        panel_html_parts.append(_generate_product_sales_ratio_detail_panel(date_str, data_df))
    detail_html += '''</div></div>''' # Close sales-flex, sales-container
    detail_html += "\n".join(panel_html_parts) # Append panels
    detail_html += '''</div></div>''' # Close section-body, section
    return detail_html
# --- Copied and adapted from ratio_report.py --- END ---

# --- Copied and adapted from sales_report.py --- START ---
# Panel generation function (used by _generate_sales_detail_section)
def _generate_sales_detail_panel(date_str, sales_data, quantity_column):
    """生成每日销售明细面板的HTML。"""
    if sales_data is None or sales_data.empty:
         # Return an empty div with the panel ID so JS doesn't break
        return f'''<div id="salesPanel_{date_str}" class="sales-panel" style="display: none;">
                 <div class="sales-panel-header"><h4>销售明细 - {date_str}</h4><button onclick="togglePanel('salesPanel_{date_str}', event)" class="close-button"><i class="bi bi-x-lg"></i></button></div>
                 <div class="sales-panel-body"><p>当日无详细销售数据。</p></div>
               </div>'''

    panel_html = f'''
    <div id="salesPanel_{date_str}" class="sales-panel" style="display: none;">
        <div class="sales-panel-header">
            <h4>销售明细 - {date_str}</h4>
            <div class="sales-panel-controls">
                <input type="text" id="salesSearch_{date_str}" onkeyup="searchTableInPanel('salesTable_{date_str}', 'salesSearch_{date_str}')" placeholder="搜索产品..." class="search-input">
                <button onclick="togglePanel('salesPanel_{date_str}', event)" class="close-button"><i class="bi bi-x-lg"></i></button>
            </div>
        </div>
        <div class="sales-panel-body">
            <div class="sales-table-container table-responsive">
                <table id="salesTable_{date_str}" class="mobile-friendly-table">
                    <thead><tr><th>物料名称</th><th>销量</th><th>销售金额(无税)</th><th>含税单价(元/吨)</th></tr></thead>
                    <tbody>
    '''
    sorted_sales = sales_data
    try:
        if quantity_column and quantity_column in sales_data.columns and pd.api.types.is_numeric_dtype(sales_data[quantity_column]): sorted_sales = sales_data.sort_values(by=quantity_column, ascending=False, na_position='last')
        elif '本币无税金额' in sales_data.columns and pd.api.types.is_numeric_dtype(sales_data['本币无税金额']): sorted_sales = sales_data.sort_values(by='本币无税金额', ascending=False, na_position='last')
    except Exception: pass

    required_cols = ['物料名称', '本币无税金额', '含税单价']
    if quantity_column: required_cols.append(quantity_column)
    if not all(col in sorted_sales.columns for col in required_cols):
         panel_html += "<tr><td colspan='4'>销售明细数据列不完整。</td></tr>"
    else:
        for _, row in sorted_sales.iterrows():
            mat_name = row.get('物料名称', 'N/A'); amount_val = row.get('本币无税金额'); unit_price_val = row.get('含税单价'); quantity_val = row.get(quantity_column) if quantity_column else None
            quantity_display = "-"; amount_display = "-"; unit_price_display = "-"

            # Format values safely with proper try-except blocks
            if quantity_val is not None:
                try:
                    quantity_display = f"{float(quantity_val):,.0f}"
                except (ValueError, TypeError):
                    quantity_display = str(quantity_val)

            if amount_val is not None:
                try:
                    amount_display = f"{float(amount_val):,.0f}"
                except (ValueError, TypeError):
                    amount_display = str(amount_val)

            if unit_price_val is not None:
                try:
                    unit_price_display = f"{float(unit_price_val):,.0f}"
                except (ValueError, TypeError):
                    unit_price_display = str(unit_price_val)

            panel_html += f'''<tr><td>{mat_name}</td><td class="text-right">{quantity_display}</td><td class="text-right">{amount_display}</td><td class="text-right">{unit_price_display}</td></tr>'''
        try:
             total_volume = sorted_sales[quantity_column].sum() if quantity_column and quantity_column in sorted_sales.columns and pd.api.types.is_numeric_dtype(sorted_sales[quantity_column]) else None
             total_amount = sorted_sales['本币无税金额'].sum() if '本币无税金额' in sorted_sales.columns and pd.api.types.is_numeric_dtype(sorted_sales['本币无税金额']) else 0
             volume_total_display = f"{float(total_volume):,.0f}" if total_volume is not None else "-"
             amount_total_display = f"{float(total_amount):,.0f}"

             # Calculate average price for the total row
             total_avg_price_display = "-"
             if total_volume is not None and total_volume > 0 and total_amount is not None:
                 try:
                     # Formula: 金额 / 销量(kg) * 1.09 * 1000 = 元/吨 (含税)
                     # Assuming total_amount is 无税金额 and total_volume is in KG
                     avg_price = (total_amount / total_volume) * 1.09 * 1000
                     total_avg_price_display = f"{avg_price:,.0f}"
                 except ZeroDivisionError:
                     total_avg_price_display = "无法计算"
                 except Exception:
                     total_avg_price_display = "计算错误"

             panel_html += f'''<tr class="total-row">
                                <td><strong>合计</strong></td>
                                <td class="text-center"><strong>{volume_total_display}</strong></td>
                                <td class="text-center"><strong>{amount_total_display}</strong></td>
                                <td class="text-center"><strong>{total_avg_price_display}</strong></td>
                            </tr>'''
        except Exception: pass # Ignore error in total calculation
    panel_html += '''</tbody></table></div></div></div>'''
    return panel_html

# Section generation function for Sales details
def _generate_sales_detail_section(daily_sales):
    """生成每日销售明细部分 (卡片 + 面板)"""
    if not daily_sales or len(daily_sales) == 0:
        return '''<div id="daily-sales-details" class="section"><div class="section-header"><h2>每日销售明细</h2><a href="sales.html" class="btn btn-secondary btn-sm back-button">返回销售总览</a></div><div class="section-body"><p>无销售明细数据可供显示。</p></div></div>'''

    detail_html = '''
    <div id="daily-sales-details" class="section">
        <div class="section-header">
            <h2>每日销售明细</h2>
            <a href="sales.html" class="btn btn-secondary btn-sm back-button">返回销售总览</a>
        </div>
        <div class="section-body">
            <p>点击下方卡片查看当日各产品的销售详情。</p>
            <p style="text-align: right; font-size: 12px; color: #666; margin-top: 5px;">数据来源：销售发票执行查询（排除客户名称为空、副产品、鲜品的记录）</p>
            <div class="sales-container"><div class="sales-flex">
    '''
    try:
        # Ensure dates are comparable
        sorted_dates = sorted(daily_sales.keys())
    except TypeError:
        # Fallback if dates are strings or mixed types
        sorted_dates = sorted(daily_sales.keys(), key=str)
    except Exception:
        sorted_dates = list(daily_sales.keys())

    panel_html_parts = []
    for date in sorted_dates:
        sales_info = daily_sales.get(date)
        if not isinstance(sales_info, dict): continue
        try: date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
        except Exception: date_str = str(date)

        daily_volume = sales_info.get('volume', 0); daily_avg_price = sales_info.get('avg_price'); product_count = sales_info.get('product_count', 0)
        sales_data_df = sales_info.get('data'); quantity_column = sales_info.get('quantity_column')
        volume_display = "-"; avg_price_display = "无法计算"
        try: volume_display = f"{float(daily_volume):,.0f}" if pd.notna(daily_volume) else "-" # Assuming volume is KG/units
        except: volume_display = str(daily_volume)
        if daily_avg_price is not None:
            try: avg_price_display = f"{float(daily_avg_price):,.0f} 元/吨"
            except: avg_price_display = f"{str(daily_avg_price)} 元/吨"

        detail_html += f'''
            <div class="sales-flex-item">
                <div class="sales-card" onclick="toggleSalesPanel('{date_str}', event)">
                    <div class="sales-card-header"><h4><i class="bi bi-calendar3"></i> {date_str}</h4><i class="bi bi-chevron-down toggle-icon"></i></div>
                    <div class="sales-card-body">
                        <p><i class="bi bi-box"></i> 销量: <strong>{volume_display}</strong></p>
                        <p><i class="bi bi-currency-yen"></i> 均价: <strong>{avg_price_display}</strong></p>
                        <p><i class="bi bi-collection"></i> 产品数: <strong>{product_count}</strong></p>
            </div>
                    <div class="card-hint">点击查看详情</div>
                </div>
                </div>
        '''
        panel_html_parts.append(_generate_sales_detail_panel(date_str, sales_data_df, quantity_column))
    detail_html += '''</div></div>''' # Close sales-flex, sales-container
    detail_html += "\n".join(panel_html_parts)
    detail_html += '''</div></div>''' # Close section-body, section
    return detail_html
# --- Copied and adapted from sales_report.py --- END ---

def generate_details_page(product_sales_ratio_data, daily_sales, output_dir):
    """生成 details.html 页面
    Args:
        product_sales_ratio_data (list): 每日产品产销率明细数据列表。
        daily_sales (dict): 每日销售数据。
        output_dir (str): HTML 文件输出目录。
    """
    print("开始生成 details.html 页面...")
    page_title = "春雪食品生品产销分析报告 - 详细数据"

    # Generate content for the two sections using placeholders for now
    ratio_details_html = _generate_ratio_detail_section(product_sales_ratio_data)
    sales_details_html = _generate_sales_detail_section(daily_sales)

    # Assemble page
    header_html = generate_header(title=page_title, output_dir=output_dir)
    nav_html = generate_navigation(active_page="details")
    footer_html = generate_footer()

    # Add CSS Styles and container
    # Ensure necessary JS functions (togglePanel, searchTableInPanel) are loaded, assuming via generate_footer or generate_header
    full_html = header_html + CSS_STYLES + "<div class='container'>" + nav_html + ratio_details_html + sales_details_html + "</div>" + footer_html

    write_html_report(full_html, "details.html", output_dir)
    print(f"details.html 页面已生成在 {output_dir}")

# --- Example Usage (Updated for testing, needs dummy data matching new args) ---
if __name__ == '__main__':
    # Dummy data needs to match new function signature
    dummy_product_ratio_details = [
        {'date': datetime(2023, 10, 25), 'data': pd.DataFrame({'品名': ['A'], '销量': [1], '产量': [2], '产销率': [50]})},
    ]
    dummy_daily_sales = {
        datetime(2023, 10, 25): {'volume': 5000, 'avg_price': 15000, 'product_count': 1, 'data': pd.DataFrame({'物料名称':['X']}), 'quantity_column': 'Q'},
    }
    output_directory = './test_report_output'
    import os
    os.makedirs(output_directory, exist_ok=True)

    generate_details_page(dummy_product_ratio_details, dummy_daily_sales, output_directory)
    print(f"测试 details.html 已生成在 {output_directory}") 