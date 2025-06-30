# -*- coding: utf-8 -*-
"""
工具函数模块，提供各种辅助函数
"""

import re
import os
import zipfile
from datetime import datetime


def extract_date_info(sheet_name):
    """
    从sheet名称中提取日期和调价次数信息
    
    参数:
        sheet_name: sheet名称，如'3.7(3)'
        
    返回:
        (month, day, change_count): 月份、日期和调价次数的元组
    """
    pattern = r'(\d+)\.(\d+)(?:\((\d+)\))?'
    match = re.match(pattern, sheet_name)
    
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        change_count = int(match.group(3)) if match.group(3) else 1
        return (month, day, change_count)
    return None


def create_zip_archive(output_dir, files_to_exclude=None):
    """
    创建ZIP压缩包
    
    参数:
        output_dir: 输出目录
        files_to_exclude: 要排除的文件列表
    """
    today = datetime.now().strftime("%Y%m%d")
    zip_path = os.path.join(output_dir, f"{today}_价格波动分析.zip")
    
    if files_to_exclude is None:
        files_to_exclude = [f"{today}_价格波动分析.zip"]
    else:
        files_to_exclude.append(f"{today}_价格波动分析.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                # 跳过排除的文件
                if file in files_to_exclude:
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    print(f"ZIP压缩包已创建: {zip_path}")
    return zip_path 