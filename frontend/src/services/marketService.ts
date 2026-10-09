import apiClient from './api';
import type { MarketComparison, PriceRecord } from '../types';
export const marketService = {
  async getMarkets() {
    const res = await apiClient.get('/api/markets');
    return res.data;
  },

  async getMarketComparison(commodity: string, quantity: number, origin: string): Promise<MarketComparison[]> {
    void commodity;
    void quantity;
    void origin;
    return [];
  },

  async getMarketPrices(marketId: string, commodity: string, days: number = 30): Promise<PriceRecord[]> {
    const res = await apiClient.get(`/api/markets/${marketId}/prices`, {
      params: { commodity_id: commodity, days }
    });
    return res.data;
  },
};
