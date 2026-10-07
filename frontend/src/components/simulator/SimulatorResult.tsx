import React, { useState } from 'react';
import type { Recommendation, MarketComparison } from '../../types';
import RecommendationCard from '../recommendation/RecommendationCard';
import MarketTable from '../market/MarketTable';
import RecommendationFactorsChart from '../charts/RecommendationFactorsChart';
import './SimulatorResult.css';

interface SimulatorResultProps {
  recommendation: Recommendation;
  allMarkets: MarketComparison[];
}

const SimulatorResult: React.FC<SimulatorResultProps> = ({ recommendation, allMarkets }) => {
  const [activeTab, setActiveTab] = useState<'recommendation' | 'alternatives' | 'factors'>('recommendation');

  return (
    <div className="simulator-result animate-fade-in">

      {/* Step connector */}
      <div className="sim-step-connector">
        <div className="sim-step-connector-line" />
        <span>AI Decision Engine →</span>
        <div className="sim-step-connector-line" />
      </div>

      {/* Segmented tab shell */}
      <div className="sim-tabs-shell">
        <nav className="sim-tabs-nav">
          <button
            className={`sim-tab-btn ${activeTab === 'recommendation' ? 'sim-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('recommendation')}
          >
            <span className="sim-tab-step">2</span>
            <span className="sim-tab-icon sim-tab-icon--green">🏆</span>
            AI Recommended Strategy
          </button>

          <button
            className={`sim-tab-btn ${activeTab === 'alternatives' ? 'sim-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('alternatives')}
          >
            <span className="sim-tab-step">—</span>
            <span className="sim-tab-icon sim-tab-icon--slate">📊</span>
            All Markets ({allMarkets.length})
          </button>

          <button
            className={`sim-tab-btn ${activeTab === 'factors' ? 'sim-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('factors')}
          >
            <span className="sim-tab-step">—</span>
            <span className="sim-tab-icon sim-tab-icon--amber">💡</span>
            Decision Rationale
          </button>
        </nav>

        <div className="sim-tab-content">
          {activeTab === 'recommendation' && (
            <RecommendationCard recommendation={recommendation} />
          )}

          {activeTab === 'alternatives' && (
            <div>
              <div className="sim-alt-tab-heading">
                📊 Ranked Market Profitability Comparison
              </div>
              <MarketTable markets={allMarkets} />
            </div>
          )}

          {activeTab === 'factors' && (
            <RecommendationFactorsChart factors={recommendation.factors} />
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulatorResult;
