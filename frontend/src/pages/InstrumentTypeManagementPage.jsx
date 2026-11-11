import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Plus, Edit2, RefreshCw, X, ToggleLeft, ToggleRight } from 'lucide-react';

const empty = { type_code:'', type_name:'', description:'', measurement_unit:'', default_calibration_interval_days:90, default_tolerance:2.0, is_active:true };

export default function InstrumentTypeManagementPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInactive, setShowInactive] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true); setError('');
    try {
      const params = new URLSearchParams();
      if (showInactive) params.set('include_inactive', 'true');
      if (search) params.set('search', search);
      const res = await api.get(`/instrument-types?${params.toString()}`);
      setItems(res.data || []);
    } catch (e) { setError(e.response?.data?.detail || 'Failed to load instrument types'); }
    finally { setLoading(false); }
  };

  useEffect(()=>{ fetchData(); }, [showInactive]);

  const openCreate = () => { setEditing(null); setForm(empty); setModal(true); };
  const openEdit = (it) => { setEditing(it); setForm({ type_code:it.type_code, type_name:it.type_name, description:it.description||'', measurement_unit:it.measurement_unit||'', default_calibration_interval_days:it.default_calibration_interval_days||90, default_tolerance:it.default_tolerance??2.0, is_active:!!it.is_active }); setModal(true); };

  const save = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const payload = { ...form, default_calibration_interval_days: parseInt(form.default_calibration_interval_days,10), default_tolerance: parseFloat(form.default_tolerance) };
      if (editing) {
        const { type_code, ...upd } = payload;
        await api.put(`/instrument-types/${editing.id}`, upd);
      } else {
        await api.post('/instrument-types', payload);
      }
      setModal(false); await fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to save instrument type'); }
    finally { setSaving(false); }
  };

  const toggleActive = async (it) => {
    try {
      if (it.is_active) await api.post(`/instrument-types/${it.id}/deactivate`); else await api.post(`/instrument-types/${it.id}/reactivate`);
      await fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to update status'); }
  };

  return (
    <>
      <div className="bc">Home / Administration / Instrument Types</div>
      <header className="hd"><div><h1>Instrument Type Management</h1><p>Manage instrument types, defaults, and active status. Deactivation preserves referenced assets/history.</p></div>
        <div className="tb"><button className="btn" onClick={openCreate}><Plus size={18}/><span>Create type</span></button><button className="btn o" onClick={fetchData}><RefreshCw size={18}/><span>Refresh</span></button></div>
      </header>
      {error && <div className="al" style={{marginBottom:12}}><span>{error}</span></div>}
      <div className="tb">
        <input className="fi" placeholder="Search by code or name..." value={search} onChange={e=>setSearch(e.target.value)} />
        <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={showInactive} onChange={e=>setShowInactive(e.target.checked)} /> Show inactive</label>
        <button className="btn o" onClick={fetchData}>Apply</button>
      </div>
      <div className="pn" style={{overflowX:'auto'}}>
        {loading ? <p className="text-sm text-slate-500">Loading instrument types...</p> : (
          <table><thead><tr><th>ID</th><th>Code</th><th>Name</th><th>Unit</th><th>Default interval (days)</th><th>Default tolerance</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>{items.map(it => (
              <tr key={it.id}><td>{it.id}</td><td>{it.type_code}</td><td>{it.type_name}</td><td>{it.measurement_unit || '—'}</td><td>{it.default_calibration_interval_days}</td><td>{it.default_tolerance}</td><td><span className={`tg ${it.is_active?'g':''}`}>{it.is_active?'Active':'Inactive'}</span></td>
                <td><div className="tb" style={{gap:6}}><button className="btn sm o" onClick={()=>openEdit(it)} title="Edit"><Edit2 size={14}/></button><button className="btn sm o" onClick={()=>toggleActive(it)} title={it.is_active?'Deactivate':'Reactivate'}>{it.is_active?<ToggleLeft size={14}/>:<ToggleRight size={14}/>}</button></div></td>
              </tr>
            ))}{items.length===0 && <tr><td colSpan="8" className="text-center py-6 text-slate-500">No instrument types found.</td></tr>}</tbody>
          </table>
        )}
      </div>

      {modal && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6">
          <div className="flex items-center justify-between pb-3 border-b"><h2 className="text-base font-bold">{editing?'Edit instrument type':'Create instrument type'}</h2><button onClick={()=>setModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={save} className="space-y-3 pt-4">
            <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Type code *</label><input className="fi w-full" value={form.type_code} onChange={e=>setForm({...form,type_code:e.target.value.toUpperCase()})} required disabled={!!editing}/></div><div><label className="block text-xs font-semibold mb-1">Type name *</label><input className="fi w-full" value={form.type_name} onChange={e=>setForm({...form,type_name:e.target.value})} required/></div></div>
            <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Measurement unit *</label><input className="fi w-full" value={form.measurement_unit} onChange={e=>setForm({...form,measurement_unit:e.target.value})} required/></div><div><label className="block text-xs font-semibold mb-1">Default interval (days) *</label><input type="number" min="1" className="fi w-full" value={form.default_calibration_interval_days} onChange={e=>setForm({...form,default_calibration_interval_days:e.target.value})} required/></div></div>
            <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Default tolerance *</label><input type="number" min="0" step="0.01" className="fi w-full" value={form.default_tolerance} onChange={e=>setForm({...form,default_tolerance:e.target.value})} required/></div><div className="flex items-end"><label className="flex items-center gap-2 text-sm pb-2"><input type="checkbox" checked={form.is_active} onChange={e=>setForm({...form,is_active:e.target.checked})}/> Active</label></div></div>
            <div><label className="block text-xs font-semibold mb-1">Description</label><textarea className="fi w-full" rows={3} value={form.description} onChange={e=>setForm({...form,description:e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-2 border-t"><button type="button" className="btn o" onClick={()=>setModal(false)}>Cancel</button><button type="submit" className="btn" disabled={saving}>{saving?'Saving...':'Save'}</button></div>
          </form>
        </div></div>
      )}
    </>
  );
}
