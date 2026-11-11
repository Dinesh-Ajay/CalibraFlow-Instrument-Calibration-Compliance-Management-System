import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('calibraflow_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }
      try {
        const res = await api.get('/auth/me');
        setUser(res.data);
        localStorage.setItem('calibraflow_user', JSON.stringify(res.data));
      } catch (err) {
        localStorage.removeItem('calibraflow_token');
        localStorage.removeItem('calibraflow_user');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (username, password) => {
    const res = await api.post('/auth/login', { username, password });
    const { access_token, user: userData } = res.data;
    localStorage.setItem('calibraflow_token', access_token);
    localStorage.setItem('calibraflow_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('calibraflow_token');
    localStorage.removeItem('calibraflow_user');
    setUser(null);
  };

  const roles = user?.roles || [];
  const hasRole = (roleNames) => {
    if (!user) return false;
    if (roles.includes('Administrator') || roles.includes('admin')) return true;
    const list = Array.isArray(roleNames) ? roleNames : [roleNames];
    return list.some((r) => roles.includes(r));
  };

  const value = useMemo(() => ({ user, loading, login, logout, hasRole, roles }), [user, loading, roles]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => useContext(AuthContext);
