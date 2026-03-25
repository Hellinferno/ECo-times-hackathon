import { useAuth } from '../components/auth/AuthContext';
import { ArrowLeft, User, Building2, Shield, Mail } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  const accountInfo = [
    { icon: User, label: 'User ID', value: user?.user_id ?? '—' },
    { icon: Building2, label: 'Tenant', value: user?.tenant_id ?? '—' },
    { icon: Shield, label: 'Role', value: user?.role ?? '—' },
    { icon: Mail, label: 'Email', value: user?.email ?? '—' },
  ];

  return (
    <div className="p-6 md:p-10 max-w-[900px] mx-auto animate-fade-in-up">
      {/* Back Link */}
      <Link
        to="/"
        className="inline-flex items-center gap-2 mb-8 no-underline transition-colors duration-200"
        style={{
          fontSize: 12,
          color: 'var(--text-muted)',
          fontFamily: "'JetBrains Mono', monospace",
          letterSpacing: '0.04em',
        }}
        onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)' }}
        onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)' }}
      >
        <ArrowLeft size={14} /> Back to Pipeline
      </Link>

      {/* Page Title */}
      <div className="mb-10" style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: 24 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.03em', marginBottom: 4 }}>
          Settings
        </h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          Manage your account and platform configurations
        </p>
      </div>

      {/* Account Overview Section */}
      <section className="glass-card-static mb-8" style={{ overflow: 'hidden' }}>
        <div
          className="px-6 py-4 gradient-border"
          style={{ borderBottom: '1px solid var(--border-glass)' }}
        >
          <h2 style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', margin: 0, fontFamily: "'JetBrains Mono', monospace" }}>
            Account Overview
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2">
          {accountInfo.map((item, i) => (
            <div
              key={i}
              className="px-6 py-5 flex items-start gap-4 transition-colors duration-200"
              style={{
                borderBottom: i < accountInfo.length - 2 ? '1px solid var(--border-subtle)' : 'none',
                borderRight: i % 2 === 0 ? '1px solid var(--border-subtle)' : 'none',
                animation: `fadeInUp 0.3s ease ${i * 60}ms both`,
              }}
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-hover)' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent' }}
            >
              <div
                className="flex items-center justify-center flex-shrink-0"
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--accent-glow)',
                  border: '1px solid rgba(99, 130, 255, 0.12)',
                  color: 'var(--accent-light)',
                }}
              >
                <item.icon size={14} />
              </div>
              <div>
                <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', fontFamily: "'JetBrains Mono', monospace", wordBreak: 'break-all' }}>
                  {item.value}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Security Section */}
      <section className="glass-card-static mb-8" style={{ overflow: 'hidden' }}>
        <div
          className="px-6 py-4"
          style={{ borderBottom: '1px solid var(--border-glass)' }}
        >
          <h2 style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', margin: 0, fontFamily: "'JetBrains Mono', monospace" }}>
            Session & Security
          </h2>
        </div>
        <div className="px-6 py-5 flex items-center justify-between">
          <div>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 2 }}>
              Sign out of your account
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              This will end your current session and redirect to login
            </div>
          </div>
          <button className="btn-danger" onClick={logout}>
            Sign Out
          </button>
        </div>
      </section>

      {/* Platform Info */}
      <div
        className="text-center mt-12 animate-fade-in"
        style={{ animationDelay: '300ms' }}
      >
        <p style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', fontFamily: "'JetBrains Mono', monospace" }}>
          AIBAA Platform v1.0.0-alpha &middot; Enterprise Financial AI
        </p>
      </div>
    </div>
  );
}
