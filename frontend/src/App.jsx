import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Layout from './pages/Layout.jsx';
import Login from './pages/Login.jsx';
import SearchLab from './pages/SearchLab.jsx';
import Students from './pages/Students.jsx';
import './styles.css';

function Guard({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Guard><Dashboard /></Guard>} />
          <Route path="/students" element={<Guard><Students /></Guard>} />
          <Route path="/search" element={<Guard><SearchLab /></Guard>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
