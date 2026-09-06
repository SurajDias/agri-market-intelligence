import React from 'react';
import {
  ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ReferenceDot
} from 'recharts';
import type { ForecastPoint } from '../../types';

interface PriceChartProps {
  dataPoints: ForecastPoint[];
  height?: number;
  showForecastToggle?: boolean;
}

const PriceChart: React.FC<PriceChartProps> = ({
  dataPoints,
  height = 420,
}) => {
  // Find transition index where forecast starts
  const forecastStartIndex = dataPoints.findIndex(dp => dp.isForecasted);
  const splitDate = forecastStartIndex > 0 ? dataPoints[forecastStartIndex]?.date : undefined;

  // Last historical point & final forecast point for price markers
  const currentPricePoint = forecastStartIndex > 0 ? dataPoints[forecastStartIndex - 1] : dataPoints[0];
  const finalForecastPoint = dataPoints[dataPoints.length - 1];

  const formattedData = dataPoints.map((dp) => ({
    ...dp,
    historicalPrice: !dp.isForecasted ? dp.predictedPrice : null,
    forecastPrice: dp.isForecasted ? dp.predictedPrice : null,
    // Connect historical and forecast at bridge point
    forecastLine: dp.isForecasted || dp.date === dataPoints[forecastStartIndex - 1]?.date ? dp.predictedPrice : null,
    band: dp.isForecasted ? [dp.lowerBound, dp.upperBound] : null,
  }));

  const formatPrice = (val: number) => `₹${val.toLocaleString()}`;
  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })}`;
  };

  /* Professional Market Terminal Tooltip */
  const CustomTerminalTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data: ForecastPoint = payload[0].payload;
    const isForecast = data.isForecasted;

    return (
      <div className="terminal-tooltip">
        <div className="terminal-tooltip__header">
          <span className="terminal-tooltip__date">{formatDate(label)}</span>
          <span className={`terminal-tooltip__badge ${isForecast ? 'terminal-tooltip__badge--ai' : 'terminal-tooltip__badge--history'}`}>
            {isForecast ? 'AI Forecast' : 'Historical'}
          </span>
        </div>

        <div className="terminal-tooltip__body">
          <div className="terminal-tooltip__row">
            <span className="terminal-tooltip__label">Modal Price:</span>
            <span className="terminal-tooltip__value">₹{data.predictedPrice.toLocaleString()}<span className="terminal-tooltip__unit">/q</span></span>
          </div>

          {isForecast && (
            <>
              <div className="terminal-tooltip__row">
                <span className="terminal-tooltip__label">95% CI Range:</span>
                <span className="terminal-tooltip__range">₹{data.lowerBound.toLocaleString()} – ₹{data.upperBound.toLocaleString()}</span>
              </div>
              <div className="terminal-tooltip__row">
                <span className="terminal-tooltip__label">Variance:</span>
                <span className="terminal-tooltip__unit" style={{ fontWeight: 700, color: '#15803D' }}>
                  ±₹{Math.round((data.upperBound - data.lowerBound) / 2)}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="terminal-chart-wrapper">
      <div className="terminal-chart-header">
        <div>
          <div className="terminal-chart-title">Price History &amp; AI Trajectory Forecast</div>
          <div className="terminal-chart-sub">
            Solid line: Historical APMC modal price • Dashed line: AI 7-day predictive trajectory &amp; 95% confidence interval
          </div>
        </div>

        {/* Custom Terminal Legend Header & Toolbar */}
        <div className="flex items-center gap-4">
          <div className="terminal-chart-legend">
            <div className="terminal-legend-item">
              <span className="terminal-legend-dot" style={{ backgroundColor: '#15803D' }}></span>
              <span style={{ color: '#0F172A' }}>Historical</span>
            </div>
            <div className="terminal-legend-item">
              <span className="terminal-legend-dot" style={{ backgroundColor: '#D97706', borderRadius: '50%' }}></span>
              <span style={{ color: '#D97706' }}>AI Forecast</span>
            </div>
            <div className="terminal-legend-item">
              <span className="terminal-legend-dot" style={{ backgroundColor: 'rgba(34, 197, 94, 0.25)', border: '1px solid #86EFAC' }}></span>
              <span style={{ color: '#64748B' }}>95% CI Band</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={formattedData} margin={{ top: 25, right: 35, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} opacity={0.6} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#64748B"
              fontSize={11}
              fontWeight={600}
              tickLine={false}
              axisLine={{ stroke: '#CBD5E1' }}
            />
            <YAxis
              tickFormatter={formatPrice}
              stroke="#64748B"
              fontSize={11}
              fontWeight={600}
              tickLine={false}
              axisLine={{ stroke: '#CBD5E1' }}
              domain={['auto', 'auto']}
            />
            
            <Tooltip content={<CustomTerminalTooltip />} />

            {/* Shaded confidence interval band */}
            <Area
              type="monotone"
              dataKey="band"
              stroke="none"
              fill="#DCFCE7"
              fillOpacity={0.55}
              name="95% Confidence Band"
            />

            {/* Historical price line (Forest Green) */}
            <Line
              type="monotone"
              dataKey="historicalPrice"
              stroke="#15803D"
              strokeWidth={3}
              dot={{ r: 3.5, fill: '#15803D', strokeWidth: 0 }}
              activeDot={{ r: 6, fill: '#15803D', stroke: '#FFFFFF', strokeWidth: 2 }}
              name="historicalPrice"
            />

            {/* Forecasted price line (Restrained Harvest Amber/Orange) */}
            <Line
              type="monotone"
              dataKey="forecastLine"
              stroke="#D97706"
              strokeWidth={3}
              strokeDasharray="5 4"
              dot={{ r: 4.5, fill: '#D97706', strokeWidth: 0 }}
              activeDot={{ r: 6, fill: '#B45309', stroke: '#FFFFFF', strokeWidth: 2 }}
              name="forecastLine"
            />

            {/* Transition Forecast Start Marker */}
            {splitDate && (
              <ReferenceLine
                x={splitDate}
                stroke="#64748B"
                strokeDasharray="4 3"
                strokeWidth={1.5}
                label={{
                  value: 'Forecast Start ➔',
                  position: 'top',
                  fill: '#475569',
                  fontSize: 11,
                  fontWeight: 800,
                  offset: 10
                }}
              />
            )}

            {/* Key Price Marker: Current Price */}
            {currentPricePoint && (
              <ReferenceDot
                x={currentPricePoint.date}
                y={currentPricePoint.predictedPrice}
                r={5}
                fill="#15803D"
                stroke="#FFFFFF"
                strokeWidth={2}
                label={{
                  value: `Current: ₹${currentPricePoint.predictedPrice}`,
                  position: 'bottom',
                  fill: '#15803D',
                  fontSize: 10,
                  fontWeight: 800,
                  offset: 8
                }}
              />
            )}

            {/* Key Price Marker: Forecast End Price */}
            {finalForecastPoint && (
              <ReferenceDot
                x={finalForecastPoint.date}
                y={finalForecastPoint.predictedPrice}
                r={5}
                fill="#D97706"
                stroke="#FFFFFF"
                strokeWidth={2}
                label={{
                  value: `Target: ₹${finalForecastPoint.predictedPrice}`,
                  position: 'top',
                  fill: '#B45309',
                  fontSize: 10,
                  fontWeight: 800,
                  offset: 8
                }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PriceChart;
