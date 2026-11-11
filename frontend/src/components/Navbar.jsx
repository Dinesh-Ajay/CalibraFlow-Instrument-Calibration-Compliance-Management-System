import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, LogOut, Bell, Search } from 'lucide-react';
import AIAssistantDrawer from './AIAssistantDrawer';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [aiDrawerOpen, setAiDrawerOpen] = useState(false);
  const [alertCount, setAlertCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    let mounted = true;
    const fetchAlertCount = async () => {
      try {
        const res = await api.get('/alerts');
        const items = Array.isArray(res.data) ? res.data : (res.data?.items || []);
        const open = items.filter(a => (a.status || a.alert_status || 'OPEN') !== 'RESOLVED' && (a.status || a.alert_status || 'OPEN') !== 'ACKNOWLEDGED').length;
        if (mounted) setAlertCount(open || items.length || 0);
      } catch {}
    };
    fetchAlertCount();
    const interval = setInterval(fetchAlertCount, 30000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const handleSearchSubmit = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      navigate(`/instruments?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map((n) => n[0]).join('').toUpperCase().substring(0, 2);
  };

  const primaryRole = user?.roles?.[0] || 'User';
  const displayName = user?.full_name || user?.username || 'User';

  return (
    <>
      <header className="top">
        <div className="relative fi flex items-center p-0 mr-auto max-w-sm w-full">
          <Search size={16} className="absolute left-3 text-slate-400 pointer-events-none" />
          <input
            className="w-full h-full pl-9 pr-3 text-sm bg-transparent border-0 outline-none placeholder:text-slate-400"
            placeholder="Search assets, work orders, certificates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchSubmit}
            aria-label="Search"
          />
        </div>

        <button
          onClick={() => setAiDrawerOpen(true)}
          className="btn sm o flex items-center gap-1.5 text-xs text-blue-700 bg-blue-50/70 hover:bg-blue-100/70 border-blue-200"
          title="Open AI Operational Assistant"
        >
          <Sparkles size={14} className="text-blue-600" />
          <span className="hidden sm:inline">AI Assistant</span>
        </button>

        <span className="bell" role="button" onClick={() => navigate('/alerts')} title="View alerts">
          <Bell size={22} className="text-slate-600 hover:text-blue-600 transition-colors" />
          {alertCount > 0 && <b>{alertCount}</b>}
        </span>

        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
          <div className="av">{getInitials(displayName)}</div>
          <div className="who">
            <b>{displayName}</b>
            <span>{primaryRole}</span>
          </div>
          <button onClick={logout} className="ml-1 p-1 text-slate-400 hover:text-red-600 rounded-md transition-colors" title="Sign out">
            <LogOut size={16} />
          </button>
        </div>
      </header>
      <AIAssistantDrawer isOpen={aiDrawerOpen} onClose={() => setAiDrawerOpen(false)} />
    </>
  );
};

export default Navbar;
