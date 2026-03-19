import { useState } from 'react';
import { ensureAuthToken } from '../lib/api';

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
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: 360, padding: 32, border: '1px solid #222', borderRadius: 4, background: '#0a0a0a' }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: '0 0 4px', letterSpacing: '0.08em', color: '#ff6600' }}>
          AIBAA
        </h1>
        <p style={{ color: '#666', fontSize: 12, margin: '0 0 28px' }}>
          AI Investment Banking Analyst Agent
        </p>

        {error && (
          <div style={{
            color: '#ff4444', fontSize: 12, padding: '8px 12px', marginBottom: 16,
            background: 'rgba(255,68,68,0.08)', border: '1px solid rgba(255,68,68,0.25)', borderRadius: 3,
          }}>
            {error}
          </div>
        )}

        <button
          className="btn-primary"
          onClick={handleDevLogin}
          disabled={loading}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {loading ? 'Signing in...' : 'Sign in (Dev Mode)'}
        </button>

        <p style={{ color: '#444', fontSize: 10, marginTop: 16, textAlign: 'center' }}>
          Development authentication — not for production use
        </p>
      </div>
    </div>
  );
}
