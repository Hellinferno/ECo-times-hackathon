/**
 * AuthProvider — session state for the platform shell.
 *
 * Reads the persisted JWT from sessionStorage on mount, hydrates the current
 * user from GET /auth/me, and exposes login/logout helpers that the rest of
 * the app consumes via useAuth() (exported from ./auth-context).
 */
import { useEffect, useState, useCallback, type ReactNode } from "react";
import { api, getAuthToken, setAuthToken } from "../api/client";
import { AuthContext, type AuthState } from "./auth-context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: Boolean(getAuthToken()),
    error: null,
  });

  const refresh = useCallback(async () => {
    if (!getAuthToken()) {
      setState({ user: null, loading: false, error: null });
      return;
    }
    try {
      const res = await api.getCurrentUser();
      setState({ user: res.data, loading: false, error: null });
    } catch (e) {
      setAuthToken(null);
      setState({ user: null, loading: false, error: (e as Error).message });
    }
  }, []);

  useEffect(() => {
    // Initial hydration from persisted session storage — external source, so
    // the setState-in-effect warning does not apply here.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  const login = useCallback(async (username: string, password: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    const res = await api.login(username, password);
    setState({ user: res.data.user, loading: false, error: null });
    return res.data.user;
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setState({ user: null, loading: false, error: null });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
