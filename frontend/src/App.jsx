import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ROLE_ROUTES } from './utils/constants';
import AuthLayout from './layouts/AuthLayout';
import AppLayout from './layouts/AppLayout';

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';

// Personnel pages
import PersonnelDashboard from './pages/personnel/Dashboard';
import Checkin from './pages/personnel/Checkin';
import ConsentPage from './pages/personnel/Consent';
import SupportPage from './pages/personnel/Support';
import Profile from './pages/personnel/Profile';

// Welfare Officer pages
import Cases from './pages/welfare/Cases';
import CaseDetail from './pages/welfare/CaseDetail';
import SupportRequests from './pages/welfare/SupportRequests';

// Commander pages
import CommanderOverview from './pages/commander/Overview';
import CommanderRoster from './pages/commander/Roster';

// Admin pages
import AdminPersonnel from './pages/admin/Personnel';
import AdminImport from './pages/admin/Import';
import AdminUsers from './pages/admin/Users';

import AdminAuditLogs from './pages/admin/AuditLogs';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

/**
 * Route guard — redirects to login if not authenticated
 */
function ProtectedRoute({ allowedRoles, children }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={ROLE_ROUTES[user.role] || '/login'} replace />;
  }

  return children;
}

/**
 * Redirect authenticated users to their role's dashboard
 */
function AuthRedirect({ children }) {
  const { isAuthenticated, user } = useAuth();
  if (isAuthenticated) {
    return <Navigate to={ROLE_ROUTES[user.role] || '/login'} replace />;
  }
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Landing />} />
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<AuthRedirect><Login /></AuthRedirect>} />
      </Route>

      {/* Personnel routes */}
      <Route element={<ProtectedRoute allowedRoles={['personnel']}><AppLayout /></ProtectedRoute>}>
        <Route path="/p/dashboard" element={<PersonnelDashboard />} />
        <Route path="/p/checkin" element={<Checkin />} />
        <Route path="/p/consent" element={<ConsentPage />} />
        <Route path="/p/support" element={<SupportPage />} />
        <Route path="/p/profile" element={<Profile />} />
      </Route>

      {/* Welfare Officer routes */}
      <Route element={<ProtectedRoute allowedRoles={['welfare_officer']}><AppLayout /></ProtectedRoute>}>
        <Route path="/w/cases" element={<Cases />} />
        <Route path="/w/cases/:id" element={<CaseDetail />} />
        <Route path="/w/support-requests" element={<SupportRequests />} />
      </Route>

      {/* Commander routes */}
      <Route element={<ProtectedRoute allowedRoles={['commander']}><AppLayout /></ProtectedRoute>}>
        <Route path="/c/overview" element={<CommanderOverview />} />
        <Route path="/c/roster" element={<CommanderRoster />} />
      </Route>

      {/* Admin routes */}
      <Route element={<ProtectedRoute allowedRoles={['admin']}><AppLayout /></ProtectedRoute>}>
        <Route path="/a/personnel" element={<AdminPersonnel />} />
        <Route path="/a/import" element={<AdminImport />} />
        <Route path="/a/users" element={<AdminUsers />} />

        <Route path="/a/audit" element={<AdminAuditLogs />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
