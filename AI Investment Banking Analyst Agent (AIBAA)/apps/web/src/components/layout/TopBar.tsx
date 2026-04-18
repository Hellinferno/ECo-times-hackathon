import { PanelLeftClose, Bell } from 'lucide-react';

interface Props {
  breadcrumb: string[];
  sidebarCollapsed: boolean;
  onToggleSidebar: () => void;
}

export default function TopBar({ breadcrumb, sidebarCollapsed, onToggleSidebar }: Props) {
  return (
    <header
      className="flex items-center justify-between px-6"
      style={{
        height: 'var(--topbar-height)',
        background: 'var(--bg-primary)',
        borderBottom: '1px solid var(--border-primary)',
        flexShrink: 0,
      }}
    >
      <div className="flex items-center gap-4">
        {sidebarCollapsed && (
          <button
            onClick={onToggleSidebar}
            className="cursor-pointer flex items-center justify-center"
            style={{
              background: 'transparent',
              border: '1px solid var(--border-primary)',
              color: 'var(--text-muted)',
              padding: 5,
              borderRadius: 'var(--radius-sm)',
              transition: 'color 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)' }}
          >
            <PanelLeftClose size={14} />
          </button>
        )}

        <nav className="flex items-center gap-1.5">
          {breadcrumb.map((item, idx) => (
            <span key={idx} className="flex items-center gap-1.5">
              {idx > 0 && (
                <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>/</span>
              )}
              <span
                style={{
                  fontSize: 12,
                  fontWeight: idx === breadcrumb.length - 1 ? 500 : 400,
                  color: idx === breadcrumb.length - 1 ? 'var(--text-primary)' : 'var(--text-muted)',
                }}
              >
                {item}
              </span>
            </span>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <button
          className="cursor-pointer flex items-center justify-center relative"
          title="Notifications"
          style={{
            background: 'transparent',
            border: '1px solid var(--border-primary)',
            color: 'var(--text-muted)',
            padding: 6,
            borderRadius: 'var(--radius-sm)',
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)' }}
        >
          <Bell size={14} />
        </button>
      </div>
    </header>
  );
}
