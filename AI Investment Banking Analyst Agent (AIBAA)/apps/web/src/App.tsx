import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './components/auth/AuthContext';
import { AuthGuard } from './components/auth/AuthGuard';
import AppShell from './components/layout/AppShell';
import FeedbackWidget from './components/feedback/FeedbackWidget';
import LoginPage from './pages/LoginPage';
import SettingsPage from './pages/SettingsPage';
import Dashboard from './pages/Dashboard';
import DealWorkspace from './pages/DealWorkspace';
import AdminPage from './pages/AdminPage';
import { useEffect } from 'react';
import { api } from './lib/api';

function BootstrappedApp() {
  const { isLoading, login, isAuthenticated } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    if (isAuthenticated) {
      // NOTE: localStorage token storage is acceptable for this demo app.
      // Production deployments should switch to httpOnly session cookies instead.
      api.defaults.headers.common['Authorization'] = `Bearer ${localStorage.getItem('aibaa_token') || ''}`;
    }
  }, [isAuthenticated, isLoading]);

  const handleLogin = async (token: string) => {
    // NOTE: localStorage is acceptable for demo use; production should use httpOnly cookies.
    localStorage.setItem('aibaa_token', token);
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    await login(token);
  };

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? (
            <Navigate to="/" replace />
          ) : (
            <LoginPage onLogin={handleLogin} />
          )
        }
      />
      <Route
        path="/"
        element={
          <AuthGuard>
            <AppShell>
              <Dashboard />
            </AppShell>
          </AuthGuard>
        }
      />
      <Route
        path="/deals/:dealId"
        element={
          <AuthGuard>
            <AppShell>
              <DealWorkspace />
            </AppShell>
          </AuthGuard>
        }
      />
      <Route
        path="/settings"
        element={
          <AuthGuard>
            <AppShell>
              <SettingsPage />
            </AppShell>
          </AuthGuard>
        }
      />
      <Route
        path="/admin"
        element={
          <AuthGuard>
            <AppShell>
              <AdminPage />
            </AppShell>
          </AuthGuard>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function AuthedFeedbackWidget() {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <FeedbackWidget /> : null;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <BootstrappedApp />
        <AuthedFeedbackWidget />
      </AuthProvider>
    </BrowserRouter>
  );
}
