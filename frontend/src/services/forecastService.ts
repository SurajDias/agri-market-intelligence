import apiClient from './api';
import type { Forecast } from '../types';
import { MOCK_FORECAST } from './mockData';

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

export const forecastService = {
  async getForecast(commodity: string, market: string, horizon: number = 7): Promise<Forecast> {
    try {
      const res = await apiClient.get('/api/forecasts', {
        params: { commodity, market, horizon }
      });
      return res.data;
    } catch {
      await delay(700);
      return { ...MOCK_FORECAST, commodity, market, horizon };
    }
  },
};
