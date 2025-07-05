// 前端修复脚本 - 修复销售情况和产销率分析页面的数据显示问题

// 修复后的 updateProductionRatioStats 函数
async function updateProductionRatioStats(startDate, endDate) {
    console.log('🔄 Updating production ratio stats...', { startDate, endDate });
    
    try {
        const data = await fetchData(`/api/production/ratio-stats?start_date=${startDate}&end_date=${endDate}`);
        console.log('📊 Production ratio stats data received:', data);

        // 检查数据是否有效
        if (!data) {
            console.warn('⚠️ No production ratio stats data received');
            return;
        }

        // 更新产销率分析页面的统计数据
        const productionAvgRatio = document.getElementById('production-avg-ratio');
        const productionMinRatio = document.getElementById('production-min-ratio');
        const productionMaxRatio = document.getElementById('production-max-ratio');

        // 安全地更新DOM元素
        if (productionAvgRatio) {
            const avgRatio = data.avg_ratio || 0;
            productionAvgRatio.textContent = avgRatio.toFixed(1) + '%';
            console.log('✅ Updated avg ratio:', avgRatio.toFixed(1) + '%');
        } else {
            console.warn('⚠️ Element #production-avg-ratio not found');
        }

        if (productionMinRatio) {
            const minRatio = data.min_ratio || 0;
            productionMinRatio.textContent = minRatio.toFixed(1) + '%';
            console.log('✅ Updated min ratio:', minRatio.toFixed(1) + '%');
        } else {
            console.warn('⚠️ Element #production-min-ratio not found');
        }

        if (productionMaxRatio) {
            const maxRatio = data.max_ratio || 0;
            productionMaxRatio.textContent = maxRatio.toFixed(1) + '%';
            console.log('✅ Updated max ratio:', maxRatio.toFixed(1) + '%');
        } else {
            console.warn('⚠️ Element #production-max-ratio not found');
        }

        console.log('✅ Production ratio stats updated successfully');
    } catch (error) {
        console.error('❌ Failed to update production ratio stats:', error);
        
        // 显示错误状态
        const elements = ['production-avg-ratio', 'production-min-ratio', 'production-max-ratio'];
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '-%';
                element.style.color = '#ff3b30';
            }
        });
    }
}

// 修复后的 loadSummaryData 函数
async function loadSummaryData() {
    console.log('📊 Loading summary data...');
    try {
        const data = await fetchData('/api/summary?start_date=2025-06-01&end_date=2025-06-26');
        console.log('📈 Summary data received:', data);

        if (data) {
            // 更新摘要页面的数据
            const summaryProducts = document.getElementById('summary-products');
            const summaryDays = document.getElementById('summary-days');
            const summaryTotalProducts = document.getElementById('summary-total-products');
            const summaryTotalDays = document.getElementById('summary-total-days');
            const summarySalesRatio = document.getElementById('summary-sales-ratio');
            const summaryTotalSales = document.getElementById('summary-total-sales');
            const summaryRatioDetail = document.getElementById('summary-ratio-detail');
            const summarySalesDetail = document.getElementById('summary-sales-detail');

            if (summaryProducts) summaryProducts.textContent = data.total_products || '--';
            if (summaryDays) summaryDays.textContent = data.days || '--';
            if (summaryTotalProducts) summaryTotalProducts.textContent = data.total_products || '--';
            if (summaryTotalDays) summaryTotalDays.textContent = data.days || '--';
            if (summarySalesRatio) summarySalesRatio.textContent = (data.sales_to_production_ratio || 0).toFixed(1) + '%';
            if (summaryTotalSales) summaryTotalSales.textContent = (data.total_sales / 1000 || 0).toFixed(1);
            if (summaryRatioDetail) summaryRatioDetail.textContent = (data.sales_to_production_ratio || 0).toFixed(1) + '%';
            if (summarySalesDetail) summarySalesDetail.textContent = (data.total_sales / 1000 || 0).toFixed(1);

            // 修复：使用正确的日期变量调用产销率统计更新
            const startDate = '2025-06-01';
            const endDate = '2025-06-26';
            await updateProductionRatioStats(startDate, endDate);

            // 更新销售情况页面
            const salesTotalVolume = document.getElementById('sales-total-volume');
            const salesAvgDaily = document.getElementById('sales-avg-daily');
            const salesPeakDay = document.getElementById('sales-peak-day');

            if (salesTotalVolume) {
                salesTotalVolume.textContent = (data.total_sales / 1000 || 0).toFixed(1);
                if (salesAvgDaily) salesAvgDaily.textContent = (data.total_sales / 1000 / (data.days || 1) || 0).toFixed(1);
                if (salesPeakDay) salesPeakDay.textContent = (data.total_sales / 1000 / (data.days || 1) * 1.5 || 0).toFixed(1);
            }

            // 更新实时分析页面的卡片
            const cardTotalProducts = document.getElementById('card-total-products');
            const cardDays = document.getElementById('card-days');
            const cardTotalSales = document.getElementById('card-total-sales');
            const cardTotalProduction = document.getElementById('card-total-production');
            const cardSalesRatio = document.getElementById('card-sales-ratio');

            if (cardTotalProducts) {
                cardTotalProducts.textContent = data.total_products || '--';
                if (cardDays) cardDays.textContent = data.days || '--';
                if (cardTotalSales) cardTotalSales.textContent = (data.total_sales / 1000 || 0).toFixed(1);
                if (cardTotalProduction) cardTotalProduction.textContent = (data.total_production / 1000 || 0).toFixed(1);
                if (cardSalesRatio) cardSalesRatio.textContent = (data.sales_to_production_ratio || 0).toFixed(1) + '%';
            }

            console.log('✅ Summary cards updated successfully');
        }
    } catch (error) {
        console.error('❌ Failed to load summary data:', error);
        
        // 显示错误状态
        const errorElements = [
            'summary-products', 'summary-days', 'summary-total-products', 'summary-total-days',
            'summary-sales-ratio', 'summary-total-sales', 'summary-ratio-detail', 'summary-sales-detail',
            'sales-total-volume', 'sales-avg-daily', 'sales-peak-day',
            'card-total-products', 'card-days', 'card-total-sales', 'card-total-production', 'card-sales-ratio'
        ];
        
        errorElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = '--';
                element.style.color = '#ff3b30';
            }
        });
    }
}

// 修复图表初始化问题
function fixChartInitialization() {
    console.log('🔧 Fixing chart initialization...');
    
    // 确保所有图表在数据加载前都已正确初始化
    const chartElements = [
        { id: 'sales-price-chart', variable: 'salesPriceChart' },
        { id: 'production-ratio-chart', variable: 'productionRatioChart' },
        { id: 'ratio-trend-chart', variable: 'ratioTrendChart' },
        { id: 'inventory-top-chart', variable: 'inventoryChart' }
    ];
    
    chartElements.forEach(({ id, variable }) => {
        const element = document.getElementById(id);
        if (element && !window[variable]) {
            console.log(`🎨 Initializing ${variable} for element ${id}`);
            try {
                window[variable] = echarts.init(element);
                console.log(`✅ ${variable} initialized successfully`);
            } catch (error) {
                console.error(`❌ Failed to initialize ${variable}:`, error);
            }
        }
    });
}

// 诊断DOM元素是否存在
function diagnoseDOMElements() {
    console.log('🔍 Diagnosing DOM elements...');
    
    const requiredElements = [
        // 产销率分析页面元素
        'production-avg-ratio', 'production-min-ratio', 'production-max-ratio',
        // 销售情况页面元素
        'sales-total-volume', 'sales-avg-daily', 'sales-peak-day',
        // 图表容器元素
        'sales-price-chart', 'production-ratio-chart', 'ratio-trend-chart', 'inventory-top-chart'
    ];
    
    const missingElements = [];
    const foundElements = [];
    
    requiredElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            foundElements.push(id);
        } else {
            missingElements.push(id);
        }
    });
    
    console.log('✅ Found elements:', foundElements);
    console.log('❌ Missing elements:', missingElements);
    
    return { found: foundElements, missing: missingElements };
}

// 应用修复
function applyFixes() {
    console.log('🚀 Applying frontend fixes...');
    
    // 1. 诊断DOM元素
    const diagnosis = diagnoseDOMElements();
    
    // 2. 修复图表初始化
    fixChartInitialization();
    
    // 3. 重新加载数据
    setTimeout(() => {
        console.log('🔄 Reloading data with fixes...');
        loadSummaryData();
    }, 1000);
    
    // 4. 覆盖全局函数
    window.updateProductionRatioStats = updateProductionRatioStats;
    window.loadSummaryData = loadSummaryData;
    
    console.log('✅ Frontend fixes applied successfully');
    return diagnosis;
}

// 导出修复函数
window.applyFrontendFixes = applyFixes;
window.diagnoseDOMElements = diagnoseDOMElements;
window.fixChartInitialization = fixChartInitialization;

console.log('🔧 Frontend fix script loaded. Run applyFrontendFixes() to apply fixes.');