import React from 'react';
import { Download, Share2, Sparkles } from 'lucide-react';
import EmptyState from '../components/ui/EmptyState';

const ReportsPage: React.FC = () => {
  return (
    <div className="reports-page flex flex-col gap-6">
      <div className="section-header">
        <div>
          <h1 className="section-title">Reports & Executive Market Insights</h1>
          <p className="section-subtitle">
            Automated intelligence reports for FPO directors and commodity traders.
          </p>
        </div>

        <div className="flex gap-2">
          <button className="btn btn-secondary btn-sm">
            <Share2 size={14} /> Share Report
          </button>
          <button className="btn btn-primary btn-sm">
            <Download size={14} /> Export PDF
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="text-primary" size={20} />
          <h3 className="section-title">Executive Summary — Weekly Market Briefing</h3>
        </div>
        <EmptyState
          title="No verified market intelligence available"
          description="Reports remain empty until canonical, verified market observations support an evidence-backed briefing."
        />
      </div>
    </div>
  );
};

export default ReportsPage;
