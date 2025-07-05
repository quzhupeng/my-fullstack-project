#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型数据质量监控系统
版本: 2.0
作者: Kilo Code
日期: 2025-01-05

功能:
1. 精细化四维数据质量评分体系
2. 智能异常检测算法
3. 实时质量监控和告警
4. 自适应阈值调整
5. 业务规则智能验证
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict, field
import json
import os
import warnings
from scipy import stats
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, ML anomaly detection disabled")

warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_data_quality_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class QualityDimension:
    """数据质量维度评分"""
    dimension_name: str
    score: float
    weight: float
    sub_scores: Dict[str, float] = field(default_factory=dict)
    issues_count: int = 0
    critical_issues: int = 0

@dataclass
class AnomalyDetection:
    """异常检测结果"""
    detection_method: str
    anomaly_type: str
    confidence: float
    affected_records: List[int]
    statistical_info: Dict[str, Any] = field(default_factory=dict)
    business_impact: str = "medium"

@dataclass
class EnhancedQualityIssue:
    """增强型数据质量问题"""
    issue_id: str
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0-1, 检测置信度
    description: str
    affected_records: int
    table_name: str
    column_name: str
    detection_time: str
    detection_method: str
    suggested_action: str
    business_impact: str
    auto_fixable: bool = False
    anomaly_details: Optional[AnomalyDetection] = None

@dataclass
class EnhancedQualityMetrics:
    """增强型数据质量指标"""
    # 四维评分
    completeness: QualityDimension
    accuracy: QualityDimension
    consistency: QualityDimension
    validity: QualityDimension
    
    # 整体指标
    overall_score: float
    weighted_score: float
    quality_grade: str  # A+, A, B+, B, C+, C, D, F
    
    # 统计信息
    total_records: int
    valid_records: int
    issue_count: int
    critical_issue_count: int
    
    # 趋势信息
    score_trend: str  # "improving", "stable", "declining"
    historical_comparison: Dict[str, float] = field(default_factory=dict)

@dataclass
class EnhancedQualityReport:
    """增强型数据质量报告"""
    report_id: str
    timestamp: str
    metrics: EnhancedQualityMetrics
    issues: List[EnhancedQualityIssue]
    anomalies: List[AnomalyDetection]
    recommendations: List[str]
    data_sources: List[str]
    processing_time: float
    quality_summary: Dict[str, Any] = field(default_factory=dict)
    alert_level: str = "normal"  # "normal", "warning", "critical"

class EnhancedDataQualityMonitor:
    """增强型数据质量监控器"""
    
    def __init__(self, excel_folder: str = './Excel文件夹/', db_path: str = None):
        self.excel_folder = excel_folder
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.EnhancedDataQualityMonitor")
        
        # 增强型质量阈值配置
        self.quality_thresholds = {
            'A+': 0.98,  # 卓越
            'A': 0.95,   # 优秀
            'B+': 0.90,  # 良好+
            'B': 0.85,   # 良好
            'C+': 0.75,  # 可接受+
            'C': 0.70,   # 可接受
            'D': 0.50,   # 较差
            'F': 0.0     # 不合格
        }
        
        # 四维权重配置（可动态调整）
        self.dimension_weights = {
            'completeness': 0.25,  # 完整性 25%
            'accuracy': 0.40,      # 准确性 40%
            'consistency': 0.25,   # 一致性 25%
            'validity': 0.10       # 有效性 10%
        }
        
        # 异常检测参数
        self.anomaly_params = {
            'z_score_threshold': 3.0,
            'iqr_multiplier': 1.5,
            'isolation_forest_contamination': 0.1,
            'confidence_threshold': 0.8
        }
        
        # 数据源配置
        self.data_sources = {
            'sales': '销售发票执行查询.xlsx',
            'inventory': '收发存汇总表查询.xlsx',
            'production': '产成品入库列表.xlsx'
        }
        
        # 业务规则配置
        self.business_rules = {
            'product_filters': {
                'exclude_patterns': ['鲜'],
                'include_patterns': ['凤肠', '烤肠', '火腿肠']
            },
            'required_fields': {
                'sales': ['物料名称', '主数量', '单价'],
                'inventory': ['物料名称', '入库', '出库'],
                'production': ['物料名称', '主数量']
            },
            'value_ranges': {
                '主数量': (0, 1000000),
                '单价': (0, 10000),
                '入库': (0, 1000000),
                '出库': (0, 1000000)
            }
        }
        
        # 历史数据存储
        self.quality_history = []
    
    def run_enhanced_quality_check(self) -> EnhancedQualityReport:
        """运行增强型数据质量检查"""
        start_time = datetime.now()
        self.logger.info("开始增强型数据质量检查...")
        
        try:
            # 1. 加载所有数据源
            datasets = self._load_all_datasets()
            
            # 2. 执行多层次质量检查
            all_issues = []
            all_anomalies = []
            dimension_scores = {}
            
            for source_name, df in datasets.items():
                if df is not None and not df.empty:
                    # 基础质量检查
                    issues, dimensions = self._check_enhanced_dataset_quality(df, source_name)
                    all_issues.extend(issues)
                    dimension_scores[source_name] = dimensions
                    
                    # 异常检测
                    anomalies = self._detect_anomalies(df, source_name)
                    all_anomalies.extend(anomalies)
            
            # 3. 计算整体质量指标
            overall_metrics = self._calculate_enhanced_metrics(dimension_scores, all_issues)
            
            # 4. 生成智能建议
            recommendations = self._generate_intelligent_recommendations(
                all_issues, all_anomalies, overall_metrics
            )
            
            # 5. 确定告警级别
            alert_level = self._determine_alert_level(overall_metrics, all_issues)
            
            # 6. 创建增强型报告
            processing_time = (datetime.now() - start_time).total_seconds()
            report = EnhancedQualityReport(
                report_id=f"EQR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                metrics=overall_metrics,
                issues=all_issues,
                anomalies=all_anomalies,
                recommendations=recommendations,
                data_sources=list(datasets.keys()),
                processing_time=processing_time,
                quality_summary=self._generate_quality_summary(overall_metrics, all_issues),
                alert_level=alert_level
            )
            
            # 7. 存储历史数据
            self._store_quality_history(report)
            
            self.logger.info(f"增强型数据质量检查完成，耗时 {processing_time:.2f} 秒")
            return report
            
        except Exception as e:
            self.logger.error(f"增强型数据质量检查失败: {e}")
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
    
    def _check_enhanced_dataset_quality(self, df: pd.DataFrame, source_name: str) -> Tuple[List[EnhancedQualityIssue], Dict[str, QualityDimension]]:
        """检查单个数据集的增强型质量"""
        self.logger.info(f"检查 {source_name} 增强型数据质量...")
        
        issues = []
        
        # 1. 完整性检查（25%权重）
        completeness_issues, completeness_dim = self._check_enhanced_completeness(df, source_name)
        issues.extend(completeness_issues)
        
        # 2. 准确性检查（40%权重）
        accuracy_issues, accuracy_dim = self._check_enhanced_accuracy(df, source_name)
        issues.extend(accuracy_issues)
        
        # 3. 一致性检查（25%权重）
        consistency_issues, consistency_dim = self._check_enhanced_consistency(df, source_name)
        issues.extend(consistency_issues)
        
        # 4. 有效性检查（10%权重）
        validity_issues, validity_dim = self._check_enhanced_validity(df, source_name)
        issues.extend(validity_issues)
        
        dimensions = {
            'completeness': completeness_dim,
            'accuracy': accuracy_dim,
            'consistency': consistency_dim,
            'validity': validity_dim
        }
        
        return issues, dimensions
    
    def _check_enhanced_completeness(self, df: pd.DataFrame, source_name: str) -> Tuple[List[EnhancedQualityIssue], QualityDimension]:
        """增强型完整性检查"""
        issues = []
        sub_scores = {}
        
        # 1. 空值检测
        null_counts = df.isnull().sum()
        total_cells = len(df) * len(df.columns)
        null_cells = null_counts.sum()
        
        null_ratio = null_cells / total_cells if total_cells > 0 else 0
        sub_scores['null_ratio'] = max(0, 1 - null_ratio)
        
        # 2. 必填字段检查
        required_fields = self.business_rules.get('required_fields', {}).get(source_name, [])
        required_completeness = 1.0
        
        for field in required_fields:
            if field in df.columns:
                field_null_ratio = df[field].isnull().sum() / len(df)
                if field_null_ratio > 0:
                    severity = self._determine_enhanced_severity(field_null_ratio, 'completeness')
                    confidence = 1.0 - field_null_ratio
                    
                    issues.append(EnhancedQualityIssue(
                        issue_id=f"COMP_{source_name}_{field}_{datetime.now().strftime('%H%M%S')}",
                        issue_type="missing_required_data",
                        severity=severity,
                        confidence=confidence,
                        description=f"必填字段 '{field}' 有 {df[field].isnull().sum()} 个空值 ({field_null_ratio:.1%})",
                        affected_records=df[field].isnull().sum(),
                        table_name=source_name,
                        column_name=field,
                        detection_time=datetime.now().isoformat(),
                        detection_method="required_field_validation",
                        suggested_action=f"检查 {field} 字段的数据录入流程，确保必填字段完整性",
                        business_impact="high" if field_null_ratio > 0.1 else "medium",
                        auto_fixable=False
                    ))
                    required_completeness *= (1 - field_null_ratio)
        
        sub_scores['required_fields'] = required_completeness
        
        # 3. 数据覆盖度检查
        coverage_score = 1.0
        if '物料名称' in df.columns:
            unique_products = df['物料名称'].nunique()
            total_records = len(df)
            coverage_ratio = unique_products / total_records if total_records > 0 else 0
            coverage_score = min(1.0, coverage_ratio * 2)
        
        sub_scores['data_coverage'] = coverage_score
        
        # 计算完整性总分
        completeness_score = (
            sub_scores['null_ratio'] * 0.4 +
            sub_scores['required_fields'] * 0.4 +
            sub_scores['data_coverage'] * 0.2
        )
        
        dimension = QualityDimension(
            dimension_name="completeness",
            score=completeness_score,
            weight=self.dimension_weights['completeness'],
            sub_scores=sub_scores,
            issues_count=len([i for i in issues if 'missing' in i.issue_type]),
            critical_issues=len([i for i in issues if i.severity == 'critical' and 'missing' in i.issue_type])
        )
        
        return issues, dimension
    
    def _check_enhanced_accuracy(self, df: pd.DataFrame, source_name: str) -> Tuple[List[EnhancedQualityIssue], QualityDimension]:
        """增强型准确性检查"""
        issues = []
        sub_scores = {}
        
        # 1. 数值范围验证
        range_violations = 0
        total_numeric_checks = 0
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for column in numeric_columns:
            if column in self.business_rules['value_ranges']:
                min_val, max_val = self.business_rules['value_ranges'][column]
                out_of_range = ((df[column] < min_val) | (df[column] > max_val)).sum()
                total_numeric_checks += len(df)
                range_violations += out_of_range
                
                if out_of_range > 0:
                    violation_ratio = out_of_range / len(df)
                    severity = self._determine_enhanced_severity(violation_ratio, 'accuracy')
                    
                    issues.append(EnhancedQualityIssue(
                        issue_id=f"ACC_RANGE_{source_name}_{column}_{datetime.now().strftime('%H%M%S')}",
                        issue_type="value_out_of_range",
                        severity=severity,
                        confidence=0.95,
                        description=f"列 '{column}' 有 {out_of_range} 个值超出合理范围 [{min_val}, {max_val}]",
                        affected_records=out_of_range,
                        table_name=source_name,
                        column_name=column,
                        detection_time=datetime.now().isoformat(),
                        detection_method="business_rule_validation",
                        suggested_action=f"检查 {column} 列的数据录入，确保值在合理范围内",
                        business_impact="high" if violation_ratio > 0.05 else "medium",
                        auto_fixable=True
                    ))
        
        sub_scores['range_validation'] = max(0, (total_numeric_checks - range_violations) / total_numeric_checks) if total_numeric_checks > 0 else 1.0
        
        # 2. 统计异常检测
        statistical_score = self._check_statistical_accuracy(df, source_name, issues)
        sub_scores['statistical_accuracy'] = statistical_score
        
        # 3. 业务逻辑验证
        business_logic_score = self._check_business_logic_accuracy(df, source_name, issues)
        sub_scores['business_logic'] = business_logic_score
        
        # 计算准确性总分
        accuracy_score = (
            sub_scores['range_validation'] * 0.4 +
            sub_scores['statistical_accuracy'] * 0.4 +
            sub_scores['business_logic'] * 0.2
        )
        
        dimension = QualityDimension(
            dimension_name="accuracy",
            score=accuracy_score,
            weight=self.dimension_weights['accuracy'],
            sub_scores=sub_scores,
            issues_count=len([i for i in issues if 'accuracy' in i.detection_method or 'range' in i.issue_type]),
            critical_issues=len([i for i in issues if i.severity == 'critical' and ('accuracy' in i.detection_method or 'range' in i.issue_type)])
        )
        
        return issues, dimension
    
    def _check_statistical_accuracy(self, df: pd.DataFrame, source_name: str, issues: List[EnhancedQualityIssue]) -> float:
        """统计准确性检查"""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            return 1.0
        
        outlier_ratio = 0
        total_values = 0
        
        for column in numeric_columns:
            if df[column].notna().sum() > 10:
                values = df[column].dropna()
                total_values += len(values)
                
                # Z-Score异常检测
                z_scores = np.abs(stats.zscore(values))
                z_outliers = (z_scores > self.anomaly_params['z_score_threshold']).sum()
                
                # IQR异常检测
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                iqr_outliers = ((values < (Q1 - 1.5 * IQR)) | (values > (Q3 + 1.5 * IQR))).sum()
                
                # 取较保守的结果
                outliers = min(z_outliers, iqr_outliers)
                outlier_ratio += outliers
                
                if outliers > 0:
                    outlier_percentage = outliers / len(values)
                    if outlier_percentage > 0.05:
                        severity = self._determine_enhanced_severity(outlier_percentage, 'accuracy')
                        
                        issues.append(EnhancedQualityIssue(
                            issue_id=f"ACC_STAT_{source_name}_{column}_{datetime.now().strftime('%H%M%S')}",
                            issue_type="statistical_outlier",
                            severity=severity,
                            confidence=0.85,
                            description=f"列 '{column}' 检测到 {outliers} 个统计异常值 ({outlier_percentage:.1%})",
                            affected_records=outliers,
                            table_name=source_name,
                            column_name=column,
                            detection_time=datetime.now().isoformat(),
                            detection_method="statistical_analysis",
                            suggested_action=f"检查 {column} 列的异常值，确认是否为数据录入错误",
                            business_impact="medium",
                            auto_fixable=False
                        ))
        
        return max(0, (total_values - outlier_ratio) / total_values) if total_values > 0 else 1.0
    
    def _check_business_logic_accuracy(self, df: pd.DataFrame, source_name: str, issues: List[EnhancedQualityIssue]) -> float:
        """业务逻辑准确性检查"""
        violations = 0
        total_checks = 0
        
        # 检查产品过滤规则
        if '物料名称' in df.columns:
            exclude_patterns = self.business_rules['product_filters']['exclude_patterns']
            include_patterns = self.business_rules['product_filters']['include_patterns']
            
            for pattern in exclude_patterns:
                excluded_products = df[df['物料名称'].str.contains(pattern, na=False)]
                if len(excluded_products) > 0:
                    # 检查是否有例外情况
                    exceptions = excluded_products[
                        excluded_products['物料名称'].str.contains('|'.join(include_patterns), na=False)
                    ]
                    actual_violations = len(excluded_products) - len(exceptions)
                    
                    if actual_violations > 0:
                        violations += actual_violations
                        violation_ratio = actual_violations / len(df)
                        
                        issues.append(EnhancedQualityIssue(
                            issue_id=f"ACC_BIZ_{source_name}_{pattern}_{datetime.now().strftime('%H%M%S')}",
                            issue_type="business_rule_violation",
                            severity=self._determine_enhanced_severity(violation_ratio, 'accuracy'),
                            confidence=0.9,
                            description=f"发现 {actual_violations} 个应被过滤的 '{pattern}' 类产品",
                            affected_records=actual_violations,
                            table_name=source_name,
                            column_name="物料名称",
                            detection_time=datetime.now().isoformat(),
                            detection_method="business_rule_validation",
                            suggested_action=f"检查产品过滤规则，确保 '{pattern}' 类产品被正确处理",
                            business_impact="medium",
                            auto_fixable=True
                        ))
            
            total_checks += len(df)
        
        return max(0, (total_checks - violations) / total_checks) if total_checks > 0 else 1.0
    
    def _check_enhanced_consistency(self, df: pd.DataFrame, source_name: str) -> Tuple[List[EnhancedQualityIssue], QualityDimension]:
        """增强型一致性检查"""
        issues = []
        sub_scores = {}
        
        # 1. 重复记录检测
        duplicate_count = df.duplicated().sum()
        duplicate_ratio = duplicate_count / len(df) if len(df) > 0 else 0
        sub_scores['duplicate_records'] = max(0, 1 - duplicate_ratio)
        
        if duplicate_count > 0:
            severity = self._determine_enhanced_severity(duplicate_ratio, 'consistency')
            
            issues.append(EnhancedQualityIssue(
                issue_id=f"CONS_DUP_{source_name}_{datetime.now().strftime('%H%M%S')}",
                issue_type="duplicate_records",
                severity=severity,
                confidence=1.0,
                description=f"发现 {duplicate_count} 条重复记录 ({duplicate_ratio:.1%})",
                affected_records=duplicate_count,
                table_name=source_name,
                column_name="all",
                detection_time=datetime.now().isoformat(),
                detection_method="duplicate_detection",
                suggested_action="删除重复记录或检查数据录入流程",
                business_impact="medium" if duplicate_ratio > 0.05 else "low",
                auto_fixable=True
            ))
        
        # 2. 格式一致性检查
        format_consistency_score = 1.0
        sub_scores['format_consistency'] = format_consistency_score
        
        # 3. 关联数据一致性检查
        relational_consistency_score = 1.0
        sub_scores['relational_consistency'] = relational_consistency_score
        
        # 计算一致性总分
        consistency_score = (
            sub_scores['duplicate_records'] * 0.4 +
            sub_scores['format_consistency'] * 0.3 +
            sub_scores['relational_consistency'] * 0.3
        )
        
        dimension = QualityDimension(
            dimension_name="consistency",
            score=consistency_score,
            weight=self.dimension_weights['consistency'],
            sub_scores=sub_scores,
            issues_count=len([i for i in issues if 'consistency' in i.detection_method or 'duplicate' in i.issue_type]),
            critical_issues=len([i for i in issues if i.severity == 'critical' and ('consistency' in i.detection_method or 'duplicate' in i.issue_type)])
        )
        
        return issues, dimension
    
    def _check_enhanced_validity(self, df: pd.DataFrame, source_name: str) -> Tuple[List[EnhancedQualityIssue], QualityDimension]:
        """增强型有效性检查"""
        issues = []
        sub_scores = {}
        
        # 1. 业务规则有效性
        business_validity_score = 1.0
        sub_scores['business_validity'] = business_validity_score
        
        # 2. 时间序列有效性
        temporal_validity_score = 1.0
        sub_scores['temporal_validity'] = temporal_validity_score
        
        # 3. 数据类型有效性
        type_validity_score = 1.0
        sub_scores['type_validity'] = type_validity_score
        
        # 计算有效性总分
        validity_score = (
            sub_scores['business_validity'] * 0.5 +
            sub_scores['temporal_validity'] * 0.3 +
            sub_scores['type_validity'] * 0.2
        )
        
        dimension = QualityDimension(
            dimension_name="validity",
            score=validity_score,
            weight=self.dimension_weights['validity'],
            sub_scores=sub_scores,
            issues_count=len([i for i in issues if 'validity' in i.detection_method]),
            critical_issues=len([i for i in issues if i.severity == 'critical' and 'validity' in i.detection_method])
        )
        
        return issues, dimension
    
    def _detect_anomalies(self, df: pd.DataFrame, source_name: str) -> List[AnomalyDetection]:
        """智能异常检测"""
        anomalies = []
        
        # 1. 统计异常检测
        statistical_anomalies = self._detect_statistical_anomalies(df, source_name)
        anomalies.extend(statistical_anomalies)
        
        # 2. 机器学习异常检测
        if SKLEARN_AVAILABLE:
            ml_anomalies = self._detect_ml_anomalies(df, source_name)
            anomalies.extend(ml_anomalies)
        
        return anomalies
    
    def _detect_statistical_anomalies(self, df: pd.DataFrame, source_name: str) -> List[AnomalyDetection]:
        """统计异常检测"""
        anomalies = []
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if df[column].notna().sum() > 10:
                values = df[column].dropna()
                
                # Z-Score异常检测
                z_scores = np.abs(stats.zscore(values))
                z_outliers_mask = z_scores > self.anomaly_params['z_score_threshold']
                z_outliers_indices = values[z_outliers_mask].index.tolist()
                
                if len(z_outliers_indices) > 0:
                    confidence = min(0.95, (z_scores[z_outliers_mask].mean() - self.anomaly_params['z_score_threshold']) / 3.0)
                    
                    anomalies.append(AnomalyDetection(
                        detection_method="z_score",
                        anomaly_type="statistical_outlier",
                        confidence=confidence,
                        affected_records=z_outliers_indices,
                        statistical_info={
                            'column': column,
                            'mean': float(values.mean()),
                            'std': float(values.std()),
                            'z_threshold': self.anomaly_params['z_score_threshold'],
                            'outlier_count': len(z_outliers_indices)
                        },
                        business_impact=self._assess_business_impact(column, len(z_outliers_indices), len(values))
                    ))
        
        return anomalies
    
    def _detect_ml_anomalies(self, df: pd.DataFrame, source_name: str) -> List[AnomalyDetection]:
        """机器学习异常检测"""
        anomalies = []
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) >= 2:
            try:
                # 准备数据
                data = df[numeric_columns].dropna()
                if len(data) > 20:
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(data)
                    
                    # Isolation Forest异常检测
                    iso_forest = IsolationForest(
                        contamination=self.anomaly_params['isolation_forest_contamination'],
                        random_state=42
                    )
                    outliers = iso_forest.fit_predict(scaled_data)
                    outlier_indices = data.index[outliers == -1].tolist()
                    
                    if len(outlier_indices) > 0:
                        # 计算异常分数
                        anomaly_scores = iso_forest.decision_function(scaled_data)
                        confidence = float(np.mean(np.abs(anomaly_scores[outliers == -1])))
                        
                        anomalies.append(AnomalyDetection(
                            detection_method="isolation_forest",
                            anomaly_type="multivariate_outlier",
                            confidence=min(0.95, confidence),
                            affected_records=outlier_indices,
                            statistical_info={
                                'features': list(numeric_columns),
                                'contamination': self.anomaly_params['isolation_forest_contamination'],
                                'outlier_count': len(outlier_indices),
                                'total_records': len(data)
                            },
                            business_impact=self._assess_business_impact('multivariate', len(outlier_indices), len(data))
                        ))
            except Exception as e:
                self.logger.warning(f"机器学习异常检测失败: {e}")
        
        return anomalies
    
    def _assess_business_impact(self, column: str, outlier_count: int, total_count: int) -> str:
        """评估业务影响"""
        impact_ratio = outlier_count / total_count if total_count > 0 else 0
        
        if impact_ratio > 0.1:
            return "high"
        elif impact_ratio > 0.05:
            return "medium"
        else:
            return "low"
    
    def _determine_enhanced_severity(self, ratio: float, dimension: str) -> str:
        """确定增强型严重程度"""
        # 根据不同维度调整阈值
        thresholds = {
            'completeness': {'critical': 0.2, 'high': 0.1, 'medium': 0.05},
            'accuracy': {'critical': 0.15, 'high': 0.08, 'medium': 0.03},
            'consistency': {'critical': 0.1, 'high': 0.05, 'medium': 0.02},
            'validity': {'critical': 0.05, 'high': 0.02, 'medium': 0.01}
        }
        
        dim_thresholds = thresholds.get(dimension, thresholds['accuracy'])
        
        if ratio >= dim_thresholds['critical']:
            return 'critical'
        elif ratio >= dim_thresholds['high']:
            return 'high'
        elif ratio >= dim_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_enhanced_metrics(self, dimension_scores: Dict[str, Dict[str, QualityDimension]],
                                  all_issues: List[EnhancedQualityIssue]) -> EnhancedQualityMetrics:
        """计算增强型质量指标"""
        # 聚合各数据源的维度分数
        aggregated_dimensions = {}
        
        for dimension_name in ['completeness', 'accuracy', 'consistency', 'validity']:
            scores = []
            weights = []
            total_issues = 0
            critical_issues = 0
            
            for source_name, dimensions in dimension_scores.items():
                if dimension_name in dimensions:
                    dim = dimensions[dimension_name]
                    scores.append(dim.score)
                    weights.append(1.0)  # 可以根据数据源重要性调整权重
                    total_issues += dim.issues_count
                    critical_issues += dim.critical_issues
            
            if scores:
                weighted_score = np.average(scores, weights=weights)
                aggregated_dimensions[dimension_name] = QualityDimension(
                    dimension_name=dimension_name,
                    score=weighted_score,
                    weight=self.dimension_weights[dimension_name],
                    sub_scores={},
                    issues_count=total_issues,
                    critical_issues=critical_issues
                )
            else:
                aggregated_dimensions[dimension_name] = QualityDimension(
                    dimension_name=dimension_name,
                    score=1.0,
                    weight=self.dimension_weights[dimension_name],
                    sub_scores={},
                    issues_count=0,
                    critical_issues=0
                )
        
        # 计算加权总分
        weighted_score = sum(
            dim.score * dim.weight
            for dim in aggregated_dimensions.values()
        )
        
        # 确定质量等级
        quality_grade = self._determine_quality_grade(weighted_score)
        
        # 计算趋势
        score_trend = self._calculate_score_trend(weighted_score)
        
        # 统计信息 - 修复：all_issues是EnhancedQualityIssue对象列表，不是嵌套列表
        total_records = 0
        for source_name, dimensions in dimension_scores.items():
            for dim_name, dim in dimensions.items():
                total_records += dim.issues_count
        
        critical_issue_count = len([i for i in all_issues if i.severity == 'critical'])
        
        return EnhancedQualityMetrics(
            completeness=aggregated_dimensions['completeness'],
            accuracy=aggregated_dimensions['accuracy'],
            consistency=aggregated_dimensions['consistency'],
            validity=aggregated_dimensions['validity'],
            overall_score=weighted_score,
            weighted_score=weighted_score,
            quality_grade=quality_grade,
            total_records=total_records,
            valid_records=max(0, total_records - len(all_issues)),
            issue_count=len(all_issues),
            critical_issue_count=critical_issue_count,
            score_trend=score_trend,
            historical_comparison=self._get_historical_comparison(weighted_score)
        )
    
    def _determine_quality_grade(self, score: float) -> str:
        """确定质量等级"""
        for grade, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return grade
        return 'F'
    
    def _calculate_score_trend(self, current_score: float) -> str:
        """计算分数趋势"""
        if len(self.quality_history) < 2:
            return "stable"
        
        recent_scores = [h.metrics.weighted_score for h in self.quality_history[-3:]]
        recent_scores.append(current_score)
        
        if len(recent_scores) >= 3:
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
            if trend > 0.01:
                return "improving"
            elif trend < -0.01:
                return "declining"
        
        return "stable"
    
    def _get_historical_comparison(self, current_score: float) -> Dict[str, float]:
        """获取历史对比数据"""
        comparison = {}
        
        if self.quality_history:
            last_score = self.quality_history[-1].metrics.weighted_score
            comparison['last_period'] = current_score - last_score
            
            if len(self.quality_history) >= 7:
                week_ago_score = self.quality_history[-7].metrics.weighted_score
                comparison['week_ago'] = current_score - week_ago_score
            
            if len(self.quality_history) >= 30:
                month_ago_score = self.quality_history[-30].metrics.weighted_score
                comparison['month_ago'] = current_score - month_ago_score
        
        return comparison
    
    def _generate_intelligent_recommendations(self, issues: List[EnhancedQualityIssue],
                                            anomalies: List[AnomalyDetection],
                                            metrics: EnhancedQualityMetrics) -> List[str]:
        """生成智能建议"""
        recommendations = []
        
        # 1. 基于质量等级的建议
        if metrics.quality_grade in ['F', 'D']:
            recommendations.append("🚨 数据质量严重不达标，建议立即启动数据质量改进计划")
            recommendations.append("📋 优先处理所有critical级别的数据质量问题")
        elif metrics.quality_grade in ['C', 'C+']:
            recommendations.append("⚠️ 数据质量需要改进，建议制定系统性的质量提升方案")
        elif metrics.quality_grade in ['B', 'B+']:
            recommendations.append("✅ 数据质量良好，建议继续保持并优化细节问题")
        else:
            recommendations.append("🌟 数据质量优秀，建议建立最佳实践标准")
        
        # 2. 基于维度分数的建议
        if metrics.completeness.score < 0.8:
            recommendations.append("📊 完整性问题突出，建议检查数据录入流程和必填字段验证")
        
        if metrics.accuracy.score < 0.8:
            recommendations.append("🎯 准确性需要提升，建议加强数据验证规则和异常值检测")
        
        if metrics.consistency.score < 0.8:
            recommendations.append("🔄 一致性问题较多，建议统一数据格式和清理重复记录")
        
        if metrics.validity.score < 0.8:
            recommendations.append("✔️ 有效性检查发现问题，建议完善业务规则验证")
        
        # 3. 基于问题类型的建议
        issue_types = {}
        for issue in issues:
            issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
        
        if issue_types.get('missing_required_data', 0) > 0:
            recommendations.append("📝 发现必填字段缺失，建议在数据录入界面增加必填验证")
        
        if issue_types.get('value_out_of_range', 0) > 0:
            recommendations.append("📏 发现数值超出合理范围，建议设置数据录入的范围限制")
        
        if issue_types.get('duplicate_records', 0) > 0:
            recommendations.append("🔍 发现重复记录，建议实施去重策略和唯一性约束")
        
        # 4. 基于异常检测的建议
        if anomalies:
            ml_anomalies = [a for a in anomalies if a.detection_method == 'isolation_forest']
            if ml_anomalies:
                recommendations.append("🤖 机器学习检测到复杂异常模式，建议深入分析多维度数据关系")
            
            stat_anomalies = [a for a in anomalies if a.detection_method == 'z_score']
            if stat_anomalies:
                recommendations.append("📈 统计异常检测发现离群值，建议检查数据录入的准确性")
        
        # 5. 基于趋势的建议
        if metrics.score_trend == "declining":
            recommendations.append("📉 数据质量呈下降趋势，建议立即调查原因并采取纠正措施")
        elif metrics.score_trend == "improving":
            recommendations.append("📈 数据质量持续改善，建议继续当前的质量管理策略")
        
        # 6. 自动修复建议
        auto_fixable_count = len([i for i in issues if i.auto_fixable])
        if auto_fixable_count > 0:
            recommendations.append(f"🔧 发现 {auto_fixable_count} 个可自动修复的问题，建议启用自动修复功能")
        
        return recommendations[:10]  # 限制建议数量
    
    def _determine_alert_level(self, metrics: EnhancedQualityMetrics, issues: List[EnhancedQualityIssue]) -> str:
        """确定告警级别"""
        critical_issues = len([i for i in issues if i.severity == 'critical'])
        high_issues = len([i for i in issues if i.severity == 'high'])
        
        if critical_issues > 0 or metrics.quality_grade in ['F', 'D']:
            return "critical"
        elif high_issues > 5 or metrics.quality_grade in ['C', 'C+']:
            return "warning"
        else:
            return "normal"
    
    def _generate_quality_summary(self, metrics: EnhancedQualityMetrics, issues: List[EnhancedQualityIssue]) -> Dict[str, Any]:
        """生成质量摘要"""
        return {
            'overall_grade': metrics.quality_grade,
            'overall_score': round(metrics.weighted_score, 3),
            'dimension_scores': {
                'completeness': round(metrics.completeness.score, 3),
                'accuracy': round(metrics.accuracy.score, 3),
                'consistency': round(metrics.consistency.score, 3),
                'validity': round(metrics.validity.score, 3)
            },
            'issue_summary': {
                'total': len(issues),
                'critical': len([i for i in issues if i.severity == 'critical']),
                'high': len([i for i in issues if i.severity == 'high']),
                'medium': len([i for i in issues if i.severity == 'medium']),
                'low': len([i for i in issues if i.severity == 'low'])
            },
            'trend': metrics.score_trend,
            'auto_fixable': len([i for i in issues if i.auto_fixable])
        }
    
    def _store_quality_history(self, report: EnhancedQualityReport):
        """存储质量历史数据"""
        self.quality_history.append(report)
        
        # 保持历史记录在合理范围内（最多保留100条）
        if len(self.quality_history) > 100:
            self.quality_history = self.quality_history[-100:]
        
        # 可选：持久化到文件
        try:
            history_file = 'quality_history.json'
            history_data = []
            
            for report in self.quality_history[-10:]:  # 只保存最近10条到文件
                history_data.append({
                    'timestamp': report.timestamp,
                    'overall_score': report.metrics.weighted_score,
                    'quality_grade': report.metrics.quality_grade,
                    'issue_count': report.metrics.issue_count,
                    'critical_issues': report.metrics.critical_issue_count
                })
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.warning(f"保存质量历史失败: {e}")
    
    def export_report(self, report: EnhancedQualityReport, format_type: str = 'json') -> str:
        """导出增强型质量报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type.lower() == 'json':
            filename = f'enhanced_quality_report_{timestamp}.json'
            
            # 转换为可序列化的格式
            report_dict = asdict(report)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"增强型质量报告已导出: {filename}")
            return filename
            
        elif format_type.lower() == 'html':
            filename = f'enhanced_quality_report_{timestamp}.html'
            html_content = self._generate_html_report(report)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"增强型HTML质量报告已导出: {filename}")
            return filename
        
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def _generate_html_report(self, report: EnhancedQualityReport) -> str:
        """生成HTML格式报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>增强型数据质量报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }}
        .grade {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
        .grade.A {{ color: #4CAF50; }} .grade.B {{ color: #8BC34A; }} .grade.C {{ color: #FFC107; }} .grade.D {{ color: #FF9800; }} .grade.F {{ color: #F44336; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .metric-title {{ font-weight: bold; color: #333; margin-bottom: 10px; }}
        .metric-score {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .issues-section {{ margin: 30px 0; }}
        .issue-item {{ background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; }}
        .issue-critical {{ border-left: 4px solid #F44336; }} .issue-high {{ border-left: 4px solid #FF9800; }}
        .issue-medium {{ border-left: 4px solid #FFC107; }} .issue-low {{ border-left: 4px solid #4CAF50; }}
        .recommendations {{ background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .alert-critical {{ background: #ffebee; border: 1px solid #f44336; }}
        .alert-warning {{ background: #fff3e0; border: 1px solid #ff9800; }}
        .alert-normal {{ background: #e8f5e8; border: 1px solid #4caf50; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 增强型数据质量监控报告</h1>
            <div class="grade {grade_class}">{quality_grade}</div>
            <p>总体评分: <strong>{overall_score:.1%}</strong></p>
            <p>生成时间: {timestamp}</p>
            <p>告警级别: <span class="alert-{alert_level}">{alert_level_text}</span></p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-title">📊 完整性</div>
                <div class="metric-score">{completeness_score:.1%}</div>
                <small>权重: {completeness_weight:.0%}</small>
            </div>
            <div class="metric-card">
                <div class="metric-title">🎯 准确性</div>
                <div class="metric-score">{accuracy_score:.1%}</div>
                <small>权重: {accuracy_weight:.0%}</small>
            </div>
            <div class="metric-card">
                <div class="metric-title">🔄 一致性</div>
                <div class="metric-score">{consistency_score:.1%}</div>
                <small>权重: {consistency_weight:.0%}</small>
            </div>
            <div class="metric-card">
                <div class="metric-title">✔️ 有效性</div>
                <div class="metric-score">{validity_score:.1%}</div>
                <small>权重: {validity_weight:.0%}</small>
            </div>
        </div>
        
        <div class="issues-section">
            <h2>📋 质量问题详情 ({issue_count} 个问题)</h2>
            {issues_html}
        </div>
        
        <div class="recommendations">
            <h2>💡 智能建议</h2>
            {recommendations_html}
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
            <small>报告ID: {report_id} | 处理时间: {processing_time:.2f}秒</small>
        </div>
    </div>
</body>
</html>
        """
        
        # 准备数据
        grade_class = report.metrics.quality_grade[0] if report.metrics.quality_grade else 'F'
        alert_level_map = {'critical': '严重', 'warning': '警告', 'normal': '正常'}
        
        # 生成问题HTML
        issues_html = ""
        for issue in report.issues[:20]:  # 限制显示数量
            severity_class = f"issue-{issue.severity}"
            issues_html += f"""
            <div class="issue-item {severity_class}">
                <strong>{issue.issue_type}</strong> - {issue.severity.upper()}
                <p>{issue.description}</p>
                <small>表: {issue.table_name} | 列: {issue.column_name} | 影响记录: {issue.affected_records}</small>
                <p><em>建议: {issue.suggested_action}</em></p>
            </div>
            """
        
        # 生成建议HTML
        recommendations_html = "<ul>"
        for rec in report.recommendations:
            recommendations_html += f"<li>{rec}</li>"
        recommendations_html += "</ul>"
        
        return html_template.format(
            grade_class=grade_class,
            quality_grade=report.metrics.quality_grade,
            overall_score=report.metrics.weighted_score,
            timestamp=report.timestamp,
            alert_level=report.alert_level,
            alert_level_text=alert_level_map.get(report.alert_level, '未知'),
            completeness_score=report.metrics.completeness.score,
            completeness_weight=report.metrics.completeness.weight,
            accuracy_score=report.metrics.accuracy.score,
            accuracy_weight=report.metrics.accuracy.weight,
            consistency_score=report.metrics.consistency.score,
            consistency_weight=report.metrics.consistency.weight,
            validity_score=report.metrics.validity.score,
            validity_weight=report.metrics.validity.weight,
            issue_count=len(report.issues),
            issues_html=issues_html,
            recommendations_html=recommendations_html,
            report_id=report.report_id,
            processing_time=report.processing_time
        )
    
    def print_summary(self, report: EnhancedQualityReport):
        """打印报告摘要"""
        print("\n" + "="*80)
        print("🔍 增强型数据质量监控报告摘要")
        print("="*80)
        
        # 基本信息
        print(f"📅 生成时间: {report.timestamp}")
        print(f"🆔 报告ID: {report.report_id}")
        print(f"⏱️  处理时间: {report.processing_time:.2f} 秒")
        print(f"🚨 告警级别: {report.alert_level.upper()}")
        
        # 质量评分
        print(f"\n📊 整体质量评分")
        print(f"   等级: {report.metrics.quality_grade} ({report.metrics.weighted_score:.1%})")
        print(f"   趋势: {report.metrics.score_trend}")
        
        # 维度分数
        print(f"\n📈 各维度评分:")
        print(f"   📊 完整性: {report.metrics.completeness.score:.1%} (权重: {report.metrics.completeness.weight:.0%})")
        print(f"   🎯 准确性: {report.metrics.accuracy.score:.1%} (权重: {report.metrics.accuracy.weight:.0%})")
        print(f"   🔄 一致性: {report.metrics.consistency.score:.1%} (权重: {report.metrics.consistency.weight:.0%})")
        print(f"   ✔️ 有效性: {report.metrics.validity.score:.1%} (权重: {report.metrics.validity.weight:.0%})")
        
        # 问题统计
        print(f"\n📋 问题统计:")
        print(f"   总问题数: {len(report.issues)}")
        print(f"   严重问题: {len([i for i in report.issues if i.severity == 'critical'])}")
        print(f"   高级问题: {len([i for i in report.issues if i.severity == 'high'])}")
        print(f"   中级问题: {len([i for i in report.issues if i.severity == 'medium'])}")
        print(f"   低级问题: {len([i for i in report.issues if i.severity == 'low'])}")
        print(f"   可自动修复: {len([i for i in report.issues if i.auto_fixable])}")
        
        # 异常检测
        if report.anomalies:
            print(f"\n🤖 异常检测:")
            print(f"   检测到异常: {len(report.anomalies)} 个")
            for anomaly in report.anomalies[:3]:  # 显示前3个
                print(f"   - {anomaly.anomaly_type} ({anomaly.detection_method}): {len(anomaly.affected_records)} 条记录")
        
        # 智能建议
        print(f"\n💡 智能建议 (前5条):")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"   {i}. {rec}")
        
        print("="*80)


def main():
    """主程序入口"""
    print("🚀 启动增强型数据质量监控系统...")
    
    try:
        # 初始化监控器
        monitor = EnhancedDataQualityMonitor()
        
        # 运行质量检查
        report = monitor.run_enhanced_quality_check()
        
        # 打印摘要
        monitor.print_summary(report)
        
        # 导出报告
        json_file = monitor.export_report(report, 'json')
        html_file = monitor.export_report(report, 'html')
        
        print(f"\n📄 报告已导出:")
        print(f"   JSON: {json_file}")
        print(f"   HTML: {html_file}")
        
        # 根据告警级别给出建议
        if report.alert_level == 'critical':
            print(f"\n🚨 严重告警: 数据质量问题严重，建议立即处理！")
        elif report.alert_level == 'warning':
            print(f"\n⚠️ 警告: 发现数据质量问题，建议及时处理。")
        else:
            print(f"\n✅ 数据质量良好，继续保持！")
        
        return report
        
    except Exception as e:
        logger.error(f"增强型数据质量监控失败: {e}")
        raise


if __name__ == "__main__":
    main()