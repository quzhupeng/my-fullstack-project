import pandas as pd
import json
import os
import subprocess

# --- Configuration ---
EXCEL_FOLDER = './Excel文件夹/'

# File paths
inv_summary_path = os.path.join(EXCEL_FOLDER, '收发存汇总表查询.xlsx')
production_path = os.path.join(EXCEL_FOLDER, '产成品入库列表.xlsx')
sales_path = os.path.join(EXCEL_FOLDER, '销售发票执行查询.xlsx')

print("--- Starting D1 Data Import Script ---")
print("This script will import real production data via Wrangler D1")

def filter_products(df, product_col='物料名称'):
    """Apply data filtering logic from original Python script"""
    # Filter out fresh products (starting with '鲜') except '凤肠' products
    mask = ~df[product_col].str.startswith('鲜', na=False) | df[product_col].str.contains('凤肠', na=False)
    df = df[mask]
    
    # Filter out by-products and empty categories
    if '客户' in df.columns:
        df = df[~df['客户'].isin(['副产品', '鲜品']) | df['客户'].isna()]
    
    if '物料分类名称' in df.columns:
        df = df[~df['物料分类名称'].isin(['副产品', '生鲜品其他']) | df['物料分类名称'].isna()]
    
    return df

def process_sales_data(df_sales):
    """Process sales data from 销售发票执行查询.xlsx"""
    print("Processing sales data...")
    
    # Apply filtering
    df_sales = filter_products(df_sales, '物料名称')
    
    # Check available columns and extract relevant ones
    print(f"Available columns: {list(df_sales.columns)}")
    
    # Extract relevant columns - use 本币无税金额 for sales amount calculation
    required_columns = ['发票日期', '物料名称', '主数量', '本币无税金额', '物料分类']
    missing_columns = [col for col in required_columns if col not in df_sales.columns]
    
    if missing_columns:
        print(f"Warning: Missing columns: {missing_columns}")
        # Try alternative column names
        if '本币无税金额' not in df_sales.columns and '无税金额' in df_sales.columns:
            df_sales['本币无税金额'] = df_sales['无税金额']
            print("Using '无税金额' as '本币无税金额'")
    
    df_processed = df_sales[['发票日期', '物料名称', '主数量', '本币无税金额', '物料分类']].copy()
    df_processed.columns = ['record_date', 'product_name', 'sales_volume', 'tax_free_amount', 'category']
    
    # Convert date, volume, and amount
    df_processed['record_date'] = pd.to_datetime(df_processed['record_date']).dt.strftime('%Y-%m-%d')
    df_processed['sales_volume'] = pd.to_numeric(df_processed['sales_volume'], errors='coerce')
    df_processed['tax_free_amount'] = pd.to_numeric(df_processed['tax_free_amount'], errors='coerce')
    
    # Remove rows with missing data
    df_processed = df_processed.dropna(subset=['record_date', 'product_name', 'sales_volume', 'tax_free_amount'])
    df_processed = df_processed[df_processed['sales_volume'] > 0]
    df_processed = df_processed[df_processed['tax_free_amount'] > 0]
    
    # Group by date and product to aggregate data first
    df_processed = df_processed.groupby(['record_date', 'product_name', 'category']).agg({
        'sales_volume': 'sum',
        'tax_free_amount': 'sum'
    }).reset_index()

    # Calculate average unit price using the formula: (本币无税金额 / 主数量) * 1.09
    # Note: Assuming 主数量 is in KG, multiply by 1000 to get price per ton
    # Calculate this AFTER aggregation to get the correct weighted average
    df_processed['average_price'] = (df_processed['tax_free_amount'] / df_processed['sales_volume']) * 1.09 * 1000

    # Calculate sales amount (tax-inclusive) for display
    df_processed['sales_amount'] = df_processed['tax_free_amount'] * 1.09
    
    print(f"Processed sales data: {len(df_processed)} records")
    print(f"Date range: {df_processed['record_date'].min()} to {df_processed['record_date'].max()}")
    
    return df_processed

def execute_d1_command(command):
    """Execute a D1 command via wrangler"""
    try:
        result = subprocess.run([
            'npx', 'wrangler', 'd1', 'execute', 'chunxue-prod-db', '--local', '--command', command
        ], capture_output=True, text=True, cwd='backend')
        
        if result.returncode != 0:
            print(f"D1 command failed: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error executing D1 command: {e}")
        return False

def update_sales_amount_in_d1():
    """Update sales_amount values in D1 database"""
    print("\n--- Updating Sales Amount in D1 Database ---")
    
    try:
        # Load and process sales data
        df_sales = pd.read_excel(sales_path, sheet_name='销售发票执行查询')
        print(f"Loaded sales data: {len(df_sales)} rows")
        
        df_sales_processed = process_sales_data(df_sales)
        
        # Clear existing sales_amount data
        print("Clearing existing sales_amount data...")
        clear_cmd = "UPDATE DailyMetrics SET sales_amount = NULL WHERE sales_amount IS NOT NULL;"
        execute_d1_command(clear_cmd)
        
        # Update sales_amount for each record
        print("Updating sales_amount values...")
        update_count = 0
        
        for _, row in df_sales_processed.iterrows():
            # Find matching records in DailyMetrics and update sales_amount
            update_cmd = f"""
            UPDATE DailyMetrics 
            SET sales_amount = {row['sales_amount']}
            WHERE record_date = '{row['record_date']}' 
            AND product_id IN (
                SELECT product_id FROM Products WHERE product_name = '{row['product_name'].replace("'", "''")}'
            );
            """
            
            if execute_d1_command(update_cmd):
                update_count += 1
                if update_count % 100 == 0:
                    print(f"Updated {update_count} records...")
        
        print(f"Successfully updated {update_count} sales amount records")
        
        # Verify the update
        print("\nVerifying update...")
        verify_cmd = "SELECT record_date, SUM(sales_volume) as total_sales, SUM(sales_amount) as total_amount FROM DailyMetrics WHERE record_date BETWEEN '2025-06-01' AND '2025-06-05' AND sales_volume > 0 GROUP BY record_date ORDER BY record_date LIMIT 3;"
        execute_d1_command(verify_cmd)
        
        return True
        
    except Exception as e:
        print(f"Error updating sales amount: {e}")
        return False

if __name__ == "__main__":
    success = update_sales_amount_in_d1()
    if success:
        print("\n✅ D1 database update completed successfully!")
        print("You can now test the API to verify sales_amount values are correct.")
    else:
        print("\n❌ D1 database update failed!")
