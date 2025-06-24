// src/index.ts
import { Router, IRequest } from 'itty-router';
import bcrypt from 'bcryptjs';

// JWT相关依赖
import { sign, verify, decode, JwtPayload } from '@tsndr/cloudflare-worker-jwt';

// 定义我们的环境类型，这样 TypeScript 就知道 env.DB 的存在
export interface Env {
  DB: D1Database;
  JWT_SECRET: string; // JWT密钥
  // 如果你还有其他绑定，在这里添加
}

// 定义请求体接口
interface LoginRequest {
  username: string;
  password: string;
}

interface RegisterRequest extends LoginRequest {
  inviteCode: string;
}

interface ValidateInviteCodeRequest {
  inviteCode: string;
}

// JWT载荷接口
interface UserJwtPayload extends JwtPayload {
  sub: string;
  username: string;
  roles: string[];
}

// 定义统一响应格式
interface ApiResponse<T> {
  code: number;
  message: string;
  data: T | null;
}

// 辅助函数：生成统一响应
function createResponse<T>(code: number, message: string, data: T | null = null): Response {
  const responseBody: ApiResponse<T> = {
    code,
    message,
    data
  };
  
  return new Response(JSON.stringify(responseBody), {
    status: code >= 200 && code < 300 ? code : 200, // HTTP状态码
    headers: { 
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*', // CORS支持
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
  });
}

// 创建一个新的路由器实例
const router = Router();

// --- API 路由 ---

// 注册接口
router.post('/auth/register', async (request: IRequest, env: Env) => {
  try {
    const data = await request.json() as unknown as RegisterRequest;
    const { username, password, inviteCode } = data;

    if (!username || !password || !inviteCode) {
      return createResponse(400, '用户名、密码和邀请码为必填项。');
    }
    
    // 用户名长度检查
    if (username.length < 3 || username.length > 20) {
      return createResponse(400, '用户名长度应为3-20个字符。');
    }
    
    // 密码强度检查
    if (password.length < 6) {
      return createResponse(400, '密码长度不能少于6位。');
    }

    // 验证邀请码
    const inviteCodeValid = await env.DB.prepare('SELECT * FROM invite_codes WHERE code = ? AND status = "active" AND (max_uses > used OR max_uses = -1) AND (expire_date IS NULL OR expire_date >= CURRENT_DATE)')
                                    .bind(inviteCode)
                                    .first();
    
    if (!inviteCodeValid) {
      return createResponse(400, '邀请码无效或已过期。');
    }

    // 检查用户是否已存在
    const existingUser = await env.DB.prepare('SELECT id FROM users WHERE username = ?')
                                     .bind(username)
                                     .first();
    if (existingUser) {
      return createResponse(409, '该用户名已被注册。');
    }

    // 使用 bcryptjs 哈希密码，10是成本因子，越高越安全但越慢
    const hashedPassword = await bcrypt.hash(password, 10);

    // 生成头像字符（用户名首字母大写）
    const avatar = username.charAt(0).toUpperCase();

    // 开始数据库事务
    const userId = crypto.randomUUID();
    
    // 插入新用户到数据库
    await env.DB.prepare('INSERT INTO users (id, username, password, avatar, roles, created_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)')
                .bind(userId, username, hashedPassword, avatar, JSON.stringify(["user"]))
                .run();

    // 更新邀请码使用次数
    await env.DB.prepare('UPDATE invite_codes SET used = used + 1 WHERE code = ?')
                .bind(inviteCode)
                .run();

    // 生成JWT令牌
    const token = await sign({
      sub: userId,
      username: username,
      roles: ["user"],
      exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60, // 24小时有效期
    }, env.JWT_SECRET || 'default-secret-key');

    return createResponse(200, '注册成功', {
      token,
      user: {
        id: userId,
        username,
        avatar,
        roles: ["user"]
      }
    });

  } catch (error: any) {
    console.error('注册错误:', error);
    return createResponse(500, '服务器内部错误。');
  }
});

// 登录接口
router.post('/auth/login', async (request: IRequest, env: Env) => {
  try {
    const data = await request.json() as unknown as LoginRequest;
    const { username, password } = data;

    if (!username || !password) {
      return createResponse(400, '用户名和密码为必填项。');
    }

    // 在数据库中查找用户
    const user: { id: string; username: string; password: string; avatar: string; roles: string } | null = await env.DB.prepare(
        'SELECT id, username, password, avatar, roles FROM users WHERE username = ?'
      )
      .bind(username)
      .first();

    if (!user) {
      return createResponse(401, '用户名或密码无效。');
    }

    // 验证密码是否匹配
    const passwordMatch = await bcrypt.compare(password, user.password);

    if (!passwordMatch) {
      return createResponse(401, '用户名或密码无效。');
    }

    // 解析角色
    const roles = JSON.parse(user.roles);

    // 更新最后登录时间
    await env.DB.prepare('UPDATE users SET last_login_time = CURRENT_TIMESTAMP WHERE id = ?')
                .bind(user.id)
                .run();

    // 生成JWT令牌
    const token = await sign({
      sub: user.id,
      username: user.username,
      roles: roles,
      exp: Math.floor(Date.now() / 1000) + 24 * 60 * 60, // 24小时有效期
    }, env.JWT_SECRET || 'default-secret-key');

    return createResponse(200, '登录成功', {
      token,
      user: {
        id: user.id,
        username: user.username,
        avatar: user.avatar,
        roles: roles
      }
    });

  } catch (error: any) {
    console.error('登录错误:', error);
    return createResponse(500, '服务器内部错误。');
  }
});

// 邀请码验证接口
router.post('/auth/validate-invite-code', async (request: IRequest, env: Env) => {
  try {
    const data = await request.json() as unknown as ValidateInviteCodeRequest;
    const { inviteCode } = data;

    if (!inviteCode) {
      return createResponse(400, '邀请码为必填项。');
    }

    // 验证邀请码
    const inviteCodeValid = await env.DB.prepare('SELECT * FROM invite_codes WHERE code = ? AND status = "active" AND (max_uses > used OR max_uses = -1) AND (expire_date IS NULL OR expire_date >= CURRENT_DATE)')
                                    .bind(inviteCode)
                                    .first();
    
    if (!inviteCodeValid) {
      return createResponse(200, '邀请码无效', { valid: false });
    }

    return createResponse(200, '邀请码有效', { valid: true });

  } catch (error: any) {
    console.error('邀请码验证错误:', error);
    return createResponse(500, '服务器内部错误。');
  }
});

// 退出登录接口
router.post('/auth/logout', async (request: IRequest, env: Env) => {
  // 由于JWT是无状态的，服务器端不需要做特殊处理
  // 客户端只需要删除本地存储的token即可
  return createResponse(200, '退出成功', null);
});

// 获取用户信息接口
router.get('/auth/user-info', async (request: IRequest, env: Env) => {
  try {
    // 从请求头获取JWT令牌
    const authHeader = request.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return createResponse(401, '未授权，请先登录。');
    }

    const token = authHeader.split(' ')[1];
    
    // 验证JWT令牌
    try {
      // 根据类型定义，verify可能返回undefined
      const jwtData = await verify<UserJwtPayload>(token, env.JWT_SECRET || 'default-secret-key');
      if (!jwtData) {
        return createResponse(401, 'token已过期或无效，请重新登录。');
      }
      
      // 使用decode获取payload，避免类型问题
      const decoded = decode(token);
      // 强制类型转换
      const userId = String(decoded.payload.sub);
      
      // 从数据库获取最新的用户信息
      const user = await env.DB.prepare(
        'SELECT id, username, avatar, email, roles, last_login_time FROM users WHERE id = ?'
      )
      .bind(userId)
      .first();

      if (!user) {
        return createResponse(404, '用户不存在。');
      }

      // 解析角色
      const roles = JSON.parse(user.roles as string);

      return createResponse(200, '获取成功', {
        id: user.id,
        username: user.username,
        avatar: user.avatar,
        email: user.email,
        roles: roles,
        lastLoginTime: user.last_login_time
      });
    } catch (err) {
      return createResponse(401, 'token已过期或无效，请重新登录。');
    }
  } catch (error: any) {
    console.error('获取用户信息错误:', error);
    return createResponse(500, '服务器内部错误。');
  }
});

// --- CORS预检请求处理 ---
router.options('*', () => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    }
  });
});

// --- 静态文件服务 ---
router.get('/', (request: IRequest, env: Env) => {
    return new Response('春雪食品生产销售分析报告系统API服务', { 
      status: 200, 
      headers: { 'Content-Type': 'text/html' } 
    });
});

// --- 兜底路由 ---
router.all('*', () => createResponse(404, '请求的资源不存在。'));

// --- Worker 入口 ---
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // 将请求交给我们的路由器处理
    return router.handle(request, env, ctx);
  },
};