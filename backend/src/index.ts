import { Hono } from 'hono';
import { cors } from 'hono/cors';
import * as XLSX from 'xlsx';

// Define the bindings for Cloudflare environment variables
type Bindings = {
  DB: D1Database;
};

const app = new Hono<{ Bindings: Bindings }>();

// Apply CORS middleware with specific configuration
app.use('/*', cors({
  origin: ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:8080'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Accept', 'Authorization'],
  exposeHeaders: ['Content-Length', 'X-Requested-With'],
  credentials: false,
  maxAge: 86400, // 24 hours
}));

// Add explicit OPTIONS handler for preflight requests
app.options('/*', (c) => {
  return c.text('', 200);
});

// --- API Endpoints ---

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
app.get('/api/summary', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    const query = `
      SELECT
        COUNT(DISTINCT p.product_id) as total_products,
        CAST(JULIANDAY(?) - JULIANDAY(?) + 1 AS INTEGER) as days,
        SUM(dm.sales_volume) as total_sales,
        SUM(dm.production_volume) as total_production,
        (SUM(dm.sales_volume) / SUM(dm.production_volume)) * 100 as sales_to_production_ratio
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ? AND ?;
    `;
    const ps = c.env.DB.prepare(query).bind(end_date, start_date, start_date, end_date);
    const data = await ps.first();

    return c.json(data);
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
    // Apply data filtering logic from original Python script:
    // 1. Filter out fresh products (starting with '鲜')
    // 2. Filter out by-products and empty categories
    // 3. Special handling for '凤肠' products (keep them)
    const ps = c.env.DB.prepare(
      `SELECT
         p.product_name,
         dm.inventory_level
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date = ?1
         AND dm.inventory_level IS NOT NULL
         AND dm.inventory_level > 0
         AND (
           -- Keep products that don't start with '鲜' (fresh products)
           p.product_name NOT LIKE '鲜%'
           OR
           -- Special exception: keep '凤肠' products even if they contain '鲜'
           p.product_name LIKE '%凤肠%'
         )
         AND (
           -- Filter out by-products and empty categories (if category exists)
           p.category IS NULL
           OR p.category = ''
           OR p.category NOT IN ('副产品', '生鲜品其他')
         )
       ORDER BY dm.inventory_level DESC
       LIMIT ?2`
    ).bind(date, parseInt(limit, 10));

    const { results } = await ps.all();
    return c.json(results);
  } catch (e: any) {
    return c.json({ error: 'Database query failed', details: e.message }, 500);
  }
});

// Endpoint for the daily sales-to-production ratio trend chart
// Applies data filtering logic from original Python script
app.get('/api/trends/ratio', async (c) => {
  const { start_date, end_date } = c.req.query();

  if (!start_date || !end_date) {
    return c.json({ error: 'Missing start_date or end_date query parameters' }, 400);
  }

  try {
    // Apply consistent data filtering logic from original Python script
    const ps = c.env.DB.prepare(
      `SELECT
        dm.record_date,
        (SUM(dm.sales_volume) / SUM(dm.production_volume)) * 100 as ratio
      FROM DailyMetrics dm
      JOIN Products p ON dm.product_id = p.product_id
      WHERE dm.record_date BETWEEN ?1 AND ?2
        AND dm.sales_volume IS NOT NULL
        AND dm.production_volume IS NOT NULL
        AND dm.sales_volume > 0
        AND dm.production_volume > 0
        AND (
          -- Filter out fresh products (starting with '鲜')
          p.product_name NOT LIKE '鲜%'
          OR
          -- Special exception: keep '凤肠' products
          p.product_name LIKE '%凤肠%'
        )
        AND (
          -- Filter out by-products and empty categories (if category exists)
          p.category IS NULL
          OR p.category = ''
          OR p.category NOT IN ('副产品', '生鲜品其他')
        )
      GROUP BY dm.record_date
      ORDER BY dm.record_date ASC`
    ).bind(start_date, end_date);

    const { results } = await ps.all();
    return c.json(results);
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
    // Apply consistent data filtering logic from original Python script
    const ps = c.env.DB.prepare(
      `SELECT
         dm.record_date,
         SUM(dm.sales_volume) as total_sales,
         AVG(dm.average_price) as avg_price
       FROM DailyMetrics dm
       JOIN Products p ON dm.product_id = p.product_id
       WHERE dm.record_date BETWEEN ?1 AND ?2
         AND dm.sales_volume IS NOT NULL
         AND dm.sales_volume > 0
         AND (
           -- Filter out fresh products (starting with '鲜')
           p.product_name NOT LIKE '鲜%'
           OR
           -- Special exception: keep '凤肠' products
           p.product_name LIKE '%凤肠%'
         )
         AND (
           -- Filter out by-products and empty categories (if category exists)
           p.category IS NULL
           OR p.category = ''
           OR p.category NOT IN ('副产品', '生鲜品其他')
         )
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
    // Apply the same filtering logic from original Python script:
    // 1. Filter out fresh products (starting with '鲜')
    // 2. Filter out by-products and empty categories
    // 3. Special handling for '凤肠' products (keep them)
    // 4. Only show significant price changes (≥ threshold)
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
         AND (
           -- Filter out fresh products (starting with '鲜')
           pa.product_name NOT LIKE '鲜%'
           OR
           -- Special exception: keep '凤肠' products
           pa.product_name LIKE '%凤肠%'
         )
         AND (
           -- Filter out by-products and empty categories
           pa.category IS NOT NULL
           AND pa.category != ''
           AND pa.category NOT IN ('副产品', '生鲜品其他')
         )
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
    let query = `
      SELECT
        pa.adjustment_date,
        pa.product_name,
        pa.current_price,
        pa.price_difference
      FROM PriceAdjustments pa
      JOIN Products p ON pa.product_id = p.product_id
      WHERE pa.adjustment_date BETWEEN ?1 AND ?2
        AND (
          -- Apply same filtering logic
          pa.product_name NOT LIKE '鲜%'
          OR pa.product_name LIKE '%凤肠%'
        )
        AND (
          pa.category IS NOT NULL
          AND pa.category != ''
          AND pa.category NOT IN ('副产品', '生鲜品其他')
        )
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
            let productResult = await productQuery.first();

            if (!productResult) {
              const insertProduct = db.prepare('INSERT INTO Products (product_name, category) VALUES (?, ?) RETURNING product_id')
                .bind(productName, category || null);
              productResult = await insertProduct.first();
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

// Endpoint for handling Excel file uploads
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

    // In a real-world scenario, you would perform more robust data cleaning and validation here.
    // This example assumes the Excel columns match the database fields.

    const stmts = rows.map(row => {
        const { product_id, record_date, production_volume, sales_volume, inventory_level, average_price } = row as any;
        return db.prepare(
          'INSERT INTO DailyMetrics (product_id, record_date, production_volume, sales_volume, inventory_level, average_price) VALUES (?, ?, ?, ?, ?, ?)'
        ).bind(product_id, record_date, production_volume, sales_volume, inventory_level, average_price);
      });

    const batchResult = await db.batch(stmts);

    return c.json({ message: 'Upload successful', results: batchResult });

  } catch (e: any) {
    console.error('Upload error:', e);
    return c.json({ error: 'Internal server error', details: e.message }, 500);
  }
});

export default app;
