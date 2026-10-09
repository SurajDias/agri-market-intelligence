import React, { useState, useEffect } from 'react';
import {
  ShieldCheck, Database, AlertTriangle, RefreshCw, CheckCircle,
  Globe, Cloud, Map, BarChart2, Cpu, GitMerge, ArrowRight
} from 'lucide-react';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';
import EmptyState from '../components/ui/EmptyState';
import { dataQualityService } from '../services/dataQualityService';
import type { DataQuality, DataSource } from '../types';
import './DataQuality.css';

/* ---- Relative time ---- */
const relativeTime = (iso: string) => {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

/* ---- Source Lucide icon & style by id ---- */
const sourceIconConfig = (id: string): { icon: React.ReactNode; iconClass: string } => {
  const props = { size: 14 };
  if (id === 'agmarknet') return { icon: <Database {...props} />,  iconClass: 'dq-src-icon--ok'   };
  if (id === 'datagov')   return { icon: <Globe   {...props} />,   iconClass: 'dq-src-icon'        };
  if (id === 'weather')   return { icon: <Cloud   {...props} />,   iconClass: 'dq-src-icon--warn'  };
  if (id === 'roads')     return { icon: <Map     {...props} />,   iconClass: 'dq-src-icon'        };
  return                         { icon: <Database {...props} />,  iconClass: 'dq-src-icon'        };
};

/* ---- Inline quality score bar + value ---- */
const QualityCell: React.FC<{ score: number }> = ({ score }) => {
  const isGreen = score >= 90;
  const cls     = isGreen ? 'green' : 'amber';
  return (
    <div className="dq-quality-cell">
      <span className={`dq-quality-score dq-quality-score--${cls}`}>{score}%</span>
      <div className="dq-quality-bar-track">
        <div
          className={`dq-quality-bar-fill dq-quality-bar-fill--${cls}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};

/* ---- Pipeline nodes ---- */
type PipelineStatus = 'ok' | 'warn';
interface PipelineNode { label: string; sub: string; icon: React.ReactNode; status: PipelineStatus; }

const PIPELINE: PipelineNode[] = [
  { label: 'Sources',    sub: '4 feeds',      icon: <Database  size={13} />, status: 'ok'   },
  { label: 'Ingestion',  sub: '847K rows',     icon: <ArrowRight size={13} />, status: 'ok'   },
  { label: 'Cleaning',   sub: 'ETL pass',      icon: <GitMerge  size={13} />, status: 'ok'   },
  { label: 'Validation', sub: '1 stale src',   icon: <AlertTriangle size={13} />, status: 'warn' },
  { label: 'AI Models',  sub: '87% conf.',     icon: <Cpu       size={13} />, status: 'ok'   },
];

/* ================================================================
   Main Page Component
   ================================================================ */
const DataQualityPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [quality, setQuality] = useState<DataQuality | null>(null);

  useEffect(() => {
    dataQualityService.getDataQuality()
      .then((res) => setQuality(res))
      .catch(() => setQuality(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="data-quality-page">

      {/* ---- Header ---- */}
      <div className="dq-header-row">
        <div>
          <h1 className="section-title">Data Quality &amp; Pipeline Health</h1>
          <p className="section-subtitle">
            Real-time ingestion status, ETL health, and data validation for all upstream government feeds.
          </p>
        </div>
        <div className="dq-sync-pill">
          <span className="dq-sync-live" />
          Last sync: {quality ? relativeTime(quality.lastUpdated) : '—'}
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col gap-4">
          <LoadingSkeleton type="card" height={72} />
          <LoadingSkeleton type="table" rows={4} />
        </div>
      ) : !quality || quality.recordsProcessed === 0 ? (
        <EmptyState
          title="No verified market data available"
          description="Data-quality metrics will appear after a verified source is ingested. The database currently contains no market-price observations."
        />
      ) : quality && (
        <>
          {/* ================================================================
              KPI BAR — 5 metrics in one horizontal strip
              ================================================================ */}
          <div className="dq-kpi-bar">

            {/* Overall health */}
            <div className="dq-kpi-item">
              <div className="dq-kpi-item__label">
                <ShieldCheck size={11} />
                Pipeline Health
              </div>
              <div className="dq-kpi-item__value dq-kpi-item__value--green">
                {quality.overallScore}%
              </div>
              <div className="dq-kpi-item__sub">Overall quality score</div>
              <span className="dq-kpi-status-chip dq-kpi-status-chip--green">
                <CheckCircle size={8} /> Operational
              </span>
            </div>

            {/* Records processed */}
            <div className="dq-kpi-item">
              <div className="dq-kpi-item__label">
                <Database size={11} />
                Records Processed
              </div>
              <div className="dq-kpi-item__value">
                {quality.recordsProcessed.toLocaleString('en-IN')}
              </div>
              <div className="dq-kpi-item__sub">Daily raw rows ingested</div>
            </div>

            {/* Markets covered */}
            <div className="dq-kpi-item">
              <div className="dq-kpi-item__label">
                <Globe size={11} />
                Markets
              </div>
              <div className="dq-kpi-item__value">{quality.marketsCount}</div>
              <div className="dq-kpi-item__sub">APMC &amp; eNAM nodes</div>
            </div>

            {/* Missing values */}
            <div className="dq-kpi-item">
              <div className="dq-kpi-item__label">
                <AlertTriangle size={11} />
                Missing Values
              </div>
              <div className="dq-kpi-item__value dq-kpi-item__value--amber">
                {quality.missingValues.toLocaleString('en-IN')}
              </div>
              <div className="dq-kpi-item__sub">Auto-imputed by ETL</div>
              <span className="dq-kpi-status-chip dq-kpi-status-chip--amber">
                <AlertTriangle size={8} /> Imputed
              </span>
            </div>

            {/* Duplicates */}
            <div className="dq-kpi-item">
              <div className="dq-kpi-item__label">
                <BarChart2 size={11} />
                Duplicates Removed
              </div>
              <div className="dq-kpi-item__value">
                {quality.duplicateRecords.toLocaleString('en-IN')}
              </div>
              <div className="dq-kpi-item__sub">De-duplicated by pipeline</div>
            </div>
          </div>

          {/* ================================================================
              PIPELINE FLOW — compact horizontal strip
              ================================================================ */}
          <div className="dq-pipeline-bar">
            {PIPELINE.map((node, i) => (
              <React.Fragment key={node.label}>
                <div className="dq-pl-node">
                  <div className={`dq-pl-dot dq-pl-dot--${node.status}`}>
                    {node.icon}
                  </div>
                  <div className="dq-pl-label">{node.label}</div>
                  <div className="dq-pl-sub">{node.sub}</div>
                </div>
                {i < PIPELINE.length - 1 && (
                  <div className="dq-pl-connector" />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* ================================================================
              INGESTION DATA SOURCES TABLE
              ================================================================ */}
          <div className="dq-sources-card">

            {/* Table header */}
            <div className="dq-sources-header">
              <div>
                <div className="dq-sources-title">
                  <GitMerge size={13} />
                  Ingestion Data Sources
                </div>
                <div className="dq-sources-sub">
                  Live status of all upstream government data feeds
                </div>
              </div>
              <div className="dq-sources-meta">
                <span className="dq-sources-count">
                  {quality.sources.filter(s => s.status === 'FRESH').length} / {quality.sources.length} live
                </span>
              </div>
            </div>

            {/* Table */}
            <table className="dq-table">
              <thead>
                <tr>
                  <th style={{ width: '26%' }}>Source</th>
                  <th>Status</th>
                  <th className="th-right">Total Records</th>
                  <th className="th-right">Missing / Dups</th>
                  <th className="th-right">Quality Score</th>
                  <th>Last Ingested</th>
                </tr>
              </thead>
              <tbody>
                {quality.sources.map((src: DataSource) => {
                  const isStale = src.status === 'STALE';
                  const { icon, iconClass } = sourceIconConfig(src.id);

                  return (
                    <tr key={src.id} className={isStale ? 'dq-row--stale' : ''}>

                      {/* Source name + URL */}
                      <td>
                        <div className="dq-src-cell">
                          <span className={`dq-src-icon ${iconClass}`}>{icon}</span>
                          <div>
                            <div className="dq-src-name">{src.name}</div>
                            <div className="dq-src-url">{src.url}</div>
                          </div>
                        </div>
                      </td>

                      {/* Status */}
                      <td>
                        <span className={`dq-status ${
                          src.status === 'FRESH' ? 'dq-status--fresh'
                          : src.status === 'STALE' ? 'dq-status--stale'
                          : 'dq-status--error'
                        }`}>
                          {src.status === 'FRESH'
                            ? <CheckCircle size={10} />
                            : <AlertTriangle size={10} />
                          }
                          {src.status}
                        </span>
                      </td>

                      {/* Records */}
                      <td className="dq-num">
                        <span className="dq-num-primary">{src.recordsTotal.toLocaleString('en-IN')}</span>
                        <span className="dq-num-sub">rows</span>
                      </td>

                      {/* Anomalies */}
                      <td className="dq-num">
                        <span className={`dq-num-primary ${src.missingValues > 5000 ? 'dq-num-primary--amber' : ''}`}>
                          {src.missingValues.toLocaleString('en-IN')}
                        </span>
                        <span className="dq-num-sub">{src.duplicates.toLocaleString('en-IN')} dups</span>
                      </td>

                      {/* Quality bar */}
                      <td>
                        <QualityCell score={src.qualityScore} />
                      </td>

                      {/* Timestamp */}
                      <td>
                        <span className={`dq-ts-primary ${isStale ? 'dq-ts-primary--amber' : ''}`}>
                          {new Date(src.lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        <span className="dq-ts-ago">{relativeTime(src.lastUpdated)}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Footer */}
            <div className="dq-table-footer">
              <span className="dq-footer-note">
                All feeds auto-refresh every 6 hours &nbsp;·&nbsp;
                IMD weather data is 1 cycle stale &nbsp;·&nbsp;
                ETL anomaly tolerance: 2%
              </span>
              <button className="dq-resync-btn">
                <RefreshCw size={11} /> Trigger Re-sync
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default DataQualityPage;
