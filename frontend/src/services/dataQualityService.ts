import apiClient from './api';
import type { DataQuality } from '../types';
import { MOCK_DATA_QUALITY } from './mockData';

const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

export const dataQualityService = {
  async getDataQuality(): Promise<DataQuality> {
    try {
      const res = await apiClient.get('/api/data-quality');
      return res.data;
    } catch {
      await delay(500);
      return MOCK_DATA_QUALITY;
    }
  },
};
