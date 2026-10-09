import React from 'react';
import FilterBar from '../components/filters/FilterBar';
import EmptyState from '../components/ui/EmptyState';

const CommodityTrendsPage: React.FC = () => {
  return (
    <div className="commodity-trends-page flex flex-col gap-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Commodity Trends & Seasonality</h1>
          <p className="section-subtitle">
            Long-term price volatility and seasonal cycle analysis across Karnataka commodities.
          </p>
        </div>
      </div>

      <EmptyState
        title="No verified trend history available"
        description="Trend and seasonality charts require canonical market-price observations."
      />
    </div>
  );
};

export default CommodityTrendsPage;
