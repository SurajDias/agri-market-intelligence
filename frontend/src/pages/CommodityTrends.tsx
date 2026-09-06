import React from 'react';
import FilterBar from '../components/filters/FilterBar';
import PriceChart from '../components/charts/PriceChart';
import { TOMATO_FORECAST_POINTS } from '../services/mockData';

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

      <PriceChart dataPoints={TOMATO_FORECAST_POINTS} height={380} />
    </div>
  );
};

export default CommodityTrendsPage;
