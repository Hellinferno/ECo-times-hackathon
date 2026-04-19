/**
 * Shared auth context + hook. Separated from AuthProvider to satisfy the
 * react-refresh/only-export-components rule (HMR works only when a file
 * exports components exclusively).
 */
import { createContext, useContext } from "react";
import type { PlatformUser } from "../api/client";

export interface AuthState {
  user: PlatformUser | null;
  loading: boolean;
  error: string | null;
}

export interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<PlatformUser>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
