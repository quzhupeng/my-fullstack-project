-- schema.sql

-- 产品主表，用于存储所有产品的静态信息
CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 产品的唯一标识，自动递增
    product_name TEXT NOT NULL UNIQUE,             -- 产品名称，如“鸡大胸”，必须唯一且不能为空
    sku TEXT UNIQUE,                               -- 产品的库存单位(SKU)，可选，但建议唯一
    category TEXT                                  -- 产品分类，如“分割品”、“调理品”等，用于聚合分析
);

-- 每日指标表，记录每个产品每天的产销存数据
CREATE TABLE DailyMetrics (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 记录的唯一标识，自动递增
    record_date TEXT NOT NULL,                    -- 记录日期，格式为 'YYYY-MM-DD'，便于排序和查询
    product_id INTEGER NOT NULL,                  -- 关联到Products表的外键
    production_volume REAL,                       -- 当日产量（单位：吨）
    sales_volume REAL,                            -- 当日销量（单位：吨）
    inventory_level REAL,                         -- 当日终库存（单位：吨）
    average_price REAL,                           -- 当日平均售价（单位：元/吨）
    FOREIGN KEY (product_id) REFERENCES Products(product_id) -- 定义外键约束，确保数据完整性
);

-- 价格调整记录表，用于存储产品价格变动历史
CREATE TABLE PriceAdjustments (
    adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 调价记录的唯一标识
    adjustment_date TEXT NOT NULL,                   -- 调价日期，格式为 'YYYY-MM-DD'
    product_id INTEGER NOT NULL,                     -- 关联到Products表的外键
    product_name TEXT NOT NULL,                      -- 产品名称（冗余存储，便于查询）
    specification TEXT,                              -- 产品规格
    adjustment_count INTEGER DEFAULT 1,             -- 当日调价次数
    previous_price REAL,                            -- 调价前价格（元/吨）
    current_price REAL NOT NULL,                    -- 调价后价格（元/吨）
    price_difference REAL NOT NULL,                 -- 价格差异（元/吨），current_price - previous_price
    category TEXT,                                  -- 产品分类
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,     -- 记录创建时间
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

-- 为PriceAdjustments表创建索引，提升查询性能
CREATE INDEX idx_priceadjustments_date ON PriceAdjustments(adjustment_date);
CREATE INDEX idx_priceadjustments_product_id ON PriceAdjustments(product_id);
CREATE INDEX idx_priceadjustments_price_diff ON PriceAdjustments(price_difference);

-- 为DailyMetrics表的关键查询字段创建索引，大幅提升查询性能
CREATE INDEX idx_dailymetrics_date ON DailyMetrics(record_date);
CREATE INDEX idx_dailymetrics_product_id ON DailyMetrics(product_id);

-- 用户表，用于存储用户信息
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT, -- 用户的唯一标识，自动递增
    username TEXT NOT NULL UNIQUE,             -- 用户名，必须唯一且不能为空
    password TEXT NOT NULL,                    -- 密码
    created_at TEXT DEFAULT CURRENT_TIMESTAMP      -- 记录创建时间
);
