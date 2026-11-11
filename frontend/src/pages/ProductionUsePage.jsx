import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { Download, CheckCircle, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function ProductionUsePage() {
  const [usages, setUsages] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [decisionFilter, setDecisionFilter] = useState('');
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [productionLine, setProductionLine] = useState('Line 1');
  const [batchLot, setBatchLot] = useState('');
  const [validating, setValidating] = useState(false);
  const [recording, setRecording] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  const fetchData = async () => {
    const params = new URLSearchParams(); params.set('limit','100');
    if (decisionFilter) params.set('validation_decision', decisionFilter);
    const [useRes, asRes] = await Promise.all([api.get(`/production/usage?${params.toString()}`), api.get('/assets?limit=500')]);
    const useList = Array.isArray(useRes.data) ? useRes.data : (useRes.data?.items || []);
    const asList = Array.isArray(asRes.data) ? asRes.data : (asRes.data?.items || []);
    setUsages(useList); setAssets(asList);
    if (!selectedAssetId && asList.length) setSelectedAssetId(String(asList[0].id));
  };

  useEffect(() => { (async()=>{ try { await fetchData(); } finally { setLoading(false); } })(); }, []);
  useEffect(() => { fetchData().catch(()=>{}); }, [decisionFilter]);

  const filteredUsages = useMemo(() => usages.filter(u => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return [u.usage_code, u.asset_code, u.asset_name, u.production_line, u.decision_reason, u.operator_name].some(v => String(v||'').toLowerCase().includes(q));
  }), [usages, search]);

  const allowedCount = usages.filter(u => u.validation_decision === 'ALLOWED').length;
  const flaggedCount = usages.filter(u => u.validation_decision === 'ALLOWED_WITH_EXCEPTION').length;
  const blockedCount = usages.filter(u => u.validation_decision === 'BLOCKED').length;

  const dryRun = async () => {
    if (!selectedAssetId) return;
    setValidating(true); setValidationResult(null);
    try {
      const res = await api.post('/production/validate-usage', { asset_id: parseInt(selectedAssetId,10), production_line: productionLine || 'Line 1', usage_timestamp: new Date().toISOString() });
      setValidationResult({ ...res.data, dry_run: true, batch_lot: batchLot });
    } catch (err) {
      setValidationResult({ decision:'BLOCKED', decision_reason: err.response?.data?.detail || 'Validation failed', is_allowed:false, dry_run:true, batch_lot: batchLot });
    } finally { setValidating(false); }
  };

  const recordUse = async () => {
    if (!selectedAssetId) return;
    setRecording(true);
    try {
      const res = await api.post('/production/usage', { asset_id: parseInt(selectedAssetId,10), production_line: productionLine || 'Line 1', usage_timestamp: new Date().toISOString(), usage_status: 'RECORDED' });
      const usage = res.data;
      setValidationResult({
        decision: usage.validation_decision,
        decision_reason: usage.decision_reason,
        asset_code: usage.asset_code,
        asset_name: usage.asset_name,
        last_calibration_date: usage.last_calibration_date,
        applicable_due_date: usage.applicable_due_date,
        is_allowed: usage.validation_decision !== 'BLOCKED',
        dry_run: false,
        batch_lot: batchLot,
      });
      await fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record production use');
      await fetchData();
    } finally { setRecording(false); }
  };

  const exportCsv = () => {
    const rows = [['Usage','Asset','Line','Decision','Reason','Timestamp','Operator'], ...filteredUsages.map(u => [u.usage_code,u.asset_code||u.asset_id,u.production_line,u.validation_decision,u.decision_reason,u.usage_timestamp,u.operator_name||u.operator_id])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const a = document.createElement('a'); a.href = encodeURI(csv); a.download = `calibraflow_production_use_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  if (loading) return <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3"><div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div><p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Loading production usage...</p></div>;

  const selectedAsset = assets.find(a => String(a.id) === String(selectedAssetId));

  return (
    <>
      <div className="bc">Home / Production use</div>
      <header className="hd"><div><h1>Production use</h1><p>Each usage attempt is validated by backend rules and persisted with its decision.</p></div><div className="tb"><button className="btn o" onClick={exportCsv}><Download size={18}/><span>Export</span></button></div></header>
      <section className="kp">
        <div className="cd"><span className="ic g"><CheckCircle size={26}/></span><div><small>Allowed</small><b className="g">{allowedCount.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic y"><AlertTriangle size={26}/></span><div><small>Allowed with exception</small><b className="y">{flaggedCount.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic r"><ShieldAlert size={26}/></span><div><small>Blocked</small><b className="r">{blockedCount.toLocaleString()}</b></div></div>
      </section>

      <div className="pn border border-blue-200 bg-blue-50/25 p-5 shadow-sm" style={{ overflow: 'visible' }}>
        <h2><span>Live Production Usage Gate Evaluation</span><span className="text-xs text-blue-700 font-semibold">Backend deterministic validation</span></h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5 mt-3.5 items-end">
          <div><label className="block text-xs font-semibold text-slate-700 mb-1">Target Instrument *</label><select className="fi w-full" value={selectedAssetId} onChange={e=>setSelectedAssetId(e.target.value)}>{assets.map(a => <option key={a.id} value={a.id}>{a.asset_code} — {a.asset_name} ({a.calibration_status})</option>)}</select></div>
          <div><label className="block text-xs font-semibold text-slate-700 mb-1">Production Line *</label><input className="fi w-full" value={productionLine} onChange={e=>setProductionLine(e.target.value)} placeholder="Line 1" /></div>
          <div><label className="block text-xs font-semibold text-slate-700 mb-1">Batch / Lot Reference</label><input className="fi w-full" value={batchLot} onChange={e=>setBatchLot(e.target.value)} placeholder="Optional reference" /></div>
          <div className="flex gap-2 w-full"><button className="btn o flex-1 h-[44px] justify-center" onClick={dryRun} disabled={validating || !selectedAssetId}>{validating?'Evaluating...':'Dry Run Check'}</button><button className="btn flex-1 h-[44px] justify-center" onClick={recordUse} disabled={recording || !selectedAssetId}>{recording?'Recording...':'Record Use'}</button></div>
        </div>

        {validationResult && (
          <div className={`mt-4 p-4 rounded-xl border ${validationResult.decision==='ALLOWED'?'bg-emerald-50 border-emerald-200 text-emerald-900':validationResult.decision==='ALLOWED_WITH_EXCEPTION'?'bg-amber-50 border-amber-200 text-amber-900':'bg-rose-50 border-rose-200 text-rose-900'}`} style={{minHeight:120}}>
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-2"><span className="font-bold text-sm">Gate Decision:</span><span className={`tg ${validationResult.decision==='ALLOWED'?'g':validationResult.decision==='ALLOWED_WITH_EXCEPTION'?'y':''}`}>{validationResult.decision || 'BLOCKED'}</span>{validationResult.dry_run && <span className="text-xs opacity-80">(dry run)</span>}</div>
              <div className="text-xs opacity-80">{validationResult.asset_code || selectedAsset?.asset_code || ''} {batchLot ? `· Batch ${batchLot}` : ''}</div>
            </div>
            <p className="text-sm mt-2 leading-relaxed break-words" style={{whiteSpace:'normal'}}>{validationResult.decision_reason || validationResult.reason || 'Evaluation completed.'}</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-3 text-xs">
              <div><b>Last calibration:</b> {validationResult.last_calibration_date ? new Date(validationResult.last_calibration_date).toLocaleString() : '—'}</div>
              <div><b>Applicable due date:</b> {validationResult.applicable_due_date ? new Date(validationResult.applicable_due_date).toLocaleString() : '—'}</div>
              <div><b>Certificate:</b> {validationResult.certificate_status || '—'}</div>
            </div>
          </div>
        )}
      </div>

      <div className="tb mt-2">
        <input className="fi" placeholder="Search usage, asset, reason..." value={search} onChange={e=>setSearch(e.target.value)} />
        <select className="fi" value={decisionFilter} onChange={e=>setDecisionFilter(e.target.value)}>
          <option value="">All decisions</option>
          <option value="ALLOWED">ALLOWED</option>
          <option value="ALLOWED_WITH_EXCEPTION">ALLOWED_WITH_EXCEPTION</option>
          <option value="BLOCKED">BLOCKED</option>
        </select>
        {(search || decisionFilter) && <button className="btn o" onClick={()=>{setSearch(''); setDecisionFilter('');}}>Clear</button>}
      </div>

      <div className="pn" style={{overflowX:'auto'}}>
        <table>
          <thead><tr><th>Use event</th><th>Asset</th><th>Line</th><th>Decision</th><th>Reason</th><th>Timestamp</th></tr></thead>
          <tbody>
            {filteredUsages.length ? filteredUsages.map(u => (
              <tr key={u.id}><td>{u.usage_code}</td><td>{u.asset_code || u.asset_id}</td><td>{u.production_line || '—'}</td><td><span className={`tg ${u.validation_decision==='ALLOWED'?'g':u.validation_decision==='ALLOWED_WITH_EXCEPTION'?'y':''}`}>{u.validation_decision}</span></td><td style={{whiteSpace:'normal', minWidth:320}}>{u.decision_reason}</td><td>{u.usage_timestamp ? new Date(u.usage_timestamp).toLocaleString() : '—'}</td></tr>
            )) : <tr><td colSpan="6" className="text-center py-8 text-slate-500">No production usage records matched the selected filters.</td></tr>}
          </tbody>
        </table>
      </div>
    </>
  );
}
