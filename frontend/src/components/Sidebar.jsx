import React, { useMemo, useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getPermittedNavItems } from '../config/navigation';

const Sidebar = () => {
  const { roles } = useAuth();
  const [syncTime, setSyncTime] = useState('Just now');

  useEffect(() => {
    const updateSync = () => {
      const now = new Date();
      setSyncTime(`${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')} UTC`);
    };
    updateSync();
    const interval = setInterval(updateSync, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = useMemo(() => {
    return getPermittedNavItems(roles);
  }, [roles]);

  return (
    <aside className="sb">
      <div className="lg">
        <svg width="34" height="34" viewBox="0 0 32 32" role="img" aria-label="CalibraFlow logo" className="shrink-0">
          <rect width="32" height="32" rx="9" fill="#2563EB" />
          <path d="M7.5 21a8.5 8.5 0 0117 0" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" />
          <path d="M16 21l4.2-6.2" stroke="#BFD6FF" strokeWidth="2.6" strokeLinecap="round" />
          <circle cx="16" cy="21" r="2.2" fill="#fff" />
        </svg>
        <span>
          Calibra<em>Flow</em>
          <small>Calibration control</small>
        </span>
      </div>

      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink key={item.to} to={item.to} end={item.to === '/'} className={({ isActive }) => (isActive ? 'on' : '')}>
            <Icon size={18} strokeWidth={2} />
            <span>{item.label}</span>
          </NavLink>
        );
      })}

      <div className="live">
        <b>Live · Rules engine running</b>
        <small>Last sync: {syncTime}</small>
      </div>
    </aside>
  );
};

export default Sidebar;
