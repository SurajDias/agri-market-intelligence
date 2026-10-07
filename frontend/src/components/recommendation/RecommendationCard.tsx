import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Award, ArrowRight, Truck, Calendar } from 'lucide-react';
import type { Recommendation } from '../../types';
import RiskBadge from '../ui/RiskBadge';
import ConfidenceScore from '../ui/ConfidenceScore';
import './RecommendationCard.css';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const navigate = useNavigate();

  return (
    <div className="recommendation-card animate-fade-in-up">

      {/* ---- Masthead ---- */}
      <div className="recommendation-card__masthead">
        <div className="recommendation-card__badge-row">
          <span className="rec-ai-badge">
            <Award size={10} />
            AI Recommended Strategy
          </span>
          <RiskBadge level={recommendation.risk} />
        </div>
        <div className="recommendation-card__metrics-top">
          <ConfidenceScore score={recommendation.confidence} size={36} strokeWidth={3} />
        </div>
      </div>

      {/* ---- Target Market + Net Revenue Hero ---- */}
      <div className="recommendation-card__target">
        <div className="recommendation-card__target-left">
          <div className="recommendation-card__label">Sell At</div>
          <h2 className="recommendation-card__market-name">
            {recommendation.recommendedMarket.name} APMC Market
          </h2>
          <div className="recommendation-card__sub">
            {recommendation.recommendedMarket.district}, {recommendation.recommendedMarket.state}
            &nbsp;·&nbsp;{recommendation.recommendedMarket.type}
          </div>
        </div>

        <div className="rec-net-callout">
          <div className="rec-net-callout__label">Expected Net Revenue</div>
          <div className="rec-net-callout__value">
            ₹{recommendation.netRevenue.toLocaleString('en-IN')}
          </div>
          <div className="rec-net-callout__sub">
            ₹{recommendation.netProfitPerQ}/q · {recommendation.confidence}% confidence
          </div>
        </div>
      </div>

      {/* ---- Metric Stripe ---- */}
      <div className="recommendation-card__grid">
        <div className="rec-metric">
          <span className="rec-metric__label">Expected Price</span>
          <span className="rec-metric__value rec-metric__value--green">
            ₹{recommendation.expectedPrice.toLocaleString()}<span style={{ fontSize: 11, fontWeight: 600, color: '#64748B' }}>/q</span>
          </span>
          <span className="rec-metric__sub">7-day APMC forecast</span>
        </div>

        <div className="rec-metric">
          <span className="rec-metric__label">Gross Revenue</span>
          <span className="rec-metric__value">
            ₹{recommendation.grossRevenue.toLocaleString()}
          </span>
          <span className="rec-metric__sub">before transport</span>
        </div>

        <div className="rec-metric">
          <span className="rec-metric__label">Transport Cost</span>
          <span className="rec-metric__value rec-metric__value--amber">
            <Truck size={13} />
            ₹{recommendation.transportCost.toLocaleString()}
          </span>
          <span className="rec-metric__sub">logistics overhead</span>
        </div>

        <div className="rec-metric">
          <span className="rec-metric__label">Selling Window</span>
          <span className="rec-metric__value">
            <Calendar size={13} />
            {recommendation.sellingWindowLabel}
          </span>
          <span className="rec-metric__sub">{recommendation.sellingWindowDays}-day window</span>
        </div>
      </div>

      {/* ---- Footer ---- */}
      <div className="recommendation-card__footer">
        <p className="recommendation-card__summary">
          {recommendation.insights[0]}
        </p>
        <button
          className="rec-cta-btn"
          onClick={() => navigate(`/recommendation/${recommendation.id}`)}
        >
          View Full Breakdown <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default RecommendationCard;
