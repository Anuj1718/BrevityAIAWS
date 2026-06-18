import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Navbar from './components/layout/Navbar.jsx';
import Footer from './components/layout/Footer.jsx';

// Lazy-load page components for faster initial load
const Home = lazy(() => import('./components/Home/Home.jsx'));
const Upload = lazy(() => import('./components/Upload/Upload.jsx'));
const Login = lazy(() => import('./components/Auth/login.jsx'));
const Signup = lazy(() => import('./components/Auth/Signup.jsx'));
const Pricing = lazy(() => import('./components/Marketing/Pricing.jsx'));
const Services = lazy(() => import('./components/Marketing/Services.jsx'));
const Help = lazy(() => import('./components/Marketing/Help.jsx'));

import RequireAuth from './components/Auth/RequireAuth.jsx';

function PageLoader() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      minHeight: '60vh', color: '#a78bfa', fontSize: '1.1rem'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 40, height: 40, border: '3px solid rgba(167,139,250,0.3)',
          borderTopColor: '#a78bfa', borderRadius: '50%',
          animation: 'spin 0.8s linear infinite', margin: '0 auto 12px'
        }} />
        Loading...
      </div>
    </div>
  );
}

export default function App() {
  return (
    <>
      <Navbar />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/upload" element={
            <RequireAuth><Upload /></RequireAuth>
            } />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/services" element={<Services />} />
          <Route path="/help" element={<Help />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      <Footer />
    </>
  );
}