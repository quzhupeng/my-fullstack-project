-- 删除已存在的表，以便重新初始化
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS invite_codes;

-- 用户信息表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user', -- 'user' 或 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- 邀请码表
CREATE TABLE invite_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    -- PRD中提到使用次数限制，我们简化为 expires_at
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT 0,
    used_by_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为常用查询创建索引
CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_invite_codes_code ON invite_codes (code);