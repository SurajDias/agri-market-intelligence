import React from 'react';
import type { RecommendationFactor } from '../../types';
import './RecommendationFactorsChart.css';

interface RecommendationFactorsChartProps {
  factors: RecommendationFactor[];
}

const RecommendationFactorsChart: React.FC<RecommendationFactorsChartProps> = ({ factors }) => {
  return (
    <div className="factors-chart">
      <div className="factors-chart__header">
        <h4 className="factors-chart__title">Why This Recommendation?</h4>
        <span className="factors-chart__subtitle">
          Explainable AI · Factor weights &amp; scores that drove this decision
        </span>
      </div>

      <div className="factors-chart__list">
        {factors.map((factor) => (
          <div key={factor.name} className="factor-item">
            <div className="factor-item__meta">
              <span className="factor-item__name">{factor.name}</span>
              <div className="factor-item__weight-score">
                <span className="factor-item__weight">{factor.weight}% weight</span>
                <span className="factor-item__score-val">{factor.score}/100</span>
              </div>
            </div>

            <div className="factor-item__bar-bg">
              <div
                className={`factor-item__bar-fill factor-item__bar-fill--${factor.impact.toLowerCase()}`}
                style={{ width: `${factor.score}%` }}
              />
            </div>

            <p className="factor-item__explanation">{factor.explanation}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendationFactorsChart;
