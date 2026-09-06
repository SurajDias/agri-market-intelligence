import React, { useState } from 'react';
import { COMMODITIES, DISTRICTS } from '../../services/mockData';
import type { SimulatorInput } from '../../types';
import { Sparkles, SlidersHorizontal } from 'lucide-react';
import './SimulatorInputPanel.css';

interface SimulatorInputPanelProps {
  onAnalyze: (input: SimulatorInput) => void;
  isLoading?: boolean;
}

const SimulatorInputPanel: React.FC<SimulatorInputPanelProps> = ({ onAnalyze, isLoading }) => {
  const [commodity, setCommodity] = useState('tomato');
  const [quantity, setQuantity] = useState(5000);
  const [origin, setOrigin] = useState('Mandya');
  const [sellingDate, setSellingDate] = useState(
    new Date(Date.now() + 2 * 86400000).toISOString().split('T')[0]
  );
  const [cropQuality, setCropQuality] = useState<'A' | 'B' | 'C'>('A');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze({ commodity, quantity, origin, sellingDate, cropQuality });
  };

  return (
    <form className="sim-input-shell" onSubmit={handleSubmit}>
      {/* Header */}
      <div className="sim-input-header">
        <div className="sim-input-header-left">
          <span className="sim-input-step-chip">1</span>
          <div>
            <div className="sim-input-title">
              <SlidersHorizontal size={12} style={{ display: 'inline', marginRight: 5 }} />
              Simulation Inputs
            </div>
            <div className="sim-input-subtitle">Configure your crop, batch, and logistics parameters</div>
          </div>
        </div>
      </div>

      {/* Inline field row */}
      <div className="sim-input-fields">
        <div className="sim-field-cell">
          <label className="sim-field-label" htmlFor="sim-commodity">Commodity</label>
          <select
            id="sim-commodity"
            className="select"
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
          >
            {COMMODITIES.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="sim-field-cell">
          <label className="sim-field-label" htmlFor="sim-quantity">Batch Volume (kg)</label>
          <input
            id="sim-quantity"
            type="number"
            className="input"
            value={quantity}
            step={500}
            min={100}
            onChange={(e) => setQuantity(Number(e.target.value))}
          />
        </div>

        <div className="sim-field-cell">
          <label className="sim-field-label" htmlFor="sim-origin">Origin District</label>
          <select
            id="sim-origin"
            className="select"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
          >
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div className="sim-field-cell">
          <label className="sim-field-label" htmlFor="sim-date">Target Selling Date</label>
          <input
            id="sim-date"
            type="date"
            className="input"
            value={sellingDate}
            onChange={(e) => setSellingDate(e.target.value)}
          />
        </div>

        <div className="sim-field-cell">
          <label className="sim-field-label" htmlFor="sim-quality">Crop Grade</label>
          <select
            id="sim-quality"
            className="select"
            value={cropQuality}
            onChange={(e) => setCropQuality(e.target.value as 'A' | 'B' | 'C')}
          >
            <option value="A">Grade A — Premium Export</option>
            <option value="B">Grade B — Standard Mandi</option>
            <option value="C">Grade C — Fair Average</option>
          </select>
        </div>
      </div>

      {/* CTA */}
      <div className="sim-input-cta">
        <span className="sim-cta-hint">AI will rank all nearby APMCs and compute your optimal selling strategy.</span>
        <button
          type="submit"
          className={`sim-analyze-btn ${isLoading ? 'sim-analyze-btn--loading' : ''}`}
          disabled={isLoading}
        >
          <Sparkles size={15} />
          {isLoading ? 'Running Decision Engine…' : 'Analyze Best Decision'}
        </button>
      </div>
    </form>
  );
};

export default SimulatorInputPanel;
