import React from 'react';
import { TrendingUp, TrendingDown, Minus, IndianRupee, Store, Target, Award, Shield } from 'lucide-react';
import type { TrendDirection } from '../../types';
import './KPICard.css';

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  changeLabel?: string;
  trend?: TrendDirection;
  icon?: string;
  description?: string;
  accentColor?: string;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  change,
  changeLabel = 'vs last period',
  trend,
  icon = 'rupee',
  description,
}) => {
  const renderIcon = () => {
    switch (icon) {
      case 'rupee': return <IndianRupee size={20} />;
      case 'store': return <Store size={20} />;
      case 'target': return <Target size={20} />;
      case 'award': return <Award size={20} />;
      case 'shield': return <Shield size={20} />;
      default: return <IndianRupee size={20} />;
    }
  };

  const getTrendBadge = () => {
    if (change === undefined) return null;
    const isPositive = change > 0;
    const isNegative = change < 0;

    return (
      <div className={`kpi-card__change ${isPositive ? 'kpi-card__change--positive' : isNegative ? 'kpi-card__change--negative' : 'kpi-card__change--neutral'}`}>
        {isPositive && <TrendingUp size={12} />}
        {isNegative && <TrendingDown size={12} />}
        {!isPositive && !isNegative && <Minus size={12} />}
        <span>{change > 0 ? `+${change}%` : `${change}%`}</span>
      </div>
    );
  };

  return (
    <div className="kpi-card animate-fade-in">
      <div className="kpi-card__header">
        <span className="kpi-card__title">{title}</span>
        <div className="kpi-card__icon">{renderIcon()}</div>
      </div>
      <div className="kpi-card__body">
        <div className="kpi-card__value-row">
          <span className="kpi-card__value">{value}</span>
          {unit && <span className="kpi-card__unit">{unit}</span>}
        </div>
        {(change !== undefined || description) && (
          <div className="kpi-card__footer">
            {getTrendBadge()}
            {changeLabel && <span className="kpi-card__change-label">{changeLabel}</span>}
            {description && <span className="kpi-card__desc">{description}</span>}
          </div>
        )}
      </div>
    </div>
  );
};

export default KPICard;
