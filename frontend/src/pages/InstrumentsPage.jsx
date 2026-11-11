import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { Plus, Download, Bell, Box, CheckCircle, Calendar, AlertTriangle, X } from 'lucide-react';

export default function InstrumentsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [assets, setAssets] = useState([]);
  const [instrumentTypes, setInstrumentTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [assetEvents, setAssetEvents] = useState([]);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');
  const [formData, setFormData] = useState({
    asset_name: '', instrument_type_id: '', serial_number: '', manufacturer: '', model_number: '',
    plant_location: 'Plant 01 - Main Floor', production_line: 'Line 1', calibration_interval_days: 180,
    requires_calibration: true, requires_certificate: true
  });

  const fetchAssets = async () => {
    const params = new URLSearchParams();
    params.set('limit', '500');
    if (search.trim()) params.set('search', search.trim());
    if (typeFilter) params.set('instrument_type_id', typeFilter);
    if (statusFilter) params.set('calibration_status', statusFilter);
    const [assetsRes, typesRes] = await Promise.all([
      api.get(`/assets?${params.toString()}`),
      api.get('/instrument-types?include_inactive=false')
    ]);
    const assetList = Array.isArray(assetsRes.data) ? assetsRes.data : (assetsRes.data?.items || []);
    const typesList = Array.isArray(typesRes.data) ? typesRes.data : [];
    setAssets(assetList);
    setInstrumentTypes(typesList);
    if (assetList.length > 0) {
      const current = assetList.find(a => a.id === selectedAsset?.id) || assetList[0];
      setSelectedAsset(current);
      fetchAssetHistory(current.id);
    } else {
      setSelectedAsset(null);
      setAssetEvents([]);
    }
    if (!formData.instrument_type_id && typesList.length > 0) {
      setFormData(prev => ({ ...prev, instrument_type_id: String(typesList[0].id) }));
    }
  };

  const fetchAssetHistory = async (assetId) => {
    try {
      const res = await api.get(`/calibration/events?asset_id=${assetId}&limit=20`);
      setAssetEvents(Array.isArray(res.data) ? res.data : (res.data?.items || []));
    } catch { setAssetEvents([]); }
  };

  useEffect(() => { (async () => { try { await fetchAssets(); } finally { setLoading(false); } })(); }, []);
  useEffect(() => { const t = setTimeout(() => { fetchAssets().catch(() => {}); }, 250); return () => clearTimeout(t); }, [search, typeFilter, statusFilter]);

  const filteredAssets = useMemo(() => assets, [assets]); // server-side filtered
  const totalCount = assets.length;
  const calibratedCount = assets.filter(a => ['COMPLIANT', 'VALID'].includes(a.calibration_status)).length;
  const dueCount = assets.filter(a => ['UPCOMING', 'DUE_SOON', 'EXTENSION'].includes(a.calibration_status)).length;
  const overdueCount = assets.filter(a => ['OVERDUE', 'FAILED'].includes(a.calibration_status)).length;

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!formData.instrument_type_id) return alert('Please select an instrument type.');
    setSubmitting(true);
    try {
      await api.post('/assets', {
        asset_name: formData.asset_name,
        instrument_type_id: parseInt(formData.instrument_type_id, 10),
        serial_number: formData.serial_number,
        manufacturer: formData.manufacturer,
        model_number: formData.model_number,
        plant_location: formData.plant_location,
        production_line: formData.production_line,
        calibration_interval_days: parseInt(formData.calibration_interval_days, 10),
        requires_calibration: !!formData.requires_calibration,
        requires_certificate: !!formData.requires_certificate,
      });
      setIsAddModalOpen(false);
      setFormData(prev => ({ ...prev, asset_name:'', serial_number:'', manufacturer:'', model_number:'' }));
      await fetchAssets();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add instrument');
    } finally { setSubmitting(false); }
  };

  const handleExport = () => {
    const rows = [['Asset Code','Name','Type','Manufacturer','Model','Status','Last Calibrated','Next Due'],
      ...filteredAssets.map(a => [a.asset_code,a.asset_name,a.instrument_type_name||'',a.manufacturer,a.model_number,a.calibration_status,a.last_calibration_date||'',a.next_due_date||''])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r => r.map(x => `"${String(x ?? '').replace(/"/g,'""')}"`).join(',')).join('\n');
    const link = document.createElement('a'); link.href = encodeURI(csv); link.download = `calibraflow_instruments_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(link); link.click(); document.body.removeChild(link);
  };

  const formatDateSafe = (d) => {
    if (!d) return '—';
    const parsed = new Date(d);
    return isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString();
  };

  if (loading) return <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3"><div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div><p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Loading instruments...</p></div>;

  return (
    <>
      <div className="bc">Home / Instruments</div>
      <header className="hd">
        <div><h1>Instruments</h1><p>{assets.length.toLocaleString()} assets · filter by type and status</p></div>
        <div className="tb">
          <button className="btn" onClick={() => setIsAddModalOpen(true)} disabled={instrumentTypes.length === 0}><Plus size={18}/><span>Add instrument</span></button>
          <button className="btn o" onClick={handleExport}><Download size={18}/><span>Export</span></button>
        </div>
      </header>

      <div className="al"><span><Bell size={20}/> {dueCount} upcoming and {overdueCount} overdue/failed instruments require attention</span><button className="btn" onClick={() => navigate('/alerts')}>View alerts</button></div>

      <section className="kp">
        <div className="cd"><span className="ic"><Box size={26}/></span><div><small>Total instruments</small><b>{totalCount.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic g"><CheckCircle size={26}/></span><div><small>Calibrated</small><b className="g">{calibratedCount.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic y"><Calendar size={26}/></span><div><small>Due / upcoming</small><b className="y">{dueCount.toLocaleString()}</b></div></div>
        <div className="cd"><span className="ic r"><AlertTriangle size={26}/></span><div><small>Overdue / failed</small><b className="r">{overdueCount.toLocaleString()}</b></div></div>
      </section>

      <div className="tb">
        <input className="fi" placeholder="Search asset code, name, serial..." value={search} onChange={(e)=>setSearch(e.target.value)} />
        <select className="fi" value={typeFilter} onChange={(e)=>setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          {instrumentTypes.map(t => <option key={t.id} value={t.id}>{t.type_name}</option>)}
        </select>
        <select className="fi" value={statusFilter} onChange={(e)=>setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="COMPLIANT">Compliant</option>
          <option value="UPCOMING">Upcoming</option>
          <option value="OVERDUE">Overdue</option>
          <option value="FAILED">Failed</option>
          <option value="RESTRICTED">Restricted</option>
        </select>
        {(search || typeFilter || statusFilter) && <button className="btn o" onClick={()=>{setSearch(''); setTypeFilter(''); setStatusFilter('');}}>Clear</button>}
      </div>

      <div className="pn">
        <table>
          <thead><tr><th>Asset</th><th>Name</th><th>Type</th><th>Production line</th><th>Last calibrated</th><th>Next due</th><th>Status</th></tr></thead>
          <tbody>
            {filteredAssets.length > 0 ? filteredAssets.map(asset => (
              <tr key={asset.id} onClick={() => { setSelectedAsset(asset); fetchAssetHistory(asset.id); }} className={`cursor-pointer ${selectedAsset?.id===asset.id ? 'bg-blue-50/60 font-semibold' : 'hover:bg-slate-50/80'}`}>
                <td>{asset.asset_code}</td>
                <td>{asset.asset_name}</td>
                <td>{asset.instrument_type_name || '—'}</td>
                <td>{asset.production_line || '—'}</td>
                <td>{formatDateSafe(asset.last_calibration_date)}</td>
                <td>{formatDateSafe(asset.next_due_date)}</td>
                <td><StatusBadge status={asset.calibration_status} /></td>
              </tr>
            )) : <tr><td colSpan="7" className="text-center py-8 text-slate-500">No instruments matched the selected filters.</td></tr>}
          </tbody>
        </table>
      </div>

      {selectedAsset && (
        <div className="pn">
          <h2>Service history ({selectedAsset.asset_code} · {selectedAsset.instrument_type_name || selectedAsset.asset_name}) <span>{selectedAsset.calibration_status}</span></h2>
          <div className="tl">
            {assetEvents.length > 0 ? assetEvents.map((evt) => (
              <div key={evt.id} className={evt.result === 'FAIL' ? 'd' : ''}>
                <b>{formatDateSafe(evt.calibration_date)}</b>
                {evt.result || 'Recorded'} · Error {evt.measurement_error != null ? `${evt.measurement_error}%` : '—'}
              </div>
            )) : <div><b>No calibration events yet</b>History will appear after calibration records are created.</div>}
          </div>
        </div>
      )}

      {isAddModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100"><h2 className="text-base font-bold text-slate-900">Add New Instrument</h2><button onClick={()=>setIsAddModalOpen(false)} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400"><X size={18}/></button></div>
            <form onSubmit={handleAddSubmit} className="space-y-4 pt-4">
              <div><label className="block text-xs font-semibold text-slate-700 mb-1">Instrument Name *</label><input className="fi w-full" value={formData.asset_name} onChange={e=>setFormData({...formData, asset_name:e.target.value})} required /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-semibold text-slate-700 mb-1">Instrument Type *</label><select className="fi w-full" value={formData.instrument_type_id} onChange={e=>setFormData({...formData, instrument_type_id:e.target.value})} required><option value="">Select type</option>{instrumentTypes.map(t => <option key={t.id} value={t.id}>{t.type_name}</option>)}</select></div>
                <div><label className="block text-xs font-semibold text-slate-700 mb-1">Serial Number *</label><input className="fi w-full" value={formData.serial_number} onChange={e=>setFormData({...formData, serial_number:e.target.value})} required /></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-semibold text-slate-700 mb-1">Manufacturer *</label><input className="fi w-full" value={formData.manufacturer} onChange={e=>setFormData({...formData, manufacturer:e.target.value})} required /></div>
                <div><label className="block text-xs font-semibold text-slate-700 mb-1">Model Number *</label><input className="fi w-full" value={formData.model_number} onChange={e=>setFormData({...formData, model_number:e.target.value})} required /></div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs font-semibold text-slate-700 mb-1">Plant Location *</label><input className="fi w-full" value={formData.plant_location} onChange={e=>setFormData({...formData, plant_location:e.target.value})} required /></div>
                <div><label className="block text-xs font-semibold text-slate-700 mb-1">Production Line *</label><input className="fi w-full" value={formData.production_line} onChange={e=>setFormData({...formData, production_line:e.target.value})} required /></div>
              </div>
              <div><label className="block text-xs font-semibold text-slate-700 mb-1">Calibration Interval (Days) *</label><input type="number" min="1" className="fi w-full" value={formData.calibration_interval_days} onChange={e=>setFormData({...formData, calibration_interval_days:e.target.value})} required /></div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100"><button type="button" className="btn o" onClick={()=>setIsAddModalOpen(false)}>Cancel</button><button type="submit" disabled={submitting || instrumentTypes.length===0} className="btn">{submitting?'Registering...':'Add Instrument'}</button></div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
