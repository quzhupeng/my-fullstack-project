# -*- coding: utf-8 -*-
"""
Main script to orchestrate the generation of all HTML reports.
Imports necessary functions from report modules and executes them.
"""

import os
import pandas as pd
from datetime import datetime

# --- Import Core Logic Classes ---
# Assuming config.py is used internally by these modules
from data_loader import DataLoader
from analyzer import PriceAnalyzer
from visualizer import DataVisualizer

# --- Import Report Generation Functions ---
print("--- Starting Imports ---")

print("Importing index_report...")
from index_report import generate_index_page
print("Imported index_report.")

print("Importing inventory_report...")
from inventory_report import generate_inventory_page
print("Imported inventory_report.")

print("Importing ratio_report...")
from ratio_report import generate_ratio_page
print("Imported ratio_report.")

print("Importing sales_report...")
from sales_report import generate_sales_page
print("Imported sales_report.")

print("Importing details_report...")
from details_report import generate_details_page
print("Imported details_report.")

print("Importing comparison_report...")
from comparison_report import generate_comparison_page
print("Imported comparison_report.")

print("Importing industry_report...")
from industry_report import generate_industry_page
print("Imported industry_report.")

print("--- Finished Imports ---")

# --- Main Report Generation Function ---
def generate_all_reports():
    """
    Loads real data, performs analysis, generates visualizations,
    and then generates all HTML report pages.
    """
    output_dir = './output_html_report'
    print(f"Ensuring output directory exists: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    # --- Instantiate Core Logic Classes ---
    loader = DataLoader()
    visualizer = DataVisualizer(output_dir=output_dir)

    # --- Load Real Data ---
    print("\n--- Loading Real Data ---")
    # Price data (调价表) - Used by PriceAnalyzer
    # Pass the directory containing the Excel files if config.DATA_PATH is a dir, or the file itself.
    # Assuming config.DATA_PATH points to the specific file for simplicity based on original file structure.
    all_price_data = loader.load_and_process_price_data() # Uses config.DATA_PATH by default
    if all_price_data is None or all_price_data.empty:
        print("Error: Failed to load price data (调价表). Aborting.")
        return

    # Inventory data (收发存汇总表查询) - Used for inventory report
    inventory_data = loader.load_inventory_data() # Uses config.INVENTORY_PATH by default
    if inventory_data is None:
        print("Warning: Failed to load inventory data. Inventory report might be empty.")
        inventory_data = pd.DataFrame(columns=['品名', '产量', '销量', '库存量']) # Provide empty DF

    # Sales data (销售发票执行查询) - Used for sales trend, ratio analysis
    sales_data = loader.load_sales_data() # Uses config.SALES_PATH by default
    if sales_data is None:
         print("Warning: Failed to load sales data. Sales report and ratio analysis might be affected.")
         sales_data = pd.DataFrame() # Provide empty DF

    # Production data (产成品入库列表) - Used for ratio analysis
    # Returns dict: {'by_material': {date: {product: qty}}, 'total': {date: total_qty}}
    daily_production_data = loader.load_daily_production_data() # Uses config.PRODUCTION_PATH by default
    if not daily_production_data or not daily_production_data.get('by_material'):
         print("Warning: Failed to load production data. Ratio analysis might be affected.")
         daily_production_data = {'by_material': {}, 'total': {}} # Provide empty structure

    # Comparison data (春雪与小明农牧价格对比)
    # Assuming the comparison file path is hardcoded in the loader or added to config.py
    # loader.load_price_comparison_data() handles the path internally now.
    comparison_data = loader.load_price_comparison_data()
    if comparison_data is None:
        print("Warning: Failed to load comparison data. Comparison report might be empty.")
        comparison_data = pd.DataFrame(columns=['品名', '规格', '春雪价格', '小明中间价', '中间价差']) # Provide empty DF

    # Comprehensive price data (综合售价)
    comprehensive_price_file = loader.load_comprehensive_price_data() # 现在返回文件路径而不是数据
    if comprehensive_price_file is None:
         print("Warning: Failed to find comprehensive price file. Sales page might be missing table.")
         
    # Industry price data (卓创资讯价格数据)
    industry_price_data = loader.load_industry_price_data() # 加载卓创资讯价格数据
    if not industry_price_data:
        print("Warning: Failed to load industry price data. Industry report might be empty.")
        # 如果没有数据，创建一个空字典
        industry_price_data = {'鸡苗': None, '毛鸡': None, '板冻大胸': None, '琵琶腿': None}

    print("--- Finished Loading Data ---\n")


    # --- Analyze Data ---
    print("--- Analyzing Data ---")
    # Pass loaded data to Analyzer. Analyzer might use config paths too internally if needed.
    analyzer = PriceAnalyzer(
        all_data=all_price_data,
        sales_data=sales_data,
        # industry_trend_data=industry_trend_data, # Load if needed by analyzer
        daily_production_data=daily_production_data # Pass the dict structure
    )
    analyzer.analyze_price_changes() # Analyzes self.all_data for abnormal, inconsistent, conflict records

    # Process sales data to get daily summaries needed for the sales report
    processed_daily_sales = analyzer.process_sales_data() # Analyzes self.sales_data
    if processed_daily_sales is None:
        print("Warning: Failed to process daily sales data. Sales report might be empty.")
        processed_daily_sales = {} # Provide empty dict

    # Calculate overall production/sales ratio summary for ratio_report
    # Recalculate daily totals from the 'by_material' dicts or use pre-calculated 'total'
    prod_total_by_date = daily_production_data.get('total', {})
    sales_total_by_date_from_processed = {date: data['volume'] for date, data in processed_daily_sales.items()}

    ratio_summary_data = {}
    all_ratio_dates = sorted(set(list(sales_total_by_date_from_processed.keys()) + list(prod_total_by_date.keys())))
    for date in all_ratio_dates:
        sales_vol = sales_total_by_date_from_processed.get(date, 0)
        prod_vol = prod_total_by_date.get(date, 0)
        ratio = (sales_vol / prod_vol * 100) if prod_vol > 0 else 0
        ratio = min(ratio, 500) # Clip ratio similar to analyzer's internal logic if needed
        ratio_summary_data[date] = {'sales': sales_vol, 'production': prod_vol, 'ratio': ratio}
    print(f"Calculated ratio summary for {len(ratio_summary_data)} dates.")

    # Calculate product-level sales ratio details for ratio_report
    # Pass the dictionary structures loaded earlier
    # product_ratio_details = analyzer.calculate_product_sales_ratio_detail(
    #     daily_sales_data={'by_material': {}}, # Placeholder - Removed, use correct data below
    #     daily_production_data=daily_production_data
    # )
    # Self-correction: The sales data needed here is likely the raw sales grouped by date/material.
    # DataLoader's load_daily_sales_data seems designed for this, but was maybe overwritten.
    # Let's call it again or ensure the main sales_data load retains this structure if needed.
    # Re-checking DataLoader: load_sales_data returns a DataFrame. load_daily_sales_data returns the dict.
    # Let's load the dict version specifically for the analyzer's detail calculation.
    print("Loading sales data specifically for detailed ratio calculation...")
    # Assuming config.SALES_PATH is correct for this function too
    specific_sales_data_for_ratio = loader.load_daily_sales_data(path=None) # Uses config.SALES_PATH
    if specific_sales_data_for_ratio is None:
        print("Warning: Failed to load specific sales data for ratio details.")
        specific_sales_data_for_ratio = {'by_material': {}}

    # Use the correctly loaded data in the call
    product_ratio_details = analyzer.calculate_product_sales_ratio_detail(
        daily_sales_data=specific_sales_data_for_ratio,
        daily_production_data=daily_production_data
    )
    if product_ratio_details is None:
        print("Warning: Failed to calculate product ratio details.")
        product_ratio_details = [] # Provide empty list


    # Get analysis results from analyzer instance
    abnormal_changes = analyzer.abnormal_changes
    inconsistent_records = analyzer.inconsistent_records
    conflict_records = analyzer.conflict_records

    print("--- Finished Analyzing Data ---\n")

    # --- Generate Visualizations ---
    print("--- Generating Visualizations ---")
    # Generate charts using visualizer instance and real data
    vis_inventory_path = visualizer.generate_inventory_visualization(inventory_data)
    vis_sales_trend_path = visualizer.generate_daily_sales_trend(processed_daily_sales)
    # Pass the calculated ratio_summary_data dictionary
    vis_ratio_path = visualizer.generate_production_sales_ratio_chart(ratio_summary_data, os.path.join(output_dir, "production_sales_ratio.png"))
    
    # 不再生成综合售价图表，直接使用Excel文件
    # 如果以下代码存在则注释掉：
    # vis_comp_price_path = visualizer.generate_comprehensive_price_chart(comprehensive_price_data, os.path.join(output_dir, "comprehensive_price_chart.png"))
    
    print("--- Finished Generating Visualizations ---\n")

    # --- Prepare Data Dictionary for Reports ---
    print("--- Preparing Data for Reports ---")
    # Calculate summary data for index page based on real analysis results
    final_summary_data = {
         "total_products": inventory_data['品名'].nunique() if not inventory_data.empty else 0,
         "avg_ratio": sum(d['ratio'] for d in ratio_summary_data.values()) / len(ratio_summary_data) if ratio_summary_data else 0,
         "total_sales_volume": sum(d.get('volume', 0) for d in processed_daily_sales.values()) if processed_daily_sales else 0,
         "total_inventory": inventory_data['库存量'].sum() if not inventory_data.empty else 0,
         "abnormal_count": len(abnormal_changes),
         "inconsistent_count": len(inconsistent_records),
         "conflict_count": len(conflict_records), # Use the length of the collected records
         "negative_price_diff_count": len(comparison_data[comparison_data['中间价差'] < 0]) if not comparison_data.empty else 0
     }

    # Create the dictionary to pass data to report generation functions
    data_for_reports = {
        "summary_data": final_summary_data,
        "inventory_data": inventory_data, # Pass the loaded DF
        "ratio_summary": ratio_summary_data, # Pass the calculated summary dict {date: {ratio:.., sales:.., prod:..}}
        "product_ratio_details": product_ratio_details, # Pass the list of dicts [{date:..., data:DF}, ...]
        "daily_sales": processed_daily_sales, # Pass the dict {date: {data:DF, volume:...}}
        "comprehensive_price_file": comprehensive_price_file,  # 传递文件路径
        "abnormal_changes": abnormal_changes, # Pass list of dicts
        "inconsistent_records": inconsistent_records, # Pass list of dicts
        "conflict_records": conflict_records, # Pass list of dicts
        "price_comparison_data": comparison_data, # Pass the loaded DF
        "industry_price_data": industry_price_data # Pass the industry price data dict
    }
    print("--- Finished Preparing Data ---\n")


    # --- Generate Individual Report Pages ---
    print("--- Generating Reports ---")

    # 1. Index Page
    try:
        print("Generating index.html...")
        summary_data_for_index = {
            'all_data': all_price_data,
            'abnormal_changes': data_for_reports["abnormal_changes"],
            'inconsistent_records': data_for_reports["inconsistent_records"],
            'missing_dates': [], # Placeholder
            'production_sales_ratio': data_for_reports["ratio_summary"],
            'daily_sales': data_for_reports["daily_sales"]
        }
        generate_index_page(summary_data_for_index, output_dir)
        print("index.html generated.")
    except Exception as e:
        print(f"Error generating index.html: {e}")
        # import traceback; traceback.print_exc() # Uncomment for debugging

    # 2. Inventory Page
    try:
        print("Generating inventory.html...")
        generate_inventory_page(data_for_reports["inventory_data"], output_dir)
        print("inventory.html generated.")
    except Exception as e:
        print(f"Error generating inventory.html: {e}")
        # import traceback; traceback.print_exc()

    # 3. Ratio Page
    try:
        print("Generating ratio.html...")
        generate_ratio_page(data_for_reports["ratio_summary"], data_for_reports["product_ratio_details"], output_dir)
        print("ratio.html generated.")
    except Exception as e:
        print(f"Error generating ratio.html: {e}")
        # import traceback; traceback.print_exc()

    # 4. Sales Page
    try:
        print("Generating sales.html...")
        generate_sales_page(data_for_reports["daily_sales"], data_for_reports["comprehensive_price_file"], output_dir)
        print("sales.html generated.")
    except Exception as e:
        print(f"Error generating sales.html: {e}")
        # import traceback; traceback.print_exc()

    # 5. Details Page (Now contains ratio and sales details)
    try:
        print("Generating details.html...")
        # Pass the required detailed data
        generate_details_page(
            product_sales_ratio_data=data_for_reports["product_ratio_details"],
            daily_sales=data_for_reports["daily_sales"],
            output_dir=output_dir
        )
        print("details.html generated.")
    except Exception as e:
        print(f"Error generating details.html: {e}")
        # import traceback; traceback.print_exc()

    # 6. Price Volatility Page (Was Comparison Page)
    try:
        print("Generating price_volatility.html...")
        print(f"Number of conflict_records: {len(data_for_reports['conflict_records'])}")
        # Pass comparison data and conflict (adjustment) records
        generate_comparison_page(
            price_comparison_data=data_for_reports["price_comparison_data"],
            conflict_records=data_for_reports["conflict_records"],
            output_dir=output_dir
        )
        print("price_volatility.html generated.")
    except Exception as e:
        print(f"Error generating price_volatility.html: {e}")
        # import traceback; traceback.print_exc()
        
    # 7. Industry Price Page (New)
    try:
        print("Generating industry.html...")
        # Pass industry price data
        generate_industry_page(
            industry_data=data_for_reports["industry_price_data"],
            output_dir=output_dir
        )
        print("industry.html generated.")
    except Exception as e:
        print(f"Error generating industry.html: {e}")
        import traceback; traceback.print_exc()

    print("--- Finished Generating Reports ---")

def main():
    """Main execution function."""
    start_time = datetime.now()
    print(f"Report generation started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    generate_all_reports()
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Report generation finished at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration}")

if __name__ == "__main__":
    main() 