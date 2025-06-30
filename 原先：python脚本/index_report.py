# -*- coding: utf-8 -*-
"""
生成报告主页 (index.html)，包含摘要信息。
"""

from html_utils import generate_header, generate_navigation, write_html_report
# 导入generate_footer但不直接使用，我们将重写这个函数
from html_utils import generate_footer as original_generate_footer

# --- CSS Styles ---
# Moved CSS here to be accessible by generate_index_page
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
        background-color: #fff; /* Keep sections white */
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
    .summary strong {
        color: #0056b3; /* Highlight key metrics */
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
            font-size: 16px; /* Adjust base font size for mobile */
        }
        h2 {
            font-size: 1.5em;
        }
    }
</style>
"""

def _generate_summary_content(summary_data):
    """生成摘要部分的HTML内容

    Args:
        summary_data (dict): 包含摘要所需数据的字典，例如:
            {
                'all_data': all_data_df, # For total products/dates
                'abnormal_changes': abnormal_changes_list,
                'inconsistent_records': inconsistent_records_list,
                'missing_dates': missing_dates_list,
                'production_sales_ratio': production_sales_ratio_dict,
                'daily_sales': daily_sales_dict
                # Note: Inventory data is not directly passed here, link will be static
            }
    """
    all_data = summary_data.get('all_data')
    abnormal_changes = summary_data.get('abnormal_changes')
    inconsistent_records = summary_data.get('inconsistent_records') # Used for data consistency check
    missing_dates = summary_data.get('missing_dates') # Used for data integrity check
    production_sales_ratio = summary_data.get('production_sales_ratio')
    daily_sales = summary_data.get('daily_sales')

    # 数据概览
    total_products = 0
    total_dates = 0
    if all_data is not None and not all_data.empty:
         total_products = all_data['品名'].nunique() if '品名' in all_data.columns else 0
         total_dates = all_data['日期'].nunique() if '日期' in all_data.columns else 0

    summary_html = f"""
        <div class="section">
            <div class="section-header">
                <h2>核心指标摘要</h2>
            </div>
            <div class="section-body">
                <div class="summary">
                    <p><strong>报告范围:</strong> 分析覆盖 <strong>{total_products}</strong> 种产品，时间跨度 <strong>{total_dates}</strong> 天。</p>
                    <ul>
    """

    # 1. 库存情况 (Link only, as specific summary data isn't passed)
    summary_html += "<li><strong>库存情况:</strong> 详细库存水平、周转天数等请参见 <a href='inventory.html'>库存分析报告</a>。</li>"

    # 2. 产销率情况
    ratio_summary = "" # Default empty string
    if production_sales_ratio and len(production_sales_ratio) > 0:
        try:
            valid_ratios = [data.get('ratio', 0) for data in production_sales_ratio.values() if isinstance(data.get('ratio'), (int, float))]
            if len(valid_ratios) > 0:
                 avg_ratio = sum(valid_ratios) / len(valid_ratios)
                 ratio_summary = f"期间平均产销率为 <strong>{avg_ratio:.1f}%</strong>。"
                 if avg_ratio < 90:
                     ratio_summary += " (提示: 偏低，可能存在积压风险)"
                 elif avg_ratio > 110:
                     ratio_summary += " (提示: 偏高，可能存在缺货风险)"
                 else:
                     ratio_summary += " (提示: 产销相对平衡)"
            else:
                 ratio_summary = "无法计算平均产销率（无有效数据）。"
        except Exception as e:
              ratio_summary = f"计算产销率时出错: {e}"
    else:
        ratio_summary = "无产销率数据。"
    summary_html += f"<li><strong>产销率情况:</strong> {ratio_summary} 详细分析请参见 <a href='ratio.html'>产销率报告</a>。</li>"


    # 3. 销售情况 (MODIFIED FOR UNIT CONVERSION)
    sales_summary = "" # Default empty string
    if daily_sales and len(daily_sales) > 0:
        try:
            total_sales_volume_kg = sum(info.get('volume', 0) for info in daily_sales.values() if info and isinstance(info.get('volume'), (int, float)))
            total_sales_volume_tons = total_sales_volume_kg / 1000.0 # Convert KG to Tons

            valid_avg_prices = [info.get('avg_price') for info in daily_sales.values() if info and isinstance(info.get('avg_price'), (int, float))]
            avg_price = sum(valid_avg_prices) / len(valid_avg_prices) if valid_avg_prices else 0
            # Format tons with maybe one decimal place for precision if needed, or keep as int if preferred.
            sales_summary = f"期间总销量约为 <strong>{total_sales_volume_tons:,.1f}</strong> 吨。"
            if avg_price > 0:
                 sales_summary += f" 加权平均销售单价约为 <strong>{int(avg_price):,}</strong> 元/吨。"
        except Exception as e:
              sales_summary = f"计算销售摘要时出错: {e}"
    else:
        sales_summary = "无销售数据。"
    summary_html += f"<li><strong>销售情况:</strong> {sales_summary} 详细趋势请参见 <a href='sales.html'>销售分析报告</a>。</li>"

    # 4. 价格波动情况 (Focus on large fluctuations)
    price_summary = "" # Default empty string
    if abnormal_changes and len(abnormal_changes) > 0:
        price_summary = "监测到部分产品价格调整较为频繁。" # Changed to a general statement
    else:
        price_summary = "未监测到价格调整频率明显异常的情况。" # Changed to a general statement
    # Link to the page where adjustment records are shown (price_volatility.html)
    summary_html += f"<li><strong>价格波动情况:</strong> {price_summary} 详细调价记录请参见 <a href='price_volatility.html'>价格波动分析页</a>。</li>"
    
    # 5. 添加卓创资讯行业价格趋势导航
    summary_html += "<li><strong>行业价格趋势:</strong> 查看卓创资讯提供的行业价格监测数据，请参见 <a href='industry.html'>行业价格趋势</a>。</li>"

    summary_html += "</ul>"

    # Data Integrity/Consistency Notes (Keep them separate)
    integrity_notes = ""
    if missing_dates:
        integrity_notes += f"<p style='font-size:0.9em; color:#666;'>注：发现 {len(missing_dates)} 个日期数据缺失或不完整。</p>"
    if inconsistent_records and len(inconsistent_records) > 0:
        integrity_notes += f"<p style='font-size:0.9em; color:#666;'>注：发现 <a href='details.html'>{len(inconsistent_records)} 条</a> 调幅与价格变动不一致记录。</p>"

    if integrity_notes:
        summary_html += "<hr style='border:none; border-top: 1px solid #eee; margin: 15px 0;'>" + integrity_notes

    summary_html += """
                </div>
            </div>
        </div>
    """
    return summary_html

# SECURITY_TAG: PRIVATE_ACCESS_FOOTER_BEGIN
def generate_footer():
    """生成HTML页脚，包含隐藏链接"""
    from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"""
            <div class="section">
                <div class="section-header">
                    <h2>报告说明</h2>
                </div>
                <div class="section-body">
                    <p>本报告数据来源于企业内部系统。报告中的分析结果仅供参考，具体业务决策请结合实际情况。</p>
                    <p>如有任何问题<a href="private_access.html" style="color:inherit;text-decoration:none;">或</a>建议，请联系guanlibu@springsnow.cn</p>
                    <p style="text-align: right; margin-top: 20px;">
                        报告生成时间：{current_time}
                    </p>
                </div>
            </div>
        </div> <!-- Close container -->
        <script>
             // Add specific JS calls needed on all pages after DOM load, if any were in the original footer
             // e.g., initializing components
              function searchAbnormal() {{ searchTable('abnormalTable', 'abnormalSearch'); }}
              function searchInconsistent() {{ searchTable('inconsistentTable', 'inconsistentSearch'); }}
              function searchConflict() {{ searchTable('conflictTable', 'conflictSearch'); }}
              function searchComparison() {{ searchTable('comparisonTable', 'comparisonSearch'); }}
              
              // 表格搜索函数 - 用于一般表格搜索
              function searchTable(tableId, inputId) {{
                  const input = document.getElementById(inputId);
                  const filter = input.value.toUpperCase();
                  const table = document.getElementById(tableId);
                  const tr = table.getElementsByTagName("tr");
                  
                  for (let i = 0; i < tr.length; i++) {{
                      if (i === 0) continue; // 跳过表头
                      const td = tr[i].getElementsByTagName("td");
                      let txtValue = "";
                      let visible = false;
                      
                      for (let j = 0; j < td.length; j++) {{
                          if (td[j]) {{
                              txtValue = td[j].textContent || td[j].innerText;
                              if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                                  visible = true;
                                  break;
                              }}
                          }}
                      }}
                      
                      tr[i].style.display = visible ? "" : "none";
                  }}
              }}
              
              // 切换面板显示/隐藏
              function togglePanel(panelId, event) {{
                  if (event) event.stopPropagation();
                  const panel = document.getElementById(panelId);
                  if (panel) {{
                      if (panel.style.display === "none" || panel.style.display === "") {{
                          panel.style.display = "block";
                      }} else {{
                          panel.style.display = "none";
                      }}
                  }}
              }}
              
              // 切换产销率明细面板
              function toggleRatioPanel(dateStr, event) {{
                  if (event) event.stopPropagation();
                  const panelId = `ratioPanel_${{dateStr}}`;
                  togglePanel(panelId, null);
              }}
              
              // 切换销售明细面板
              function toggleSalesPanel(dateStr, event) {{
                  if (event) event.stopPropagation();
                  const panelId = `salesPanel_${{dateStr}}`;
                  togglePanel(panelId, null);
              }}
        </script>
    </body>
</html>
"""
# SECURITY_TAG: PRIVATE_ACCESS_FOOTER_END

def generate_index_page(summary_data, output_dir):
    """生成 index.html 页面

    Args:
        summary_data (dict): 传递给 _generate_summary_content 的数据字典。
        output_dir (str): HTML 文件输出目录。
    """
    print("开始生成 index.html 页面...")
    if not isinstance(summary_data, dict):
        print("错误: summary_data 不是有效的字典。无法生成 index.html。")
        return

    page_title = "春雪食品生品产销分析报告 - 摘要"
    header_html = generate_header(title=page_title)
    nav_html = generate_navigation(active_page="index")
    summary_content_html = _generate_summary_content(summary_data)
    footer_html = generate_footer()

    # --- Add History Link Section Separately ---
    history_section_html = """
    <div class="section">
        <div class="section-header">
            <h2>历史报告存档</h2>
        </div>
        <div class="section-body">
             <ul>
                 <li><a href='history/'>浏览过往月份报告</a></li>
             </ul>
        </div>
    </div>
    """

    # Construct the full HTML, placing history section after summary, before footer
    full_html = header_html + CSS_STYLES + "<div class='container'>" + nav_html + summary_content_html + history_section_html + "</div>" + footer_html

    write_html_report(full_html, "index.html", output_dir)
    print(f"index.html 页面已生成在 {output_dir}")

# --- Example Usage (for testing) ---
if __name__ == '__main__':
    import pandas as pd
    # Create dummy data matching the structure expected by _generate_summary_content
    dummy_summary_data = {
        'all_data': pd.DataFrame({'品名': ['A', 'B', 'A'], '日期': ['2023-01-01', '2023-01-01', '2023-01-02']}),
        'abnormal_changes': [{'品名': 'Product X', '日期': '2023-10-25', '调价次数': 4}, {'品名': 'Product Y', '日期': '2023-10-26', '调价次数': 3}],
        'inconsistent_records': [{'品名': 'Product Z', '日期': '2023-10-25', '调幅': 100, '前价格': 5000, '价格': 4900, '价格变动': -100}],
        'missing_dates': ['2023-10-20', '2023-10-21'],
        'production_sales_ratio': {'2023-10-25': {'ratio': 95.5}, '2023-10-26': {'ratio': 105.2}, '2023-10-27': {'ratio': 'N/A'}}, # Added invalid data for testing
        'daily_sales': {
             '2023-10-25': {'volume': 5000, 'avg_price': 15000, 'product_count': 10, 'data': None, 'quantity_column': '销量'},
             '2023-10-26': {'volume': 6000, 'avg_price': 15500, 'product_count': 12, 'data': None, 'quantity_column': '销量'},
             '2023-10-27': None # Added missing data for testing
        }
    }
    output_directory = './test_report_output'
    generate_index_page(dummy_summary_data, output_directory)
    print(f"测试 index.html 已生成在 {output_directory}")
 