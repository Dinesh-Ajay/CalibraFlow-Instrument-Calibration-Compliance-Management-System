import React, { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { Plus, Download, CheckCircle2, XCircle, X, CalendarCheck } from 'lucide-react';

export default function PlansAndEventsPage() {
  const { user, hasRole } = useAuth();
  const canManagePlansAndEvents = hasRole(['Administrator', 'admin', 'Maintenance Engineer', 'maint_eng']);
  const [plans, setPlans] = useState([]);
  const [events, setEvents] = useState([]);
  const [assets, setAssets] = useState([]);
  const [instrumentTypes, setInstrumentTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [showRecordModal, setShowRecordModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [planForm, setPlanForm] = useState({ instrument_type_id:'', interval_months:6, tolerance_percentage:2.0, calculation_method:'CALENDAR_DAYS', certificate_required:true, emergency_extension_allowed:true, grace_period_days:0 });
  const [recordForm, setRecordForm] = useState({ asset_id:'', measured_value:100.0, reference_value:100.0, tolerance:2.0, technician_name:'', notes:'' });

  const measured = parseFloat(recordForm.measured_value) || 0;
  const reference = parseFloat(recordForm.reference_value) || 0;
  const tolerance = parseFloat(recordForm.tolerance) || 0;
  const errorVal = Math.abs(measured - reference);
  const isPass = errorVal <= tolerance;

  const fetchData = async () => {
    const [plansRes, eventsRes, assetsRes, typesRes] = await Promise.all([
      api.get('/calibration-plans'),
      api.get('/calibration/events?limit=50'),
      api.get('/assets?limit=500'),
      api.get('/instrument-types?include_inactive=false'),
    ]);
    const p = Array.isArray(plansRes.data) ? plansRes.data : (plansRes.data?.items || []);
    const e = Array.isArray(eventsRes.data) ? eventsRes.data : (eventsRes.data?.items || []);
    const a = Array.isArray(assetsRes.data) ? assetsRes.data : (assetsRes.data?.items || []);
    const t = Array.isArray(typesRes.data) ? typesRes.data : [];
    setPlans(p); setEvents(e); setAssets(a); setInstrumentTypes(t);
    if (!recordForm.asset_id && a.length) setRecordForm(prev => ({ ...prev, asset_id:String(a[0].id) }));
    if (!recordForm.technician_name) setRecordForm(prev => ({ ...prev, technician_name: user?.full_name || user?.username || '' }));
    if (!planForm.instrument_type_id && t.length) setPlanForm(prev => ({ ...prev, instrument_type_id:String(t[0].id) }));
  };

  useEffect(() => { (async()=>{ try { await fetchData(); } finally { setLoading(false); } })(); }, []);

  const handleCreatePlan = async (e) => {
    e.preventDefault();
    if (!planForm.instrument_type_id) return alert('Please select an instrument type.');
    setSubmitting(true);
    try {
      await api.post('/calibration-plans', {
        instrument_type_id: parseInt(planForm.instrument_type_id, 10),
        interval_months: parseInt(planForm.interval_months, 10),
        tolerance_percentage: parseFloat(planForm.tolerance_percentage),
        calculation_method: planForm.calculation_method,
        certificate_required: !!planForm.certificate_required,
        emergency_extension_allowed: !!planForm.emergency_extension_allowed,
        grace_period_days: parseInt(planForm.grace_period_days || 0, 10),
        status: 'ACTIVE',
      });
      setShowPlanModal(false);
      await fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to create plan'); }
    finally { setSubmitting(false); }
  };

  const handleRecordEvent = async (e) => {
    e.preventDefault();
    if (!recordForm.asset_id) return alert('Please select an asset.');
    setSubmitting(true);
    try {
      await api.post('/calibration/events', {
        asset_id: parseInt(recordForm.asset_id, 10),
        measured_value: measured,
        reference_value: reference,
        tolerance: tolerance,
        performed_by: recordForm.technician_name || user?.full_name || user?.username || 'Unknown',
        notes: recordForm.notes,
        calibration_date: new Date().toISOString(),
      });
      setShowRecordModal(false);
      await fetchData();
    } catch (err) { alert(err.response?.data?.detail || 'Failed to record calibration event'); }
    finally { setSubmitting(false); }
  };

  const handleExport = () => {
    const rows = [['Event','Date','Asset','Measured','Reference','Error','Tolerance','Result'], ...events.map(ev => [ev.calibration_code, ev.calibration_date||'', ev.asset_code||ev.asset_id, ev.measured_value, ev.reference_value, ev.measurement_error, ev.tolerance, ev.result])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const link = document.createElement('a'); link.href = encodeURI(csv); link.download = `calibraflow_plans_events_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(link); link.click(); document.body.removeChild(link);
  };

  const formatDateSafe = (d) => {
    if (!d) return '—';
    const parsed = new Date(d);
    return isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString();
  };

  if (loading) return <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3"><div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div><p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Loading plans and events...</p></div>;

  return (
    <>
      <div className="bc">Home / Plans and events</div>
      <header className="hd"><div><h1>Plans and events</h1><p>Calibration plans define intervals/tolerances; events record measured outcomes.</p></div>
        <div className="tb">
          {canManagePlansAndEvents && (
            <>
              <button className="btn" onClick={()=>setShowRecordModal(true)} disabled={assets.length===0}><CalendarCheck size={18}/><span>Record event</span></button>
              <button className="btn o" onClick={()=>setShowPlanModal(true)} disabled={instrumentTypes.length===0}><Plus size={18}/><span>New plan</span></button>
            </>
          )}
          <button className="btn o" onClick={handleExport}><Download size={18}/><span>Export</span></button>
        </div>
      </header>
      <section className="g2">
        <div className="pn"><h2>Calibration plans <span>{plans.length} configured</span></h2>
          <table><thead><tr><th>Plan</th><th>Instrument type</th><th>Interval</th><th>Tolerance</th><th>Status</th></tr></thead>
            <tbody>{plans.length ? plans.map(p => (<tr key={p.id}><td>{p.plan_code || p.plan_name || `PLAN-${p.id}`}</td><td>{p.instrument_type_name || p.instrument_type?.type_name || p.instrument_type_id}</td><td>{p.interval_months || (p.calibration_interval_days ? Math.max(1, Math.round(p.calibration_interval_days / 30)) : 6)} months</td><td>{p.tolerance != null ? `${p.tolerance}%` : (p.tolerance_percentage != null ? `${p.tolerance_percentage}%` : '2%')}</td><td><span className={`tg ${p.status==='ACTIVE'?'g':''}`}>{p.status || 'ACTIVE'}</span></td></tr>)) : <tr><td colSpan="5" className="text-center py-6 text-slate-500">No calibration plans configured.</td></tr>}</tbody>
          </table>
        </div>
        <div className="pn"><h2>Recent calibration events <span>{events.length}</span></h2>
          <table><thead><tr><th>Event</th><th>Date</th><th>Asset</th><th>Error</th><th>Result</th></tr></thead>
            <tbody>{events.length ? events.slice(0,20).map(ev => (<tr key={ev.id}><td>{ev.calibration_code}</td><td>{formatDateSafe(ev.calibration_date)}</td><td>{ev.asset_code || ev.asset_id}</td><td>{ev.measurement_error != null ? `${ev.measurement_error}%` : '—'}</td><td><StatusBadge status={ev.result || ev.calibration_status || 'PENDING'} /></td></tr>)) : <tr><td colSpan="5" className="text-center py-6 text-slate-500">No calibration events recorded.</td></tr>}</tbody>
          </table>
        </div>
      </section>

      {showPlanModal && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6">
          <div className="flex items-center justify-between pb-4 border-b"><h2 className="text-base font-bold">Define Calibration Plan</h2><button onClick={()=>setShowPlanModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={handleCreatePlan} className="space-y-4 pt-4">
            <div><label className="block text-xs font-semibold mb-1">Instrument Type *</label>
              <select className="fi w-full" value={planForm.instrument_type_id} onChange={e=>setPlanForm({...planForm, instrument_type_id:e.target.value})} required>
                <option value="">Select instrument type</option>
                {instrumentTypes.map(t => <option key={t.id} value={t.id}>{t.type_name}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-xs font-semibold mb-1">Interval (Months) *</label><input type="number" min="1" className="fi w-full" value={planForm.interval_months} onChange={e=>setPlanForm({...planForm, interval_months:e.target.value})} required /></div>
              <div><label className="block text-xs font-semibold mb-1">Tolerance *</label><input type="number" min="0" step="0.01" className="fi w-full" value={planForm.tolerance_percentage} onChange={e=>setPlanForm({...planForm, tolerance_percentage:e.target.value})} required /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-xs font-semibold mb-1">Grace period (days)</label><input type="number" min="0" className="fi w-full" value={planForm.grace_period_days} onChange={e=>setPlanForm({...planForm, grace_period_days:e.target.value})} /></div>
              <div><label className="block text-xs font-semibold mb-1">Calculation method</label><select className="fi w-full" value={planForm.calculation_method} onChange={e=>setPlanForm({...planForm, calculation_method:e.target.value})}><option value="CALENDAR_DAYS">Calendar days</option><option value="WORKING_DAYS">Working days</option></select></div>
            </div>
            <div className="flex gap-4 text-sm"><label className="flex items-center gap-2"><input type="checkbox" checked={planForm.certificate_required} onChange={e=>setPlanForm({...planForm, certificate_required:e.target.checked})}/>Certificate required</label><label className="flex items-center gap-2"><input type="checkbox" checked={planForm.emergency_extension_allowed} onChange={e=>setPlanForm({...planForm, emergency_extension_allowed:e.target.checked})}/>Extensions allowed</label></div>
            <div className="flex justify-end gap-2 pt-3 border-t"><button type="button" className="btn o" onClick={()=>setShowPlanModal(false)}>Cancel</button><button type="submit" disabled={submitting || instrumentTypes.length===0} className="btn">{submitting?'Saving...':'Create Plan'}</button></div>
          </form>
        </div></div>
      )}

      {showRecordModal && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6">
          <div className="flex items-center justify-between pb-4 border-b"><h2 className="text-base font-bold">Record Calibration Event</h2><button onClick={()=>setShowRecordModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={handleRecordEvent} className="space-y-4 pt-4">
            <div><label className="block text-xs font-semibold mb-1">Instrument *</label><select className="fi w-full" value={recordForm.asset_id} onChange={e=>setRecordForm({...recordForm, asset_id:e.target.value})} required><option value="">Select instrument</option>{assets.map(a => <option key={a.id} value={a.id}>{a.asset_code} — {a.asset_name}</option>)}</select></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-xs font-semibold mb-1">Measured value *</label><input type="number" step="0.01" className="fi w-full" value={recordForm.measured_value} onChange={e=>setRecordForm({...recordForm, measured_value:e.target.value})} required /></div>
              <div><label className="block text-xs font-semibold mb-1">Reference value *</label><input type="number" step="0.01" className="fi w-full" value={recordForm.reference_value} onChange={e=>setRecordForm({...recordForm, reference_value:e.target.value})} required /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-xs font-semibold mb-1">Tolerance *</label><input type="number" step="0.01" min="0" className="fi w-full" value={recordForm.tolerance} onChange={e=>setRecordForm({...recordForm, tolerance:e.target.value})} required /></div>
              <div><label className="block text-xs font-semibold mb-1">Performed by *</label><input className="fi w-full" value={recordForm.technician_name} onChange={e=>setRecordForm({...recordForm, technician_name:e.target.value})} required /></div>
            </div>
            <div className={`p-3 rounded-xl border flex items-center justify-between ${isPass?'bg-emerald-50 border-emerald-200 text-emerald-900':'bg-rose-50 border-rose-200 text-rose-900'}`}>
              <div className="flex items-center gap-2">{isPass?<CheckCircle2 size={18}/>:<XCircle size={18}/>}<div><div className="text-xs font-bold uppercase">Calculated error: {errorVal.toFixed(4)}</div><div className="text-[11px] opacity-80">|measured - reference| = |{measured} - {reference}|</div></div></div>
              <span className={`tg ${isPass?'g':''}`}>{isPass?'PASS (preview)':'FAIL (preview)'}</span>
            </div>
            <div><label className="block text-xs font-semibold mb-1">Notes</label><textarea className="fi w-full" rows={3} value={recordForm.notes} onChange={e=>setRecordForm({...recordForm, notes:e.target.value})} /></div>
            <p className="text-[11px] text-slate-500">Final pass/fail and due-date updates are determined by backend calibration logic.</p>
            <div className="flex justify-end gap-2 pt-3 border-t"><button type="button" className="btn o" onClick={()=>setShowRecordModal(false)}>Cancel</button><button type="submit" disabled={submitting} className="btn">{submitting?'Submitting...':'Record Calibration'}</button></div>
          </form>
        </div></div>
      )}
    </>
  );
}
