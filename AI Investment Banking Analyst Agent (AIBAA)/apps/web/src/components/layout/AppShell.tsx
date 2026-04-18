import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

interface Props {
  children: React.ReactNode;
}

export default function AppShell({ children }: Props) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  // Derive breadcrumb from path
  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return ['Dashboard'];
    if (path === '/settings') return ['Settings'];
    if (path.startsWith('/deals/')) return ['Dashboard', 'Deal Workspace'];
    return ['Dashboard'];
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-void)' }}>
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(prev => !prev)}
      />

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Bar */}
        <TopBar
          breadcrumb={getBreadcrumb()}
          sidebarCollapsed={sidebarCollapsed}
          onToggleSidebar={() => setSidebarCollapsed(prev => !prev)}
        />

        {/* Content */}
        <main
          className="flex-1 overflow-y-auto"
          style={{
            background: 'var(--bg-void)',
            scrollBehavior: 'smooth',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
