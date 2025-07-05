import { Hono } from 'hono';
import { cors } from 'hono/cors';
import * as XLSX from 'xlsx';

// Comprehensive CORS configuration
const ALLOWED_ORIGINS = [
  'http://localhost:3000',
  'http://127.0.0.1:3000',
  'http://localhost:8080',
  'https://my-fullstack-project.pages.dev',
  'https://7bbead58.my-fullstack-project.pages.dev',
  'https://backend.qu18354531302.workers.dev',
  'https://my-auth-worker.qu18354531302.workers.dev'
];

// CORS headers for manual handling
const CORS_HEADERS = {
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, X-Requested-With',
  'Access-Control-Expose-Headers': 'Content-Length, X-Requested-With',
  'Access-Control-Max-Age': '86400',
};

// Define the bindings for Cloudflare environment variables
type Bindings = {
  DB: D1Database;
};

const app = new Hono<{ Bindings: Bindings }>();

// --- Business Logic Layer ---

/**
 * Centralized product filtering logic based on original Python script requirements
 * Filters out:
 * 1. Fresh products (starting with '鲜') except '凤肠' products
 * 2. By-products and empty categories (when category filtering is enabled)
 */
class ProductFilter {
  /**
   * Generate SQL WHERE clause for product name filtering
   * Always excludes fresh products except '凤肠'
   */
  static getProductNameFilter(): string {
    return `(
      -- Keep products that don't start with '鲜' (fresh products)
      p.product_name NOT LIKE '鲜%'
      OR
      -- Special exception: keep '凤肠' products even if they contain '鲜'
      p.product_name LIKE '%凤肠%'
    )`;
  }

  /**
   * Generate SQL WHERE clause for category filtering
   * @param strict - If true, requires category to be non-null/non-empty
   *                If false, allows null/empty categories (relaxed mode)
   */
  static getCategoryFilter(strict: boolean = false): string {
    if (strict) {
      return `(
        -- Strict mode: require valid category and exclude specific ones
        p.category IS NOT NULL
        AND p.category != ''
        AND p.category NOT IN ('副产品', '生鲜品其他')
      )`;
    } else {
      return `(
        -- Relaxed mode: allow null/empty categories or exclude specific ones
        p.category IS NULL
        OR p.category = ''
        OR p.category NOT IN ('副产品', '生鲜品其他')
      )`;
    }
  }

  /**
   * Generate complete product filtering WHERE clause
   * @param strict - Whether to use strict category filtering
   * @param tableAlias - Table alias for the Products table (default: 'p')
   */
  static getCompleteFilter(strict: boolean = false, tableAlias: string = 'p'): string {
    const productNameFilter = this.getProductNameFilter().replace(/p\./g, `${tableAlias}.`);
    const categoryFilter = this.getCategoryFilter(strict).replace(/p\./g, `${tableAlias}.`);

    return `${productNameFilter} AND ${categoryFilter}`;
  }

  /**
   * Generate filtering for PriceAdjustments table (uses pa.product_name and pa.category)
   */
  static getPriceAdjustmentFilter(strict: boolean = false): string {
    const productNameFilter = `(
      pa.product_name NOT LIKE '鲜%'
      OR
      pa.product_name LIKE '%凤肠%'
    )`;

    const categoryFilter = strict
      ? `(
          pa.category IS NOT NULL
          AND pa.category != ''
          AND pa.category NOT IN ('副产品', '生鲜品其他')
        )`
      : `(
          pa.category IS NULL
          OR pa.category = ''
          OR pa.category NOT IN ('副产品', '生鲜品其他')
        )`;

    return `${productNameFilter} AND ${categoryFilter}`;
  }
}

// Comprehensive CORS middleware that handles both preflight and actual requests
app.use('/*', async (c, next) => {
  const origin = c.req.header('Origin');
  const requestMethod = c.req.method;

  // Determine if origin is allowed
  const isAllowedOrigin = origin && ALLOWED_ORIGINS.includes(origin);
  const allowOrigin = isAllowedOrigin ? origin : ALLOWED_ORIGINS[0]; // fallback to first allowed origin

  // Handle preflight OPTIONS requests
  if (requestMethod === 'OPTIONS') {
    return c.text('', 200, {
      'Access-Control-Allow-Origin': allowOrigin,
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, X-Requested-With',
      'Access-Control-Expose-Headers': 'Content-Length, X-Requested-With',
      'Access-Control-Max-Age': '86400',
      'Vary': 'Origin'
    });
  }

  // Process the actual request
  await next();

  // Add CORS headers to all responses
  c.res.headers.set('Access-Control-Allow-Origin', allowOrigin);
  c.res.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  c.res.headers.set('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization, X-Requested-With');
  c.res.headers.set('Access-Control-Expose-Headers', 'Content-Length, X-Requested-With');
  c.res.headers.set('Access-Control-Max-Age', '86400');
  c.res.headers.set('Vary', 'Origin');
});

// --- API Endpoints ---

app.post('/api/register', async (c) => {
  const { username, password, inviteCode } = await c.req.json();

  if (!username || !password || !inviteCode) {
    return c.json({ success: false, message: 'Missing required fields' }, 400);
  }

  // In a real application, you would have a database of invite codes.
  if (inviteCode !== 'SPRING2025') {
    return c.json({ success: false, message: 'Invalid invite code' }, 400);
  }

  try {
    // In a real application, you would hash the password before storing it.
    const ps = c.env.DB.prepare('INSERT INTO Users (username, password) VALUES (?, ?)').bind(username, password);
    await ps.run();

    // In a real application, you would generate a proper JWT.
    const token = 'mock-token-' + Date.now();
    const user = { username, avatar: username.charAt(0).toUpperCase() };

    return c.json({ success: true, token, user });
  } catch (e: any) {
    if (e.message.includes('UNIQUE constraint failed')) {
      return c.json({ success: false, message: 'Username already exists' }, 409);
    }
    return c.json({ success: false, message: 'Registration failed', details: e.message }, 500);
  }
});

app.post('/api/login', async (c) => {
  const { username, password } = await c.req.json();

  if (!username || !password) {
    return c.json({ success: false, message: 'Missing required fields' }, 400);
  }

  try {
    const ps = c.env.DB.prepare('SELECT * FROM Users WHERE username = ? AND password = ?').bind(username, password);
    const user = await ps.first<{ username: string }>();

    if (user) {
      // In a real application, you would generate a proper JWT.
      const token = 'mock-token-' + Date.now();
      const userResponse = { username: user.username, avatar: user.username.charAt(0).toUpperCase() };
      return c.json({ success: true, token, user: userResponse });
    } else {
      return c.json({ success: false, message: 'Invalid username or password' }, 401);
    }
  } catch (e: any) {
    return c.json({ success: false, message: 'Login failed', details: e.message }, 500);
  }
});

// Endpoint to get all products
app.get('/api/products', async (c) => {
  try {
    const ps = c.env.DB.prepare('SELECT * FROM Products ORDER BY product_name');
    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for the summary cards
// Uses Python script equivalent logic for accurate ratio calculation
app.get('/api/summary', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Calculate days between dates
    const startDate = new Date(start_date);
    const endDate = new Date(end_date);
    const timeDiff = endDate.getTime() - startDate.getTime();
    const days = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1;

    // Get total sales with Python script's exact filtering logic
    const salesQuery = `
      SELECT
        SUM(CASE
          WHEN p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%'
          THEN dm.sales_volume
          ELSE 0
        END) as total_sales
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.sales_volume IS NOT NULL
        AND dm.sales_volume > 0
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
    `;

    // Get total production with Python script's exact filtering logic
    const productionQuery = `
      SELECT
        SUM(CASE
          WHEN p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%'
          THEN dm.production_volume
          ELSE 0
        END) as total_production
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.production_volume IS NOT NULL
        AND dm.production_volume > 0
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
    `;

    // Get product count with filtering
    const productCountQuery = `
      SELECT COUNT(DISTINCT p.product_id) as total_products
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
    `;

    const salesPs = c.env.DB.prepare(salesQuery).bind(start_date, end_date);
    const productionPs = c.env.DB.prepare(productionQuery).bind(start_date, end_date);
    const productCountPs = c.env.DB.prepare(productCountQuery).bind(start_date, end_date);

    const salesResult = await salesPs.first<{ total_sales: number }>();
    const productionResult = await productionPs.first<{ total_production: number }>();
    const productCountResult = await productCountPs.first<{ total_products: number }>();

    const totalSales = salesResult?.total_sales || 0;
    const totalProduction = productionResult?.total_production || 0;
    const totalProducts = productCountResult?.total_products || 0;

    // Calculate ratio using Python script's logic
    let salesToProductionRatio = 0;
    if (totalProduction > 0) {
      salesToProductionRatio = (totalSales / totalProduction) * 100;
      // Apply Python script's ratio clipping logic (min(ratio, 500))
      salesToProductionRatio = Math.min(salesToProductionRatio, 500);
    }

    return c.json({
      total_products: totalProducts,
      days: days,
      total_sales: totalSales,
      total_production: totalProduction,
      sales_to_production_ratio: salesToProductionRatio,
      calculation_method: 'Python script equivalent'
    });
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for the top N inventory products chart
// Implements data filtering logic from original Python script
app.get('/api/inventory/top', async (c) => {
  const { date, limit = '15' } = c.req.query();

  if (!date) {
    return c.json({ error: 'Missing date query parameter' }, 400);
  }

  try {
    // Use centralized filtering logic (relaxed mode for inventory)
    const filterClause = ProductFilter.getCompleteFilter(false);

    // First get total inventory for percentage calculation
    const totalPs = c.env.DB.prepare(
      `SELECT SUM(dm.inventory_level) as total_inventory
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date = ?1
         AND dm.inventory_level IS NOT NULL
         AND dm.inventory_level > 0
         AND ${filterClause}`
    ).bind(date);

    const totalResult = await totalPs.first();
    const totalInventory = totalResult?.total_inventory || 0;

    const ps = c.env.DB.prepare(
      `SELECT
         p.product_name,
         dm.inventory_level,
         ROUND((dm.inventory_level * 100.0 / ?3), 2) as percentage,
         ROW_NUMBER() OVER (ORDER BY dm.inventory_level DESC) as rank
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date = ?1
         AND dm.inventory_level IS NOT NULL
         AND dm.inventory_level > 0
         AND ${filterClause}
       ORDER BY dm.inventory_level DESC
       LIMIT ?2`
    ).bind(date, parseInt(limit, 10), totalInventory);

    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for inventory summary statistics
app.get('/api/inventory/summary', async (c) => {
  const { date } = c.req.query();

  if (!date) {
    return c.json({ error: 'Missing date query parameter' }, 400);
  }

  try {
    // Use centralized filtering logic (relaxed mode for inventory)
    const filterClause = ProductFilter.getCompleteFilter(false);

    const ps = c.env.DB.prepare(
      `SELECT
         SUM(dm.inventory_level) as total_inventory,
         COUNT(DISTINCT p.product_id) as product_count
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date = ?1
         AND dm.inventory_level IS NOT NULL
         AND dm.inventory_level > 0
         AND ${filterClause}`
    ).bind(date);

    const summaryResult = await ps.first<{ total_inventory: number; product_count: number }>();

    // Get TOP15 total
    const top15Ps = c.env.DB.prepare(
      `SELECT SUM(inventory_level) as top15_total
       FROM (
         SELECT dm.inventory_level
         FROM DailyMetrics dm
         JOIN Products p ON dm.product_id = p.product_id
         WHERE dm.record_date = ?1
           AND dm.inventory_level IS NOT NULL
           AND dm.inventory_level > 0
           AND ${filterClause}
         ORDER BY dm.inventory_level DESC
         LIMIT 15
       )`
    ).bind(date);

    const top15Result = await top15Ps.first<{ top15_total: number }>();

    const totalInventory = summaryResult?.total_inventory || 0;
    const top15Total = top15Result?.top15_total || 0;
    const top15Percentage = totalInventory > 0 ? (top15Total / totalInventory * 100) : 0;

    return c.json({
      total_inventory: totalInventory,
      top15_total: top15Total,
      top15_percentage: Math.round(top15Percentage * 100) / 100,
      product_count: summaryResult?.product_count || 0
    });
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for inventory distribution (pie chart data)
app.get('/api/inventory/distribution', async (c) => {
  const { date, limit = '15' } = c.req.query();

  if (!date) {
    return c.json({ error: 'Missing date query parameter' }, 400);
  }

  try {
    // Use centralized filtering logic (relaxed mode for inventory)
    const filterClause = ProductFilter.getCompleteFilter(false);

    // Get total inventory for percentage calculation
    const totalPs = c.env.DB.prepare(
      `SELECT SUM(dm.inventory_level) as total_inventory
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date = ?1
         AND dm.inventory_level IS NOT NULL
         AND dm.inventory_level > 0
         AND ${filterClause}`
    ).bind(date);

    const totalResult = await totalPs.first();
    const totalInventory = totalResult?.total_inventory || 0;

    const ps = c.env.DB.prepare(
      `SELECT
         p.product_name,
         dm.inventory_level,
         ROUND((dm.inventory_level * 100.0 / ?3), 2) as percentage
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date = ?1
         AND dm.inventory_level IS NOT NULL
         AND dm.inventory_level > 0
         AND ${filterClause}
       ORDER BY dm.inventory_level DESC
       LIMIT ?2`
    ).bind(date, parseInt(limit, 10), totalInventory);

    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for inventory trends, including inventory level and turnover days
app.get('/api/inventory/trends', async (c) => {
  const { start_date, end_date, product_id } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }
  if (!product_id) {
    return c.json({ error: 'Missing product_id query parameter' }, 400);
  }

  try {
    const ps = c.env.DB.prepare(
      `SELECT
         record_date,
         inventory_level,
         inventory_turnover_days
       FROM DailyMetrics
       WHERE record_date BETWEEN ?1 AND ?2
         AND product_id = ?3
       ORDER BY record_date ASC`
    ).bind(start_date, end_date, parseInt(product_id, 10));

    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for the daily sales-to-production ratio trend chart
// Implements the exact logic from original Python script
app.get('/api/trends/ratio', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Step 1: Get sales data with Python script's exact filtering logic
    // Equivalent to load_sales_data() and process_sales_data() from Python script
    const salesQuery = `
      SELECT
        DATE(dm.record_date) as record_date,
        SUM(CASE
          WHEN p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%'
          THEN dm.sales_volume
          ELSE 0
        END) as daily_sales_volume
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.sales_volume IS NOT NULL
        AND dm.sales_volume > 0
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
      GROUP BY DATE(dm.record_date)
      ORDER BY record_date ASC
    `;

    // Step 2: Get production data with Python script's exact filtering logic
    // Equivalent to load_daily_production_data() from Python script
    const productionQuery = `
      SELECT
        DATE(dm.record_date) as record_date,
        SUM(CASE
          WHEN p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%'
          THEN dm.production_volume
          ELSE 0
        END) as daily_production_volume
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.production_volume IS NOT NULL
        AND dm.production_volume > 0
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
      GROUP BY DATE(dm.record_date)
      ORDER BY record_date ASC
    `;

    const salesPs = c.env.DB.prepare(salesQuery).bind(start_date, end_date);
    const productionPs = c.env.DB.prepare(productionQuery).bind(start_date, end_date);

    const { results: salesResults } = await salesPs.all();
    const { results: productionResults } = await productionPs.all();

    // Step 3: Combine sales and production data and calculate ratio
    // Equivalent to main.py lines 135-146
    const salesMap = new Map();
    const productionMap = new Map();

    salesResults.forEach((row: any) => {
      salesMap.set(row.record_date, row.daily_sales_volume || 0);
    });

    productionResults.forEach((row: any) => {
      productionMap.set(row.record_date, row.daily_production_volume || 0);
    });

    // Get all unique dates from both sales and production
    const allDates = new Set([...salesMap.keys(), ...productionMap.keys()]);
    const results = [];

    for (const date of Array.from(allDates).sort()) {
      const salesVol = salesMap.get(date) || 0;
      const prodVol = productionMap.get(date) || 0;
      
      // Apply Python script's exact calculation logic
      let ratio = 0;
      if (prodVol > 0) {
        ratio = (salesVol / prodVol) * 100;
        // Apply Python script's ratio clipping logic (min(ratio, 500))
        ratio = Math.min(ratio, 500);
      }

      results.push({
        record_date: date,
        daily_sales: salesVol,
        daily_production: prodVol,
        ratio: ratio,
        calculation_method: 'Python script equivalent'
      });
    }

    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for production ratio statistics (avg, min, max)
// Uses the same Python script equivalent logic as /api/trends/ratio
app.get('/api/production/ratio-stats', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Step 1: Get sales data with Python script's exact filtering logic
    const salesQuery = `
      SELECT
        DATE(dm.record_date) as record_date,
        SUM(CASE
          WHEN p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%'
          THEN dm.sales_volume
          ELSE 0
        END) as daily_sales_volume
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.sales_volume IS NOT NULL
        AND dm.sales_volume > 0
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
      GROUP BY DATE(dm.record_date)
    `;

    // Step 2: Get production data with Python script's exact filtering logic
    const productionQuery = `
      SELECT
        DATE(dm.record_date) as record_date,
        SUM(CASE
          WHEN p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%'
          THEN dm.production_volume
          ELSE 0
        END) as daily_production_volume
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.production_volume IS NOT NULL
        AND dm.production_volume > 0
        -- Apply Python script's filtering logic
        AND (
          -- Exclude fresh products except 凤肠
          (p.product_name NOT LIKE '鲜%' OR p.product_name LIKE '%凤肠%')
          -- Exclude by-products and fresh categories
          AND (p.category IS NULL OR p.category = '' OR p.category NOT IN ('副产品', '生鲜品其他'))
        )
      GROUP BY DATE(dm.record_date)
    `;

    const salesPs = c.env.DB.prepare(salesQuery).bind(start_date, end_date);
    const productionPs = c.env.DB.prepare(productionQuery).bind(start_date, end_date);

    const { results: salesResults } = await salesPs.all();
    const { results: productionResults } = await productionPs.all();

    // Step 3: Calculate statistics using Python script's logic
    const salesMap = new Map();
    const productionMap = new Map();

    salesResults.forEach((row: any) => {
      salesMap.set(row.record_date, row.daily_sales_volume || 0);
    });

    productionResults.forEach((row: any) => {
      productionMap.set(row.record_date, row.daily_production_volume || 0);
    });

    // Calculate daily ratios with Python script's logic
    const allDates = new Set([...salesMap.keys(), ...productionMap.keys()]);
    const dailyRatios: number[] = [];
    let totalSales = 0;
    let totalProduction = 0;

    for (const date of allDates) {
      const salesVol = salesMap.get(date) || 0;
      const prodVol = productionMap.get(date) || 0;
      
      totalSales += salesVol;
      totalProduction += prodVol;
      
      // Calculate daily ratio with Python script's logic
      if (prodVol > 0) {
        let ratio = (salesVol / prodVol) * 100;
        // Apply Python script's ratio clipping logic (min(ratio, 500))
        ratio = Math.min(ratio, 500);
        dailyRatios.push(ratio);
      }
    }

    // Calculate statistics
    const avgRatio = totalProduction > 0 ? Math.min((totalSales / totalProduction) * 100, 500) : 0;
    const minRatio = dailyRatios.length > 0 ? Math.min(...dailyRatios) : 0;
    const maxRatio = dailyRatios.length > 0 ? Math.max(...dailyRatios) : 0;

    return c.json({
      avg_ratio: avgRatio,
      min_ratio: minRatio,
      max_ratio: maxRatio,
      calculation_method: 'Python script equivalent',
      total_days: dailyRatios.length,
      total_sales: totalSales,
      total_production: totalProduction
    });
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Debug endpoint to check production ratio data
app.get('/api/debug/ratio-data', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    const filterClause = ProductFilter.getCompleteFilter(false);

    // Get summary data
    const summaryPs = c.env.DB.prepare(
      `SELECT
        SUM(dm.sales_volume) as total_sales,
        SUM(dm.production_volume) as total_production,
        (SUM(dm.sales_volume) / SUM(dm.production_volume)) * 100 as overall_ratio,
        COUNT(*) as total_records
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.sales_volume IS NOT NULL
        AND dm.production_volume IS NOT NULL
        AND dm.sales_volume > 0
        AND dm.production_volume > 0
        AND ${filterClause}`
    ).bind(start_date, end_date);

    // Get daily data sample
    const dailyPs = c.env.DB.prepare(
      `SELECT
        dm.record_date,
        dm.sales_volume,
        dm.production_volume,
        (dm.sales_volume / dm.production_volume) * 100 as daily_ratio,
        p.product_name
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.sales_volume IS NOT NULL
        AND dm.production_volume IS NOT NULL
        AND dm.sales_volume > 0
        AND dm.production_volume > 0
        AND ${filterClause}
      ORDER BY (dm.sales_volume / dm.production_volume) DESC
      LIMIT 10`
    ).bind(start_date, end_date);

    const summary = await summaryPs.first();
    const { results: dailySample } = await dailyPs.all();

    return c.json({
      summary,
      high_ratio_samples: dailySample,
      calculation_explanation: {
        overall_ratio: "总销售量 / 总产量 * 100",
        daily_ratio: "每日销售量 / 每日产量 * 100"
      }
    });
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for the dual-axis sales and price trend chart
// Applies data filtering logic from original Python script
app.get('/api/trends/sales-price', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Use centralized filtering logic (relaxed mode for trends)
    const filterClause = ProductFilter.getCompleteFilter(false);

    const ps = c.env.DB.prepare(
      `SELECT
         dm.record_date,
         SUM(dm.sales_volume) as total_sales,
         SUM(dm.sales_amount) as total_amount,
         CASE
           WHEN SUM(dm.sales_volume) > 0
           THEN SUM(dm.sales_amount) / SUM(dm.sales_volume)
           ELSE 0
         END as avg_price
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date BETWEEN ?1 AND ?2
         AND dm.sales_volume IS NOT NULL
         AND dm.sales_volume > 0
         AND ${filterClause}
       GROUP BY dm.record_date
       ORDER BY dm.record_date ASC`
    ).bind(start_date, end_date);

    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint to get price change records with filtering
// Implements the same logic as the original Python script's PriceAnalyzer
app.get('/api/price-changes', async (c) => {
  const { start_date, end_date, min_price_diff = '200' } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Use centralized filtering logic (relaxed mode for consistency)
    const filterClause = ProductFilter.getPriceAdjustmentFilter(false);

    const ps = c.env.DB.prepare(
      `SELECT
         pa.adjustment_date,
         pa.product_name,
         pa.specification,
         pa.adjustment_count,
         pa.previous_price,
         pa.current_price,
         pa.price_difference,
         pa.category
       FROM PriceAdjustments pa
       JOIN Products p ON pa.product_id = p.product_id
       WHERE pa.adjustment_date BETWEEN ?1 AND ?2
         AND ABS(pa.price_difference) >= ?3
         AND ${filterClause}
       ORDER BY pa.adjustment_date DESC, ABS(pa.price_difference) DESC`
    ).bind(start_date, end_date, parseFloat(min_price_diff));

    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint to get price trend data for charts
app.get('/api/price-trends', async (c) => {
  const { start_date, end_date, product_name } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Use centralized filtering logic (relaxed mode for consistency)
    const filterClause = ProductFilter.getPriceAdjustmentFilter(false);

    let query = `
      SELECT
        pa.adjustment_date,
        pa.product_name,
        pa.current_price,
        pa.price_difference
      FROM PriceAdjustments pa
      JOIN Products p ON pa.product_id = p.product_id
      WHERE pa.adjustment_date BETWEEN ?1 AND ?2
        AND ${filterClause}
    `;

    const params = [start_date, end_date];

    if (product_name) {
      query += ` AND pa.product_name = ?3`;
      params.push(product_name);
    }

    query += ` ORDER BY pa.adjustment_date ASC`;

    const ps = c.env.DB.prepare(query).bind(...params);
    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for processing price adjustment Excel files (调价表.xlsx)
// Implements the same logic as the original Python script's DataLoader.preprocess_sheet
app.post('/api/upload/price-adjustments', async (c) => {
  try {
    const formData = await c.req.formData();
    const file = formData.get('file');

    if (!file || !(file instanceof File)) {
      return c.json({ error: 'No file uploaded' }, 400);
    }

    const buffer = await file.arrayBuffer();
    const workbook = XLSX.read(buffer, { type: 'buffer' });
    const db = c.env.DB;

    let processedRecords = 0;
    const errors: string[] = [];

    // Process each sheet (following original Python logic)
    for (const sheetName of workbook.SheetNames) {
      try {
        // Extract date info from sheet name (价格表4月2号（2）)
        const dateMatch = sheetName.match(/价格表(\d+)月(\d+)号(?:（(\d+)）)?/);
        if (!dateMatch) {
          errors.push(`Cannot extract date from sheet name: ${sheetName}`);
          continue;
        }

        const month = parseInt(dateMatch[1]);
        const day = parseInt(dateMatch[2]);
        const adjustmentCount = parseInt(dateMatch[3]) || 1;
        const adjustmentDate = `2025-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;

        const worksheet = workbook.Sheets[sheetName];
        const rawData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        if (!rawData || rawData.length === 0) {
          continue;
        }

        // Process three templates side by side (columns 0-8, 9-17, 18-26)
        const templates = [
          { start: 0, end: 9 },
          { start: 9, end: 18 },
          { start: 18, end: 27 }
        ];

        const stmts: any[] = [];

        for (const template of templates) {
          for (let i = 1; i < rawData.length; i++) { // Skip header row
            const row = rawData[i] as any[];
            if (!row || row.length <= template.start) continue;

            const category = row[template.start];
            const productName = row[template.start + 1];
            const specification = row[template.start + 2];
            const previousPrice = parseFloat(row[template.start + 7]) || null; // 加工二厂-前价格
            const currentPrice = parseFloat(row[template.start + 8]) || null;   // 加工二厂-价格

            // Skip invalid rows
            if (!productName ||
                typeof productName !== 'string' ||
                productName.includes('均价') ||
                productName.includes('品名') ||
                !currentPrice) {
              continue;
            }

            const priceDifference = previousPrice ? currentPrice - previousPrice : 0;

            // Find or create product
            const productQuery = db.prepare('SELECT product_id FROM Products WHERE product_name = ?').bind(productName);
            let productResult = await productQuery.first<{ product_id: number }>();

            if (!productResult) {
              const insertProduct = db.prepare('INSERT INTO Products (product_name, category) VALUES (?, ?) RETURNING product_id')
                .bind(productName, category || null);
              productResult = await insertProduct.first<{ product_id: number }>();
            }
            
            if (!productResult) {
              errors.push(`Failed to find or create product: ${productName}`);
              continue;
            }

            const productId = productResult.product_id;

            // Insert price adjustment record
            const stmt = db.prepare(`
              INSERT INTO PriceAdjustments
              (adjustment_date, product_id, product_name, specification, adjustment_count,
               previous_price, current_price, price_difference, category)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            `).bind(
              adjustmentDate,
              productId,
              productName,
              specification || null,
              adjustmentCount,
              previousPrice,
              currentPrice,
              priceDifference,
              category || null
            );

            stmts.push(stmt);
          }
        }

        if (stmts.length > 0) {
          await db.batch(stmts);
          processedRecords += stmts.length;
        }

      } catch (sheetError: any) {
        errors.push(`Error processing sheet ${sheetName}: ${sheetError.message}`);
      }
    }

    return c.json({
      message: 'Price adjustment data processed successfully',
      processedRecords,
      errors: errors.length > 0 ? errors : undefined
    });

  } catch (e: any) {
    console.error('Price adjustment upload error:', e);
    return c.json({ error: 'Internal server error', details: e.message }, 500);
  }
});

// --- Data Validation Layer ---

/**
 * Data validation utilities for upload endpoints
 */
class DataValidator {
  /**
   * Validate DailyMetrics row data
   */
  static validateDailyMetricsRow(row: any): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Required fields validation
    if (!row.product_id || isNaN(parseInt(row.product_id))) {
      errors.push('Invalid or missing product_id');
    }

    if (!row.record_date) {
      errors.push('Missing record_date');
    } else {
      // Validate date format
      const date = new Date(row.record_date);
      if (isNaN(date.getTime())) {
        errors.push('Invalid record_date format');
      }
    }

    // Numeric fields validation (allow null/undefined for optional fields)
    const numericFields = ['production_volume', 'sales_volume', 'inventory_level', 'average_price'];
    for (const field of numericFields) {
      if (row[field] !== null && row[field] !== undefined && row[field] !== '') {
        const value = parseFloat(row[field]);
        if (isNaN(value) || value < 0) {
          errors.push(`Invalid ${field}: must be a non-negative number`);
        }
      }
    }

    return { isValid: errors.length === 0, errors };
  }

  /**
   * Sanitize and clean row data
   */
  static sanitizeDailyMetricsRow(row: any): any {
    return {
      product_id: parseInt(row.product_id),
      record_date: row.record_date,
      production_volume: row.production_volume ? parseFloat(row.production_volume) : null,
      sales_volume: row.sales_volume ? parseFloat(row.sales_volume) : null,
      inventory_level: row.inventory_level ? parseFloat(row.inventory_level) : null,
      average_price: row.average_price ? parseFloat(row.average_price) : null
    };
  }
}

// Endpoint for handling Excel file uploads with enhanced validation
app.post('/api/upload', async (c) => {
  try {
    const formData = await c.req.formData();
    const file = formData.get('file');

    if (!file || !(file instanceof File)) {
      return c.json({ error: 'No file uploaded' }, 400);
    }

    const buffer = await file.arrayBuffer();
    const workbook = XLSX.read(buffer, { type: 'buffer' });
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const rows = XLSX.utils.sheet_to_json(worksheet);

    if (rows.length === 0) {
      return c.json({ error: 'Excel file is empty or in the wrong format' }, 400);
    }

    const db = c.env.DB;
    const validRows: any[] = [];
    const errors: string[] = [];

    // Validate and sanitize each row
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const validation = DataValidator.validateDailyMetricsRow(row);

      if (validation.isValid) {
        validRows.push(DataValidator.sanitizeDailyMetricsRow(row));
      } else {
        errors.push(`Row ${i + 1}: ${validation.errors.join(', ')}`);
      }
    }

    // If too many errors, reject the upload
    if (errors.length > rows.length * 0.1) { // Allow up to 10% error rate
      return c.json({
        error: 'Too many validation errors in uploaded data',
        details: errors.slice(0, 10), // Show first 10 errors
        totalErrors: errors.length,
        totalRows: rows.length
      }, 400);
    }

    if (validRows.length === 0) {
      return c.json({ error: 'No valid rows found in uploaded data' }, 400);
    }

    // Prepare batch insert statements
    const stmts = validRows.map(row => {
      return db.prepare(
        'INSERT INTO DailyMetrics (product_id, record_date, production_volume, sales_volume, inventory_level, average_price) VALUES (?, ?, ?, ?, ?, ?)'
      ).bind(
        row.product_id,
        row.record_date,
        row.production_volume,
        row.sales_volume,
        row.inventory_level,
        row.average_price
      );
    });

    const batchResult = await db.batch(stmts);

    return c.json({
      message: 'Upload successful',
      results: batchResult,
      processedRows: validRows.length,
      skippedRows: errors.length,
      errors: errors.length > 0 ? errors.slice(0, 5) : undefined // Show first 5 errors if any
    });

  } catch (e: any) {
    console.error('Upload error:', e);
    return c.json({ error: 'Internal server error', details: e.message }, 500);
  }
});

// Admin endpoint for batch data import
app.post('/api/admin/import-batch', async (c) => {
  try {
    const { data } = await c.req.json();

    if (!Array.isArray(data)) {
      return c.json({ error: 'Data must be an array' }, 400);
    }

    // Prepare batch insert
    const stmt = c.env.DB.prepare(`
      INSERT INTO DailyMetrics (
        record_date, product_id, production_volume, sales_volume,
        inventory_level, average_price, sales_amount
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    // Execute batch insert
    const results = [];
    for (const record of data) {
      try {
        const result = await stmt.bind(
          record.record_date,
          record.product_id,
          record.production_volume,
          record.sales_volume,
          record.inventory_level,
          record.average_price,
          record.sales_amount
        ).run();
        results.push(result);
      } catch (e: any) {
        console.error('Insert error:', e.message);
        // Continue with other records
      }
    }

    return c.json({
      success: true,
      inserted: results.length,
      total: data.length
    });
  } catch (e: any) {
    return c.json({ error: 'Import failed', details: e.message }, 500);
  }
});

export default app;
