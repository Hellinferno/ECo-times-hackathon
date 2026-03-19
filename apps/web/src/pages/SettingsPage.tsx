import { useAuth } from '../components/auth/AuthContext';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div style={{ minHeight: '100vh', padding: '24px 32px', maxWidth: 640 }}>
      <Link
        to="/"
        style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#888', fontSize: 12, textDecoration: 'none', marginBottom: 24 }}
      >
        <ArrowLeft size={14} /> Back to Dashboard
      </Link>

      <h1 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 24px', letterSpacing: '0.04em' }}>
        Settings
      </h1>

      <section style={{ border: '1px solid #222', borderRadius: 4, padding: 20, marginBottom: 20 }}>
        <h2 style={{ fontSize: 12, fontWeight: 700, color: '#888', letterSpacing: '0.08em', margin: '0 0 12px', textTransform: 'uppercase' }}>
          Account
        </h2>
        <div style={{ display: 'grid', gap: 8, fontSize: 13 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#666' }}>User ID</span>
            <span style={{ color: '#ccc', fontFamily: "'SF Mono', Consolas, monospace", fontSize: 12 }}>{user?.user_id ?? '—'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#666' }}>Tenant</span>
            <span style={{ color: '#ccc', fontFamily: "'SF Mono', Consolas, monospace", fontSize: 12 }}>{user?.tenant_id ?? '—'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#666' }}>Role</span>
            <span style={{ color: '#ccc', fontFamily: "'SF Mono', Consolas, monospace", fontSize: 12 }}>{user?.role ?? '—'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#666' }}>Email</span>
            <span style={{ color: '#ccc', fontFamily: "'SF Mono', Consolas, monospace", fontSize: 12 }}>{user?.email ?? '—'}</span>
          </div>
        </div>
      </section>

      <button
        className="btn-ghost"
        onClick={logout}
        style={{ color: '#ff4444', borderColor: 'rgba(255,68,68,0.3)' }}
      >
        Sign Out
      </button>
    </div>
  );
}
