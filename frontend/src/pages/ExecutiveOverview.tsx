import React, { useState, useEffect } from 'react';
import FilterBar from '../components/filters/FilterBar';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import { forecastService } from '../services/forecastService';
import { marketService } from '../services/marketService';
import type { Forecast, MarketComparison, FilterState } from '../types';

const ExecutiveOverview: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    commodity: 'tomato',
    state: 'Karnataka',
    district: 'All',
    market: 'All',
    dateFrom: '',
    dateTo: '',
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [markets, setMarkets] = useState<MarketComparison[]>([]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(false);
    try {
      const [fcData, mktData] = await Promise.all([
        forecastService.getForecast(filters.commodity, 'Ramanagara'),
        marketService.getMarketComparison(filters.commodity, 5000, 'Mandya'),
      ]);
      setForecast(fcData);
      setMarkets(mktData);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [filters.commodity]);

  if (error) {
    return <ErrorState onRetry={loadDashboardData} />;
  }

  return (
    <div className="dashboard-page flex flex-col gap-6">
      {/* Header */}
      <div className="section-header">
        <div>
          <h1 className="section-title">Market Intelligence Dashboard</h1>
          <p className="section-subtitle">
            Real-time market conditions, multi-APMC price comparisons, and AI-powered selling recommendations.
          </p>
        </div>
      </div>

      {/* Filter bar */}
      <FilterBar filters={filters} onChange={setFilters} />

      {loading ? (
        <LoadingSkeleton type="card" height={220} />
      ) : (
        <EmptyState
          title="No verified market intelligence available"
          description="The dashboard will show prices, forecasts, recommendations, and evidence only after verified market observations are present."
        />
      )}
    </div>
  );
};

export default ExecutiveOverview;
