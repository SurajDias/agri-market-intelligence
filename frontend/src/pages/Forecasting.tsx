import React, { useState, useEffect } from 'react';
import FilterBar from '../components/filters/FilterBar';
import PriceChart from '../components/charts/PriceChart';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import EmptyState from '../components/ui/EmptyState';
import { forecastService } from '../services/forecastService';
import type { Forecast, FilterState } from '../types';
import { TrendingUp, Target, Activity, Calendar, ShieldCheck } from 'lucide-react';
import './Forecasting.css';

const ForecastingPage: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    commodity: 'tomato',
    state: 'Karnataka',
    district: 'All',
    market: 'Ramanagara',
    dateFrom: '',
    dateTo: '',
  });

  const [horizon, setHorizon] = useState<7 | 10>(7);
  const [loading, setLoading] = useState(true);
  const [forecast, setForecast] = useState<Forecast | null>(null);

  useEffect(() => {
    setLoading(true);
    forecastService.getForecast(filters.commodity, 'Ramanagara', horizon)
      .then((res) => setForecast(res))
      .catch(() => setForecast(null))
      .finally(() => setLoading(false));
  }, [filters.commodity, horizon]);

  return (
    <div className="forecasting-page flex flex-col gap-5">
      <div className="section-header terminal-header">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="section-title">Commodity Price Forecasting</h1>
            <span className="terminal-badge">LIVE TERMINAL</span>
          </div>
          <p className="section-subtitle">
            Time-series machine learning price predictions with uncertainty bounds &amp; backtested accuracy.
          </p>
        </div>

        <div className="terminal-horizon-toggle">
          <button
            className={`terminal-toggle-btn ${horizon === 7 ? 'active' : ''}`}
            onClick={() => setHorizon(7)}
          >
            7-Day Horizon
          </button>
          <button
            className={`terminal-toggle-btn ${horizon === 10 ? 'active' : ''}`}
            onClick={() => setHorizon(10)}
          >
            10-Day Horizon
          </button>
        </div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      {/* Forecast Metrics Cards - Compact Terminal Style */}
      {loading ? (
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <LoadingSkeleton key={i} type="card" height={90} />)}
        </div>
      ) : (
        forecast ? (
          <div className="grid grid-cols-4 gap-4">
            <div className="terminal-card">
              <span className="terminal-card__label">CURRENT MODAL PRICE</span>
              <div className="terminal-card__value">₹{forecast.currentPrice.toLocaleString()}<span className="terminal-card__unit">/q</span></div>
              <span className="terminal-card__sub">Mandi benchmark</span>
            </div>

            <div className="terminal-card terminal-card--accent">
              <span className="terminal-card__label">PREDICTED PRICE ({horizon}d)</span>
              <div className="terminal-card__value text-positive">₹{forecast.predictedPrice.toLocaleString()}<span className="terminal-card__unit">/q</span></div>
              <span className="terminal-card__sub text-positive font-bold">+{forecast.changePercent}% Expected Trend</span>
            </div>

            <div className="terminal-card">
              <span className="terminal-card__label">MODEL CONFIDENCE</span>
              <div className="terminal-card__value text-primary">{forecast.confidence}%</div>
              <span className="terminal-card__sub">95% CI certainty</span>
            </div>

            <div className="terminal-card">
              <span className="terminal-card__label">HISTORICAL MAPE ACCURACY</span>
              <div className="terminal-card__value">{forecast.accuracy}%</div>
              <span className="terminal-card__sub">Backtested precision</span>
            </div>
          </div>
        ) : (
          <EmptyState
            title="Insufficient verified history"
            description="No forecast is shown because the canonical database has no usable market-price history for this selection."
          />
        )
      )}

      {/* Main Forecast Chart */}
      {loading ? (
        <LoadingSkeleton type="chart" height={420} />
      ) : (
        forecast && <PriceChart dataPoints={forecast.dataPoints} height={400} />
      )}
    </div>
  );
};

export default ForecastingPage;
