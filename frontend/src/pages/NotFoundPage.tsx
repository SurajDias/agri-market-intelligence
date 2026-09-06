import React from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';

const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-center p-6">
      <AlertCircle size={48} className="text-warning mb-4" />
      <h1 className="text-3xl font-bold mb-2">404 — Page Not Found</h1>
      <p className="text-muted mb-6">The requested market intelligence route does not exist.</p>
      <Link to="/dashboard" className="btn btn-primary">Return to Dashboard</Link>
    </div>
  );
};

export default NotFoundPage;
