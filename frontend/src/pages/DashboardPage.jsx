import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { Plus, Download, Bell, Box, Calendar, AlertTriangle, ShieldAlert, FileText, Database, Clock, ShieldCheck } from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [overdueAssets, setOverdueAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [summaryRes, assetsRes] = await Promise.all([api.get('/dashboard/summary'), api.get('/assets?limit=200')]);
        setData(summaryRes.data || {});
        const allAssets = Array.isArray(assetsRes.data) ? assetsRes.data : (assetsRes.data?.items || []);
        setOverdueAssets(allAssets.filter(a => ['OVERDUE','FAILED','RESTRICTED'].includes(a.calibration_status) || a.operational_status !== 'ACTIVE').slice(0, 8));
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading dashboard...</p></div>;
  const k = data?.kpis || {}; const r = data?.rates || {};
  const complianceRate = Number(r.compliance_rate || 0);
  const total = Number(k.total_instruments || 0);
  const due30 = Number(k.upcoming_calibration || 0);
  const overdue = Number(k.overdue_instruments || 0);
  const blocked = Number(k.blocked_production_usage || 0);

  const formatDateSafe = (d) => {
    if (!d) return '—';
    const parsed = new Date(d);
    return isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString();
  };

  const exportCsv = () => {
    const rows = [['Metric','Value'], ...Object.entries(k).map(([a,b])=>[a,b]), ...Object.entries(r).map(([a,b])=>[a,b])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(rw=>rw.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const a=document.createElement('a'); a.href=encodeURI(csv); a.download=`calibraflow_dashboard_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  return (
    <>
      <div className="bc">Home / Dashboard</div>
      <header className="hd"><div><h1>Dashboard</h1><p>Calibration compliance and operational overview (database-backed).</p></div><div className="tb"><button className="btn" onClick={()=>navigate('/work-orders')}><Plus size={18}/><span>Work orders</span></button><button className="btn o" onClick={exportCsv}><Download size={18}/><span>Export</span></button></div></header>
      <div className="al"><span><Bell size={20}/> {due30} instrument(s) due soon/upcoming and {overdue} overdue/at-risk.</span><button className="btn" onClick={()=>navigate('/alerts')}>View alerts</button></div>
      <section className="kp">
        <div className="cd"><span className="ic"><Box size={26}/></span><div><small>Instruments in service</small><b>{total.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic y"><Calendar size={26}/></span><div><small>Due soon / upcoming</small><b className="y">{due30.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic r"><AlertTriangle size={26}/></span><div><small>Overdue</small><b className="r">{overdue.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic r"><ShieldAlert size={26}/></span><div><small>Blocked production uses</small><b className="r">{blocked.toLocaleString()}</b></div></div>
      </section>
      <section className="g2">
        <div className="pn"><h2>Calibration compliance</h2><div className="dn"><div className="ring" style={{background:`conic-gradient(#16A34A 0% ${complianceRate}%, #E5EAF3 ${complianceRate}% 100%)`}}><div><b>{complianceRate}%</b><small>compliant</small></div></div><div className="text-sm space-y-1.5 text-slate-700"><div>Compliant: {Number(k.calibration_compliant||0).toLocaleString()}</div><div>Failed calibrations: {Number(k.failed_calibrations||0).toLocaleString()}</div><div>Missing certificates: {Number(k.missing_certificates||0).toLocaleString()}</div><div>Open impact assessments: {Number(k.pending_impact_assessments||0).toLocaleString()}</div></div></div></div>
        <div className="pn"><h2>Operational metrics</h2><table><tbody>
          <tr><td>Calibration success rate</td><td>{Number(r.calibration_success_rate||0)}%</td></tr>
          <tr><td>Certificate verification rate</td><td>{Number(r.certificate_verification_rate||0)}%</td></tr>
          <tr><td>Blocked usage rate</td><td>{Number(r.blocked_usage_rate||0)}%</td></tr>
          <tr><td>Open/active work orders</td><td>{Number(k.open_work_orders||0).toLocaleString()}</td></tr>
          <tr><td>Active assets</td><td>{Number(k.active_assets||0).toLocaleString()}</td></tr>
        </tbody></table></div>
      </section>
      <section className="g2">
        <div className="pn"><h2>Overdue / restricted instruments <Link to="/instruments?status=OVERDUE" className="text-xs text-blue-600 font-semibold hover:underline">View instruments</Link></h2>
          <table><thead><tr><th>Asset</th><th>Name</th><th>Due</th><th>Status</th></tr></thead><tbody>
            {overdueAssets.length ? overdueAssets.map(a => (<tr key={a.id}><td>{a.asset_code}</td><td>{a.asset_name}</td><td>{formatDateSafe(a.next_due_date)}</td><td><StatusBadge status={a.calibration_status || a.operational_status} /></td></tr>)) : <tr><td colSpan="4" className="text-center py-6 text-slate-500">No overdue or restricted instruments found.</td></tr>}
          </tbody></table>
        </div>
        <div className="pn"><h2>Quick actions</h2>
          <section className="qc" style={{gridTemplateColumns:'repeat(2,minmax(0,1fr))'}}>
            <Link to="/instruments"><span className="ic"><Database size={22}/></span><div><b>Instrument register</b><small>View and manage assets</small></div></Link>
            <Link to="/plans-events"><span className="ic y"><Calendar size={22}/></span><div><b>Plans & events</b><small>Calibration planning and recording</small></div></Link>
            <Link to="/alerts"><span className="ic r"><Bell size={22}/></span><div><b>Alerts</b><small>Review compliance alerts</small></div></Link>
            <Link to="/data-quality"><span className="ic g"><ShieldCheck size={22}/></span><div><b>Data quality</b><small>Validation and anomaly metrics</small></div></Link>
          </section>
        </div>
      </section>
    </>
  );
}
