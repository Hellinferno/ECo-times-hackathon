import { useState } from 'react';
import { ensureAuthToken } from '../lib/api';
import { TrendingUp, ArrowRight, ShieldCheck } from 'lucide-react';

interface Props {
  onLogin: (token: string) => Promise<void>;
}

export default function LoginPage({ onLogin }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDevLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await ensureAuthToken();
      if (!token) {
        setError('Could not obtain dev token. Check API connection.');
        return;
      }
      await onLogin(token);
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message || 'Login failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#000000' }}>
      <div className="w-full animate-fade-in" style={{ maxWidth: 380, padding: '0 24px' }}>
        {/* Brand */}
        <div className="flex items-center gap-3 mb-12">
          <div
            className="flex items-center justify-center"
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-sm)',
              background: '#ffffff',
              color: '#000000',
            }}
          >
            <TrendingUp size={16} strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#ffffff', letterSpacing: '-0.03em' }}>
              AIBAA
            </div>
            <div style={{ fontSize: 9, color: '#555', letterSpacing: '0.08em', textTransform: 'uppercase', fontFamily: "'JetBrains Mono', monospace" }}>
              Investment Banking Analyst
            </div>
          </div>
        </div>

        {/* Login Card */}
        <div
          style={{
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-md)',
            padding: '32px 28px',
          }}
        >
          <h2
            style={{
              fontSize: 20,
              fontWeight: 600,
              color: '#ffffff',
              marginBottom: 4,
              letterSpacing: '-0.02em',
            }}
          >
            Sign in
          </h2>
          <p
            style={{
              fontSize: 13,
              color: 'var(--text-muted)',
              marginBottom: 28,
            }}
          >
            Access your deal pipeline
          </p>

          {error && (
            <div
              className="flex items-center gap-2.5"
              style={{
                background: 'var(--negative-bg)',
                border: '1px solid var(--negative-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px 12px',
                marginBottom: 20,
                fontSize: 12,
                color: 'var(--negative)',
              }}
            >
              <ShieldCheck size={13} />
              {error}
            </div>
          )}

          <button
            className="btn-primary w-full flex items-center justify-center gap-2 group"
            style={{
              padding: '12px 24px',
              fontSize: 13,
              fontWeight: 600,
              minHeight: 44,
            }}
            onClick={handleDevLogin}
            disabled={loading}
          >
            {loading ? (
              <div className="spinner" style={{ width: 16, height: 16, borderTopColor: '#000' }} />
            ) : (
              <>
                Sign In
                <ArrowRight size={14} className="transition-transform duration-200 group-hover:translate-x-0.5" />
              </>
            )}
          </button>

          <p
            style={{
              fontSize: 10,
              color: 'var(--text-muted)',
              textAlign: 'center',
              marginTop: 16,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            Development Mode
          </p>
        </div>

        <p
          style={{
            fontSize: 11,
            color: '#333',
            textAlign: 'center',
            marginTop: 24,
          }}
        >
          &copy; 2026 AIBAA Platform
        </p>
      </div>
    </div>
  );
}
