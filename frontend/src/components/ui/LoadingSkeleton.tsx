import React from 'react';

interface LoadingSkeletonProps {
  type?: 'card' | 'table' | 'chart' | 'text';
  rows?: number;
  height?: number;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  type = 'card',
  rows = 5,
  height = 200,
}) => {
  if (type === 'table') {
    return (
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              {Array.from({ length: 6 }).map((_, i) => (
                <th key={i}><div className="skeleton" style={{ height: 16, width: '80%' }} /></th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, i) => (
              <tr key={i}>
                {Array.from({ length: 6 }).map((_, j) => (
                  <td key={j}><div className="skeleton" style={{ height: 18, width: '90%' }} /></td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div className="chart-container" style={{ height }}>
        <div className="skeleton" style={{ height: 20, width: '30%', marginBottom: 12 }} />
        <div className="skeleton" style={{ height: 14, width: '50%', marginBottom: 24 }} />
        <div className="skeleton" style={{ height: height - 100, width: '100%' }} />
      </div>
    );
  }

  if (type === 'text') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="skeleton" style={{ height: 16, width: i % 2 === 0 ? '100%' : '75%' }} />
        ))}
      </div>
    );
  }

  return (
    <div className="card" style={{ height }}>
      <div className="skeleton" style={{ height: 20, width: '40%', marginBottom: 16 }} />
      <div className="skeleton" style={{ height: 36, width: '60%', marginBottom: 12 }} />
      <div className="skeleton" style={{ height: 16, width: '80%' }} />
    </div>
  );
};

export default LoadingSkeleton;
