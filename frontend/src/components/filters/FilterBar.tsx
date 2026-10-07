import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import { COMMODITIES, STATES, DISTRICTS } from '../../services/mockData';
import type { FilterState } from '../../types';
import './FilterBar.css';

interface FilterBarProps {
  filters: FilterState;
  onChange: (newFilters: FilterState) => void;
  onReset?: () => void;
}

const FilterBar: React.FC<FilterBarProps> = ({ filters, onChange, onReset }) => {
  const handleChange = (key: keyof FilterState, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <div className="filter-bar">
      <div className="filter-bar__title">
        <Filter size={16} />
        <span>Filters</span>
      </div>

      <div className="filter-bar__fields">
        <div className="filter-group">
          <label className="input-label" htmlFor="filter-commodity">Commodity</label>
          <select
            id="filter-commodity"
            className="select select-sm"
            value={filters.commodity}
            onChange={(e) => handleChange('commodity', e.target.value)}
          >
            {COMMODITIES.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="input-label" htmlFor="filter-state">State</label>
          <select
            id="filter-state"
            className="select select-sm"
            value={filters.state}
            onChange={(e) => handleChange('state', e.target.value)}
          >
            <option value="All">All States</option>
            {STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="input-label" htmlFor="filter-district">District</label>
          <select
            id="filter-district"
            className="select select-sm"
            value={filters.district}
            onChange={(e) => handleChange('district', e.target.value)}
          >
            <option value="All">All Districts</option>
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>
      </div>

      {onReset && (
        <button className="btn btn-ghost btn-sm filter-bar__reset" onClick={onReset}>
          <RotateCcw size={14} />
          Reset
        </button>
      )}
    </div>
  );
};

export default FilterBar;
