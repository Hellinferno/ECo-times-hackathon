/**
 * App — root router component.
 *
 * All 11 pages are code-split via React.lazy so the initial bundle only
 * contains Layout, the Suspense fallback, and the router shell.
 *
 * Route tree (all inside the shared Layout shell):
 *   /                    Dashboard
 *   /scanner             Scanner
 *   /stock/:symbol       StockDetail
 *   /workspaces          Workspaces
 *   /workspaces/:id      WorkspaceDetail
 *   /valuation-lab       ValuationLab
 *   /outputs             Outputs
 *   /history             History
 *   /watchlist           Watchlist
 *   /alerts              Alerts
 *   /settings            Settings
 *   *                    → redirect to /
 */
import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { LoadingState } from "./components/ui";

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

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingState label="Launching AlphaHunter terminal..." />}>
        <Routes>
          <Route element={<Layout />}>
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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
