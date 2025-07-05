// 生产销售数据分析系统 - 全面诊断脚本
// 用于验证数据库完整性和前端API调用问题

console.log('🔍 开始系统诊断...');

// 诊断配置
const DIAGNOSIS_CONFIG = {
    API_BASE_URL: 'https://backend.qu18354531302.workers.dev',
    // API_BASE_URL: 'http://localhost:8787', // 本地测试时使用
    DATE_RANGE: {
        start: '2025-06-01',
        end: '2025-06-26'
    },
    TIMEOUT: 10000 // 10秒超时
};

// 诊断结果收集器
const DiagnosisResults = {
    database: {},
    api: {},
    frontend: {},
    charts: {},
    summary: {}
};

// 1. 数据库完整性诊断
async function diagnoseDatabaseIntegrity() {
    console.log('📊 诊断1: 数据库完整性检查');
    
    try {
        // 检查汇总数据API
        const summaryResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/summary?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors',
            credentials: 'omit'
        });

        console.log('📡 汇总API响应状态:', summaryResponse.status);
        
        if (!summaryResponse.ok) {
            throw new Error(`汇总API请求失败: ${summaryResponse.status} ${summaryResponse.statusText}`);
        }

        const summaryData = await summaryResponse.json();
        console.log('📈 汇总数据:', summaryData);

        DiagnosisResults.database.summary = {
            status: 'success',
            data: summaryData,
            hasValidData: summaryData && summaryData.total_products > 0
        };

        // 检查库存数据API
        const inventoryResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/inventory/top?date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}&limit=15`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors',
            credentials: 'omit'
        });

        console.log('📦 库存API响应状态:', inventoryResponse.status);
        
        if (!inventoryResponse.ok) {
            throw new Error(`库存API请求失败: ${inventoryResponse.status} ${inventoryResponse.statusText}`);
        }

        const inventoryData = await inventoryResponse.json();
        console.log('📦 库存数据样本:', inventoryData.slice(0, 3));

        DiagnosisResults.database.inventory = {
            status: 'success',
            data: inventoryData,
            hasValidData: Array.isArray(inventoryData) && inventoryData.length > 0
        };

        // 检查产销率趋势API
        const ratioResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/trends/ratio?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors',
            credentials: 'omit'
        });

        console.log('📊 产销率API响应状态:', ratioResponse.status);
        
        if (!ratioResponse.ok) {
            throw new Error(`产销率API请求失败: ${ratioResponse.status} ${ratioResponse.statusText}`);
        }

        const ratioData = await ratioResponse.json();
        console.log('📊 产销率数据样本:', ratioData.slice(0, 3));

        DiagnosisResults.database.ratio = {
            status: 'success',
            data: ratioData,
            hasValidData: Array.isArray(ratioData) && ratioData.length > 0,
            hasNullValues: ratioData.some(item => item.ratio === null || item.ratio === undefined)
        };

        // 检查销售价格趋势API
        const salesPriceResponse = await fetch(`${DIAGNOSIS_CONFIG.API_BASE_URL}/api/trends/sales-price?start_date=${DIAGNOSIS_CONFIG.DATE_RANGE.start}&end_date=${DIAGNOSIS_CONFIG.DATE_RANGE.end}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors',
            credentials: 'omit'
        });

        console.log('💰 销售价格API响应状态:', salesPriceResponse.status);
        
        if (!salesPriceResponse.ok) {
            throw new Error(`销售价格API请求失败: ${salesPriceResponse.status} ${salesPriceResponse.statusText}`);
        }

        const salesPriceData = await salesPriceResponse.json();
        console.log('💰 销售价格数据样本:', salesPriceData.slice(0, 3));

        DiagnosisResults.database.salesPrice = {
            status: 'success',
            data: salesPriceData,
            hasValidData: Array.isArray(salesPriceData) && salesPriceData.length > 0,
            hasNullValues: salesPriceData.some(item => 
                item.total_sales === null || item.total_sales === undefined ||
                item.avg_price === null || item.avg_price === undefined
            )
        };

    } catch (error) {
        console.error('❌ 数据库诊断失败:', error);
        DiagnosisResults.database.error = error.message;
    }
}

// 2. 前端JavaScript函数可用性诊断
async function diagnoseFrontendFunctions() {
    console.log('🔧 诊断2: 前端JavaScript函数可用性检查');
    
    const functionsToCheck = [
        'loadSummaryData',
        'loadDetailData', 
        'fetchData',
        'loadAllData',
        'updateInventoryChart',
        'updateSalesPriceChart',
        'updateRatioTrendChart',
        'initializeCharts',
        'showTab'
    ];

    DiagnosisResults.frontend.functions = {};

    functionsToCheck.forEach(funcName => {
        const isAvailable = typeof window[funcName] === 'function';
        DiagnosisResults.frontend.functions[funcName] = {
            available: isAvailable,
            type: typeof window[funcName]
        };
        
        if (isAvailable) {
            console.log(`✅ ${funcName}: 可用`);
        } else {
            console.log(`❌ ${funcName}: 不可用 (${typeof window[funcName]})`);
        }
    });

    // 检查全局变量
    const globalVarsToCheck = [
        'inventoryChart',
        'salesPriceChart', 
        'ratioTrendChart',
        'productionRatioChart',
        'salesTrendChart'
    ];

    DiagnosisResults.frontend.globalVars = {};

    globalVarsToCheck.forEach(varName => {
        const isAvailable = window[varName] !== undefined;
        DiagnosisResults.frontend.globalVars[varName] = {
            available: isAvailable,
            type: typeof window[varName],
            value: isAvailable ? 'initialized' : 'undefined'
        };
        
        if (isAvailable) {
            console.log(`✅ ${varName}: 已初始化`);
        } else {
            console.log(`❌ ${varName}: 未初始化`);
        }
    });
}

// 3. 图表渲染诊断
async function diagnoseChartRendering() {
    console.log('📈 诊断3: 图表渲染状态检查');
    
    const chartContainers = [
        'sales-trend-chart',
        'production-ratio-chart', 
        'inventory-page-top-chart',
        'inventory-page-pie-chart',
        'production-ratio-trend-chart'
    ];

    DiagnosisResults.charts.containers = {};

    chartContainers.forEach(chartId => {
        const element = document.getElementById(chartId);
        const isVisible = element && element.offsetWidth > 0 && element.offsetHeight > 0;
        
        DiagnosisResults.charts.containers[chartId] = {
            exists: !!element,
            visible: isVisible,
            dimensions: element ? {
                width: element.offsetWidth,
                height: element.offsetHeight
            } : null,
            computedStyle: element ? {
                display: window.getComputedStyle(element).display,
                visibility: window.getComputedStyle(element).visibility
            } : null
        };
        
        if (element && isVisible) {
            console.log(`✅ ${chartId}: 容器正常 (${element.offsetWidth}x${element.offsetHeight})`);
        } else if (element) {
            console.log(`⚠️ ${chartId}: 容器存在但不可见`);
        } else {
            console.log(`❌ ${chartId}: 容器不存在`);
        }
    });

    // 检查ECharts库
    DiagnosisResults.charts.echarts = {
        loaded: typeof echarts !== 'undefined',
        version: typeof echarts !== 'undefined' ? echarts.version : null
    };

    if (typeof echarts !== 'undefined') {
        console.log(`✅ ECharts库已加载: v${echarts.version}`);
    } else {
        console.log('❌ ECharts库未加载');
    }
}

// 4. 数据流转诊断
async function diagnoseDataFlow() {
    console.log('🔄 诊断4: 数据流转完整性检查');
    
    try {
        // 模拟完整的数据加载流程
        console.log('🔄 模拟数据加载流程...');
        
        if (typeof window.loadSummaryData === 'function') {
            console.log('📊 调用loadSummaryData...');
            await window.loadSummaryData();
            console.log('✅ loadSummaryData执行完成');
        } else {
            console.log('❌ loadSummaryData函数不可用');
        }

        // 检查DOM元素数据更新
        const elementsToCheck = [
            'summary-total-sales',
            'summary-sales-ratio', 
            'production-avg-ratio',
            'production-min-ratio',
            'production-max-ratio',
            'sales-total-volume',
            'sales-avg-daily',
            'sales-peak-day'
        ];

        DiagnosisResults.frontend.domUpdates = {};

        elementsToCheck.forEach(elementId => {
            const element = document.getElementById(elementId);
            const hasData = element && element.textContent && element.textContent !== '--' && element.textContent !== '--%';
            
            DiagnosisResults.frontend.domUpdates[elementId] = {
                exists: !!element,
                hasData: hasData,
                content: element ? element.textContent : null
            };
            
            if (hasData) {
                console.log(`✅ ${elementId}: ${element.textContent}`);
            } else if (element) {
                console.log(`⚠️ ${elementId}: 无数据 (${element.textContent})`);
            } else {
                console.log(`❌ ${elementId}: 元素不存在`);
            }
        });

    } catch (error) {
        console.error('❌ 数据流转诊断失败:', error);
        DiagnosisResults.frontend.dataFlowError = error.message;
    }
}

// 5. 生成诊断报告
function generateDiagnosisReport() {
    console.log('\n📋 ===== 诊断报告 =====');
    
    // 数据库诊断结果
    console.log('\n📊 数据库诊断结果:');
    if (DiagnosisResults.database.summary?.hasValidData) {
        console.log('✅ 汇总数据: 正常');
        console.log(`   - 产品数量: ${DiagnosisResults.database.summary.data.total_products}`);
        console.log(`   - 总销量: ${DiagnosisResults.database.summary.data.total_sales?.toFixed(1) || 'N/A'} 吨`);
        console.log(`   - 产销率: ${DiagnosisResults.database.summary.data.sales_to_production_ratio?.toFixed(1) || 'N/A'}%`);
    } else {
        console.log('❌ 汇总数据: 异常或无数据');
    }

    if (DiagnosisResults.database.inventory?.hasValidData) {
        console.log('✅ 库存数据: 正常');
        console.log(`   - 库存记录数: ${DiagnosisResults.database.inventory.data.length}`);
    } else {
        console.log('❌ 库存数据: 异常或无数据');
    }

    if (DiagnosisResults.database.ratio?.hasValidData) {
        console.log('✅ 产销率数据: 正常');
        console.log(`   - 趋势记录数: ${DiagnosisResults.database.ratio.data.length}`);
        if (DiagnosisResults.database.ratio.hasNullValues) {
            console.log('⚠️   - 包含空值，可能影响图表显示');
        }
    } else {
        console.log('❌ 产销率数据: 异常或无数据');
    }

    if (DiagnosisResults.database.salesPrice?.hasValidData) {
        console.log('✅ 销售价格数据: 正常');
        console.log(`   - 价格记录数: ${DiagnosisResults.database.salesPrice.data.length}`);
        if (DiagnosisResults.database.salesPrice.hasNullValues) {
            console.log('⚠️   - 包含空值，可能影响图表显示');
        }
    } else {
        console.log('❌ 销售价格数据: 异常或无数据');
    }

    // 前端函数诊断结果
    console.log('\n🔧 前端函数诊断结果:');
    const availableFunctions = Object.entries(DiagnosisResults.frontend.functions || {})
        .filter(([name, info]) => info.available).length;
    const totalFunctions = Object.keys(DiagnosisResults.frontend.functions || {}).length;
    
    console.log(`✅ 可用函数: ${availableFunctions}/${totalFunctions}`);
    
    Object.entries(DiagnosisResults.frontend.functions || {}).forEach(([name, info]) => {
        if (!info.available) {
            console.log(`❌ ${name}: 不可用`);
        }
    });

    // 图表诊断结果
    console.log('\n📈 图表诊断结果:');
    const visibleCharts = Object.entries(DiagnosisResults.charts.containers || {})
        .filter(([name, info]) => info.visible).length;
    const totalCharts = Object.keys(DiagnosisResults.charts.containers || {}).length;
    
    console.log(`✅ 可见图表容器: ${visibleCharts}/${totalCharts}`);
    
    if (DiagnosisResults.charts.echarts?.loaded) {
        console.log(`✅ ECharts库: v${DiagnosisResults.charts.echarts.version}`);
    } else {
        console.log('❌ ECharts库: 未加载');
    }

    // DOM更新诊断结果
    console.log('\n🔄 DOM更新诊断结果:');
    const updatedElements = Object.entries(DiagnosisResults.frontend.domUpdates || {})
        .filter(([name, info]) => info.hasData).length;
    const totalElements = Object.keys(DiagnosisResults.frontend.domUpdates || {}).length;
    
    console.log(`✅ 已更新元素: ${updatedElements}/${totalElements}`);

    // 问题总结
    console.log('\n🎯 问题总结:');
    const issues = [];

    if (!DiagnosisResults.database.summary?.hasValidData) {
        issues.push('数据库汇总数据缺失或异常');
    }
    if (!DiagnosisResults.database.inventory?.hasValidData) {
        issues.push('库存数据缺失或异常');
    }
    if (!DiagnosisResults.database.ratio?.hasValidData) {
        issues.push('产销率数据缺失或异常');
    }
    if (!DiagnosisResults.database.salesPrice?.hasValidData) {
        issues.push('销售价格数据缺失或异常');
    }
    if (availableFunctions < totalFunctions) {
        issues.push('前端JavaScript函数部分不可用');
    }
    if (visibleCharts < totalCharts) {
        issues.push('图表容器部分不可见');
    }
    if (!DiagnosisResults.charts.echarts?.loaded) {
        issues.push('ECharts库未正确加载');
    }
    if (updatedElements < totalElements) {
        issues.push('DOM元素数据更新不完整');
    }

    if (issues.length === 0) {
        console.log('✅ 未发现明显问题，系统运行正常');
    } else {
        console.log('❌ 发现以下问题:');
        issues.forEach((issue, index) => {
            console.log(`   ${index + 1}. ${issue}`);
        });
    }

    // 修复建议
    console.log('\n💡 修复建议:');
    if (issues.length > 0) {
        console.log('1. 检查数据库DailyMetrics表是否存在且包含数据');
        console.log('2. 验证API端点响应格式和数据完整性');
        console.log('3. 确保前端JavaScript文件正确加载和初始化');
        console.log('4. 检查图表容器的CSS显示状态');
        console.log('5. 验证ECharts库的加载顺序和版本兼容性');
    }

    return DiagnosisResults;
}

// 主诊断函数
async function runFullDiagnosis() {
    try {
        console.log('🚀 开始全面系统诊断...\n');
        
        await diagnoseDatabaseIntegrity();
        await diagnoseFrontendFunctions();
        await diagnoseChartRendering();
        await diagnoseDataFlow();
        
        const report = generateDiagnosisReport();
        
        console.log('\n🏁 诊断完成！');
        console.log('📋 完整诊断结果已保存到 DiagnosisResults 对象');
        
        // 将结果保存到全局变量供进一步分析
        window.DiagnosisResults = report;
        
        return report;
        
    } catch (error) {
        console.error('❌ 诊断过程中发生错误:', error);
        return { error: error.message };
    }
}

// 自动运行诊断（如果在浏览器环境中）
if (typeof window !== 'undefined') {
    // 等待页面加载完成后运行诊断
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(runFullDiagnosis, 1000); // 延迟1秒确保所有脚本加载完成
        });
    } else {
        setTimeout(runFullDiagnosis, 1000);
    }
}

// 导出诊断函数供手动调用
if (typeof window !== 'undefined') {
    window.runFullDiagnosis = runFullDiagnosis;
    window.DiagnosisResults = DiagnosisResults;
}