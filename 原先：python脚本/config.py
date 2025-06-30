# -*- coding: utf-8 -*-
"""
配置文件，存储路径和基本设置
"""

import os

# 文件路径配置
DATA_PATH = r'\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\调价表.xlsx'
INVENTORY_PATH = r'\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\收发存汇总表查询.xlsx'
SALES_PATH = r'\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\销售发票执行查询.xlsx'
PRODUCTION_PATH = r'\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\产成品入库列表.xlsx'
INDUSTRY_TREND_PATH = r'\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\小明农牧.xlsx'
OUTPUT_DIR = r'输出'  # 使用相对路径，指向当前目录下的输出文件夹

# 添加综合售价数据目录和文件模式
COMPREHENSIVE_PRICE_DIR = r"\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表"
COMPREHENSIVE_PRICE_PATTERN = r"综合售价(\d+\.\d+)\.xlsx"  # 用于匹配文件名并提取日期
# 保留旧配置用于兼容性，但不再使用
COMPREHENSIVE_PRICE_PATH = r"\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\综合售价.xlsx"

# 添加卓创资讯价格文件路径
CHICKEN_PRICE_PATH = r"\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\鸡苗历史价格.xlsx"
RAW_CHICKEN_PRICE_PATH = r"\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\毛鸡历史价格.xlsx"
BREAST_PRICE_PATH = r"\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\板冻大胸历史价格.xlsx"
LEG_PRICE_PATH = r"\\xskynas\userdata\quzhupeng\Desktop\my_python_project\价格表\琵琶腿历史价格.xlsx"

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)



