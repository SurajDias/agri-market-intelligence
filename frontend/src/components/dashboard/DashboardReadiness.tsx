import React, { useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, Database, FlaskConical } from 'lucide-react';
import LoadingSkeleton from '../ui/LoadingSkeleton';
import { dashboardStatusService, type DashboardHealthStatus, type DashboardReadinessStatus } from '../../services/dashboardStatusService';
import './DashboardReadiness.css';

type LoadState<T> = { status: 'loading' } | { status: 'ready'; value: T } | { status: 'error' };

const ReadinessLabel: React.FC<{ value: string }> = ({ value }) => (
  <span className="dashboard-readiness__value dashboard-readiness__value--amber">
    {value.split('_').join(' ')}
  </span>
);

const DashboardReadiness: React.FC = () => {
  const [health, setHealth] = useState<LoadState<DashboardHealthStatus>>({ status: 'loading' });
  const [readiness, setReadiness] = useState<LoadState<DashboardReadinessStatus>>({ status: 'loading' });

  useEffect(() => {
    dashboardStatusService.getHealth()
      .then((value) => setHealth({ status: 'ready', value }))
      .catch(() => setHealth({ status: 'error' }));
    dashboardStatusService.getReadiness()
      .then((value) => setReadiness({ status: 'ready', value }))
      .catch(() => setReadiness({ status: 'error' }));
  }, []);

  if (health.status === 'loading' || readiness.status === 'loading') {
    return <LoadingSkeleton type="card" height={132} />;
  }

  const healthVerified = health.status === 'ready'
    && health.value.status === 'ok'
    && health.value.database === 'connected';

  return (
    <section className="dashboard-readiness" aria-label="Platform readiness">
      <div className="dashboard-readiness__header">
        <div>
          <div className="dashboard-readiness__eyebrow"><Activity size={13} /> Platform readiness</div>
          <p className="dashboard-readiness__subtitle">A truthful view of what the platform can support today.</p>
        </div>
        <span className="dashboard-readiness__badge">Presentation status</span>
      </div>

      <div className="dashboard-readiness__grid">
        <div className="dashboard-readiness__item">
          <div className="dashboard-readiness__label"><Database size={13} /> Backend / API</div>
          {health.status === 'error' ? (
            <span className="dashboard-readiness__value dashboard-readiness__value--error">Unable to verify</span>
          ) : (
            <span className={`dashboard-readiness__value ${healthVerified ? 'dashboard-readiness__value--green' : 'dashboard-readiness__value--amber'}`}>
              {healthVerified ? 'Connected' : 'Unavailable'}
            </span>
          )}
          <span className="dashboard-readiness__detail">Health check and database response</span>
        </div>

        <div className="dashboard-readiness__item">
          <div className="dashboard-readiness__label"><CheckCircle2 size={13} /> Verified observations</div>
          {readiness.status === 'error' ? (
            <span className="dashboard-readiness__value dashboard-readiness__value--error">Unable to verify</span>
          ) : (
            <span className={`dashboard-readiness__value ${readiness.value.verifiedObservations > 0 ? 'dashboard-readiness__value--green' : 'dashboard-readiness__value--amber'}`}>
              {readiness.value.verifiedObservations.toLocaleString('en-IN')}
            </span>
          )}
          <span className="dashboard-readiness__detail">Canonical historical market-price rows</span>
        </div>

        <div className="dashboard-readiness__item">
          <div className="dashboard-readiness__label"><AlertTriangle size={13} /> Data readiness</div>
          {readiness.status === 'error' ? <span className="dashboard-readiness__value dashboard-readiness__value--error">Unable to verify</span> : <ReadinessLabel value={readiness.value.readiness} />}
          <span className="dashboard-readiness__detail">
            {readiness.status === 'ready' && readiness.value.recommendationReady
              ? 'Evidence gate reports ready'
              : 'Real-data forecasts and recommendations remain unvalidated'}
          </span>
        </div>

        <div className="dashboard-readiness__item dashboard-readiness__item--simulator">
          <div className="dashboard-readiness__label"><FlaskConical size={13} /> Simulator</div>
          <span className="dashboard-readiness__value dashboard-readiness__value--blue">Hypothetical only</span>
          <span className="dashboard-readiness__detail">Uses user-supplied assumptions, not live prices</span>
        </div>
      </div>

      <div className="dashboard-readiness__next-step">
        <strong>Next step:</strong> acquire and verify official market-price history before presenting real-data forecasting or recommendations as validated.
      </div>
    </section>
  );
};

export default DashboardReadiness;
