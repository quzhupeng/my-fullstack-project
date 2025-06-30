# -*- coding: utf-8 -*-
"""
数据加载模块，处理各种数据源的加载和预处理
"""

import os
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob

import config


def extract_date_info(sheet_name):
    """
    从sheet名称中提取日期和调价次数信息
  
    参数:
        sheet_name: sheet名称，如'价格表4月2号（2）'或'价格表4月2号'
      
    返回:
        (month, day, change_count): 月份、日期和调价次数的元组，或者None
    """
    # 新的正则表达式模式，匹配"价格表X月Y号"和"价格表X月Y号（Z）"格式
    # 使用中文括号
    pattern = r'价格表(\d+)月(\d+)号(?:（(\d+)）)?'
    match = re.match(pattern, sheet_name)
  
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        # 如果group(3)存在，说明有括号内的数字，否则默认为1
        change_count = int(match.group(3)) if match.group(3) else 1
        return (month, day, change_count)
  
    # 保留原来的模式匹配作为备选，以防有些sheet还使用旧格式 (例如 4.2(2))
    old_pattern = r'(\d+)\.(\d+)(?:\((\d+)\))?' # Ensure correct escaping for literal dots and parens
    match = re.match(old_pattern, sheet_name)
  
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        change_count = int(match.group(3)) if match.group(3) else 1
        return (month, day, change_count)

    print(f"无法从sheet名称 '{sheet_name}' 中提取日期信息，跳过处理") # Add print statement for debugging
    return None


class DataLoader:
    """数据加载和预处理类"""
    
    def __init__(self):
        """初始化数据加载器"""
        self.all_data = pd.DataFrame()
        self.inventory_data = None
        self.sales_data = None
        self.daily_production_data = None
        self.industry_trend_data = None
        self.missing_dates = []
        
    def preprocess_sheet(self, df, sheet_name):
        """
        预处理单个sheet中的数据，将三个并排的模板纵向合并
        
        参数:
            df: 原始DataFrame
            sheet_name: sheet名称
            
        返回:
            processed_df: 处理后的DataFrame
        """
        # 提取日期信息
        date_info = extract_date_info(sheet_name)
        if not date_info:
            print(f"无法从sheet名称 '{sheet_name}' 中提取日期信息，跳过处理")
            return None
        
        month, day, change_count = date_info
        date_str = f"2025-{month:02d}-{day:02d}"  # 假设年份为2025
        
        # 检查数据是否为空
        if df.empty:
            print(f"Sheet '{sheet_name}' 中没有数据，跳过处理")
            return None
        
        # 定义三个模板的列范围
        templates = [
            (0, 9),   # 第一个模板: 列0-8
            (9, 18),  # 第二个模板: 列9-17
            (18, 27)  # 第三个模板: 列18-26
        ]
        
        # 创建一个空的DataFrame来存储合并后的数据
        merged_data = []
        
        # 处理每个模板
        for start_col, end_col in templates:
            if start_col >= df.shape[1]:
                continue  # 如果列数不够，跳过此模板
            
            # 提取当前模板的数据
            template_df = df.iloc[:, start_col:end_col].copy()
            
            # 重命名列
            if template_df.shape[1] >= 9:  # 确保列数足够
                template_df.columns = [
                    '分类', '品名', '规格',
                    '加工一厂-调幅', '加工一厂-前价格', '加工一厂-价格',
                    '加工二厂-调幅', '加工二厂-前价格', '加工二厂-价格'
                ]
                
                # 删除空行
                template_df = template_df.dropna(subset=['品名'], how='all')
                
                # 忽略所有包含"均价"或"品名"的行
                template_df = template_df[~template_df['品名'].astype(str).str.contains('均价|品名')]
                
                # 只保留加工二厂的数据
                template_df = template_df[['分类', '品名', '规格', '加工二厂-调幅', '加工二厂-前价格', '加工二厂-价格']]
                template_df.columns = ['分类', '品名', '规格', '调幅', '前价格', '价格']
                
                # 添加日期和调价次数信息
                template_df['日期'] = date_str
                template_df['调价次数'] = change_count
                
                merged_data.append(template_df)
        
        # 合并所有模板的数据
        if merged_data:
            processed_df = pd.concat(merged_data, ignore_index=True)
            
            # 删除重复行
            processed_df = processed_df.drop_duplicates(subset=['品名', '规格'], keep='first')
            
            # 确保数值列为数值类型
            for col in ['调幅', '前价格', '价格']:
                processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            return processed_df
        
        return None
    
    def load_and_process_price_data(self, data_path=None):
        """加载并处理价格数据"""
        print("开始加载和处理价格数据...")
        
        if data_path is None:
            data_path = config.DATA_PATH
        
        # 检查路径是文件还是目录
        if os.path.isfile(data_path):
            # 如果是文件，直接处理这个文件
            excel_files = [os.path.basename(data_path)]
            file_dir = os.path.dirname(data_path)
        elif os.path.isdir(data_path):
            # 如果是目录，获取目录中的所有Excel文件
            excel_files = [f for f in os.listdir(data_path) if f.endswith('.xlsx') or f.endswith('.xls')]
            file_dir = data_path
        else:
            print(f"路径 {data_path} 既不是文件也不是目录")
            return
        
        if not excel_files:
            print(f"在路径 {data_path} 中没有找到Excel文件")
            return
        
        all_sheets_data = []
        date_records = set()  # 用于记录已处理的日期
        
        for file in excel_files:
            if os.path.isfile(data_path):
                file_path = data_path
            else:
                file_path = os.path.join(file_dir, file)
            
            print(f"处理文件: {file}")
            
            try:
                # 读取Excel文件中的所有sheet
                excel = pd.ExcelFile(file_path)
                
                # 按照日期顺序排序sheet
                def sheet_sort_key(sheet_name):
                    date_info = extract_date_info(sheet_name)
                    if date_info:
                        month, day, count = date_info
                        return (month, day, count)
                    return (0, 0, 0)
                
                sorted_sheets = sorted(excel.sheet_names, key=sheet_sort_key)
                
                for sheet_name in sorted_sheets:
                    print(f"  处理sheet: {sheet_name}")
                    
                    # 读取sheet数据
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # 预处理sheet数据
                    processed_df = self.preprocess_sheet(df, sheet_name)
                    
                    if processed_df is not None and not processed_df.empty:
                        all_sheets_data.append(processed_df)
                        
                        # 记录日期
                        date_info = extract_date_info(sheet_name)
                        if date_info:
                            month, day, _ = date_info
                            date_records.add((month, day))
            
            except Exception as e:
                print(f"处理文件 {file} 时出错: {str(e)}")
        
        # 合并所有sheet的数据
        if all_sheets_data:
            self.all_data = pd.concat(all_sheets_data, ignore_index=True)
            print(f"成功加载 {len(self.all_data)} 条数据记录")
            
            # 检查日期连续性
            self.check_date_continuity(date_records)
        else:
            print("没有成功加载任何数据")
        
        return self.all_data
    
    def check_date_continuity(self, date_records):
        """
        检查日期的连续性
        
        参数:
            date_records: 包含(月,日)元组的集合
        """
        # 将(月,日)转换为日期对象
        current_year = datetime.now().year
        dates = [datetime(current_year, month, day) for month, day in date_records]
        dates.sort()
        
        # 检查日期连续性
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            delta = (next_date - current_date).days
            
            if delta > 1:
                # 找出缺失的日期
                missing_date = current_date + timedelta(days=1)
                while missing_date < next_date:
                    self.missing_dates.append(missing_date.strftime("%Y-%m-%d"))
                    missing_date += timedelta(days=1)
        
        if self.missing_dates:
            print(f"发现缺失的日期: {', '.join(self.missing_dates)}")
    
    def load_inventory_data(self, inventory_path=None):
        """加载库存数据（不包含鲜品和副产品，但特殊保留"凤肠"产品）"""
        print("开始加载库存数据...")
        
        if inventory_path is None:
            inventory_path = config.INVENTORY_PATH
        
        try:
            # 读取库存表
            inventory_df = pd.read_excel(inventory_path)
            
            # 打印列名，帮助调试
            print("库存表的列名:")
            for col in inventory_df.columns:
                print(f"  - '{col}' (类型: {type(col).__name__})")
            
            # 基本数据清洗
            if not inventory_df.empty:
                # 删除全空行和品名为空的行
                inventory_df = inventory_df.dropna(how='all')
                inventory_df = inventory_df[inventory_df['物料名称'].notna() & (inventory_df['物料名称'] != '')]
                
                # 在过滤前保存所有"凤肠"产品记录，以便后续添加回来
                feng_chang_products = inventory_df[inventory_df['物料名称'].astype(str).str.contains('凤肠', case=False, na=False)].copy()
                if not feng_chang_products.empty:
                    print(f"找到 {len(feng_chang_products)} 条凤肠产品记录，将在过滤后特殊保留")
                
                # 过滤掉客户为"副产品"、"鲜品"或空白的记录
                if '客户' in inventory_df.columns:
                    original_count_customer_filter = len(inventory_df)
                    # 确保客户列是字符串类型并去除首尾空格
                    inventory_df['客户'] = inventory_df['客户'].astype(str).str.strip()
                    excluded_customers_values = ['副产品', '鲜品', ''] # 添加空字符串到排除列表
                    mask = ~inventory_df['客户'].isin(excluded_customers_values)
                    inventory_df = inventory_df[mask]
                    print(f"排除客户为'副产品'、'鲜品'或空白的数据后，从 {original_count_customer_filter} 条记录中剩余 {len(inventory_df)} 条记录")
                
                # 新增：根据"物料分类名称"列进行筛选
                material_category_col = '物料分类名称' # 假设Excel中的
                if material_category_col in inventory_df.columns:
                    excluded_categories = ['副产品', '生鲜品其他'] # 更新排除列表
                    # 首先处理空字符串，将其替换为 NaN，以便后续 .isin() 可以正确处理
                    inventory_df[material_category_col] = inventory_df[material_category_col].replace(r'^\s*$', np.nan, regex=True)
                    
                    # 构建排除 NaN 和特定分类的掩码
                    mask = ~(
                        inventory_df[material_category_col].isin(excluded_categories) | \
                        inventory_df[material_category_col].isna()
                    )
                    original_count = len(inventory_df)
                    inventory_df = inventory_df[mask]
                    print(f"根据'物料分类名称'排除特定分类（空白、副产品、生鲜品其他）后，从 {original_count} 条记录中剩余 {len(inventory_df)} 条记录") # 更新打印信息
                else:
                    print(f"警告: 库存数据中未找到列 '{material_category_col}'，无法应用物料分类名称筛选。")
                
                # 新增：排除物料名称含"鲜"字的记录
                original_count = len(inventory_df)
                inventory_df = inventory_df[~inventory_df['物料名称'].astype(str).str.contains('鲜', case=False, na=False)]
                print(f"排除物料名称含'鲜'字的记录后，从 {original_count} 条记录中剩余 {len(inventory_df)} 条记录")
                
                # 特殊处理：将"凤肠"产品添加回来
                if not feng_chang_products.empty:
                    # 确保不重复添加已经存在的记录
                    feng_chang_to_add = feng_chang_products[~feng_chang_products['物料名称'].isin(inventory_df['物料名称'])]
                    if not feng_chang_to_add.empty:
                        inventory_df = pd.concat([inventory_df, feng_chang_to_add], ignore_index=True)
                        print(f"特殊处理：添加了 {len(feng_chang_to_add)} 条凤肠产品记录回到库存数据中")
                
                # 定义列名映射
                column_mapping = {
                    '物料名称': '品名',
                    '入库': '产量',
                    '出库': '销量',
                    '结存': '库存量'
                }
                
                # 重命名列
                inventory_df = inventory_df.rename(columns=column_mapping)
                
                # 数据类型转换
                numeric_columns = ['产量', '销量', '库存量']
                for col in numeric_columns:
                    if col in inventory_df.columns:
                        inventory_df[col] = pd.to_numeric(inventory_df[col], errors='coerce')
                
                # 排序
                inventory_df = inventory_df.sort_values(by=['品名'], ascending=True)
                
                self.inventory_data = inventory_df
                print(f"成功加载 {len(inventory_df)} 条库存记录")
                return inventory_df
            else:
                print("库存表为空")
                return None
        
        except Exception as e:
            print(f"加载库存数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_sales_data(self, sales_path=None):
        """加载销售数据（用于绘制销售趋势图，排除客户名称为空、副产品、鲜品的记录）"""
        print("开始加载销售数据 (统一清洗规则)...")
        
        if sales_path is None:
            sales_path = config.SALES_PATH
        
        try:
            # 读取销售数据
            sales_df = pd.read_excel(sales_path)
            
            # 打印列名，帮助调试
            print("原始销售数据的列名:")
            for col in sales_df.columns:
                print(f"  - '{col}' (类型: {type(col).__name__})")
            
            if sales_df.empty:
                print("销售数据文件为空")
                return None

            # 删除全空行
            sales_df = sales_df.dropna(how='all')
            print(f"删除全空行后，剩余 {len(sales_df)} 条记录")

            # 检查基本日期列是否存在
            date_column_name = '发票日期'
            if date_column_name not in sales_df.columns:
                print(f"错误: 销售数据缺少必要的日期列 '{date_column_name}'")
                return None
            sales_df[date_column_name] = pd.to_datetime(sales_df[date_column_name], errors='coerce')
            sales_df = sales_df.dropna(subset=[date_column_name])
            print(f"转换 '{date_column_name}' 并移除无效日期后，剩余 {len(sales_df)} 条记录")

            # 清洗条件 1: 物料分类列，去除"副产品"、"空白"的行
            material_category_column = '物料分类' 
            if material_category_column in sales_df.columns:
                print(f"应用物料分类筛选前: {len(sales_df)} 条记录")
                sales_df[material_category_column] = sales_df[material_category_column].replace(r'^\\s*$', np.nan, regex=True)
                sales_df = sales_df[
                    (~sales_df[material_category_column].astype(str).str.lower().isin(['副产品', 'nan', '']))
                ]
                print(f'筛选掉"物料分类"为"副产品"或空白后，剩余 {len(sales_df)} 条记录')
            else:
                print(f"警告: 未找到列 '{material_category_column}'，无法应用物料分类筛选。")

            # 清洗条件 2: 客户名称列，排除客户名称为空、"副产品"或"鲜品"的记录
            customer_name_column = '客户名称' 
            if customer_name_column in sales_df.columns:
                print(f"清洗前'客户名称'筛选，记录数: {len(sales_df)}")
                # 确保为字符串类型并去除首尾空格，处理潜在的 NaN 值
                sales_df[customer_name_column] = sales_df[customer_name_column].fillna('').astype(str).str.strip()
                
                # 定义要排除的客户名称列表 (统一小写以进行不区分大小写的比较)
                excluded_customer_names_lower = ['', '副产品'.lower(), '鲜品'.lower()] 
                
                # 应用排除筛选 (将列内容转为小写进行比较)
                sales_df = sales_df[~sales_df[customer_name_column].str.lower().isin(excluded_customer_names_lower)]
                print(f'按新规则筛选"客户名称"（排除空白、副产品、鲜品）后，剩余 {len(sales_df)} 条记录')
            else:
                print(f"警告: 未找到列 '{customer_name_column}'，无法应用客户名称筛选。")

            # 清洗条件 3: 物料名称"列，删除其中包含"鲜"的记录
            material_name_column = '物料名称' 
            if material_name_column in sales_df.columns:
                print(f"应用物料名称筛选前: {len(sales_df)} 条记录")
                sales_df = sales_df[
                    ~sales_df[material_name_column].astype(str).str.contains('鲜', case=False, na=False)
                ]
                print(f'删除"物料名称"包含"鲜"的记录后，剩余 {len(sales_df)} 条记录')    
            else:
                print(f"警告: 未找到列 '{material_name_column}'，无法应用物料名称筛选。")

            # 清洗条件 4: 数量列的确定:固定使用"主数量"列作为销量来源。
            quantity_column_to_use = '主数量'
            if quantity_column_to_use not in sales_df.columns:
                print(f"错误: 销售数据缺少必要的数量列 '{quantity_column_to_use}'")
                # Potentially return None or an empty DataFrame if this column is critical
                # For now, we will proceed, but downstream process_sales_data will need to handle its absence
                # if it's not present, or we ensure it must exist.
                # To strictly enforce, uncomment: return None 
            else:
                sales_df[quantity_column_to_use] = pd.to_numeric(sales_df[quantity_column_to_use], errors='coerce')
                # Optional: Filter out rows where '主数量' is NaN or non-positive, if business logic requires
                sales_df = sales_df.dropna(subset=[quantity_column_to_use])
                # sales_df = sales_df[sales_df[quantity_column_to_use] > 0] # Uncomment if sales must be positive
                print(f"转换 '{quantity_column_to_use}' 为数值并移除无效条目后，剩余 {len(sales_df)} 条记录")

            # 其他必要的列，如金额，也应进行检查和类型转换
            amount_column = '本币无税金额'
            if amount_column in sales_df.columns:
                sales_df[amount_column] = pd.to_numeric(sales_df[amount_column], errors='coerce')
            else:
                print(f"警告: 未找到金额列 '{amount_column}'。相关计算可能受影响。")
                
            # 存储结果
            self.sales_data = sales_df
            
            print(f"成功加载并按统一规则清洗后，剩余 {len(sales_df)} 条销售数据")
            return self.sales_data
        
        except Exception as e:
            print(f"加载销售数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_daily_production_data(self, production_path=None):
        """加载每日产量数据，用于计算产销率"""
        print("开始加载产量数据...")
        
        if production_path is None:
            production_path = config.PRODUCTION_PATH  # 现在指向"产成品入库列表.xlsx"
        
        try:
            # 读取产量数据
            production_df = pd.read_excel(production_path, engine='openpyxl')
            
            # 打印列名，帮助调试
            print("产量数据的列名:")
            for col in production_df.columns:
                print(f"  - '{col}' (类型: {type(col).__name__})")
            
            # 基本数据清洗
            if not production_df.empty:
                # 删除全空行
                production_df = production_df.dropna(how='all')
                
                # 列名映射 - 适配新的Excel格式
                date_column = '入库日期'
                material_column = '物料名称'
                quantity_column = '主数量'
                
                # 检查必要的列是否存在
                required_columns = [date_column, material_column, quantity_column]
                missing_columns = [col for col in required_columns if col not in production_df.columns]
                
                if missing_columns:
                    print(f"产量数据缺少必要的列: {', '.join(missing_columns)}")
                    return {'by_material': {}, 'total': {}}
                
                # 数据清洗：去除物料名称中含"鲜"字的行
                if material_column in production_df.columns:
                    production_df = production_df[~production_df[material_column].astype(str).str.contains('鲜')]
                    print(f"排除物料名称含'鲜'字的记录后，剩余 {len(production_df)} 条记录")
                
                # 数据清洗：去掉物料大类中"副产品"和空白
                material_category_column = None
                for col in ['物料大类', '物料所属分类']:
                    if col in production_df.columns:
                        material_category_column = col
                        break
                        
                if material_category_column:
                    # 去除物料大类为空白的记录
                    production_df = production_df[production_df[material_category_column].notna() & 
                                                 (production_df[material_category_column] != '')]
                    print(f"排除物料大类为空白的记录后，剩余 {len(production_df)} 条记录")
                    
                    # 去除物料大类为"副产品"的记录
                    production_df = production_df[production_df[material_category_column] != '副产品']
                    print(f"排除物料大类为'副产品'的记录后，剩余 {len(production_df)} 条记录")
                
                # 转换日期列为日期类型
                production_df[date_column] = pd.to_datetime(production_df[date_column], errors='coerce')
                
                # 删除日期为空的行
                production_df = production_df.dropna(subset=[date_column])
                
                # 转换主数量列为数值类型
                production_df[quantity_column] = pd.to_numeric(production_df[quantity_column], errors='coerce')
                
                # 删除主数量为NaN的行
                production_df = production_df.dropna(subset=[quantity_column])
                
                # 按日期和物料名称分组，汇总产量
                daily_production = production_df.groupby([production_df[date_column].dt.date, material_column])[
                    quantity_column].sum().reset_index()
                
                # 创建按日期和物料分组的字典
                daily_production_dict = {}
                daily_total_production = {}
                
                for _, row in daily_production.iterrows():
                    date = row[date_column]
                    material = row[material_column]
                    quantity = row[quantity_column]
                    
                    if date not in daily_production_dict:
                        daily_production_dict[date] = {}
                        daily_total_production[date] = 0
                    
                    daily_production_dict[date][material] = quantity
                    daily_total_production[date] += quantity
                
                print(f"成功加载 {len(production_df)} 条产量数据，覆盖 {len(daily_production_dict)} 个日期")
                
                # 返回两个字典：按物料分组的和每日总产量
                return {
                    'by_material': daily_production_dict,
                    'total': daily_total_production
                }
            else:
                print("产量数据为空")
                return {'by_material': {}, 'total': {}}
        
        except Exception as e:
            print(f"加载产量数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'by_material': {}, 'total': {}}
    
    def load_industry_trend_data(self, industry_trend_path=None):
        """加载行业趋势数据"""
        print("开始加载行业趋势数据...")
        
        if industry_trend_path is None:
            industry_trend_path = config.INDUSTRY_TREND_PATH
        
        try:
            # 读取行业趋势数据
            industry_trend_df = pd.read_excel(industry_trend_path)
            
            # 打印列名，帮助调试
            print("行业趋势数据的列名:")
            for col in industry_trend_df.columns:
                print(f"  - '{col}' (类型: {type(col).__name__})")
            
            # 基本数据清洗
            if not industry_trend_df.empty:
                # 删除全空行
                industry_trend_df = industry_trend_df.dropna(how='all')
                
                # 转换日期列
                date_cols = [col for col in industry_trend_df.columns if '日期' in col]
                for col in date_cols:
                    industry_trend_df[col] = pd.to_datetime(industry_trend_df[col], errors='coerce')
                
                # 存储结果
                self.industry_trend_data = industry_trend_df
                
                print(f"成功加载 {len(industry_trend_df)} 条行业趋势数据")
                return industry_trend_df
            else:
                print("行业趋势数据为空")
                return None
        
        except Exception as e:
            print(f"加载行业趋势数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_price_comparison_data(self, comparison_path=None):
        """加载春雪与小明农牧价格对比数据"""
        print("开始加载价格对比数据...")
        
        if comparison_path is None:
            comparison_path = r'\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\春雪与小明农牧价格对比.xlsx'
        
        try:
            # 读取价格对比表
            comparison_df = pd.read_excel(comparison_path)
            
            # 打印列名，帮助调试
            print("价格对比表的列名:")
            for col in comparison_df.columns:
                print(f"  - '{col}' (类型: {type(col).__name__})")
            
            # 基本数据清洗
            if not comparison_df.empty:
                # 删除全空行
                comparison_df = comparison_df.dropna(how='all')
                
                # 检查必要的列是否存在
                required_columns = ['品名', '规格', '春雪价格', '小明中间价', '中间价差']
                missing_columns = [col for col in required_columns if col not in comparison_df.columns]
                
                if missing_columns:
                    print(f"价格对比表缺少必要的列: {', '.join(missing_columns)}")
                    return None
                
                # 确保数值列为数值类型
                for col in ['春雪价格', '小明中间价', '中间价差']:
                    comparison_df[col] = pd.to_numeric(comparison_df[col], errors='coerce')
                
                print(f"成功加载 {len(comparison_df)} 条价格对比数据")
                return comparison_df
            else:
                print("价格对比表为空")
                return None
        
        except Exception as e:
            print(f"加载价格对比数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_daily_sales_data(self, path):
        """加载销售数据（用于计算产销率，排除客户名称为空、副产品、鲜品的记录）"""
        # 如果 path 为 None，则从 config 文件加载路径
        if path is None:
            path = config.SALES_PATH
            print(f"Path was None, using config.SALES_PATH: {path}")
        
        # 检查路径是否存在
        if not path or not os.path.exists(path):
            print(f"Error: Sales data file not found at path: {path}")
            return {'by_material': {}, 'total': {}} # 返回空结构

        print(f"Loading daily sales data from: {path}")
        try:
            sales_df = pd.read_excel(path, engine='openpyxl')
        except FileNotFoundError:
            print(f"Error: File not found at specified path: {path}")
            return {'by_material': {}, 'total': {}} # 返回空结构
        except Exception as e:
            print(f"Error reading Excel file at {path}: {e}")
            import traceback
            traceback.print_exc()
            return {'by_material': {}, 'total': {}} # 返回空结构

        # 数据清洗：转换日期列
        date_column_name = '发票日期' # 修正列名
        if date_column_name in sales_df.columns:
            sales_df[date_column_name] = pd.to_datetime(sales_df[date_column_name], errors='coerce')
            sales_df = sales_df.dropna(subset=[date_column_name])  # 删除日期为NaN的行
            print(f"使用列 '{date_column_name}' 进行日期转换和处理。")
        else:
            print(f"错误：在销售数据中未找到预期的日期列 '{date_column_name}'。可用列：{sales_df.columns.tolist()}")
            return {'by_material': {}, 'total': {}} # 暂时返回空
        
        # 清洗条件 1: 物料分类列，去除"副产品"、"空白"的行
        material_category_column = '物料分类' # 假设列名为'物料分类'
        if material_category_column in sales_df.columns:
            print(f"原始记录数 (清洗前物料分类筛选): {len(sales_df)}")
            # 替换空白字符串为空值 (NaN) 以便统一处理
            sales_df[material_category_column] = sales_df[material_category_column].replace(r'^\\s*$', np.nan, regex=True)
            sales_df = sales_df[
                (~sales_df[material_category_column].astype(str).str.lower().isin(['副产品', 'nan', '']))
            ]
            print(f'筛选掉"物料分类"为"副产品"或空白后，剩余 {len(sales_df)} 条记录')
        else:
            print(f"警告: 未找到列 '{material_category_column}'，无法应用物料分类筛选。")

        # 清洗条件 2: 客户名称列，排除客户名称为空、"副产品"或"鲜品"的记录
        customer_name_column = '客户名称' # 假设列名为'客户名称'
        if customer_name_column in sales_df.columns:
            print(f"清洗前'客户名称'筛选，记录数: {len(sales_df)}")
            # 1. 确保为字符串类型并去除首尾空格，处理潜在的 NaN 值
            sales_df[customer_name_column] = sales_df[customer_name_column].fillna('').astype(str).str.strip()
            
            # 2. 定义要排除的客户名称列表 (统一小写以进行不区分大小写的比较)
            excluded_customer_names_lower = ['', '副产品'.lower(), '鲜品'.lower()] 
            
            # 3. 应用排除筛选 (将列内容转为小写进行比较)
            sales_df = sales_df[~sales_df[customer_name_column].str.lower().isin(excluded_customer_names_lower)]
            print(f'按新规则筛选"客户名称"（排除空白、副产品、鲜品）后，剩余 {len(sales_df)} 条记录')
        else:
            print(f"警告: 列 '{customer_name_column}' 未找到，无法应用客户名称筛选。")

        # 清洗条件 3: 物料名称"列，删除其中包含"鲜"的记录
        material_name_column = '物料名称' # 假设列名为'物料名称'
        if material_name_column in sales_df.columns:
            print(f"原始记录数 (清洗前物料名称筛选): {len(sales_df)}")
            sales_df = sales_df[
                ~sales_df[material_name_column].astype(str).str.contains('鲜', case=False, na=False)
            ]
            print(f'删除"物料名称"包含"鲜"的记录后，剩余 {len(sales_df)} 条记录')   
        else:
            print(f"警告: 未找到列 '{material_name_column}'，无法应用物料名称筛选。")
        
        # 清洗条件 4: 数量列的确定:固定使用"主数量"列作为销量来源。
        quantity_column_name = '主数量'
        if quantity_column_name not in sales_df.columns:
            print(f"错误：在销售数据中未找到预期的数量列 '{quantity_column_name}' 用于销量。可用列：{sales_df.columns.tolist()}")
            return {'by_material': {}, 'total': {}}

        sales_df[quantity_column_name] = pd.to_numeric(sales_df[quantity_column_name], errors='coerce')
        # 考虑是否需要删除销量为0或负数的记录，根据业务逻辑决定
        sales_df = sales_df.dropna(subset=[quantity_column_name])  # 删除主数量为NaN的行
        # sales_df = sales_df[sales_df[quantity_column_name] > 0] # 例如：如果销量必须为正
        print(f'使用"{quantity_column_name}"作为销量，并进行数值转换和NaN排除后，剩余 {len(sales_df)} 条记录')
        
        # 日期分组，计算每日销售数据
        daily_sales = {}
        daily_total_sales = {}
        
        # 按日期和品名分组 - 使用修正后的日期列名和物料名称列名
        material_column_name = '物料名称'
        if material_column_name not in sales_df.columns:
            print(f"错误：在销售数据中未找到预期的物料列 '{material_name_column}'。可用列：{sales_df.columns.tolist()}")
            return {'by_material': {}, 'total': {}} # 返回空
        
        grouped = sales_df.groupby([date_column_name, material_column_name])
        
        for (date, name), group in grouped:
            # 确保日期是 Timestamp 对象，如果需要转换回字符串或其他格式可以在这里处理
            # date 变量现在是 '发票日期' 列的值
            # 如果后续字典的 key 需要是特定的日期格式，例如 YYYY-MM-DD 字符串或 date 对象
            # 可以进行转换，例如： date_key = date.date() if isinstance(date, pd.Timestamp) else date
            if isinstance(date, pd.Timestamp):
                date_key = date.date() 
            else:
                 # 如果分组键不是 Timestamp (理论上不应发生，但作为保险), 尝试转换
                try:
                    date_key = pd.to_datetime(date).date()
                except: 
                    print(f"警告：无法将分组键 {date} 转换为 date 对象，跳过此条目。")
                    continue # 跳过这个无法处理的条目

            if date_key not in daily_sales:
                daily_sales[date_key] = {}
            
            # 累加同一天同一品名的主数量
            total_quantity = group[quantity_column_name].sum()
            daily_sales[date_key][name] = total_quantity
            
            # 计算每日总销量
            if date_key not in daily_total_sales:
                daily_total_sales[date_key] = 0
            daily_total_sales[date_key] += total_quantity
        
        return {'by_material': daily_sales, 'total': daily_total_sales}
    
    def load_comprehensive_price_data(self, file_path=None):
        """
        加载综合售价数据 - 从目录中查找最新的综合售价X.XX.xlsx文件
        
        参数:
            file_path: 可选，直接指定文件路径；如为None则自动查找最新文件
            
        返回:
            str: 找到的综合售价文件路径，如果未找到则返回None
        """
        import os
        import re
        import glob
        from datetime import datetime
        import config
        
        try:
            # 如果提供了具体文件路径，则直接使用
            if file_path is not None:
                print(f"使用指定的综合售价文件: {file_path}")
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    print(f"错误: 指定的文件不存在: {file_path}")
                    return None
                latest_file = file_path
            else:
                # 如果没有提供文件路径，则在目录中查找最新的综合售价X.XX.xlsx文件
                directory = config.COMPREHENSIVE_PRICE_DIR
                pattern = config.COMPREHENSIVE_PRICE_PATTERN
                
                print(f"在目录 {directory} 中查找匹配模式 {pattern} 的最新综合售价文件")
                
                # 获取所有匹配的文件
                all_files = []
                search_pattern = os.path.join(directory, "综合售价*.xlsx")
                for file_path in glob.glob(search_pattern):
                    file_name = os.path.basename(file_path)
                    match = re.search(pattern, file_name)
                    if match:
                        date_str = match.group(1)
                        try:
                            # 解析日期字符串
                            month, day = date_str.split('.')
                            # 使用当前年份
                            year = datetime.now().year
                            file_date = datetime(year, int(month), int(day))
                            all_files.append((file_path, file_date))
                        except ValueError:
                            print(f"无法解析文件名中的日期: {file_name}")
                
                if not all_files:
                    print(f"错误: 在目录 {directory} 中没有找到匹配的综合售价文件")
                    return None
                
                # 按日期排序，获取最新的文件
                all_files.sort(key=lambda x: x[1], reverse=True)
                latest_file = all_files[0][0]
                print(f"找到最新的综合售价文件: {latest_file}")
            
            # 直接返回文件路径，不再处理Excel数据
            return latest_file
            
        except Exception as e:
            print(f"加载综合售价数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_industry_price_data(self, chicken_path=None, raw_chicken_path=None, breast_path=None, leg_path=None):
        """
        加载卓创资讯历史价格数据
        
        参数:
            chicken_path: 鸡苗历史价格Excel文件路径，若为None则使用配置文件中的路径
            raw_chicken_path: 毛鸡历史价格Excel文件路径，若为None则使用配置文件中的路径
            breast_path: 板冻大胸历史价格Excel文件路径，若为None则使用配置文件中的路径
            leg_path: 琵琶腿历史价格Excel文件路径，若为None则使用配置文件中的路径
            
        返回:
            dict: 包含各产品价格数据的字典，格式为 {产品名: DataFrame}
        """
        import config
        
        # 使用配置文件中的路径（如果未提供）
        chicken_path = chicken_path or config.CHICKEN_PRICE_PATH
        raw_chicken_path = raw_chicken_path or config.RAW_CHICKEN_PRICE_PATH
        breast_path = breast_path or config.BREAST_PRICE_PATH
        leg_path = leg_path or config.LEG_PRICE_PATH
        
        print(f"鸡苗路径: {chicken_path}")
        print(f"毛鸡路径: {raw_chicken_path}")
        print(f"板冻大胸路径: {breast_path}")
        print(f"琵琶腿路径: {leg_path}")
        
        industry_data = {}
        
        # 用于处理Excel文件的通用方法
        def process_price_file(file_path, product_name, fallback_filename):
            try:
                if os.path.exists(file_path):
                    print(f"正在加载{product_name}历史价格数据: {file_path}")
                    try:
                        # 尝试读取Excel文件
                        df = pd.read_excel(file_path, engine='openpyxl')
                        # 检查列数，如果只有少数几列，可能是常规格式
                        if len(df.columns) < 9:
                            # 标准格式: 直接读取日期和价格列
                            if 'date' not in df.columns and df.columns[0] != 'date':
                                df.rename(columns={df.columns[0]: 'date'}, inplace=True)
                            if 'price' not in df.columns and '价格' in df.columns:
                                df.rename(columns={'价格': 'price'}, inplace=True)
                        else:
                            # 特殊格式: 第一列是日期，第九列是价格
                            print(f"{product_name}文件使用特殊格式: 第一列为日期，第九列为价格")
                            if len(df.columns) >= 9:
                                # 创建新的DataFrame，只保留需要的两列
                                df = pd.DataFrame({
                                    'date': df.iloc[:, 0],  # 第一列作为date
                                    'price': df.iloc[:, 8]  # 第九列作为price
                                })
                            else:
                                print(f"警告: {product_name}文件列数不足，无法提取价格数据")
                                return None
                    except Exception as e1:
                        print(f"使用openpyxl引擎加载失败，尝试使用xlrd引擎: {str(e1)}")
                        try:
                            df = pd.read_excel(file_path, engine='xlrd')
                            # 同样处理列
                            if len(df.columns) < 9:
                                if 'date' not in df.columns and df.columns[0] != 'date':
                                    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
                                if 'price' not in df.columns and '价格' in df.columns:
                                    df.rename(columns={'价格': 'price'}, inplace=True)
                            else:
                                if len(df.columns) >= 9:
                                    df = pd.DataFrame({
                                        'date': df.iloc[:, 0],
                                        'price': df.iloc[:, 8]
                                    })
                                else:
                                    print(f"警告: {product_name}文件列数不足，无法提取价格数据")
                                    return None
                        except Exception as e2:
                            print(f"使用xlrd引擎加载失败: {str(e2)}")
                            # 最后尝试使用Python直接读取文件
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            relative_path = os.path.join(current_dir, fallback_filename)
                            print(f"尝试从默认路径加载: {relative_path}")
                            try:
                                df = pd.read_excel(relative_path, engine='openpyxl')
                                # 同样处理列
                                if len(df.columns) < 9:
                                    if 'date' not in df.columns and df.columns[0] != 'date':
                                        df.rename(columns={df.columns[0]: 'date'}, inplace=True)
                                    if 'price' not in df.columns and '价格' in df.columns:
                                        df.rename(columns={'价格': 'price'}, inplace=True)
                                else:
                                    if len(df.columns) >= 9:
                                        df = pd.DataFrame({
                                            'date': df.iloc[:, 0],
                                            'price': df.iloc[:, 8]
                                        })
                                    else:
                                        print(f"警告: {product_name}文件列数不足，无法提取价格数据")
                                        return None
                            except Exception as e3:
                                print(f"尝试从默认路径加载失败: {str(e3)}")
                                return None
                    
                    # 检查是否有必要的列
                    if 'date' in df.columns and 'price' in df.columns:
                        # 确保date列是datetime格式
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                        # 确保price列是数值类型
                        df['price'] = pd.to_numeric(df['price'], errors='coerce')
                        # 清理数据
                        df = df.dropna(subset=['date', 'price'])
                        return df
                    else:
                        print(f"警告: {product_name}价格数据缺少必要的列。文件中的列: {list(df.columns)}")
                        return None
                else:
                    print(f"警告: {product_name}价格文件不存在: {file_path}")
                    return None
            except Exception as e:
                print(f"加载{product_name}价格数据时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
        
        # 加载鸡苗价格数据
        chicken_df = process_price_file(chicken_path, "鸡苗", "鸡苗历史价格.xlsx")
        if chicken_df is not None:
            industry_data['鸡苗'] = chicken_df
            print(f"成功加载鸡苗价格数据，共 {len(chicken_df)} 条记录")
        
        # 加载毛鸡价格数据
        raw_chicken_df = process_price_file(raw_chicken_path, "毛鸡", "毛鸡历史价格.xlsx")
        if raw_chicken_df is not None:
            industry_data['毛鸡'] = raw_chicken_df
            print(f"成功加载毛鸡价格数据，共 {len(raw_chicken_df)} 条记录")
        
        # 加载板冻大胸价格数据
        breast_df = process_price_file(breast_path, "板冻大胸", "板冻大胸历史价格.xlsx")
        if breast_df is not None:
            industry_data['板冻大胸'] = breast_df
            print(f"成功加载板冻大胸价格数据，共 {len(breast_df)} 条记录")
        
        # 加载琵琶腿价格数据
        leg_df = process_price_file(leg_path, "琵琶腿", "琵琶腿历史价格.xlsx")
        if leg_df is not None:
            industry_data['琵琶腿'] = leg_df
            print(f"成功加载琵琶腿价格数据，共 {len(leg_df)} 条记录")
        
        # 添加变动列（如果不存在）
        for product, df in industry_data.items():
            if 'change' not in df.columns:
                # 按日期排序
                df = df.sort_values(by='date')
                # 计算变动
                df['change'] = df['price'].diff()
                industry_data[product] = df
        
        print(f"最终返回的industry_data包含键: {list(industry_data.keys())}")
        return industry_data 