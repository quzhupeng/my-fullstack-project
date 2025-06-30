import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import numpy as np

# --- Configuration ---
EXCEL_FOLDER = './Excel文件夹/'
DB_NAME = 'backend/.wrangler/state/v3/d1/chunxue-prod-db.sqlite'
SQL_OUTPUT_FILE = 'import_data.sql'

# File paths
inv_summary_path = os.path.join(EXCEL_FOLDER, '收发存汇总表查询.xlsx')
production_path = os.path.join(EXCEL_FOLDER, '产成品入库列表.xlsx')
sales_path = os.path.join(EXCEL_FOLDER, '销售发票执行查询.xlsx')
price_path = os.path.join(EXCEL_FOLDER, '综合售价6.23.xlsx')

print("--- Starting Real Data Import Script ---")

# --- 1. Load Data using Pandas ---
print(f"Loading data from: {EXCEL_FOLDER}")

# Inventory Summary: Main source for product list and inventory levels
df_inv = pd.read_excel(inv_summary_path, sheet_name='收发存汇总表查询')
# Production Data
df_prod = pd.read_excel(production_path, sheet_name='产成品入库列表')
# Sales Data
df_sales = pd.read_excel(sales_path, sheet_name='销售发票执行查询')

print("All Excel files loaded successfully.")

# --- 2. Data Cleaning and Preparation ---
print("Cleaning and preparing data...")

def process_price_data(df_price):
    # The relevant data starts from the third row
    df_price = df_price.iloc[2:].copy()
    
    # Rename the columns based on their position/name in the Excel file
    df_price.rename(columns={
        'Unnamed: 0': 'record_date_str',
        'Unnamed: 1': 'product_name',
        'Unnamed: 2': 'average_price'
    }, inplace=True)
    
    # Convert date column, coercing errors to NaT
    df_price['record_date'] = pd.to_datetime(df_price['record_date_str'], errors='coerce')
    
    # Forward-fill the valid dates
    df_price['record_date'].ffill(inplace=True)
    
    # Drop rows that couldn't be assigned a date
    df_price.dropna(subset=['record_date'], inplace=True)

    # Format the date to 'YYYY-MM-DD'
    df_price['record_date'] = df_price['record_date'].dt.strftime('%Y-%m-%d')

    # Drop rows with no product name
    df_price.dropna(subset=['product_name'], inplace=True)
    
    # Keep only the columns we need
    return df_price[['record_date', 'product_name', 'average_price']]

# Clean up column names
df_inv.rename(columns={'物料名称': 'product_name', '结存': 'inventory_level'}, inplace=True)
df_prod.rename(columns={'物料名称': 'product_name', '入库日期': 'record_date', '主数量': 'production_volume'}, inplace=True)
df_sales.rename(columns={'物料名称': 'product_name', '发票日期': 'record_date', '主数量': 'sales_volume'}, inplace=True)

# Process the price data
df_price_processed = process_price_data(df_price)

print("df_inv columns:", df_inv.columns)
print("df_prod columns:", df_prod.columns)
print("df_sales columns:", df_sales.columns)
print("df_price_processed columns:", df_price_processed.columns)

# Convert dates to 'YYYY-MM-DD' format
for df in [df_prod, df_sales, df_price_processed]:
    df['record_date'] = pd.to_datetime(df['record_date']).dt.strftime('%Y-%m-%d')

# --- 3. Create Products Table Data ---
print("Extracting unique products...")
all_products = pd.concat([
    df_inv['product_name'],
    df_prod['product_name'],
    df_sales['product_name'],
    df_price_processed['product_name']
]).unique()

products_df = pd.DataFrame(all_products, columns=['product_name'])
products_df.dropna(inplace=True)

# --- 4. Create DailyMetrics Table Data ---
print("Aggregating daily metrics...")

prod_agg = df_prod.groupby(['record_date', 'product_name'])['production_volume'].sum().reset_index()
sales_agg = df_sales.groupby(['record_date', 'product_name'])['sales_volume'].sum().reset_index()

# Merge production and sales data
metrics_df = pd.merge(prod_agg, sales_agg, on=['record_date', 'product_name'], how='outer')

# Merge price data - use outer merge to include all data points
metrics_df = pd.merge(metrics_df, df_price_processed, on=['record_date', 'product_name'], how='outer')

# --- Correct Inventory Handling ---
# Find the latest production date for each product from the production data
latest_prod_dates = df_prod.groupby('product_name')['record_date'].max().reset_index()

# Get the final inventory level for each product from the inventory summary
inv_summary = df_inv[['product_name', 'inventory_level']].dropna(subset=['product_name'])
inv_summary = inv_summary.drop_duplicates(subset='product_name', keep='last')

# Combine the inventory level with its correct date (the latest production date)
inventory_df = pd.merge(latest_prod_dates, inv_summary, on='product_name', how='left')

# Now, merge this dated inventory data into the main metrics dataframe
metrics_df = pd.merge(metrics_df, inventory_df[['record_date', 'product_name', 'inventory_level']], on=['record_date', 'product_name'], how='left')

# Clean up the merged data
metrics_df.fillna({
    'production_volume': 0,
    'sales_volume': 0,
    'inventory_level': 0,
    'average_price': 0
}, inplace=True)

# Drop any rows that might have been created from merges but have no product name
metrics_df.dropna(subset=['product_name'], inplace=True)

# Ensure integer columns are of integer type
metrics_df['production_volume'] = metrics_df['production_volume'].astype(int)
metrics_df['sales_volume'] = metrics_df['sales_volume'].astype(int)
metrics_df['inventory_level'] = metrics_df['inventory_level'].astype(int)


print(f"Aggregated {len(metrics_df)} daily metric records.")

# --- 5. Generate SQL File ---
print(f"Writing data to temporary database: {DB_NAME}")
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

engine = sqlite3.connect(DB_NAME)

# Write products to a temporary table
products_df.to_sql('Products_temp', engine, if_exists='replace', index=False)
# Get the products with their new auto-incremented IDs
products_with_id = pd.read_sql('SELECT row_number() OVER (ORDER BY product_name) as product_id, product_name FROM Products_temp', engine)

# Write the final products table with IDs
products_to_write = products_with_id[['product_id', 'product_name']]
products_to_write['sku'] = None
products_to_write['category'] = None
products_to_write.to_sql('Products', engine, if_exists='replace', index=False)
print(f"{len(products_with_id)} unique products written to 'Products' table.")

# Add product_id to the metrics dataframe
metrics_with_product_id = pd.merge(metrics_df, products_with_id, on='product_name', how='inner')

# Select and reorder columns to match the final DailyMetrics schema
final_metrics_df = metrics_with_product_id[[
    'record_date',
    'product_id',
    'production_volume',
    'sales_volume',
    'inventory_level',
    'average_price'
]]

# Write the final metrics table
final_metrics_df.to_sql('DailyMetrics', engine, if_exists='replace', index=False)
print(f"{len(final_metrics_df)} records written to 'DailyMetrics' table.")

print(f"Dumping database to {SQL_OUTPUT_FILE}...")
with open(SQL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
    # Dump the schema first (from the main schema.sql file)
    with open('./backend/schema.sql', 'r', encoding='utf-8') as schema_file:
        f.write(schema_file.read())
        f.write('\n')

    # Manually generate INSERT statements with explicit column names
    f.write("\n-- Inserting data into Products --\n")
    products_from_db = pd.read_sql('SELECT product_id, product_name, sku, category FROM Products', engine)
    for index, row in products_from_db.iterrows():
        f.write(f"INSERT INTO Products (product_id, product_name, sku, category) VALUES ({row['product_id']}, '{row['product_name'].replace("'", "''")}', NULL, NULL);\n")

    f.write("\n-- Inserting data into DailyMetrics --\n")
    metrics_from_db = pd.read_sql('SELECT record_date, product_id, production_volume, sales_volume, inventory_level, average_price FROM DailyMetrics', engine)
    for index, row in metrics_from_db.iterrows():
        f.write(f"INSERT INTO DailyMetrics (record_date, product_id, production_volume, sales_volume, inventory_level, average_price) VALUES ('{row['record_date']}', {row['product_id']}, {row['production_volume']}, {row['sales_volume']}, {row['inventory_level']}, {row['average_price']});\n")

engine.close()

print("--- Script Finished ---")
print(f"SQL file '{SQL_OUTPUT_FILE}' generated successfully.")
print(f"You can now run: wrangler d1 execute DB --local --file=./{SQL_OUTPUT_FILE}")
