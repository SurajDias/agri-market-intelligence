import React, { useState } from 'react';
import SimulatorInputPanel from '../components/simulator/SimulatorInputPanel';
import SimulatorResult from '../components/simulator/SimulatorResult';
import ScenarioComparison from '../components/simulator/ScenarioComparison';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import { simulatorService } from '../services/simulatorService';
import type { SimulatorInput, SimulatorResult as SimResultType } from '../types';
import EmptyState from '../components/ui/EmptyState';
import { BrainCircuit } from 'lucide-react';
import './DecisionSimulator.css';

const DecisionSimulatorPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimResultType | null>(null);

  const handleAnalyze = async (input: SimulatorInput) => {
    setLoading(true);
    try {
      const simRes = await simulatorService.runSimulation(input);
      setResult(simRes);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="decision-simulator-page">

      {/* Page Header */}
      <div className="sim-page-header">
        <div className="sim-page-header-inner">
          <div className="sim-page-title-row">
            <div className="sim-page-icon">
              <BrainCircuit size={18} color="#15803D" />
            </div>
            <div>
              <h1 className="section-title" style={{ marginBottom: 0 }}>Decision Simulator</h1>
              <p className="section-subtitle" style={{ marginTop: 2 }}>
                Configure your crop parameters and let the AI compute your optimal selling strategy across all nearby APMCs.
              </p>
            </div>
          </div>

          {/* Workflow breadcrumb */}
          <div className="sim-workflow-trail">
            <span className="sim-workflow-step sim-workflow-step--done">
              <span className="sim-workflow-dot">1</span> Inputs
            </span>
            <span className="sim-workflow-arrow">›</span>
            <span className={`sim-workflow-step ${result ? 'sim-workflow-step--done' : ''}`}>
              <span className="sim-workflow-dot">2</span> AI Decision
            </span>
            <span className="sim-workflow-arrow">›</span>
            <span className={`sim-workflow-step ${result ? 'sim-workflow-step--done' : ''}`}>
              <span className="sim-workflow-dot">3</span> What-If
            </span>
          </div>
        </div>
      </div>

      {/* Step 1 — Input Panel */}
      <SimulatorInputPanel onAnalyze={handleAnalyze} isLoading={loading} />

      {/* Step 2 + 3 — Results */}
      {loading ? (
        <div className="sim-loading-shell">
          <div className="sim-loading-label">
            <span className="sim-loading-spinner" />
            Running AI decision engine across 24 markets…
          </div>
          <LoadingSkeleton type="card" height={280} />
        </div>
      ) : (
        result ? (
          <>
            {/* Step 2 — AI Recommendation + Tabs */}
            <SimulatorResult
              recommendation={result.recommendation}
              allMarkets={result.marketComparisons}
            />

            {/* Step connector before What-If */}
            <div className="sim-between-connector">
              <div className="sim-between-line" />
              <span className="sim-between-label">What-If Scenario</span>
              <div className="sim-between-line" />
            </div>

            {/* Step 3 — Scenario Comparison */}
            <ScenarioComparison
              currentMarket={result.marketComparisons[0]}
              alternativeMarkets={result.marketComparisons.slice(1)}
            />
          </>
        ) : (
          <EmptyState
            title="No verified market data available"
            description="The simulator requires canonical market observations and compatible backend inputs. No scenario was fabricated."
          />
        )
      )}
    </div>
  );
};

export default DecisionSimulatorPage;
