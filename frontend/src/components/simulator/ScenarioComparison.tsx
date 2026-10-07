import React, { useState } from 'react';
import type { MarketComparison } from '../../types';
import RiskBadge from '../ui/RiskBadge';
import './ScenarioComparison.css';

interface ScenarioComparisonProps {
  currentMarket: MarketComparison;
  alternativeMarkets: MarketComparison[];
}

const ScenarioComparison: React.FC<ScenarioComparisonProps> = ({
  currentMarket,
  alternativeMarkets,
}) => {
  const [selectedAltId, setSelectedAltId] = useState(
    alternativeMarkets[0]?.market.id ?? ''
  );

  const selectedAlt = alternativeMarkets.find(
    (m) => m.market.id === selectedAltId
  ) ?? alternativeMarkets[0];

  if (!selectedAlt) return null;

  // Positive = recommended is better (alt is worse)
  const profitDiff = currentMarket.expectedNetProfit - selectedAlt.expectedNetProfit;
  const isRecBetter = profitDiff >= 0;

  return (
    <div className="scenario-comparison">

      {/* ---- Header ---- */}
      <div className="scenario-comparison__header">
        <div className="scenario-header-left">
          <span className="scenario-step-chip">3</span>
          <div>
            <div className="scenario-header-title">What-If Scenario Comparison</div>
            <div className="scenario-header-sub">
              See how much you gain or lose by choosing a different market
            </div>
          </div>
        </div>

        <div className="scenario-select-row">
          <label className="scenario-select-label" htmlFor="scenario-market-select">
            Compare against:
          </label>
          <select
            id="scenario-market-select"
            className="scenario-select"
            value={selectedAltId}
            onChange={(e) => setSelectedAltId(e.target.value)}
          >
            {alternativeMarkets.map((m) => (
              <option key={m.market.id} value={m.market.id}>
                {m.market.name} APMC
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ---- Split panels ---- */}
      <div className="scenario-grid">
        {/* RECOMMENDED */}
        <div className="scenario-panel scenario-panel--recommended">
          <span className="scenario-panel__badge scenario-panel__badge--rec">
            🏆 Recommended
          </span>

          <div>
            <div className="scenario-panel__market">{currentMarket.market.name} APMC</div>
            <div className="scenario-panel__location">
              {currentMarket.market.district}, {currentMarket.market.state}
            </div>
          </div>

          {/* Net Revenue Hero */}
          <div className="scenario-revenue-row">
            <div className="scenario-revenue-label">Expected Net Revenue</div>
            <div className="scenario-revenue-value">
              ₹{currentMarket.expectedNetProfit.toLocaleString('en-IN')}
            </div>
          </div>

          {/* Metrics */}
          <div className="scenario-metrics">
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Forecast Price</span>
              <span className="scenario-metric-val">₹{currentMarket.forecastPrice}/q</span>
            </div>
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Transport Cost</span>
              <span className="scenario-metric-val">₹{currentMarket.transportCostPerQ}/q</span>
            </div>
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Arrivals</span>
              <span className="scenario-metric-val">{currentMarket.arrivals} t/day</span>
            </div>
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Risk</span>
              <span className="scenario-metric-val"><RiskBadge level={currentMarket.risk} /></span>
            </div>
          </div>
        </div>

        {/* ALTERNATIVE */}
        <div className="scenario-panel scenario-panel--alternative">
          <span className="scenario-panel__badge scenario-panel__badge--alt">
            Alternative
          </span>

          <div>
            <div className="scenario-panel__market">{selectedAlt.market.name} APMC</div>
            <div className="scenario-panel__location">
              {selectedAlt.market.district}, {selectedAlt.market.state}
            </div>
          </div>

          {/* Net Revenue Hero */}
          <div className="scenario-revenue-row" style={{ background: 'rgba(15,23,42,0.025)', borderColor: '#E2E8F0' }}>
            <div className="scenario-revenue-label">Expected Net Revenue</div>
            <div className="scenario-revenue-value scenario-revenue-value--muted">
              ₹{selectedAlt.expectedNetProfit.toLocaleString('en-IN')}
            </div>
          </div>

          {/* Metrics */}
          <div className="scenario-metrics">
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Forecast Price</span>
              <span className="scenario-metric-val">₹{selectedAlt.forecastPrice}/q</span>
            </div>
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Transport Cost</span>
              <span className="scenario-metric-val">₹{selectedAlt.transportCostPerQ}/q</span>
            </div>
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Arrivals</span>
              <span className="scenario-metric-val">{selectedAlt.arrivals} t/day</span>
            </div>
            <div className="scenario-metric-row">
              <span className="scenario-metric-key">Risk</span>
              <span className="scenario-metric-val"><RiskBadge level={selectedAlt.risk} /></span>
            </div>
          </div>
        </div>
      </div>

      {/* ---- Delta Banner ---- */}
      <div className="scenario-delta-banner">
        <span className="scenario-delta-label">Net Revenue Difference:</span>
        <span className={`scenario-delta-pill ${isRecBetter ? 'scenario-delta-pill--positive' : 'scenario-delta-pill--negative'}`}>
          {isRecBetter ? '▲' : '▼'}
          &nbsp;₹{Math.abs(profitDiff).toLocaleString('en-IN')}
        </span>
        <span className="scenario-delta-context">
          {isRecBetter
            ? `You earn ₹${Math.abs(profitDiff).toLocaleString('en-IN')} more by following the AI recommendation.`
            : `${selectedAlt.market.name} offers higher revenue, but carries ${selectedAlt.risk} risk — factor this before deciding.`}
        </span>
      </div>
    </div>
  );
};

export default ScenarioComparison;
