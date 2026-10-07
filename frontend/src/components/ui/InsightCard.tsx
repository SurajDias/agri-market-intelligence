import React from 'react';
import { Lightbulb, AlertCircle, Info, ShieldAlert } from 'lucide-react';
import type { InsightCard as InsightType } from '../../types';
import './InsightCard.css';

interface InsightCardProps {
  insight: InsightType;
}

const InsightCard: React.FC<InsightCardProps> = ({ insight }) => {
  const getIcon = () => {
    switch (insight.type) {
      case 'OPPORTUNITY': return <Lightbulb className="insight-icon insight-icon--opportunity" size={18} />;
      case 'RISK': return <AlertCircle className="insight-icon insight-icon--risk" size={18} />;
      case 'ALERT': return <ShieldAlert className="insight-icon insight-icon--alert" size={18} />;
      case 'INFO':
      default:
        return <Info className="insight-icon insight-icon--info" size={18} />;
    }
  };

  return (
    <div className={`insight-card insight-card--${insight.type.toLowerCase()}`}>
      <div className="insight-card__header">
        {getIcon()}
        <span className="insight-card__title">{insight.title}</span>
      </div>
      <p className="insight-card__body">{insight.body}</p>
      {insight.impact && (
        <div className="insight-card__footer">
          <span className="insight-card__impact-label">Expected Impact:</span>
          <span className="insight-card__impact-val">{insight.impact}</span>
        </div>
      )}
    </div>
  );
};

export default InsightCard;
