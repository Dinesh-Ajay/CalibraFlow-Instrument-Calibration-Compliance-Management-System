import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import { isModuleAllowed } from './config/navigation';
import { ShieldAlert } from 'lucide-react';

import LoginPage from './pages/LoginPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import DashboardPage from './pages/DashboardPage';
import WorkflowBoardPage from './pages/WorkflowBoardPage';
import InstrumentsPage from './pages/InstrumentsPage';
import PlansAndEventsPage from './pages/PlansAndEventsPage';
import CertificatesPage from './pages/CertificatesPage';
import WorkOrdersPage from './pages/WorkOrdersPage';
import ProductionUsePage from './pages/ProductionUsePage';
import AlertsPage from './pages/AlertsPage';
import AuditTrailPage from './pages/AuditTrailPage';
import DataQualityPage from './pages/DataQualityPage';
import UserManagementPage from './pages/UserManagementPage';
import RoleManagementPage from './pages/RoleManagementPage';
import InstrumentTypeManagementPage from './pages/InstrumentTypeManagementPage';

const ProtectedRoute = ({ moduleId, children }) => {
  const { user, loading, roles } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  if (!isModuleAllowed(moduleId, roles)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600 mb-4 shadow-sm">
          <ShieldAlert size={32} />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">403 — Access Denied</h2>
        <p className="text-sm text-slate-600 max-w-md mb-6 leading-relaxed">
          Your role ({roles?.join(', ') || 'Current User'}) does not have permission to access this module.
        </p>
        <Link to="/" className="btn">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          <Route path="/" element={<Layout />}>
            <Route index element={<ProtectedRoute moduleId="dashboard"><DashboardPage /></ProtectedRoute>} />
            <Route path="workflow-board" element={<ProtectedRoute moduleId="workflow-board"><WorkflowBoardPage /></ProtectedRoute>} />
            <Route path="instruments" element={<ProtectedRoute moduleId="instruments"><InstrumentsPage /></ProtectedRoute>} />
            <Route path="assets" element={<Navigate to="/instruments" replace />} />
            <Route path="plans-events" element={<ProtectedRoute moduleId="plans-events"><PlansAndEventsPage /></ProtectedRoute>} />
            <Route path="calibration" element={<Navigate to="/plans-events" replace />} />
            <Route path="certificates" element={<ProtectedRoute moduleId="certificates"><CertificatesPage /></ProtectedRoute>} />
            <Route path="work-orders" element={<ProtectedRoute moduleId="work-orders"><WorkOrdersPage /></ProtectedRoute>} />
            <Route path="production-use" element={<ProtectedRoute moduleId="production-use"><ProductionUsePage /></ProtectedRoute>} />
            <Route path="production-usage" element={<Navigate to="/production-use" replace />} />
            <Route path="alerts" element={<ProtectedRoute moduleId="alerts"><AlertsPage /></ProtectedRoute>} />
            <Route path="audit" element={<ProtectedRoute moduleId="audit"><AuditTrailPage /></ProtectedRoute>} />
            <Route path="data-quality" element={<ProtectedRoute moduleId="data-quality"><DataQualityPage /></ProtectedRoute>} />
            <Route path="admin/users" element={<ProtectedRoute moduleId="user-management"><UserManagementPage /></ProtectedRoute>} />
            <Route path="admin/roles" element={<ProtectedRoute moduleId="roles-permissions"><RoleManagementPage /></ProtectedRoute>} />
            <Route path="admin/instrument-types" element={<ProtectedRoute moduleId="instrument-types"><InstrumentTypeManagementPage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
