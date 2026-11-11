import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { Plus, RefreshCw, Search, UserX, UserCheck, KeyRound, Edit2, X } from 'lucide-react';

const emptyForm = { username:'', email:'', full_name:'', password:'', role_ids:[], is_active:true };

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [activity, setActivity] = useState([]);
  const [selected, setSelected] = useState(null);
  const [resetPwUser, setResetPwUser] = useState(null);
  const [newPw, setNewPw] = useState('');

  const fetchAll = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (roleFilter) params.set('role', roleFilter);
      if (statusFilter) params.set('is_active', statusFilter === 'active' ? 'true' : 'false');
      const [uRes, rRes] = await Promise.all([api.get(`/users?${params.toString()}`), api.get('/users/roles')]);
      setUsers(Array.isArray(uRes.data) ? uRes.data : []);
      setRoles(Array.isArray(rRes.data) ? rRes.data : []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); }, []);

  const openCreate = () => { setEditing(null); setForm(emptyForm); setShowModal(true); };
  const openEdit = (u) => { setEditing(u); setForm({ username:u.username,email:u.email,full_name:u.full_name,password:'',role_ids:u.role_ids||[],is_active:u.is_active }); setShowModal(true); };

  const saveUser = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const payload = { email: form.email, full_name: form.full_name, is_active: form.is_active, role_ids: form.role_ids.map(Number) };
        await api.put(`/users/${editing.id}`, payload);
      } else {
        const payload = { ...form, role_ids: form.role_ids.map(Number) };
        await api.post('/users', payload);
      }
      setShowModal(false); await fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to save user'); }
    finally { setSaving(false); }
  };

  const toggleActive = async (u) => {
    try {
      if (u.is_active) await api.post(`/users/${u.id}/deactivate`); else await api.post(`/users/${u.id}/reactivate`);
      await fetchAll();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to update status'); }
  };

  const viewActivity = async (u) => {
    setSelected(u);
    try { const res = await api.get(`/users/${u.id}/activity?limit=50`); setActivity(res.data || []); } catch { setActivity([]); }
  };

  const submitReset = async (e) => {
    e.preventDefault();
    if (!resetPwUser) return;
    try { await api.post(`/users/${resetPwUser.id}/reset-password`, { new_password: newPw }); setResetPwUser(null); setNewPw(''); alert('Password reset successfully'); }
    catch (err) { alert(err.response?.data?.detail || 'Failed to reset password'); }
  };

  const roleOptions = useMemo(() => roles, [roles]);

  return (
    <>
      <div className="bc">Home / Administration / Users</div>
      <header className="hd"><div><h1>User Management</h1><p>Create, edit, deactivate/reactivate users, assign roles, and reset passwords</p></div>
        <div className="tb"><button className="btn" onClick={openCreate}><Plus size={18}/><span>Create user</span></button><button className="btn o" onClick={fetchAll}><RefreshCw size={18}/><span>Refresh</span></button></div>
      </header>
      <div className="tb">
        <input className="fi" placeholder="Search users..." value={search} onChange={e=>setSearch(e.target.value)} />
        <select className="fi" value={roleFilter} onChange={e=>setRoleFilter(e.target.value)}><option value="">All roles</option>{roleOptions.map(r=> <option key={r.id} value={r.role_name}>{r.role_name}</option>)}</select>
        <select className="fi" value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select>
        <button className="btn o" onClick={fetchAll}><Search size={16}/><span>Apply</span></button>
      </div>
      <div className="pn" style={{overflowX:'auto'}}>
        {loading ? <p className="text-sm text-slate-500">Loading users...</p> : (
          <table><thead><tr><th>Username</th><th>Full name</th><th>Email</th><th>Roles</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>{users.map(u => (
              <tr key={u.id}>
                <td>{u.username}</td><td>{u.full_name}</td><td>{u.email}</td>
                <td>{(u.roles||[]).join(', ') || '—'}</td>
                <td><span className={`tg ${u.is_active?'g':''}`}>{u.is_active?'Active':'Inactive'}</span></td>
                <td>
                  <div className="tb" style={{gap:6}}>
                    <button className="btn sm o" onClick={()=>openEdit(u)} title="Edit"><Edit2 size={14}/></button>
                    <button className="btn sm o" onClick={()=>toggleActive(u)} title={u.is_active?'Deactivate':'Reactivate'}>{u.is_active?<UserX size={14}/>:<UserCheck size={14}/>}</button>
                    <button className="btn sm o" onClick={()=>{setResetPwUser(u); setNewPw('');}} title="Reset password"><KeyRound size={14}/></button>
                    <button className="btn sm o" onClick={()=>viewActivity(u)} title="View activity">Activity</button>
                  </div>
                </td>
              </tr>
            ))}{users.length===0 && <tr><td colSpan="6" className="text-center py-6 text-slate-500">No users found.</td></tr>}</tbody>
          </table>
        )}
      </div>

      {selected && (
        <div className="pn"><h2>User activity <span>{selected.username}</span></h2>
          {activity.length===0 ? <p className="text-sm text-slate-500">No recent activity found.</p> : (
            <table><thead><tr><th>Time</th><th>Action</th><th>Entity</th><th>Reason</th></tr></thead>
              <tbody>{activity.map((a,i)=>(<tr key={i}><td>{a.timestamp ? new Date(a.timestamp).toLocaleString() : '—'}</td><td>{a.action}</td><td>{a.entity_type}{a.entity_id?` #${a.entity_id}`:''}</td><td>{a.reason||'—'}</td></tr>))}</tbody>
            </table>
          )}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-xl w-full p-6">
          <div className="flex items-center justify-between pb-3 border-b"><h2 className="text-base font-bold">{editing?'Edit user':'Create user'}</h2><button onClick={()=>setShowModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={saveUser} className="space-y-3 pt-4">
            {!editing && <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Username *</label><input className="fi w-full" value={form.username} onChange={e=>setForm({...form,username:e.target.value})} required/></div><div><label className="block text-xs font-semibold mb-1">Password *</label><input type="password" className="fi w-full" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} required minLength={8}/></div></div>}
            <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Full name *</label><input className="fi w-full" value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} required/></div><div><label className="block text-xs font-semibold mb-1">Email *</label><input type="email" className="fi w-full" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} required/></div></div>
            <div><label className="block text-xs font-semibold mb-1">Roles</label><div className="flex flex-wrap gap-2">{roleOptions.map(r => { const checked = form.role_ids.includes(r.id); return <label key={r.id} className={`px-2 py-1 rounded border text-xs cursor-pointer ${checked?'bg-blue-50 border-blue-300 text-blue-700':'border-slate-200'}`}><input type="checkbox" className="mr-1" checked={checked} onChange={(e)=>{ const ids = new Set(form.role_ids.map(Number)); if(e.target.checked) ids.add(r.id); else ids.delete(r.id); setForm({...form,role_ids:[...ids]}); }} />{r.role_name}</label>; })}</div></div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_active} onChange={e=>setForm({...form,is_active:e.target.checked})}/> Active account</label>
            <div className="flex justify-end gap-2 pt-2 border-t"><button type="button" className="btn o" onClick={()=>setShowModal(false)}>Cancel</button><button type="submit" className="btn" disabled={saving}>{saving?'Saving...':'Save'}</button></div>
          </form>
        </div></div>
      )}

      {resetPwUser && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-6">
          <div className="flex items-center justify-between pb-3 border-b"><h2 className="text-base font-bold">Reset password</h2><button onClick={()=>setResetPwUser(null)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={submitReset} className="space-y-3 pt-4"><p className="text-sm text-slate-600">Reset password for <b>{resetPwUser.username}</b></p>
            <div><label className="block text-xs font-semibold mb-1">New password (min 8 chars)</label><input type="password" className="fi w-full" value={newPw} onChange={e=>setNewPw(e.target.value)} minLength={8} required/></div>
            <div className="flex justify-end gap-2 pt-2 border-t"><button type="button" className="btn o" onClick={()=>setResetPwUser(null)}>Cancel</button><button type="submit" className="btn">Reset password</button></div>
          </form>
        </div></div>
      )}
    </>
  );
}
