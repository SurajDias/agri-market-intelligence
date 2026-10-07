import React, { useState, useEffect } from 'react';
import KPICard from '../components/ui/KPICard';
import FilterBar from '../components/filters/FilterBar';
import PriceChart from '../components/charts/PriceChart';
import MarketComparisonChart from '../components/charts/MarketComparisonChart';
import RecommendationCard from '../components/recommendation/RecommendationCard';
import RecommendationFactorsChart from '../components/charts/RecommendationFactorsChart';
import MarketTable from '../components/market/MarketTable';
import InsightCard from '../components/ui/InsightCard';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import ErrorState from '../components/ui/ErrorState';
import { forecastService } from '../services/forecastService';
import { marketService } from '../services/marketService';
import { MOCK_RECOMMENDATION, MOCK_INSIGHTS, MOCK_KPIS } from '../services/mockData';
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

      {/* KPI Cards Row */}
      {loading ? (
        <div className="grid grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <LoadingSkeleton key={i} type="card" height={130} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-5 gap-4 stagger-children">
          <KPICard
            title="Current Avg Price"
            value={`₹${MOCK_KPIS.avgPrice.value.toLocaleString()}`}
            unit="₹/q"
            change={MOCK_KPIS.avgPrice.change}
            icon="rupee"
            changeLabel="vs last week"
          />
          <KPICard
            title="7-Day Forecast"
            value={`₹${MOCK_KPIS.forecastPrice.value.toLocaleString()}`}
            unit="₹/q"
            change={MOCK_KPIS.forecastPrice.change}
            icon="target"
            changeLabel="expected rise"
          />
          <KPICard
            title="Markets Tracked"
            value={MOCK_KPIS.marketsTracked.value}
            icon="store"
            description="APMC & eNAM markets"
          />
          <KPICard
            title="Expected Best Profit"
            value={MOCK_KPIS.bestProfit.value}
            change={MOCK_KPIS.bestProfit.change}
            icon="award"
            changeLabel="vs local mandi"
          />
          <KPICard
            title="Recommendation Confidence"
            value={`${MOCK_KPIS.confidence.value}%`}
            icon="shield"
            description="High model certainty"
          />
        </div>
      )}

      {/* Primary Hero AI Recommendation */}
      {loading ? (
        <LoadingSkeleton type="card" height={220} />
      ) : (
        <RecommendationCard recommendation={MOCK_RECOMMENDATION} />
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-6">
        {loading ? (
          <>
            <LoadingSkeleton type="chart" height={360} />
            <LoadingSkeleton type="chart" height={360} />
          </>
        ) : (
          <>
            {forecast && <PriceChart dataPoints={forecast.dataPoints} height={320} />}
            <MarketComparisonChart markets={markets} height={320} />
          </>
        )}
      </div>

      {/* Explainable AI Rationale + Insights */}
      <div className="grid grid-cols-2 gap-6">
        {loading ? (
          <>
            <LoadingSkeleton type="card" height={300} />
            <LoadingSkeleton type="card" height={300} />
          </>
        ) : (
          <>
            <RecommendationFactorsChart factors={MOCK_RECOMMENDATION.factors} />
            <div className="card flex flex-col gap-3">
              <h4 className="chart-title">AI Market Advisories & Insights</h4>
              <p className="chart-subtitle">Real-time alerts driving current recommendation</p>
              <div className="flex flex-col gap-3">
                {MOCK_INSIGHTS.slice(0, 3).map((ins) => (
                  <InsightCard key={ins.id} insight={ins} />
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Full Market Table */}
      <div className="card">
        <div className="section-header mb-4">
          <div>
            <h3 className="section-title">Regional APMC Market Analysis</h3>
            <p className="section-subtitle">Real-time modal prices, logistics overhead, and risk ratings across Karnataka</p>
          </div>
        </div>
        {loading ? <LoadingSkeleton type="table" rows={5} /> : <MarketTable markets={markets} />}
      </div>
    </div>
  );
};

export default ExecutiveOverview;
