import apiClient from './api';

export interface DashboardHealthStatus {
  status: string;
  database: string;
}

export interface DashboardReadinessStatus {
  verifiedObservations: number;
  readiness: string;
  recommendationReady: boolean;
}

const isFiniteNumber = (value: unknown): value is number => (
  typeof value === 'number' && Number.isFinite(value)
);

const requireString = (value: unknown, field: string): string => {
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`Dashboard status response is missing ${field}.`);
  }
  return value;
};

export const parseDashboardReadiness = (summary: unknown): DashboardReadinessStatus => {
  const response = summary as {
    overall?: { readiness?: unknown };
    readiness?: {
      verified_observation_count?: unknown;
      recommendation_ready?: unknown;
    };
  };
  const verifiedObservations = response.readiness?.verified_observation_count;
  const recommendationReady = response.readiness?.recommendation_ready;

  if (!isFiniteNumber(verifiedObservations)) {
    throw new Error('Dashboard status response is missing verified observation count.');
  }
  if (typeof recommendationReady !== 'boolean') {
    throw new Error('Dashboard status response is missing recommendation readiness.');
  }

  return {
    verifiedObservations,
    readiness: requireString(response.overall?.readiness, 'readiness'),
    recommendationReady,
  };
};

export const dashboardStatusService = {
  async getHealth(): Promise<DashboardHealthStatus> {
    const response = await apiClient.get<DashboardHealthStatus>('/api/health');
    const status = requireString(response.data?.status, 'backend status');
    const database = requireString(response.data?.database, 'database status');
    return { status, database };
  },

  async getReadiness(): Promise<DashboardReadinessStatus> {
    const response = await apiClient.get('/api/data-quality/summary', {
      params: { reference_datetime: new Date().toISOString() },
    });
    return parseDashboardReadiness(response.data);
  },
};
