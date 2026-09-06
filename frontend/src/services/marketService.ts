import apiClient from './api';
import type { MarketComparison, PriceRecord } from '../types';
import { MOCK_MARKET_COMPARISONS, TOMATO_HISTORY, MARKETS } from './mockData';

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

export const marketService = {
  async getMarkets() {
    try {
      const res = await apiClient.get('/api/markets');
      return res.data;
    } catch {
      await delay(600);
      return MARKETS;
    }
  },

  async getMarketComparison(commodity: string, quantity: number, origin: string): Promise<MarketComparison[]> {
    try {
      const res = await apiClient.get('/api/markets/comparison', {
        params: { commodity, quantity, origin }
      });
      return res.data;
    } catch {
      await delay(800);
      return MOCK_MARKET_COMPARISONS;
    }
  },

  async getMarketPrices(marketId: string, commodity: string, days: number = 30): Promise<PriceRecord[]> {
    try {
      const res = await apiClient.get(`/api/markets/${marketId}/prices`, {
        params: { commodity, days }
      });
      return res.data;
    } catch {
      await delay(500);
      return TOMATO_HISTORY;
    }
  },
};
