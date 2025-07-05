#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量监控系统
版本: 1.0
作者: Kilo Code
日期: 2025-01-05

功能:
1. 实时数据质量监控
2. 异常检测和告警
3. 数据质量报告生成
4. 自动化质量检查
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json
import os
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_quality_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QualityIssue:
    """数据质量问题数据类"""
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    affected_records: int
    table_name: str
    column_name: str
    detection_time: str
    suggested_action: str

@dataclass
class QualityMetrics:
    """数据质量指标数据类"""
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    validity_score: float
    overall_score: float
    total_records: int
    valid_records: int
    issue_count: int

@dataclass
class QualityReport:
    """数据质量报告数据类"""
    report_id: str
    timestamp: str
    metrics: QualityMetrics
    issues: List[QualityIssue]
    recommendations: List[str]
    data_sources: List[str]
    processing_time: float

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self, excel_folder: str = './Excel文件夹/'):
        self.excel_folder = excel_folder
        self.logger = logging.getLogger(f"{__name__}.DataQualityMonitor")
        
        # 质量阈值配置
        self.quality_thresholds = {
            'excellent': 0.95,
            'good': 0.85,
            'acceptable': 0.70,
            'poor': 0.50
        }
        
        # 异常检测参数
        self.anomaly_params = {
            'z_score_threshold': 3.0,
            'iqr_multiplier': 1.5,
            'ratio_min': 0,
            'ratio_max': 200,
            'volume_min': 0,
            'volume_max': 1000000
        }
        
        # 数据源配置
        self.data_sources = {
            'sales': '销售发票执行查询.xlsx',
            'inventory': '收发存汇总表查询.xlsx',
            'production': '产成品入库列表.xlsx'
        }
    
    def run_quality_check(self) -> QualityReport:
        """运行完整的数据质量检查"""
        start_time = datetime.now()
        self.logger.info("开始数据质量检查...")
        
        try:
            # 加载所有数据源
            datasets = self._load_all_datasets()
            
            # 执行质量检查
            all_issues = []
            all_metrics = []
            
            for source_name, df in datasets.items():
                if df is not None and not df.empty:
                    issues, metrics = self._check_dataset_quality(df, source_name)
                    all_issues.extend(issues)
                    all_metrics.append(metrics)
            
            # 计算整体质量指标
            overall_metrics = self._calculate_overall_metrics(all_metrics)
            
            # 生成建议
            recommendations = self._generate_recommendations(all_issues, overall_metrics)
            
            # 创建报告
            processing_time = (datetime.now() - start_time).total_seconds()
            report = QualityReport(
                report_id=f"QR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                metrics=overall_metrics,
                issues=all_issues,
                recommendations=recommendations,
                data_sources=list(datasets.keys()),
                processing_time=processing_time
            )
            
            self.logger.info(f"数据质量检查完成，耗时 {processing_time:.2f} 秒")
            return report
            
        except Exception as e:
            self.logger.error(f"数据质量检查失败: {e}")
            raise
    
    def _load_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """加载所有数据集"""
        datasets = {}
        
        for source_name, filename in self.data_sources.items():
            try:
                filepath = os.path.join(self.excel_folder, filename)
                if os.path.exists(filepath):
                    df = pd.read_excel(filepath)
                    datasets[source_name] = df
                    self.logger.info(f"加载 {source_name} 数据: {len(df)} 条记录")
                else:
                    self.logger.warning(f"数据文件不存在: {filepath}")
                    datasets[source_name] = None
            except Exception as e:
                self.logger.error(f"加载 {source_name} 数据失败: {e}")
                datasets[source_name] = None
        
        return datasets
    
    def _check_dataset_quality(self, df: pd.DataFrame, source_name: str) -> Tuple[List[QualityIssue], QualityMetrics]:
        """检查单个数据集的质量"""
        self.logger.info(f"检查 {source_name} 数据质量...")
        
        issues = []
        
        # 1. 完整性检查
        completeness_issues, completeness_score = self._check_completeness(df, source_name)
        issues.extend(completeness_issues)
        
        # 2. 准确性检查
        accuracy_issues, accuracy_score = self._check_accuracy(df, source_name)
        issues.extend(accuracy_issues)
        
        # 3. 一致性检查
        consistency_issues, consistency_score = self._check_consistency(df, source_name)
        issues.extend(consistency_issues)
        
        # 4. 有效性检查
        validity_issues, validity_score = self._check_validity(df, source_name)
        issues.extend(validity_issues)
        
        # 计算整体质量分数
        overall_score = (completeness_score + accuracy_score + consistency_score + validity_score) / 4
        
        metrics = QualityMetrics(
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            validity_score=validity_score,
            overall_score=overall_score,
            total_records=len(df),
            valid_records=len(df) - len([i for i in issues if i.severity in ['high', 'critical']]),
            issue_count=len(issues)
        )
        
        return issues, metrics
    
    def _check_completeness(self, df: pd.DataFrame, source_name: str) -> Tuple[List[QualityIssue], float]:
        """检查数据完整性"""
        issues = []
        
        # 检查空值
        null_counts = df.isnull().sum()
        total_cells = len(df) * len(df.columns)
        null_cells = null_counts.sum()
        
        for column, null_count in null_counts.items():
            if null_count > 0:
                severity = self._determine_severity(null_count / len(df))
                issues.append(QualityIssue(
                    issue_type="missing_data",
                    severity=severity,
                    description=f"列 '{column}' 有 {null_count} 个空值",
                    affected_records=null_count,
                    table_name=source_name,
                    column_name=column,
                    detection_time=datetime.now().isoformat(),
                    suggested_action=f"检查 {column} 列的数据录入流程"
                ))
        
        # 计算完整性分数
        completeness_score = max(0, (total_cells - null_cells) / total_cells) if total_cells > 0 else 0
        
        return issues, completeness_score
    
    def _check_accuracy(self, df: pd.DataFrame, source_name: str) -> Tuple[List[QualityIssue], float]:
        """检查数据准确性"""
        issues = []
        accuracy_violations = 0
        total_checks = 0
        
        # 检查数值列的合理性
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            total_checks += len(df)
            
            # 检查负值（对于应该为正的字段）
            if column in ['主数量', '入库', '出库', '单价']:
                negative_count = (df[column] < 0).sum()
                if negative_count > 0:
                    accuracy_violations += negative_count
                    issues.append(QualityIssue(
                        issue_type="invalid_value",
                        severity="high",
                        description=f"列 '{column}' 有 {negative_count} 个负值",
                        affected_records=negative_count,
                        table_name=source_name,
                        column_name=column,
                        detection_time=datetime.now().isoformat(),
                        suggested_action=f"检查 {column} 列的数据录入，负值可能不合理"
                    ))
            
            # 检查异常大的值
            if len(df[column].dropna()) > 0:
                q99 = df[column].quantile(0.99)
                extreme_values = (df[column] > q99 * 10).sum()
                if extreme_values > 0:
                    accuracy_violations += extreme_values
                    issues.append(QualityIssue(
                        issue_type="outlier",
                        severity="medium",
                        description=f"列 '{column}' 有 {extreme_values} 个极端值",
                        affected_records=extreme_values,
                        table_name=source_name,
                        column_name=column,
                        detection_time=datetime.now().isoformat(),
                        suggested_action=f"检查 {column} 列的极端值是否正确"
                    ))
        
        # 计算准确性分数
        accuracy_score = max(0, (total_checks - accuracy_violations) / total_checks) if total_checks > 0 else 1.0
        
        return issues, accuracy_score
    
    def _check_consistency(self, df: pd.DataFrame, source_name: str) -> Tuple[List[QualityIssue], float]:
        """检查数据一致性"""
        issues = []
        consistency_violations = 0
        total_checks = 0
        
        # 检查重复记录
        if len(df) > 0:
            duplicate_count = df.duplicated().sum()
            total_checks += len(df)
            
            if duplicate_count > 0:
                consistency_violations += duplicate_count
                issues.append(QualityIssue(
                    issue_type="duplicate_records",
                    severity="medium",
                    description=f"发现 {duplicate_count} 条重复记录",
                    affected_records=duplicate_count,
                    table_name=source_name,
                    column_name="all",
                    detection_time=datetime.now().isoformat(),
                    suggested_action="删除重复记录或检查数据录入流程"
                ))
        
        # 检查数据格式一致性
        text_columns = df.select_dtypes(include=['object']).columns
        for column in text_columns:
            if column in df.columns:
                # 检查空字符串和空格
                empty_strings = (df[column].astype(str).str.strip() == '').sum()
                total_checks += len(df)
                
                if empty_strings > 0:
                    consistency_violations += empty_strings
                    issues.append(QualityIssue(
                        issue_type="format_inconsistency",
                        severity="low",
                        description=f"列 '{column}' 有 {empty_strings} 个空字符串",
                        affected_records=empty_strings,
                        table_name=source_name,
                        column_name=column,
                        detection_time=datetime.now().isoformat(),
                        suggested_action=f"标准化 {column} 列的数据格式"
                    ))
        
        # 计算一致性分数
        consistency_score = max(0, (total_checks - consistency_violations) / total_checks) if total_checks > 0 else 1.0
        
        return issues, consistency_score
    
    def _check_validity(self, df: pd.DataFrame, source_name: str) -> Tuple[List[QualityIssue], float]:
        """检查数据有效性"""
        issues = []
        validity_violations = 0
        total_checks = 0
        
        # 检查业务规则
        if '物料名称' in df.columns:
            total_checks += len(df)
            
            # 检查是否包含应该过滤的产品
            fresh_products = df[df['物料名称'].str.contains('鲜', na=False)]
            if len(fresh_products) > 0:
                validity_violations += len(fresh_products)
                issues.append(QualityIssue(
                    issue_type="business_rule_violation",
                    severity="medium",
                    description=f"发现 {len(fresh_products)} 个鲜品记录（应被过滤）",
                    affected_records=len(fresh_products),
                    table_name=source_name,
                    column_name="物料名称",
                    detection_time=datetime.now().isoformat(),
                    suggested_action="检查业务过滤规则是否正确应用"
                ))
        
        # 检查日期有效性
        date_columns = df.select_dtypes(include=['datetime64']).columns
        for column in date_columns:
            total_checks += len(df)
            
            # 检查未来日期
            future_dates = (df[column] > datetime.now()).sum()
            if future_dates > 0:
                validity_violations += future_dates
                issues.append(QualityIssue(
                    issue_type="invalid_date",
                    severity="high",
                    description=f"列 '{column}' 有 {future_dates} 个未来日期",
                    affected_records=future_dates,
                    table_name=source_name,
                    column_name=column,
                    detection_time=datetime.now().isoformat(),
                    suggested_action=f"检查 {column} 列的日期录入"
                ))
        
        # 计算有效性分数
        validity_score = max(0, (total_checks - validity_violations) / total_checks) if total_checks > 0 else 1.0
        
        return issues, validity_score
    
    def _determine_severity(self, ratio: float) -> str:
        """根据比例确定问题严重程度"""
        if ratio >= 0.5:
            return "critical"
        elif ratio >= 0.2:
            return "high"
        elif ratio >= 0.05:
            return "medium"
        else:
            return "low"
    
    def _calculate_overall_metrics(self, metrics_list: List[QualityMetrics]) -> QualityMetrics:
        """计算整体质量指标"""
        if not metrics_list:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        # 加权平均（按记录数加权）
        total_records = sum(m.total_records for m in metrics_list)
        
        if total_records == 0:
            return QualityMetrics(0, 0, 0, 0, 0, 0, 0, 0)
        
        weighted_completeness = sum(m.completeness_score * m.total_records for m in metrics_list) / total_records
        weighted_accuracy = sum(m.accuracy_score * m.total_records for m in metrics_list) / total_records
        weighted_consistency = sum(m.consistency_score * m.total_records for m in metrics_list) / total_records
        weighted_validity = sum(m.validity_score * m.total_records for m in metrics_list) / total_records
        
        overall_score = (weighted_completeness + weighted_accuracy + weighted_consistency + weighted_validity) / 4
        
        return QualityMetrics(
            completeness_score=round(weighted_completeness, 3),
            accuracy_score=round(weighted_accuracy, 3),
            consistency_score=round(weighted_consistency, 3),
            validity_score=round(weighted_validity, 3),
            overall_score=round(overall_score, 3),
            total_records=total_records,
            valid_records=sum(m.valid_records for m in metrics_list),
            issue_count=sum(m.issue_count for m in metrics_list)
        )
    
    def _generate_recommendations(self, issues: List[QualityIssue], metrics: QualityMetrics) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于整体质量分数的建议
        if metrics.overall_score < self.quality_thresholds['poor']:
            recommendations.append("数据质量较差，建议全面检查数据录入流程")
        elif metrics.overall_score < self.quality_thresholds['acceptable']:
            recommendations.append("数据质量需要改进，重点关注高严重性问题")
        elif metrics.overall_score < self.quality_thresholds['good']:
            recommendations.append("数据质量基本可接受，建议持续优化")
        else:
            recommendations.append("数据质量良好，保持现有流程")
        
        # 基于具体问题的建议
        critical_issues = [i for i in issues if i.severity == 'critical']
        high_issues = [i for i in issues if i.severity == 'high']
        
        if critical_issues:
            recommendations.append(f"紧急处理 {len(critical_issues)} 个严重问题")
        
        if high_issues:
            recommendations.append(f"优先处理 {len(high_issues)} 个高优先级问题")
        
        # 基于问题类型的建议
        issue_types = {}
        for issue in issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
        
        if 'missing_data' in issue_types:
            recommendations.append("加强数据录入的完整性检查")
        
        if 'duplicate_records' in issue_types:
            recommendations.append("建立重复数据检测和清理机制")
        
        if 'business_rule_violation' in issue_types:
            recommendations.append("检查和完善业务规则过滤逻辑")
        
        return recommendations
    
    def export_report(self, report: QualityReport, format: str = 'json') -> str:
        """导出质量报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == 'json':
            filename = f"data_quality_report_{timestamp}.json"
            
            # 转换为可序列化的字典
            report_dict = {
                'report_id': report.report_id,
                'timestamp': report.timestamp,
                'metrics': asdict(report.metrics),
                'issues': [asdict(issue) for issue in report.issues],
                'recommendations': report.recommendations,
                'data_sources': report.data_sources,
                'processing_time': report.processing_time
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            
        elif format.lower() == 'html':
            filename = f"data_quality_report_{timestamp}.html"
            html_content = self._generate_html_report(report)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        self.logger.info(f"质量报告已导出: {filename}")
        return filename
    
    def _generate_html_report(self, report: QualityReport) -> str:
        """生成HTML格式的报告"""
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>数据质量报告 - {report.report_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .issues {{ margin: 20px 0; }}
                .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .critical {{ border-left-color: #d32f2f; }}
                .high {{ border-left-color: #f57c00; }}
                .medium {{ border-left-color: #fbc02d; }}
                .low {{ border-left-color: #388e3c; }}
                .recommendations {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>数据质量报告</h1>
                <p><strong>报告ID:</strong> {report.report_id}</p>
                <p><strong>生成时间:</strong> {report.timestamp}</p>
                <p><strong>处理时间:</strong> {report.processing_time:.2f} 秒</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>整体质量</h3>
                    <p>{report.metrics.overall_score:.1%}</p>
                </div>
                <div class="metric">
                    <h3>完整性</h3>
                    <p>{report.metrics.completeness_score:.1%}</p>
                </div>
                <div class="metric">
                    <h3>准确性</h3>
                    <p>{report.metrics.accuracy_score:.1%}</p>
                </div>
                <div class="metric">
                    <h3>一致性</h3>
                    <p>{report.metrics.consistency_score:.1%}</p>
                </div>
                <div class="metric">
                    <h3>有效性</h3>
                    <p>{report.metrics.validity_score:.1%}</p>
                </div>
            </div>
            
            <h2>质量问题 ({len(report.issues)} 个)</h2>
            <div class="issues">
        """
        
        for issue in report.issues:
            html += f"""
                <div class="issue {issue.severity}">
                    <h4>{issue.issue_type} - {issue.severity.upper()}</h4>
                    <p><strong>描述:</strong> {issue.description}</p>
                    <p><strong>影响记录:</strong> {issue.affected_records}</p>
                    <p><strong>建议操作:</strong> {issue.suggested_action}</p>
                </div>
            """
        
        html += f"""
            </div>
            
            <h2>改进建议</h2>
            <div class="recommendations">
                <ul>
        """
        
        for rec in report.recommendations:
            html += f"<li>{rec}</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def print_summary(self, report: QualityReport):
        """打印报告摘要"""
        print("\n" + "=" * 80)
        print("数据质量监控报告摘要")
        print("=" * 80)
        print(f"报告ID: {report.report_id}")
        print(f"生成时间: {report.timestamp}")
        print(f"处理时间: {report.processing_time:.2f} 秒")
        print(f"数据源: {', '.join(report.data_sources)}")
        
        print(f"\n质量指标:")
        print(f"  整体质量: {report.metrics.overall_score:.1%}")
        print(f"  完整性: {report.metrics.completeness_score:.1%}")
        print(f"  准确性: {report.metrics.accuracy_score:.1%}")
        print(f"  一致性: {report.metrics.consistency_score:.1%}")
        print(f"  有效性: {report.metrics.validity_score:.1%}")
        
        print(f"\n数据统计:")
        print(f"  总记录数: {report.metrics.total_records:,}")
        print(f"  有效记录数: {report.metrics.valid_records:,}")
        print(f"  问题数量: {report.metrics.issue_count}")
        
        # 按严重程度统计问题
        severity_counts = {}
        for issue in report.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        if severity_counts:
            print(f"\n问题分布:")
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in severity_counts:
                    print(f"  {severity.upper()}: {severity_counts[severity]}")
        
        print(f"\n改进建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
        
        print("=" * 80)


def main():
    """主函数"""
    print("=" * 80)
    print("数据质量监控系统 v1.0")
    print("=" * 80)
    
    try:
        # 创建监控器
        monitor = DataQualityMonitor()
        
        # 运行质量检查
        report = monitor.run_quality_check()
        
        # 打印摘要
        monitor.print_summary(report)
        
        # 导出报告
        json_file = monitor.export_report(report, 'json')
        html_file = monitor.export_report(report, 'html')
        
        print(f"\n📄 详细报告已保存:")
        print(f"  JSON格式: {json_file}")
        print(f"  HTML格式: {html_file}")
        
    except Exception as e:
        logger.error(f"数据质量监控失败: {e}")
        print(f"\n❌ 监控失败: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()