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
    <div className="min-h-screen bg-black flex items-center justify-center font-sans selection:bg-white selection:text-black p-6">
      <div className="w-full max-w-[400px] bg-black border border-neutral-800 p-8 md:p-12">
        <h1 className="text-2xl font-medium tracking-tight text-white mb-2">
          AIBAA
        </h1>
        <p className="text-neutral-500 text-xs font-mono uppercase tracking-widest mb-10">
          AI Investment Banking Analyst Agent
        </p>

        {error && (
          <div className="text-white border border-neutral-700 bg-neutral-900 px-4 py-3 text-xs font-mono mb-6">
            Error: {error}
          </div>
        )}

        <button
          className="w-full bg-white text-black py-3 text-xs font-mono uppercase tracking-widest hover:bg-neutral-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-h-[44px]"
          onClick={handleDevLogin}
          disabled={loading}
        >
          {loading ? <div className="spinner border-black border-t-transparent w-4 h-4" /> : 'Sign in (Dev Mode)'}
        </button>

        <p className="text-neutral-600 text-[10px] uppercase font-mono tracking-widest mt-6 text-center">
          Development authentication — not for production use
        </p>
      </div>
    </div>
  );
}
