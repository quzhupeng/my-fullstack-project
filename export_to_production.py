#!/usr/bin/env python3
"""
Export corrected data from local D1 database to production environment
This script exports the fixed unit conversion data to SQL format for production deployment
"""

import sqlite3
import os
import subprocess

# Configuration
LOCAL_DB_PATH = 'backend/.wrangler/state/v3/d1/chunxue-prod-db.sqlite'
EXPORT_SQL_FILE = 'production_data_export.sql'
REMOTE_DB_NAME = 'chunxue-prod-db'

def export_data_to_sql():
    """Export corrected data from local database to SQL file"""
    print("--- Exporting Corrected Data to Production ---")
    
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"Error: Local database not found at {LOCAL_DB_PATH}")
        return False
    
    # Connect to local database
    conn = sqlite3.connect(LOCAL_DB_PATH)
    cursor = conn.cursor()
    
    # Check data availability
    cursor.execute("SELECT COUNT(*) FROM DailyMetrics")
    total_records = cursor.fetchone()[0]
    print(f"Found {total_records} records in local database")
    
    if total_records == 0:
        print("No data to export!")
        conn.close()
        return False
    
    # Create SQL export file
    with open(EXPORT_SQL_FILE, 'w', encoding='utf-8') as f:
        f.write("-- Spring Snow Food Analysis System - Corrected Data Export\n")
        f.write("-- Generated with fixed unit conversions (KG -> Tons)\n")
        f.write(f"-- Total records: {total_records}\n\n")
        
        # Export Products table
        f.write("-- Products Data --\n")
        cursor.execute("SELECT product_id, product_name, sku, category FROM Products ORDER BY product_id")
        products = cursor.fetchall()
        
        for product in products:
            product_id, product_name, sku, category = product
            # Escape single quotes in product names
            safe_name = product_name.replace("'", "''") if product_name else ''
            safe_sku = sku.replace("'", "''") if sku else 'NULL'
            safe_category = category.replace("'", "''") if category else 'NULL'
            
            if sku is None:
                safe_sku = 'NULL'
            else:
                safe_sku = f"'{safe_sku}'"
                
            if category is None:
                safe_category = 'NULL'
            else:
                safe_category = f"'{safe_category}'"
            
            f.write(f"INSERT OR REPLACE INTO Products (product_id, product_name, sku, category) VALUES ({product_id}, '{safe_name}', {safe_sku}, {safe_category});\n")
        
        f.write(f"\n-- Inserted {len(products)} products\n\n")
        
        # Export DailyMetrics data in batches
        f.write("-- DailyMetrics Data (Corrected Units) --\n")
        cursor.execute("""
            SELECT record_date, product_id, production_volume, sales_volume, 
                   sales_amount, inventory_level, average_price 
            FROM DailyMetrics 
            ORDER BY record_date, product_id
        """)
        
        batch_size = 1000
        batch_count = 0
        
        while True:
            records = cursor.fetchmany(batch_size)
            if not records:
                break
                
            batch_count += 1
            f.write(f"-- Batch {batch_count} --\n")
            
            for record in records:
                record_date, product_id, production_volume, sales_volume, sales_amount, inventory_level, average_price = record
                
                # Handle NULL values
                prod_vol = production_volume if production_volume is not None else 'NULL'
                sales_vol = sales_volume if sales_volume is not None else 'NULL'
                sales_amt = sales_amount if sales_amount is not None else 'NULL'
                inv_level = inventory_level if inventory_level is not None else 'NULL'
                avg_price = average_price if average_price is not None else 'NULL'
                
                f.write(f"INSERT INTO DailyMetrics (record_date, product_id, production_volume, sales_volume, sales_amount, inventory_level, average_price) VALUES ('{record_date}', {product_id}, {prod_vol}, {sales_vol}, {sales_amt}, {inv_level}, {avg_price});\n")
    
    conn.close()
    print(f"Data exported to {EXPORT_SQL_FILE}")
    return True

def deploy_to_production():
    """Deploy the exported data to production D1 database"""
    print("--- Deploying to Production D1 Database ---")
    
    if not os.path.exists(EXPORT_SQL_FILE):
        print(f"Error: Export file {EXPORT_SQL_FILE} not found")
        return False
    
    try:
        # Execute the SQL file on remote D1 database
        # Need to provide absolute path to SQL file
        abs_sql_path = os.path.abspath(EXPORT_SQL_FILE)

        cmd = [
            'npx', 'wrangler', 'd1', 'execute', REMOTE_DB_NAME,
            '--remote', '--file', abs_sql_path
        ]

        print(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd='backend', capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Data successfully deployed to production!")
            print(result.stdout)
            return True
        else:
            print("❌ Deployment failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"Error during deployment: {e}")
        return False

def verify_production_data():
    """Verify the deployed data in production"""
    print("--- Verifying Production Data ---")
    
    try:
        # Check total records
        cmd = [
            'npx', 'wrangler', 'd1', 'execute', REMOTE_DB_NAME,
            '--remote', '--command', 
            'SELECT COUNT(*) as total_records FROM DailyMetrics;'
        ]
        
        result = subprocess.run(cmd, cwd='backend', capture_output=True, text=True)
        if result.returncode == 0:
            print("Total records in production:")
            print(result.stdout)
        
        # Check sample sales data (should show corrected units)
        cmd = [
            'npx', 'wrangler', 'd1', 'execute', REMOTE_DB_NAME,
            '--remote', '--command',
            'SELECT record_date, SUM(sales_volume) as total_sales_tons FROM DailyMetrics WHERE sales_volume IS NOT NULL GROUP BY record_date ORDER BY record_date LIMIT 5;'
        ]
        
        result = subprocess.run(cmd, cwd='backend', capture_output=True, text=True)
        if result.returncode == 0:
            print("Sample daily sales data (should be in hundreds of tons):")
            print(result.stdout)
            
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

def main():
    """Main execution function"""
    print("🚀 Spring Snow Food Analysis System - Production Data Deployment")
    print("This script deploys corrected unit conversion data to production\n")
    
    # Step 1: Export data from local database
    if not export_data_to_sql():
        print("❌ Data export failed!")
        return
    
    # Step 2: Deploy to production
    if not deploy_to_production():
        print("❌ Production deployment failed!")
        return
    
    # Step 3: Verify deployment
    if not verify_production_data():
        print("⚠️  Verification failed, but deployment may have succeeded")
    
    print("\n✅ Production deployment completed!")
    print("🌐 Frontend URL: https://my-fullstack-project.pages.dev/")
    print("📊 Please verify the frontend displays corrected data (sales in hundreds of tons)")

if __name__ == "__main__":
    main()
