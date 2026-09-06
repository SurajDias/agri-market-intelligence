import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import Topography from '../ui/Topography';
import './AppLayout.css';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="app-layout">
      {/* Shared Global Topography Background for all authenticated pages */}
      <div className="app-layout__bg-topography">
        <Topography
          lowColor="#15803D"
          midColor="#22C55E"
          highColor="#D97706"
          speed={0.12}
          morphAmount={1.8}
          morphSpeed={0.02}
          bands={2.8}
          thickness={0.009}
          scale={1.2}
          pixelSize={1.0}
          glow={0.0}
          colorMode="elevation"
          contrast={2.8}
          brightness={0.95}
          fillBands={false}
          opacity={0.32}
          grain={false}
          mouseInteraction={false}
        />
      </div>

      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          className="app-layout__overlay"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(prev => !prev)}
      />

      <div
        className="app-layout__main"
        style={{
          marginLeft: sidebarCollapsed
            ? 'var(--sidebar-collapsed-width)'
            : 'var(--sidebar-width)',
        }}
      >
        <Topbar
          onMobileMenuToggle={() => setMobileSidebarOpen(prev => !prev)}
          sidebarCollapsed={sidebarCollapsed}
        />

        <main className="app-layout__content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
