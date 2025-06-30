# 春雪食品产销分析系统 - API文档

## API概述

本文档详细描述了春雪食品产销分析系统的实际实现的RESTful API接口，基于Cloudflare Workers + Hono框架构建。

### 基础信息
- **Base URL (本地开发)**: `http://localhost:8787`
- **Base URL (生产环境)**: `https://your-worker.your-subdomain.workers.dev`
- **API版本**: v1 (当前实现)
- **认证方式**: 前端Mock认证 (生产环境建议使用JWT)
- **数据格式**: JSON
- **字符编码**: UTF-8
- **CORS**: 已配置，支持跨域请求

### 实际响应格式

**成功响应** (直接返回数据):
```json
[
  {
    "record_date": "2025-06-01",
    "sales_volume": 10.5,
    "avg_price": 4.50
  }
]
```

**错误响应**:
```json
{
  "error": "Missing required parameters: start_date, end_date"
}
```

**注意**: 当前实现为简化版本，直接返回数据数组或错误对象，未使用标准化的响应包装格式。

## 已实现的API端点

### 1. 产品管理

#### 1.1 获取产品列表
**GET** `/api/products`

获取所有产品信息，支持分页。

**查询参数**:
- `page` (可选): 页码，默认1
- `limit` (可选): 每页数量，默认50

**响应示例**:
```json
[
  {
    "product_id": 1,
    "product_name": "鸡大胸",
    "sku": null,
    "category": null
  },
  {
    "product_id": 2,
    "product_name": "鸡翅根",
    "sku": null,
    "category": null
  }
]
```

**实际测试**:
```bash
curl "http://localhost:8787/api/products?limit=5"
# 返回: 704个产品的列表
```

### 2. 数据分析

#### 2.1 获取汇总数据
**GET** `/api/summary`

获取指定日期范围内的汇总统计数据。

**查询参数**:
- `start_date` (必需): 开始日期，格式 YYYY-MM-DD
- `end_date` (必需): 结束日期，格式 YYYY-MM-DD

**响应示例**:
```json
{
  "total_products": 633,
  "analysis_days": 26,
  "total_sales": 10885.123,
  "total_production": 12861.456,
  "production_sales_ratio": 84.6
}
```

**实际测试**:
```bash
curl "http://localhost:8787/api/summary?start_date=2025-06-01&end_date=2025-06-26"
# 返回: 实际的汇总统计数据
```

#### 2.2 获取库存TOP排行
**GET** `/api/inventory/top`

获取指定日期的库存TOP排行榜。

**查询参数**:
- `date` (必需): 查询日期，格式 YYYY-MM-DD
- `limit` (可选): 返回数量，默认15

**响应示例**:
```json
[
  {
    "product_name": "鲜鸡肠",
    "inventory_level": 510463.0
  },
  {
    "product_name": "鸡胗",
    "inventory_level": 318990.0
  },
  {
    "product_name": "鸡心",
    "inventory_level": 273984.0
  }
]
```

**实际测试**:
```bash
curl "http://localhost:8787/api/inventory/top?date=2025-06-01&limit=5"
# 返回: 实际的库存排行数据
```

#### 2.3 获取销售价格趋势
**GET** `/api/trends/sales-price`

获取指定日期范围内的销售量和价格趋势数据。

**查询参数**:
- `start_date` (必需): 开始日期，格式 YYYY-MM-DD
- `end_date` (必需): 结束日期，格式 YYYY-MM-DD

**响应示例**:
```json
[
  {
    "record_date": "2025-06-01",
    "sales_volume": 85.234,
    "avg_price": 4.495
  },
  {
    "record_date": "2025-06-02",
    "sales_volume": 92.156,
    "avg_price": 4.521
  }
]
```

**实际测试**:
```bash
curl "http://localhost:8787/api/trends/sales-price?start_date=2025-06-01&end_date=2025-06-05"
# 返回: 实际的销售价格趋势数据
```

#### 2.4 获取产销比趋势
**GET** `/api/trends/ratio`

获取指定日期范围内的产销比趋势数据。

**查询参数**:
- `start_date` (必需): 开始日期，格式 YYYY-MM-DD
- `end_date` (必需): 结束日期，格式 YYYY-MM-DD

**响应示例**:
```json
[
  {
    "record_date": "2025-06-01",
    "ratio": 58.316
  },
  {
    "record_date": "2025-06-02",
    "ratio": 55.804
  }
]
```

**实际测试**:
```bash
curl "http://localhost:8787/api/trends/ratio?start_date=2025-06-01&end_date=2025-06-05"
# 返回: 实际的产销比趋势数据
```

## 产品管理模块

### 1. 获取产品列表
**GET** `/api/products`

获取产品列表，支持分页和筛选。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认1 |
| limit | number | 否 | 每页数量，默认20 |
| category | string | 否 | 产品分类筛选 |
| status | string | 否 | 状态筛选：active/inactive |
| search | string | 否 | 搜索关键词 |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "prod_001",
        "name": "鸡大胸",
        "sku": "CX001",
        "category": "分割品",
        "unit": "吨",
        "status": "active",
        "createdAt": "2024-01-01T12:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "pages": 8
    }
  },
  "message": "获取产品列表成功"
}
```

### 2. 创建产品
**POST** `/api/products`

创建新产品。

#### 请求参数
```json
{
  "name": "string",          // 产品名称，必填
  "sku": "string",           // SKU编码，可选
  "category": "string",      // 产品分类，可选
  "unit": "string",          // 计量单位，默认"吨"
  "description": "string"    // 产品描述，可选
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "id": "prod_002",
    "name": "鸡翅根",
    "sku": "CX002",
    "category": "分割品",
    "unit": "吨",
    "status": "active",
    "createdAt": "2024-01-01T12:00:00Z"
  },
  "message": "产品创建成功"
}
```

### 3. 更新产品
**PUT** `/api/products/{id}`

更新产品信息。

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 产品ID |

#### 请求参数
```json
{
  "name": "string",          // 产品名称
  "sku": "string",           // SKU编码
  "category": "string",      // 产品分类
  "unit": "string",          // 计量单位
  "description": "string",   // 产品描述
  "status": "string"         // 状态：active/inactive
}
```

### 4. 删除产品
**DELETE** `/api/products/{id}`

删除产品（软删除）。

#### 路径参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | string | 产品ID |

## 数据管理模块

### 1. 获取每日指标
**GET** `/api/metrics`

获取每日指标数据，支持多维度查询。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startDate | string | 否 | 开始日期，格式：YYYY-MM-DD |
| endDate | string | 否 | 结束日期，格式：YYYY-MM-DD |
| productIds | string | 否 | 产品ID列表，逗号分隔 |
| categories | string | 否 | 产品分类列表，逗号分隔 |
| metrics | string | 否 | 指标类型：production,sales,inventory,revenue |
| groupBy | string | 否 | 分组方式：date,product,category |
| page | number | 否 | 页码，默认1 |
| limit | number | 否 | 每页数量，默认50 |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "id": "metric_001",
        "date": "2024-01-01",
        "productId": "prod_001",
        "productName": "鸡大胸",
        "category": "分割品",
        "productionVolume": 125.6,
        "salesVolume": 98.3,
        "inventoryLevel": 456.7,
        "unitPrice": 18.5,
        "revenue": 1818.55,
        "cost": 1456.8
      }
    ],
    "summary": {
      "totalProduction": 2156.8,
      "totalSales": 1987.4,
      "totalRevenue": 36789.2,
      "averagePrice": 18.52
    },
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 1256,
      "pages": 26
    }
  },
  "message": "获取指标数据成功"
}
```

### 2. 创建每日指标
**POST** `/api/metrics`

创建新的每日指标记录。

#### 请求参数
```json
{
  "date": "2024-01-01",      // 日期，必填
  "productId": "prod_001",   // 产品ID，必填
  "productionVolume": 125.6, // 产量
  "salesVolume": 98.3,       // 销量
  "inventoryLevel": 456.7,   // 库存
  "unitPrice": 18.5,         // 单价
  "cost": 1456.8            // 成本
}
```

### 3. 批量导入数据
**POST** `/api/metrics/import`

批量导入Excel数据。

#### 请求格式
```
Content-Type: multipart/form-data
```

#### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | Excel文件 |
| skipHeader | boolean | 否 | 是否跳过表头，默认true |
| validateData | boolean | 否 | 是否验证数据，默认true |
| updateExisting | boolean | 否 | 是否更新已存在记录，默认false |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "importId": "import_001",
    "totalRows": 1000,
    "successRows": 987,
    "errorRows": 13,
    "errors": [
      {
        "row": 15,
        "field": "productionVolume",
        "message": "数值格式错误"
      }
    ]
  },
  "message": "数据导入完成"
}
```

### 4. 获取导入历史
**GET** `/api/metrics/import-history`

获取数据导入历史记录。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认1 |
| limit | number | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选：processing,completed,failed |

## 分析报表模块

### 1. 趋势分析
**GET** `/api/analytics/trends`

获取趋势分析数据。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| startDate | string | 是 | 开始日期 |
| endDate | string | 是 | 结束日期 |
| productIds | string | 否 | 产品ID列表 |
| metrics | string | 是 | 分析指标 |
| interval | string | 否 | 时间间隔：day,week,month |

#### 响应示例
```json
{
  "success": true,
  "data": {
    "trends": [
      {
        "date": "2024-01-01",
        "production": 125.6,
        "sales": 98.3,
        "inventory": 456.7,
        "revenue": 1818.55
      }
    ],
    "statistics": {
      "growthRate": {
        "production": 12.5,
        "sales": -2.3,
        "revenue": 8.9
      },
      "correlation": {
        "productionSales": 0.85,
        "salesRevenue": 0.92
      }
    }
  },
  "message": "趋势分析完成"
}
```

### 2. 对比分析
**GET** `/api/analytics/comparison`

获取产品对比分析数据。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productIds | string | 是 | 对比产品ID列表 |
| startDate | string | 是 | 开始日期 |
| endDate | string | 是 | 结束日期 |
| metrics | string | 是 | 对比指标 |

### 3. 预测分析
**GET** `/api/analytics/forecast`

获取预测分析数据。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productId | string | 是 | 产品ID |
| metric | string | 是 | 预测指标 |
| period | number | 是 | 预测周期（天数） |
| model | string | 否 | 预测模型：linear,polynomial,exponential |

## 系统管理模块

### 1. 用户管理
**GET** `/api/admin/users`

获取用户列表（管理员权限）。

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | number | 否 | 页码，默认1 |
| limit | number | 否 | 每页数量，默认20 |
| role | string | 否 | 角色筛选 |
| status | string | 否 | 状态筛选 |

### 2. 邀请码管理
**GET** `/api/admin/invite-codes`

获取邀请码列表。

**POST** `/api/admin/invite-codes`

创建新邀请码。

#### 请求参数
```json
{
  "code": "string",          // 邀请码，可选（自动生成）
  "maxUses": 10,            // 最大使用次数，-1为无限
  "expireDate": "2024-12-31" // 过期日期，可选
}
```

### 3. 系统统计
**GET** `/api/admin/statistics`

获取系统统计信息。

#### 响应示例
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 156,
      "active": 142,
      "newThisMonth": 23
    },
    "data": {
      "totalRecords": 15678,
      "lastImport": "2024-01-01T12:00:00Z",
      "storageUsed": "2.3GB"
    },
    "api": {
      "totalRequests": 45678,
      "averageResponseTime": 245,
      "errorRate": 0.02
    }
  },
  "message": "获取统计信息成功"
}
```

## 错误码参考

### 通用错误码
| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未授权访问 |
| 403 | 403 | 权限不足 |
| 404 | 404 | 资源不存在 |
| 409 | 409 | 资源冲突 |
| 422 | 422 | 数据验证失败 |
| 429 | 429 | 请求频率超限 |
| 500 | 500 | 服务器内部错误 |

### 业务错误码
| 错误码 | 说明 |
|--------|------|
| AUTH_E001 | 用户名或密码错误 |
| AUTH_E002 | Token已过期 |
| AUTH_E003 | 无效的Token |
| AUTH_E004 | 权限不足 |
| AUTH_E005 | 邀请码无效 |
| DATA_E001 | 数据格式错误 |
| DATA_E002 | 数据验证失败 |
| DATA_E003 | 重复数据 |
| SYS_E001 | 系统维护中 |
| SYS_E002 | 服务不可用 |

## 请求限制

### 速率限制
| 端点类型 | 限制 | 时间窗口 |
|----------|------|----------|
| 认证接口 | 5次/IP | 1小时 |
| 数据查询 | 100次/用户 | 1小时 |
| 数据导入 | 10次/用户 | 1天 |
| 其他接口 | 1000次/用户 | 1小时 |

### 数据限制
| 项目 | 限制 |
|------|------|
| 请求体大小 | 10MB |
| 查询结果数量 | 1000条/次 |
| 导入文件大小 | 50MB |
| 并发连接数 | 100/用户 |

## 版本管理

### API版本控制
- 当前版本：v1
- 版本格式：`/api/v1/endpoint`
- 向后兼容：支持至少2个主版本

### 版本更新说明
- **v1.0.0** (2024-01-01): 初始版本
- **v1.1.0** (2024-02-01): 新增预测分析功能
- **v1.2.0** (2024-03-01): 优化查询性能

**注意**: 本API文档会随着系统更新而持续维护，请关注版本变更说明。

#### 响应示例
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "username": "testuser",
      "roles": ["user"],
      "createdAt": "2024-01-01T12:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "message": "注册成功"
}
```

#### 错误码
- `AUTH_E005`: 邀请码无效或已过期
- `AUTH_E006`: 用户名已存在
- `DATA_E001`: 请求参数无效

### 2. 用户登录
**POST** `/api/auth/login`

用户登录获取访问令牌。

#### 请求参数
```json
{
  "username": "string",
  "password": "string"
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "username": "testuser",
      "roles": ["user"]
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400
  },
  "message": "登录成功"
}
```

#### 错误码
- `AUTH_E001`: 用户名或密码错误

### 3. 令牌验证
**GET** `/api/auth/verify`

验证当前令牌的有效性。

#### 请求头
```
Authorization: Bearer <token>
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "valid": true,
    "user": {
      "id": "user_123",
      "username": "testuser",
      "roles": ["user"]
    }
  }
}
```

### 4. 刷新令牌
**POST** `/api/auth/refresh`

刷新访问令牌。

#### 请求头
```
Authorization: Bearer <token>
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400
  }
}
```

## 产品管理模块

### 1. 获取产品列表
**GET** `/api/products`

获取所有产品信息。

#### 查询参数
- `category` (可选): 产品分类筛选
- `page` (可选): 页码，默认1
- `limit` (可选): 每页数量，默认50

#### 响应示例
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "productId": 1,
        "productName": "鸡大胸",
        "sku": "JDX001",
        "category": "分割品"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 100,
      "pages": 2
    }
  }
}
```

### 2. 创建产品
**POST** `/api/products`

创建新产品。

#### 请求参数
```json
{
  "productName": "string",   // 产品名称，必填
  "sku": "string",          // SKU，可选
  "category": "string"      // 分类，可选
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "productId": 123,
    "productName": "新产品",
    "sku": "NEW001",
    "category": "新分类"
  },
  "message": "产品创建成功"
}
```

### 3. 更新产品
**PUT** `/api/products/{productId}`

更新产品信息。

#### 路径参数
- `productId`: 产品ID

#### 请求参数
```json
{
  "productName": "string",   // 可选
  "sku": "string",          // 可选
  "category": "string"      // 可选
}
```

### 4. 删除产品
**DELETE** `/api/products/{productId}`

删除产品（软删除）。

#### 路径参数
- `productId`: 产品ID

## 数据管理模块

### 1. 获取每日指标
**GET** `/api/metrics/daily`

获取每日产销数据。

#### 查询参数
- `startDate`: 开始日期 (YYYY-MM-DD)
- `endDate`: 结束日期 (YYYY-MM-DD)
- `productIds` (可选): 产品ID列表，逗号分隔
- `categories` (可选): 产品分类列表，逗号分隔
- `page` (可选): 页码
- `limit` (可选): 每页数量

#### 响应示例
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "recordId": 1,
        "recordDate": "2024-01-01",
        "productId": 1,
        "productName": "鸡大胸",
        "productionVolume": 10.5,
        "salesVolume": 8.2,
        "inventoryLevel": 15.3,
        "averagePrice": 12.5
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 100,
      "total": 500,
      "pages": 5
    }
  }
}
```

### 2. 批量导入数据
**POST** `/api/metrics/import`

批量导入每日指标数据。

#### 请求参数
```json
{
  "data": [
    {
      "recordDate": "2024-01-01",
      "productId": 1,
      "productionVolume": 10.5,
      "salesVolume": 8.2,
      "inventoryLevel": 15.3,
      "averagePrice": 12.5
    }
  ],
  "overwrite": false  // 是否覆盖已存在的数据
}
```

#### 响应示例
```json
{
  "success": true,
  "data": {
    "imported": 100,
    "skipped": 5,
    "errors": 2,
    "details": [
      {
        "row": 10,
        "error": "产品ID不存在"
      }
    ]
  },
  "message": "数据导入完成"
}
```

### 3. 更新单条记录
**PUT** `/api/metrics/{recordId}`

更新单条每日指标记录。

#### 路径参数
- `recordId`: 记录ID

#### 请求参数
```json
{
  "productionVolume": 10.5,  // 可选
  "salesVolume": 8.2,       // 可选
  "inventoryLevel": 15.3,   // 可选
  "averagePrice": 12.5      // 可选
}
```

### 4. 删除记录
**DELETE** `/api/metrics/{recordId}`

删除指定的每日指标记录。

## 数据分析模块

### 1. 时间序列分析
**GET** `/api/analysis/timeseries`

获取时间序列分析数据。

#### 查询参数
- `startDate`: 开始日期
- `endDate`: 结束日期
- `productIds` (可选): 产品ID列表
- `metrics`: 指标类型 (production,sales,inventory,price)
- `groupBy` (可选): 分组方式 (day,week,month)

#### 响应示例
```json
{
  "success": true,
  "data": {
    "series": [
      {
        "date": "2024-01-01",
        "production": 100.5,
        "sales": 85.2,
        "inventory": 200.3,
        "avgPrice": 12.5
      }
    ],
    "summary": {
      "totalProduction": 3000.5,
      "totalSales": 2500.2,
      "avgInventory": 200.3,
      "avgPrice": 12.8
    }
  }
}
```

### 2. 产品对比分析
**GET** `/api/analysis/compare`

产品间对比分析。

#### 查询参数
- `productIds`: 产品ID列表，逗号分隔
- `startDate`: 开始日期
- `endDate`: 结束日期
- `metrics`: 对比指标

#### 响应示例
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "productId": 1,
        "productName": "鸡大胸",
        "totalProduction": 500.0,
        "totalSales": 450.0,
        "avgPrice": 12.5,
        "salesRate": 0.9
      }
    ],
    "comparison": {
      "bestPerformer": {
        "productId": 1,
        "metric": "salesRate",
        "value": 0.95
      }
    }
  }
}
```

### 3. 分类聚合分析
**GET** `/api/analysis/category`

按产品分类进行聚合分析。

#### 查询参数
- `startDate`: 开始日期
- `endDate`: 结束日期
- `categories` (可选): 分类列表

#### 响应示例
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "category": "分割品",
        "productCount": 10,
        "totalProduction": 1000.0,
        "totalSales": 900.0,
        "avgPrice": 15.2,
        "salesRate": 0.9
      }
    ],
    "total": {
      "totalProduction": 5000.0,
      "totalSales": 4500.0,
      "overallSalesRate": 0.9
    }
  }
}
```

### 4. 趋势预测
**GET** `/api/analysis/forecast`

基于历史数据进行趋势预测。

#### 查询参数
- `productId`: 产品ID
- `metric`: 预测指标 (production,sales,price)
- `days`: 预测天数，默认30

#### 响应示例
```json
{
  "success": true,
  "data": {
    "productId": 1,
    "metric": "sales",
    "forecast": [
      {
        "date": "2024-02-01",
        "predicted": 85.5,
        "confidence": 0.85,
        "upperBound": 95.0,
        "lowerBound": 76.0
      }
    ],
    "accuracy": {
      "mape": 0.15,  // 平均绝对百分比误差
      "rmse": 5.2    // 均方根误差
    }
  }
}
```

## 系统管理模块

### 1. 邀请码管理
**GET** `/api/admin/invite-codes`

获取邀请码列表（管理员权限）。

#### 响应示例
```json
{
  "success": true,
  "data": {
    "codes": [
      {
        "code": "WELCOME2024",
        "status": "active",
        "maxUses": -1,
        "used": 5,
        "expireDate": null,
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

### 2. 创建邀请码
**POST** `/api/admin/invite-codes`

创建新的邀请码。

#### 请求参数
```json
{
  "code": "string",         // 邀请码，可选（自动生成）
  "maxUses": 10,           // 最大使用次数，-1为无限
  "expireDate": "2024-12-31" // 过期日期，可选
}
```

### 3. 用户管理
**GET** `/api/admin/users`

获取用户列表（管理员权限）。

#### 查询参数
- `page` (可选): 页码
- `limit` (可选): 每页数量
- `role` (可选): 角色筛选

#### 响应示例
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "user_123",
        "username": "testuser",
        "roles": ["user"],
        "createdAt": "2024-01-01T00:00:00Z",
        "lastLogin": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 100,
      "pages": 2
    }
  }
}
```

### 4. 系统统计
**GET** `/api/admin/stats`

获取系统统计信息。

#### 响应示例
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 100,
      "active": 85,
      "newThisMonth": 15
    },
    "data": {
      "totalRecords": 50000,
      "dateRange": {
        "earliest": "2023-01-01",
        "latest": "2024-01-15"
      }
    },
    "api": {
      "requestsToday": 1500,
      "avgResponseTime": 250,
      "errorRate": 0.02
    }
  }
}
```

## 工具接口

### 1. 健康检查
**GET** `/health`

系统健康检查。

#### 响应示例
```json
{
  "status": "healthy",
  "checks": {
    "database": true,
    "memory": true,
    "responseTime": 45
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. 系统信息
**GET** `/api/system/info`

获取系统信息。

#### 响应示例
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "environment": "production",
    "region": "auto",
    "uptime": 86400,
    "features": {
      "authentication": true,
      "dataImport": true,
      "analytics": true
    }
  }
}
```

## 错误处理

### HTTP状态码
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `409`: 资源冲突
- `422`: 数据验证失败
- `429`: 请求过于频繁
- `500`: 服务器内部错误

### 错误码说明
详细的错误码定义请参考《错误处理文档》。

## 限流和配额

### 请求限制
- **未认证用户**: 每分钟10次请求
- **普通用户**: 每分钟100次请求
- **管理员**: 每分钟500次请求

### 数据限制
- **单次查询**: 最多返回1000条记录
- **批量导入**: 单次最多导入5000条记录
- **文件上传**: 最大10MB

## SDK和示例

### JavaScript示例
```javascript
// 认证
const auth = async (username, password) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  const result = await response.json();
  if (result.success) {
    localStorage.setItem('token', result.data.token);
  }
  return result;
};

// 获取数据
const getMetrics = async (startDate, endDate) => {
  const token = localStorage.getItem('token');
  const response = await fetch(`/api/metrics/daily?startDate=${startDate}&endDate=${endDate}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};
```

### Python示例
```python
import requests

class ChunxueAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        response = requests.post(f"{self.base_url}/api/auth/login", 
                               json={"username": username, "password": password})
        result = response.json()
        if result["success"]:
            self.token = result["data"]["token"]
        return result
    
    def get_metrics(self, start_date, end_date):
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"startDate": start_date, "endDate": end_date}
        response = requests.get(f"{self.base_url}/api/metrics/daily", 
                              headers=headers, params=params)
        return response.json()
```

## 版本历史

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础认证功能
- 产品和数据管理
- 基础分析功能

---

**注意**: 本API文档会随着系统更新而持续维护，请关注版本变更说明。