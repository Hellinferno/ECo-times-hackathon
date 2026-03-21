import { useAuth } from '../components/auth/AuthContext';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-12 font-sans selection:bg-white selection:text-black">
      <div className="max-w-[800px] mx-auto">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-neutral-500 text-xs font-mono uppercase tracking-widest hover:text-white transition-colors mb-10 border border-transparent hover:border-neutral-800 px-3 py-2 -ml-3"
        >
          <ArrowLeft size={14} /> Back to Pipeline
        </Link>

        <h1 className="text-3xl font-medium tracking-tight text-white mb-10 border-b border-neutral-800 pb-6">
          Settings
        </h1>

        <section className="border border-neutral-800 bg-black mb-8">
          <div className="border-b border-neutral-800 px-6 py-4">
            <h2 className="text-xs font-mono uppercase tracking-widest text-neutral-500">
              Account Overview
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-neutral-800">
            <div className="bg-black p-6">
              <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-2">User ID</div>
              <div className="text-white font-mono text-sm">{user?.user_id ?? '—'}</div>
            </div>
            <div className="bg-black p-6">
              <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-2">Tenant</div>
              <div className="text-white font-mono text-sm">{user?.tenant_id ?? '—'}</div>
            </div>
            <div className="bg-black p-6">
              <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-2">Role</div>
              <div className="text-white font-mono text-sm">{user?.role ?? '—'}</div>
            </div>
            <div className="bg-black p-6">
              <div className="text-neutral-500 text-[10px] uppercase font-mono tracking-widest mb-2">Email</div>
              <div className="text-white font-mono text-sm">{user?.email ?? '—'}</div>
            </div>
          </div>
        </section>

        <button
          className="border border-neutral-800 text-neutral-400 hover:text-white hover:bg-neutral-900 px-6 py-3 text-xs font-mono uppercase tracking-widest transition-colors"
          onClick={logout}
        >
          Sign Out
        </button>
      </div>
    </div>
  );
}
