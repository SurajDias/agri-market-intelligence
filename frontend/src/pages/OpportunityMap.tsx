import React, { useState, useEffect } from 'react';
import MarketMap from '../components/map/MarketMap';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { marketService } from '../services/marketService';
import { MOCK_RECOMMENDATION } from '../services/mockData';
import type { MarketComparison } from '../types';
import { MapPin, Navigation, Star, TrendingUp, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import './OpportunityMap.css';

const OpportunityMapPage: React.FC = () => {
  const [markets, setMarkets] = useState<MarketComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState<MarketComparison | null>(null);

  useEffect(() => {
    marketService.getMarketComparison('tomato', 5000, 'Mandya').then((res) => {
      setMarkets(res);
      setSelectedMarket(res.find((m) => m.isRecommended) ?? res[0]);
      setLoading(false);
    });
  }, []);

  const getRiskClass = (risk: string) => {
    if (risk === 'LOW') return 'risk-badge--low';
    if (risk === 'MEDIUM') return 'risk-badge--medium';
    return 'risk-badge--high';
  };

  const getRiskIcon = (risk: string) => {
    if (risk === 'LOW') return <CheckCircle size={10} />;
    if (risk === 'MEDIUM') return <AlertTriangle size={10} />;
    return <AlertTriangle size={10} />;
  };

  const getFactorIcon = (impact: string) => {
    if (impact === 'POSITIVE') return <span className="panel-factor-icon panel-factor-icon--positive">✓</span>;
    return <span className="panel-factor-icon panel-factor-icon--neutral">~</span>;
  };

  // Use the recommendation factors only for the recommended market
  const decisionFactors = selectedMarket?.isRecommended
    ? MOCK_RECOMMENDATION.factors
    : null;

  return (
    <div className="opportunity-map-page">
      {/* Page Header */}
      <div className="section-header" style={{ paddingBottom: 0 }}>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="section-title">Regional Opportunity Map</h1>
            <span className="map-live-badge">
              <span className="map-live-dot" />
              Live
            </span>
          </div>
          <p className="section-subtitle">
            Geographic view of APMC markets colour-coded by expected net profit capture.
          </p>
        </div>
      </div>

      {/* Map + Detail Panel */}
      <div className="map-workspace-grid">
        {/* LEFT — Leaflet Map */}
        {loading ? (
          <LoadingSkeleton type="chart" height={520} />
        ) : (
          <div className="map-chrome-container" style={{ height: '520px' }}>
            <MarketMap
              markets={markets}
              onSelectMarket={setSelectedMarket}
              height="520px"
            />

            {/* Legend overlay — inside the chrome container, above the map */}
            <div className="map-legend-overlay">
              <div className="map-legend-title">Opportunity Signal</div>
              <div className="map-legend-row">
                <span className="map-legend-dot" style={{ background: '#15803D' }} />
                High Opportunity
              </div>
              <div className="map-legend-row">
                <span className="map-legend-dot" style={{ background: '#D97706' }} />
                Medium / Monitor
              </div>
              <div className="map-legend-row">
                <span className="map-legend-dot" style={{ background: '#DC2626' }} />
                Higher Risk
              </div>
            </div>
          </div>
        )}

        {/* RIGHT — Selected Market Detail Panel */}
        <div className="market-detail-panel">
          {!selectedMarket ? (
            <div className="panel-empty-state">
              <div className="panel-empty-icon">
                <MapPin size={18} color="#94A3B8" />
              </div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#94A3B8' }}>
                Select a market pin
              </div>
              <div style={{ fontSize: '11px', color: '#CBD5E1' }}>
                Click any marker on the map to inspect market details.
              </div>
            </div>
          ) : (
            <>
              {/* ---- Header ---- */}
              <div className="panel-header">
                <div className="panel-header-eyebrow">
                  <span className="panel-eyebrow-label">
                    <MapPin size={9} style={{ display: 'inline', marginRight: 3 }} />
                    AI Market Analysis
                  </span>
                  <span className={`risk-badge ${getRiskClass(selectedMarket.risk)}`}>
                    {getRiskIcon(selectedMarket.risk)}
                    {selectedMarket.risk} Risk
                  </span>
                </div>

                <div className="panel-market-name">{selectedMarket.market.name} APMC</div>
                <div className="panel-market-sub">
                  {selectedMarket.market.district}, {selectedMarket.market.state} · {selectedMarket.market.type}
                </div>

                {selectedMarket.isRecommended && (
                  <div className="panel-recommended-row">
                    <span className="panel-recommended-chip">
                      <Star size={9} fill="#15803D" />
                      Top Recommendation
                    </span>
                  </div>
                )}
              </div>

              {/* ---- Net Revenue Hero ---- */}
              <div className="panel-revenue-hero">
                <div className="panel-revenue-label">Expected Net Revenue</div>
                <div>
                  <span className="panel-revenue-value">
                    ₹{selectedMarket.expectedNetProfit.toLocaleString('en-IN')}
                  </span>
                  <span className="panel-revenue-perq">/ 50q batch</span>
                </div>
                <div className="panel-revenue-sub">
                  ₹{selectedMarket.expectedNetProfitPerQ}/q · {selectedMarket.confidence}% model confidence
                </div>
              </div>

              {/* ---- Metric Blocks ---- */}
              <div className="panel-metrics-grid">
                <div className="panel-metric-block">
                  <div className="panel-metric-label">Expected Price</div>
                  <div className="panel-metric-value">₹{selectedMarket.forecastPrice.toLocaleString()}</div>
                  <div className="panel-metric-sub">7-day forecast /q</div>
                </div>
                <div className="panel-metric-block">
                  <div className="panel-metric-label">Arrivals</div>
                  <div className="panel-metric-value">{selectedMarket.arrivals} t</div>
                  <div className="panel-metric-sub">daily throughput</div>
                </div>
                <div className="panel-metric-block">
                  <div className="panel-metric-label">Distance</div>
                  <div className="panel-metric-value panel-metric-value--orange">
                    {selectedMarket.transportDistance} km
                  </div>
                  <div className="panel-metric-sub">from Mandya</div>
                </div>
                <div className="panel-metric-block">
                  <div className="panel-metric-label">Transport Overhead</div>
                  <div className="panel-metric-value panel-metric-value--orange">
                    ₹{selectedMarket.transportCostPerQ}/q
                  </div>
                  <div className="panel-metric-sub">est. logistics cost</div>
                </div>
              </div>

              {/* ---- Confidence Bar ---- */}
              <div className="panel-confidence-bar-row">
                <span className="panel-confidence-label">AI Confidence</span>
                <div className="panel-confidence-track">
                  <div
                    className="panel-confidence-fill"
                    style={{ width: `${selectedMarket.confidence}%` }}
                  />
                </div>
                <span className="panel-confidence-pct">{selectedMarket.confidence}%</span>
              </div>

              {/* ---- Why This Market ---- */}
              {decisionFactors && (
                <div className="panel-why-section">
                  <div className="panel-why-title">
                    <Info size={11} />
                    Why this market?
                  </div>
                  {decisionFactors.slice(0, 4).map((factor) => (
                    <div key={factor.name} className="panel-factor-row">
                      {getFactorIcon(factor.impact)}
                      <div className="panel-factor-text">
                        <div className="panel-factor-name">
                          <span>{factor.name}</span>
                          <span className="panel-factor-score">{factor.score}/100</span>
                        </div>
                        <div className="panel-factor-explanation">{factor.explanation}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Non-recommended market: show trend insight instead */}
              {!selectedMarket.isRecommended && (
                <div className="panel-why-section">
                  <div className="panel-why-title">
                    <TrendingUp size={11} />
                    Market Signal
                  </div>
                  <div className="panel-factor-row">
                    <span className={`panel-factor-icon ${selectedMarket.trend === 'DOWN' ? 'panel-factor-icon--neutral' : 'panel-factor-icon--positive'}`}>
                      {selectedMarket.trend === 'UP' ? '↑' : selectedMarket.trend === 'DOWN' ? '↓' : '→'}
                    </span>
                    <div className="panel-factor-text">
                      <div className="panel-factor-name">
                        Price Trend
                        <span className="panel-factor-score" style={{ color: selectedMarket.priceChange < 0 ? '#B91C1C' : '#15803D' }}>
                          {selectedMarket.priceChange > 0 ? '+' : ''}{selectedMarket.priceChange}%
                        </span>
                      </div>
                      <div className="panel-factor-explanation">
                        {selectedMarket.trend === 'UP'
                          ? 'Prices are trending upward. Monitor for potential opportunity.'
                          : selectedMarket.trend === 'DOWN'
                          ? 'Prices are under pressure. Higher risk of revenue shortfall.'
                          : 'Prices are stable. Low volatility but limited upside potential.'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ---- CTA ---- */}
              <div className="panel-cta-area">
                <button className="panel-cta-btn">
                  <Navigation size={15} />
                  Route &amp; Logistics Plan
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default OpportunityMapPage;
