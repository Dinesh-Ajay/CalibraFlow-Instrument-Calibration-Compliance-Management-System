import React, { useMemo, useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Kanban, Gauge, CalendarDays, FileCheck2, Wrench, Factory,
  BellRing, History, ShieldCheck, Users, KeyRound, Boxes
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { hasRole } = useAuth();
  const [syncTime, setSyncTime] = useState('Just now');
  const isAdmin = hasRole(['Administrator', 'admin']);

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
    const items = [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/workflow-board', label: 'Workflow board', icon: Kanban },
      { to: '/instruments', label: 'Instruments', icon: Gauge },
      { to: '/plans-events', label: 'Plans and events', icon: CalendarDays },
      { to: '/certificates', label: 'Certificates', icon: FileCheck2 },
      { to: '/work-orders', label: 'Work orders', icon: Wrench },
      { to: '/production-use', label: 'Production use', icon: Factory },
      { to: '/alerts', label: 'Alerts', icon: BellRing },
      { to: '/audit', label: 'Audit trail', icon: History },
      { to: '/data-quality', label: 'Data quality', icon: ShieldCheck },
    ];
    if (isAdmin) {
      items.push(
        { to: '/admin/users', label: 'User management', icon: Users },
        { to: '/admin/roles', label: 'Roles & permissions', icon: KeyRound },
        { to: '/admin/instrument-types', label: 'Instrument types', icon: Boxes },
      );
    }
    return items;
  }, [isAdmin]);

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
