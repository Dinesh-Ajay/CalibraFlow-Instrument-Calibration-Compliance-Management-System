import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#F4F6FB] text-slate-600 gap-3">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold tracking-wider text-slate-500 uppercase">
          Loading CalibraFlow...
        </p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return (
    <div className="app">
      <Sidebar />
      <div className="rt">
        <Navbar />
        <main className="mn">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
