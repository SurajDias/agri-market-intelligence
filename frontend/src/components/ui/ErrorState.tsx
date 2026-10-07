import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import './ErrorState.css';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message = 'An unexpected error occurred while fetching information from the server.',
  onRetry,
}) => {
  return (
    <div className="error-state">
      <div className="error-state__icon">
        <AlertTriangle size={32} />
      </div>
      <h3 className="error-state__title">{title}</h3>
      <p className="error-state__message">{message}</p>
      {onRetry && (
        <button className="btn btn-secondary btn-sm" onClick={onRetry}>
          <RefreshCw size={14} />
          Retry Connection
        </button>
      )}
    </div>
  );
};

export default ErrorState;
