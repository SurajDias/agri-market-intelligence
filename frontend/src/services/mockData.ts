// ============================================
// AGRIMARK AI — Realistic Mock Data
// All values based on Karnataka/India agri markets
// ============================================

import type {
  Commodity, Market, PriceRecord, ForecastPoint,
  Forecast, MarketComparison, Recommendation,
  DataQuality, InsightCard, User
} from '../types';

// ---- Commodities ----
export const COMMODITIES: Commodity[] = [
  { id: 'tomato', name: 'Tomato', nameHindi: 'टमाटर', category: 'Vegetables', unit: 'quintal', shelfLifeDays: 7 },
  { id: 'onion', name: 'Onion', nameHindi: 'प्याज', category: 'Vegetables', unit: 'quintal', shelfLifeDays: 60 },
  { id: 'potato', name: 'Potato', nameHindi: 'आलू', category: 'Vegetables', unit: 'quintal', shelfLifeDays: 90 },
  { id: 'chilli', name: 'Chilli (Dry)', nameHindi: 'मिर्च', category: 'Spices', unit: 'quintal', shelfLifeDays: 180 },
  { id: 'maize', name: 'Maize', nameHindi: 'मक्का', category: 'Cereals', unit: 'quintal', shelfLifeDays: 365 },
  { id: 'banana', name: 'Banana', nameHindi: 'केला', category: 'Fruits', unit: 'quintal', shelfLifeDays: 5 },
  { id: 'groundnut', name: 'Groundnut', nameHindi: 'मूंगफली', category: 'Oilseeds', unit: 'quintal', shelfLifeDays: 180 },
  { id: 'paddy', name: 'Paddy (Rice)', nameHindi: 'धान', category: 'Cereals', unit: 'quintal', shelfLifeDays: 365 },
];

// ---- Karnataka Markets ----
export const MARKETS: Market[] = [
  { id: 'ramanagara', name: 'Ramanagara', state: 'Karnataka', district: 'Ramanagara', lat: 12.7177, lng: 77.2820, type: 'APMC', isActive: true },
  { id: 'kolar', name: 'Kolar', state: 'Karnataka', district: 'Kolar', lat: 13.1368, lng: 78.1325, type: 'eNAM', isActive: true },
  { id: 'bengaluru', name: 'Bengaluru (KIADB)', state: 'Karnataka', district: 'Bengaluru Urban', lat: 12.9716, lng: 77.5946, type: 'Wholesale', isActive: true },
  { id: 'mysuru', name: 'Mysuru', state: 'Karnataka', district: 'Mysuru', lat: 12.2958, lng: 76.6394, type: 'APMC', isActive: true },
  { id: 'tumakuru', name: 'Tumakuru', state: 'Karnataka', district: 'Tumakuru', lat: 13.3393, lng: 77.1014, type: 'APMC', isActive: true },
  { id: 'mandya', name: 'Mandya', state: 'Karnataka', district: 'Mandya', lat: 12.5218, lng: 76.8951, type: 'APMC', isActive: true },
  { id: 'hassan', name: 'Hassan', state: 'Karnataka', district: 'Hassan', lat: 13.0068, lng: 76.1004, type: 'APMC', isActive: true },
  { id: 'chikkaballapur', name: 'Chikkaballapur', state: 'Karnataka', district: 'Chikkaballapur', lat: 13.4356, lng: 77.7272, type: 'eNAM', isActive: true },
];

// ---- Generate price history (last 30 days) ----
function generatePriceHistory(
  basePrice: number,
  volatility: number,
  days: number = 30
): PriceRecord[] {
  const records: PriceRecord[] = [];
  const today = new Date();
  let price = basePrice;

  for (let i = days; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const change = (Math.random() - 0.48) * volatility;
    price = Math.max(basePrice * 0.6, Math.min(basePrice * 1.5, price + change));

    records.push({
      date: date.toISOString().split('T')[0],
      market: 'ramanagara',
      commodity: 'tomato',
      minPrice: Math.round(price * 0.88),
      maxPrice: Math.round(price * 1.12),
      modalPrice: Math.round(price),
      arrivals: Math.round(120 + Math.random() * 80),
      unit: 'quintal',
    });
  }
  return records;
}

// ---- Generate forecast points ----
function generateForecastPoints(
  history: PriceRecord[],
  forecastDays: number = 7
): ForecastPoint[] {
  const points: ForecastPoint[] = history.map(h => ({
    date: h.date,
    predictedPrice: h.modalPrice,
    lowerBound: h.minPrice,
    upperBound: h.maxPrice,
    isForecasted: false,
  }));

  const lastPrice = history[history.length - 1]?.modalPrice ?? 2800;
  const trend = 35; // upward trend

  const today = new Date();
  for (let i = 1; i <= forecastDays; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const predicted = Math.round(lastPrice + trend * i + (Math.random() - 0.4) * 60);
    const uncertainty = Math.round(predicted * 0.06 * Math.sqrt(i));

    points.push({
      date: date.toISOString().split('T')[0],
      predictedPrice: predicted,
      lowerBound: predicted - uncertainty,
      upperBound: predicted + uncertainty,
      isForecasted: true,
    });
  }
  return points;
}

// ---- Tomato price history ----
export const TOMATO_HISTORY: PriceRecord[] = generatePriceHistory(2700, 80);
export const TOMATO_FORECAST_POINTS: ForecastPoint[] = generateForecastPoints(TOMATO_HISTORY);

export const MOCK_FORECAST: Forecast = {
  commodity: 'Tomato',
  market: 'Ramanagara',
  currentPrice: 2840,
  predictedPrice: 3080,
  changePercent: 8.45,
  changeAbsolute: 240,
  horizon: 7,
  confidence: 87,
  accuracy: 83,
  dataPoints: TOMATO_FORECAST_POINTS,
  generatedAt: new Date().toISOString(),
};

// ---- Market Comparisons ----
export const MOCK_MARKET_COMPARISONS: MarketComparison[] = [
  {
    market: MARKETS[0], // Ramanagara
    currentPrice: 3180,
    forecastPrice: 3380,
    transportCostPerQ: 75,
    transportDistance: 48,
    expectedRevenue: 159000,
    expectedNetProfit: 143500,
    expectedNetProfitPerQ: 143.5,
    risk: 'LOW',
    confidence: 87,
    trend: 'UP',
    priceChange: 8.2,
    arrivals: 145,
    isRecommended: true,
  },
  {
    market: MARKETS[1], // Kolar
    currentPrice: 3050,
    forecastPrice: 3180,
    transportCostPerQ: 90,
    transportDistance: 65,
    expectedRevenue: 152500,
    expectedNetProfit: 138000,
    expectedNetProfitPerQ: 138.0,
    risk: 'MEDIUM',
    confidence: 79,
    trend: 'UP',
    priceChange: 4.3,
    arrivals: 98,
    isRecommended: false,
  },
  {
    market: MARKETS[2], // Bengaluru
    currentPrice: 2950,
    forecastPrice: 3100,
    transportCostPerQ: 120,
    transportDistance: 92,
    expectedRevenue: 147500,
    expectedNetProfit: 131500,
    expectedNetProfitPerQ: 131.5,
    risk: 'MEDIUM',
    confidence: 74,
    trend: 'STABLE',
    priceChange: 1.8,
    arrivals: 320,
    isRecommended: false,
  },
  {
    market: MARKETS[3], // Mysuru
    currentPrice: 2780,
    forecastPrice: 2900,
    transportCostPerQ: 105,
    transportDistance: 82,
    expectedRevenue: 139000,
    expectedNetProfit: 123500,
    expectedNetProfitPerQ: 123.5,
    risk: 'HIGH',
    confidence: 61,
    trend: 'DOWN',
    priceChange: -3.2,
    arrivals: 76,
    isRecommended: false,
  },
  {
    market: MARKETS[4], // Tumakuru
    currentPrice: 2900,
    forecastPrice: 3050,
    transportCostPerQ: 95,
    transportDistance: 72,
    expectedRevenue: 145000,
    expectedNetProfit: 130500,
    expectedNetProfitPerQ: 130.5,
    risk: 'MEDIUM',
    confidence: 70,
    trend: 'UP',
    priceChange: 2.9,
    arrivals: 88,
    isRecommended: false,
  },
];

// ---- Recommendation ----
export const MOCK_RECOMMENDATION: Recommendation = {
  id: 'rec-001',
  commodity: 'Tomato',
  quantity: 5000,
  origin: 'Mandya',
  sellingDate: (() => {
    const d = new Date(); d.setDate(d.getDate() + 2); return d.toISOString().split('T')[0];
  })(),
  recommendedMarket: MARKETS[0],
  expectedPrice: 3180,
  grossRevenue: 159000,
  transportCost: 7500,
  netRevenue: 143500,
  netProfitPerQ: 143.5,
  confidence: 87,
  risk: 'LOW',
  sellingWindowDays: 3,
  sellingWindowLabel: 'Next 2–3 days',
  factors: [
    { name: 'Price Forecast', weight: 42, score: 88, impact: 'POSITIVE', explanation: 'Forecasted price is ₹240/q higher than current market average, indicating strong near-term demand.' },
    { name: 'Transport Cost', weight: 28, score: 82, impact: 'POSITIVE', explanation: 'At 48 km, Ramanagara offers the lowest transportation cost among shortlisted markets.' },
    { name: 'Shelf Life', weight: 15, score: 75, impact: 'POSITIVE', explanation: 'Remaining shelf life of 5 days comfortably covers the 2–3 day selling window.' },
    { name: 'Historical Volatility', weight: 9, score: 71, impact: 'NEUTRAL', explanation: 'Market shows moderate price volatility within acceptable range for LOW risk classification.' },
    { name: 'Market Demand', weight: 6, score: 68, impact: 'POSITIVE', explanation: 'Arrivals data indicates healthy demand with 145 tonnes daily throughput.' },
  ],
  alternatives: MOCK_MARKET_COMPARISONS.slice(1),
  insights: [
    'Tomato prices are expected to rise 8.2% over the next 7 days due to reduced supply from Kolar region.',
    'Ramanagara currently offers the highest expected net revenue among 5 analysed markets.',
    'Transport costs are ₹45/q lower at Ramanagara vs. Bengaluru KIADB despite similar forecast prices.',
    'Shelf life allows delay of up to 3 days without quality loss; selling on Day 2 maximises forecast price capture.',
  ],
  generatedAt: new Date().toISOString(),
};

// ---- Data Quality ----
export const MOCK_DATA_QUALITY: DataQuality = {
  overallScore: 94,
  recordsProcessed: 847293,
  missingValues: 12847,
  duplicateRecords: 3421,
  marketsCount: 24,
  commoditiesCount: 18,
  lastUpdated: new Date().toISOString(),
  sources: [
    {
      id: 'agmarknet',
      name: 'AGMARKNET',
      url: 'https://agmarknet.gov.in',
      status: 'FRESH',
      recordsTotal: 621840,
      lastUpdated: new Date().toISOString(),
      qualityScore: 96,
      missingValues: 8234,
      duplicates: 1890,
    },
    {
      id: 'datagov',
      name: 'data.gov.in',
      url: 'https://data.gov.in',
      status: 'FRESH',
      recordsTotal: 198453,
      lastUpdated: (() => { const d = new Date(); d.setHours(d.getHours() - 2); return d.toISOString(); })(),
      qualityScore: 91,
      missingValues: 4613,
      duplicates: 1531,
    },
    {
      id: 'weather',
      name: 'IMD Weather Data',
      url: 'https://mausam.imd.gov.in',
      status: 'STALE',
      recordsTotal: 24000,
      lastUpdated: (() => { const d = new Date(); d.setDate(d.getDate() - 1); return d.toISOString(); })(),
      qualityScore: 88,
      missingValues: 0,
      duplicates: 0,
    },
    {
      id: 'roads',
      name: 'Road Distance API',
      url: 'https://maps.roads.gov.in',
      status: 'FRESH',
      recordsTotal: 3000,
      lastUpdated: (() => { const d = new Date(); d.setDate(d.getDate() - 7); return d.toISOString(); })(),
      qualityScore: 99,
      missingValues: 0,
      duplicates: 0,
    },
  ],
};

// ---- Insights ----
export const MOCK_INSIGHTS: InsightCard[] = [
  {
    id: 'ins-001',
    type: 'OPPORTUNITY',
    title: 'Tomato price surge expected',
    body: 'Tomato prices are forecast to rise 8.2% over the next 7 days. Ramanagara offers the highest net revenue at ₹3,180/q.',
    commodity: 'Tomato',
    market: 'Ramanagara',
    impact: '+₹240/q vs current price',
    generatedAt: new Date().toISOString(),
  },
  {
    id: 'ins-002',
    type: 'RISK',
    title: 'Mysuru market showing weakness',
    body: 'Mysuru mandi prices have declined 3.2% over the past week. High arrivals are suppressing modal prices. Recommend avoiding.',
    commodity: 'Tomato',
    market: 'Mysuru',
    impact: '-₹420/q vs best market',
    generatedAt: new Date().toISOString(),
  },
  {
    id: 'ins-003',
    type: 'INFO',
    title: 'Chilli prices stabilising post-monsoon',
    body: 'Dry chilli arrivals in Byadagi and Hubli are normalising after the monsoon disruption. Price volatility is falling.',
    commodity: 'Chilli (Dry)',
    impact: 'Moderate risk profile',
    generatedAt: new Date().toISOString(),
  },
  {
    id: 'ins-004',
    type: 'ALERT',
    title: 'Transport route advisory',
    body: 'NH 48 (Mandya–Bengaluru) corridor congestion expected this weekend due to road work. Factor in 15–20% extra transit time.',
    impact: 'Plan shipments before Friday',
    generatedAt: new Date().toISOString(),
  },
  {
    id: 'ins-005',
    type: 'OPPORTUNITY',
    title: 'Onion off-season premium window',
    body: 'Kolar onion prices at ₹2,350/q — 12% above seasonal average. Short window before new crop arrives in 3 weeks.',
    commodity: 'Onion',
    market: 'Kolar',
    impact: '+₹250/q above average',
    generatedAt: new Date().toISOString(),
  },
];

// ---- Mock User ----
export const MOCK_USER: User = {
  id: 'usr-001',
  name: 'Ravi Kumar',
  email: 'ravi.kumar@mandya-fpo.org',
  phone: '+91 98456 78901',
  organization: 'Mandya Farmers Producer Organisation',
  role: 'FPO',
};

// ---- KPI values ----
export const MOCK_KPIS = {
  avgPrice: { value: 2840, unit: '₹/q', change: 3.2 },
  forecastPrice: { value: 3080, unit: '₹/q', change: 8.45 },
  marketsTracked: { value: 24, change: 0 },
  bestProfit: { value: '₹1.43L', change: 12.3 },
  confidence: { value: 87, unit: '%', change: 2 },
};

// ---- States for filter ----
export const STATES = ['Karnataka', 'Tamil Nadu', 'Andhra Pradesh', 'Maharashtra', 'Kerala'];
export const DISTRICTS = ['Ramanagara', 'Kolar', 'Bengaluru Urban', 'Mysuru', 'Tumakuru', 'Mandya', 'Hassan', 'Chikkaballapur'];
