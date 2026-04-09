import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Query from "./pages/Query";
import Results from "./pages/Results";
import Audit from "./pages/Audit";
import AuditHistory from "./pages/AuditHistory";
import Experimental from "./pages/Experimental";
import CustomQuery from "./pages/CustomQuery";
import Settings from "./pages/Settings";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Layout from "./components/Layout";
import { AuthProvider, useAuth } from "./contexts/AuthContext";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />

          {/* Protected Routes */}
          <Route path="/" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
          <Route path="/query" element={<ProtectedRoute><Layout><Query /></Layout></ProtectedRoute>} />
          <Route path="/custom-query" element={<ProtectedRoute><Layout><CustomQuery /></Layout></ProtectedRoute>} />
          <Route path="/results/:taskId" element={<ProtectedRoute><Layout><Results /></Layout></ProtectedRoute>} />
          <Route path="/audit/:taskId" element={<ProtectedRoute><Layout><Audit /></Layout></ProtectedRoute>} />
          <Route path="/audit-history" element={<ProtectedRoute><Layout><AuditHistory /></Layout></ProtectedRoute>} />
          <Route path="/disease-drug-classification" element={<ProtectedRoute><Layout><Experimental /></Layout></ProtectedRoute>} />
          <Route path="/experimental" element={<Navigate to="/disease-drug-classification" replace />} />
          <Route path="/settings" element={<ProtectedRoute><Layout><Settings /></Layout></ProtectedRoute>} />

          {/* Default Redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
