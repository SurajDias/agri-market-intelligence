import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import EmptyState from '../components/ui/EmptyState';

const RecommendationDetails: React.FC = () => {
  useParams<{ id: string }>();

  return (
    <div className="recommendation-details-page flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Link to="/dashboard" className="btn btn-ghost btn-sm">
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>

      <EmptyState
        title="No verified recommendation available"
        description="Recommendation details require actual market observations and preserved evidence. No recommendation is fabricated."
      />
    </div>
  );
};

export default RecommendationDetails;
