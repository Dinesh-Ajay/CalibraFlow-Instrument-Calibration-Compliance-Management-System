import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Download, Check, CheckCircle2 } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [showOnlyOpen, setShowOnlyOpen] = useState(false);

  const fetchAlerts = async () => {
    try { const res = await api.get('/alerts?limit=200'); setAlerts(Array.isArray(res.data)?res.data:(res.data?.items||[])); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  };
  useEffect(()=>{ fetchAlerts(); }, []);

  const acknowledge = async (id) => { try { await api.patch(`/alerts/${id}/acknowledge`, {}); fetchAlerts(); } catch(e){ alert(e.response?.data?.detail || 'Failed to acknowledge alert'); } };

  const filtered = alerts.filter(a => {
    if (showOnlyOpen && ['ACKNOWLEDGED','RESOLVED'].includes(String(a.status||'').toUpperCase())) return false;
    if (filterSeverity !== 'ALL' && String(a.severity||'').toUpperCase() !== filterSeverity) return false;
    return true;
  });

  const sevBadge = (s) => {
    const v = String(s||'').toUpperCase();
    if (v==='CRITICAL') return <span className="tg mr-2">Critical</span>;
    if (v==='HIGH') return <span className="tg y mr-2">High</span>;
    if (v==='MEDIUM') return <span className="tg y mr-2">Medium</span>;
    return <span className="tg b mr-2">Low</span>;
  };

  const exportCsv = () => {
    const rows = [['Code','Severity','Type','Status','Message','Asset','Generated'], ...filtered.map(a=>[a.alert_code,a.severity,a.alert_type,a.status,a.message,a.asset_code||a.asset_id,a.generated_at||''])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const el=document.createElement('a'); el.href=encodeURI(csv); el.download=`calibraflow_alerts_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(el); el.click(); document.body.removeChild(el);
  };

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading alerts...</p></div>;

  return (
    <>
      <div className="bc">Home / Alerts</div>
      <header className="hd"><div><h1>Alerts</h1><p>Compliance and operational alerts generated from backend rules and events.</p></div><div className="tb"><button className="btn o" onClick={exportCsv}><Download size={18}/><span>Export</span></button></div></header>
      <div className="tb"><select className="fi" value={filterSeverity} onChange={e=>setFilterSeverity(e.target.value)}><option value="ALL">All severities</option><option value="CRITICAL">Critical</option><option value="HIGH">High</option><option value="MEDIUM">Medium</option><option value="LOW">Low</option></select><label className="flex items-center gap-2 text-xs font-medium text-slate-700"><input type="checkbox" checked={showOnlyOpen} onChange={e=>setShowOnlyOpen(e.target.checked)} /> Show open only</label></div>
      <div className="pn"><ul className="ls">
        {filtered.length ? filtered.map(a => (
          <li key={a.id}><div><div className="flex items-center flex-wrap">{sevBadge(a.severity)}<span className="font-semibold text-slate-900">{a.alert_type || 'Alert'}</span></div><small>{a.message || a.alert_code} {a.asset_code ? `· ${a.asset_code}` : ''} {a.generated_at ? `· ${new Date(a.generated_at).toLocaleString()}` : ''}</small></div>
            <div>{['ACKNOWLEDGED','RESOLVED'].includes(String(a.status||'').toUpperCase()) ? <span className="text-xs text-slate-500 font-semibold flex items-center gap-1"><CheckCircle2 size={14} className="text-emerald-500"/> {a.status}</span> : <button className="btn o sm" onClick={()=>acknowledge(a.id)}><Check size={14}/> Acknowledge</button>}</div>
          </li>
        )) : <li className="text-center py-8 text-slate-500">No alerts found.</li>}
      </ul></div>
    </>
  );
}
