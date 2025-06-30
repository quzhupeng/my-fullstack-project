#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格调整数据导入脚本
基于原先Python脚本的逻辑，处理调价表Excel文件并导入到数据库
"""

import os
import re
import sqlite3
import pandas as pd
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_date_info(sheet_name):
    """
    从sheet名称中提取日期和调价次数信息
    参数:
        sheet_name: sheet名称，如'价格表4月2号（2）'或'价格表4月2号'
    返回:
        (month, day, change_count): 月份、日期和调价次数的元组，或者None
    """
    # 新的正则表达式模式，匹配"价格表X月Y号"和"价格表X月Y号（Z）"格式
    pattern = r'价格表(\d+)月(\d+)号(?:（(\d+)）)?'
    match = re.match(pattern, sheet_name)
    
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        change_count = int(match.group(3)) if match.group(3) else 1
        return (month, day, change_count)
    
    # 保留原来的模式匹配作为备选
    old_pattern = r'(\d+)\.(\d+)(?:\((\d+)\))?'
    match = re.match(old_pattern, sheet_name)
    
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        change_count = int(match.group(3)) if match.group(3) else 1
        return (month, day, change_count)

    logger.warning(f"无法从sheet名称 '{sheet_name}' 中提取日期信息")
    return None

def preprocess_sheet(df, sheet_name):
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
        logger.warning(f"无法从sheet名称 '{sheet_name}' 中提取日期信息，跳过处理")
        return None
    
    month, day, change_count = date_info
    date_str = f"2025-{month:02d}-{day:02d}"  # 假设年份为2025
    
    # 检查数据是否为空
    if df.empty:
        logger.warning(f"Sheet '{sheet_name}' 中没有数据，跳过处理")
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
            template_df = template_df[~template_df['品名'].astype(str).str.contains('均价|品名', na=False)]
            
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

def create_database_tables(db_path):
    """创建数据库表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建Products表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL UNIQUE,
            sku TEXT UNIQUE,
            category TEXT
        )
    ''')
    
    # 创建PriceAdjustments表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PriceAdjustments (
            adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            adjustment_date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            specification TEXT,
            adjustment_count INTEGER DEFAULT 1,
            previous_price REAL,
            current_price REAL NOT NULL,
            price_difference REAL NOT NULL,
            category TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES Products(product_id)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_priceadjustments_date ON PriceAdjustments(adjustment_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_priceadjustments_product_id ON PriceAdjustments(product_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_priceadjustments_price_diff ON PriceAdjustments(price_difference)')
    
    conn.commit()
    conn.close()

def import_price_data(excel_file_path, db_path):
    """导入价格调整数据"""
    logger.info(f"开始处理文件: {excel_file_path}")
    
    # 创建数据库表
    create_database_tables(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 读取Excel文件中的所有sheet
        excel = pd.ExcelFile(excel_file_path)
        
        # 按照日期顺序排序sheet
        def sheet_sort_key(sheet_name):
            date_info = extract_date_info(sheet_name)
            if date_info:
                month, day, count = date_info
                return (month, day, count)
            return (0, 0, 0)
        
        sorted_sheets = sorted(excel.sheet_names, key=sheet_sort_key)
        
        total_records = 0
        
        for sheet_name in sorted_sheets:
            logger.info(f"处理sheet: {sheet_name}")
            
            # 读取sheet数据
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            
            # 预处理sheet数据
            processed_df = preprocess_sheet(df, sheet_name)
            
            if processed_df is not None and not processed_df.empty:
                # 处理每一行数据
                for _, row in processed_df.iterrows():
                    product_name = row['品名']
                    category = row['分类']
                    specification = row['规格']
                    adjustment_date = row['日期']
                    adjustment_count = row['调价次数']
                    previous_price = row['前价格'] if pd.notna(row['前价格']) else None
                    current_price = row['价格']
                    
                    # 跳过无效数据
                    if pd.isna(current_price) or not product_name:
                        continue
                    
                    # 计算价格差异
                    price_difference = current_price - previous_price if previous_price else 0
                    
                    # 查找或创建产品
                    cursor.execute('SELECT product_id FROM Products WHERE product_name = ?', (product_name,))
                    product_result = cursor.fetchone()
                    
                    if product_result:
                        product_id = product_result[0]
                    else:
                        cursor.execute('INSERT INTO Products (product_name, category) VALUES (?, ?)', 
                                     (product_name, category))
                        product_id = cursor.lastrowid
                    
                    # 插入价格调整记录
                    cursor.execute('''
                        INSERT INTO PriceAdjustments 
                        (adjustment_date, product_id, product_name, specification, adjustment_count,
                         previous_price, current_price, price_difference, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (adjustment_date, product_id, product_name, specification, adjustment_count,
                          previous_price, current_price, price_difference, category))
                    
                    total_records += 1
        
        conn.commit()
        logger.info(f"成功导入 {total_records} 条价格调整记录")
        
    except Exception as e:
        logger.error(f"导入数据时出错: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """主函数"""
    # 配置文件路径
    excel_file_path = "Excel文件夹/调价表.xlsx"
    db_path = "backend/.wrangler/state/v3/d1/chunxue-prod-db.sqlite"
    
    # 检查文件是否存在
    if not os.path.exists(excel_file_path):
        logger.error(f"Excel文件不存在: {excel_file_path}")
        return
    
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        import_price_data(excel_file_path, db_path)
        logger.info("价格调整数据导入完成！")
    except Exception as e:
        logger.error(f"导入失败: {str(e)}")

if __name__ == "__main__":
    main()
