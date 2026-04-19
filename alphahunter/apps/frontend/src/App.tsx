/**
 * App — root router component.
 *
 * All pages are code-split via React.lazy so the initial bundle only contains
 * Layout, the Suspense fallback, auth plumbing, and the router shell.
 *
 * Route tree (all inside the shared Layout shell, except /login):
 *   /login               Login (public)
 *   /                    Dashboard                 (auth)
 *   /scanner             Scanner                   (auth)
 *   /stock/:symbol       StockDetail               (auth)
 *   /workspaces          Workspaces                (auth)
 *   /workspaces/:id      WorkspaceDetail           (auth)
 *   /valuation-lab       ValuationLab              (auth)
 *   /outputs             Outputs                   (auth)
 *   /history             History                   (auth)
 *   /watchlist           Watchlist                 (auth)
 *   /alerts              Alerts                    (auth)
 *   /settings            Settings                  (auth)
 *   /admin               Admin                     (admin only)
 *   *                    → redirect to /
 */
import { Suspense, lazy, type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import Layout from "./components/Layout";
import FeedbackWidget from "./components/FeedbackWidget";
import { LoadingState } from "./components/ui";
import { AuthProvider } from "./auth/AuthContext";
import { useAuth } from "./auth/auth-context";

const Dashboard = lazy(() => import("./Dashboard"));
const Scanner = lazy(() => import("./Scanner"));
const StockDetail = lazy(() => import("./StockDetail"));
const History = lazy(() => import("./History"));
const Watchlist = lazy(() => import("./Watchlist"));
const Alerts = lazy(() => import("./Alerts"));
const Settings = lazy(() => import("./Settings"));
const Workspaces = lazy(() => import("./Workspaces"));
const WorkspaceDetail = lazy(() => import("./WorkspaceDetail"));
const ValuationLab = lazy(() => import("./ValuationLab"));
const Outputs = lazy(() => import("./Outputs"));
const Login = lazy(() => import("./Login"));
const Admin = lazy(() => import("./Admin"));

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <LoadingState label="Verifying session..." />;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return <>{children}</>;
}

function RequireAdmin({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState label="Verifying session..." />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role.toLowerCase() !== "admin") return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AuthedShell() {
  return (
    <>
      <Layout />
      <FeedbackWidget />
    </>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<LoadingState label="Launching AlphaHunter terminal..." />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              element={
                <RequireAuth>
                  <AuthedShell />
                </RequireAuth>
              }
            >
              <Route path="/" element={<Dashboard />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/stock/:symbol" element={<StockDetail />} />
              <Route path="/workspaces" element={<Workspaces />} />
              <Route path="/workspaces/:workspaceId" element={<WorkspaceDetail />} />
              <Route path="/valuation-lab" element={<ValuationLab />} />
              <Route path="/outputs" element={<Outputs />} />
              <Route path="/history" element={<History />} />
              <Route path="/watchlist" element={<Watchlist />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/settings" element={<Settings />} />
              <Route
                path="/admin"
                element={
                  <RequireAdmin>
                    <Admin />
                  </RequireAdmin>
                }
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
