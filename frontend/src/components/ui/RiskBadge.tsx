import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';
import type { RiskLevel } from '../../types';

interface RiskBadgeProps {
  level: RiskLevel;
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ level }) => {
  const getConfig = () => {
    switch (level) {
      case 'LOW':
        return {
          label: 'LOW RISK',
          class: 'badge-positive',
          icon: <ShieldCheck size={12} />
        };
      case 'MEDIUM':
        return {
          label: 'MEDIUM RISK',
          class: 'badge-warning',
          icon: <AlertTriangle size={12} />
        };
      case 'HIGH':
        return {
          label: 'HIGH RISK',
          class: 'badge-danger',
          icon: <ShieldAlert size={12} />
        };
    }
  };

  const config = getConfig();

  return (
    <span className={`badge ${config.class}`}>
      {config.icon}
      {config.label}
    </span>
  );
};

export default RiskBadge;
