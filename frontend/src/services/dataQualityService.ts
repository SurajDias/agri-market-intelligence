import apiClient from './api';
import type { DataQuality } from '../types';
export const dataQualityService = {
  async getDataQuality(): Promise<DataQuality> {
    const res = await apiClient.get('/api/data-quality/summary', {
      params: { reference_datetime: new Date().toISOString() },
    });
    const summary = res.data;
    const latestRun = summary.ingestion?.latest_run;
    return {
      overallScore: Number(summary.overall.score),
      recordsProcessed: summary.records.total,
      missingValues: summary.records.missing_price,
      duplicateRecords: summary.records.duplicates,
      marketsCount: new Set(summary.coverage_matrix.map((entry: { market_id: string }) => entry.market_id)).size,
      commoditiesCount: new Set(summary.coverage_matrix.map((entry: { commodity_id: string }) => entry.commodity_id)).size,
      lastUpdated: summary.overall.reference_datetime,
      sources: latestRun?.source ? [{
        id: String(latestRun.ingestion_run_id),
        name: latestRun.source,
        url: latestRun.resource ?? '',
        status: latestRun.status === 'SUCCESS' ? 'FRESH' : 'ERROR',
        recordsTotal: latestRun.records_seen,
        lastUpdated: latestRun.completed_at ?? latestRun.started_at,
        qualityScore: Number(summary.overall.score),
        missingValues: 0,
        duplicates: latestRun.duplicate_count,
      }] : [],
      readiness: summary.overall.readiness,
      classification: summary.overall.classification,
      limitations: summary.limitations,
    };
  },
};
