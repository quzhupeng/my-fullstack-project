# CORS跨域配置参考指南

## 📋 文档概述

本文档提供春雪食品分析系统CORS(跨域资源共享)配置的完整参考，包括问题诊断、解决方案实施和最佳实践。基于v2.2.0版本的重大CORS修复经验编写。

**适用版本**: v2.2.0+  
**最后更新**: 2025-07-01  
**修复状态**: ✅ CORS问题已完全解决

## 🚨 问题背景

### 历史问题
在v2.1.0及之前版本，系统存在严重的CORS配置冲突，导致：
- 前端无法连接后端API
- 浏览器控制台显示CORS策略错误
- 认证功能完全失效
- 所有数据加载失败

### 根本原因
**多重冲突的CORS配置**同时存在于后端代码中，造成不可预测的跨域行为。

## 🔧 当前CORS配置 (v2.2.0)

### 完整实现代码
**文件位置**: `backend/src/index.ts`

```typescript
import { Hono } from 'hono';

// 允许的源列表配置
const ALLOWED_ORIGINS = [
  'http://localhost:3000',           // 本地开发前端
  'http://127.0.0.1:3000',          // 本地开发前端(备用)
  'http://localhost:8080',           // 备用开发端口
  'https://my-fullstack-project.pages.dev',  // 生产前端域名
  'https://backend.qu18354531302.workers.dev',  // 后端自身
  'https://my-auth-worker.qu18354531302.workers.dev'  // 认证服务
];

const app = new Hono<{ Bindings: Bindings }>();

// 综合CORS中间件 - 处理预检和实际请求
app.use('/*', async (c, next) => {
  const origin = c.req.header('Origin');
  const requestMethod = c.req.method;
  
  // 验证请求源是否在允许列表中
  const isAllowedOrigin = origin && ALLOWED_ORIGINS.includes(origin);
  const allowOrigin = isAllowedOrigin ? origin : ALLOWED_ORIGINS[0];
  
  // 处理预检OPTIONS请求
  if (requestMethod === 'OPTIONS') {
    return c.text('', 200, {
      'Access-Control-Allow-Origin': allowOrigin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, X-Requested-With',
      'Access-Control-Expose-Headers': 'Content-Length, X-Requested-With',
      'Access-Control-Max-Age': '86400',  // 24小时缓存
      'Vary': 'Origin'  // 重要：告诉CDN根据Origin缓存
    });
  }
  
  // 处理实际API请求
  await next();
  
  // 为所有响应添加CORS头
  c.res.headers.set('Access-Control-Allow-Origin', allowOrigin);
  c.res.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  c.res.headers.set('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization, X-Requested-With');
  c.res.headers.set('Access-Control-Expose-Headers', 'Content-Length, X-Requested-With');
  c.res.headers.set('Access-Control-Max-Age', '86400');
  c.res.headers.set('Vary', 'Origin');
});

// API端点定义...
export default app;
```

### 配置说明

#### 允许的源 (ALLOWED_ORIGINS)
| 源地址 | 用途 | 环境 |
|--------|------|------|
| `http://localhost:3000` | 本地前端开发 | 开发 |
| `http://127.0.0.1:3000` | 本地前端开发(备用) | 开发 |
| `http://localhost:8080` | 备用开发端口 | 开发 |
| `https://my-fullstack-project.pages.dev` | 生产前端 | 生产 |
| `https://backend.qu18354531302.workers.dev` | 后端自身 | 生产 |
| `https://my-auth-worker.qu18354531302.workers.dev` | 认证服务 | 生产 |

#### CORS头说明
| 头名称 | 值 | 作用 |
|--------|-----|------|
| `Access-Control-Allow-Origin` | 特定源或回退源 | 指定允许的请求源 |
| `Access-Control-Allow-Methods` | `GET, POST, PUT, DELETE, OPTIONS` | 允许的HTTP方法 |
| `Access-Control-Allow-Headers` | `Content-Type, Accept, Authorization, X-Requested-With` | 允许的请求头 |
| `Access-Control-Expose-Headers` | `Content-Length, X-Requested-With` | 前端可访问的响应头 |
| `Access-Control-Max-Age` | `86400` | 预检请求缓存时间(24小时) |
| `Vary` | `Origin` | CDN缓存策略指示 |

## 🧪 CORS测试与验证

### 1. 预检请求测试
```bash
# 测试OPTIONS预检请求
curl -I -X OPTIONS "https://backend.qu18354531302.workers.dev/api/products" \
  -H "Origin: https://my-fullstack-project.pages.dev" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type"

# 预期响应头:
# HTTP/2 200
# access-control-allow-origin: https://my-fullstack-project.pages.dev
# access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
# access-control-allow-headers: Content-Type, Accept, Authorization, X-Requested-With
# access-control-max-age: 86400
# vary: Origin
```

### 2. 实际API请求测试
```bash
# 测试GET请求
curl -X GET "https://backend.qu18354531302.workers.dev/api/summary?start_date=2025-06-01&end_date=2025-06-26" \
  -H "Origin: https://my-fullstack-project.pages.dev" \
  -H "Accept: application/json" \
  -v

# 预期结果:
# - 返回JSON数据
# - 包含正确的CORS头
# - 无错误信息
```

### 3. 认证端点测试
```bash
# 测试POST认证请求的预检
curl -I -X OPTIONS "https://backend.qu18354531302.workers.dev/api/login" \
  -H "Origin: https://my-fullstack-project.pages.dev" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

# 预期: 返回200状态码和正确CORS头
```

### 4. 自动化测试页面
访问专用测试页面进行全面验证：
```
https://my-fullstack-project.pages.dev/cors-test.html
```

**测试项目**:
- ✅ 摘要数据API (`/api/summary`)
- ✅ 产品列表API (`/api/products`)
- ✅ 库存数据API (`/api/inventory/top`)
- ✅ 趋势数据API (`/api/trends/sales-price`)

## 🔧 配置管理

### 添加新的允许源
如需添加新的前端域名或开发环境：

1. **修改配置**:
```typescript
const ALLOWED_ORIGINS = [
  // 现有源...
  'https://new-frontend-domain.com',  // 新增源
  'http://localhost:8081',            // 新开发端口
];
```

2. **部署更新**:
```bash
cd backend
npm run deploy
```

3. **验证新源**:
```bash
curl -I -X OPTIONS "https://backend.qu18354531302.workers.dev/api/products" \
  -H "Origin: https://new-frontend-domain.com"
```

### 移除不需要的源
1. 从`ALLOWED_ORIGINS`数组中删除对应条目
2. 重新部署后端
3. 验证旧源无法访问

## 🚨 故障排除

### 常见CORS错误

#### 错误1: "No 'Access-Control-Allow-Origin' header"
**症状**: 浏览器控制台显示CORS策略错误
**原因**: 请求源不在允许列表中
**解决**: 将源添加到`ALLOWED_ORIGINS`数组

#### 错误2: "CORS preflight request failed"
**症状**: OPTIONS请求失败
**原因**: 预检请求处理不正确
**解决**: 检查OPTIONS处理逻辑

#### 错误3: "Method not allowed by CORS policy"
**症状**: 特定HTTP方法被拒绝
**原因**: `Access-Control-Allow-Methods`不包含该方法
**解决**: 更新允许的方法列表

### 诊断命令
```bash
# 检查当前CORS配置
curl -I -X OPTIONS "https://backend.qu18354531302.workers.dev/api/products" \
  -H "Origin: https://my-fullstack-project.pages.dev"

# 检查特定源的访问权限
curl -I -X GET "https://backend.qu18354531302.workers.dev/api/summary?start_date=2025-06-01&end_date=2025-06-26" \
  -H "Origin: YOUR_FRONTEND_DOMAIN"

# 验证部署版本
curl "https://backend.qu18354531302.workers.dev/" | grep -i version
```

## 📝 最佳实践

### 安全性
1. **避免使用通配符**: 不使用`Access-Control-Allow-Origin: *`
2. **最小权限原则**: 只允许必要的源、方法和头
3. **定期审查**: 定期检查和清理不需要的源

### 性能优化
1. **合理缓存**: 设置适当的`max-age`值
2. **CDN友好**: 使用`Vary: Origin`头
3. **减少预检**: 尽量使用简单请求

### 维护性
1. **集中配置**: 所有CORS设置在一个地方
2. **文档同步**: 配置变更时更新文档
3. **测试覆盖**: 每次变更后进行完整测试

## 📊 部署信息

### 当前生产配置
- **后端URL**: https://backend.qu18354531302.workers.dev
- **前端URL**: https://my-fullstack-project.pages.dev
- **版本**: v2.2.0
- **部署状态**: ✅ 已部署并验证

### 部署历史
| 版本 | 日期 | CORS状态 | 说明 |
|------|------|----------|------|
| v2.2.0 | 2025-07-01 | ✅ 完全修复 | 单一综合CORS中间件 |
| v2.1.0 | 2025-06-30 | ❌ 冲突配置 | 多重CORS配置冲突 |
| v2.0.0 | 2025-06-29 | ⚠️ 部分工作 | 基础CORS配置 |

---

**维护说明**: 本文档应在每次CORS配置变更时更新，确保与实际代码保持同步。
