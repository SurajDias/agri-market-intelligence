import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Award, CheckCircle, Truck, Calendar, ShieldCheck } from 'lucide-react';
import { MOCK_RECOMMENDATION } from '../services/mockData';
import RiskBadge from '../components/ui/RiskBadge';
import ConfidenceScore from '../components/ui/ConfidenceScore';
import RecommendationFactorsChart from '../components/charts/RecommendationFactorsChart';

const RecommendationDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const rec = MOCK_RECOMMENDATION;

  return (
    <div className="recommendation-details-page flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Link to="/dashboard" className="btn btn-ghost btn-sm">
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>

      <div className="card card-highlight flex flex-col gap-4">
        <div className="flex justify-between items-start">
          <div>
            <span className="badge badge-primary mb-2">🏆 BEST OPTIMAL STRATEGY</span>
            <h1 className="text-3xl font-bold text-primary">Target: {rec.recommendedMarket.name} APMC</h1>
            <p className="text-sm text-muted">{rec.recommendedMarket.district}, {rec.recommendedMarket.state}</p>
          </div>
          <div className="flex items-center gap-4">
            <RiskBadge level={rec.risk} />
            <ConfidenceScore score={rec.confidence} size={48} />
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 bg-surface p-4 rounded-xl border border-border">
          <div>
            <span className="text-xs text-muted">Expected Price</span>
            <div className="text-xl font-bold">₹{rec.expectedPrice}/q</div>
          </div>
          <div>
            <span className="text-xs text-muted">Expected Net Revenue</span>
            <div className="text-xl font-bold text-primary">₹{rec.netRevenue.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-xs text-muted">Transport Cost</span>
            <div className="text-xl font-bold">₹{rec.transportCost.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-xs text-muted">Selling Window</span>
            <div className="text-xl font-bold">{rec.sellingWindowLabel}</div>
          </div>
        </div>
      </div>

      {/* Rationale */}
      <RecommendationFactorsChart factors={rec.factors} />

      {/* Key Insights List */}
      <div className="card flex flex-col gap-3">
        <h3 className="section-title">Key Operational Advisories</h3>
        <ul className="flex flex-col gap-2">
          {rec.insights.map((ins, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-secondary">
              <CheckCircle size={16} className="text-primary mt-1 flex-shrink-0" />
              <span>{ins}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default RecommendationDetails;
