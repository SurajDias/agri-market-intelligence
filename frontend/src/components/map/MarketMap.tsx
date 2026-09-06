import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { MarketComparison } from '../../types';
import 'leaflet/dist/leaflet.css';
import './MarketMap.css';

interface MarketMapProps {
  markets: MarketComparison[];
  onSelectMarket?: (market: MarketComparison) => void;
  height?: string;
}

const MarketMap: React.FC<MarketMapProps> = ({
  markets,
  onSelectMarket,
  height = '500px',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Leaflet map centered on Karnataka
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current).setView([13.0, 77.0], 8);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear old markers
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    /**
     * Marker colour:
     *  - Recommended (Top Pick) → deep forest green #15803D
     *  - LOW risk               → forest green #22C55E
     *  - MEDIUM risk            → harvest orange #D97706
     *  - HIGH risk              → muted red #DC2626
     */
    const getMarkerColor = (risk: string, isRec: boolean) => {
      if (isRec) return '#15803D';
      if (risk === 'LOW') return '#22C55E';
      if (risk === 'MEDIUM') return '#D97706';
      return '#DC2626';
    };

    const createCustomIcon = (risk: string, isRec: boolean) => {
      const color = getMarkerColor(risk, isRec);
      const outerSize = isRec ? 42 : 30;
      const innerSize = isRec ? 26 : 18;
      const ringColor = isRec ? 'rgba(21,128,61,0.22)' : 'transparent';

      return L.divIcon({
        className: 'custom-map-pin',
        html: `
          <div style="
            width: ${outerSize}px;
            height: ${outerSize}px;
            border-radius: 50%;
            background: ${ringColor};
            display: flex;
            align-items: center;
            justify-content: center;
          ">
            <div style="
              background-color: ${color};
              width: ${innerSize}px;
              height: ${innerSize}px;
              border-radius: 50%;
              border: 2.5px solid #ffffff;
              box-shadow: 0 3px 8px rgba(0,0,0,0.25), 0 1px 3px rgba(0,0,0,0.15);
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-weight: 900;
              font-size: ${isRec ? '11px' : '8px'};
              letter-spacing: -0.5px;
            ">${isRec ? '★' : '₹'}</div>
          </div>`,
        iconSize: [outerSize, outerSize],
        iconAnchor: [outerSize / 2, outerSize / 2],
      });
    };

    // Add markers for markets
    markets.forEach((m) => {
      const icon = createCustomIcon(m.risk, m.isRecommended);
      const marker = L.marker([m.market.lat, m.market.lng], { icon }).addTo(map);

      const riskColor = m.risk === 'LOW' ? '#15803D' : m.risk === 'MEDIUM' ? '#B45309' : '#B91C1C';
      const riskBg   = m.risk === 'LOW' ? '#DCFCE7' : m.risk === 'MEDIUM' ? '#FEF3C7' : '#FEE2E2';

      const popupContent = `
        <div class="map-popup-card">
          <div class="map-popup-title">${m.market.name} APMC</div>
          <div class="map-popup-sub">${m.market.district}, ${m.market.state}</div>
          <hr class="map-popup-divider" />
          <div class="map-popup-row">
            <span class="map-popup-key">Forecast Price</span>
            <span class="map-popup-val">₹${m.forecastPrice.toLocaleString()}/q</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-key">Net Revenue</span>
            <span class="map-popup-val map-popup-val--green">₹${m.expectedNetProfit.toLocaleString()}</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-key">Transport</span>
            <span class="map-popup-val">₹${m.transportCostPerQ}/q · ${m.transportDistance} km</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-key">Arrivals</span>
            <span class="map-popup-val">${m.arrivals} t/day</span>
          </div>
          <div class="map-popup-row">
            <span class="map-popup-key">Risk</span>
            <span style="font-size:11px;font-weight:800;padding:1px 7px;border-radius:3px;background:${riskBg};color:${riskColor}">${m.risk}</span>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent, {
        maxWidth: 210,
        className: 'agrimark-popup',
      });
      marker.on('click', () => {
        if (onSelectMarket) onSelectMarket(m);
      });
    });

  }, [markets, onSelectMarket]);

  return (
    <div className="market-map-element" style={{ height }} ref={mapContainerRef} />
  );
};

export default MarketMap;
