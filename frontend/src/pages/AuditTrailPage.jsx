import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Download, X } from 'lucide-react';

export default function AuditTrailPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [entityFilter, setEntityFilter] = useState('All entities');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    (async () => {
      try { const res = await api.get('/audit?limit=200'); setRecords(Array.isArray(res.data)?res.data:(res.data?.items||[])); }
      catch (e) { console.error(e); setRecords([]); } finally { setLoading(false); }
    })();
  }, []);

  const filtered = records.filter(r => {
    const q = search.toLowerCase();
    const ms = !q || [r.entity_type,r.entity_id,r.action,r.actor_name,r.reason].some(v=>String(v||'').toLowerCase().includes(q));
    const me = entityFilter==='All entities' || String(r.entity_type||'').toLowerCase()===entityFilter.toLowerCase();
    return ms && me;
  });

  const exportCsv = () => {
    const rows = [['Timestamp','Entity Type','Entity ID','Action','Actor','Reason'], ...filtered.map(r=>[r.timestamp||'',r.entity_type||'',r.entity_id||'',r.action||'',r.actor_name||r.actor_id||'',r.reason||''])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const a=document.createElement('a'); a.href=encodeURI(csv); a.download=`calibraflow_audit_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading audit records...</p></div>;

  return (
    <>
      <div className="bc">Home / Audit trail</div>
      <header className="hd"><div><h1>Audit trail</h1><p>Append-only history of important system actions. Records are not editable or deletable.</p></div><div className="tb"><button className="btn o" onClick={exportCsv}><Download size={18}/><span>Export</span></button></div></header>
      <div className="tb"><input className="fi" placeholder="Search entity, action, actor..." value={search} onChange={e=>setSearch(e.target.value)} /><select className="fi" value={entityFilter} onChange={e=>setEntityFilter(e.target.value)}><option>All entities</option><option>User</option><option>Asset</option><option>CalibrationEvent</option><option>Certificate</option><option>WorkOrder</option><option>ProductionUse</option><option>Alert</option><option>EmergencyExtension</option><option>ImpactAssessment</option></select></div>
      <div className="pn"><table><thead><tr><th>Time</th><th>Entity</th><th>ID</th><th>Action</th><th>By</th><th>Reason</th></tr></thead><tbody>
        {filtered.length ? filtered.map(r => (
          <tr key={r.id} className="cursor-pointer hover:bg-slate-50/80" onClick={()=>setSelected(r)}>
            <td>{r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}</td><td>{r.entity_type}</td><td>{r.entity_id}</td><td>{r.action}</td><td>{r.actor_name || r.actor_id || 'System'}</td><td style={{whiteSpace:'normal'}}>{r.reason || '—'}</td>
          </tr>
        )) : <tr><td colSpan="6" className="text-center py-8 text-slate-500">No audit records found or access is restricted.</td></tr>}
      </tbody></table></div>

      {selected && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6"><div className="flex items-center justify-between pb-4 border-b"><div><h2 className="text-base font-bold">Audit record</h2><p className="text-xs text-slate-500">{selected.entity_type} · {selected.entity_id}</p></div><button onClick={()=>setSelected(null)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <div className="space-y-3 pt-4 text-xs"><div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl"><div><b>Action</b><div>{selected.action}</div></div><div><b>Timestamp</b><div>{selected.timestamp ? new Date(selected.timestamp).toLocaleString() : '—'}</div></div><div><b>Actor</b><div>{selected.actor_name || selected.actor_id || 'System'}</div></div><div><b>Request ID</b><div>{selected.request_id || '—'}</div></div></div>
            <div className="grid grid-cols-2 gap-3"><div><b>Previous value</b><pre className="mt-1 p-3 bg-slate-100 rounded-lg overflow-auto max-h-56">{selected.previous_value ? JSON.stringify(selected.previous_value, null, 2) : '—'}</pre></div><div><b>New value</b><pre className="mt-1 p-3 bg-emerald-50 border border-emerald-100 rounded-lg overflow-auto max-h-56">{selected.new_value ? JSON.stringify(selected.new_value, null, 2) : '—'}</pre></div></div>
          </div>
          <div className="flex justify-end pt-3 border-t mt-4"><button className="btn o" onClick={()=>setSelected(null)}>Close</button></div>
        </div></div>
      )}
    </>
  );
}
