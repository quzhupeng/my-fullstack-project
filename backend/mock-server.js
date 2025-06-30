const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 8787;

// Enable CORS for all routes - very permissive for development
app.use(cors({
  origin: true, // Allow all origins
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Accept', 'Authorization'],
  credentials: false
}));

app.use(express.json());

// Mock data generators
function generateMockProducts() {
  return [
    { product_id: 1, product_name: '鸡大胸', category: '分割品' },
    { product_id: 2, product_name: '鸡小胸', category: '分割品' },
    { product_id: 3, product_name: '鸡腿肉', category: '分割品' },
    { product_id: 4, product_name: '鸡翅中', category: '分割品' },
    { product_id: 5, product_name: '鸡翅根', category: '分割品' },
    { product_id: 6, product_name: '鸡爪', category: '分割品' },
    { product_id: 7, product_name: '鸡胗', category: '副产品' },
    { product_id: 8, product_name: '鸡心', category: '副产品' },
    { product_id: 9, product_name: '鸡肝', category: '副产品' },
    { product_id: 10, product_name: '整鸡', category: '白条鸡' }
  ];
}

function generateMockInventoryData() {
  const products = generateMockProducts();
  return products.slice(0, 15).map((product, index) => ({
    product_name: product.product_name,
    inventory_level: Math.random() * 1000 + 100, // Random inventory between 100-1100 tons
    category: product.category
  })).sort((a, b) => b.inventory_level - a.inventory_level);
}

function generateMockSalesPriceData(startDate, endDate) {
  const data = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0];
    data.push({
      record_date: dateStr,
      total_sales: Math.random() * 500 + 200, // Random sales between 200-700 tons
      avg_price: Math.random() * 2000 + 8000  // Random price between 8000-10000 yuan/ton
    });
  }
  
  return data;
}

function generateMockRatioData(startDate, endDate) {
  const data = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    const dateStr = d.toISOString().split('T')[0];
    data.push({
      record_date: dateStr,
      ratio: Math.random() * 150 + 50 // Random ratio between 50-200%
    });
  }
  
  return data;
}

function generateMockSummaryData() {
  return {
    total_products: 10,
    days: 26,
    total_sales: 12500.5,
    total_production: 13200.8,
    sales_to_production_ratio: 94.7
  };
}

// API Routes
app.get('/api/products', (req, res) => {
  console.log('📦 GET /api/products');
  res.json(generateMockProducts());
});

app.get('/api/inventory/top', (req, res) => {
  const { date, limit = 15 } = req.query;
  console.log(`📊 GET /api/inventory/top?date=${date}&limit=${limit}`);
  const data = generateMockInventoryData().slice(0, parseInt(limit));
  res.json(data);
});

app.get('/api/trends/sales-price', (req, res) => {
  const { start_date, end_date } = req.query;
  console.log(`📈 GET /api/trends/sales-price?start_date=${start_date}&end_date=${end_date}`);
  
  if (!start_date || !end_date) {
    return res.status(400).json({ error: 'Missing start_date or end_date' });
  }
  
  const data = generateMockSalesPriceData(start_date, end_date);
  res.json(data);
});

app.get('/api/trends/ratio', (req, res) => {
  const { start_date, end_date } = req.query;
  console.log(`📊 GET /api/trends/ratio?start_date=${start_date}&end_date=${end_date}`);
  
  if (!start_date || !end_date) {
    return res.status(400).json({ error: 'Missing start_date or end_date' });
  }
  
  const data = generateMockRatioData(start_date, end_date);
  res.json(data);
});

app.get('/api/summary', (req, res) => {
  const { start_date, end_date } = req.query;
  console.log(`📋 GET /api/summary?start_date=${start_date}&end_date=${end_date}`);
  
  if (!start_date || !end_date) {
    return res.status(400).json({ error: 'Missing start_date or end_date' });
  }
  
  const data = generateMockSummaryData();
  res.json(data);
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'Spring Snow Mock API Server is running' });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Spring Snow Mock API Server running on http://localhost:${PORT}`);
  console.log(`📊 Available endpoints:`);
  console.log(`   GET /api/products`);
  console.log(`   GET /api/inventory/top?date=YYYY-MM-DD&limit=15`);
  console.log(`   GET /api/trends/sales-price?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`);
  console.log(`   GET /api/trends/ratio?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`);
  console.log(`   GET /api/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`);
  console.log(`   GET /health`);
});
