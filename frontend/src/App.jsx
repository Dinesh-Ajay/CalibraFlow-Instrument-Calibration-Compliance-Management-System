import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';

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

const RequireRole = ({ roles, children }) => {
  const { user, loading, hasRole } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !hasRole(roles)) return <div className="pn"><h2>Access denied</h2><p>You do not have permission to view this page.</p></div>;
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
            <Route index element={<DashboardPage />} />
            <Route path="workflow-board" element={<WorkflowBoardPage />} />
            <Route path="instruments" element={<InstrumentsPage />} />
            <Route path="assets" element={<Navigate to="/instruments" replace />} />
            <Route path="plans-events" element={<PlansAndEventsPage />} />
            <Route path="calibration" element={<Navigate to="/plans-events" replace />} />
            <Route path="certificates" element={<CertificatesPage />} />
            <Route path="work-orders" element={<WorkOrdersPage />} />
            <Route path="production-use" element={<ProductionUsePage />} />
            <Route path="production-usage" element={<Navigate to="/production-use" replace />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="audit" element={<AuditTrailPage />} />
            <Route path="data-quality" element={<DataQualityPage />} />
            <Route path="admin/users" element={<RequireRole roles={['Administrator','admin']}><UserManagementPage /></RequireRole>} />
            <Route path="admin/roles" element={<RequireRole roles={['Administrator','admin']}><RoleManagementPage /></RequireRole>} />
            <Route path="admin/instrument-types" element={<RequireRole roles={['Administrator','admin']}><InstrumentTypeManagementPage /></RequireRole>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
