// 后端API诊断脚本
// 用于检查销售情况和产销率分析页面的数据问题

const API_BASE_URL = 'https://backend.qu18354531302.workers.dev';

// 测试日期范围
const START_DATE = '2025-06-01';
const END_DATE = '2025-06-26';

async function testAPI(endpoint, description) {
    console.log(`\n🔍 测试 ${description}`);
    console.log(`📡 API: ${endpoint}`);
    
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (!response.ok) {
            console.log(`❌ HTTP错误: ${response.status}`);
            console.log(`📄 错误详情:`, data);
            return null;
        }
        
        console.log(`✅ 响应成功`);
        console.log(`📊 数据:`, JSON.stringify(data, null, 2));
        
        // 检查数据是否为空或无效
        if (Array.isArray(data)) {
            console.log(`📈 数组长度: ${data.length}`);
            if (data.length === 0) {
                console.log(`⚠️  警告: 返回空数组`);
            }
        } else if (typeof data === 'object') {
            const keys = Object.keys(data);
            console.log(`🔑 对象键: ${keys.join(', ')}`);
            
            // 检查关键指标是否为null或undefined
            const nullValues = keys.filter(key => data[key] === null || data[key] === undefined);
            if (nullValues.length > 0) {
                console.log(`⚠️  警告: 以下字段为空值: ${nullValues.join(', ')}`);
            }
        }
        
        return data;
    } catch (error) {
        console.log(`❌ 请求失败:`, error.message);
        return null;
    }
}

async function diagnosisAPIs() {
    console.log('🚀 开始后端API诊断...');
    console.log(`📅 测试日期范围: ${START_DATE} 到 ${END_DATE}`);
    
    // 1. 测试汇总数据API (销售情况页面主要数据源)
    await testAPI(
        `${API_BASE_URL}/api/summary?start_date=${START_DATE}&end_date=${END_DATE}`,
        '汇总数据API (销售情况页面)'
    );
    
    // 2. 测试销售价格趋势API (销售情况页面图表)
    await testAPI(
        `${API_BASE_URL}/api/trends/sales-price?start_date=${START_DATE}&end_date=${END_DATE}`,
        '销售价格趋势API (销售情况页面图表)'
    );
    
    // 3. 测试产销率趋势API (产销率分析页面主图表)
    await testAPI(
        `${API_BASE_URL}/api/trends/ratio?start_date=${START_DATE}&end_date=${END_DATE}`,
        '产销率趋势API (产销率分析页面主图表)'
    );
    
    // 4. 测试产销率统计API (产销率分析页面统计数据)
    await testAPI(
        `${API_BASE_URL}/api/production/ratio-stats?start_date=${START_DATE}&end_date=${END_DATE}`,
        '产销率统计API (产销率分析页面统计)'
    );
    
    // 5. 测试产品列表API
    await testAPI(
        `${API_BASE_URL}/api/products`,
        '产品列表API'
    );
    
    // 6. 测试库存排行API (用于验证是否有基础数据)
    await testAPI(
        `${API_BASE_URL}/api/inventory/top?date=${END_DATE}&limit=5`,
        '库存排行API (验证基础数据)'
    );
    
    console.log('\n📋 诊断完成！');
    console.log('\n💡 问题分析建议:');
    console.log('1. 如果所有API都返回空数组或null值，说明数据库中没有数据');
    console.log('2. 如果API返回错误，检查数据库连接和SQL查询');
    console.log('3. 如果产销率显示为null，可能是除零错误或数据过滤过严');
    console.log('4. 检查日期范围是否与数据库中的实际数据匹配');
}

// 运行诊断
diagnosisAPIs().catch(console.error);