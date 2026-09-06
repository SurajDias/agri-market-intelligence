import apiClient from './api';
import type { SimulatorInput, SimulatorResult } from '../types';
import { MOCK_RECOMMENDATION, MOCK_MARKET_COMPARISONS } from './mockData';

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

export const simulatorService = {
  async runSimulation(input: SimulatorInput): Promise<SimulatorResult> {
    try {
      const res = await apiClient.post('/api/simulator/analyze', input);
      return res.data;
    } catch {
      await delay(1400); // Simulate AI processing time
      return {
        input,
        recommendation: MOCK_RECOMMENDATION,
        marketComparisons: MOCK_MARKET_COMPARISONS,
        generatedAt: new Date().toISOString(),
      };
    }
  },
};
