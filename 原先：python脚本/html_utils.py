# -*- coding: utf-8 -*-
"""
HTML 生成工具模块
"""
from datetime import datetime
import os
import time
import tempfile
import shutil
import random

def generate_header(title="分析报告", output_dir="."):
    """生成HTML头部，包含样式和导航"""
    # Correctly reference image paths relative to the output directory
    # Example: Use os.path.basename if images are in the same dir, or adjust path
    # Assuming images are in the same output_dir as html files for simplicity now.

    # Extract CSS and JS from the original _generate_html_header
    # Note: Ensure all necessary JS functions are included.
    css_styles = """
        :root {
            --primary-color: #1976D2;
            --secondary-color: #03A9F4;
            --success-color: #4CAF50;
            --warning-color: #FFC107;
            --danger-color: #F44336;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
            --border-radius: 8px;
            --box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f7fa;
            margin: 0;
            padding: 0;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .report-header { /* Renamed from .header to avoid conflicts if used elsewhere */
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 30px 20px;
            border-radius: var(--border-radius);
            margin-bottom: 30px;
            box-shadow: var(--box-shadow);
            text-align: center;
        }
        h1, h2, h3, h4 { color: #333; margin-bottom: 15px; }
        .report-header h1 { color: white; margin: 0; font-size: 28px; }
        .report-header p { margin: 10px 0 0; opacity: 0.9; font-size: 14px; }
        .navigation { background-color: var(--dark-color); padding: 10px 0; margin-bottom: 20px; border-radius: var(--border-radius); box-shadow: var(--box-shadow); }
        .navigation ul { list-style: none; text-align: center; padding: 0; margin: 0; }
        .navigation ul li { display: inline-block; margin: 0 15px; }
        .navigation ul li a { color: var(--light-color); text-decoration: none; padding: 8px 15px; border-radius: 4px; transition: background-color 0.3s ease; }
        .navigation ul li a:hover, .navigation ul li a.active { background-color: var(--primary-color); color: white; }

        .section { background: white; margin-bottom: 30px; border-radius: var(--border-radius); box-shadow: var(--box-shadow); overflow: hidden; }
        .section-header { background-color: var(--light-color); padding: 15px 20px; border-bottom: 1px solid #eee; }
        .section-body { padding: 20px; }
        .subsection { margin-bottom: 25px; border-bottom: 1px solid #eee; padding-bottom: 20px; }
        .subsection:last-child { border-bottom: none; margin-bottom: 0; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; border-radius: var(--border-radius); overflow: hidden; }
        th, td { border: 1px solid #eee; padding: 12px; text-align: left; }
        th { background-color: var(--light-color); font-weight: 600; position: sticky; top: 0; z-index: 10; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f1f1f1; }
        .warning { color: var(--danger-color); font-weight: bold; }
        .highlight { background-color: rgba(255, 193, 7, 0.2); }
        .summary { background-color: #e8f4fd; padding: 15px; border-radius: var(--border-radius); border-left: 4px solid var(--primary-color); max-height: 200px; overflow-y: auto; }
        img { max-width: 100%; height: auto; margin: 15px 0; border-radius: var(--border-radius); box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .filter-container { margin-bottom: 20px; padding: 15px; background-color: var(--light-color); border-radius: var(--border-radius); display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
        .filter-container label { margin-right: 8px; font-weight: 600; color: #555; }
        .filter-container select, .filter-container input { padding: 8px 12px; margin-right: 15px; border-radius: 4px; border: 1px solid #ddd; min-width: 150px; background-color: white; }
        .filter-container select:focus, .filter-container input:focus { outline: none; border-color: var(--primary-color); box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1); }
        .filter-container button { padding: 8px 15px; background-color: var(--primary-color); color: white; border: none; border-radius: 4px; cursor: pointer; transition: var(--transition); }
        .filter-container button:hover { background-color: #1565C0; transform: translateY(-2px); }
        .inventory-table-container, .sales-table-container, .detail-table-container { /* Consolidated common styles */
            max-height: 300px; /* Default height, can be overridden */
            overflow-y: auto;
            margin-bottom: 20px;
            border-radius: var(--border-radius);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #eee;
        }
        .inventory-summary { display: flex; flex-wrap: wrap; justify-content: space-between; margin-bottom: 20px; gap: 15px; }
        .inventory-card { background-color: white; border-radius: var(--border-radius); padding: 20px; flex: 1; min-width: 200px; box-shadow: var(--box-shadow); transition: var(--transition); border-top: 4px solid var(--primary-color); }
        .inventory-card:hover { transform: translateY(-5px); }
        .inventory-card h4 { margin-top: 0; color: #555; font-size: 16px; }
        .inventory-card .value { font-size: 28px; font-weight: bold; color: var(--primary-color); margin: 10px 0; }
        .inventory-search, .sales-search, .detail-search { /* Consolidated common styles */
            margin-bottom: 15px;
            position: relative;
        }
        .inventory-search input, .sales-search input, .detail-search input { /* Consolidated common styles */
            padding: 10px 15px 10px 40px;
            width: 100%;
            border: 1px solid #ddd;
            border-radius: var(--border-radius);
            font-size: 14px;
        }
        .inventory-search:before, .sales-search:before, .detail-search:before { /* Consolidated common styles */
            content: "🔍";
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #999;
        }
        .ratio-chart-container { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
        .ratio-chart { flex: 1; min-width: 300px; background-color: white; padding: 20px; border-radius: var(--border-radius); box-shadow: var(--box-shadow); }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .status-balanced { background-color: rgba(25, 118, 210, 0.1); color: var(--primary-color); }
        .status-surplus { background-color: rgba(244, 67, 54, 0.1); color: var(--danger-color); }
        .status-shortage { background-color: rgba(76, 175, 80, 0.1); color: var(--success-color); }
        .data-card { background-color: white; border-radius: var(--border-radius); padding: 20px; margin-bottom: 20px; box-shadow: var(--box-shadow); }
        .data-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
        .data-card-title { font-size: 18px; font-weight: 600; color: #333; margin: 0; }
        .data-card-body { padding: 10px 0; }
        .sales-container { width: 100%; margin-bottom: 15px; }
        .sales-flex { display: flex; flex-wrap: wrap; margin: -5px; }
        .sales-flex-item { flex: 0 0 calc(20% - 10px); margin: 5px; box-sizing: border-box; }
        .sales-card { background-color: #f5f5f5; border-radius: 4px; padding: 8px 10px; cursor: pointer; transition: 0.2s; position: relative; border: 1px solid #e0e0e0; box-shadow: 0 1px 2px rgba(0,0,0,0.03); height: 100%; }
        .sales-card:hover { background-color: #eaeaea; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
        .sales-card.active { background-color: #e0e0e0; } /* Highlight active card */
        .sales-card-header { display: flex; justify-content: space-between; align-items: center; }
        .sales-card-header h4 { margin: 0; font-size: 13px; color: #333; font-weight: 600; }
        .toggle-icon { font-size: 11px; color: #777; transition: transform 0.3s ease; }
        .sales-card.active .toggle-icon { transform: rotate(180deg); }
        .sales-card-body { margin-top: 5px; }
        .sales-card-body p { margin: 3px 0 0 0; font-size: 12px; color: #555; line-height: 1.3; }
        .card-hint { font-size: 11px; color: #999; text-align: center; margin-top: 5px; }

        /* Panel styles for ratio and sales details */
        .ratio-panel, .sales-panel {
            display: none; /* Hidden by default */
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            padding: 15px; /* Add padding */
        }
        .ratio-panel.active, .sales-panel.active {
             display: block; /* Shown when active */
        }
        .ratio-panel-header, .sales-panel-header { /* Shared styles for panel headers */
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 10px;
            margin-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
         .ratio-panel-header h4, .sales-panel-header h4 { margin: 0; font-size: 16px; }
         .ratio-panel-controls, .sales-panel-controls { display: flex; align-items: center; gap: 10px;}
        .search-input { /* Specific styling for search inputs in panels */
            padding: 5px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
        }
        .close-button { /* Styling for close buttons in panels */
            background: none;
            border: none;
            font-size: 16px;
            cursor: pointer;
            color: #666;
            padding: 0 5px;
        }
        .close-button:hover { color: #333; }

        .ratio-panel .sales-table-container, .sales-panel .sales-table-container { /* Panel specific table container */
             max-height: 400px;
             border: 1px solid #eee; /* Add border */
             border-radius: 4px;
         }
        .ratio-panel table td, .ratio-panel table th,
        .sales-panel table td, .sales-panel table th { /* Compact table cells for panels */
            padding: 6px 8px;
            font-size: 13px;
        }

        /* Value highlighting */
        .high-value { color: var(--success-color); font-weight: bold; }
        .medium-value { color: var(--warning-color); font-weight: bold; }
        .low-value { color: var(--danger-color); font-weight: bold; }

        /* Collapsible button/content (if needed later) */
        .collapsible-button { /* ... styles ... */ }
        .collapsible-content { /* ... styles ... */ }

        /* Total row style */
        .total-row { background-color: #f0f8ff; border-top: 2px solid #ddd; font-weight: bold; }
        .total-row td { padding: 8px; }
        .text-right { text-align: right; } /* Utility class */

        /* Responsive */
        @media (max-width: 992px) { /* Adjust breakpoint if needed */
             .sales-flex-item { flex: 0 0 calc(25% - 10px); } /* 4 cards per row */
        }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .report-header { padding: 20px 15px; }
            .inventory-summary { flex-direction: column; }
            .inventory-card { width: 100%; }
            .filter-container { flex-direction: column; align-items: flex-start; }
            .filter-container select, .filter-container input { width: 100%; margin-right: 0; margin-bottom: 10px; }
            .sales-flex-item { flex: 0 0 calc(50% - 10px); } /* 2 cards per row */
            .navigation ul li { margin: 0 5px; } /* Reduce nav spacing */
             .navigation ul li a { padding: 6px 10px; }
        }
         @media (max-width: 576px) {
             .sales-flex-item { flex: 0 0 calc(100% - 10px); } /* 1 card per row */
         }

        /* --- Added Mobile Responsive Styles --- */
        @media (max-width: 768px) {
            .container {
                padding: 0 10px;
                margin: 10px auto;
            }

            /* 表格容器适配 */
            .detail-table-container, .inventory-table-container, .sales-table-container {
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch; /* 更顺滑的iOS滚动 */
            }

            /* 表格内容精简 */
            table th, table td {
                padding: 6px 8px;
                font-size: 0.85em;
            }

            /* 调整图表大小 */
            img.chart, img.img-fluid {
                max-width: 100%;
                height: auto;
            }

            /* 卡片布局调整 */
            .sales-flex-item, .inventory-card {
                width: 100%;
                margin-bottom: 10px;
            }

            /* 减少面板填充 */
            .data-card-body, .section-body {
                padding: 10px;
            }

            /* 确保按钮大小适中 */
            .btn {
                padding: 6px 12px;
                font-size: 0.9em;
            }

            /* --- Responsive Stacking Table for Price Volatility --- */
            .stacking-table-mobile {
                border: none; /* Remove table border */
                width: 100%;
            }
            .stacking-table-mobile thead {
                display: none; /* Hide table header on mobile */
            }
            .stacking-table-mobile tr {
                display: block; /* Make rows behave like blocks */
                margin-bottom: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background-color: #fff; /* Give each 'row' a background */
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .stacking-table-mobile td {
                display: block; /* Make cells behave like blocks */
                width: 100%;
                box-sizing: border-box;
                text-align: right; /* Align data value to the right */
                padding-left: 45%; /* Make space for the label */
                position: relative; /* Needed for absolute positioning of the label */
                border-bottom: 1px dotted #eee; /* Separator between 'cells' */
                padding-top: 5px;
                padding-bottom: 5px;
                min-height: 24px; /* Ensure minimum height */
            }
            .stacking-table-mobile td:last-child {
                border-bottom: none; /* No border for the last 'cell' in a block */
            }
            .stacking-table-mobile td::before {
                content: attr(data-label); /* Use the data-label attribute as content */
                position: absolute;
                left: 10px; /* Position the label */
                width: calc(45% - 15px); /* Control label width */
                padding-right: 10px;
                text-align: left; /* Align label text to the left */
                font-weight: bold;
                white-space: nowrap; /* Prevent label wrap */
                color: #333;
            }
            /* --- End Responsive Stacking Table --- */

        }
        /* --- End Added Mobile Responsive Styles --- */

        /* 增强表格滚动容器，确保适配小屏幕 */
        .table-responsive {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            max-width: 100vw; /* Changed from 100% to 100vw for clarity */
        }
    """

    javascript = """
        // Global function: Toggle ratio/sales detail panel visibility and card active state
        function toggleDetailPanel(panelType, dateStr, event) {
            var panelId = panelType + "Panel_" + dateStr; // e.g., "ratioPanel_2023-10-26" or "salesPanel_2023-10-26"
            var panel = document.getElementById(panelId);
            if(!panel) return; // Element not found

            var clickedCard = event.currentTarget; // The card that was clicked
            var allPanels = document.querySelectorAll('.' + panelType + '-panel'); // Select all panels of the same type
            var allCards = clickedCard.closest('.sales-flex').querySelectorAll('.sales-card'); // Find sibling cards

            // If the clicked panel is already active, hide it and deactivate card
            if (panel.classList.contains('active')) {
                panel.classList.remove('active');
                panel.style.display = "none";
                if(clickedCard) clickedCard.classList.remove('active');
            } else {
                // Hide all other panels of the same type and deactivate their cards
                allPanels.forEach(function(p) {
                    if (p.id !== panelId && p.classList.contains('active')) {
                        p.classList.remove('active');
                        p.style.display = "none";
                    }
                });
                 allCards.forEach(function(card) {
                     card.classList.remove('active');
                 });

                // Show the clicked panel and activate its card
                panel.classList.add('active');
                panel.style.display = "block"; // Make sure display is set to block
                if(clickedCard) clickedCard.classList.add('active');
            }

            // Prevent event bubbling (optional, but often good practice)
            if(event) event.stopPropagation();
        }

        // Global function: Search within a table inside a panel
        function searchTableInPanel(tableId, inputId) {
            const input = document.getElementById(inputId);
            if (!input) return;
            
            const filter = input.value.toUpperCase();
            const table = document.getElementById(tableId);
            if (!table) return;
            
            const tr = table.getElementsByTagName("tr");
            const totalRow = Array.from(tr).find(row => row.classList.contains('total-row'));
            
            // 如果没有输入筛选条件，确保所有非合计行都可见
            if (!filter) {
                for (let i = 0; i < tr.length; i++) {
                    if (i === 0 || tr[i].classList.contains('total-row')) continue;
                    tr[i].style.display = ""; // 确保行可见
                }
                // **重要**: 如果没有筛选，不修改合计行，保持其原始状态。
                // 需要确保Python生成的HTML包含正确的原始合计。
                return; 
            }
            
            // 根据表格ID判断表格类型
            const isRatioTable = tableId.includes('ratioTable');
            const isSalesTable = tableId.includes('salesTable');
            
            // 初始化合计值
            let volumeTotal = 0;      // 通用：销量/数量合计
            let productionTotal = 0;  // 产销率表：产量合计
            let amountTotal = 0;      // 销售表：无税金额合计
            let visibleRowCount = 0;
            
            // 处理数据行 (过滤并累加)
            for (let i = 0; i < tr.length; i++) {
                if (i === 0 || tr[i].classList.contains('total-row')) continue; // 跳过表头和合计行
                
                const td = tr[i].getElementsByTagName("td");
                let txtValue = "";
                let visible = false;
                
                // 检查所有单元格是否匹配筛选条件
                for (let j = 0; j < td.length; j++) {
                    if (td[j]) {
                        txtValue = td[j].textContent || td[j].innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            visible = true;
                            break;
                        }
                    }
                }
                
                tr[i].style.display = visible ? "" : "none"; // 根据可见性设置显示
                
                // 如果行可见，累加数据到合计
                if (visible) {
                    visibleRowCount++;
                    try {
                        if (isRatioTable && td.length >= 3) {
                            // 产销率表: 累加销量(td[1])和产量(td[2])
                            let salesVal = parseFloat(td[1].textContent.replace(/,/g, '')) || 0;
                            let prodVal = parseFloat(td[2].textContent.replace(/,/g, '')) || 0;
                            volumeTotal += salesVal;
                            productionTotal += prodVal;
                        } else if (isSalesTable && td.length >= 3) {
                            // 销售明细表: 累加销量(td[1])和无税金额(td[2])
                            let salesVol = parseFloat(td[1].textContent.replace(/,/g, '')) || 0;
                            let salesAmount = parseFloat(td[2].textContent.replace(/,/g, '')) || 0;
                            volumeTotal += salesVol;
                            amountTotal += salesAmount;
                        }
                    } catch (e) {
                        console.error("处理数值进行合计时出错:", e, tr[i]);
                    }
                }
            }
            
            // 更新合计行数据 (仅当有筛选条件时)
            if (totalRow && filter) {
                const totalTds = totalRow.getElementsByTagName("td");
                if (isRatioTable && totalTds.length >= 4) {
                    totalTds[1].innerHTML = '<strong>' + volumeTotal.toLocaleString('en-US', {maximumFractionDigits: 0}) + '</strong>'; // 销量合计
                    totalTds[2].innerHTML = '<strong>' + productionTotal.toLocaleString('en-US', {maximumFractionDigits: 0}) + '</strong>'; // 产量合计
                    const ratio = productionTotal > 0 ? (volumeTotal / productionTotal * 100).toFixed(1) : "0.0";
                    totalTds[3].innerHTML = '<strong>' + ratio + '%</strong>'; // 产销率
                } else if (isSalesTable && totalTds.length >= 4) {
                    totalTds[1].innerHTML = '<strong>' + volumeTotal.toLocaleString('en-US', {maximumFractionDigits: 0}) + '</strong>'; // 销量合计
                    totalTds[2].innerHTML = '<strong>' + amountTotal.toLocaleString('en-US', {maximumFractionDigits: 0}) + '</strong>'; // 无税金额合计
                    // 计算含税单价 (元/吨)
                    let avgPrice = 0;
                    if (volumeTotal > 0) {
                        // 假设 volumeTotal 单位是 kg, amountTotal 是元
                        avgPrice = (amountTotal / volumeTotal) * 1.09 * 1000; 
                    }
                    totalTds[3].innerHTML = '<strong>' + avgPrice.toLocaleString('en-US', {maximumFractionDigits: 0}) + '</strong>'; // 含税单价
                }
            }
        }

        // General purpose table search function (for tables not in panels)
        function searchTable(tableId, searchInputId) {
             var input = document.getElementById(searchInputId);
             var filter = input.value.toUpperCase();
             var table = document.getElementById(tableId);
             var tr = table.getElementsByTagName("tr");

             for (var i = 1; i < tr.length; i++) { // Start from 1 to skip header
                 var found = false;
                 var td = tr[i].getElementsByTagName("td");
                 for (var j = 0; j < td.length; j++) {
                     if (td[j]) {
                         var txtValue = td[j].textContent || td[j].innerText;
                         // Improved search: check if any cell contains the filter text
                         if (txtValue.toUpperCase().indexOf(filter) > -1) {
                             found = true;
                             break; // Exit inner loop once found in a row
                         }
                     }
                 }
                 tr[i].style.display = found ? "" : "none";
             }
         }

        // Specific function wrappers for onclick events to maintain compatibility
         function toggleRatioPanel(dateStr, event) {
             toggleDetailPanel('ratio', dateStr, event);
         }
         function searchProducts(dateStr) {
            // Assuming the input id is searchInput-dateStr and table id is productTable-dateStr based on original code
            var input = document.getElementById("searchInput-" + dateStr);
            var table = document.getElementById("productTable-" + dateStr);
            if (!input || !table) return;

            var filter = input.value.toUpperCase();
            var tr = table.getElementsByTagName("tr");

            for (var i = 1; i < tr.length; i++) { // Skip header row
                var td = tr[i].getElementsByTagName("td")[0]; // Search first column (Product Name)
                if (td) {
                    var txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
        }
         function toggleSalesPanel(dateStr, event) {
             toggleDetailPanel('sales', dateStr, event);
         }
         function searchSales(dateStr) {
             searchTableInPanel('sales', dateStr);
         }
        function searchInventory() {
            searchTable('inventoryTable', 'inventorySearch');
        }
        // Add search functions for other tables if needed, e.g., searchAbnormal, searchInconsistent, searchConflict, searchComparison
        // They can all use the generic searchTable function:
        // function searchAbnormal() { searchTable('abnormalTable', 'abnormalSearch'); }
        // function searchInconsistent() { searchTable('inconsistentTable', 'inconsistentSearch'); }
        // function searchConflict() { searchTable('conflictTable', 'conflictSearch'); }
        // function searchComparison() { searchTable('comparisonTable', 'comparisonSearch'); }

        // Add DOMContentLoaded listener if needed for initializations from original footer script
        // document.addEventListener('DOMContentLoaded', function() { /* ... */ });

        // --- Added Mobile Enhancement Script ---
        document.addEventListener('DOMContentLoaded', function() {
            // 添加表格滑动提示
            const tableContainers = document.querySelectorAll('.table-responsive');

            tableContainers.forEach(container => {
                // Check if the table actually needs to scroll
                if (container.scrollWidth > container.clientWidth) {
                    // 创建滑动提示元素
                    const hint = document.createElement('div');
                    hint.className = 'swipe-hint';
                    hint.innerHTML = '<i class="bi bi-arrow-left-right"></i> 左右滑动查看更多';
                    // Use inline styles as provided, ensure Bootstrap Icons are loaded if using bi-* classes
                    hint.style.cssText = 'text-align: center; color: #666; font-size: 0.8em; padding: 5px; margin-top: -10px; margin-bottom: 5px;'; // Adjusted margins

                    // 插入到表格容器之前
                    container.parentNode.insertBefore(hint, container);

                    // 监听滚动，滚动后隐藏提示
                    container.addEventListener('scroll', function() {
                        hint.style.display = 'none';
                    }, {once: true});  // 只触发一次
                }
            });

            // 适配表格列宽 (Optional: 'auto' might not always be desired, consider carefully)
            const tables = document.querySelectorAll('.mobile-friendly-table'); // Target tables with this class
            if (window.innerWidth <= 768) {
                tables.forEach(table => {
                    // 根据内容自动调整列宽 - Use with caution, might make narrow columns too wide
                    // table.style.tableLayout = 'auto';
                    console.log("Adjusting table layout for mobile:", table.id); // Log for debugging
                });
            }

            // --- Add other DOMContentLoaded initializations below if needed ---

        });
        // --- End Added Mobile Enhancement Script ---
    """

    # Get current time for the header (if needed, or use footer)
    current_time_header = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        {css_styles}
    </style>
    <script>
        {javascript}
    </script>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <h1>春雪食品生品产销分析报告</h1>
            <!-- <p>生成时间: {current_time_header}</p> -->
            <p>报告作者: quzhupeng@springsnow.cn</p>
        </div>
"""

def generate_navigation(active_page="index"):
    """生成导航栏HTML"""
    nav_items = {
        "index": {"name": "分析摘要", "url": "index.html"},
        "inventory": {"name": "库存情况", "url": "inventory.html"},
        "ratio": {"name": "产销率分析", "url": "ratio.html"},
        "sales": {"name": "销售情况", "url": "sales.html"},
        "details": {"name": "详细数据", "url": "details.html"},
        "price_volatility": {"name": "价格波动", "url": "price_volatility.html"},
        "industry": {"name": "卓创资讯", "url": "industry.html"}
    }
    nav_html = '<nav class="navigation"><ul>'
    for key, item in nav_items.items():
        active_class = 'active' if key == active_page else ''
        nav_html += f'<li><a href="{item["url"]}" class="{active_class}">{item["name"]}</a></li>'
    nav_html += '</ul></nav>'
    return nav_html

def generate_footer():
    """生成HTML页脚"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"""
            <div class="section">
                <div class="section-header">
                    <h2>报告说明</h2>
                </div>
                <div class="section-body">
                    <p>本报告数据来源于企业内部系统。报告中的分析结果仅供参考，具体业务决策请结合实际情况。</p>
                    <p>如有任何问题或建议，请联系guanlibu@springsnow.cn</p>
                    <p style="text-align: right; margin-top: 20px;">
                        报告生成时间：{current_time}
                    </p>
                </div>
            </div>
        </div> <!-- Close container -->
        <script>
             // Add specific JS calls needed on all pages after DOM load, if any were in the original footer
             // e.g., initializing components
              function searchAbnormal() {{ searchTable('abnormalTable', 'abnormalSearch'); }}
              function searchInconsistent() {{ searchTable('inconsistentTable', 'inconsistentSearch'); }}
              function searchConflict() {{ searchTable('conflictTable', 'conflictSearch'); }}
              function searchComparison() {{ searchTable('comparisonTable', 'comparisonSearch'); }}
              
              // 表格搜索函数 - 用于一般表格搜索
              function searchTable(tableId, inputId) {{
                  const input = document.getElementById(inputId);
                  const filter = input.value.toUpperCase();
                  const table = document.getElementById(tableId);
                  const tr = table.getElementsByTagName("tr");
                  
                  for (let i = 0; i < tr.length; i++) {{
                      if (i === 0) continue; // 跳过表头
                      const td = tr[i].getElementsByTagName("td");
                      let txtValue = "";
                      let visible = false;
                      
                      for (let j = 0; j < td.length; j++) {{
                          if (td[j]) {{
                              txtValue = td[j].textContent || td[j].innerText;
                              if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                                  visible = true;
                                  break;
                              }}
                          }}
                      }}
                      
                      tr[i].style.display = visible ? "" : "none";
                  }}
              }}
              
              // 切换面板显示/隐藏
              function togglePanel(panelId, event) {{
                  if (event) event.stopPropagation();
                  const panel = document.getElementById(panelId);
                  if (panel) {{
                      if (panel.style.display === "none" || panel.style.display === "") {{
                          panel.style.display = "block";
                      }} else {{
                          panel.style.display = "none";
                      }}
                  }}
              }}
              
              // 切换产销率明细面板
              function toggleRatioPanel(dateStr, event) {{
                  if (event) event.stopPropagation();
                  const panelId = `ratioPanel_${{dateStr}}`;
                  togglePanel(panelId, null);
              }}
              
              // 切换销售明细面板
              function toggleSalesPanel(dateStr, event) {{
                  if (event) event.stopPropagation();
                  const panelId = `salesPanel_${{dateStr}}`;
                  togglePanel(panelId, null);
              }}
        </script>
    </body>
</html>
"""

def write_html_report(html_content, filename, output_dir):
    """将HTML内容写入文件"""
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, filename)
    
    # 强制垃圾回收，尝试释放文件句柄
    import gc
    gc.collect()
    
    # 重试机制
    max_retries = 3
    retry_delay = 1  # 延迟1秒
    
    for attempt in range(max_retries):
        try:
            # 使用临时文件方式写入，避免直接写入时的文件锁定问题
            temp_fd, temp_path = tempfile.mkstemp(suffix='.html', prefix=f"{filename.split('.')[0]}_temp_", dir=output_dir)
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                temp_file.write(html_content)
            
            # 如果目标文件存在，尝试删除它
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except PermissionError:
                    # 如果不能删除，尝试重命名原文件
                    backup_name = f"{filename.split('.')[0]}_{int(time.time())}_{random.randint(1000, 9999)}.bak.html"
                    backup_path = os.path.join(output_dir, backup_name)
                    os.rename(report_path, backup_path)
                    print(f"无法删除原文件，已将其重命名为: {backup_name}")
            
            # 将临时文件复制到目标路径
            shutil.copy2(temp_path, report_path)
            os.remove(temp_path)  # 删除临时文件
            
            print(f"报告已生成: {report_path}")
            # 如果成功写入，输出页面成功生成消息
            if filename == "index.html":
                print(f"index.html 页面已生成在 {output_dir}")
            elif filename == "details.html":
                print(f"details.html 页面已生成在 {output_dir}")
            elif filename == "price_volatility.html":
                print(f"price_volatility.html generated in {output_dir}")
            elif filename == "industry.html":
                print(f"industry.html 页面已生成在 {output_dir}")
            
            return report_path
            
        except Exception as e:
            print(f"写入报告 {filename} 时发生错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            import traceback
            traceback.print_exc()
            
            if attempt < max_retries - 1:
                print(f"将在 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 增加下一次等待时间
            else:
                print(f"无法写入报告 {filename}，达到最大重试次数。")
    
    return None

# Helper function to generate image tags safely
def generate_image_tag(image_filename, alt_text="", css_class="img-fluid"):
    """Generates an <img> tag, assuming image is relative to HTML file."""
    # In a multi-file setup, ensure the image path is correct relative to the HTML file.
    # If images and HTML are in the same output dir, just the filename is needed.
    return f'<img src="{image_filename}" alt="{alt_text}" class="{css_class}">' 