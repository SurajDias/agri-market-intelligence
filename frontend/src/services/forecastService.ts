import apiClient from './api';
import type { Forecast } from '../types';
export const forecastService = {
  async getForecast(commodity: string, market: string, horizon: number = 7): Promise<Forecast | null> {
    const res = await apiClient.get('/api/forecasts/baseline', {
      params: { commodity_id: commodity, market_id: market.toLowerCase(), horizon }
    });
    const baseline = res.data;
    if (baseline.status !== 'sufficient_history' || baseline.forecast.length === 0) return null;
    const latest = baseline.latest_observed_price_per_kg;
    const finalPrice = baseline.forecast[baseline.forecast.length - 1].predicted_price_per_kg;
    if (latest === null || latest === undefined) return null;
    const dataPoints = baseline.forecast.map((point: { forecast_date: string; predicted_price_per_kg: number }) => ({
      date: point.forecast_date,
      predictedPrice: point.predicted_price_per_kg * 100,
      lowerBound: point.predicted_price_per_kg * 100,
      upperBound: point.predicted_price_per_kg * 100,
      isForecasted: true,
    }));
    return {
      commodity, market, currentPrice: latest * 100, predictedPrice: finalPrice * 100,
      changePercent: latest === 0 ? 0 : ((finalPrice - latest) / latest) * 100,
      changeAbsolute: (finalPrice - latest) * 100, horizon,
      confidence: baseline.confidence ?? 0, accuracy: 0, dataPoints,
      generatedAt: new Date().toISOString(),
    };
  },
};
