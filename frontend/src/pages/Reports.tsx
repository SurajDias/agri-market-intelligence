import React from 'react';
import { Download, FileText, Share2, Sparkles } from 'lucide-react';
import { MOCK_INSIGHTS, MOCK_MARKET_COMPARISONS } from '../services/mockData';
import InsightCard from '../components/ui/InsightCard';

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
        <p className="text-sm text-secondary leading-relaxed mb-4">
          Tomato prices across Karnataka mandis have exhibited a strong 8.4% upward trajectory over the past week, driven by restricted arrivals from Kolar district. Ramanagara APMC represents the highest profit capture opportunity for Mandya-based aggregators, yielding an expected net margin of ₹1,43,500 on 5,000 kg shipments. Logistics costs remain optimal via the SH-17 route.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="card flex flex-col gap-3">
          <h3 className="chart-title">Market Opportunities & Advisories</h3>
          <div className="flex flex-col gap-3">
            {MOCK_INSIGHTS.map((ins) => (
              <InsightCard key={ins.id} insight={ins} />
            ))}
          </div>
        </div>

        <div className="card flex flex-col gap-3">
          <h3 className="chart-title">Top Market Net Revenue Rankings</h3>
          <div className="flex flex-col gap-2">
            {MOCK_MARKET_COMPARISONS.map((m, i) => (
              <div key={m.market.id} className="flex justify-between items-center p-3 bg-surface-hover rounded-lg border border-border">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-muted">#{i + 1}</span>
                  <div>
                    <span className="font-bold text-primary">{m.market.name}</span>
                    <div className="text-xs text-muted">{m.market.district}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-primary">₹{m.expectedNetProfit.toLocaleString()}</div>
                  <div className="text-xs text-muted">₹{m.forecastPrice}/q forecast</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
