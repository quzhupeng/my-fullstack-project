import pandas as pd
import sqlite3
import numpy as np
from sqlalchemy import create_engine
import os

def inspect_excel_files():
    """
    检查Excel文件的列结构，帮助诊断数据导入问题
    """
    excel_files = {
        'inbound': 'Excel文件夹/产成品入库列表.xlsx',
        'summary': 'Excel文件夹/收发存汇总表查询.xlsx',
        'sales': 'Excel文件夹/销售发票执行查询.xlsx',
    }

    for file_type, file_path in excel_files.items():
        if os.path.exists(file_path):
            print(f"\n=== {file_type.upper()} FILE: {file_path} ===")
            try:
                df = pd.read_excel(file_path, sheet_name=0)
                print(f"Shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                print(f"First few rows:")
                print(df.head(3))
                print(f"Data types:")
                print(df.dtypes)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")
    print("\n" + "="*80)

# --- 配置 ---
# 请替换为您的Excel文件路径，确保这些文件在 'Excel文件夹' 内
EXCEL_FILES = {
    'inbound': 'Excel文件夹/产成品入库列表.xlsx',
    'summary': 'Excel文件夹/收发存汇总表查询.xlsx',
    'sales': 'Excel文件夹/销售发票执行查询.xlsx',
    # 如果有其他Excel文件，也可以在这里添加
}
DB_NAME = 'temp_db.sqlite'                 # 临时SQLite数据库文件名
SQL_OUTPUT_FILE = 'import_data.sql'        # 最终生成的SQL文件名
DB_TABLE_PRODUCTS = 'Products'
DB_TABLE_METRICS = 'DailyMetrics'

def apply_inventory_data_filters(inventory_df):
    """
    应用库存数据过滤逻辑，参考原始Python脚本中的data_loader.py
    """
    if inventory_df.empty:
        return inventory_df

    print(f"  📊 Applying inventory data filters (original shape: {inventory_df.shape})")

    # 删除全空行和品名为空的行
    inventory_df = inventory_df.dropna(how='all')
    inventory_df = inventory_df[inventory_df['物料名称'].notna() & (inventory_df['物料名称'] != '')]

    # 在过滤前保存所有"凤肠"产品记录，以便后续添加回来
    feng_chang_products = inventory_df[inventory_df['物料名称'].astype(str).str.contains('凤肠', case=False, na=False)].copy()
    if not feng_chang_products.empty:
        print(f"  🔍 Found {len(feng_chang_products)} 凤肠 products, will preserve after filtering")

    # 过滤掉客户为"副产品"、"鲜品"或空白的记录
    if '客户' in inventory_df.columns:
        original_count = len(inventory_df)
        inventory_df['客户'] = inventory_df['客户'].astype(str).str.strip()
        excluded_customers = ['副产品', '鲜品', '']
        mask = ~inventory_df['客户'].isin(excluded_customers)
        inventory_df = inventory_df[mask]
        print(f"  🚫 Excluded customers (副产品, 鲜品, empty): {original_count} → {len(inventory_df)} records")

    # 根据"物料分类名称"列进行筛选
    material_category_col = '物料分类名称'
    if material_category_col in inventory_df.columns:
        excluded_categories = ['副产品', '生鲜品其他']
        inventory_df[material_category_col] = inventory_df[material_category_col].replace(r'^\s*$', np.nan, regex=True)

        mask = ~(
            inventory_df[material_category_col].isin(excluded_categories) |
            inventory_df[material_category_col].isna()
        )
        original_count = len(inventory_df)
        inventory_df = inventory_df[mask]
        print(f"  🚫 Excluded material categories (副产品, 生鲜品其他, empty): {original_count} → {len(inventory_df)} records")

    # 排除物料名称含"鲜"字的记录
    original_count = len(inventory_df)
    inventory_df = inventory_df[~inventory_df['物料名称'].astype(str).str.contains('鲜', case=False, na=False)]
    print(f"  🚫 Excluded products containing '鲜': {original_count} → {len(inventory_df)} records")

    # 特殊处理：将"凤肠"产品添加回来
    if not feng_chang_products.empty:
        feng_chang_to_add = feng_chang_products[~feng_chang_products['物料名称'].isin(inventory_df['物料名称'])]
        if not feng_chang_to_add.empty:
            inventory_df = pd.concat([inventory_df, feng_chang_to_add], ignore_index=True)
            print(f"  ✅ Re-added {len(feng_chang_to_add)} 凤肠 products back to inventory data")

    print(f"  ✅ Inventory filtering complete: final shape {inventory_df.shape}")
    return inventory_df

def apply_production_data_filters(production_df):
    """
    应用生产数据过滤逻辑，参考原始Python脚本中的data_loader.py
    """
    if production_df.empty:
        return production_df

    print(f"  📊 Applying production data filters (original shape: {production_df.shape})")

    # 删除全空行
    production_df = production_df.dropna(how='all')

    # 数据清洗：去除物料名称中含"鲜"字的行
    if 'product_name' in production_df.columns:
        original_count = len(production_df)
        production_df = production_df[~production_df['product_name'].astype(str).str.contains('鲜', case=False, na=False)]
        print(f"  🚫 Excluded products containing '鲜': {original_count} → {len(production_df)} records")

    print(f"  ✅ Production filtering complete: final shape {production_df.shape}")
    return production_df

def apply_sales_data_filters(sales_df):
    """
    应用销售数据过滤逻辑，参考原始Python脚本中的data_loader.py
    """
    if sales_df.empty:
        return sales_df

    print(f"  📊 Applying sales data filters (original shape: {sales_df.shape})")

    # 清洗条件 1: 物料分类列，去除"副产品"、"空白"的行
    material_category_column = '物料分类'
    if material_category_column in sales_df.columns:
        original_count = len(sales_df)
        sales_df[material_category_column] = sales_df[material_category_column].replace(r'^\s*$', np.nan, regex=True)
        sales_df = sales_df[
            (~sales_df[material_category_column].astype(str).str.lower().isin(['副产品', 'nan', '']))
        ]
        print(f"  🚫 Excluded material categories (副产品, empty): {original_count} → {len(sales_df)} records")

    # 清洗条件 2: 客户名称列，排除客户名称为空、"副产品"或"鲜品"的记录
    customer_name_column = '客户名称'
    if customer_name_column in sales_df.columns:
        original_count = len(sales_df)
        sales_df[customer_name_column] = sales_df[customer_name_column].fillna('').astype(str).str.strip()
        excluded_customer_names_lower = ['', '副产品'.lower(), '鲜品'.lower()]
        sales_df = sales_df[~sales_df[customer_name_column].str.lower().isin(excluded_customer_names_lower)]
        print(f"  🚫 Excluded customers (empty, 副产品, 鲜品): {original_count} → {len(sales_df)} records")

    # 清洗条件 3: 物料名称列，删除其中包含"鲜"的记录
    if 'product_name' in sales_df.columns:
        original_count = len(sales_df)
        sales_df = sales_df[
            ~sales_df['product_name'].astype(str).str.contains('鲜', case=False, na=False)
        ]
        print(f"  🚫 Excluded products containing '鲜': {original_count} → {len(sales_df)} records")

    print(f"  ✅ Sales filtering complete: final shape {sales_df.shape}")
    return sales_df

def clean_and_load_excel(file_path, file_type, sheet_name=0):
    """
    读取Excel文件并进行初步清洗。
    此函数根据文件类型调整列名，并将日期转换为YYYY-MM-DD格式。
    实现与原始Python脚本相同的数据过滤逻辑。
    """
    print(f"Reading data from {file_path}...")
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    print(f"  Original shape: {df.shape}")
    print(f"  Available columns: {list(df.columns)}")

    # 根据文件类型重命名列
    if file_type == 'inbound':
        df.rename(columns={'单据日期': 'record_date', '物料名称': 'product_name', '主数量': 'production_volume'}, inplace=True)
        print(f"  Mapped columns: record_date, product_name, production_volume")

        # 修复：将产量从公斤(kg)转换为吨(t)
        if 'production_volume' in df.columns:
            df['production_volume'] = df['production_volume'] / 1000

        # 应用生产数据过滤逻辑（参考原始Python脚本）
        df = apply_production_data_filters(df)

    elif file_type == 'summary':
        # 应用库存数据过滤逻辑（参考原始Python脚本）
        df = apply_inventory_data_filters(df)

        df.rename(columns={'物料名称': 'product_name', '结存': 'inventory_level'}, inplace=True)
        print(f"  Mapped columns: product_name, inventory_level")

        # 库存数据作为期初库存，不需要扩展日期
        # 假设 '收发存汇总表查询.xlsx' 提供的是计算周期开始前一天的期末库存
        # 例如，如果数据从6月1日开始，这里应该是5月31日的库存
        # 我们将在主逻辑中处理它，这里只做重命名
        print("  ℹ️ Summary data will be used as starting inventory.")

    elif file_type == 'sales':
        # 应用销售数据过滤逻辑（参考原始Python脚本）
        df = apply_sales_data_filters(df)

        # 检查实际的价格列名
        price_columns = [col for col in df.columns if '单价' in col or '价格' in col]
        print(f"  Available price columns: {price_columns}")

        # 尝试多种价格列映射
        if '本币含税单价' in df.columns:
            df.rename(columns={'发票日期': 'record_date', '物料名称': 'product_name', '主数量': 'sales_volume', '本币含税单价': 'average_price'}, inplace=True)
            print(f"  Using '本币含税单价' for price data")
        elif '含税单价' in df.columns:
            df.rename(columns={'发票日期': 'record_date', '物料名称': 'product_name', '主数量': 'sales_volume', '含税单价': 'average_price'}, inplace=True)
            print(f"  Using '含税单价' for price data")
        elif '本币无税单价' in df.columns and '本币无税金额' in df.columns:
            # 计算含税价格: (无税金额 / 主数量) * 1.09
            df.rename(columns={'发票日期': 'record_date', '物料名称': 'product_name', '主数量': 'sales_volume'}, inplace=True)
            # 修复：价格单位从 元/公斤 转换为 元/吨
            df['average_price'] = (df['本币无税金额'] / df['sales_volume']) * 1.09 * 1000
            print(f"  Calculated price from (无税金额/主数量*1.09*1000) to get price in Yuan/Ton")
        else:
            df.rename(columns={'发票日期': 'record_date', '物料名称': 'product_name', '主数量': 'sales_volume'}, inplace=True)
            df['average_price'] = 0
            print(f"  ⚠️  No suitable price column found, using 0")

    # 确保日期格式统一为 'YYYY-MM-DD'
    if 'record_date' in df.columns:
        # Convert to datetime, coercing errors to NaT
        df['record_date'] = pd.to_datetime(df['record_date'], errors='coerce')
        # Drop rows where record_date is NaT (invalid date)
        before_count = len(df)
        df.dropna(subset=['record_date'], inplace=True)
        after_count = len(df)
        if before_count != after_count:
            print(f"  Dropped {before_count - after_count} rows with invalid dates")
        # Format to string
        df['record_date'] = df['record_date'].dt.strftime('%Y-%m-%d')
    else:
        print(f"  ⚠️  Warning: No 'record_date' column found after renaming for {file_type} file.")

    # 确保产品名称列存在并处理可能的商品名称别名
    if 'product_name' not in df.columns and '商品名称' in df.columns:
        df.rename(columns={'商品名称': 'product_name'}, inplace=True)

    # 对所有关键数值列进行非数值处理（例如，将 NaN 替换为 0）
    numeric_cols = [
        'production_volume', 'sales_volume', 'inventory_level', 'average_price'
    ]
    for col in numeric_cols:
        if col in df.columns:
            before_conversion = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            after_conversion = (df[col] == 0).sum()
            print(f"  Column '{col}': {before_conversion} NaN values, {after_conversion} zero values after conversion")

    # --- 单位转换 ---
    # 修复：将销量和产量从公斤(kg)转换为吨(t)
    if 'sales_volume' in df.columns:
        print("  🔧 CONVERTING: sales_volume from KG to Tons")
        df['sales_volume'] = df['sales_volume'] / 1000
    if 'production_volume' in df.columns:
        print("  🔧 CONVERTING: production_volume from KG to Tons")
        df['production_volume'] = df['production_volume'] / 1000

    print(f"  Final shape: {df.shape}")
    return df

def calculate_inventory_turnover(df):
    """
    计算每个产品的每日库存周转天数。
    公式：库存周转天数 = 当日结存库存 / 过去30天日均销售量
    """
    print("  🔄 Calculating inventory turnover days...")
    if df.empty or 'sales_volume' not in df.columns or 'inventory_level' not in df.columns:
        print("  ⚠️ Not enough data to calculate turnover days. Skipping.")
        df['inventory_turnover_days'] = 0
        return df

    # 确保数据按产品和日期排序
    # 如果 record_date 不是 datetime 类型，先转换
    if not pd.api.types.is_datetime64_any_dtype(df['record_date']):
        df['record_date'] = pd.to_datetime(df['record_date'])
    
    df.sort_values(by=['product_id', 'record_date'], inplace=True)

    # 计算过去30天的日均销售量
    # 使用 rolling(window=30, min_periods=1) 来处理数据开始时不足30天的情况
    df['avg_sales_30d'] = df.groupby('product_id')['sales_volume'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )

    # 计算库存周转天数
    # 处理日均销量为0的情况，避免除以零
    df['inventory_turnover_days'] = df['inventory_level'] / df['avg_sales_30d']
    
    # 将无穷大（由于除以零产生）和NaN值替换为0
    df['inventory_turnover_days'].replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna({'inventory_turnover_days': 0}, inplace=True)

    print(f"  ✅ Calculated inventory turnover days.")
    
    # 删除临时列
    df.drop(columns=['avg_sales_30d'], inplace=True)
    
    return df

def main():
    # --- 1. 读取并合并所有Excel数据 ---
    all_data_frames = {}
    for key, path in EXCEL_FILES.items():
        all_data_frames[key] = clean_and_load_excel(path, key)

    # 首先，从所有数据中提取唯一的产品名称
    unique_products = set()
    for df_key, df in all_data_frames.items():
        if 'product_name' in df.columns:
            unique_products.update(df['product_name'].unique())

    # 创建一个临时的内存SQLite数据库连接
    engine = create_engine(f'sqlite:///{DB_NAME}')
    conn = engine.connect()

    # --- 2. 提取并插入唯一的产品信息到 Products 表 ---
    print("Extracting unique products...")
    products_df = pd.DataFrame(list(unique_products), columns=['product_name'])
    # 手动分配 product_id，从1开始
    products_df['product_id'] = products_df.index + 1
    
    products_df.to_sql(DB_TABLE_PRODUCTS, conn, if_exists='replace', index=False)
    print(f"{len(products_df)} unique products written to '{DB_TABLE_PRODUCTS}' table.")

    # 直接从 products_df 创建映射，因为 product_id 已经明确分配
    product_name_to_id = products_df.set_index('product_name')['product_id'].to_dict()

    # --- 3. 准备每日指标数据并关联产品ID ---
    print("Preparing daily metrics data using a production-centric merge strategy...")

    # 1. 聚合生产数据 (inbound)
    inbound_df = all_data_frames.get('inbound')
    if inbound_df is not None and not inbound_df.empty:
        production_daily = inbound_df.groupby(['record_date', 'product_name'])['production_volume'].sum().reset_index()
        print(f"  Aggregated production data: {production_daily.shape[0]} records")
    else:
        production_daily = pd.DataFrame(columns=['record_date', 'product_name', 'production_volume'])
        print("  No production data found.")

    # 2. 聚合销售数据 (sales)
    sales_df = all_data_frames.get('sales')
    if sales_df is not None and not sales_df.empty:
        # 计算加权平均价格所需的总金额
        sales_df['total_amount'] = sales_df['sales_volume'] * sales_df['average_price']
        sales_daily = sales_df.groupby(['record_date', 'product_name']).agg(
            sales_volume=('sales_volume', 'sum'),
            total_amount=('total_amount', 'sum')
        ).reset_index()
        # 计算最终的加权平均价格
        sales_daily['average_price'] = sales_daily['total_amount'] / sales_daily['sales_volume']
        sales_daily.drop(columns=['total_amount'], inplace=True)
        print(f"  Aggregated sales data: {sales_daily.shape[0]} records")
    else:
        sales_daily = pd.DataFrame(columns=['record_date', 'product_name', 'sales_volume', 'average_price'])
        print("  No sales data found.")

    # 3. 以生产数据为核心，合并销售数据
    # 使用 outer join 保留所有有生产或销售的记录，后续再根据生产记录进行过滤
    merged_df = pd.merge(
        production_daily,
        sales_daily,
        on=['record_date', 'product_name'],
        how='outer'
    )
    print(f"  Merged production and sales data (outer join): {merged_df.shape[0]} records")

    # 关键修复：只保留有生产记录的数据行
    # 过滤掉 production_volume 为 NaN 或 0 的情况
    final_metrics_df = merged_df[merged_df['production_volume'].notna() & (merged_df['production_volume'] > 0)].copy()
    print(f"  Filtered for production records only: {final_metrics_df.shape[0]} records remain")

    # 4. 实现动态库存计算
    print("  🔄 Implementing dynamic inventory calculation...")
    summary_df = all_data_frames.get('summary')
    
    # 准备期初库存 (前一天的结存)
    # 将 'inventory_level' 从公斤转换为吨
    if summary_df is not None and not summary_df.empty:
        summary_df['inventory_level'] = summary_df['inventory_level'] / 1000
        initial_inventory = summary_df.set_index('product_name')['inventory_level'].to_dict()
        print(f"  Loaded {len(initial_inventory)} initial inventory records (converted to tons).")
    else:
        initial_inventory = {}
        print("  ⚠️ No summary data found, starting with zero inventory.")

    # 确保 'record_date' 是 datetime 类型，以便排序
    final_metrics_df['record_date'] = pd.to_datetime(final_metrics_df['record_date'])
    final_metrics_df.sort_values(by=['product_name', 'record_date'], inplace=True)

    # 填充NaN值为0，以便计算
    final_metrics_df.fillna({'production_volume': 0, 'sales_volume': 0}, inplace=True)

    # 按产品逐日计算库存
    calculated_inventory = []
    # 使用 .groupby('product_name') 确保我们按产品处理数据
    for product_name, group in final_metrics_df.groupby('product_name'):
        # 获取该产品的期初库存，如果不存在则为0
        last_day_inventory = initial_inventory.get(product_name, 0)
        
        # 迭代该产品的每一天记录
        for index, row in group.iterrows():
            # 当日库存 = 昨日库存 + 当日生产 - 当日销售
            current_inventory = last_day_inventory + row['production_volume'] - row['sales_volume']
            calculated_inventory.append({
                'record_date': row['record_date'],
                'product_name': product_name,
                'inventory_level': current_inventory
            })
            # 更新昨日库存为今日库存，为下一天做准备
            last_day_inventory = current_inventory

    # 将计算出的库存转换为DataFrame
    if calculated_inventory:
        inventory_df = pd.DataFrame(calculated_inventory)
        print(f"  ✅ Calculated {len(inventory_df)} dynamic inventory records.")
        # 将计算出的库存合并回主DataFrame
        final_metrics_df = pd.merge(
            final_metrics_df,
            inventory_df,
            on=['record_date', 'product_name'],
            how='left'
        )
        print(f"  Merged dynamic inventory data: {final_metrics_df.shape[0]} records")
    else:
        final_metrics_df['inventory_level'] = 0
        print("  No inventory calculated, setting inventory_level to 0.")


    # 5. 关联产品ID并填充缺失值
    final_metrics_df['product_id'] = final_metrics_df['product_name'].map(product_name_to_id)
    
    # 填充NaN值为0
    fill_values = {
        'sales_volume': 0,
        'inventory_level': 0,
        'average_price': 0,
        'production_volume': 0
    }
    final_metrics_df.fillna(fill_values, inplace=True)

    # 6. 计算库存周转天数
    final_metrics_df = calculate_inventory_turnover(final_metrics_df)
    
    # 将 record_date 转回字符串格式以便写入SQL
    if pd.api.types.is_datetime64_any_dtype(final_metrics_df['record_date']):
        final_metrics_df['record_date'] = final_metrics_df['record_date'].dt.strftime('%Y-%m-%d')

    # 筛选并重排最终列
    final_metrics_df = final_metrics_df[[
        'record_date', 'product_id', 'production_volume',
        'sales_volume', 'inventory_level', 'average_price',
        'inventory_turnover_days'
    ]]
    
    print(f"  Created {len(final_metrics_df)} final data records for DailyMetrics table.")

    # --- 4. 从临时数据库导出为.sql文件 ---
    print(f"Dumping database to {SQL_OUTPUT_FILE}...")
    with open(SQL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # 添加 schema.sql 的内容到导入脚本中，以确保表结构存在
        with open('backend/schema.sql', 'r', encoding='utf-8') as schema_f:
            f.write(schema_f.read())
            f.write('\n\n') # 添加空行分隔

        # Manually construct and write Products inserts with correct column order
        for index, row in products_df.iterrows():
            sql_values = (
                f"{row['product_id']},"
                f"'{row['product_name']}',"
                f"NULL,"  # sku
                f"NULL"   # category
            )
            f.write(f'INSERT INTO "Products" (product_id, product_name, sku, category) VALUES ({sql_values});\n')
        f.write('\n') # Add a newline after products inserts
        print(f"{len(products_df)} products written to SQL file.")

        # Manually construct and write DailyMetrics inserts
        if not final_metrics_df.empty:
            for index, row in final_metrics_df.iterrows():
                sql_values = (
                    f"'{row['record_date']}',"
                    f"{row['product_id']},"
                    f"{row['production_volume']},"
                    f"{row['sales_volume']},"
                    f"{row['inventory_level']},"
                    f"{row['average_price']},"
                    f"{row['inventory_turnover_days']}"
                )
                f.write(f'INSERT INTO "DailyMetrics" (record_date, product_id, production_volume, sales_volume, inventory_level, average_price, inventory_turnover_days) VALUES ({sql_values});\n')
            print(f"{len(final_metrics_df)} records written to '{DB_TABLE_METRICS}' table in SQL file.")
        else:
            print("No metrics data to write to SQL file.")


    print("SQL file generated successfully.")

    # --- 5. 清理临时数据库文件 ---
    conn.close()
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Temporary database file '{DB_NAME}' removed.")

    print("Process complete. You can now use wrangler to execute the .sql file:")
    print(f"npx wrangler d1 execute <YOUR_DB_NAME> --remote --file=./{SQL_OUTPUT_FILE}")

if __name__ == "__main__":
    # First inspect the Excel files to understand their structure
    print("🔍 INSPECTING EXCEL FILES...")
    inspect_excel_files()

    # Ask user if they want to proceed with import
    proceed = input("\n📋 Do you want to proceed with data import? (y/n): ").lower().strip()
    if proceed == 'y':
        main()
    else:
        print("Import cancelled.")
