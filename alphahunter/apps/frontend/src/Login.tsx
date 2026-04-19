/**
 * Login — simple credential form that hits POST /auth/login.
 *
 * On success, the JWT is persisted by api.login() and the AuthContext user
 * is populated; we then redirect to the location the user was trying to
 * reach (via location.state.from) or the dashboard.
 */
import { useState, type FormEvent } from "react";
import { useLocation, useNavigate, type Location } from "react-router-dom";
import { useAuth } from "./auth/auth-context";
import { Button } from "./components/ui";
import { cx } from "./lib/utils";

interface FromState {
  from?: Location;
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [username, setUsername] = useState("analyst");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      const redirectTo = (location.state as FromState | null)?.from?.pathname ?? "/";
      navigate(redirectTo, { replace: true });
    } catch (e) {
      setError((e as Error).message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16">
      <div className="w-full max-w-md panel-card">
        <div className="mb-6 text-center">
          <h1 className="text-xl font-semibold text-white">Sign in to AlphaHunter</h1>
          <p className="mt-1 text-sm text-slate-400">Use your platform credentials.</p>
        </div>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
              Username
            </label>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-emerald-400/60"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-slate-400">
              Password
            </label>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white outline-none focus:border-emerald-400/60"
              required
            />
          </div>
          {error ? (
            <div className={cx("rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300")}>
              {error}
            </div>
          ) : null}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}
