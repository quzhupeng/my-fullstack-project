// --- CONFIGURATION ---
// 生产环境API地址
const API_BASE_URL = 'https://backend.qu18354531302.workers.dev';
// 本地开发环境API地址
// const API_BASE_URL = 'http://localhost:8787';

// 添加调试日志
console.log('🚀 Script.js loaded, API_BASE_URL:', API_BASE_URL);

// --- GLOBAL VARIABLES ---
let inventoryChart, salesPriceChart, ratioTrendChart;
let inventoryTrendChart, productionRatioChart, salesTrendChart;
let salesSparkline, ratioSparkline, realtimeSalesSparkline, realtimeRatioSparkline;
// 新增专业图表变量
let categoryPieChart, categoryBarChart, categoryPriceChart;
let multiSeriesChart, inventoryTurnoverChart;
// 价格分析图表变量
let priceFrequencyChart, priceMajorChangesChart;
// 库存页面图表变量
let inventoryPageTopChart, inventoryPieChart, productionRatioTrendChart;

// --- GLOBAL API HELPER (Available immediately) ---
async function fetchData(endpoint) {
    const fullUrl = `${API_BASE_URL}${endpoint}`;
    console.log('🌐 Fetching data from:', fullUrl);

    try {
        const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            mode: 'cors', // Explicitly enable CORS
            credentials: 'omit' // Don't send credentials for CORS
        });

        console.log('📡 Response status:', response.status, response.statusText);
        console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

        if (!response.ok) {
            let errorMessage = `HTTP error! status: ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (parseError) {
                console.warn('⚠️ Could not parse error response as JSON');
                const errorText = await response.text();
                console.log('📄 Error response text:', errorText);
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('✅ Data received:', data);
        return data;
    } catch (error) {
        console.error('❌ API request failed:', error);
        console.error('❌ Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        throw error;
    }
}

// --- GLOBAL DATA LOADING FUNCTIONS (Available immediately) ---
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

            // 更新产销率分析页面 - 使用专门的API获取统计数据
            updateProductionRatioStats(startDate, endDate);

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
    }
}

// --- GLOBAL DETAIL DATA LOADING ---
async function loadDetailData() {
    const productFilter = document.getElementById('product-filter')?.value || '';
    const startDate = document.getElementById('detail-start-date')?.value || '2025-06-01';
    const endDate = document.getElementById('detail-end-date')?.value || '2025-06-26';

    try {
        // 这里可以根据需要调用不同的API端点
        const data = await fetchData(`/api/summary?start_date=${startDate}&end_date=${endDate}`);

        const tableBody = document.getElementById('detail-table-body');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #86868b;">暂无详细数据，功能开发中...</td></tr>';
        }
    } catch (error) {
        console.error('Failed to load detail data:', error);
        const tableBody = document.getElementById('detail-table-body');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #ff3b30;">数据加载失败</td></tr>';
        }
    }
}

// --- GLOBAL CHART UPDATE FUNCTIONS ---
async function updateInventoryChart(date) {
    if (!inventoryChart) {
        console.warn('⚠️ Inventory chart not initialized');
        return;
    }

    try {
        inventoryChart.showLoading();
        const data = await fetchData(`/api/inventory/top?date=${date}&limit=15`);
        inventoryChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No inventory data received');
            return;
        }

        console.log('📊 Updating inventory chart with data:', data.length, 'items');

        // 专业财经报告风格的库存TOP15图表配置
        inventoryChart.setOption({
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.98)',
                borderColor: '#E0E0E0',
                borderWidth: 1,
                textStyle: {
                    color: '#333333',
                    fontSize: 12,
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                },
                padding: [8, 12],
                extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
                formatter: function(params) {
                    const item = params[0];
                    return `<div style="font-weight: 600; margin-bottom: 8px; color: #005BAC;">${item.name}</div>
                            <div style="display: flex; align-items: center; margin: 4px 0;">
                                <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                库存量: <strong>${item.value.toFixed(1)} 吨</strong>
                            </div>
                            <div style="color: #666666; font-size: 11px; margin-top: 4px;">排名: TOP ${item.dataIndex + 1}</div>`;
                }
            },
            grid: {
                left: '8%',
                right: '8%',
                bottom: '20%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.map(item => item.product_name),
                axisLabel: {
                    rotate: 45,
                    fontSize: 12,
                    color: '#666666',
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif',
                    interval: 0
                },
                axisLine: {
                    lineStyle: {
                        color: '#E0E0E0',
                        width: 1
                    }
                },
                axisTick: {
                    lineStyle: { color: '#E0E0E0' }
                }
            },
            yAxis: {
                type: 'value',
                name: '库存量 (吨)',
                nameTextStyle: {
                    color: '#005BAC',
                    fontSize: 12,
                    fontWeight: 600,
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                },
                axisLabel: {
                    color: '#666666',
                    fontSize: 12,
                    formatter: '{value}'
                },
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: '#005BAC',
                        width: 2
                    }
                },
                axisTick: {
                    lineStyle: { color: '#005BAC' }
                },
                splitLine: {
                    lineStyle: {
                        color: '#F5F5F5',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '库存量',
                type: 'bar',
                data: data.map(item => item.inventory_level),
                barWidth: '60%',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#005BAC' },
                        { offset: 1, color: '#49A9E8' }
                    ]),
                    borderRadius: [4, 4, 0, 0],
                    shadowColor: 'rgba(0, 91, 172, 0.3)',
                    shadowBlur: 8,
                    shadowOffsetY: 2
                },
                emphasis: {
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#49A9E8' },
                            { offset: 1, color: '#005BAC' }
                        ]),
                        shadowBlur: 12,
                        shadowOffsetY: 4
                    }
                },
                label: {
                    show: true,  // 启用数据标签显示
                    position: 'top',
                    color: '#005BAC',
                    fontSize: 11,
                    fontWeight: 'bold',
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif',
                    formatter: function(params) {
                        const value = params.value;
                        // 使用T单位格式化显示：大于1000显示为T格式，否则显示整数
                        return value >= 1000 ? `${(value / 1000).toFixed(1)}T` : value.toFixed(0);
                    }
                }
                // 移除markPoint以避免红色标记点遮挡库存量数值
            }]
        });

        console.log('✅ Inventory chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update inventory chart:', error);
        if (inventoryChart) inventoryChart.hideLoading();
    }
}

async function updateInventoryPageTopChart(date) {
    if (!inventoryPageTopChart) {
        console.warn('⚠️ Inventory page top chart not initialized');
        return;
    }

    try {
        inventoryPageTopChart.showLoading();
        const data = await fetchData(`/api/inventory/top?date=${date}&limit=15`);
        inventoryPageTopChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No inventory data received for page top chart');
            return;
        }

        console.log('📊 Updating inventory page top chart with data:', data.length, 'items');

        // This uses the same options as the original inventory chart
        inventoryPageTopChart.setOption({
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.98)',
                borderColor: '#E0E0E0',
                borderWidth: 1,
                textStyle: {
                    color: '#333333',
                    fontSize: 12,
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                },
                padding: [8, 12],
                extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
                formatter: function(params) {
                    const item = params[0];
                    return `<div style="font-weight: 600; margin-bottom: 8px; color: #005BAC;">${item.name}</div>
                            <div style="display: flex; align-items: center; margin: 4px 0;">
                                <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                库存量: <strong>${item.value.toFixed(1)} 吨</strong>
                            </div>
                            <div style="color: #666666; font-size: 11px; margin-top: 4px;">排名: TOP ${item.dataIndex + 1}</div>`;
                }
            },
            grid: {
                left: '8%',
                right: '8%',
                bottom: '20%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.map(item => item.product_name),
                axisLabel: {
                    rotate: 45,
                    fontSize: 12,
                    color: '#666666',
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif',
                    interval: 0
                },
                axisLine: {
                    lineStyle: {
                        color: '#E0E0E0',
                        width: 1
                    }
                },
                axisTick: {
                    lineStyle: { color: '#E0E0E0' }
                }
            },
            yAxis: {
                type: 'value',
                name: '库存量 (吨)',
                nameTextStyle: {
                    color: '#005BAC',
                    fontSize: 12,
                    fontWeight: 600,
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                },
                axisLabel: {
                    color: '#666666',
                    fontSize: 12,
                    formatter: '{value}'
                },
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: '#005BAC',
                        width: 2
                    }
                },
                axisTick: {
                    lineStyle: { color: '#005BAC' }
                },
                splitLine: {
                    lineStyle: {
                        color: '#F5F5F5',
                        type: 'dashed'
                    }
                }
            },
            series: [{
                name: '库存量',
                type: 'bar',
                data: data.map(item => item.inventory_level),
                barWidth: '60%',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#005BAC' },
                        { offset: 1, color: '#49A9E8' }
                    ]),
                    borderRadius: [4, 4, 0, 0],
                    shadowColor: 'rgba(0, 91, 172, 0.3)',
                    shadowBlur: 8,
                    shadowOffsetY: 2
                },
                emphasis: {
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#49A9E8' },
                            { offset: 1, color: '#005BAC' }
                        ]),
                        shadowBlur: 12,
                        shadowOffsetY: 4
                    }
                },
                label: {
                    show: true,  // 启用数据标签显示
                    position: 'top',
                    color: '#005BAC',
                    fontSize: 11,
                    fontWeight: 'bold',
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif',
                    formatter: function(params) {
                        const value = params.value;
                        // 使用T单位格式化显示：大于1000显示为T格式，否则显示整数
                        return value >= 1000 ? `${(value / 1000).toFixed(1)}T` : value.toFixed(0);
                    }
                }
            }]
        });

        console.log('✅ Inventory page top chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update inventory page top chart:', error);
        if (inventoryPageTopChart) inventoryPageTopChart.hideLoading();
    }
}

async function updateSalesPriceChart(startDate, endDate) {
    if (!salesPriceChart) {
        console.warn('⚠️ Sales price chart not initialized');
        return;
    }

    try {
        salesPriceChart.showLoading();
        const data = await fetchData(`/api/trends/sales-price?start_date=${startDate}&end_date=${endDate}`);
        salesPriceChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No sales price data received');
            return;
        }

        console.log('📈 Updating sales price chart with data:', data.length, 'items');

        salesPriceChart.setOption({
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderColor: '#e5e5e7',
                borderWidth: 1,
                textStyle: {
                    color: '#1d1d1f',
                    fontSize: 14
                },
                formatter: function(params) {
                    let result = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].name}</div>`;
                    params.forEach(param => {
                        const color = param.color;
                        const value = param.seriesName === '销售量' ?
                            `${param.value.toFixed(1)} 吨` :
                            `¥${param.value.toFixed(0)}`;
                        result += `<div style="color: ${color};">● ${param.seriesName}: ${value}</div>`;
                    });
                    return result;
                }
            },
            legend: {
                data: ['销售量', '平均价格'],
                top: 10,
                textStyle: {
                    color: '#86868b',
                    fontSize: 14
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: '15%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: data.map(item => item.record_date),
                axisLabel: {
                    color: '#86868b',
                    fontSize: 12,
                    rotate: 45,
                    interval: 'auto',
                    formatter: function(value) {
                        // 改善日期格式显示，避免重叠
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                    }
                },
                axisLine: {
                    lineStyle: { color: '#e5e5e7' }
                }
            },
            yAxis: [
                {
                    type: 'value',
                    name: '销售量 (吨)',
                    position: 'left',
                    nameTextStyle: {
                        color: '#86868b',
                        fontSize: 12
                    },
                    axisLabel: {
                        color: '#86868b',
                        fontSize: 12,
                        formatter: '{value} 吨'
                    },
                    axisLine: {
                        lineStyle: { color: '#e5e5e7' }
                    },
                    splitLine: {
                        lineStyle: { color: '#f0f0f0' }
                    }
                },
                {
                    type: 'value',
                    name: '平均价格 (¥)',
                    position: 'right',
                    nameTextStyle: {
                        color: '#86868b',
                        fontSize: 12
                    },
                    axisLabel: {
                        color: '#86868b',
                        fontSize: 12,
                        formatter: '¥{value}'
                    },
                    axisLine: {
                        lineStyle: { color: '#e5e5e7' }
                    }
                }
            ],
            series: [
                {
                    name: '销售量',
                    type: 'bar',
                    data: data.map(item => item.total_sales),
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#34c759' },
                            { offset: 1, color: '#30d158' }
                        ]),
                        borderRadius: [4, 4, 0, 0]
                    },
                    emphasis: {
                        itemStyle: {
                            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                                { offset: 0, color: '#28a745' },
                                { offset: 1, color: '#34c759' }
                            ])
                        }
                    }
                },
                {
                    name: '平均价格',
                    type: 'line',
                    yAxisIndex: 1,
                    data: data.map(item => item.avg_price),
                    lineStyle: {
                        color: '#ff9500',
                        width: 3
                    },
                    itemStyle: {
                        color: '#ff9500',
                        borderWidth: 2,
                        borderColor: '#fff'
                    },
                    symbol: 'circle',
                    symbolSize: 8,
                    smooth: true
                }
            ]
        });

        console.log('✅ Sales price chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update sales price chart:', error);
        if (salesPriceChart) salesPriceChart.hideLoading();
    }
}

async function updateRatioTrendChart(startDate, endDate) {
    if (!ratioTrendChart) {
        console.warn('⚠️ Ratio trend chart not initialized');
        return;
    }

    try {
        ratioTrendChart.showLoading();
        const data = await fetchData(`/api/trends/ratio?start_date=${startDate}&end_date=${endDate}`);
        ratioTrendChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No ratio trend data received');
            return;
        }

        console.log('📊 Updating ratio trend chart with data:', data.length, 'items');

        // 过滤掉null值的数据
        const validData = data.filter(item => item.ratio !== null && item.ratio !== undefined);

        ratioTrendChart.setOption({
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.98)',
                borderColor: '#E0E0E0',
                borderWidth: 1,
                textStyle: {
                    color: '#333333',
                    fontSize: 12,
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                },
                padding: [8, 12],
                extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
                formatter: function(params) {
                    const item = params[0];
                    return `<div style="font-weight: 600; margin-bottom: 8px;">${item.axisValue}</div>
                            <div style="display: flex; align-items: center; margin: 4px 0;">
                                <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                产销率: <strong>${item.value ? item.value.toFixed(1) : '--'}%</strong>
                            </div>`;
                }
            },
            xAxis: {
                type: 'category',
                data: validData.map(item => item.record_date),
                axisLine: { lineStyle: { color: '#E0E0E0' } },
                axisLabel: { color: '#666666', fontSize: 12 }
            },
            yAxis: {
                type: 'value',
                name: '产销率 (%)',
                nameTextStyle: {
                    color: '#005BAC',
                    fontSize: 12,
                    fontWeight: 600
                },
                min: 0,
                max: function(value) {
                    return Math.max(value.max * 1.1, 100);
                },
                axisLine: { show: true, lineStyle: { color: '#005BAC', width: 2 } },
                axisLabel: { color: '#666666', fontSize: 12 },
                splitLine: { lineStyle: { color: '#F5F5F5', type: 'dashed' } }
            },
            series: [{
                name: '产销率',
                type: 'line',
                data: validData.map(item => item.ratio),
                lineStyle: {
                    color: '#D92E2E',
                    width: 3,
                    shadowColor: 'rgba(217, 46, 46, 0.3)',
                    shadowBlur: 6,
                    shadowOffsetY: 2
                },
                itemStyle: {
                    color: '#D92E2E',
                    borderWidth: 3,
                    borderColor: '#ffffff'
                },
                symbol: 'circle',
                symbolSize: 6,
                smooth: true,
                // 添加平均线标注
                markLine: {
                    silent: true,
                    lineStyle: {
                        color: '#005BAC',
                        type: 'dashed',
                        width: 2,
                        opacity: 0.6
                    },
                    label: {
                        position: 'end',
                        color: '#005BAC',
                        fontSize: 11,
                        fontWeight: 600
                    },
                    data: [
                        {
                            type: 'average',
                            name: '平均产销率'
                        }
                    ]
                }
            }]
        });

        console.log('✅ Ratio trend chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update ratio trend chart:', error);
        if (ratioTrendChart) ratioTrendChart.hideLoading();
    }
}

// 更新产销率分析页面的图表
async function updateProductionRatioChart(startDate, endDate) {
    if (!productionRatioChart) {
        console.warn('⚠️ Production ratio chart not initialized');
        return;
    }

    try {
        productionRatioChart.showLoading();
        const data = await fetchData(`/api/trends/ratio?start_date=${startDate}&end_date=${endDate}`);
        productionRatioChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No production ratio data received');
            return;
        }

        console.log('📊 Updating production ratio chart with data:', data.length, 'items');

        // 过滤掉null值的数据
        const validData = data.filter(item => item.ratio !== null && item.ratio !== undefined);

        productionRatioChart.setOption({
            ...professionalTheme,
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.98)',
                borderColor: '#E0E0E0',
                borderWidth: 1,
                textStyle: {
                    color: '#333333',
                    fontSize: 12,
                    fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                },
                padding: [8, 12],
                extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
                formatter: function(params) {
                    const item = params[0];
                    const ratio = item.value;
                    const status = ratio >= 100 ? '库存消耗' : '库存积累';
                    const statusColor = ratio >= 100 ? '#34c759' : '#ff9500';
                    const statusIcon = ratio >= 100 ? '📉' : '📈';
                    return `<div style="font-weight: 600; margin-bottom: 8px; color: #005BAC;">${item.axisValue}</div>
                            <div style="display: flex; align-items: center; margin: 4px 0;">
                                <span style="display: inline-block; width: 10px; height: 10px; background: ${statusColor}; border-radius: 50%; margin-right: 8px;"></span>
                                产销率: <strong style="color: ${statusColor};">${ratio ? ratio.toFixed(1) : '--'}%</strong>
                            </div>
                            <div style="color: ${statusColor}; font-size: 11px; margin-top: 4px;">
                                ${statusIcon} ${status} ${ratio >= 100 ? '(销量>产量)' : '(销量<产量)'}
                            </div>
                            <div style="color: #666; font-size: 10px; margin-top: 4px; border-top: 1px solid #eee; padding-top: 4px;">
                                100%为基准线：>100%表示库存消耗，<100%表示库存积累
                            </div>`;
                }
            },
            xAxis: {
                type: 'category',
                data: validData.map(item => item.record_date),
                axisLine: { lineStyle: { color: '#E0E0E0', width: 1 } },
                axisTick: { lineStyle: { color: '#E0E0E0' } },
                axisLabel: {
                    color: '#666666',
                    fontSize: 12,
                    rotate: 45,
                    interval: 'auto',
                    formatter: function(value) {
                        // 改善日期格式显示，避免重叠
                        const date = new Date(value);
                        return `${date.getMonth() + 1}/${date.getDate()}`;
                    }
                }
            },
            yAxis: {
                type: 'value',
                name: '产销率 (%)',
                nameTextStyle: {
                    color: '#005BAC',
                    fontSize: 12,
                    fontWeight: 600
                },
                min: 0,
                max: function(value) {
                    return Math.max(value.max * 1.1, 100);
                },
                axisLine: { show: true, lineStyle: { color: '#005BAC', width: 2 } },
                axisTick: { lineStyle: { color: '#005BAC' } },
                axisLabel: { color: '#666666', fontSize: 12 },
                splitLine: { lineStyle: { color: '#F5F5F5', type: 'dashed' } }
            },
            series: [{
                name: '产销率',
                type: 'line',
                data: validData.map(item => item.ratio),
                lineStyle: {
                    color: '#005BAC',
                    width: 3,
                    shadowColor: 'rgba(0, 91, 172, 0.3)',
                    shadowBlur: 6,
                    shadowOffsetY: 2
                },
                itemStyle: {
                    color: function(params) {
                        const ratio = params.value;
                        return ratio >= 100 ? '#34c759' : '#ff9500';
                    },
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    shadowColor: 'rgba(0, 91, 172, 0.4)',
                    shadowBlur: 8
                },
                symbol: 'circle',
                symbolSize: 8,
                smooth: true,
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(217, 46, 46, 0.3)' },
                        { offset: 1, color: 'rgba(217, 46, 46, 0.05)' }
                    ])
                },
                // 添加标注线
                markLine: {
                    silent: true,
                    lineStyle: {
                        color: '#005BAC',
                        type: 'dashed',
                        width: 2,
                        opacity: 0.6
                    },
                    label: {
                        position: 'end',
                        color: '#005BAC',
                        fontSize: 11,
                        fontWeight: 600
                    },
                    data: [
                        {
                            type: 'average',
                            name: '平均产销率',
                            lineStyle: { color: '#005BAC', type: 'dashed', width: 1 },
                            label: {
                                color: '#005BAC',
                                formatter: '平均: {c}%',
                                position: 'insideEndBottom'
                            }
                        },
                        {
                            yAxis: 100,
                            name: '100%基准线',
                            lineStyle: { color: '#D92E2E', type: 'solid', width: 2 },
                            label: {
                                color: '#D92E2E',
                                formatter: '100%基准线 (库存平衡点)',
                                position: 'insideEndTop'
                            }
                        }
                    ]
                },
                // 添加峰值标注
                markPoint: {
                    symbol: 'pin',
                    symbolSize: 50,
                    itemStyle: {
                        color: '#D92E2E'
                    },
                    label: {
                        color: '#ffffff',
                        fontSize: 11,
                        fontWeight: 600
                    },
                    data: [
                        {
                            type: 'max',
                            name: '最高产销率',
                            label: {
                                formatter: '峰值\n{c}%'
                            }
                        }
                    ]
                }
            }]
        });

        console.log('✅ Production ratio chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update production ratio chart:', error);
        if (productionRatioChart) productionRatioChart.hideLoading();
    }
}

// 更新产销率分析页面的统计数据
async function updateProductionRatioStats(startDate, endDate) {
    try {
        const data = await fetchData(`/api/production/ratio-stats?start_date=${startDate}&end_date=${endDate}`);

        const productionAvgRatio = document.getElementById('production-avg-ratio');
        const productionMinRatio = document.getElementById('production-min-ratio');
        const productionMaxRatio = document.getElementById('production-max-ratio');

        if (productionAvgRatio && data) {
            productionAvgRatio.textContent = (data.avg_ratio || 0).toFixed(1) + '%';
            if (productionMinRatio) productionMinRatio.textContent = (data.min_ratio || 0).toFixed(1) + '%';
            if (productionMaxRatio) productionMaxRatio.textContent = (data.max_ratio || 0).toFixed(1) + '%';
        }

        console.log('✅ Production ratio stats updated:', data);
    } catch (error) {
        console.error('❌ Failed to update production ratio stats:', error);
    }
}

async function updateSummaryCards(startDate, endDate) {
    try {
        const data = await fetchData(`/api/summary?start_date=${startDate}&end_date=${endDate}`);

        if (data) {
            // Update real-time analysis page cards
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
        }
    } catch (error) {
        console.error('❌ Failed to update summary cards:', error);
    }
}

// --- SPARKLINE FUNCTIONS ---
function initializeSparklines() {
    console.log('🎨 Initializing sparklines...');

    // Initialize sparklines for summary page
    const salesSparklineEl = document.getElementById('sales-sparkline');
    const ratioSparklineEl = document.getElementById('ratio-sparkline');

    if (salesSparklineEl) {
        salesSparkline = echarts.init(salesSparklineEl);
        salesSparkline.setOption(getSparklineOption([20, 25, 30, 28, 35, 40, 38]));
    }

    if (ratioSparklineEl) {
        ratioSparkline = echarts.init(ratioSparklineEl);
        ratioSparkline.setOption(getSparklineOption([80, 85, 82, 88, 84, 86, 85], '#34c759'));
    }

    // Initialize sparklines for realtime page
    const realtimeSalesSparklineEl = document.getElementById('realtime-sales-sparkline');
    const realtimeRatioSparklineEl = document.getElementById('realtime-ratio-sparkline');

    if (realtimeSalesSparklineEl) {
        realtimeSalesSparkline = echarts.init(realtimeSalesSparklineEl);
        realtimeSalesSparkline.setOption(getSparklineOption([20, 25, 30, 28, 35, 40, 38]));
    }

    if (realtimeRatioSparklineEl) {
        realtimeRatioSparkline = echarts.init(realtimeRatioSparklineEl);
        realtimeRatioSparkline.setOption(getSparklineOption([80, 85, 82, 88, 84, 86, 85], '#34c759'));
    }
}

function getSparklineOption(data, color = '#ff9500') {
    return {
        grid: {
            left: 0,
            right: 0,
            top: 0,
            bottom: 0
        },
        xAxis: {
            type: 'category',
            show: false,
            data: data.map((_, index) => index)
        },
        yAxis: {
            type: 'value',
            show: false
        },
        series: [{
            type: 'line',
            data: data,
            smooth: true,
            symbol: 'none',
            lineStyle: {
                color: color,
                width: 2
            },
            areaStyle: {
                color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [{
                        offset: 0,
                        color: color + '40'
                    }, {
                        offset: 1,
                        color: color + '10'
                    }]
                }
            }
        }]
    };
}

// --- CHART EXPORT FUNCTION ---
function exportChart(chartId) {
    const chart = window[chartId.replace('-', '_')]; // Convert ID to variable name
    if (chart) {
        const url = chart.getDataURL({
            type: 'png',
            pixelRatio: 2,
            backgroundColor: '#fff'
        });

        const link = document.createElement('a');
        link.download = `${chartId}-${new Date().toISOString().split('T')[0]}.png`;
        link.href = url;
        link.click();
    }
}

// --- CHART INITIALIZATION FUNCTION ---
function initializeCharts() {
    console.log('🎨 Initializing charts...');

    // Check if ECharts is available
    if (typeof echarts === 'undefined') {
        console.error('❌ ECharts library not loaded');
        return false;
    }

    try {
        // 等待CSS完全加载和容器尺寸计算完成
        return new Promise(async (resolve) => {
            // 首先等待样式表完全加载
            await waitForStylesLoaded();

            // 使用requestAnimationFrame确保渲染完成
            requestAnimationFrame(() => {
                setTimeout(() => {
                    initializeChartsInternal();
                    resolve(true);
                }, 150); // 额外等待150ms确保CSS应用完成
            });
        });
    } catch (error) {
        console.error('❌ Chart initialization failed:', error);
        return false;
    }
}

// 内部图表初始化函数
function initializeChartsInternal() {
    console.log('🎨 Starting internal chart initialization...');

    // 实时分析页面的图表
    const inventoryChartElement = document.getElementById('inventory-top-chart');
    if (inventoryChartElement && isElementVisible(inventoryChartElement)) {
        // Dispose existing chart if any
        if (inventoryChart) {
            inventoryChart.dispose();
        }
        inventoryChart = echarts.init(inventoryChartElement, null, {
            width: 'auto',
            height: 400,
            renderer: 'canvas'
        });
        console.log('✅ Inventory chart initialized');
    }

    const salesPriceChartElement = document.getElementById('sales-price-chart');
    if (salesPriceChartElement && isElementVisible(salesPriceChartElement)) {
        if (salesPriceChart) {
            salesPriceChart.dispose();
        }
        salesPriceChart = echarts.init(salesPriceChartElement, null, {
            width: 'auto',
            height: 400,
            renderer: 'canvas'
        });
        console.log('✅ Sales price chart initialized');
    }

    const ratioTrendChartElement = document.getElementById('ratio-trend-chart');
    if (ratioTrendChartElement && isElementVisible(ratioTrendChartElement)) {
        if (ratioTrendChart) {
            ratioTrendChart.dispose();
        }
        ratioTrendChart = echarts.init(ratioTrendChartElement, null, {
            width: 'auto',
            height: 400,
            renderer: 'canvas'
        });
        console.log('✅ Ratio trend chart initialized');
    }

    // 其他页面的图表
    const inventoryTrendChartElement = document.getElementById('inventory-trend-chart');
    if (inventoryTrendChartElement && isElementVisible(inventoryTrendChartElement)) {
        if (inventoryTrendChart) {
            inventoryTrendChart.dispose();
        }
        inventoryTrendChart = echarts.init(inventoryTrendChartElement, null, {
            width: 'auto',
            height: 400,
            renderer: 'canvas'
        });
        console.log('✅ Inventory trend chart initialized');
    }

    const productionRatioChartElement = document.getElementById('production-ratio-chart');
    if (productionRatioChartElement && isElementVisible(productionRatioChartElement)) {
        if (productionRatioChart) {
            productionRatioChart.dispose();
        }
        productionRatioChart = echarts.init(productionRatioChartElement, null, {
            width: 'auto',
            height: 400,
            renderer: 'canvas'
        });
        console.log('✅ Production ratio chart initialized');
    }

    const salesTrendChartElement = document.getElementById('sales-trend-chart');
    if (salesTrendChartElement && isElementVisible(salesTrendChartElement)) {
        if (salesTrendChart) {
            salesTrendChart.dispose();
        }
        salesTrendChart = echarts.init(salesTrendChartElement, null, {
            width: 'auto',
            height: 400,
            renderer: 'canvas'
        });
        console.log('✅ Sales trend chart initialized');
    }

    // 初始化专业级图表
    initProfessionalCharts();

    // 初始化库存页面图表
    initializeInventoryPageCharts();

    // Add window resize handler to prevent chart deformation
    if (!window.chartResizeHandlerAdded) {
        window.addEventListener('resize', () => {
            if (inventoryChart) inventoryChart.resize();
            if (salesPriceChart) salesPriceChart.resize();
            if (ratioTrendChart) ratioTrendChart.resize();
            if (inventoryTrendChart) inventoryTrendChart.resize();
            if (productionRatioChart) productionRatioChart.resize();
            if (salesTrendChart) salesTrendChart.resize();
            // 专业级图表响应式处理
            if (categoryPieChart) categoryPieChart.resize();
            if (categoryBarChart) categoryBarChart.resize();
            if (categoryPriceChart) categoryPriceChart.resize();
            if (multiSeriesChart) multiSeriesChart.resize();
            if (inventoryTurnoverChart) inventoryTurnoverChart.resize();
            // 库存页面图表响应式处理
            if (inventoryPieChart) inventoryPieChart.resize();
            if (productionRatioTrendChart) productionRatioTrendChart.resize();
        });
        window.chartResizeHandlerAdded = true;
    }

    console.log('🎨 Chart initialization complete:', {
        inventoryChart: !!inventoryChart,
        salesPriceChart: !!salesPriceChart,
        ratioTrendChart: !!ratioTrendChart,
        inventoryTrendChart: !!inventoryTrendChart,
        productionRatioChart: !!productionRatioChart,
        salesTrendChart: !!salesTrendChart,
        categoryPieChart: !!categoryPieChart,
        categoryBarChart: !!categoryBarChart,
        categoryPriceChart: !!categoryPriceChart,
        multiSeriesChart: !!multiSeriesChart,
        inventoryTurnoverChart: !!inventoryTurnoverChart
    });
}

// 检查元素是否可见且有有效尺寸的辅助函数
function isElementVisible(element) {
    if (!element) return false;

    const rect = element.getBoundingClientRect();
    const computedStyle = window.getComputedStyle(element);

    // 检查元素是否可见且有有效尺寸
    const isVisible = rect.width > 0 && rect.height > 0 &&
                     computedStyle.display !== 'none' &&
                     computedStyle.visibility !== 'hidden' &&
                     computedStyle.opacity !== '0';

    if (!isVisible) {
        console.warn(`⚠️ Element ${element.id} is not visible or has zero dimensions:`, {
            width: rect.width,
            height: rect.height,
            display: computedStyle.display,
            visibility: computedStyle.visibility,
            opacity: computedStyle.opacity
        });
    }

    return isVisible;
}

// 等待CSS完全加载的函数
function waitForStylesLoaded() {
    return new Promise((resolve) => {
        // 检查是否所有样式表都已加载
        const checkStylesLoaded = () => {
            const styleSheets = Array.from(document.styleSheets);
            const allLoaded = styleSheets.every(sheet => {
                try {
                    // 尝试访问cssRules来检查样式表是否已加载
                    return sheet.cssRules !== null;
                } catch (e) {
                    // 如果是跨域样式表，可能会抛出异常，但这通常意味着它已加载
                    return true;
                }
            });

            if (allLoaded) {
                console.log('✅ All stylesheets loaded');
                resolve(true);
            } else {
                console.log('⏳ Waiting for stylesheets to load...');
                setTimeout(checkStylesLoaded, 50);
            }
        };

        // 如果文档已经完全加载，直接检查
        if (document.readyState === 'complete') {
            setTimeout(checkStylesLoaded, 10);
        } else {
            // 否则等待load事件
            window.addEventListener('load', () => {
                setTimeout(checkStylesLoaded, 10);
            });
        }
    });
}

// 强制重新渲染所有图表的函数
function forceResizeAllCharts() {
    console.log('🔄 Force resizing all charts...');

    const charts = [
        inventoryChart, salesPriceChart, ratioTrendChart, inventoryTrendChart,
        productionRatioChart, salesTrendChart, categoryPieChart, categoryBarChart,
        categoryPriceChart, multiSeriesChart, inventoryTurnoverChart,
        inventoryPageTopChart, inventoryPieChart, productionRatioTrendChart, priceFrequencyChart,
        priceMajorChangesChart
    ];

    // 同时更新全局变量引用
    window.inventoryPieChart = inventoryPieChart;
    window.productionRatioTrendChart = productionRatioTrendChart;

    charts.forEach((chart, index) => {
        if (chart && typeof chart.resize === 'function') {
            try {
                chart.resize();
                console.log(`✅ Chart ${index + 1} resized successfully`);
            } catch (error) {
                console.warn(`⚠️ Failed to resize chart ${index + 1}:`, error);
            }
        }
    });

    console.log('✅ All charts resize completed');
}

// 专门的库存页面图表初始化函数
async function initializeInventoryPageCharts() {
    console.log('📊 Initializing inventory page charts...');

    try {
        // 等待DOM和CSS完全准备好
        await waitForStylesLoaded();
        await new Promise(resolve => requestAnimationFrame(resolve));

        // 初始化库存页面TOP15图表（使用新的ID）
        const inventoryPageTopElement = document.getElementById('inventory-page-top-chart');
        if (inventoryPageTopElement) {
            // 即使元素不可见也尝试初始化，ECharts可以处理隐藏的容器
            if (inventoryPageTopChart) inventoryPageTopChart.dispose();
            inventoryPageTopChart = echarts.init(inventoryPageTopElement);
            window.inventoryPageTopChart = inventoryPageTopChart;
            console.log('✅ Inventory page top chart initialized (may be hidden)');
        } else {
            console.warn('⚠️ Inventory page top chart element not found');
        }

        // 初始化库存页面饼状图（使用新的ID）
        const inventoryPagePieElement = document.getElementById('inventory-page-pie-chart');
        if (inventoryPagePieElement) {
            // 即使元素不可见也尝试初始化，ECharts可以处理隐藏的容器
            if (inventoryPieChart) inventoryPieChart.dispose();
            inventoryPieChart = echarts.init(inventoryPagePieElement);
            window.inventoryPieChart = inventoryPieChart;

            // 设置饼状图的基本配置
            const pieOption = {
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c}T ({d}%)'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    textStyle: {
                        fontSize: 12,
                        color: '#666666'
                    }
                },
                series: [
                    {
                        name: '库存分布',
                        type: 'pie',
                        radius: ['40%', '70%'],
                        avoidLabelOverlap: false,
                        itemStyle: {
                            borderRadius: 10,
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        label: {
                            show: false,
                            position: 'center'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: '18',
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: []
                    }
                ]
            };
            inventoryPieChart.setOption(pieOption);
            console.log('✅ Inventory page pie chart initialized with options (may be hidden)');
        } else {
            console.warn('⚠️ Inventory page pie chart element not found');
        }

        // 初始化产销率趋势图
        const productionRatioTrendElement = document.getElementById('production-ratio-trend-chart');
        if (productionRatioTrendElement) {
            // 即使元素不可见也尝试初始化，ECharts可以处理隐藏的容器
            if (productionRatioTrendChart) productionRatioTrendChart.dispose();
            productionRatioTrendChart = echarts.init(productionRatioTrendElement);
            window.productionRatioTrendChart = productionRatioTrendChart;

            // 设置产销率趋势图的基本配置
            const trendOption = {
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: 'rgba(255, 255, 255, 0.98)',
                    borderColor: '#E0E0E0',
                    borderWidth: 1,
                    textStyle: {
                        color: '#333333',
                        fontSize: 12,
                        fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
                    },
                    padding: [8, 12],
                    extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
                    formatter: function(params) {
                        const item = params[0];
                        const ratio = item.value;
                        const status = ratio >= 100 ? '库存消耗' : '库存积累';
                        const statusColor = ratio >= 100 ? '#34c759' : '#ff9500';
                        const statusIcon = ratio >= 100 ? '📉' : '📈';
                        return `<div style="font-weight: 600; margin-bottom: 8px; color: #005BAC;">${item.axisValue}</div>
                                <div style="display: flex; align-items: center; margin: 4px 0;">
                                    <span style="display: inline-block; width: 10px; height: 10px; background: ${statusColor}; border-radius: 50%; margin-right: 8px;"></span>
                                    产销率: <strong style="color: ${statusColor};">${ratio ? ratio.toFixed(1) : '--'}%</strong>
                                </div>
                                <div style="color: ${statusColor}; font-size: 11px; margin-top: 4px;">
                                    ${statusIcon} ${status} ${ratio >= 100 ? '(销量>产量)' : '(销量<产量)'}
                                </div>
                                <div style="color: #666; font-size: 10px; margin-top: 4px; border-top: 1px solid #eee; padding-top: 4px;">
                                    100%为基准线：>100%表示库存消耗，<100%表示库存积累
                                </div>`;
                    }
                },
                grid: {
                    left: '8%',
                    right: '8%',
                    bottom: '15%',
                    top: '15%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: [],
                    axisLine: { lineStyle: { color: '#E0E0E0', width: 1 } },
                    axisTick: { lineStyle: { color: '#E0E0E0' } },
                    axisLabel: {
                        color: '#666666',
                        fontSize: 12,
                        rotate: 45,
                        interval: 'auto',
                        formatter: function(value) {
                            const date = new Date(value);
                            return `${date.getMonth() + 1}/${date.getDate()}`;
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '产销率 (%)',
                    nameTextStyle: {
                        color: '#005BAC',
                        fontSize: 12,
                        fontWeight: 600
                    },
                    min: 0,
                    max: function(value) {
                        return Math.max(value.max * 1.1, 120);
                    },
                    axisLine: { show: true, lineStyle: { color: '#005BAC', width: 2 } },
                    axisTick: { lineStyle: { color: '#005BAC' } },
                    axisLabel: { color: '#666666', fontSize: 12 },
                    splitLine: { lineStyle: { color: '#F5F5F5', type: 'dashed' } }
                },
                series: [{
                    name: '产销率',
                    type: 'line',
                    data: [],
                    lineStyle: {
                        color: function(params) {
                            return params.value >= 100 ? '#34c759' : '#ff9500';
                        },
                        width: 3
                    },
                    markLine: {
                        silent: true,
                        lineStyle: {
                            color: '#005BAC',
                            type: 'dashed',
                            width: 2
                        },
                        label: {
                            show: true,
                            position: 'end',
                            formatter: '基准线 100%',
                            color: '#005BAC',
                            fontSize: 12
                        },
                        data: [
                            {
                                yAxis: 100,
                                name: '基准线'
                            }
                        ]
                    },
                    markArea: {
                        silent: true,
                        itemStyle: {
                            color: 'rgba(52, 199, 89, 0.1)'
                        },
                        data: [
                            [
                                {
                                    yAxis: 100,
                                    name: '库存消耗区间'
                                },
                                {
                                    yAxis: 'max'
                                }
                            ]
                        ]
                    }
                }]
            };
            productionRatioTrendChart.setOption(trendOption);
            console.log('✅ Production ratio trend chart initialized with options (may be hidden)');
        } else {
            console.warn('⚠️ Production ratio trend chart element not found');
        }

        return true;
    } catch (error) {
        console.error('❌ Failed to initialize inventory page charts:', error);
        return false;
    }
}

// Tab switching function
function showTab(tabName) {
    console.log('🔄 Switching to tab:', tabName);

    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all nav tabs
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab content
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked nav tab
    const clickedNavTab = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (clickedNavTab) {
        clickedNavTab.classList.add('active');
    }

    // Load data for specific tabs
    const startDate = '2025-06-01';
    const endDate = '2025-06-26';

    switch(tabName) {
        case 'production':
            // 产销率分析页面 - 确保图表已初始化并加载数据
            console.log('📊 Switching to production page...');
            setTimeout(() => {
                // 确保图表容器可见后再初始化
                const chartElement = document.getElementById('production-ratio-chart');
                if (chartElement) {
                    console.log('🔧 Found production ratio chart element, initializing...');

                    // 强制重新初始化图表
                    if (productionRatioChart) {
                        productionRatioChart.dispose();
                        productionRatioChart = null;
                    }

                    productionRatioChart = echarts.init(chartElement, null, {
                        width: 'auto',
                        height: 400,
                        renderer: 'canvas'
                    });

                    console.log('✅ Production ratio chart initialized');

                    // 加载数据和统计信息
                    updateProductionRatioChart(startDate, endDate);
                    updateProductionRatioStats(startDate, endDate);
                } else {
                    console.warn('⚠️ Production ratio chart element not found');
                }
            }, 100);
            break;
        case 'realtime':
            // 实时分析页面 - 确保图表已初始化并加载数据
            console.log('📊 Switching to realtime page...');
            setTimeout(() => {
                // 确保所有图表容器可见后再初始化
                const inventoryElement = document.getElementById('inventory-chart');
                const salesElement = document.getElementById('sales-price-chart');
                const ratioElement = document.getElementById('ratio-trend-chart');

                if (inventoryElement && !inventoryChart) {
                    inventoryChart = echarts.init(inventoryElement);
                }
                if (salesElement && !salesPriceChart) {
                    salesPriceChart = echarts.init(salesElement);
                }
                if (ratioElement && !ratioTrendChart) {
                    ratioTrendChart = echarts.init(ratioElement);
                }

                // 加载数据
                if (inventoryChart) updateInventoryChart(endDate);
                if (salesPriceChart) updateSalesPriceChart(startDate, endDate);
                if (ratioTrendChart) updateRatioTrendChart(startDate, endDate);
            }, 100);
            break;
        case 'inventory':
            // 库存情况页面 - 使用专门的初始化函数
            console.log('📊 Switching to inventory page...');

            // 延迟执行以确保DOM完全渲染
            setTimeout(async () => {
                // 使用专门的库存页面图表初始化函数
                const success = await initializeInventoryPageCharts();

                if (success) {
                    // 加载数据
                    updateInventoryAnalytics(endDate);
                    if (window.productionRatioTrendChart) {
                        updateProductionRatioTrendChart(startDate, endDate);
                    }

                    // 强制调整图表大小
                    setTimeout(() => {
                        if (window.inventoryPageTopChart) window.inventoryPageTopChart.resize();
                        if (window.inventoryPieChart) window.inventoryPieChart.resize();
                        if (window.productionRatioTrendChart) window.productionRatioTrendChart.resize();
                    }, 200);
                } else {
                    console.warn('⚠️ Failed to initialize inventory page charts');
                }
            }, 100);
            break;
        case 'sales':
            // 销售情况页面
            if (salesTrendChart) updateSalesPriceChart(startDate, endDate);
            break;
        case 'pricing':
            // 价格波动分析页面
            loadPriceAdjustments();
            break;
    }

    // 在切换选项卡后，延迟执行resize以确保DOM渲染完成
    setTimeout(() => {
        console.log(`Resizing charts for tab: ${tabName}`);
        if (tabName === 'inventory') {
            // 库存页面使用标准图表变量
            if (window.inventoryPageTopChart) window.inventoryPageTopChart.resize();
            if (window.inventoryPieChart) window.inventoryPieChart.resize();
            if (window.productionRatioTrendChart) window.productionRatioTrendChart.resize();
        } else if (tabName === 'production') { // 对应“产销率分析”
            if (window.productionRatioChart) window.productionRatioChart.resize();
        } else if (tabName === 'sales') {
            if (window.salesTrendChart) window.salesTrendChart.resize();
            if (window.salesPriceChart) window.salesPriceChart.resize(); // 假设 salesDistributionChart 是 salesPriceChart
        }
        // 为其他包含图表的选项卡也添加resize逻辑
        if (tabName === 'realtime') {
            if (window.inventoryChart) window.inventoryChart.resize();
            if (window.salesPriceChart) window.salesPriceChart.resize();
            if (window.ratioTrendChart) window.ratioTrendChart.resize();
        }
        if (tabName === 'pricing') {
            if (window.priceFrequencyChart) window.priceFrequencyChart.resize();
            if (window.priceMajorChangesChart) window.priceMajorChangesChart.resize();
        }
    }, 50);
}

// Export functions to global scope immediately
window.loadSummaryData = loadSummaryData;
window.loadDetailData = loadDetailData;
window.fetchData = fetchData;
window.updateInventoryChart = updateInventoryChart;
window.updateSalesPriceChart = updateSalesPriceChart;
window.updateRatioTrendChart = updateRatioTrendChart;
window.updateProductionRatioChart = updateProductionRatioChart;
window.updateProductionRatioStats = updateProductionRatioStats;
window.updateSummaryCards = updateSummaryCards;
window.initializeCharts = initializeCharts;
window.showTab = showTab;
window.initializeInventoryPageCharts = initializeInventoryPageCharts;

// Define loadAllData function and export it immediately
window.loadAllData = async function() {
    console.log('🔄 Loading all data automatically...');

    try {
        // Step 1: 加载摘要数据
        console.log('📊 Step 1: Loading summary data...');
        await loadSummaryData();
        console.log('✅ Step 1: Summary data loaded');

        // Step 2: 等待DOM完全准备好
        await new Promise(resolve => {
            if (document.readyState === 'complete') {
                resolve(true);
            } else {
                document.addEventListener('DOMContentLoaded', () => resolve(true));
            }
        });
        console.log('✅ Step 2: DOM ready');

        // Step 3: 初始化图表（如果还未初始化）
        console.log('🎨 Step 3: Initializing charts...');
        if (typeof window.initializeCharts === 'function') {
            let success = await window.initializeCharts();

            // 如果第一次初始化失败，重试一次
            if (!success) {
                console.warn('⚠️ First chart initialization failed, retrying...');
                await new Promise(resolve => setTimeout(resolve, 300));
                success = await window.initializeCharts();
            }

            if (success) {
                console.log('✅ Step 3: Charts initialized');
            } else {
                console.warn('⚠️ Step 3: Chart initialization failed after retry');
            }
        }

        // Step 4: 等待图表准备好
        await new Promise(resolve => setTimeout(resolve, 200));
        console.log('✅ Step 4: Charts ready');

        // Step 5: 加载图表数据
        console.log('📊 Step 5: Loading chart data...');
        const startDate = '2025-06-01';
        const endDate = '2025-06-26';

        const dataPromises = [
            updateSummaryCards(startDate, endDate)
        ];

        // Only add chart updates if charts are available
        if (inventoryChart) {
            dataPromises.push(updateInventoryChart(endDate));
        }
        if (salesPriceChart) {
            dataPromises.push(updateSalesPriceChart(startDate, endDate));
        }
        if (ratioTrendChart) {
            dataPromises.push(updateRatioTrendChart(startDate, endDate));
        }
        if (productionRatioChart) {
            dataPromises.push(updateProductionRatioChart(startDate, endDate));
        }
        // 库存页面相关数据加载 - 先确保图表已初始化
        dataPromises.push(loadInventorySummary(endDate));

        // 确保库存页面图表已初始化
        if (!inventoryPageTopChart || !inventoryPieChart || !productionRatioTrendChart) {
            console.log('🔧 Inventory page charts not initialized, initializing now...');
            const inventoryChartsSuccess = await initializeInventoryPageCharts();
            if (inventoryChartsSuccess) {
                console.log('✅ Inventory page charts initialized successfully');
            } else {
                console.warn('⚠️ Failed to initialize inventory page charts');
            }
        }

        if (inventoryPieChart) {
            dataPromises.push(updateInventoryPieChart(endDate));
        }
        if (productionRatioTrendChart) {
            dataPromises.push(updateProductionRatioTrendChart(startDate, endDate));
        }
        if (inventoryPageTopChart) {
            dataPromises.push(updateInventoryPageTopChart(endDate));
        }

        await Promise.allSettled(dataPromises);
        console.log('✅ All data loading completed');

        // Step 6: 强制重新渲染所有图表以确保正确显示
        console.log('🔄 Step 6: Force chart resize to ensure proper display...');
        setTimeout(() => {
            forceResizeAllCharts();
        }, 100);

    } catch (error) {
        console.error('❌ Error in loadAllData:', error);
        // Still try to load basic summary data
        try {
            await loadSummaryData();
            console.log('✅ Fallback: Basic summary data loaded');
        } catch (fallbackError) {
            console.error('❌ Fallback also failed:', fallbackError);
        }
    }
};

console.log('✅ Global functions exported:', {
    loadSummaryData: typeof window.loadSummaryData,
    loadDetailData: typeof window.loadDetailData,
    fetchData: typeof window.fetchData,
    loadAllData: typeof window.loadAllData,
    updateInventoryChart: typeof window.updateInventoryChart,
    updateSalesPriceChart: typeof window.updateSalesPriceChart,
    updateRatioTrendChart: typeof window.updateRatioTrendChart,
    updateProductionRatioChart: typeof window.updateProductionRatioChart,
    updateSummaryCards: typeof window.updateSummaryCards,
    initializeCharts: typeof window.initializeCharts
});

// initializeCharts is now available globally

document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM Content Loaded - Initializing application...');

    // --- DOM ELEMENTS ---
    const startDateInput = document.getElementById('start-date');
    const endDateInput = document.getElementById('end-date');
    const filterBtn = document.getElementById('filter-btn');
    const uploadBtn = document.getElementById('submit-btn');
    const fileInput = document.getElementById('excel-upload');
    const uploadStatusDiv = document.getElementById('upload-status');

    // --- 产品筛选器初始化 ---
    async function initializeProductFilter() {
        try {
            console.log('🔍 Initializing product filter...');
            const products = await fetchData('/api/products');
            const productFilter = document.getElementById('product-filter');

            if (products && productFilter) {
                // 清空现有选项
                productFilter.innerHTML = '<option value="">全部产品</option>';

                // 添加前20个产品作为示例
                products.slice(0, 20).forEach(product => {
                    const option = document.createElement('option');
                    option.value = product.product_id;
                    option.textContent = product.product_name;
                    productFilter.appendChild(option);
                });
                console.log('✅ Product filter initialized with', products.length, 'products');
            }
        } catch (error) {
            console.error('❌ Failed to load products for filter:', error);
        }
    }

    // --- DATA FETCHING & UPDATING ---
    // Note: These functions are now using the global versions defined above

    // --- FILE UPLOAD ---
    async function handleFileUpload() {
        const file = fileInput.files[0];
        if (!file) {
            uploadStatusDiv.textContent = 'Please select a file first.';
            return;
        }

        uploadStatusDiv.textContent = 'Uploading and processing...';
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok) {
                uploadStatusDiv.textContent = `Successfully processed file! Results: ${JSON.stringify(result.results)}`;
                // Refresh data after successful upload
                fetchAllData(); 
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            uploadStatusDiv.textContent = `Error: ${error.message}`;
            console.error('Upload failed:', error);
        }
    }

    // --- MAIN EXECUTION ---
    async function fetchAllData() {
        const startDate = startDateInput?.value || '2025-06-01';
        const endDate = endDateInput?.value || '2025-06-26';

        if (!startDate || !endDate) {
            console.warn('⚠️ Date inputs not found, using default dates');
        }

        console.log(`🔄 Fetching all data for ${startDate} to ${endDate}`);

        try {
            // 初始化专业图表（如果还未初始化）
            if (!salesPriceChart) {
                console.log('🎨 Initializing professional sales-price chart...');
                initProfessionalSalesPriceChart();
            }

            if (!categoryPieChart) {
                console.log('🥧 Initializing category pie chart...');
                initCategoryPieChart();
            }

            if (!multiSeriesChart) {
                console.log('📊 Initializing multi-series chart...');
                initMultiSeriesChart();
            }

            // Ensure legacy charts are initialized before updating
            if (!inventoryChart || !ratioTrendChart) {
                console.log('🔧 Legacy charts not initialized, initializing now...');
                const initialized = initializeCharts();
                if (!initialized) {
                    console.error('❌ Failed to initialize legacy charts');
                    return;
                }
                // Wait a bit for charts to be ready
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // 使用专业级数据更新函数
            await updateProfessionalCharts(startDate, endDate);

            // 同时更新摘要数据
            await updateSummaryCards(startDate, endDate);

            console.log('✅ All professional data fetched successfully');
        } catch (error) {
            console.error('❌ Error fetching data:', error);
            showErrorMessage('数据加载失败，请检查网络连接');
        }
    }

    // --- EVENT LISTENERS ---
    if (filterBtn) {
        filterBtn.addEventListener('click', () => {
            console.log('🔄 Filter button clicked - updating professional charts...');
            fetchAllData();
        });
        console.log('✅ Professional filter button event listener added');
    }
    if (uploadBtn) {
        uploadBtn.addEventListener('click', handleFileUpload);
        console.log('✅ Upload button event listener added');
    }

    // 初始化产品筛选器
    initializeProductFilter();

    // 初始化价格分析功能
    setupPriceTableSearch();
    setupPriceFileUpload();

    // 初始化认证系统 (这会自动加载数据)
    console.log('🔐 Initializing authentication system...');
    initializeAuth();

    console.log('✅ Application initialization complete');
});

// 全局函数，供其他地方调用
window.loadData = async function() {
    const startDate = document.getElementById('start-date')?.value || '2025-06-01';
    const endDate = document.getElementById('end-date')?.value || '2025-06-26';

    try {
        const data = await fetchData(`/api/summary?start_date=${startDate}&end_date=${endDate}`);
        if (data) {
            if (document.getElementById('card-total-products')) {
                document.getElementById('card-total-products').textContent = data.total_products || 0;
                document.getElementById('card-days').textContent = data.days || 0;
                document.getElementById('card-total-sales').textContent = (data.total_sales / 1000 || 0).toFixed(1);
                document.getElementById('card-total-production').textContent = (data.total_production / 1000 || 0).toFixed(1);
                document.getElementById('card-sales-ratio').textContent = (data.sales_to_production_ratio || 0).toFixed(1) + '%';
            }
        }

        await updateInventoryChart(endDate);
        await updateSalesPriceChart(startDate, endDate);
        await updateRatioTrendChart(startDate, endDate);
    } catch (error) {
        console.error('Error loading data:', error);
    }
};

// Functions already exported globally above

// loadAllData function is now defined above in the global exports section

// ===== 专业级图表配置函数 =====

// 专业级ECharts主题配置 - 财经报告风格
const professionalTheme = {
    color: ['#005BAC', '#49A9E8', '#D92E2E', '#FF9500', '#28a745', '#6C757D', '#17a2b8'],
    backgroundColor: 'transparent',
    textStyle: {
        fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif',
        fontSize: 12,
        color: '#333333'
    },
    title: {
        textStyle: {
            color: '#333333',
            fontWeight: 700,
            fontSize: 16
        }
    },
    legend: {
        textStyle: {
            color: '#666666',
            fontSize: 12
        },
        itemWidth: 14,
        itemHeight: 14
    },
    grid: {
        left: '8%',
        right: '8%',
        bottom: '10%',
        top: '15%',
        containLabel: true,
        borderColor: '#E0E0E0'
    },
    xAxis: {
        axisLine: {
            lineStyle: {
                color: '#E0E0E0'
            }
        },
        axisTick: {
            lineStyle: {
                color: '#E0E0E0'
            }
        },
        axisLabel: {
            color: '#666666',
            fontSize: 12
        },
        splitLine: {
            lineStyle: {
                color: '#F5F5F5',
                type: 'dashed'
            }
        }
    },
    yAxis: {
        axisLine: {
            lineStyle: {
                color: '#E0E0E0'
            }
        },
        axisTick: {
            lineStyle: {
                color: '#E0E0E0'
            }
        },
        axisLabel: {
            color: '#666666',
            fontSize: 12
        },
        splitLine: {
            lineStyle: {
                color: '#F5F5F5',
                type: 'dashed'
            }
        }
    }
};

// 初始化专业级销售价格双轴图 - 财经报告风格
function initProfessionalSalesPriceChart() {
    console.log('🎨 Initializing professional sales-price chart...');

    if (salesPriceChart) {
        salesPriceChart.dispose();
    }

    const chartDom = document.getElementById('sales-price-chart');
    if (!chartDom) {
        console.warn('⚠️ Sales-price chart container not found');
        return;
    }

    salesPriceChart = echarts.init(chartDom);

    const option = {
        ...professionalTheme,
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                crossStyle: {
                    color: '#005BAC',
                    width: 1,
                    opacity: 0.6
                }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#E0E0E0',
            borderWidth: 1,
            textStyle: {
                color: '#333333',
                fontSize: 12,
                fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
            formatter: function(params) {
                let result = `<div style="font-weight: 600; margin-bottom: 8px;">${params[0].axisValue}</div>`;
                params.forEach(param => {
                    const unit = param.seriesName === '日销量' ? ' 吨' : ' 元/吨';
                    const value = param.value ? param.value.toFixed(2) : '--';
                    result += `<div style="margin: 4px 0;">
                        <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
                        ${param.seriesName}: <strong>${value}${unit}</strong>
                    </div>`;
                });
                return result;
            }
        },
        legend: {
            data: ['日销量', '平均价格'],
            top: 15,
            left: 'center',
            textStyle: {
                fontSize: 12,
                color: '#666666',
                fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
            },
            itemWidth: 14,
            itemHeight: 14
        },
        xAxis: {
            type: 'category',
            data: [],
            axisPointer: {
                type: 'shadow'
            },
            axisLine: {
                lineStyle: {
                    color: '#E0E0E0',
                    width: 1
                }
            },
            axisTick: {
                lineStyle: {
                    color: '#E0E0E0'
                }
            },
            axisLabel: {
                color: '#666666',
                fontSize: 12,
                fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
            }
        },
        yAxis: [
            {
                type: 'value',
                name: '销量 (吨)',
                nameTextStyle: {
                    color: '#005BAC',
                    fontSize: 12,
                    fontWeight: 600
                },
                position: 'left',
                axisLabel: {
                    formatter: '{value}',
                    color: '#666666',
                    fontSize: 12
                },
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: '#005BAC',
                        width: 2
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: '#005BAC'
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: '#F5F5F5',
                        type: 'dashed'
                    }
                }
            },
            {
                type: 'value',
                name: '价格 (元/吨)',
                nameTextStyle: {
                    color: '#D92E2E',
                    fontSize: 12,
                    fontWeight: 600
                },
                position: 'right',
                axisLabel: {
                    formatter: '{value}',
                    color: '#666666',
                    fontSize: 12
                },
                axisLine: {
                    show: true,
                    lineStyle: {
                        color: '#D92E2E',
                        width: 2
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: '#D92E2E'
                    }
                },
                splitLine: {
                    show: false
                }
            }
        ],
        series: [
            {
                name: '日销量',
                type: 'bar',
                yAxisIndex: 0,
                data: [],
                barWidth: '60%',
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#005BAC' },
                        { offset: 1, color: '#49A9E8' }
                    ]),
                    borderRadius: [3, 3, 0, 0]
                },
                emphasis: {
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#49A9E8' },
                            { offset: 1, color: '#005BAC' }
                        ])
                    }
                },
                label: {
                    show: false,
                    position: 'top',
                    color: '#333333',
                    fontSize: 11,
                    fontWeight: 500
                }
            },
            {
                name: '平均价格',
                type: 'line',
                yAxisIndex: 1,
                data: [],
                smooth: true,
                lineStyle: {
                    color: '#D92E2E',
                    width: 3,
                    shadowColor: 'rgba(217, 46, 46, 0.3)',
                    shadowBlur: 6,
                    shadowOffsetY: 2
                },
                itemStyle: {
                    color: '#D92E2E',
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    shadowColor: 'rgba(217, 46, 46, 0.4)',
                    shadowBlur: 8
                },
                symbol: 'circle',
                symbolSize: 6,
                smooth: true,
                // 专业级标注功能
                markPoint: {
                    symbol: 'pin',
                    symbolSize: 50,
                    itemStyle: {
                        color: '#D92E2E'
                    },
                    label: {
                        color: '#ffffff',
                        fontSize: 11,
                        fontWeight: 600
                    },
                    data: [
                        {
                            type: 'max',
                            name: '价格峰值',
                            label: {
                                formatter: '峰值\n{c}'
                            }
                        }
                    ]
                },
                markLine: {
                    silent: true,
                    lineStyle: {
                        color: '#D92E2E',
                        type: 'dashed',
                        width: 2,
                        opacity: 0.6
                    },
                    label: {
                        position: 'end',
                        color: '#D92E2E',
                        fontSize: 11,
                        fontWeight: 600
                    },
                    data: [
                        {
                            type: 'average',
                            name: '平均价格线'
                        }
                    ]
                }
            }
        ],
        // 专业级图形标注
        graphic: [
            {
                type: 'group',
                left: '15%',
                top: '25%',
                children: [
                    {
                        type: 'rect',
                        z: 100,
                        left: 0,
                        top: 0,
                        shape: {
                            width: 120,
                            height: 40
                        },
                        style: {
                            fill: 'rgba(0, 91, 172, 0.9)',
                            stroke: '#005BAC',
                            lineWidth: 1,
                            shadowColor: 'rgba(0, 91, 172, 0.3)',
                            shadowBlur: 8,
                            shadowOffsetY: 2
                        }
                    },

                    {
                        type: 'polygon',
                        z: 99,
                        shape: {
                            points: [[120, 20], [135, 15], [135, 25]]
                        },
                        style: {
                            fill: 'rgba(0, 91, 172, 0.9)',
                            stroke: '#005BAC'
                        }
                    }
                ]
            }
        ]
    };

    salesPriceChart.setOption(option);

    // 响应式处理
    window.addEventListener('resize', () => {
        if (salesPriceChart) {
            salesPriceChart.resize();
        }
    });
}

// 初始化产品类别饼图 - 专业财经报告风格
function initCategoryPieChart() {
    console.log('🥧 Initializing professional category pie chart...');

    if (categoryPieChart) {
        categoryPieChart.dispose();
    }

    const chartDom = document.getElementById('category-pie-chart');
    if (!chartDom) {
        console.warn('⚠️ Category pie chart container not found');
        return;
    }

    categoryPieChart = echarts.init(chartDom);

    const option = {
        ...professionalTheme,
        tooltip: {
            trigger: 'item',
            formatter: function(params) {
                return `<div style="font-weight: 600; margin-bottom: 6px;">${params.seriesName}</div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <span style="display: inline-block; width: 12px; height: 12px; background: ${params.color}; border-radius: 50%; margin-right: 8px;"></span>
                            ${params.name}: <strong>${params.value}%</strong>
                        </div>
                        <div style="color: #666666; font-size: 11px; margin-top: 4px;">占比: ${params.percent}%</div>`;
            },
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#E0E0E0',
            borderWidth: 1,
            textStyle: {
                color: '#333333',
                fontSize: 12
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;'
        },
        legend: {
            orient: 'vertical',
            left: '5%',
            top: 'middle',
            textStyle: {
                fontSize: 12,
                color: '#666666',
                fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
            },
            itemWidth: 14,
            itemHeight: 14
        },
        series: [
            {
                name: '产品类别分布',
                type: 'pie',
                radius: ['45%', '75%'],
                center: ['65%', '50%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 6,
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    shadowColor: 'rgba(0, 0, 0, 0.1)',
                    shadowBlur: 8,
                    shadowOffsetY: 2
                },
                label: {
                    show: true,
                    position: 'outside',
                    fontSize: 11,
                    fontWeight: 600,
                    color: '#333333',
                    formatter: function(params) {
                        return `${params.name}\n${params.percent}%`;
                    }
                },
                labelLine: {
                    show: true,
                    length: 15,
                    length2: 10,
                    lineStyle: {
                        color: '#E0E0E0',
                        width: 2
                    }
                },
                emphasis: {
                    itemStyle: {
                        shadowBlur: 15,
                        shadowOffsetY: 4,
                        shadowColor: 'rgba(0, 0, 0, 0.2)'
                    },
                    label: {
                        fontSize: 13,
                        fontWeight: 700
                    }
                },
                data: [
                    {
                        value: 45.2,
                        name: '冷冻食品',
                        itemStyle: { color: '#005BAC' }
                    },
                    {
                        value: 32.1,
                        name: '冷鲜食品',
                        itemStyle: { color: '#49A9E8' }
                    },
                    {
                        value: 22.7,
                        name: '加工食品',
                        itemStyle: { color: '#FF9500' }
                    }
                ]
            }
        ]
    };

    categoryPieChart.setOption(option);

    window.addEventListener('resize', () => {
        if (categoryPieChart) {
            categoryPieChart.resize();
        }
    });
}

// 专业级图表初始化函数
function initProfessionalCharts() {
    console.log('🎨 Initializing professional charts...');

    try {
        // 初始化专业级销售价格双轴图
        initProfessionalSalesPriceChart();

        // 初始化产品类别饼图
        initCategoryPieChart();

        // 初始化其他专业图表
        initCategoryBarChart();
        initCategoryPriceChart();
        initMultiSeriesChart();
        initInventoryTurnoverChart();

        console.log('✅ Professional charts initialized successfully');
    } catch (error) {
        console.error('❌ Professional charts initialization failed:', error);
    }
}

// 初始化类别柱状图
function initCategoryBarChart() {
    const chartDom = document.getElementById('category-bar-chart');
    if (!chartDom) return;

    if (categoryBarChart) categoryBarChart.dispose();
    categoryBarChart = echarts.init(chartDom);

    const option = {
        ...professionalTheme,
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#E0E0E0',
            borderWidth: 1,
            textStyle: {
                color: '#333333',
                fontSize: 12
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;'
        },
        legend: {
            data: ['2023年', '2024年'],
            top: 15,
            textStyle: {
                fontSize: 12,
                color: '#666666'
            }
        },
        xAxis: {
            type: 'category',
            data: ['冷冻食品', '冷鲜食品', '加工食品']
        },
        yAxis: {
            type: 'value',
            name: '销量 (千吨)',
            nameTextStyle: {
                color: '#005BAC',
                fontSize: 12,
                fontWeight: 600
            }
        },
        series: [
            {
                name: '2023年',
                type: 'bar',
                data: [62.5, 51.2, 42.8],
                itemStyle: { color: '#005BAC' }
            },
            {
                name: '2024年',
                type: 'bar',
                data: [68.3, 48.9, 45.1],
                itemStyle: { color: '#D92E2E' }
            }
        ]
    };

    categoryBarChart.setOption(option);
}

// 初始化类别价格图
function initCategoryPriceChart() {
    const chartDom = document.getElementById('category-price-chart');
    if (!chartDom) return;

    if (categoryPriceChart) categoryPriceChart.dispose();
    categoryPriceChart = echarts.init(chartDom);

    const option = {
        ...professionalTheme,
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#E0E0E0',
            borderWidth: 1,
            textStyle: {
                color: '#333333',
                fontSize: 12
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;'
        },
        xAxis: {
            type: 'category',
            data: ['冷冻食品', '冷鲜食品', '加工食品']
        },
        yAxis: {
            type: 'value',
            name: '平均价格 (元/吨)',
            nameTextStyle: {
                color: '#005BAC',
                fontSize: 12,
                fontWeight: 600
            }
        },
        series: [{
            name: '平均价格',
            type: 'line',
            data: [8500, 12000, 15800],
            lineStyle: {
                color: '#D92E2E',
                width: 3
            },
            itemStyle: {
                color: '#D92E2E',
                borderWidth: 3,
                borderColor: '#ffffff'
            },
            symbol: 'circle',
            symbolSize: 8
        }]
    };

    categoryPriceChart.setOption(option);
}



// 初始化库存周转图
function initInventoryTurnoverChart() {
    const chartDom = document.getElementById('inventory-turnover-chart');
    if (!chartDom) return;

    if (inventoryTurnoverChart) inventoryTurnoverChart.dispose();
    inventoryTurnoverChart = echarts.init(chartDom);

    const option = {
        ...professionalTheme,
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#E0E0E0',
            borderWidth: 1,
            textStyle: {
                color: '#333333',
                fontSize: 12
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;'
        },
        legend: {
            data: ['库存量', '周转率'],
            top: 15,
            textStyle: {
                fontSize: 12,
                color: '#666666'
            }
        },
        xAxis: {
            type: 'category',
            data: [] // 将通过API填充
        },
        yAxis: [
            {
                type: 'value',
                name: '库存量 (吨)',
                nameTextStyle: {
                    color: '#005BAC',
                    fontSize: 12,
                    fontWeight: 600
                },
                position: 'left'
            },
            {
                type: 'value',
                name: '周转率 (%)',
                nameTextStyle: {
                    color: '#D92E2E',
                    fontSize: 12,
                    fontWeight: 600
                },
                position: 'right'
            }
        ],
        series: [
            {
                name: '库存量',
                type: 'bar',
                yAxisIndex: 0,
                data: [],
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: '#005BAC' },
                        { offset: 1, color: '#49A9E8' }
                    ])
                }
            },
            {
                name: '周转率',
                type: 'line',
                yAxisIndex: 1,
                data: [],
                lineStyle: { color: '#D92E2E', width: 3 },
                itemStyle: { color: '#D92E2E' }
            }
        ]
    };

    inventoryTurnoverChart.setOption(option);
}

// 初始化多指标时间序列图
function initMultiSeriesChart() {
    console.log('📊 Initializing multi-series chart...');

    if (multiSeriesChart) {
        multiSeriesChart.dispose();
    }

    const chartDom = document.getElementById('multi-series-chart');
    if (!chartDom) {
        console.warn('⚠️ Multi-series chart container not found');
        return;
    }

    multiSeriesChart = echarts.init(chartDom);

    const option = {
        ...professionalTheme,
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e9ecef',
            borderWidth: 1
        },
        legend: {
            data: ['产量', '销量', '库存'],
            top: 10,
            textStyle: {
                fontSize: 12,
                color: '#6C757D'
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: [],
            axisLine: {
                lineStyle: {
                    color: '#e9ecef'
                }
            },
            axisLabel: {
                color: '#6C757D',
                fontSize: 11
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: '{value} 吨',
                color: '#6C757D',
                fontSize: 11
            },
            splitLine: {
                lineStyle: {
                    color: '#f8f9fa'
                }
            }
        },
        series: [
            {
                name: '产量',
                type: 'line',
                stack: 'Total',
                areaStyle: {
                    opacity: 0.3
                },
                lineStyle: {
                    width: 2
                },
                data: []
            },
            {
                name: '销量',
                type: 'line',
                stack: 'Total',
                areaStyle: {
                    opacity: 0.3
                },
                lineStyle: {
                    width: 2
                },
                data: []
            },
            {
                name: '库存',
                type: 'line',
                areaStyle: {
                    opacity: 0.2
                },
                lineStyle: {
                    width: 2
                },
                data: []
            }
        ]
    };

    multiSeriesChart.setOption(option);

    window.addEventListener('resize', () => {
        if (multiSeriesChart) {
            multiSeriesChart.resize();
        }
    });
}

// 专业级数据更新函数
async function updateProfessionalCharts(startDate, endDate) {
    console.log('🔄 Updating professional charts with date range:', startDate, 'to', endDate);

    try {
        // 显示加载状态
        showChartsLoading();

        // 并行获取所有需要的数据
        const [salesPriceData, inventoryData, ratioData] = await Promise.all([
            fetchData(`/api/trends/sales-price?start_date=${startDate}&end_date=${endDate}`),
            fetchData(`/api/inventory/top?date=${endDate}&limit=15`),
            fetchData(`/api/trends/ratio?start_date=${startDate}&end_date=${endDate}`)
        ]);

        // 更新销售价格双轴图
        if (salesPriceChart && salesPriceData) {
            const dates = salesPriceData.map(item => item.record_date);
            const sales = salesPriceData.map(item => parseFloat(item.total_sales || 0));
            const prices = salesPriceData.map(item => parseFloat(item.avg_price || 0));

            salesPriceChart.setOption({
                xAxis: {
                    data: dates
                },
                series: [
                    { name: '日销量', data: sales },
                    { name: '平均价格', data: prices }
                ]
            });

            // 更新支撑数据表格
            updateSalesPriceTable(salesPriceData);
        }

        // 更新库存TOP15图表
        if (inventoryChart && inventoryData) {
            const productNames = inventoryData.map(item => item.product_name);
            const inventoryLevels = inventoryData.map(item => parseFloat(item.inventory_level || 0));

            inventoryChart.setOption({
                xAxis: {
                    data: productNames
                },
                series: [{
                    data: inventoryLevels
                }]
            });
        }

        // 更新产销率趋势图
        if (ratioTrendChart && ratioData) {
            const dates = ratioData.map(item => item.record_date);
            const ratios = ratioData.map(item => parseFloat(item.ratio || 0));

            ratioTrendChart.setOption({
                xAxis: {
                    data: dates
                },
                series: [{
                    data: ratios
                }]
            });
        }

        // 隐藏加载状态
        hideChartsLoading();

        console.log('✅ Professional charts updated successfully');

    } catch (error) {
        console.error('❌ Error updating professional charts:', error);
        hideChartsLoading();

        // 显示错误提示
        showErrorMessage('数据更新失败，请检查网络连接或稍后重试');
    }
}

// 更新销售价格支撑数据表格
function updateSalesPriceTable(data) {
    const tableBody = document.getElementById('sales-price-table-body');
    if (!tableBody || !data || data.length === 0) {
        return;
    }

    let html = '';
    data.forEach((item, index) => {
        const sales = parseFloat(item.total_sales || 0);
        const price = parseFloat(item.avg_price || 0);
        const revenue = (sales * price / 10000).toFixed(2); // 转换为万元

        // 计算环比变化
        let change = '--';
        if (index > 0) {
            const prevSales = parseFloat(data[index - 1].total_sales || 0);
            if (prevSales > 0) {
                const changePercent = ((sales - prevSales) / prevSales * 100).toFixed(1);
                change = `${changePercent > 0 ? '+' : ''}${changePercent}%`;
            }
        }

        html += `
            <tr>
                <td>${item.record_date}</td>
                <td>${sales.toFixed(2)}</td>
                <td>${price.toFixed(2)}</td>
                <td>${revenue}</td>
                <td style="color: ${change.startsWith('+') ? '#28a745' : change.startsWith('-') ? '#dc3545' : '#6C757D'}">${change}</td>
            </tr>
        `;
    });

    tableBody.innerHTML = html;
}

// 显示图表加载状态
function showChartsLoading() {
    const charts = ['sales-price-chart', 'inventory-top-chart', 'ratio-trend-chart'];
    charts.forEach(chartId => {
        const chartDom = document.getElementById(chartId);
        if (chartDom) {
            chartDom.style.position = 'relative';
            if (!chartDom.querySelector('.loading-overlay')) {
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading-overlay';
                loadingDiv.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(255, 255, 255, 0.8);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                    font-size: 14px;
                    color: #6C757D;
                `;
                loadingDiv.innerHTML = '📊 数据加载中...';
                chartDom.appendChild(loadingDiv);
            }
        }
    });
}

// 隐藏图表加载状态
function hideChartsLoading() {
    const loadingOverlays = document.querySelectorAll('.loading-overlay');
    loadingOverlays.forEach(overlay => {
        overlay.remove();
    });
}

// 显示错误消息
function showErrorMessage(message) {
    // 创建临时错误提示
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f8d7da;
        color: #721c24;
        padding: 12px 20px;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        z-index: 10000;
        font-size: 14px;
        max-width: 300px;
    `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);

    // 3秒后自动移除
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 3000);
}

// --- PRICE CHANGE ANALYSIS FUNCTIONS ---

// 加载价格调整数据
async function loadPriceAdjustments() {
    try {
        console.log('🔄 Loading price adjustments data...');

        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

        const data = await fetchData(`/api/price-changes?start_date=${startDate}&end_date=${endDate}&min_price_diff=200`);

        // 更新统计卡片
        updatePriceMetrics(data);

        // 更新图表
        updatePriceCharts(data);

        // 更新表格
        updatePriceTable(data);

        console.log('✅ Price adjustments data loaded successfully');
    } catch (error) {
        console.error('❌ Error loading price adjustments:', error);
        showErrorMessage('加载价格调整数据失败: ' + error.message);
    }
}

// 更新价格统计指标
function updatePriceMetrics(data) {
    const totalAdjustments = data.length;
    const avgChange = data.length > 0 ? (data.reduce((sum, item) => sum + Math.abs(item.price_difference), 0) / data.length).toFixed(1) : 0;

    const increases = data.filter(item => item.price_difference > 0);
    const decreases = data.filter(item => item.price_difference < 0);

    const maxIncrease = increases.length > 0 ? increases.reduce((max, item) => item.price_difference > max.price_difference ? item : max) : null;
    const maxDecrease = decreases.length > 0 ? decreases.reduce((min, item) => item.price_difference < min.price_difference ? item : min) : null;

    // 更新DOM元素
    document.getElementById('price-adjustments-total').textContent = totalAdjustments;
    document.getElementById('price-avg-change').textContent = avgChange;
    document.getElementById('price-max-increase').textContent = maxIncrease ? `+${maxIncrease.price_difference.toFixed(1)}` : '--';
    document.getElementById('price-max-increase-product').textContent = maxIncrease ? maxIncrease.product_name : '--';
    document.getElementById('price-max-decrease').textContent = maxDecrease ? maxDecrease.price_difference.toFixed(1) : '--';
    document.getElementById('price-max-decrease-product').textContent = maxDecrease ? maxDecrease.product_name : '--';
}

// 更新价格图表
function updatePriceCharts(data) {
    // 价格调整频次分布图
    createPriceFrequencyChart(data);

    // 重大价格调整记录图
    createPriceMajorChangesChart(data);
}

// 创建价格调整频次分布图
function createPriceFrequencyChart(data) {
    const container = document.getElementById('price-frequency-chart');
    if (!container) return;

    if (priceFrequencyChart) {
        priceFrequencyChart.dispose();
    }

    priceFrequencyChart = echarts.init(container);

    // 按价格变动幅度分组
    const ranges = [
        { name: '200-500元', min: 200, max: 500, count: 0 },
        { name: '500-1000元', min: 500, max: 1000, count: 0 },
        { name: '1000-2000元', min: 1000, max: 2000, count: 0 },
        { name: '2000元以上', min: 2000, max: Infinity, count: 0 }
    ];

    data.forEach(item => {
        const absChange = Math.abs(item.price_difference);
        for (let range of ranges) {
            if (absChange >= range.min && absChange < range.max) {
                range.count++;
                break;
            }
        }
    });

    const option = {
        color: ['#005BAC', '#49A9E8', '#D92E2E', '#FF6B35'],
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { fontSize: 12 }
        },
        series: [{
            name: '调价频次',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['60%', '50%'],
            data: ranges.map(range => ({
                value: range.count,
                name: range.name
            })),
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            },
            label: {
                formatter: '{b}\n{c}次'
            }
        }]
    };

    priceFrequencyChart.setOption(option);
}

// 创建重大价格调整记录图
function createPriceMajorChangesChart(data) {
    const container = document.getElementById('price-major-changes-chart');
    if (!container) return;

    if (priceMajorChangesChart) {
        priceMajorChangesChart.dispose();
    }

    priceMajorChangesChart = echarts.init(container);

    // 取前10个最大变动的记录
    const sortedData = data.sort((a, b) => Math.abs(b.price_difference) - Math.abs(a.price_difference)).slice(0, 10);

    const option = {
        color: ['#005BAC'],
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            formatter: function(params) {
                const item = params[0];
                const dataItem = sortedData[item.dataIndex];
                return `${dataItem.product_name}<br/>
                        调价日期: ${dataItem.adjustment_date}<br/>
                        价格变动: ${dataItem.price_difference > 0 ? '+' : ''}${dataItem.price_difference.toFixed(1)}元/吨<br/>
                        前价格: ${dataItem.previous_price ? dataItem.previous_price.toFixed(1) : '--'}元/吨<br/>
                        现价格: ${dataItem.current_price.toFixed(1)}元/吨`;
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'value',
            axisLabel: {
                formatter: '{value}元/吨'
            }
        },
        yAxis: {
            type: 'category',
            data: sortedData.map(item => item.product_name.length > 8 ? item.product_name.substring(0, 8) + '...' : item.product_name),
            axisLabel: {
                fontSize: 11
            }
        },
        series: [{
            name: '价格变动',
            type: 'bar',
            data: sortedData.map(item => ({
                value: Math.abs(item.price_difference),
                itemStyle: {
                    color: item.price_difference > 0 ? '#D92E2E' : '#005BAC'
                }
            })),
            barWidth: '60%',
            label: {
                show: true,
                position: 'right',
                formatter: function(params) {
                    const item = sortedData[params.dataIndex];
                    return (item.price_difference > 0 ? '+' : '') + item.price_difference.toFixed(1);
                }
            }
        }]
    };

    priceMajorChangesChart.setOption(option);
}

// 更新价格调整表格
function updatePriceTable(data) {
    const tbody = document.getElementById('price-adjustments-table-body');
    if (!tbody) return;

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #86868b;">暂无价格调整记录</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(item => {
        const changePercent = item.previous_price ? ((item.price_difference / item.previous_price) * 100).toFixed(2) : '--';
        const changeClass = item.price_difference > 0 ? 'price-increase' : 'price-decrease';

        return `
            <tr>
                <td>${item.adjustment_date}</td>
                <td>${item.product_name}</td>
                <td>${item.specification || '--'}</td>
                <td>${item.adjustment_count}</td>
                <td>${item.previous_price ? item.previous_price.toFixed(1) : '--'}</td>
                <td>${item.current_price.toFixed(1)}</td>
                <td class="${changeClass}">${item.price_difference > 0 ? '+' : ''}${item.price_difference.toFixed(1)}</td>
                <td class="${changeClass}">${changePercent !== '--' ? (item.price_difference > 0 ? '+' : '') + changePercent + '%' : '--'}</td>
            </tr>
        `;
    }).join('');
}

// 价格表格搜索功能
function setupPriceTableSearch() {
    const searchInput = document.getElementById('price-search');
    if (!searchInput) return;

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const table = document.getElementById('price-adjustments-table');
        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const productName = row.cells[1]?.textContent.toLowerCase() || '';
            const specification = row.cells[2]?.textContent.toLowerCase() || '';

            if (productName.includes(searchTerm) || specification.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// 导出价格表格数据
function exportPriceTable() {
    const table = document.getElementById('price-adjustments-table');
    if (!table) return;

    let csv = '';
    const rows = table.querySelectorAll('tr');

    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => `"${cell.textContent}"`).join(',');
        csv += rowData + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `price_adjustments_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 设置价格调整文件上传
function setupPriceFileUpload() {
    const fileInput = document.getElementById('price-file-input');
    const uploadArea = document.getElementById('price-upload-area');
    const progressDiv = document.getElementById('price-upload-progress');

    if (!fileInput || !uploadArea || !progressDiv) return;

    fileInput.addEventListener('change', async function(event) {
        const file = event.target.files[0];
        if (!file) return;

        // 显示进度条
        uploadArea.style.display = 'none';
        progressDiv.style.display = 'block';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_BASE_URL}/api/upload/price-adjustments`, {
                method: 'POST',
                body: formData,
                mode: 'cors'
            });

            const result = await response.json();

            if (response.ok) {
                showSuccessMessage(`成功处理 ${result.processedRecords} 条价格调整记录`);
                // 重新加载数据
                await loadPriceAdjustments();
            } else {
                throw new Error(result.error || '上传失败');
            }
        } catch (error) {
            console.error('❌ Price file upload error:', error);
            showErrorMessage('上传失败: ' + error.message);
        } finally {
            // 隐藏进度条，显示上传区域
            progressDiv.style.display = 'none';
            uploadArea.style.display = 'block';
            fileInput.value = ''; // 清空文件选择
        }
    });
}

// 显示成功消息
function showSuccessMessage(message) {
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #d4edda;
        color: #155724;
        padding: 12px 20px;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        z-index: 10000;
        font-size: 14px;
        max-width: 300px;
    `;
    successDiv.textContent = message;
    document.body.appendChild(successDiv);

    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.parentNode.removeChild(successDiv);
        }
    }, 3000);
}

// --- 库存页面相关函数 ---

// 加载库存总量数据
async function loadInventorySummary(date = '2025-06-26') {
    try {
        const data = await fetchData(`/api/inventory/summary?date=${date}`);

        if (data) {
            // 更新库存总量指标卡片
            const totalInventoryEl = document.getElementById('total-inventory');
            const top15TotalEl = document.getElementById('top15-total');
            const top15PercentageEl = document.getElementById('top15-percentage');
            const productCountEl = document.getElementById('product-count');

            if (totalInventoryEl) {
                totalInventoryEl.textContent = (data.total_inventory / 1000).toFixed(1) + 'K';
            }
            if (top15TotalEl) {
                top15TotalEl.textContent = (data.top15_total / 1000).toFixed(1) + 'K';
            }
            if (top15PercentageEl) {
                top15PercentageEl.textContent = data.top15_percentage.toFixed(1) + '%';
            }
            if (productCountEl) {
                productCountEl.textContent = data.product_count;
            }

            console.log('✅ Inventory summary loaded:', data);
        }
    } catch (error) {
        console.error('❌ Failed to load inventory summary:', error);
    }
}

// 初始化库存占比饼图
function initInventoryPieChart() {
    const chartDom = document.getElementById('inventory-page-pie-chart');
    if (!chartDom) {
        console.warn('⚠️ Inventory pie chart container not found');
        return;
    }

    // 移除可见性检查，允许在隐藏状态下初始化（ECharts支持）
    // 这样可以确保页面加载时图表能正确初始化

    if (inventoryPieChart) inventoryPieChart.dispose();
    inventoryPieChart = echarts.init(chartDom);
    console.log('✅ Inventory pie chart initialized');

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c}T ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: {
                fontSize: 12,
                color: '#666666'
            }
        },
        series: [
            {
                name: '库存分布',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#fff',
                    borderWidth: 2
                },
                label: {
                    show: false,
                    position: 'center'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: '18',
                        fontWeight: 'bold'
                    }
                },
                labelLine: {
                    show: false
                },
                data: []
            }
        ]
    };

    inventoryPieChart.setOption(option);
}

// 更新库存占比饼图数据
async function updateInventoryPieChart(date = '2025-06-26') {
    if (!inventoryPieChart) {
        console.warn('⚠️ Inventory pie chart not initialized');
        return;
    }

    try {
        inventoryPieChart.showLoading();
        const data = await fetchData(`/api/inventory/distribution?date=${date}&limit=15`);
        inventoryPieChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No inventory distribution data received');
            return;
        }

        console.log('🥧 Updating inventory pie chart with data:', data.length, 'items');

        inventoryPieChart.setOption({
            series: [{
                data: data.map(item => ({
                    name: item.product_name,
                    value: item.inventory_level
                }))
            }]
        });

        console.log('✅ Inventory pie chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update inventory pie chart:', error);
        if (inventoryPieChart) inventoryPieChart.hideLoading();
    }
}

// 初始化产销率趋势图表（库存页面下方）
function initProductionRatioTrendChart() {
    const chartDom = document.getElementById('production-ratio-trend-chart');
    if (!chartDom) return;

    if (productionRatioTrendChart) productionRatioTrendChart.dispose();
    productionRatioTrendChart = echarts.init(chartDom);

    const option = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            borderColor: '#E0E0E0',
            borderWidth: 1,
            textStyle: {
                color: '#333333',
                fontSize: 12,
                fontFamily: '"Microsoft YaHei", "微软雅黑", Arial, sans-serif'
            },
            padding: [8, 12],
            extraCssText: 'box-shadow: 0 4px 12px rgba(0, 91, 172, 0.15); border-radius: 6px;',
            formatter: function(params) {
                const item = params[0];
                const ratio = item.value;
                const status = ratio >= 100 ? '库存消耗' : '库存积累';
                const statusColor = ratio >= 100 ? '#34c759' : '#ff9500';
                const statusIcon = ratio >= 100 ? '📉' : '📈';
                return `<div style="font-weight: 600; margin-bottom: 8px; color: #005BAC;">${item.axisValue}</div>
                        <div style="display: flex; align-items: center; margin: 4px 0;">
                            <span style="display: inline-block; width: 10px; height: 10px; background: ${statusColor}; border-radius: 50%; margin-right: 8px;"></span>
                            产销率: <strong style="color: ${statusColor};">${ratio ? ratio.toFixed(1) : '--'}%</strong>
                        </div>
                        <div style="color: ${statusColor}; font-size: 11px; margin-top: 4px;">
                            ${statusIcon} ${status} ${ratio >= 100 ? '(销量>产量)' : '(销量<产量)'}
                        </div>
                        <div style="color: #666; font-size: 10px; margin-top: 4px; border-top: 1px solid #eee; padding-top: 4px;">
                            100%为基准线：>100%表示库存消耗，<100%表示库存积累
                        </div>`;
            }
        },
        grid: {
            left: '8%',
            right: '8%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: [],
            axisLine: { lineStyle: { color: '#E0E0E0', width: 1 } },
            axisTick: { lineStyle: { color: '#E0E0E0' } },
            axisLabel: {
                color: '#666666',
                fontSize: 12,
                rotate: 45,
                interval: 'auto',
                formatter: function(value) {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                }
            }
        },
        yAxis: {
            type: 'value',
            name: '产销率 (%)',
            nameTextStyle: {
                color: '#005BAC',
                fontSize: 12,
                fontWeight: 600
            },
            min: 0,
            max: function(value) {
                return Math.max(value.max * 1.1, 120);
            },
            axisLine: { show: true, lineStyle: { color: '#005BAC', width: 2 } },
            axisTick: { lineStyle: { color: '#005BAC' } },
            axisLabel: { color: '#666666', fontSize: 12 },
            splitLine: { lineStyle: { color: '#F5F5F5', type: 'dashed' } }
        },
        series: [{
            name: '产销率',
            type: 'line',
            data: [],
            lineStyle: {
                color: function(params) {
                    return params.value >= 100 ? '#34c759' : '#ff9500';
                },
                width: 3
            },
            markLine: {
                silent: true,
                lineStyle: {
                    color: '#005BAC',
                    type: 'dashed',
                    width: 2
                },
                label: {
                    show: true,
                    position: 'end',
                    formatter: '基准线 100%',
                    color: '#005BAC',
                    fontSize: 12
                },
                data: [
                    {
                        yAxis: 100,
                        name: '基准线'
                    }
                ]
            },
            markArea: {
                silent: true,
                itemStyle: {
                    color: 'rgba(52, 199, 89, 0.1)'
                },
                data: [
                    [
                        {
                            yAxis: 100,
                            name: '库存消耗区间'
                        },
                        {
                            yAxis: 'max'
                        }
                    ]
                ]
            }
        }]
    };

    productionRatioTrendChart.setOption(option);
    console.log('✅ Production ratio trend chart initialized');
}

// 更新产销率趋势图表数据
async function updateProductionRatioTrendChart(startDate = '2025-06-01', endDate = '2025-06-26') {
    if (!productionRatioTrendChart) {
        console.warn('⚠️ Production ratio trend chart not initialized');
        return;
    }

    try {
        productionRatioTrendChart.showLoading();
        const data = await fetchData(`/api/trends/ratio?start_date=${startDate}&end_date=${endDate}`);
        productionRatioTrendChart.hideLoading();

        if (!data || !Array.isArray(data)) {
            console.warn('⚠️ No production ratio trend data received');
            return;
        }

        console.log('📊 Updating production ratio trend chart with data:', data.length, 'items');

        // 过滤掉null值的数据
        const validData = data.filter(item => item.ratio !== null && item.ratio !== undefined);

        productionRatioTrendChart.setOption({
            xAxis: {
                data: validData.map(item => item.record_date)
            },
            series: [{
                data: validData.map(item => item.ratio)
            }]
        });

        console.log('✅ Production ratio trend chart updated successfully');
    } catch (error) {
        console.error('❌ Failed to update production ratio trend chart:', error);
        if (productionRatioTrendChart) productionRatioTrendChart.hideLoading();
    }
}

// 导出库存相关函数到全局作用域
window.loadInventorySummary = loadInventorySummary;
window.initInventoryPieChart = initInventoryPieChart;
window.updateInventoryPieChart = updateInventoryPieChart;
window.initProductionRatioTrendChart = initProductionRatioTrendChart;
window.updateProductionRatioTrendChart = updateProductionRatioTrendChart;

// --- 新增函数：统一更新库存分析数据 ---

/**
 * 异步获取并更新所有库存分析相关数据
 * @param {string} date - YYYY-MM-DD格式的日期
 */
async function updateInventoryAnalytics(date) {
    console.log(`📊 Updating all inventory analytics for date: ${date}`);
    
    // 1. 更新指标卡片
    try {
        const summaryData = await fetchData(`/api/inventory/summary?date=${date}`);
        if (summaryData) {
            const totalInventoryEl = document.getElementById('total-inventory');
            const top15TotalEl = document.getElementById('top15-total');
            const top15PercentageEl = document.getElementById('top15-percentage');

            if (totalInventoryEl) totalInventoryEl.textContent = (summaryData.total_inventory / 1000).toFixed(1) + 'K';
            if (top15TotalEl) top15TotalEl.textContent = (summaryData.top15_total / 1000).toFixed(1) + 'K';
            if (top15PercentageEl) top15PercentageEl.textContent = summaryData.top15_percentage.toFixed(1) + '%';
            
            console.log('✅ Inventory summary cards updated.');
        }
    } catch (error) {
        console.error('❌ Failed to update inventory summary cards:', error);
    }

    // 2. 更新库存占比饼图
    if (inventoryPieChart) {
        updateInventoryPieChart(date);
    }

    // 3. 更新库存TOP15柱状图
    if (inventoryPageTopChart) {
        updateInventoryPageTopChart(date);
    }
}



// 导出新函数以供全局调用（如果需要）
window.updateInventoryAnalytics = updateInventoryAnalytics;
window.updateInventoryPageTopChart = updateInventoryPageTopChart;
