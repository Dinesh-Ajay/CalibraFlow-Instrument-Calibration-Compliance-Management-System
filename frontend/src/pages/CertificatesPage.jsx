import React, { useEffect, useState } from 'react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { Upload, Download, Check, X } from 'lucide-react';

export default function CertificatesPage() {
  const [certificates, setCertificates] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [checkFilter, setCheckFilter] = useState('All checks');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadForm, setUploadForm] = useState({ calibration_event_id:'', asset_id:'', certificate_number:'', issue_date:new Date().toISOString().slice(0,10), expiry_date:new Date(Date.now()+180*86400000).toISOString().slice(0,10) });

  const fetchData = async () => {
    try {
      const [certRes, evRes] = await Promise.all([api.get('/certificates'), api.get('/calibration/events?limit=100')]);
      const certList = Array.isArray(certRes.data) ? certRes.data : (certRes.data?.items || []);
      const evList = Array.isArray(evRes.data) ? evRes.data : (evRes.data?.items || []);
      setCertificates(certList); setEvents(evList);
      if (evList.length && !uploadForm.calibration_event_id) setUploadForm(p => ({...p, calibration_event_id:String(evList[0].id), asset_id:String(evList[0].asset_id)}));
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };
  useEffect(()=>{ fetchData(); }, []);

  const handleVerify = async (id) => {
    try { await api.patch(`/certificates/${id}/verify`, { verification_status:'VERIFIED', notes:'Verified by quality workflow' }); fetchData(); }
    catch (e) { alert(e.response?.data?.detail || 'Verification failed'); }
  };

  const handleUpload = async (e) => {
    e.preventDefault(); setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append('calibration_event_id', uploadForm.calibration_event_id);
      fd.append('asset_id', uploadForm.asset_id);
      fd.append('certificate_number', uploadForm.certificate_number || `CERT-${Date.now()}`);
      fd.append('issue_date', new Date(uploadForm.issue_date).toISOString());
      fd.append('expiry_date', new Date(uploadForm.expiry_date).toISOString());
      if (selectedFile) fd.append('file', selectedFile);
      await api.post('/certificates/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setShowUploadModal(false); setSelectedFile(null); fetchData();
    } catch (e) { alert(e.response?.data?.detail || 'Upload failed'); } finally { setSubmitting(false); }
  };

  const formatDateSafe = (d) => {
    if (!d) return '—';
    const parsed = new Date(d);
    return isNaN(parsed.getTime()) ? '—' : parsed.toLocaleDateString();
  };

  const rows = certificates.map(c => {
    const expired = c.expiry_date && new Date(c.expiry_date) < new Date();
    let check = 'Valid', cls = 'g';
    if (c.verification_status === 'INVALID' || c.verification_status === 'REJECTED') { check = c.verification_status === 'INVALID' ? 'Wrong/Invalid' : 'Rejected'; cls=''; }
    else if (expired) { check = 'Expired'; cls=''; }
    else if (c.verification_status === 'PENDING') { check = 'Pending QA'; cls='y'; }
    else if (c.verification_status === 'VERIFIED') { check = 'Valid'; cls='g'; }
    return { ...c, check, cls, canVerify: c.verification_status === 'PENDING' };
  }).filter(r => {
    const q = search.toLowerCase();
    const ms = !q || [r.certificate_code,r.certificate_number,r.asset_code,r.calibration_event_id].some(v=>String(v||'').toLowerCase().includes(q));
    const mc = checkFilter==='All checks' || (checkFilter==='Mismatch' && (r.check.includes('Wrong')||r.check==='Rejected')) || r.check.toLowerCase()===checkFilter.toLowerCase();
    return ms && mc;
  });

  const exportCsv = () => {
    const csvRows = [['Certificate','Calibration Event','Asset','Valid Until','Status','Check'], ...rows.map(r=>[r.certificate_code,r.calibration_event_id,r.asset_code||r.asset_id,r.expiry_date||'',r.verification_status,r.check])];
    const csv = "data:text/csv;charset=utf-8," + csvRows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const a=document.createElement('a'); a.href=encodeURI(csv); a.download=`calibraflow_certificates_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading certificates...</p></div>;

  return (
    <>
      <div className="bc">Home / Certificates</div>
      <header className="hd"><div><h1>Certificates</h1><p>Certificate records linked to calibration events and assets with verification status.</p></div><div className="tb"><button className="btn" onClick={()=>setShowUploadModal(true)}><Upload size={18}/><span>Upload certificate</span></button><button className="btn o" onClick={exportCsv}><Download size={18}/><span>Export</span></button></div></header>
      <div className="tb"><input className="fi" placeholder="Search certificate, asset..." value={search} onChange={e=>setSearch(e.target.value)} /><select className="fi" value={checkFilter} onChange={e=>setCheckFilter(e.target.value)}><option>All checks</option><option>Valid</option><option>Pending QA</option><option>Mismatch</option><option>Expired</option><option>Rejected</option></select></div>
      <div className="pn"><table><thead><tr><th>Certificate</th><th>Calibration</th><th>Asset</th><th>Valid until</th><th>Verification</th><th>Check</th><th>Actions</th></tr></thead><tbody>
        {rows.length ? rows.map(r => (<tr key={r.id}><td>{r.certificate_code}</td><td>{r.calibration_event_id}</td><td>{r.asset_code || r.asset_id}</td><td>{formatDateSafe(r.expiry_date)}</td><td><StatusBadge status={r.verification_status} /></td><td><span className={`tg ${r.cls}`}>{r.check}</span></td><td>{r.canVerify && <button className="btn sm o" onClick={()=>handleVerify(r.id)}><Check size={14}/> Verify</button>}</td></tr>)) : <tr><td colSpan="7" className="text-center py-8 text-slate-500">No certificates found.</td></tr>}
      </tbody></table></div>

      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center p-4 z-50"><div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6">
          <div className="flex items-center justify-between pb-4 border-b"><h2 className="text-base font-bold">Upload Certificate</h2><button onClick={()=>setShowUploadModal(false)} className="p-1 rounded hover:bg-slate-100"><X size={18}/></button></div>
          <form onSubmit={handleUpload} className="space-y-4 pt-4">
            <div><label className="block text-xs font-semibold mb-1">Calibration Event *</label><select className="fi w-full" required value={uploadForm.calibration_event_id} onChange={e=>{const id=e.target.value; const ev=events.find(x=>String(x.id)===String(id)); setUploadForm({...uploadForm, calibration_event_id:id, asset_id: ev?String(ev.asset_id):uploadForm.asset_id});}}><option value="">Select event</option>{events.map(ev => <option key={ev.id} value={ev.id}>{ev.calibration_code} (Asset {ev.asset_id})</option>)}</select></div>
            <div><label className="block text-xs font-semibold mb-1">Certificate number *</label><input className="fi w-full" value={uploadForm.certificate_number} onChange={e=>setUploadForm({...uploadForm, certificate_number:e.target.value})} required /></div>
            <div className="grid grid-cols-2 gap-3"><div><label className="block text-xs font-semibold mb-1">Issue date *</label><input type="date" className="fi w-full" value={uploadForm.issue_date} onChange={e=>setUploadForm({...uploadForm, issue_date:e.target.value})} required /></div><div><label className="block text-xs font-semibold mb-1">Expiry date *</label><input type="date" className="fi w-full" value={uploadForm.expiry_date} onChange={e=>setUploadForm({...uploadForm, expiry_date:e.target.value})} required /></div></div>
            <div><label className="block text-xs font-semibold mb-1">Certificate file (optional)</label><input type="file" className="fi w-full pt-2" accept=".pdf,.png,.jpg,.jpeg" onChange={e=>setSelectedFile(e.target.files?.[0]||null)} /></div>
            <div className="flex justify-end gap-2 pt-3 border-t"><button type="button" className="btn o" onClick={()=>setShowUploadModal(false)}>Cancel</button><button type="submit" className="btn" disabled={submitting}>{submitting?'Uploading...':'Save Certificate'}</button></div>
          </form>
        </div></div>
      )}
    </>
  );
}
