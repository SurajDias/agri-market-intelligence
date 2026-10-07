import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, Cell
} from 'recharts';
import type { MarketComparison } from '../../types';

interface MarketComparisonChartProps {
  markets: MarketComparison[];
  height?: number;
}

const MarketComparisonChart: React.FC<MarketComparisonChartProps> = ({
  markets,
  height = 320,
}) => {
  const chartData = markets.map((m) => ({
    name: m.market.name,
    expectedRevenue: m.expectedRevenue,
    transportCost: m.transportCostPerQ * (5000 / 100), // Assuming 5000kg load
    netProfit: m.expectedNetProfit,
    isRecommended: m.isRecommended,
  }));

  const formatCurrency = (val: number) => `₹${(val / 1000).toFixed(1)}k`;

  return (
    <div className="chart-container">
      <div className="chart-title">Net Profit Comparison Across Markets</div>
      <div className="chart-subtitle">
        Comparing expected gross revenue minus estimated transport cost for 5,000 kg shipment.
      </div>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 30, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
            <XAxis dataKey="name" stroke="#6b7280" fontSize={12} tickLine={false} />
            <YAxis tickFormatter={formatCurrency} stroke="#6b7280" fontSize={12} tickLine={false} />
            <Tooltip
              formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, '']}
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
            />
            <Legend verticalAlign="top" height={36} />
            <Bar dataKey="netProfit" name="Expected Net Profit (₹)" radius={[6, 6, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isRecommended ? '#1b5e20' : '#7cb342'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MarketComparisonChart;
