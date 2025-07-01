# Spring Snow Food Analysis System - API文档更新

**版本**: v2.1.0 (2025-07-01)  
**状态**: ✅ 生产就绪 - 销售数据API已修复

## 重要更新说明

### 销售价格API修复 (v2.1.0)

**端点**: `GET /api/trends/sales-price`

**修复内容**:
- ✅ 解决了`total_amount`字段返回null的问题
- ✅ 确保所有数值字段返回有效数据
- ✅ 修复了前端JavaScript错误

**修复前响应** (有问题):
```json
[
  {
    "record_date": "2025-06-01",
    "total_sales": 102578.25,
    "total_amount": null,           // ❌ null值导致前端错误
    "avg_price": 21.533213442913247
  }
]
```

**修复后响应** (正确):
```json
[
  {
    "record_date": "2025-06-01",
    "total_sales": 102578.25,
    "total_amount": 652.935472895,  // ✅ 正确的销售金额
    "avg_price": 21.533213442913247
  }
]
```

## API端点详细说明

### 1. 销售价格趋势API

**端点**: `GET /api/trends/sales-price`

**参数**:
- `start_date` (必需): 开始日期，格式 YYYY-MM-DD
- `end_date` (必需): 结束日期，格式 YYYY-MM-DD

**响应字段**:
- `record_date`: 记录日期
- `total_sales`: 总销售量 (吨)
- `total_amount`: 总销售金额 (元，含税)
- `avg_price`: 平均价格 (元/吨)

**数据计算逻辑**:
```sql
SELECT
  dm.record_date,
  SUM(dm.sales_volume) as total_sales,
  SUM(dm.sales_amount) as total_amount,    -- 修复: 现在正确计算
  AVG(dm.average_price) as avg_price
FROM DailyMetrics dm
JOIN Products p ON dm.product_id = p.product_id
WHERE dm.record_date BETWEEN ?1 AND ?2
  AND dm.sales_volume IS NOT NULL
  AND dm.sales_volume > 0
  AND [产品过滤条件]
GROUP BY dm.record_date
ORDER BY dm.record_date ASC
```

**使用示例**:
```bash
# 获取2025年6月前5天的销售数据
curl "http://localhost:8787/api/trends/sales-price?start_date=2025-06-01&end_date=2025-06-05"
```

### 2. 数据库字段映射

**DailyMetrics表结构** (v2.1.0):
```sql
CREATE TABLE DailyMetrics (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    production_volume REAL,
    sales_volume REAL,
    sales_amount REAL,              -- 新增: 销售金额字段
    inventory_level REAL,
    average_price REAL,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);
```

**Excel数据映射**:
- `发票日期` → `record_date`
- `主数量` → `sales_volume`
- `本币无税金额` → 用于计算 `sales_amount` 和 `average_price`
- `物料名称` → 关联 `Products.product_name`

**计算公式**:
```python
# 销售金额 (含税)
sales_amount = tax_free_amount * 1.09

# 平均单价 (元/吨)
average_price = (tax_free_amount / sales_volume) * 1.09 * 1000
```

## 错误处理和最佳实践

### 前端数据处理
```javascript
// 安全的API数据处理
async function processSalesData(apiResponse) {
    return apiResponse.map(item => ({
        date: item.record_date || 'N/A',
        sales: parseFloat(item.total_sales) || 0,
        amount: parseFloat(item.total_amount) || 0,
        price: parseFloat(item.avg_price) || 0
    }));
}

// 安全的数值格式化
function formatNumber(value) {
    const num = parseFloat(value);
    return isNaN(num) ? '0' : num.toLocaleString();
}
```

### 数据验证
```bash
# 验证API数据完整性
curl -s "http://localhost:8787/api/trends/sales-price?start_date=2025-06-01&end_date=2025-06-05" | \
jq '.[] | select(.total_amount == null)'

# 如果有输出，说明仍有null值需要修复
```

## 维护注意事项

### 数据库一致性
- ⚠️ **重要**: 始终使用Wrangler D1接口进行数据操作
- ⚠️ **避免**: 直接操作SQLite文件，会导致数据不一致
- ✅ **推荐**: 使用统一的数据导入和更新流程

### 数据导入流程
1. 通过Wrangler D1执行数据导入
2. 验证关键字段非null
3. 测试API响应完整性
4. 前端功能验证

### 监控和告警
建议监控以下指标:
- API响应时间
- null值出现频率
- 前端JavaScript错误率
- 数据完整性检查

## 版本历史

### v2.1.0 (2025-07-01)
- ✅ 修复销售数据API null值问题
- ✅ 添加sales_amount字段计算
- ✅ 改进前端错误处理
- ✅ 统一数据库操作接口

### v2.0.0 (2025-06-30)
- ✅ 解决数据显示问题
- ✅ 修复API过滤逻辑
- ✅ 完善产品过滤规则

### v1.0.0 (2025-06-26)
- 🎯 初始版本发布
- 📊 基础图表功能
- 🔄 数据导入流程
