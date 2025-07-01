import pandas as pd
import sqlite3
import os

# --- Configuration ---
EXCEL_FOLDER = './Excel文件夹/'
DB_NAME = 'backend/.wrangler/state/v3/d1/chunxue-prod-db.sqlite'

# File paths
inv_summary_path = os.path.join(EXCEL_FOLDER, '收发存汇总表查询.xlsx')
production_path = os.path.join(EXCEL_FOLDER, '产成品入库列表.xlsx')
sales_path = os.path.join(EXCEL_FOLDER, '销售发票执行查询.xlsx')

print("--- Starting Real Data Import Script ---")
print("This script will import real production data into DailyMetrics table")

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

def process_inventory_data(df_inv):
    """Process inventory data from 收发存汇总表查询.xlsx"""
    print("Processing inventory data...")
    
    # Apply filtering
    df_inv = filter_products(df_inv)
    
    # Extract relevant columns: 物料名称 → product_name, 结存 → inventory_level
    df_processed = df_inv[['物料名称', '结存', '物料分类名称']].copy()
    df_processed.columns = ['product_name', 'inventory_level', 'category']
    
    # Convert inventory to numeric (tons)
    df_processed['inventory_level'] = pd.to_numeric(df_processed['inventory_level'], errors='coerce')
    
    # Remove rows with missing data
    df_processed = df_processed.dropna(subset=['product_name', 'inventory_level'])
    df_processed = df_processed[df_processed['inventory_level'] > 0]
    
    # Add a recent date for inventory snapshot
    df_processed['record_date'] = '2025-06-26'  # Latest date
    
    return df_processed

def process_production_data(df_prod):
    """Process production data from 产成品入库列表.xlsx"""
    print("Processing production data...")
    
    # Apply filtering
    df_prod = filter_products(df_prod, '物料名称')
    
    # Extract relevant columns
    df_processed = df_prod[['入库日期', '物料名称', '主数量', '物料大类']].copy()
    df_processed.columns = ['record_date', 'product_name', 'production_volume', 'category']
    
    # Convert date and volume
    df_processed['record_date'] = pd.to_datetime(df_processed['record_date']).dt.strftime('%Y-%m-%d')
    df_processed['production_volume'] = pd.to_numeric(df_processed['production_volume'], errors='coerce')
    
    # Remove rows with missing data
    df_processed = df_processed.dropna(subset=['record_date', 'product_name', 'production_volume'])
    df_processed = df_processed[df_processed['production_volume'] > 0]
    
    # Group by date and product to sum production volumes
    df_processed = df_processed.groupby(['record_date', 'product_name', 'category']).agg({
        'production_volume': 'sum'
    }).reset_index()

    # Convert production volume from KG to tons (divide by 1000)
    # Note: 主数量 is in KG, convert to tons for display
    df_processed['production_volume'] = df_processed['production_volume'] / 1000

    return df_processed

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

    # Convert sales volume from KG to tons (divide by 1000)
    # Note: 主数量 is in KG, convert to tons for display
    df_processed['sales_volume'] = df_processed['sales_volume'] / 1000

    # Calculate average unit price using the formula: (本币无税金额 / 主数量) * 1.09
    # Note: Since we converted sales_volume to tons, multiply by 1.09 only (not 1000)
    # Calculate this AFTER aggregation to get the correct weighted average
    df_processed['average_price'] = (df_processed['tax_free_amount'] / (df_processed['sales_volume'] * 1000)) * 1.09 * 1000

    # Calculate sales amount (tax-inclusive) for display
    df_processed['sales_amount'] = df_processed['tax_free_amount'] * 1.09

    print(f"Processed sales data: {len(df_processed)} records")
    print(f"Date range: {df_processed['record_date'].min()} to {df_processed['record_date'].max()}")

    return df_processed

# --- 1. Load Data using Pandas ---
print(f"Loading data from: {EXCEL_FOLDER}")

try:
    # Inventory Summary: Main source for product list and inventory levels
    df_inv = pd.read_excel(inv_summary_path, sheet_name='收发存汇总表查询')
    print(f"Loaded inventory data: {len(df_inv)} rows")
    
    # Production Data
    df_prod = pd.read_excel(production_path, sheet_name='产成品入库列表')
    print(f"Loaded production data: {len(df_prod)} rows")
    
    # Sales Data
    df_sales = pd.read_excel(sales_path, sheet_name='销售发票执行查询')
    print(f"Loaded sales data: {len(df_sales)} rows")
    
    print("All Excel files loaded successfully.")
    
except Exception as e:
    print(f"Error loading Excel files: {e}")
    exit(1)

# --- 2. Process Data ---
print("\n--- Processing Data ---")

try:
    df_inventory = process_inventory_data(df_inv)
    df_production = process_production_data(df_prod)
    df_sales = process_sales_data(df_sales)
    
    print(f"Processed inventory data: {len(df_inventory)} rows")
    print(f"Processed production data: {len(df_production)} rows")
    print(f"Processed sales data: {len(df_sales)} rows")
    
except Exception as e:
    print(f"Error processing data: {e}")
    exit(1)

# --- 3. Database Operations ---
print("\n--- Database Operations ---")

try:
    # Connect to database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Clear existing DailyMetrics data (remove sample data)
    print("Removing any existing sample data from DailyMetrics...")
    cursor.execute("DELETE FROM DailyMetrics")
    conn.commit()
    print("Sample data removed.")
    
    # Get existing products or create new ones
    print("Processing products...")
    
    # Get all unique products from our data
    all_products = set()
    all_products.update(df_inventory['product_name'].unique())
    all_products.update(df_production['product_name'].unique())
    all_products.update(df_sales['product_name'].unique())
    
    print(f"Found {len(all_products)} unique products")
    
    # Create product mapping
    product_mapping = {}
    for product_name in all_products:
        cursor.execute("SELECT product_id FROM Products WHERE product_name = ?", (product_name,))
        result = cursor.fetchone()
        if result:
            product_mapping[product_name] = result[0]
        else:
            # Create new product
            cursor.execute("INSERT INTO Products (product_name, category) VALUES (?, ?)", 
                         (product_name, None))
            product_mapping[product_name] = cursor.lastrowid
    
    conn.commit()
    print(f"Product mapping created for {len(product_mapping)} products")

    # --- 4. Insert Real Data ---
    print("\n--- Inserting Real Data ---")

    # Combine all data into DailyMetrics format
    daily_metrics_data = []

    # Process inventory data
    for _, row in df_inventory.iterrows():
        if row['product_name'] in product_mapping:
            daily_metrics_data.append({
                'record_date': row['record_date'],
                'product_id': product_mapping[row['product_name']],
                'production_volume': None,
                'sales_volume': None,
                'sales_amount': None,
                'inventory_level': row['inventory_level'],
                'average_price': None
            })

    # Process production data
    for _, row in df_production.iterrows():
        if row['product_name'] in product_mapping:
            daily_metrics_data.append({
                'record_date': row['record_date'],
                'product_id': product_mapping[row['product_name']],
                'production_volume': row['production_volume'],
                'sales_volume': None,
                'sales_amount': None,
                'inventory_level': None,
                'average_price': None
            })

    # Process sales data
    print(f"Sales data columns: {list(df_sales.columns)}")
    for _, row in df_sales.iterrows():
        if row['product_name'] in product_mapping:
            daily_metrics_data.append({
                'record_date': row['record_date'],
                'product_id': product_mapping[row['product_name']],
                'production_volume': None,
                'sales_volume': row['sales_volume'],
                'sales_amount': row.get('sales_amount', row.get('tax_free_amount', 0) * 1.09),
                'inventory_level': None,
                'average_price': row['average_price']
            })

    print(f"Prepared {len(daily_metrics_data)} daily metrics records")

    # Group by date and product_id to combine data
    from collections import defaultdict
    combined_data = defaultdict(lambda: {
        'production_volume': 0,
        'sales_volume': 0,
        'sales_amount': 0,
        'inventory_level': None,
        'average_price': None
    })

    for record in daily_metrics_data:
        key = (record['record_date'], record['product_id'])

        if record.get('production_volume') is not None:
            combined_data[key]['production_volume'] += record['production_volume']
        if record.get('sales_volume') is not None:
            combined_data[key]['sales_volume'] += record['sales_volume']
        if record.get('sales_amount') is not None:
            combined_data[key]['sales_amount'] += record['sales_amount']
        if record.get('inventory_level') is not None:
            combined_data[key]['inventory_level'] = record['inventory_level']
        if record.get('average_price') is not None:
            combined_data[key]['average_price'] = record['average_price']

    # Insert combined data
    insert_count = 0
    for (record_date, product_id), data in combined_data.items():
        cursor.execute("""
            INSERT INTO DailyMetrics
            (record_date, product_id, production_volume, sales_volume, sales_amount, inventory_level, average_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record_date,
            product_id,
            data['production_volume'] if data['production_volume'] > 0 else None,
            data['sales_volume'] if data['sales_volume'] > 0 else None,
            data['sales_amount'] if data['sales_amount'] > 0 else None,
            data['inventory_level'],
            data['average_price']
        ))
        insert_count += 1

    conn.commit()
    conn.close()

    print(f"Successfully inserted {insert_count} daily metrics records")
    print("Real data import completed!")

    # Verify data
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM DailyMetrics")
    total_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT product_id) FROM DailyMetrics")
    unique_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT record_date) FROM DailyMetrics")
    unique_dates = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(record_date), MAX(record_date) FROM DailyMetrics")
    date_range = cursor.fetchone()

    conn.close()

    print(f"\n--- Data Verification ---")
    print(f"Total DailyMetrics records: {total_records}")
    print(f"Unique products: {unique_products}")
    print(f"Unique dates: {unique_dates}")
    print(f"Date range: {date_range[0]} to {date_range[1]}")

    print("\n--- Import Complete ---")
    print("Real production data has been successfully imported!")
    print("You can now test the frontend to verify real data is displaying correctly.")

except Exception as e:
    print(f"Error with database operations: {e}")
    if conn:
        conn.close()
    exit(1)
