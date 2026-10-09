import React, { useState, useEffect } from 'react';
import FilterBar from '../components/filters/FilterBar';
import MarketTable from '../components/market/MarketTable';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import ErrorState from '../components/ui/ErrorState';
import EmptyState from '../components/ui/EmptyState';
import { marketService } from '../services/marketService';
import type { MarketComparison, FilterState } from '../types';
import { Store, TrendingUp, ShieldCheck, MapPin } from 'lucide-react';

const MarketComparisonPage: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    commodity: 'tomato',
    state: 'Karnataka',
    district: 'All',
    market: 'All',
    dateFrom: '',
    dateTo: '',
  });

  const [loading, setLoading] = useState(true);
  const [markets, setMarkets] = useState<MarketComparison[]>([]);

  useEffect(() => {
    setLoading(true);
    marketService.getMarketComparison(filters.commodity, 5000, 'Mandya').then((res) => {
      setMarkets(res);
      setLoading(false);
    });
  }, [filters.commodity]);

  return (
    <div className="market-intelligence-page flex flex-col gap-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Market Intelligence & APMC Directory</h1>
          <p className="section-subtitle">
            Compare prices, arrival volumes, and transport overhead across agricultural markets.
          </p>
        </div>
      </div>

      <FilterBar filters={filters} onChange={setFilters} />

      {/* Top market snapshot cards */}
      <div className="grid grid-cols-4 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <LoadingSkeleton key={i} type="card" height={130} />)
        ) : markets.length === 0 ? (
          <EmptyState
            title="No verified market comparison available"
            description="A comparison requires canonical market-price observations. No prices or economics are fabricated."
          />
        ) : (
          markets.slice(0, 4).map((m) => (
            <div
              key={m.market.id}
              className={`card market-summary-card ${m.isRecommended ? 'market-summary-card--recommended' : ''}`}
            >
              <div className="market-summary-card__header">
                <div className="market-summary-card__title-wrap">
                  <span className="market-summary-card__name">{m.market.name}</span>
                  <span className="market-summary-card__location">{m.market.district}, {m.market.state}</span>
                </div>
                {m.isRecommended && <span className="badge badge-primary font-bold">🏆 Recommended</span>}
              </div>

              <div className="market-summary-card__price-row">
                <span className="market-summary-card__price-label">Current Price</span>
                <span className="market-summary-card__price">₹{m.currentPrice.toLocaleString()}<span className="market-summary-card__unit">/q</span></span>
              </div>

              <div className="market-summary-card__stats-grid">
                <div className="market-summary-card__stat">
                  <span className="market-summary-card__stat-label">Arrivals</span>
                  <span className="market-summary-card__stat-value">{m.arrivals} tonnes</span>
                </div>
                <div className="market-summary-card__stat market-summary-card__stat--forecast">
                  <span className="market-summary-card__stat-label">7-Day Forecast</span>
                  <span className="market-summary-card__stat-value text-positive font-bold">₹{m.forecastPrice.toLocaleString()}/q</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <h3 className="chart-title mb-4">Complete Market Price & Profit Comparison</h3>
        {loading ? <LoadingSkeleton type="table" rows={6} /> : markets.length > 0 ? <MarketTable markets={markets} /> : null}
      </div>
    </div>
  );
};

export default MarketComparisonPage;
