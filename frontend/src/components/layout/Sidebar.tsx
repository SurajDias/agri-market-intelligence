import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Store, TrendingUp, Map, SlidersHorizontal,
  FileText, ShieldAlert, Settings, HelpCircle, LogOut, ChevronLeft,
  ChevronRight, Leaf
} from 'lucide-react';
import './Sidebar.css';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={18} /> },
  { label: 'Market Intelligence', path: '/markets', icon: <Store size={18} /> },
  { label: 'Price Forecasts', path: '/forecasts', icon: <TrendingUp size={18} /> },
  { label: 'Market Map', path: '/market-map', icon: <Map size={18} /> },
  { label: 'Decision Simulator', path: '/simulator', icon: <SlidersHorizontal size={18} /> },
  { label: 'Reports & Insights', path: '/reports', icon: <FileText size={18} /> },
  { label: 'Data Quality', path: '/data-quality', icon: <ShieldAlert size={18} /> },
  { label: 'Settings', path: '/settings', icon: <Settings size={18} /> },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('agrimark_token');
    localStorage.removeItem('agrimark_user');
    navigate('/login');
  };

  return (
    <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Logo */}
      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">
          <Leaf size={20} />
        </div>
        {!collapsed && (
          <div className="sidebar__logo-text">
            <span className="sidebar__logo-brand">AGRIMARK</span>
            <span className="sidebar__logo-ai">AI</span>
          </div>
        )}
        <button
          className="sidebar__collapse-btn"
          onClick={onToggle}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        <div className="sidebar__nav-group">
          {!collapsed && <span className="sidebar__nav-label">MAIN MENU</span>}
          {NAV_ITEMS.slice(0, 5).map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`
              }
              title={collapsed ? item.label : undefined}
            >
              <span className="sidebar__nav-icon">{item.icon}</span>
              {!collapsed && <span className="sidebar__nav-text">{item.label}</span>}
            </NavLink>
          ))}
        </div>

        <div className="sidebar__nav-group">
          {!collapsed && <span className="sidebar__nav-label">ANALYTICS</span>}
          {NAV_ITEMS.slice(5).map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `sidebar__nav-item ${isActive ? 'sidebar__nav-item--active' : ''}`
              }
              title={collapsed ? item.label : undefined}
            >
              <span className="sidebar__nav-icon">{item.icon}</span>
              {!collapsed && <span className="sidebar__nav-text">{item.label}</span>}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Bottom */}
      <div className="sidebar__bottom">
        <button className="sidebar__nav-item sidebar__help" title="Help">
          <span className="sidebar__nav-icon"><HelpCircle size={18} /></span>
          {!collapsed && <span className="sidebar__nav-text">Help & Support</span>}
        </button>

        <div className="sidebar__user" title="User Profile">
          <div className="sidebar__user-avatar">RK</div>
          {!collapsed && (
            <div className="sidebar__user-info">
              <span className="sidebar__user-name">Ravi Kumar</span>
              <span className="sidebar__user-org">Mandya FPO</span>
            </div>
          )}
        </div>

        <button className="sidebar__nav-item sidebar__logout" onClick={handleLogout} title="Logout">
          <span className="sidebar__nav-icon"><LogOut size={18} /></span>
          {!collapsed && <span className="sidebar__nav-text">Logout</span>}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
