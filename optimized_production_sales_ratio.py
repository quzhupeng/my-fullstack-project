#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的产销率计算模块
版本: 2.0
作者: Kilo Code
日期: 2025-01-05

主要优化:
1. 增强的产销率计算逻辑和异常处理
2. 多维度产销率分析（按产品、部门、时间）
3. 数据质量验证和异常检测
4. 性能优化和批量处理
5. 详细的计算报告和可视化
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_sales_ratio.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RatioCalculationResult:
    """产销率计算结果数据类"""
    product_name: str
    department: str
    date_range: str
    production_volume: float
    sales_volume: float
    ratio_percentage: float
    is_abnormal: bool
    calculation_method: str
    data_quality_score: float

@dataclass
class RatioAnalysisReport:
    """产销率分析报告数据类"""
    timestamp: str
    total_products: int
    avg_ratio: float
    max_ratio: float
    min_ratio: float
    abnormal_ratios_count: int
    department_ratios: Dict[str, float]
    product_ratios: List[RatioCalculationResult]
    data_quality_issues: List[str]
    recommendations: List[str]

class ProductionSalesRatioAnalyzer:
    """产销率分析器类"""
    
    def __init__(self, excel_folder: str = './Excel文件夹/'):
        self.excel_folder = excel_folder
        self.logger = logging.getLogger(f"{__name__}.ProductionSalesRatioAnalyzer")
        
        # 异常阈值配置
        self.abnormal_ratio_threshold = {
            'min': 0,      # 最小合理产销率
            'max': 200,    # 最大合理产销率
            'warning': 150 # 警告阈值
        }
        
        # 数据质量评分权重
        self.quality_weights = {
            'completeness': 0.3,    # 数据完整性
            'accuracy': 0.4,        # 数据准确性
            'consistency': 0.3      # 数据一致性
        }
    
    def load_and_validate_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """加载并验证销售和库存数据"""
        self.logger.info("开始加载销售和库存数据...")
        
        try:
            # 加载销售数据
            sales_path = f"{self.excel_folder}/销售发票执行查询.xlsx"
            sales_data = pd.read_excel(sales_path)
            self.logger.info(f"销售数据加载完成，原始记录数: {len(sales_data)}")
            
            # 加载库存数据（包含生产信息）
            inventory_path = f"{self.excel_folder}/收发存汇总表查询.xlsx"
            inventory_data = pd.read_excel(inventory_path)
            self.logger.info(f"库存数据加载完成，原始记录数: {len(inventory_data)}")
            
            # 数据验证
            sales_data = self._validate_sales_data(sales_data)
            inventory_data = self._validate_inventory_data(inventory_data)
            
            return sales_data, inventory_data
            
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            raise
    
    def _validate_sales_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证销售数据"""
        self.logger.info("开始验证销售数据...")
        original_count = len(df)
        
        # 检查必要列是否存在
        required_columns = ['物料名称', '主数量', '责任部门']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"销售数据缺少必要列: {missing_columns}")
        
        # 数据清洗
        df = self._apply_business_filters(df, 'sales')
        
        # 数据类型转换和验证
        df['主数量'] = pd.to_numeric(df['主数量'], errors='coerce')
        df = df.dropna(subset=['主数量'])
        df = df[df['主数量'] > 0]  # 销量必须大于0
        
        validated_count = len(df)
        self.logger.info(f"销售数据验证完成: {original_count} → {validated_count} 条记录")
        
        return df
    
    def _validate_inventory_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证库存数据"""
        self.logger.info("开始验证库存数据...")
        original_count = len(df)
        
        # 检查必要列是否存在
        required_columns = ['物料名称', '入库', '责任部门']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"库存数据缺少必要列: {missing_columns}")
        
        # 数据清洗
        df = self._apply_business_filters(df, 'inventory')
        
        # 数据类型转换和验证
        df['入库'] = pd.to_numeric(df['入库'], errors='coerce')
        df = df.dropna(subset=['入库'])
        df = df[df['入库'] > 0]  # 入库量必须大于0
        
        validated_count = len(df)
        self.logger.info(f"库存数据验证完成: {original_count} → {validated_count} 条记录")
        
        return df
    
    def _apply_business_filters(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """应用业务过滤规则"""
        # 通用过滤规则
        # 1. 排除物料分类为"副产品"、"空白"的记录
        if '物料分类' in df.columns:
            df = df[~df['物料分类'].isin(['副产品', '空白', ''])]
        
        if '物料分类名称' in df.columns:
            df = df[~df['物料分类名称'].isin(['副产品', '生鲜品其他', ''])]
        
        # 2. 排除物料名称包含"鲜"的记录
        if '物料名称' in df.columns:
            df = df[~df['物料名称'].str.contains('鲜', na=False)]
        
        # 3. 排除客户名称为空、"副产品"、"鲜品"的记录（仅销售数据）
        if data_type == 'sales' and '客户名称' in df.columns:
            df = df[~df['客户名称'].isin(['', '副产品', '鲜品'])]
        
        return df
    
    def calculate_production_sales_ratio(self, sales_data: pd.DataFrame, 
                                       inventory_data: pd.DataFrame,
                                       by_department: bool = True,
                                       by_product: bool = True) -> RatioAnalysisReport:
        """计算产销率"""
        self.logger.info("开始计算产销率...")
        
        results = []
        data_quality_issues = []
        
        # 按部门计算产销率
        if by_department:
            dept_results = self._calculate_by_department(sales_data, inventory_data)
            results.extend(dept_results)
        
        # 按产品计算产销率
        if by_product:
            product_results = self._calculate_by_product(sales_data, inventory_data)
            results.extend(product_results)
        
        # 生成分析报告
        report = self._generate_analysis_report(results, data_quality_issues)
        
        self.logger.info(f"产销率计算完成，共计算 {len(results)} 个产销率")
        return report
    
    def _calculate_by_department(self, sales_data: pd.DataFrame, 
                               inventory_data: pd.DataFrame) -> List[RatioCalculationResult]:
        """按部门计算产销率"""
        self.logger.info("按部门计算产销率...")
        
        results = []
        
        # 获取所有部门
        departments = set()
        if '责任部门' in sales_data.columns:
            departments.update(sales_data['责任部门'].dropna().unique())
        if '责任部门' in inventory_data.columns:
            departments.update(inventory_data['责任部门'].dropna().unique())
        
        for dept in departments:
            try:
                # 筛选部门数据
                dept_sales = sales_data[sales_data['责任部门'] == dept] if '责任部门' in sales_data.columns else pd.DataFrame()
                dept_inventory = inventory_data[inventory_data['责任部门'] == dept] if '责任部门' in inventory_data.columns else pd.DataFrame()
                
                # 计算总销量和总产量
                total_sales = dept_sales['主数量'].sum() if not dept_sales.empty else 0
                total_production = dept_inventory['入库'].sum() if not dept_inventory.empty else 0
                
                # 计算产销率
                ratio = self._safe_ratio_calculation(total_sales, total_production)
                
                # 数据质量评分
                quality_score = self._calculate_data_quality_score(dept_sales, dept_inventory)
                
                # 异常检测
                is_abnormal = self._is_abnormal_ratio(ratio)
                
                result = RatioCalculationResult(
                    product_name="全部产品",
                    department=dept,
                    date_range="全期间",
                    production_volume=total_production,
                    sales_volume=total_sales,
                    ratio_percentage=ratio,
                    is_abnormal=is_abnormal,
                    calculation_method="部门汇总",
                    data_quality_score=quality_score
                )
                
                results.append(result)
                self.logger.info(f"{dept} 部门产销率: {ratio:.2f}%")
                
            except Exception as e:
                self.logger.error(f"计算 {dept} 部门产销率时出错: {e}")
        
        return results
    
    def _calculate_by_product(self, sales_data: pd.DataFrame, 
                            inventory_data: pd.DataFrame) -> List[RatioCalculationResult]:
        """按产品计算产销率"""
        self.logger.info("按产品计算产销率...")
        
        results = []
        
        # 获取所有产品
        products = set()
        if '物料名称' in sales_data.columns:
            products.update(sales_data['物料名称'].dropna().unique())
        if '物料名称' in inventory_data.columns:
            products.update(inventory_data['物料名称'].dropna().unique())
        
        for product in products:
            try:
                # 筛选产品数据
                product_sales = sales_data[sales_data['物料名称'] == product] if '物料名称' in sales_data.columns else pd.DataFrame()
                product_inventory = inventory_data[inventory_data['物料名称'] == product] if '物料名称' in inventory_data.columns else pd.DataFrame()
                
                # 计算总销量和总产量
                total_sales = product_sales['主数量'].sum() if not product_sales.empty else 0
                total_production = product_inventory['入库'].sum() if not product_inventory.empty else 0
                
                # 计算产销率
                ratio = self._safe_ratio_calculation(total_sales, total_production)
                
                # 获取主要部门
                main_dept = "未知部门"
                if not product_sales.empty and '责任部门' in product_sales.columns:
                    main_dept = product_sales['责任部门'].mode().iloc[0] if len(product_sales['责任部门'].mode()) > 0 else "未知部门"
                elif not product_inventory.empty and '责任部门' in product_inventory.columns:
                    main_dept = product_inventory['责任部门'].mode().iloc[0] if len(product_inventory['责任部门'].mode()) > 0 else "未知部门"
                
                # 数据质量评分
                quality_score = self._calculate_data_quality_score(product_sales, product_inventory)
                
                # 异常检测
                is_abnormal = self._is_abnormal_ratio(ratio)
                
                result = RatioCalculationResult(
                    product_name=product,
                    department=main_dept,
                    date_range="全期间",
                    production_volume=total_production,
                    sales_volume=total_sales,
                    ratio_percentage=ratio,
                    is_abnormal=is_abnormal,
                    calculation_method="产品汇总",
                    data_quality_score=quality_score
                )
                
                results.append(result)
                
                if is_abnormal:
                    self.logger.warning(f"异常产销率检测 - {product}: {ratio:.2f}%")
                
            except Exception as e:
                self.logger.error(f"计算 {product} 产销率时出错: {e}")
        
        return results
    
    def _safe_ratio_calculation(self, sales_volume: float, production_volume: float) -> float:
        """安全的产销率计算"""
        try:
            if production_volume <= 0:
                return 0.0
            
            ratio = (sales_volume / production_volume) * 100
            
            # 处理极端值
            if ratio > 1000:
                self.logger.warning(f"极端产销率值: {ratio:.2f}%, 销量: {sales_volume}, 产量: {production_volume}")
                return min(ratio, 1000)
            
            return round(ratio, 2)
            
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0
    
    def _calculate_data_quality_score(self, sales_df: pd.DataFrame, inventory_df: pd.DataFrame) -> float:
        """计算数据质量评分"""
        scores = []
        
        # 完整性评分
        completeness_score = 0
        if not sales_df.empty:
            completeness_score += 0.5
        if not inventory_df.empty:
            completeness_score += 0.5
        scores.append(completeness_score * self.quality_weights['completeness'])
        
        # 准确性评分（基于数值合理性）
        accuracy_score = 1.0
        if not sales_df.empty and '主数量' in sales_df.columns:
            if (sales_df['主数量'] < 0).any():
                accuracy_score -= 0.3
        if not inventory_df.empty and '入库' in inventory_df.columns:
            if (inventory_df['入库'] < 0).any():
                accuracy_score -= 0.3
        scores.append(max(0, accuracy_score) * self.quality_weights['accuracy'])
        
        # 一致性评分（数据量级是否合理）
        consistency_score = 1.0
        if not sales_df.empty and not inventory_df.empty:
            sales_total = sales_df['主数量'].sum() if '主数量' in sales_df.columns else 0
            production_total = inventory_df['入库'].sum() if '入库' in inventory_df.columns else 0
            if production_total > 0:
                ratio = sales_total / production_total
                if ratio > 10 or ratio < 0.01:  # 产销比例过于极端
                    consistency_score -= 0.5
        scores.append(max(0, consistency_score) * self.quality_weights['consistency'])
        
        return round(sum(scores), 2)
    
    def _is_abnormal_ratio(self, ratio: float) -> bool:
        """判断产销率是否异常"""
        return (ratio < self.abnormal_ratio_threshold['min'] or 
                ratio > self.abnormal_ratio_threshold['max'])
    
    def _generate_analysis_report(self, results: List[RatioCalculationResult], 
                                data_quality_issues: List[str]) -> RatioAnalysisReport:
        """生成分析报告"""
        if not results:
            return RatioAnalysisReport(
                timestamp=datetime.now().isoformat(),
                total_products=0,
                avg_ratio=0.0,
                max_ratio=0.0,
                min_ratio=0.0,
                abnormal_ratios_count=0,
                department_ratios={},
                product_ratios=[],
                data_quality_issues=data_quality_issues,
                recommendations=["无数据可分析"]
            )
        
        # 统计信息
        ratios = [r.ratio_percentage for r in results]
        avg_ratio = np.mean(ratios)
        max_ratio = np.max(ratios)
        min_ratio = np.min(ratios)
        abnormal_count = sum(1 for r in results if r.is_abnormal)
        
        # 按部门汇总
        dept_ratios = {}
        for result in results:
            if result.calculation_method == "部门汇总":
                dept_ratios[result.department] = result.ratio_percentage
        
        # 生成建议
        recommendations = self._generate_recommendations(results)
        
        return RatioAnalysisReport(
            timestamp=datetime.now().isoformat(),
            total_products=len([r for r in results if r.calculation_method == "产品汇总"]),
            avg_ratio=round(avg_ratio, 2),
            max_ratio=round(max_ratio, 2),
            min_ratio=round(min_ratio, 2),
            abnormal_ratios_count=abnormal_count,
            department_ratios=dept_ratios,
            product_ratios=results,
            data_quality_issues=data_quality_issues,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, results: List[RatioCalculationResult]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 分析异常产销率
        abnormal_results = [r for r in results if r.is_abnormal]
        if abnormal_results:
            high_ratio_products = [r.product_name for r in abnormal_results if r.ratio_percentage > self.abnormal_ratio_threshold['max']]
            low_ratio_products = [r.product_name for r in abnormal_results if r.ratio_percentage < self.abnormal_ratio_threshold['min']]
            
            if high_ratio_products:
                recommendations.append(f"产销率过高的产品需要检查生产数据准确性: {', '.join(high_ratio_products[:5])}")
            
            if low_ratio_products:
                recommendations.append(f"产销率过低的产品需要关注销售情况: {', '.join(low_ratio_products[:5])}")
        
        # 分析数据质量
        low_quality_results = [r for r in results if r.data_quality_score < 0.7]
        if low_quality_results:
            recommendations.append(f"数据质量较低的产品需要改进数据收集: {len(low_quality_results)} 个产品")
        
        # 部门分析
        dept_results = [r for r in results if r.calculation_method == "部门汇总"]
        if dept_results:
            dept_ratios = [(r.department, r.ratio_percentage) for r in dept_results]
            dept_ratios.sort(key=lambda x: x[1], reverse=True)
            
            if len(dept_ratios) > 1:
                best_dept = dept_ratios[0]
                worst_dept = dept_ratios[-1]
                recommendations.append(f"部门产销率差异较大，{best_dept[0]}({best_dept[1]:.1f}%)表现最好，{worst_dept[0]}({worst_dept[1]:.1f}%)需要改进")
        
        if not recommendations:
            recommendations.append("整体产销率表现良好，继续保持")
        
        return recommendations
    
    def export_report_to_json(self, report: RatioAnalysisReport, filename: str = None) -> str:
        """导出报告为JSON格式"""
        if filename is None:
            filename = f"production_sales_ratio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 转换为可序列化的字典
        report_dict = {
            'timestamp': report.timestamp,
            'summary': {
                'total_products': report.total_products,
                'avg_ratio': report.avg_ratio,
                'max_ratio': report.max_ratio,
                'min_ratio': report.min_ratio,
                'abnormal_ratios_count': report.abnormal_ratios_count
            },
            'department_ratios': report.department_ratios,
            'product_ratios': [
                {
                    'product_name': r.product_name,
                    'department': r.department,
                    'date_range': r.date_range,
                    'production_volume': r.production_volume,
                    'sales_volume': r.sales_volume,
                    'ratio_percentage': r.ratio_percentage,
                    'is_abnormal': r.is_abnormal,
                    'calculation_method': r.calculation_method,
                    'data_quality_score': r.data_quality_score
                } for r in report.product_ratios
            ],
            'data_quality_issues': report.data_quality_issues,
            'recommendations': report.recommendations
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"报告已导出到: {filename}")
        return filename
    
    def print_summary_report(self, report: RatioAnalysisReport):
        """打印摘要报告"""
        print("\n" + "=" * 80)
        print("产销率分析报告摘要")
        print("=" * 80)
        print(f"分析时间: {report.timestamp}")
        print(f"分析产品数量: {report.total_products}")
        print(f"平均产销率: {report.avg_ratio:.2f}%")
        print(f"最高产销率: {report.max_ratio:.2f}%")
        print(f"最低产销率: {report.min_ratio:.2f}%")
        print(f"异常产销率数量: {report.abnormal_ratios_count}")
        
        print("\n部门产销率:")
        for dept, ratio in report.department_ratios.items():
            status = "⚠️" if ratio > 150 or ratio < 50 else "✅"
            print(f"  {status} {dept}: {ratio:.2f}%")
        
        print("\n改进建议:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        if report.data_quality_issues:
            print("\n数据质量问题:")
            for issue in report.data_quality_issues:
                print(f"  ⚠️ {issue}")
        
        print("=" * 80)


def main():
    """主函数"""
    print("=" * 80)
    print("优化的产销率计算系统 v2.0")
    print("=" * 80)
    
    try:
        # 创建分析器
        analyzer = ProductionSalesRatioAnalyzer()
        
        # 加载数据
        sales_data, inventory_data = analyzer.load_and_validate_data()
        
        # 计算产销率
        report = analyzer.calculate_production_sales_ratio(
            sales_data, inventory_data,
            by_department=True,
            by_product=True
        )
        
        # 打印摘要报告
        analyzer.print_summary_report(report)
        
        # 导出详细报告
        json_file = analyzer.export_report_to_json(report)
        print(f"\n📄 详细报告已保存到: {json_file}")
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        print(f"\n❌ 程序执行失败: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()