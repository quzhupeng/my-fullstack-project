-- 价格调整记录表，用于存储产品价格变动历史
CREATE TABLE IF NOT EXISTS PriceAdjustments (
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
CREATE INDEX IF NOT EXISTS idx_priceadjustments_date ON PriceAdjustments(adjustment_date);
CREATE INDEX IF NOT EXISTS idx_priceadjustments_product_id ON PriceAdjustments(product_id);
CREATE INDEX IF NOT EXISTS idx_priceadjustments_price_diff ON PriceAdjustments(price_difference);
