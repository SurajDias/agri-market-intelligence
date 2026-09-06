import React, { useState } from 'react';
import { ArrowUpDown, Award, CheckCircle2 } from 'lucide-react';
import type { MarketComparison } from '../../types';
import RiskBadge from '../ui/RiskBadge';
import ConfidenceScore from '../ui/ConfidenceScore';
import './MarketTable.css';

interface MarketTableProps {
  markets: MarketComparison[];
  onSelectMarket?: (market: MarketComparison) => void;
}

type SortField = 'name' | 'currentPrice' | 'forecastPrice' | 'transportCost' | 'netProfit' | 'confidence';

const MarketTable: React.FC<MarketTableProps> = ({ markets, onSelectMarket }) => {
  const [sortField, setSortField] = useState<SortField>('netProfit');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedMarkets = [...markets].sort((a, b) => {
    let valA: any = 0;
    let valB: any = 0;

    switch (sortField) {
      case 'name': valA = a.market.name; valB = b.market.name; break;
      case 'currentPrice': valA = a.currentPrice; valB = b.currentPrice; break;
      case 'forecastPrice': valA = a.forecastPrice; valB = b.forecastPrice; break;
      case 'transportCost': valA = a.transportCostPerQ; valB = b.transportCostPerQ; break;
      case 'netProfit': valA = a.expectedNetProfit; valB = b.expectedNetProfit; break;
      case 'confidence': valA = a.confidence; valB = b.confidence; break;
    }

    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  return (
    <div className="table-wrapper">
      <table className="table market-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('name')} className={sortField === 'name' ? 'sorted' : ''}>
              Market Name <ArrowUpDown size={12} />
            </th>
            <th onClick={() => handleSort('currentPrice')} className={`numeric ${sortField === 'currentPrice' ? 'sorted' : ''}`}>
              Current Price <ArrowUpDown size={12} />
            </th>
            <th onClick={() => handleSort('forecastPrice')} className={`numeric ${sortField === 'forecastPrice' ? 'sorted' : ''}`}>
              7-Day Forecast <ArrowUpDown size={12} />
            </th>
            <th onClick={() => handleSort('transportCost')} className={`numeric ${sortField === 'transportCost' ? 'sorted' : ''}`}>
              Transport Cost <ArrowUpDown size={12} />
            </th>
            <th onClick={() => handleSort('netProfit')} className={`numeric ${sortField === 'netProfit' ? 'sorted' : ''}`}>
              Expected Net Revenue <ArrowUpDown size={12} />
            </th>
            <th>Risk Level</th>
            <th onClick={() => handleSort('confidence')} className={sortField === 'confidence' ? 'sorted' : ''}>
              Confidence <ArrowUpDown size={12} />
            </th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {sortedMarkets.map((m) => (
            <tr
              key={m.market.id}
              className={`market-table__row ${m.isRecommended ? 'market-table__row--recommended' : ''}`}
            >
              <td>
                <div className="market-table__name-cell">
                  <span className="font-semibold text-primary">{m.market.name}</span>
                  <span className="text-xs text-muted">{m.market.district}, {m.market.state}</span>
                  {m.isRecommended && (
                    <span className="badge badge-primary">
                      <Award size={10} /> 🏆 Recommended
                    </span>
                  )}
                </div>
              </td>
              <td className="numeric font-semibold">₹{m.currentPrice.toLocaleString()}/q</td>
              <td className="numeric font-semibold text-positive">₹{m.forecastPrice.toLocaleString()}/q</td>
              <td className="numeric">₹{m.transportCostPerQ}/q ({m.transportDistance} km)</td>
              <td className="numeric market-table__net-profit-cell">
                ₹{m.expectedNetProfit.toLocaleString()}
              </td>
              <td><RiskBadge level={m.risk} /></td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <ConfidenceScore score={m.confidence} size={32} strokeWidth={3} />
                </div>
              </td>
              <td>
                <button
                  className={`btn btn-sm ${m.isRecommended ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => onSelectMarket?.(m)}
                >
                  {m.isRecommended ? 'Selected' : 'Select'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default MarketTable;
