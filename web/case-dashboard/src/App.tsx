import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { LoginPage } from './pages/auth/LoginPage';
import { CasesPage } from './pages/cases/CasesPage';
import { CaseDetailPage } from './pages/cases/CaseDetailPage';
import { EvidencePage } from './pages/evidence/EvidencePage';
import { StoryboardPage } from './pages/storyboard/StoryboardPage';
import { RendersPage } from './pages/renders/RendersPage';
import { ProfilePage } from './pages/profile/ProfilePage';

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<Navigate to="/cases" replace />} />
        <Route path="cases" element={<CasesPage />} />
        <Route path="cases/:caseId" element={<CaseDetailPage />} />
        <Route path="evidence" element={<EvidencePage />} />
        <Route path="storyboards/:id" element={<StoryboardPage />} />
        <Route path="renders" element={<RendersPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/cases" replace />} />
    </Routes>
  );
}

export default App;
