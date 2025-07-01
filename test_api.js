const http = require('http');

function testAPI() {
    const options = {
        hostname: 'localhost',
        port: 8787,
        path: '/api/trends/sales-price?start_date=2025-06-01&end_date=2025-06-05',
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    };

    const req = http.request(options, (res) => {
        console.log(`Status: ${res.statusCode}`);
        console.log(`Headers:`, res.headers);

        let data = '';
        res.on('data', (chunk) => {
            data += chunk;
        });

        res.on('end', () => {
            try {
                const jsonData = JSON.parse(data);
                console.log('\n=== API Response ===');
                console.log(JSON.stringify(jsonData, null, 2));
                
                console.log('\n=== Data Validation ===');
                if (Array.isArray(jsonData) && jsonData.length > 0) {
                    jsonData.forEach((item, index) => {
                        console.log(`Record ${index + 1}:`);
                        console.log(`  Date: ${item.record_date}`);
                        console.log(`  Sales Volume: ${item.total_sales} (type: ${typeof item.total_sales})`);
                        console.log(`  Sales Amount: ${item.total_amount} (type: ${typeof item.total_amount})`);
                        console.log(`  Avg Price: ${item.avg_price} (type: ${typeof item.avg_price})`);
                        
                        // Check for null/undefined values
                        const hasNulls = [item.total_sales, item.total_amount, item.avg_price].some(val => val === null || val === undefined);
                        console.log(`  Has null values: ${hasNulls}`);
                        console.log('');
                    });
                } else {
                    console.log('No data returned or invalid format');
                }
            } catch (error) {
                console.error('Failed to parse JSON:', error);
                console.log('Raw response:', data);
            }
        });
    });

    req.on('error', (error) => {
        console.error('Request error:', error);
    });

    req.end();
}

console.log('Testing Sales Price API...');
testAPI();
