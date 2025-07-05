// 后端数据库诊断脚本
// 用于检查D1数据库的表结构和数据完整性

const DIAGNOSIS_CONFIG = {
    API_BASE_URL: 'https://backend.qu18354531302.workers.dev',
    // API_BASE_URL: 'http://localhost:8787', // 本地测试时使用
    DATE_RANGE: {
        start: '2025-06-01',
        end: '2025-06-26'
    }
};

// 数据库表结构检查
async function checkDatabaseTables() {
    console.log('🗄️ 检查数据库表结构...');
    
    const tables = ['Products', 'DailyMetrics', 'PriceAdjustments', 'Users'];
    const results = {};
    
    for (const table of tables) {
        try {
            // 通过API检查表是否存在并获取记录数
            let endpoint = '';
            switch (table) {
                case 'Products':
                    endpoint = '/api/products';
                    break;
                case 'DailyMetrics':
                    endpoint = `/api/summary?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`;
                    break;
                case 'PriceAdjustments':
                    endpoint = `/api/price-changes?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}&min_price_diff=0`;
                    break;
                default:
                    continue;
            }
            
            const response = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                mode: 'cors',
                credentials: 'omit'
            });
            
            if (response.ok) {
                const data = await response.json();
                results[table] = {
                    exists: true,
                    status: 'accessible',
                    recordCount: Array.isArray(data) ? data.length : (data ? 1 : 0),
                    sampleData: Array.isArray(data) ? data.slice(0, 2) : data
                };
                console.log(`✅ ${table}: 可访问，记录数: ${results[table].recordCount}`);
            } else {
                results[table] = {
                    exists: false,
                    status: 'error',
                    error: `HTTP ${response.status}: ${response.statusText}`
                };
                console.log(`❌ ${table}: 访问失败 - ${results[table].error}`);
            }
            
        } catch (error) {
            results[table] = {
                exists: false,
                status: 'error',
                error: error.message
            };
            console.log(`❌ ${table}: 访问异常 - ${error.message}`);
        }
    }
    
    return results;
}

// 数据完整性检查
async function checkDataIntegrity() {
    console.log('🔍 检查数据完整性...');
    
    const checks = {};
    
    try {
        // 1. 检查汇总数据的合理性
        const summaryResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/summary?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            mode: 'cors'
        });
        
        if (summaryResponse.ok) {
            const summary = await summaryResponse.json();
            checks.summary = {
                status: 'success',
                data: summary,
                issues: []
            };
            
            // 检查数据合理性
            if (!summary.total_products || summary.total_products <= 0) {
                checks.summary.issues.push('产品数量为0或无效');
            }
            if (!summary.total_sales || summary.total_sales <= 0) {
                checks.summary.issues.push('总销量为0或无效');
            }
            if (!summary.total_production || summary.total_production <= 0) {
                checks.summary.issues.push('总产量为0或无效');
            }
            if (!summary.sales_to_production_ratio || summary.sales_to_production_ratio <= 0) {
                checks.summary.issues.push('产销率为0或无效');
            }
            
            console.log(`📊 汇总数据检查: ${checks.summary.issues.length === 0 ? '正常' : '发现问题'}`);
            if (checks.summary.issues.length > 0) {
                checks.summary.issues.forEach(issue => console.log(`   ⚠️ ${issue}`));
            }
        } else {
            checks.summary = {
                status: 'error',
                error: `HTTP ${summaryResponse.status}`
            };
        }
        
        // 2. 检查库存数据的连续性
        const inventoryResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/inventory/top?date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}&limit=15`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            mode: 'cors'
        });
        
        if (inventoryResponse.ok) {
            const inventory = await inventoryResponse.json();
            checks.inventory = {
                status: 'success',
                data: inventory,
                issues: []
            };
            
            if (!Array.isArray(inventory) || inventory.length === 0) {
                checks.inventory.issues.push('库存数据为空');
            } else {
                // 检查库存数据质量
                const invalidRecords = inventory.filter(item => 
                    !item.product_name || 
                    item.inventory_level === null || 
                    item.inventory_level === undefined ||
                    item.inventory_level < 0
                );
                
                if (invalidRecords.length > 0) {
                    checks.inventory.issues.push(`发现${invalidRecords.length}条无效库存记录`);
                }
            }
            
            console.log(`📦 库存数据检查: ${checks.inventory.issues.length === 0 ? '正常' : '发现问题'}`);
            if (checks.inventory.issues.length > 0) {
                checks.inventory.issues.forEach(issue => console.log(`   ⚠️ ${issue}`));
            }
        } else {
            checks.inventory = {
                status: 'error',
                error: `HTTP ${inventoryResponse.status}`
            };
        }
        
        // 3. 检查产销率趋势数据
        const ratioResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/trends/ratio?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            mode: 'cors'
        });
        
        if (ratioResponse.ok) {
            const ratioData = await ratioResponse.json();
            checks.ratio = {
                status: 'success',
                data: ratioData,
                issues: []
            };
            
            if (!Array.isArray(ratioData) || ratioData.length === 0) {
                checks.ratio.issues.push('产销率趋势数据为空');
            } else {
                // 检查空值比例
                const nullCount = ratioData.filter(item => 
                    item.ratio === null || item.ratio === undefined
                ).length;
                
                const nullPercentage = (nullCount / ratioData.length) * 100;
                
                if (nullPercentage > 50) {
                    checks.ratio.issues.push(`产销率数据空值比例过高: ${nullPercentage.toFixed(1)}%`);
                } else if (nullPercentage > 0) {
                    checks.ratio.issues.push(`产销率数据包含${nullCount}个空值 (${nullPercentage.toFixed(1)}%)`);
                }
                
                // 检查异常值
                const validRatios = ratioData.filter(item => item.ratio !== null && item.ratio !== undefined);
                const extremeRatios = validRatios.filter(item => item.ratio > 200 || item.ratio < 0);
                
                if (extremeRatios.length > 0) {
                    checks.ratio.issues.push(`发现${extremeRatios.length}个异常产销率值`);
                }
            }
            
            console.log(`📊 产销率数据检查: ${checks.ratio.issues.length === 0 ? '正常' : '发现问题'}`);
            if (checks.ratio.issues.length > 0) {
                checks.ratio.issues.forEach(issue => console.log(`   ⚠️ ${issue}`));
            }
        } else {
            checks.ratio = {
                status: 'error',
                error: `HTTP ${ratioResponse.status}`
            };
        }
        
        // 4. 检查销售价格数据
        const salesPriceResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/trends/sales-price?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            mode: 'cors'
        });
        
        if (salesPriceResponse.ok) {
            const salesPriceData = await salesPriceResponse.json();
            checks.salesPrice = {
                status: 'success',
                data: salesPriceData,
                issues: []
            };
            
            if (!Array.isArray(salesPriceData) || salesPriceData.length === 0) {
                checks.salesPrice.issues.push('销售价格数据为空');
            } else {
                // 检查关键字段的空值
                const invalidRecords = salesPriceData.filter(item => 
                    item.total_sales === null || item.total_sales === undefined ||
                    item.avg_price === null || item.avg_price === undefined ||
                    item.total_sales < 0 || item.avg_price < 0
                );
                
                if (invalidRecords.length > 0) {
                    checks.salesPrice.issues.push(`发现${invalidRecords.length}条无效销售价格记录`);
                }
            }
            
            console.log(`💰 销售价格数据检查: ${checks.salesPrice.issues.length === 0 ? '正常' : '发现问题'}`);
            if (checks.salesPrice.issues.length > 0) {
                checks.salesPrice.issues.forEach(issue => console.log(`   ⚠️ ${issue}`));
            }
        } else {
            checks.salesPrice = {
                status: 'error',
                error: `HTTP ${salesPriceResponse.status}`
            };
        }
        
    } catch (error) {
        console.error('❌ 数据完整性检查失败:', error);
        checks.error = error.message;
    }
    
    return checks;
}

// API响应格式检查
async function checkAPIResponseFormats() {
    console.log('📡 检查API响应格式...');
    
    const apiEndpoints = [
        {
            name: 'summary',
            url: `/api/summary?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`,
            expectedFields: ['total_products', 'days', 'total_sales', 'total_production', 'sales_to_production_ratio']
        },
        {
            name: 'inventory',
            url: `/api/inventory/top?date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}&limit=5`,
            expectedFields: ['product_name', 'inventory_level'],
            isArray: true
        },
        {
            name: 'ratio',
            url: `/api/trends/ratio?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`,
            expectedFields: ['record_date', 'ratio'],
            isArray: true
        },
        {
            name: 'salesPrice',
            url: `/api/trends/sales-price?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`,
            expectedFields: ['record_date', 'total_sales', 'avg_price'],
            isArray: true
        }
    ];
    
    const results = {};
    
    for (const endpoint of apiEndpoints) {
        try {
            const response = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}${endpoint.url}`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                mode: 'cors'
            });
            
            if (response.ok) {
                const data = await response.json();
                
                results[endpoint.name] = {
                    status: 'success',
                    responseTime: response.headers.get('x-response-time') || 'unknown',
                    dataType: Array.isArray(data) ? 'array' : typeof data,
                    recordCount: Array.isArray(data) ? data.length : 1,
                    missingFields: [],
                    sampleData: Array.isArray(data) ? data[0] : data
                };
                
                // 检查必需字段
                const sampleRecord = Array.isArray(data) ? data[0] : data;
                if (sampleRecord) {
                    endpoint.expectedFields.forEach(field => {
                        if (!(field in sampleRecord)) {
                            results[endpoint.name].missingFields.push(field);
                        }
                    });
                }
                
                // 检查数据类型匹配
                if (endpoint.isArray && !Array.isArray(data)) {
                    results[endpoint.name].typeError = '期望数组类型，实际为对象';
                } else if (!endpoint.isArray && Array.isArray(data)) {
                    results[endpoint.name].typeError = '期望对象类型，实际为数组';
                }
                
                console.log(`✅ ${endpoint.name}: 格式正常 (${results[endpoint.name].recordCount}条记录)`);
                if (results[endpoint.name].missingFields.length > 0) {
                    console.log(`   ⚠️ 缺失字段: ${results[endpoint.name].missingFields.join(', ')}`);
                }
                
            } else {
                results[endpoint.name] = {
                    status: 'error',
                    error: `HTTP ${response.status}: ${response.statusText}`
                };
                console.log(`❌ ${endpoint.name}: ${results[endpoint.name].error}`);
            }
            
        } catch (error) {
            results[endpoint.name] = {
                status: 'error',
                error: error.message
            };
            console.log(`❌ ${endpoint.name}: ${error.message}`);
        }
    }
    
    return results;
}

// 生成后端诊断报告
function generateBackendReport(tableResults, integrityResults, formatResults) {
    console.log('\n📋 ===== 后端诊断报告 =====');
    
    // 表结构状态
    console.log('\n🗄️ 数据库表状态:');
    Object.entries(tableResults).forEach(([table, result]) => {
        if (result.exists) {
            console.log(`✅ ${table}: 正常 (${result.recordCount}条记录)`);
        } else {
            console.log(`❌ ${table}: ${result.error}`);
        }
    });
    
    // 数据完整性状态
    console.log('\n🔍 数据完整性状态:');
    Object.entries(integrityResults).forEach(([check, result]) => {
        if (result.status === 'success') {
            if (result.issues && result.issues.length > 0) {
                console.log(`⚠️ ${check}: 发现${result.issues.length}个问题`);
                result.issues.forEach(issue => console.log(`   - ${issue}`));
            } else {
                console.log(`✅ ${check}: 数据完整`);
            }
        } else {
            console.log(`❌ ${check}: ${result.error}`);
        }
    });
    
    // API格式状态
    console.log('\n📡 API响应格式状态:');
    Object.entries(formatResults).forEach(([api, result]) => {
        if (result.status === 'success') {
            const issues = [];
            if (result.missingFields && result.missingFields.length > 0) {
                issues.push(`缺失字段: ${result.missingFields.join(', ')}`);
            }
            if (result.typeError) {
                issues.push(result.typeError);
            }
            
            if (issues.length === 0) {
                console.log(`✅ ${api}: 格式正确`);
            } else {
                console.log(`⚠️ ${api}: ${issues.join('; ')}`);
            }
        } else {
            console.log(`❌ ${api}: ${result.error}`);
        }
    });
    
    // 总结和建议
    console.log('\n💡 诊断总结:');
    const allIssues = [];
    
    // 收集所有问题
    Object.entries(tableResults).forEach(([table, result]) => {
        if (!result.exists) {
            allIssues.push(`${table}表不可访问`);
        }
    });
    
    Object.entries(integrityResults).forEach(([check, result]) => {
        if (result.status === 'error') {
            allIssues.push(`${check}数据检查失败`);
        } else if (result.issues && result.issues.length > 0) {
            allIssues.push(`${check}数据存在质量问题`);
        }
    });
    
    Object.entries(formatResults).forEach(([api, result]) => {
        if (result.status === 'error') {
            allIssues.push(`${api} API不可用`);
        } else if (result.missingFields && result.missingFields.length > 0) {
            allIssues.push(`${api} API响应格式不完整`);
        }
    });
    
    if (allIssues.length === 0) {
        console.log('✅ 后端系统运行正常，未发现明显问题');
    } else {
        console.log('❌ 发现以下问题需要解决:');
        allIssues.forEach((issue, index) => {
            console.log(`   ${index + 1}. ${issue}`);
        });
        
        console.log('\n🔧 建议修复步骤:');
        console.log('1. 检查D1数据库连接和表结构');
        console.log('2. 验证DailyMetrics表是否存在且包含数据');
        console.log('3. 检查数据导入脚本的执行状态');
        console.log('4. 验证API端点的SQL查询语句');
        console.log('5. 检查产品过滤逻辑的一致性');
    }
    
    return {
        tables: tableResults,
        integrity: integrityResults,
        formats: formatResults,
        issues: allIssues
    };
}

// 主后端诊断函数
async function runBackendDiagnosis() {
    try {
        console.log('🚀 开始后端系统诊断...\n');
        
        const tableResults = await checkDatabaseTables();
        const integrityResults = await checkDataIntegrity();
        const formatResults = await checkAPIResponseFormats();
        
        const report = generateBackendReport(tableResults, integrityResults, formatResults);
        
        console.log('\n🏁 后端诊断完成！');
        
        // 保存结果到全局变量
        if (typeof window !== 'undefined') {
            window.BackendDiagnosisResults = report;
        }
        
        return report;
        
    } catch (error) {
        console.error('❌ 后端诊断过程中发生错误:', error);
        return { error: error.message };
    }
}

// 导出函数
if (typeof window !== 'undefined') {
    window.runBackendDiagnosis = runBackendDiagnosis;
}

// 如果在Node.js环境中，导出模块
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        runBackendDiagnosis,
        checkDatabaseTables,
        checkDataIntegrity,
        checkAPIResponseFormats
    };
}