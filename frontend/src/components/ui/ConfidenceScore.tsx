import React from 'react';
import './ConfidenceScore.css';

interface ConfidenceScoreProps {
  score: number; // 0 - 100
  size?: number;
  strokeWidth?: number;
}

const ConfidenceScore: React.FC<ConfidenceScoreProps> = ({
  score,
  size = 48,
  strokeWidth = 4,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (score >= 80) return 'var(--color-positive)';
    if (score >= 60) return 'var(--color-warning)';
    return 'var(--color-danger)';
  };

  return (
    <div className="confidence-score" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="confidence-score__svg">
        <circle
          className="confidence-score__bg"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="confidence-score__progress"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          stroke={getColor()}
        />
      </svg>
      <div className="confidence-score__text" style={{ fontSize: size * 0.28 }}>
        {score}%
      </div>
    </div>
  );
};

export default ConfidenceScore;
