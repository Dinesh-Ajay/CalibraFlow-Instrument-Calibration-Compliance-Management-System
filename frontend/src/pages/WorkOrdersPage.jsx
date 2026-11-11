import React, { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { Plus, Download, Play, CheckSquare, X } from 'lucide-react';

export default function WorkOrdersPage() {
  const { hasRole } = useAuth();
  const canExecute = hasRole(['Administrator', 'admin', 'Maintenance Engineer', 'maint_eng']);
  const canCreate = hasRole(['Administrator', 'admin', 'Maintenance Engineer', 'maint_eng', 'Production Planner', 'planner']);
  const [workOrders, setWorkOrders] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All statuses');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [selectedWo, setSelectedWo] = useState(null);
  const [actualDowntime, setActualDowntime] = useState(60);
  const [submitting, setSubmitting] = useState(false);
  const [createForm, setCreateForm] = useState({ asset_id:'', work_order_type:'CALIBRATION', priority:'HIGH', planned_downtime_minutes:120, scheduled_start:new Date().toISOString().slice(0,16), description:'Scheduled calibration work order' });

  const fetchData = async () => {
    try {
      const [woRes, asRes] = await Promise.all([api.get('/work-orders'), api.get('/assets?limit=200')]);
      const woList = Array.isArray(woRes.data) ? woRes.data : (woRes.data?.items || []);
      const asList = Array.isArray(asRes.data) ? asRes.data : (asRes.data?.items || []);
      setWorkOrders(woList); setAssets(asList);
      if (asList.length && !createForm.asset_id) setCreateForm(p => ({...p, asset_id:String(asList[0].id)}));
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };
  useEffect(()=>{ fetchData(); }, []);

  const handleStart = async (id) => { try { await api.patch(`/work-orders/${id}/status`, { status:'IN_PROGRESS', notes:'Started by maintenance' }); fetchData(); } catch(e){ alert(e.response?.data?.detail || 'Failed to start work order'); } };
  const handleComplete = async (e) => { e.preventDefault(); if(!selectedWo) return; try { await api.patch(`/work-orders/${selectedWo.id}/status`, { status:'COMPLETED', downtime_minutes: parseInt(actualDowntime,10), notes:'Completed' }); setShowCompleteModal(false); fetchData(); } catch(err){ alert(err.response?.data?.detail || 'Failed to complete work order'); } };
  const handleCreate = async (e) => { e.preventDefault(); setSubmitting(true); try { await api.post('/work-orders', { asset_id: parseInt(createForm.asset_id,10), work_order_type:createForm.work_order_type, priority:createForm.priority, scheduled_date:new Date(createForm.scheduled_start).toISOString(), description:createForm.description }); setShowCreateModal(false); fetchData(); } catch(err){ alert(err.response?.data?.detail || 'Failed to create work order'); } finally { setSubmitting(false); } };

  const filtered = workOrders.filter(w => {
    const q = search.toLowerCase();
    const ms = !q || [w.work_order_code,w.asset_code,w.asset_name,w.description].some(v=>String(v||'').toLowerCase().includes(q));
    const s = String(w.status||'').toUpperCase();
    const mf = statusFilter==='All statuses' || (statusFilter==='Open' && ['OPEN','ASSIGNED','SCHEDULED'].includes(s)) || (statusFilter==='In progress' && s==='IN_PROGRESS') || (statusFilter==='Closed' && ['COMPLETED','CLOSED','CANCELLED'].includes(s));
    return ms && mf;
  });

  const exportCsv = () => {
    const rows = [['Work Order','Asset','Type','Status','Scheduled','Downtime (min)','Description'], ...filtered.map(w=>[w.work_order_code,w.asset_code||w.asset_id,w.work_order_type,w.status,w.scheduled_date||'',w.downtime_minutes||0,w.description||''])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const a=document.createElement('a'); a.href=encodeURI(csv); a.download=`calibraflow_work_orders_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading work orders...</p></div>;

  return (
    <>
      <div className="bc">Home / Work orders</div>
      <header className="hd"><div><h1>Work orders</h1><p>Calibration and maintenance work orders with scheduling and downtime tracking.</p></div><div className="tb">{canCreate && <button className="btn" onClick={()=>setShowCreateModal(true)} disabled={!assets.length}><Plus size={18}/><span>New work order</span></button>}<button className="btn o" onClick={exportCsv}><Download size={18}/><span>Export</span></button></div></header>
      <div className="tb"><input className="fi" placeholder="Search work order, asset..." value={search} onChange={e=>setSearch(e.target.value)} /><select className="fi" value={statusFilter} onChange={e=>setStatusFilter(e.target.value)}><option>All statuses</option><option>Open</option><option>In progress</option><option>Closed</option></select></div>
      <div className="pn" style={{ overflowX: 'auto' }}><table style={{ minWidth: 720 }}><thead><tr><th>Work order</th><th>Asset</th><th>Type</th><th>Status</th><th>Scheduled</th><th>Downtime (min)</th><th>Description</th><th>Actions</th></tr></thead><tbody>
        {filtered.length ? filtered.map(w => (
          <tr key={w.id}><td>{w.work_order_code}</td><td>{w.asset_code || w.asset_id}</td><td>{w.work_order_type}</td><td><StatusBadge status={w.status} /></td><td>{w.scheduled_date ? new Date(w.scheduled_date).toLocaleString() : '—'}</td><td>{w.downtime_minutes ?? 0}</td><td style={{whiteSpace:'normal'}}>{w.description || '—'}</td><td>
            {canExecute ? (
              <div className="flex gap-1.5">{!['IN_PROGRESS','COMPLETED','CLOSED','CANCELLED'].includes(w.status) && <button className="btn sm o" onClick={()=>handleStart(w.id)}><Play size={13}/> Start</button>}{w.status==='IN_PROGRESS' && <button className="btn sm" onClick={()=>{setSelectedWo(w); setActualDowntime(w.downtime_minutes||60); setShowCompleteModal(true);}}><CheckSquare size={13}/> Complete</button>}</div>
            ) : <span className="text-xs text-slate-400">View only</span>}
          </td></tr>
        )) : <tr><td colSpan="8" className="text-center py-8 text-slate-500">No work orders found.</td></tr>}
      </tbody></table></div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6"><div className="flex items-center justify-between pb-4 border-b"><h2 className="text-base font-bold">New Work Order</h2><button onClick={()=>setShowCreateModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={handleCreate} className="space-y-4 pt-4">
            <div><label className="block text-xs font-semibold mb-1">Asset *</label><select className="fi w-full" value={createForm.asset_id} onChange={e=>setCreateForm({...createForm,asset_id:e.target.value})} required><option value="">Select asset</option>{assets.map(a=><option key={a.id} value={a.id}>{a.asset_code} — {a.asset_name}</option>)}</select></div>
            <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Type</label><select className="fi w-full" value={createForm.work_order_type} onChange={e=>setCreateForm({...createForm,work_order_type:e.target.value})}><option value="CALIBRATION">Calibration</option><option value="CORRECTIVE_ACTION">Corrective Action</option><option value="PREVENTIVE_MAINTENANCE">Preventive Maintenance</option></select></div><div><label className="block text-xs font-semibold mb-1">Priority</label><select className="fi w-full" value={createForm.priority} onChange={e=>setCreateForm({...createForm,priority:e.target.value})}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></div></div>
            <div><label className="block text-xs font-semibold mb-1">Scheduled start *</label><input type="datetime-local" className="fi w-full" value={createForm.scheduled_start} onChange={e=>setCreateForm({...createForm,scheduled_start:e.target.value})} required /></div>
            <div><label className="block text-xs font-semibold mb-1">Description</label><textarea className="fi w-full" rows={3} value={createForm.description} onChange={e=>setCreateForm({...createForm,description:e.target.value})} /></div>
            <div className="flex justify-end gap-2 pt-3 border-t"><button type="button" className="btn o" onClick={()=>setShowCreateModal(false)}>Cancel</button><button type="submit" className="btn" disabled={submitting}>{submitting?'Creating...':'Create Order'}</button></div>
          </form></div></div>
      )}

      {showCompleteModal && selectedWo && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-6"><div className="flex items-center justify-between pb-4 border-b"><h2 className="text-base font-bold">Complete Work Order</h2><button onClick={()=>setShowCompleteModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={handleComplete} className="space-y-4 pt-4"><p className="text-sm text-slate-600">Complete <b>{selectedWo.work_order_code}</b> and record actual downtime.</p>
            <div><label className="block text-xs font-semibold mb-1">Actual downtime (minutes)</label><input type="number" min="0" className="fi w-full" value={actualDowntime} onChange={e=>setActualDowntime(e.target.value)} required /></div>
            <div className="flex justify-end gap-2 pt-3 border-t"><button type="button" className="btn o" onClick={()=>setShowCompleteModal(false)}>Cancel</button><button type="submit" className="btn">Confirm Completion</button></div>
          </form></div></div>
      )}
    </>
  );
}
