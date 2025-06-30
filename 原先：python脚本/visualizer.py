# -*- coding: utf-8 -*-
"""
可视化模块，负责生成各种图表
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import pandas as pd
import seaborn as sns
from datetime import datetime
import matplotlib
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.font_manager import FontProperties
import matplotlib.ticker as mticker

# 设置中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
matplotlib.rcParams['xtick.labelsize'] = 12  # 增大x轴标签字体大小
matplotlib.rcParams['ytick.labelsize'] = 12  # 增大y轴标签字体大小
matplotlib.rcParams['axes.titlesize'] = 14  # 增大标题字体大小
matplotlib.rcParams['axes.labelsize'] = 12  # 增大轴标签字体大小

import config


class DataVisualizer:
    """数据可视化类，负责生成各种图表"""
    
    def __init__(self, output_dir=None):
        """
        初始化可视化器
        
        参数:
            output_dir: 输出目录
        """
        self.output_dir = output_dir or config.OUTPUT_DIR
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_abnormal_timeline(self, abnormal_changes):
        """
        生成异常波动时间轴图
        
        参数:
            abnormal_changes: 异常波动记录
        
        返回:
            chart_path: 生成的图表文件路径
        """
        if not abnormal_changes:
            print("没有异常波动数据，无法生成时间轴图")
            return None
        
        try:
            # 转换为DataFrame
            abnormal_df = pd.DataFrame(abnormal_changes)
            abnormal_counts = abnormal_df.groupby('日期').size()
            
            plt.figure(figsize=(12, 6))
            sns.lineplot(x=abnormal_counts.index, y=abnormal_counts.values, marker='o', linewidth=2)
            plt.title('异常波动时间轴')
            plt.xlabel('日期')
            plt.ylabel('异常波动产品数量')
            plt.grid(True)
            plt.tight_layout()
            
            # 保存图表
            chart_path = os.path.join(self.output_dir, 'abnormal_timeline.png')
            plt.savefig(chart_path, dpi=300)
            plt.close()
            
            print(f"异常波动时间轴图已保存至: {chart_path}")
            return chart_path
        
        except Exception as e:
            print(f"生成异常波动时间轴图出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_inventory_visualization(self, inventory_data):
        """
        生成库存可视化图表
        
        参数:
            inventory_data: 库存数据
        
        返回:
            chart_path: 生成的图表文件路径
        """
        if inventory_data is None or inventory_data.empty:
            print("没有库存数据可供可视化")
            return None
        
        try:
            plt.figure(figsize=(12, 7))
            # Assuming '库存量' is the column to plot
            # Let's plot top N items by inventory
            top_n = 15
            plot_data = inventory_data.nlargest(top_n, '库存量')

            bars = plt.bar(plot_data['品名'], plot_data['库存量'], color='skyblue') # Store the bars
            plt.xlabel('产品名称')
            plt.ylabel('库存量')
            plt.title(f'库存量最高的 {top_n} 种产品')
            plt.xticks(rotation=45, ha='right')

            # --- Add value labels on top of bars --- 
            for bar in bars:
                height = bar.get_height()
                if height > 0: # Only label bars with positive height
                    plt.annotate(f'{height:,.0f}', # Format as integer with comma
                                 xy=(bar.get_x() + bar.get_width() / 2, height),
                                 xytext=(0, 3),  # 3 points vertical offset
                                 textcoords="offset points",
                                 ha='center', va='bottom',
                                 fontsize=9) # Adjust font size if needed
            # --- End value labels ---

            plt.tight_layout()

            chart_path = os.path.join(self.output_dir, 'inventory_top_items.png')
            plt.savefig(chart_path, dpi=150)
            plt.close()
            print(f"Inventory visualization saved to {chart_path}")
            return chart_path
        except Exception as e:
            print(f"Error generating inventory visualization: {e}")
            return None
    
    def generate_daily_sales_trend(self, daily_sales):
        """
        生成每日销售情况折线图
        
        参数:
            daily_sales: 每日销售数据
        
        返回:
            chart_path: 生成的图表文件路径
        """
        if not daily_sales or len(daily_sales) == 0:
            print("没有销售数据，无法生成销售趋势图")
            return None
        
        try:
            # Prepare data for plotting
            dates = sorted(daily_sales.keys())
            volumes = [daily_sales[d].get('volume', 0) for d in dates]
            avg_prices = [daily_sales[d].get('avg_price') for d in dates]
            # Convert price Nones to NaN for plotting, handle non-numeric gracefully
            numeric_prices = []
            for p in avg_prices:
                try:
                    numeric_prices.append(float(p) if p is not None else None)
                except (ValueError, TypeError):
                    numeric_prices.append(None) # Treat unconvertible values as None
            avg_prices = numeric_prices

            # Create figure and axes
            fig, ax1 = plt.subplots(figsize=(15, 8)) # Keep standard size

            # Plot daily sales volume (left y-axis)
            color = 'tab:blue'
            ax1.set_xlabel('日期')
            ax1.set_ylabel('日销量 (公斤/单位)', color=color)
            ax1.plot(dates, volumes, color=color, marker='o', linestyle='-', label='日销量')
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.tick_params(axis='x', rotation=45)
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)
            # Format Y-axis with commas
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))

            # Create a second y-axis for average price (right y-axis)
            ax2 = ax1.twinx()
            color = 'tab:red'
            ax2.set_ylabel('日均含税单价 (元/吨)', color=color)
            ax2.plot(dates, avg_prices, color=color, marker='x', linestyle='--', label='日均价')
            ax2.tick_params(axis='y', labelcolor=color)
             # Format Y-axis with commas
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: format(int(x), ',')))

            # Add annotations (labels on points) - Modified for mobile
            for i, (volume, price) in enumerate(zip(volumes, avg_prices)):
                 # Sales volume annotation (less dense)
                 if (i % 2 == 0 or i == len(volumes)-1) and pd.notna(volume):
                    ax1.annotate(f'{volume:,.0f}',
                                   xy=(dates[i], volume),
                                   xytext=(0, 10), # Offset slightly above
                                   textcoords='offset points',
                                   ha='center', va='bottom',
                                   color='tab:blue',
                                   fontsize=9)

                 # Average price annotation (less dense)
                 if (i % 2 == 1 or i == len(avg_prices)-1) and pd.notna(price):
                    ax2.annotate(f'{price:,.0f}',
                                   xy=(dates[i], price),
                                   xytext=(0, -15), # Offset slightly below
                                   textcoords='offset points',
                                   ha='center', va='top',
                                   color='tab:red',
                                   fontsize=9)

            # Add title and legend
            plt.title('每日销售量与平均单价趋势', fontsize=16)
            # Combine legends from both axes
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Improve layout
            plt.tight_layout(pad=1.2) # Keep padding

            # Save the chart
            chart_path = os.path.join(self.output_dir, 'daily_sales_trend.png')
            plt.savefig(chart_path, dpi=300, bbox_inches='tight') # Keep high DPI
            plt.close()
            print(f"Daily sales trend chart saved to {chart_path}")
            return chart_path
        except Exception as e:
            print(f"Error generating daily sales trend chart: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_production_sales_ratio_visualization(self, production_sales_ratio, output_file="production_sales_ratio.png"):
        """生成产销率趋势图"""
        # 这里的逻辑不需要修改，因为它使用的是已经计算好的产销率数据
        # 但可以更新图表标题或说明，明确数据来源
        
        plt.figure(figsize=(12, 6))
        # ... 绘图代码 ...
        plt.title("产销率趋势 (数据来源: 产成品入库列表 & 销售发票执行查询)", fontsize=14)
        # ... 其他绘图代码 ...
    
    def generate_production_sales_ratio_chart(self, ratio_summary, chart_path):
        """Generates production vs. sales ratio line chart with filled areas."""
        if not ratio_summary:
            print("No ratio summary data to visualize.")
            return None

        try:
            dates = sorted(ratio_summary.keys())
            ratios = np.array([ratio_summary[d].get('ratio', 0) for d in dates])

            # 增加图表尺寸以提高清晰度
            plt.figure(figsize=(15, 8))
            ax = plt.gca()

            # Plot the main ratio line
            line, = ax.plot(dates, ratios, marker='o', linestyle='-', color='purple', linewidth=2, markersize=6, label='综合产销率')

            # --- Add fill_between logic back --- 
            baseline = 100
            # Fill green where ratio > 100 (Consuming inventory)
            ax.fill_between(dates, ratios, baseline,
                              where=ratios >= baseline,
                              interpolate=True,
                              color='lightgreen', alpha=0.4, label='消耗库存区 (>100%)')
            # Fill red where ratio < 100 (Accumulating inventory)
            ax.fill_between(dates, ratios, baseline,
                              where=ratios <= baseline,
                              interpolate=True,
                              color='lightcoral', alpha=0.4, label='库存积压区 (<100%)')
            # --- End fill_between logic ---

            # Highlight points > 100%
            for i, r_val in enumerate(ratios):
                if r_val > 100:
                    ax.scatter(dates[i], r_val, color='darkred', s=60, zorder=5)
                # Add annotations (with increased font size)
                if i % 2 == 0 or i == len(ratios) - 1:
                   ax.annotate(f'{r_val:.0f}%',
                                 xy=(dates[i], r_val),
                                 xytext=(0, 8),
                                 textcoords='offset points',
                                 ha='center',
                                 fontsize=10)

            # Plot baseline after fills for visibility
            ax.axhline(baseline, color='grey', linestyle='--', linewidth=1.5, label='100%基准线') 

            # Set labels and title
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('综合产销率 (%)', fontsize=12)
            ax.set_title('每日综合产销率趋势 (销量/产量)', fontsize=16)
            
            # 添加数据来源说明
            plt.figtext(0.5, 0.01, 
                      '数据来源：产成品入库列表 & 销售发票执行查询（排除客户名称为空、副产品、鲜品的记录）',
                      ha='center', fontsize=9, color='#555555')
            
            # 设置x轴日期格式，只显示月-日，去除时间信息
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            plt.xticks(rotation=45, fontsize=10, ha='right')
            plt.yticks(fontsize=10)
            ax.set_ylim(bottom=0)
            ax.grid(True, linestyle='--', alpha=0.6)

            # --- Create combined legend --- 
            handles, labels = ax.get_legend_handles_labels()
            # Create custom patches for fill explanation (optional if fill_between label is sufficient)
            # green_patch = mpatches.Patch(color='lightgreen', alpha=0.4, label='消耗库存区 (>100%)')
            # red_patch = mpatches.Patch(color='lightcoral', alpha=0.4, label='库存积压区 (<100%)')
            # handles.extend([green_patch, red_patch]) # Add patches to legend if created
            
            # Use legend handles generated by plot and fill_between
            ax.legend(handles=handles, labels=labels, fontsize=10, loc='best')
            # --- End combined legend --- 

            plt.tight_layout(pad=1.2)
            # 增加DPI以提高图表清晰度
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Production/Sales ratio chart saved to {chart_path}")
            return chart_path
        except Exception as e:
            print(f"Error generating production/sales ratio chart: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_comprehensive_price_chart(self, price_data, output_path=None):
        """
        生成综合售价折线图
        
        参数:
            price_data: DataFrame，包含factory(工厂)、date(日期)和price(价格)列
            output_path: 输出图片路径
        """
        if price_data.empty:
            print("警告: 无法生成综合售价图表，数据为空")
            return None
        
        if output_path is None:
            output_path = os.path.join(self.output_dir, "comprehensive_price_chart.png")
        
        try:
            # 创建图表
            plt.figure(figsize=(14, 7))
            
            # 获取不同的工厂
            factories = price_data['factory'].unique()
            
            # 定义不同厂家的样式
            styles = {
                '加工一厂': {'color': '#1f77b4', 'marker': 'o', 'linestyle': '-', 'linewidth': 2, 'markersize': 6},
                '加工二厂': {'color': '#ff7f0e', 'marker': 's', 'linestyle': '-', 'linewidth': 2, 'markersize': 6},
                '行业（早创资讯）': {'color': '#2ca02c', 'marker': '^', 'linestyle': '--', 'linewidth': 1.5, 'markersize': 5}
            }
            
            # 绘制每个工厂的价格折线图
            for factory in factories:
                factory_data = price_data[price_data['factory'] == factory]
                # 使用预定义样式，如果没有则使用默认样式
                style = styles.get(factory, {'color': 'black', 'marker': 'x', 'linestyle': '-', 'linewidth': 1, 'markersize': 4})
                
                plt.plot(
                    factory_data['date'], 
                    factory_data['price'],
                    label=factory,
                    marker=style['marker'],
                    color=style['color'],
                    linestyle=style['linestyle'],
                    linewidth=style['linewidth'],
                    markersize=style['markersize']
                )
                
                # 为每个数据点添加价格标签
                for _, row in factory_data.iterrows():
                    plt.text(
                        row['date'], 
                        row['price'] + 20,  # 稍微上移，避免遮挡
                        f"{row['price']:.0f}",
                        ha='center',
                        va='bottom',
                        fontsize=8,
                        color=style['color']
                    )
            
            # 设置图表标题和轴标签
            plt.title('综合售价趋势图', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('日期', fontsize=12)
            plt.ylabel('价格 (元)', fontsize=12)
            
            # 设置x轴日期格式
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m.%d'))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
            
            # 添加网格线
            plt.grid(True, linestyle='--', alpha=0.3)
            
            # 添加图例，放在右上角
            plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True, fontsize=10)
            
            # 旋转x轴标签以防重叠
            plt.xticks(rotation=45)
            
            # 自动调整布局
            plt.tight_layout()
            
            # 保存图表
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"综合售价图表已生成: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成综合售价图表时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None 

    def generate_responsive_image(self, standard_image_path, output_dir):
        """为移动端生成优化版本的图片"""
        try:
            from PIL import Image
            import os
          
            # 获取原图路径
            base_name = os.path.basename(standard_image_path)
            file_name, file_ext = os.path.splitext(base_name)
          
            # 生成移动端版本路径
            mobile_path = os.path.join(output_dir, f"{file_name}_mobile{file_ext}")
          
            # 使用PIL打开图片
            img = Image.open(standard_image_path)
          
            # 获取原始尺寸
            width, height = img.size
          
            # 移动端尺寸（保持宽高比）
            mobile_width = 600  # 适合大多数移动设备
            mobile_height = int(height * (mobile_width / width))
          
            # 调整大小并保存
            mobile_img = img.resize((mobile_width, mobile_height), Image.LANCZOS) # Use Image.LANCZOS for high quality resize
            mobile_img.save(mobile_path, quality=85, optimize=True)
          
            return mobile_path
        except ImportError:
            print("Pillow library not found. Skipping responsive image generation. Install with: pip install Pillow")
            return standard_image_path # Return original path if Pillow is missing
        except Exception as e:
            print(f"生成响应式图像失败: {e}")
            return standard_image_path


# Example usage (if run directly)
if __name__ == '__main__':
    # Example: Create dummy daily sales data
    dummy_sales_data = {
        datetime(2023, 10, 1): {'volume': 5000, 'avg_price': 15000},
        datetime(2023, 10, 2): {'volume': 5500, 'avg_price': 15200},
        datetime(2023, 10, 3): {'volume': 4800, 'avg_price': 15100},
        datetime(2023, 10, 4): {'volume': 6000, 'avg_price': None}, # Test None price
        datetime(2023, 10, 5): {'volume': 5200, 'avg_price': 'invalid'}, # Test invalid price
        datetime(2023, 10, 6): {'volume': 5800, 'avg_price': 15500},
    }
    # Example: Create dummy ratio data
    dummy_ratio_data = {
        datetime(2023, 10, 1): {'ratio': 95.5},
        datetime(2023, 10, 2): {'ratio': 105.2},
        datetime(2023, 10, 3): {'ratio': 88.0},
        datetime(2023, 10, 4): {'ratio': 110.0},
        datetime(2023, 10, 5): {'ratio': 92.3},
        datetime(2023, 10, 6): {'ratio': 101.8},
    }

    visualizer = DataVisualizer(output_dir='./test_visuals')
    # Generate sales trend chart
    sales_chart = visualizer.generate_daily_sales_trend(dummy_sales_data)
    if sales_chart:
         print(f"Sales chart generated: {sales_chart}")
         # Test responsive image generation
         mobile_sales_chart = visualizer.generate_responsive_image(sales_chart, visualizer.output_dir)
         print(f"Mobile sales chart potentially generated: {mobile_sales_chart}")

    # Generate ratio chart
    ratio_chart_path = os.path.join(visualizer.output_dir, "test_ratio_chart.png")
    ratio_chart = visualizer.generate_production_sales_ratio_chart(dummy_ratio_data, ratio_chart_path)
    if ratio_chart:
         print(f"Ratio chart generated: {ratio_chart}")

    # Add other chart generation tests if needed
    print("Visualization tests completed.") 