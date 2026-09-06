import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Search, Bell, ChevronRight, Home, Menu } from 'lucide-react';
import './Topbar.css';

const BREADCRUMB_MAP: Record<string, string> = {
  '/dashboard': 'Executive Dashboard',
  '/markets': 'Market Intelligence',
  '/forecasts': 'Price Forecasts',
  '/market-map': 'Market Map',
  '/simulator': 'Decision Simulator',
  '/reports': 'Reports & Insights',
  '/data-quality': 'Data Quality',
  '/settings': 'Settings',
  '/recommendation': 'Recommendation Details',
};

interface TopbarProps {
  onMobileMenuToggle: () => void;
  sidebarCollapsed: boolean;
}

const Topbar: React.FC<TopbarProps> = ({ onMobileMenuToggle, sidebarCollapsed }) => {
  const location = useLocation();
  const pageName = BREADCRUMB_MAP[location.pathname] ?? 'Page';
  const pathSegments = location.pathname.split('/').filter(Boolean);

  return (
    <header
      className="topbar"
      style={{ left: sidebarCollapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)' }}
    >
      <div className="topbar__left">
        {/* Mobile menu toggle */}
        <button className="topbar__mobile-menu" onClick={onMobileMenuToggle}>
          <Menu size={20} />
        </button>

        {/* Breadcrumb */}
        <nav className="topbar__breadcrumb" aria-label="Breadcrumb">
          <Link to="/dashboard" className="topbar__breadcrumb-item topbar__breadcrumb-home">
            <Home size={13} />
          </Link>
          {pathSegments.map((seg, i) => {
            const path = '/' + pathSegments.slice(0, i + 1).join('/');
            const label = BREADCRUMB_MAP[path] ?? seg;
            const isLast = i === pathSegments.length - 1;
            return (
              <React.Fragment key={path}>
                <ChevronRight size={12} className="topbar__breadcrumb-sep" />
                {isLast ? (
                  <span className="topbar__breadcrumb-item topbar__breadcrumb-current">{label}</span>
                ) : (
                  <Link to={path} className="topbar__breadcrumb-item">{label}</Link>
                )}
              </React.Fragment>
            );
          })}
        </nav>
      </div>

      <div className="topbar__right">
        {/* Search */}
        <div className="topbar__search">
          <Search size={15} className="topbar__search-icon" />
          <input
            type="text"
            className="topbar__search-input"
            placeholder="Search markets, commodities…"
            aria-label="Search"
          />
        </div>

        {/* Notifications */}
        <button className="topbar__icon-btn" aria-label="Notifications" id="topbar-notifications">
          <Bell size={18} />
          <span className="topbar__badge">3</span>
        </button>

        {/* Org selector */}
        <div className="topbar__org">
          <span className="topbar__org-dot" />
          <span className="topbar__org-name">Mandya FPO</span>
        </div>

        {/* Avatar */}
        <div className="topbar__avatar" title="Ravi Kumar">RK</div>
      </div>
    </header>
  );
};

export default Topbar;
