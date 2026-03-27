import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthGuard from '@/components/layout/AuthGuard';
import AppLayout from '@/components/layout/AppLayout';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import TeamPage from '@/pages/TeamPage';
import ProjectBoardPage from '@/pages/ProjectBoardPage';
import ProjectTimelinePage from '@/pages/ProjectTimelinePage';
import ProjectSettingsPage from '@/pages/ProjectSettingsPage';
import AdminPage from '@/pages/AdminPage';
import ProfilePage from '@/pages/ProfilePage';

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<AuthGuard />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="teams/:teamId" element={<TeamPage />} />
          <Route path="projects/:id/board" element={<ProjectBoardPage />} />
          <Route path="projects/:id/timeline" element={<ProjectTimelinePage />} />
          <Route path="projects/:id/settings" element={<ProjectSettingsPage />} />
          <Route path="admin" element={<AdminPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
