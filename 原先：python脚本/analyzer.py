# -*- coding: utf-8 -*-
"""
数据分析模块，包含价格波动分析的核心逻辑
"""

import pandas as pd
import numpy as np
from datetime import datetime

import config


class PriceAnalyzer:
    """价格分析类"""
    
    def __init__(self, all_data, sales_data=None, industry_trend_data=None, daily_production_data=None):
        """
        初始化价格分析器
        
        参数:
            all_data: 价格数据
            sales_data: 销售数据
            industry_trend_data: 行业趋势数据
            daily_production_data: 每日产量数据
        """
        self.all_data = all_data
        self.sales_data = sales_data
        self.industry_trend_data = industry_trend_data
        self.daily_production_data = daily_production_data
        
        # 初始化分析结果
        self.abnormal_changes = []
        self.inconsistent_records = []
        self.conflict_records = []
        self.product_sales_ratio_data = None
    
    def analyze_price_changes(self):
        """分析价格波动情况"""
        if self.all_data.empty:
            print("没有数据可供分析")
            return
        
        print("开始分析价格波动...")
        
        # 按品名、规格和日期排序
        self.all_data.sort_values(['品名', '规格', '日期', '调价次数'], inplace=True)
        
        # 计算价格变动（简化逻辑，只保留价格差异）
        self.all_data['价格变动'] = self.all_data['价格'] - self.all_data['前价格']
        
        # 价格差异阈值
        price_diff_threshold = 200  # 设置价格差异阈值为200元/吨
        
        # 计算价格差异的绝对值
        self.all_data['价格差异绝对值'] = self.all_data['价格变动'].abs()
        
        # 筛选出价格差异绝对值超过阈值的记录
        significant_records = self.all_data[self.all_data['价格差异绝对值'] >= price_diff_threshold]
        
        # 检查是否有符合条件的记录
        if not significant_records.empty:
            # 提取所需的字段，并添加价格差异
            self.conflict_records = significant_records[
                ['日期', '品名', '规格', '调价次数', '价格', '前价格']].copy()
            
            # 添加价格差异列
            self.conflict_records['价格差异'] = significant_records['价格变动']
            
            # 转换为字典列表
            self.conflict_records = self.conflict_records.to_dict('records')
            
            print(f"发现 {len(self.conflict_records)} 条价格差异绝对值≥{price_diff_threshold}的记录")
        else:
            self.conflict_records = []
            print(f"未发现价格差异绝对值≥{price_diff_threshold}的记录")
        
        # 以下为空列表，因为我们不再检测这两项
        self.abnormal_changes = []
        self.inconsistent_records = []
    
    def process_sales_data(self):
        """处理销售数据，按日期分组"""
        if self.sales_data is None or self.sales_data.empty:
            print("没有销售数据可供处理")
            return None
        
        try:
            # 按日期分组
            daily_sales = {}
            
            # 确保日期列是日期类型
            # self.sales_data['发票日期'] = pd.to_datetime(self.sales_data['发票日期'])
            # ^^^ This is now handled in load_sales_data, assuming '发票日期' is the correct date column name.
            # If not, ensure the correct date column from the loaded self.sales_data is used here.
            date_column_for_grouping = '发票日期' # Match the one used in load_sales_data
            if date_column_for_grouping not in self.sales_data.columns:
                print(f"错误：process_sales_data 期望的日期列 '{date_column_for_grouping}' 不在 self.sales_data 中。")
                return None

            # 检查必要的列是否存在 (物料名称, 本币无税金额, 主数量)
            # '主数量' is now the fixed quantity column.
            required_columns = ['物料名称', '本币无税金额', '主数量']
            missing_columns = [col for col in required_columns if col not in self.sales_data.columns]
            
            if missing_columns:
                print(f"处理销售数据时缺少必要的列: {', '.join(missing_columns)}")
                print(f"self.sales_data 中的可用列名: {self.sales_data.columns.tolist()}")
                return None
            
            # 固定使用 '主数量' 作为数量列
            quantity_column = '主数量'
            print(f"process_sales_data 固定使用 '{quantity_column}' 作为数量列。")

            # 确保 '主数量' 列是数值类型 (this should have been handled by load_sales_data)
            # Adding a check here for robustness before aggregation.
            if not pd.api.types.is_numeric_dtype(self.sales_data[quantity_column]):
                print(f"警告: '{quantity_column}' 列在传入 process_sales_data 时不是数值类型。尝试转换...")
                self.sales_data[quantity_column] = pd.to_numeric(self.sales_data[quantity_column], errors='coerce')
                # Potentially dropna again if conversion creates new NaNs, though load_sales_data should handle this.
                # self.sales_data = self.sales_data.dropna(subset=[quantity_column])
            
            # 按日期分组
            for date_group_key, group in self.sales_data.groupby(self.sales_data[date_column_for_grouping].dt.date):
                # 选择需要的列 (物料名称, 本币无税金额, 主数量)
                # Ensure we copy to avoid SettingWithCopyWarning if group is modified later for '含税单价'
                group_for_processing = group[['物料名称', '本币无税金额', quantity_column]].copy()
                
                # 计算日销售总额
                daily_total_amount = group_for_processing['本币无税金额'].sum()
                
                # 计算日销量 (来自 '主数量')
                daily_volume = group_for_processing[quantity_column].sum()
                
                # 计算日均价 (元/吨)
                daily_avg_price = None
                if daily_volume > 0: # Avoid division by zero
                    # Formula: 金额 / 销量(kg) * 1.09 * 1000 = 元/吨 (含税)
                    # Assuming '本币无税金额' and '主数量' (in KG)
                    daily_avg_price = (daily_total_amount / daily_volume) * 1.09 * 1000
                
                # 计算每个产品的含税单价 (based on '主数量')
                # Add '含税单价' to group_for_processing to avoid modifying original 'group' slice if not needed elsewhere
                mask = group_for_processing[quantity_column] > 0
                group_for_processing.loc[mask, '含税单价'] = (group_for_processing.loc[mask, '本币无税金额'] / 
                                                          group_for_processing.loc[mask, quantity_column]) * 1.09 * 1000
                group_for_processing.loc[~mask, '含税单价'] = None # Set to None or np.nan where quantity is 0 or less
                
                # 按物料名称汇总 (金额和销量)
                summary_agg_dict = {
                    '本币无税金额': 'sum',
                    quantity_column: 'sum' # Aggregate '主数量'
                }
                # Only add '含税单价' to groupby if it was successfully calculated
                # For simplicity, we calculate mean of (potentially sparse) '含税单价' after primary aggregation

                summary = group_for_processing.groupby('物料名称', as_index=False).agg(summary_agg_dict)
                
                # 计算并映射平均含税单价 (mean of individual product unit prices for that day)
                if '含税单价' in group_for_processing.columns:
                    avg_prices_per_material = group_for_processing.groupby('物料名称')['含税单价'].mean()
                    summary = summary.merge(avg_prices_per_material.rename('含税单价'), on='物料名称', how='left')
                
                # 存储到字典中
                daily_sales[date_group_key] = {
                    'data': summary, # DataFrame with '物料名称', '本币无税金额', '主数量', '含税单价'
                    'total_amount': daily_total_amount,
                    'volume': daily_volume, # This is total daily sales from '主数量'
                    'avg_price': daily_avg_price, # Overall daily average price
                    'quantity_column': quantity_column, # Name of the quantity column used ('主数量')
                    'product_count': len(summary)
                }
            
            return daily_sales
        
        except Exception as e:
            print(f"处理销售数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()  # 打印详细的错误堆栈
            return None
    
    def calculate_production_sales_ratio(self, sales_data, production_data):
        """计算每日产销率"""
        import pandas as pd
        
        # 添加数据类型检查和转换
        print(f"calculate_production_sales_ratio - sales_data类型: {type(sales_data)}")
        print(f"calculate_production_sales_ratio - production_data类型: {type(production_data)}")
        
        if sales_data is None or production_data is None:
            print("警告: 无法计算产销率，销售数据或生产数据为空")
            return {}
        
        print("计算产销率...")
        
        # 检查sales_data字段
        print(f"销售数据列: {list(sales_data.columns)}")
        
        # 确定日期列名称
        sales_date_column = None
        for column in ['date', '发票日期', '日期']:
            if column in sales_data.columns:
                sales_date_column = column
                print(f"找到销售数据日期列: '{sales_date_column}'")
                break
        
        # 如果没有找到日期列，尝试猜测含"日期"的列
        if not sales_date_column:
            for column in sales_data.columns:
                if '日期' in column or 'date' in column.lower():
                    sales_date_column = column
                    print(f"使用销售数据列: '{sales_date_column}' 作为日期列")
                    break
        
        if not sales_date_column:
            print("错误: 销售数据中找不到日期列")
            return {}
        
        # 检查production_data字段
        print(f"生产数据列: {list(production_data.columns)}")
        
        # 确定生产数据日期列名称
        production_date_column = None
        for column in ['date', '入库日期', '日期']:
            if column in production_data.columns:
                production_date_column = column
                print(f"找到生产数据日期列: '{production_date_column}'")
                break
        
        # 如果没有找到日期列，尝试猜测含"日期"的列
        if not production_date_column:
            for column in production_data.columns:
                if '日期' in column or 'date' in column.lower():
                    production_date_column = column
                    print(f"使用生产数据列: '{production_date_column}' 作为日期列")
                    break
        
        if not production_date_column:
            print("错误: 生产数据中找不到日期列")
            return {}
        
        # 确保日期列是日期类型
        sales_data[sales_date_column] = pd.to_datetime(sales_data[sales_date_column], errors='coerce')
        production_data[production_date_column] = pd.to_datetime(production_data[production_date_column], errors='coerce')
        
        # 获取销售量列名
        quantity_column = None
        for col in ['销量', '主数量', '数量']:
            if col in sales_data.columns:
                quantity_column = col
                break
        
        if not quantity_column:
            print("警告: 未找到销售量列，无法计算产销率")
            return {}
        
        # 获取生产量列名
        production_column = None
        for col in ['产量', '入库数量', '主数量']:
            if col in production_data.columns:
                production_column = col
                break
        
        if not production_column:
            print("警告: 未找到生产量列，无法计算产销率")
            return {}
        
        # 按日期分组计算销售量
        daily_sales = {}
        try:
            sales_grouped = sales_data.groupby(sales_data[sales_date_column].dt.date)[quantity_column].sum()
            
            for date, sales_volume in sales_grouped.items():
                daily_sales[date] = sales_volume
            
            print(f"成功计算 {len(daily_sales)} 天的销售量")
        except Exception as e:
            print(f"警告: 计算每日销售量时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        # 按日期分组计算生产量
        daily_production = {}
        try:
            production_grouped = production_data.groupby(production_data[production_date_column].dt.date)[production_column].sum()
            
            for date, production_volume in production_grouped.items():
                daily_production[date] = production_volume
            
            print(f"成功计算 {len(daily_production)} 天的生产量")
        except Exception as e:
            print(f"警告: 计算每日生产量时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        # 计算产销率
        production_sales_ratio = {}
        
        # 获取所有唯一日期
        all_dates = sorted(set(list(daily_sales.keys()) + list(daily_production.keys())))
        
        for date in all_dates:
            # 为防止除零错误，需要检查生产量
            sales = daily_sales.get(date, 0)
            production = daily_production.get(date, 0)
            
            # 使用与产销率明细卡片相同的计算方法：产销率 = 销量/产量 × 100%
            if production > 0:
                ratio = (sales / production) * 100
                
                # 处理异常值，避免图表比例失调
                if ratio > 500:  # 设置上限阈值
                    print(f"警告: {date} 的产销率异常高: {ratio:.2f}%，将被限制为500%")
                    ratio = 500
            else:
                ratio = 0
                if sales > 0:
                    print(f"警告: {date} 有销售但无生产记录")
            
            production_sales_ratio[date] = {
                'sales': sales,
                'production': production,
                'ratio': ratio
            }
            
        print(f"成功计算 {len(production_sales_ratio)} 天的产销率数据")
        return production_sales_ratio
    
    def analyze_product_sales_ratio(self):
        """分析每日产品级别的产销率"""
        import pandas as pd
        
        # 添加详细调试信息
        print("================= 开始分析产品产销率明细 =================")
        print(f"sales_data类型: {type(self.sales_data)}")
        print(f"daily_production_data类型: {type(self.daily_production_data)}")
        
        # 记录处理的结果
        result = []
        
        # 获取销售和产量数据
        sales_data = self.sales_data
        daily_production_data = self.daily_production_data
        
        # 检查销售数据结构
        if sales_data is None:
            print("警告: 销售数据为空")
            return []
        
        if isinstance(sales_data, pd.DataFrame):
            print("销售数据是DataFrame，但需要处理成by_material格式")
            # 转换销售数据为by_material格式
            try:
                # 确保有日期列和数量列
                if '发票日期' in sales_data.columns:
                    date_column = '发票日期'
                else:
                    # 尝试找到日期列
                    date_columns = [col for col in sales_data.columns if 'date' in col.lower() or '日期' in col]
                    if date_columns:
                        date_column = date_columns[0]
                        print(f"使用列 '{date_column}' 作为日期列")
                    else:
                        print("错误: 销售数据中没有找到日期列")
                        return []
                
                # 查找数量列
                quantity_column = None
                for col in sales_data.columns:
                    if '数量' in col or '重量' in col or '公斤' in col or 'kg' in col.lower():
                        quantity_column = col
                        print(f"找到数量/重量列: '{quantity_column}'")
                        break
                
                if not quantity_column:
                    print("错误: 销售数据中没有找到数量列")
                    return []
                
                # 确保日期列是日期类型
                sales_data[date_column] = pd.to_datetime(sales_data[date_column], errors='coerce')
                
                # 按日期和品名分组
                sales_by_material = {}
                
                for (date, name), group in sales_data.groupby([sales_data[date_column].dt.date, '物料名称']):
                    if date not in sales_by_material:
                        sales_by_material[date] = {}
                    
                    # 累加同一天同一品名的数量
                    sales_by_material[date][name] = group[quantity_column].sum()
                
                # 创建符合要求的字典结构
                by_material_dict = {'by_material': sales_by_material}
                sales_data = by_material_dict
                print(f"已转换销售数据为by_material格式，包含 {len(sales_by_material)} 天数据")
            except Exception as e:
                print(f"转换销售数据时出错: {e}")
                import traceback
                traceback.print_exc()
                return []
        elif not isinstance(sales_data, dict) or 'by_material' not in sales_data:
            print(f"警告: 销售数据格式不是by_material字典: {type(sales_data)}")
            return []
        
        # 转换数据格式确保类型正确
        if isinstance(daily_production_data, dict) and 'by_material' in daily_production_data:
            production_by_material = daily_production_data['by_material']
            print(f"产量数据正确，包含 {len(production_by_material)} 天数据")
        else:
            print(f"警告: 产量数据格式不正确: {type(daily_production_data)}")
            return []
        
        # 显示销售数据中的日期
        sales_by_material = sales_data['by_material']
        print(f"销售数据日期: {list(sales_by_material.keys())[:5]}...")
        print(f"产量数据日期: {list(production_by_material.keys())[:5]}...")
        
        # 遍历每一天的数据
        common_dates = set(sales_by_material.keys()) & set(production_by_material.keys())
        print(f"销售数据和产量数据共有 {len(common_dates)} 天重叠")
        
        for date in production_by_material:
            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
            print(f"处理日期: {date_str}")
            
            # 获取当天产量数据
            day_production = production_by_material[date]
            
            # 获取当天销量数据
            day_sales = {}
            if date in sales_by_material:
                day_sales = sales_by_material[date]
            
            # 创建产品级别产销率DataFrame
            product_data = []
            
            # 合并所有产品
            all_products = set(day_production.keys()) | set(day_sales.keys())
            
            for product in all_products:
                # 获取产量和销量
                production_qty = day_production.get(product, 0)
                sales_qty = day_sales.get(product, 0)
                
                # 计算产销率
                sales_ratio = (sales_qty / production_qty * 100) if production_qty > 0 else 0
                
                product_data.append({
                    '品名': product,
                    '销量': sales_qty,
                    '产量': production_qty,
                    '产销率': sales_ratio
                })
            
            # 创建DataFrame
            if product_data:
                product_df = pd.DataFrame(product_data)
                result.append({
                    'date': date,
                    'data': product_df
                })
                print(f"添加了日期 {date_str} 的产销率数据，包含 {len(product_data)} 个产品")
            else:
                print(f"日期 {date_str} 没有有效的产品产销率数据")
        
        print(f"总共生成了 {len(result)} 天的产品产销率明细数据")
        print("================= 结束分析产品产销率明细 =================")
        return result
    
    def calculate_product_sales_ratio_detail(self, daily_sales_data, daily_production_data):
        """计算每日产品产销率明细"""
        print("计算每日产品产销率明细...")
        
        daily_sales_by_material = daily_sales_data['by_material']
        daily_production_by_material = daily_production_data['by_material']
        
        product_sales_ratio_data = []
        
        # 获取所有日期
        all_dates = sorted(set(list(daily_sales_by_material.keys()) + list(daily_production_by_material.keys())))
        
        for date in all_dates:
            sales_data = daily_sales_by_material.get(date, {})
            production_data = daily_production_by_material.get(date, {})
            
            # 合并所有产品
            all_products = set(list(sales_data.keys()) + list(production_data.keys()))
            
            # 为每个产品计算产销率
            product_data = []
            for product in all_products:
                sales = sales_data.get(product, 0)
                production = production_data.get(product, 0)
                
                # 计算产销率 - 修改后的逻辑
                if production != 0:  # 只要产量不为0，就计算产销率
                    ratio = (sales / production) * 100
                else:
                    ratio = 0  # 产量为0时，产销率为0
                
                product_data.append({
                    '品名': product,
                    '销量': sales,
                    '产量': production,
                    '产销率': ratio
                })
            
            # 按产销率降序排序
            if product_data:
                df = pd.DataFrame(product_data)
                df = df.sort_values(by=['产销率'], ascending=False)
                
                # 添加到结果列表
                product_sales_ratio_data.append({
                    'date': date,
                    'data': df
                })
        
        print(f"计算了 {len(product_sales_ratio_data)} 天的产品产销率明细")
        return product_sales_ratio_data 