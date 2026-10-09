import apiClient from './api';
import type { SimulatorInput, SimulatorResult } from '../types';
export const simulatorService = {
  async runSimulation(input: SimulatorInput): Promise<SimulatorResult> {
    const res = await apiClient.post<SimulatorResult>('/api/simulator/analyze', input);
    return res.data;
  },
};
