import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '@/contexts/AuthContext';

const AuthGuard: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

export default AuthGuard;
