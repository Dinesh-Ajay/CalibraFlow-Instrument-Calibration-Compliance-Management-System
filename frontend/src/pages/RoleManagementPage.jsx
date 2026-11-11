import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function RoleManagementPage() {
  const [roles, setRoles] = useState([]);
  const [matrix, setMatrix] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [rRes, mRes] = await Promise.all([api.get('/users/roles'), api.get('/users/permissions/matrix')]);
        setRoles(rRes.data || []);
        setMatrix(mRes.data || null);
      } catch (e) { setError(e.response?.data?.detail || 'Failed to load roles/permissions'); }
      finally { setLoading(false); }
    })();
  }, []);

  return (
    <>
      <div className="bc">Home / Administration / Roles & Permissions</div>
      <header className="hd"><div><h1>Role & Permission Management</h1><p>View available roles, permissions, and role-permission mappings. Role assignments are managed from User Management.</p></div></header>
      {error && <div className="al" style={{marginBottom:12}}><span>{error}</span></div>}
      {loading ? <div className="pn"><p className="text-sm text-slate-500">Loading...</p></div> : (
        <>
          <div className="pn"><h2>Available roles <span>{roles.length}</span></h2>
            <table><thead><tr><th>ID</th><th>Role</th><th>Description</th></tr></thead>
              <tbody>{roles.map(r => (<tr key={r.id}><td>{r.id}</td><td>{r.role_name}</td><td>{r.description || '—'}</td></tr>))}</tbody>
            </table>
          </div>
          <div className="pn"><h2>Role-permission mappings</h2>
            {!matrix ? <p className="text-sm text-slate-500">No matrix data available.</p> : (
              <div style={{display:'grid', gap:12}}>
                {(matrix.roles || []).map(r => (
                  <div key={r.role_internal} className="border border-slate-200 rounded-xl p-3 bg-slate-50/40">
                    <div className="flex items-center justify-between mb-2"><b className="text-sm text-slate-900">{r.role}</b><span className="text-xs text-slate-500">{r.role_internal}</span></div>
                    <div className="flex flex-wrap gap-2">{(r.permissions||[]).map(p => <span key={p} className="tg b">{p}</span>)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
