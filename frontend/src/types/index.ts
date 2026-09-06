// ============================================
// AGRIMARK AI — TypeScript Interfaces
// ============================================

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type TrendDirection = 'UP' | 'DOWN' | 'STABLE';
export type DataStatus = 'FRESH' | 'STALE' | 'MISSING' | 'ERROR';

export interface Commodity {
  id: string;
  name: string;
  nameHindi?: string;
  category: string;
  unit: string; // 'quintal' | 'kg' | 'tonne'
  icon?: string;
  shelfLifeDays: number;
}

export interface Market {
  id: string;
  name: string;
  state: string;
  district: string;
  lat: number;
  lng: number;
  type: 'APMC' | 'eNAM' | 'Private' | 'Wholesale';
  isActive: boolean;
}

export interface PriceRecord {
  date: string; // ISO date
  market: string;
  commodity: string;
  minPrice: number;
  maxPrice: number;
  modalPrice: number;
  arrivals: number; // in tonnes
  unit: string;
}

export interface ForecastPoint {
  date: string;
  predictedPrice: number;
  lowerBound: number;
  upperBound: number;
  isForecasted: boolean;
}

export interface Forecast {
  commodity: string;
  market: string;
  currentPrice: number;
  predictedPrice: number;
  changePercent: number;
  changeAbsolute: number;
  horizon: number; // days
  confidence: number; // 0–100
  accuracy: number; // 0–100 (historical MAPE-based)
  dataPoints: ForecastPoint[];
  generatedAt: string;
}

export interface MarketComparison {
  market: Market;
  currentPrice: number;
  forecastPrice: number;
  transportCostPerQ: number;
  transportDistance: number;
  expectedRevenue: number;
  expectedNetProfit: number;
  expectedNetProfitPerQ: number;
  risk: RiskLevel;
  confidence: number;
  trend: TrendDirection;
  priceChange: number;
  arrivals: number;
  isRecommended: boolean;
}

export interface RecommendationFactor {
  name: string;
  weight: number; // 0–100
  score: number; // 0–100
  impact: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  explanation: string;
}

export interface Recommendation {
  id: string;
  commodity: string;
  quantity: number;
  origin: string;
  sellingDate: string;
  recommendedMarket: Market;
  expectedPrice: number;
  grossRevenue: number;
  transportCost: number;
  netRevenue: number;
  netProfitPerQ: number;
  confidence: number;
  risk: RiskLevel;
  sellingWindowDays: number;
  sellingWindowLabel: string;
  factors: RecommendationFactor[];
  alternatives: MarketComparison[];
  insights: string[];
  generatedAt: string;
}

export interface SimulatorInput {
  commodity: string;
  quantity: number; // in kg
  origin: string;
  sellingDate: string;
  cropQuality?: 'A' | 'B' | 'C';
  variety?: string;
  transportCostPerKm?: number;
  shelfLifeDays?: number;
}

export interface SimulatorResult {
  input: SimulatorInput;
  recommendation: Recommendation;
  marketComparisons: MarketComparison[];
  generatedAt: string;
}

export interface WhatIfScenario {
  label: string;
  input: Partial<SimulatorInput>;
  result: {
    recommendedMarket: string;
    netRevenue: number;
    risk: RiskLevel;
    confidence: number;
    expectedPrice: number;
    transportCost: number;
  };
}

export interface InsightCard {
  id: string;
  type: 'OPPORTUNITY' | 'RISK' | 'INFO' | 'ALERT';
  title: string;
  body: string;
  commodity?: string;
  market?: string;
  impact?: string;
  generatedAt: string;
}

export interface Report {
  id: string;
  title: string;
  period: string;
  generatedAt: string;
  sections: {
    id: string;
    title: string;
    content: string;
  }[];
  insights: InsightCard[];
  marketSummary: MarketComparison[];
}

export interface DataSource {
  id: string;
  name: string;
  url: string;
  status: DataStatus;
  recordsTotal: number;
  lastUpdated: string;
  qualityScore: number; // 0–100
  missingValues: number;
  duplicates: number;
}

export interface DataQuality {
  overallScore: number;
  recordsProcessed: number;
  missingValues: number;
  duplicateRecords: number;
  marketsCount: number;
  commoditiesCount: number;
  lastUpdated: string;
  sources: DataSource[];
}

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  organization: string;
  role: 'FPO' | 'Trader' | 'Aggregator' | 'Administrator';
  avatarUrl?: string;
}

export interface KPICard {
  id: string;
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  changeLabel?: string;
  trend?: TrendDirection;
  icon: string;
  description?: string;
  color?: string;
}

export interface FilterState {
  commodity: string;
  state: string;
  district: string;
  market: string;
  dateFrom: string;
  dateTo: string;
}
