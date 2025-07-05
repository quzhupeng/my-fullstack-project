#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化和测试工具
版本: 1.0
作者: Kilo Code
日期: 2025-01-05

功能:
1. 性能基准测试
2. 内存使用监控
3. 处理时间分析
4. 优化建议生成
"""

import pandas as pd
import numpy as np
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
import json
import os
import gc
from functools import wraps
import warnings
warnings.filterwarnings('ignore')

# 导入优化的模块
try:
    from optimized_data_importer import OptimizedDataImporter
    from optimized_production_sales_ratio import ProductionSalesRatioAnalyzer
    from data_quality_monitor import DataQualityMonitor
except ImportError as e:
    print(f"警告: 无法导入优化模块 - {e}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_optimizer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    operation_name: str
    execution_time: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_usage: float
    records_processed: int
    throughput: float  # 记录/秒
    timestamp: str

@dataclass
class OptimizationReport:
    """优化报告数据类"""
    report_id: str
    timestamp: str
    system_info: Dict[str, Any]
    performance_metrics: List[PerformanceMetrics]
    bottlenecks: List[str]
    recommendations: List[str]
    overall_score: float

def performance_monitor(func: Callable) -> Callable:
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 记录开始状态
        start_time = time.time()
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent()
        
        # 执行函数
        result = func(*args, **kwargs)
        
        # 记录结束状态
        end_time = time.time()
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        cpu_after = process.cpu_percent()
        
        # 计算指标
        execution_time = end_time - start_time
        memory_peak = max(memory_before, memory_after)
        cpu_usage = (cpu_before + cpu_after) / 2
        
        # 记录性能数据
        metrics = PerformanceMetrics(
            operation_name=func.__name__,
            execution_time=execution_time,
            memory_before=memory_before,
            memory_after=memory_after,
            memory_peak=memory_peak,
            cpu_usage=cpu_usage,
            records_processed=0,  # 需要在函数中设置
            throughput=0,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"{func.__name__} 执行完成 - 耗时: {execution_time:.2f}s, 内存: {memory_peak:.1f}MB")
        
        return result, metrics
    
    return wrapper

class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, excel_folder: str = './Excel文件夹/'):
        self.excel_folder = excel_folder
        self.logger = logging.getLogger(f"{__name__}.PerformanceOptimizer")
        self.metrics_history = []
        
        # 性能阈值配置
        self.performance_thresholds = {
            'execution_time': {
                'excellent': 5.0,    # 秒
                'good': 15.0,
                'acceptable': 30.0,
                'poor': 60.0
            },
            'memory_usage': {
                'excellent': 100,    # MB
                'good': 250,
                'acceptable': 500,
                'poor': 1000
            },
            'throughput': {
                'excellent': 1000,   # 记录/秒
                'good': 500,
                'acceptable': 100,
                'poor': 50
            }
        }
    
    def run_performance_test(self) -> OptimizationReport:
        """运行完整的性能测试"""
        self.logger.info("开始性能测试...")
        start_time = datetime.now()
        
        try:
            # 收集系统信息
            system_info = self._collect_system_info()
            
            # 运行各项性能测试
            all_metrics = []
            
            # 1. 数据导入性能测试
            import_metrics = self._test_data_import_performance()
            all_metrics.extend(import_metrics)
            
            # 2. 产销率计算性能测试
            ratio_metrics = self._test_ratio_calculation_performance()
            all_metrics.extend(ratio_metrics)
            
            # 3. 数据质量检查性能测试
            quality_metrics = self._test_quality_check_performance()
            all_metrics.extend(quality_metrics)
            
            # 4. 内存优化测试
            memory_metrics = self._test_memory_optimization()
            all_metrics.extend(memory_metrics)
            
            # 分析瓶颈
            bottlenecks = self._identify_bottlenecks(all_metrics)
            
            # 生成优化建议
            recommendations = self._generate_optimization_recommendations(all_metrics, bottlenecks)
            
            # 计算整体性能分数
            overall_score = self._calculate_overall_score(all_metrics)
            
            # 创建报告
            report = OptimizationReport(
                report_id=f"PERF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=start_time.isoformat(),
                system_info=system_info,
                performance_metrics=all_metrics,
                bottlenecks=bottlenecks,
                recommendations=recommendations,
                overall_score=overall_score
            )
            
            self.logger.info("性能测试完成")
            return report
            
        except Exception as e:
            self.logger.error(f"性能测试失败: {e}")
            raise
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            'memory_available': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
            'disk_usage': psutil.disk_usage('.').percent,
            'python_version': f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}",
            'pandas_version': pd.__version__,
            'numpy_version': np.__version__
        }
    
    def _test_data_import_performance(self) -> List[PerformanceMetrics]:
        """测试数据导入性能"""
        self.logger.info("测试数据导入性能...")
        metrics = []
        
        try:
            # 测试原始导入方法
            original_metrics = self._benchmark_original_import()
            if original_metrics:
                metrics.append(original_metrics)
            
            # 测试优化导入方法
            optimized_metrics = self._benchmark_optimized_import()
            if optimized_metrics:
                metrics.append(optimized_metrics)
            
        except Exception as e:
            self.logger.error(f"数据导入性能测试失败: {e}")
        
        return metrics
    
    def _benchmark_original_import(self) -> Optional[PerformanceMetrics]:
        """基准测试原始导入方法"""
        try:
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 模拟原始导入逻辑
            total_records = 0
            for filename in ['销售发票执行查询.xlsx', '收发存汇总表查询.xlsx']:
                filepath = os.path.join(self.excel_folder, filename)
                if os.path.exists(filepath):
                    df = pd.read_excel(filepath)
                    total_records += len(df)
                    # 简单的数据处理
                    df = df.dropna()
                    df = df[df.select_dtypes(include=[np.number]).columns[0] > 0] if len(df.select_dtypes(include=[np.number]).columns) > 0 else df
            
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            return PerformanceMetrics(
                operation_name="original_data_import",
                execution_time=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=max(memory_before, memory_after),
                cpu_usage=process.cpu_percent(),
                records_processed=total_records,
                throughput=total_records / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"原始导入基准测试失败: {e}")
            return None
    
    def _benchmark_optimized_import(self) -> Optional[PerformanceMetrics]:
        """基准测试优化导入方法"""
        try:
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 使用优化的导入器
            importer = OptimizedDataImporter(self.excel_folder)
            result = importer.process_all_data()
            
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            total_records = sum(len(df) for df in result.processed_data.values() if df is not None)
            
            return PerformanceMetrics(
                operation_name="optimized_data_import",
                execution_time=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=max(memory_before, memory_after),
                cpu_usage=process.cpu_percent(),
                records_processed=total_records,
                throughput=total_records / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"优化导入基准测试失败: {e}")
            return None
    
    def _test_ratio_calculation_performance(self) -> List[PerformanceMetrics]:
        """测试产销率计算性能"""
        self.logger.info("测试产销率计算性能...")
        metrics = []
        
        try:
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 使用优化的产销率分析器
            analyzer = ProductionSalesRatioAnalyzer(self.excel_folder)
            sales_data, inventory_data = analyzer.load_and_validate_data()
            report = analyzer.calculate_production_sales_ratio(sales_data, inventory_data)
            
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            total_records = len(sales_data) + len(inventory_data)
            
            metrics.append(PerformanceMetrics(
                operation_name="ratio_calculation",
                execution_time=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=max(memory_before, memory_after),
                cpu_usage=process.cpu_percent(),
                records_processed=total_records,
                throughput=total_records / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.error(f"产销率计算性能测试失败: {e}")
        
        return metrics
    
    def _test_quality_check_performance(self) -> List[PerformanceMetrics]:
        """测试数据质量检查性能"""
        self.logger.info("测试数据质量检查性能...")
        metrics = []
        
        try:
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 使用数据质量监控器
            monitor = DataQualityMonitor(self.excel_folder)
            report = monitor.run_quality_check()
            
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            metrics.append(PerformanceMetrics(
                operation_name="quality_check",
                execution_time=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=max(memory_before, memory_after),
                cpu_usage=process.cpu_percent(),
                records_processed=report.metrics.total_records,
                throughput=report.metrics.total_records / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.error(f"数据质量检查性能测试失败: {e}")
        
        return metrics
    
    def _test_memory_optimization(self) -> List[PerformanceMetrics]:
        """测试内存优化"""
        self.logger.info("测试内存优化...")
        metrics = []
        
        try:
            # 测试大数据集处理
            start_time = time.time()
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 创建大数据集进行测试
            large_df = pd.DataFrame({
                'col1': np.random.randn(100000),
                'col2': np.random.randn(100000),
                'col3': np.random.choice(['A', 'B', 'C'], 100000),
                'col4': pd.date_range('2023-01-01', periods=100000, freq='H')
            })
            
            # 执行一些内存密集型操作
            result = large_df.groupby('col3').agg({
                'col1': ['mean', 'std', 'min', 'max'],
                'col2': ['sum', 'count']
            })
            
            # 强制垃圾回收
            del large_df
            gc.collect()
            
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            metrics.append(PerformanceMetrics(
                operation_name="memory_optimization_test",
                execution_time=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=max(memory_before, memory_after),
                cpu_usage=process.cpu_percent(),
                records_processed=100000,
                throughput=100000 / (end_time - start_time) if (end_time - start_time) > 0 else 0,
                timestamp=datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.error(f"内存优化测试失败: {e}")
        
        return metrics
    
    def _identify_bottlenecks(self, metrics: List[PerformanceMetrics]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []
        
        for metric in metrics:
            # 检查执行时间瓶颈
            if metric.execution_time > self.performance_thresholds['execution_time']['poor']:
                bottlenecks.append(f"{metric.operation_name}: 执行时间过长 ({metric.execution_time:.2f}s)")
            
            # 检查内存使用瓶颈
            if metric.memory_peak > self.performance_thresholds['memory_usage']['poor']:
                bottlenecks.append(f"{metric.operation_name}: 内存使用过高 ({metric.memory_peak:.1f}MB)")
            
            # 检查吞吐量瓶颈
            if metric.throughput < self.performance_thresholds['throughput']['poor']:
                bottlenecks.append(f"{metric.operation_name}: 处理速度过慢 ({metric.throughput:.1f} 记录/秒)")
        
        return bottlenecks
    
    def _generate_optimization_recommendations(self, metrics: List[PerformanceMetrics], 
                                             bottlenecks: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于瓶颈的建议
        if any("执行时间过长" in b for b in bottlenecks):
            recommendations.append("考虑使用并行处理或分块处理来减少执行时间")
            recommendations.append("优化算法复杂度，减少不必要的计算")
        
        if any("内存使用过高" in b for b in bottlenecks):
            recommendations.append("使用分块读取大文件，避免一次性加载所有数据")
            recommendations.append("及时释放不需要的变量，使用垃圾回收")
            recommendations.append("考虑使用更高效的数据类型（如category类型）")
        
        if any("处理速度过慢" in b for b in bottlenecks):
            recommendations.append("使用向量化操作替代循环")
            recommendations.append("优化数据库查询，使用批量操作")
            recommendations.append("考虑使用更快的文件格式（如Parquet）")
        
        # 通用优化建议
        avg_memory = np.mean([m.memory_peak for m in metrics])
        if avg_memory > 200:
            recommendations.append("整体内存使用较高，建议优化数据结构")
        
        avg_time = np.mean([m.execution_time for m in metrics])
        if avg_time > 10:
            recommendations.append("整体处理时间较长，建议进行性能调优")
        
        # 如果没有明显问题
        if not bottlenecks:
            recommendations.append("性能表现良好，可以考虑进一步的微调优化")
        
        return recommendations
    
    def _calculate_overall_score(self, metrics: List[PerformanceMetrics]) -> float:
        """计算整体性能分数"""
        if not metrics:
            return 0.0
        
        scores = []
        
        for metric in metrics:
            # 时间分数 (越短越好)
            time_score = 1.0
            if metric.execution_time > self.performance_thresholds['execution_time']['excellent']:
                time_score = max(0, 1 - (metric.execution_time - self.performance_thresholds['execution_time']['excellent']) / 60)
            
            # 内存分数 (越少越好)
            memory_score = 1.0
            if metric.memory_peak > self.performance_thresholds['memory_usage']['excellent']:
                memory_score = max(0, 1 - (metric.memory_peak - self.performance_thresholds['memory_usage']['excellent']) / 1000)
            
            # 吞吐量分数 (越高越好)
            throughput_score = min(1.0, metric.throughput / self.performance_thresholds['throughput']['excellent'])
            
            # 综合分数
            overall_metric_score = (time_score + memory_score + throughput_score) / 3
            scores.append(overall_metric_score)
        
        return round(np.mean(scores), 3)
    
    def export_report(self, report: OptimizationReport, format: str = 'json') -> str:
        """导出优化报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == 'json':
            filename = f"performance_report_{timestamp}.json"
            
            # 转换为可序列化的字典
            report_dict = {
                'report_id': report.report_id,
                'timestamp': report.timestamp,
                'system_info': report.system_info,
                'performance_metrics': [
                    {
                        'operation_name': m.operation_name,
                        'execution_time': m.execution_time,
                        'memory_before': m.memory_before,
                        'memory_after': m.memory_after,
                        'memory_peak': m.memory_peak,
                        'cpu_usage': m.cpu_usage,
                        'records_processed': m.records_processed,
                        'throughput': m.throughput,
                        'timestamp': m.timestamp
                    } for m in report.performance_metrics
                ],
                'bottlenecks': report.bottlenecks,
                'recommendations': report.recommendations,
                'overall_score': report.overall_score
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"性能报告已导出: {filename}")
        return filename
    
    def print_summary(self, report: OptimizationReport):
        """打印报告摘要"""
        print("\n" + "=" * 80)
        print("性能优化报告摘要")
        print("=" * 80)
        print(f"报告ID: {report.report_id}")
        print(f"生成时间: {report.timestamp}")
        print(f"整体性能分数: {report.overall_score:.1%}")
        
        print(f"\n系统信息:")
        print(f"  CPU核心数: {report.system_info['cpu_count']}")
        print(f"  总内存: {report.system_info['memory_total']:.1f} GB")
        print(f"  可用内存: {report.system_info['memory_available']:.1f} GB")
        print(f"  Python版本: {report.system_info['python_version']}")
        
        print(f"\n性能指标:")
        for metric in report.performance_metrics:
            print(f"  {metric.operation_name}:")
            print(f"    执行时间: {metric.execution_time:.2f}s")
            print(f"    内存峰值: {metric.memory_peak:.1f}MB")
            print(f"    处理记录: {metric.records_processed:,}")
            print(f"    吞吐量: {metric.throughput:.1f} 记录/秒")
        
        if report.bottlenecks:
            print(f"\n性能瓶颈:")
            for bottleneck in report.bottlenecks:
                print(f"  ⚠️ {bottleneck}")
        
        print(f"\n优化建议:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
        
        print("=" * 80)


def main():
    """主函数"""
    print("=" * 80)
    print("性能优化和测试工具 v1.0")
    print("=" * 80)
    
    try:
        # 创建优化器
        optimizer = PerformanceOptimizer()
        
        # 运行性能测试
        report = optimizer.run_performance_test()
        
        # 打印摘要
        optimizer.print_summary(report)
        
        # 导出报告
        json_file = optimizer.export_report(report)
        print(f"\n📄 详细报告已保存到: {json_file}")
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        print(f"\n❌ 性能测试失败: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()