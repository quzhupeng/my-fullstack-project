import requests
import sqlite3
import json

# Configuration
LOCAL_DB = 'backend/.wrangler/state/v3/d1/chunxue-prod-db.sqlite'
REMOTE_API = 'https://backend.qu18354531302.workers.dev'

def get_local_data():
    """Get data from local database"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    
    # Get DailyMetrics data
    cursor.execute("""
        SELECT record_date, product_id, production_volume, sales_volume, 
               inventory_level, average_price, sales_amount
        FROM DailyMetrics
        ORDER BY record_date, product_id
    """)
    
    daily_metrics = []
    for row in cursor.fetchall():
        daily_metrics.append({
            'record_date': row[0],
            'product_id': row[1],
            'production_volume': row[2],
            'sales_volume': row[3],
            'inventory_level': row[4],
            'average_price': row[5],
            'sales_amount': row[6]
        })
    
    conn.close()
    return daily_metrics

def upload_batch(batch_data):
    """Upload a batch of data to remote API"""
    try:
        response = requests.post(
            f'{REMOTE_API}/api/admin/import-batch',
            json={'data': batch_data},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def main():
    print("Starting remote data import...")
    
    # Get local data
    print("Reading local database...")
    daily_metrics = get_local_data()
    print(f"Found {len(daily_metrics)} records to import")
    
    # Upload in batches
    batch_size = 100
    total_batches = (len(daily_metrics) + batch_size - 1) // batch_size
    
    for i in range(0, len(daily_metrics), batch_size):
        batch = daily_metrics[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} records)...")
        
        success, result = upload_batch(batch)
        if success:
            print(f"✅ Batch {batch_num} uploaded successfully")
        else:
            print(f"❌ Batch {batch_num} failed: {result}")
            break
    
    print("Remote import completed!")

if __name__ == "__main__":
    main()
