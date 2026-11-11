import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Download, RefreshCw, AlertCircle } from 'lucide-react';

export default function DataQualityPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try { const res = await api.get('/data-quality/report'); setData(res.data); }
    catch (e) { setError(e.response?.data?.detail || 'Failed to load data quality report.'); }
    finally { setLoading(false); }
  };
  useEffect(()=>{ load(); }, []);

  const report = data?.validation_report || {};
  const summary = data?.generation_summary || {};
  const anomalies = report.detected_anomalies || [];

  const exportCsv = () => {
    const rows = [['Issue type','Record','Intentional','Details'], ...anomalies.map(a=>[a.issue_type,a.record_id,a.intentional,a.details])];
    const csv = "data:text/csv;charset=utf-8," + rows.map(r=>r.map(x=>`"${String(x??'').replace(/"/g,'""')}"`).join(',')).join('\n');
    const el=document.createElement('a'); el.href=encodeURI(csv); el.download='calibraflow_data_quality.csv'; document.body.appendChild(el); el.click(); document.body.removeChild(el);
  };

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading data quality report...</p></div>;

  return (
    <>
      <div className="bc">Home / Data quality</div>
      <header className="hd"><div><h1>Data quality</h1><p>Seed {data?.seed || 20261022}. Validation and anomaly detection results from stored report data.</p></div><div className="tb"><button className="btn o" onClick={load}><RefreshCw size={16}/> Reload</button><button className="btn o" onClick={exportCsv}><Download size={18}/> Export</button></div></header>
      {error && <div className="al"><span><AlertCircle size={18}/> {error}</span></div>}
      <section className="kp">
        <div className="cd"><div><small>Total records evaluated</small><b>{Number(report.total_records_evaluated||0).toLocaleString()}</b></div></div>
        <div className="cd"><div><small>FK violations</small><b className={report.foreign_key_violations ? 'r':'g'}>{Number(report.foreign_key_violations||0).toLocaleString()}</b></div></div>
        <div className="cd"><div><small>Detected anomalies</small><b>{Number(report.detected_anomalies_count||0).toLocaleString()}</b></div></div>
        <div className="cd"><div><small>Validation status</small><b className={report.validation_passed ? 'g':'r'}>{report.validation_passed ? 'PASS' : (Object.keys(report).length ? 'FAIL' : 'N/A')}</b></div></div>
      </section>
      <section className="g2">
        <div className="pn"><h2>Validation summary</h2><table><tbody>
          <tr><td>Failed calibrations</td><td>{Number(report.failed_calibrations_count||0).toLocaleString()}</td></tr>
          <tr><td>Blocked production uses</td><td>{Number(report.blocked_production_usages_count||0).toLocaleString()}</td></tr>
          <tr><td>Missing impact assessments</td><td>{Number(report.missing_impact_assessments_count||0).toLocaleString()}</td></tr>
          <tr><td>Ground-truth matches</td><td>{Number(report.intentional_ground_truth_matches||0).toLocaleString()}</td></tr>
          <tr><td>Generation summary present</td><td>{Object.keys(summary).length ? 'Yes' : 'No'}</td></tr>
        </tbody></table></div>
        <div className="pn"><h2>Detected anomalies <span>{anomalies.length}</span></h2>
          {anomalies.length ? <table><thead><tr><th>Type</th><th>Record</th><th>Intentional</th></tr></thead><tbody>{anomalies.slice(0,50).map((a,i)=>(<tr key={i}><td>{a.issue_type}</td><td>{a.record_id}</td><td>{a.intentional ? 'Yes':'No'}</td></tr>))}</tbody></table> : <p className="text-sm text-slate-500">No anomaly details available. Ensure `data/validation_report.json` exists.</p>}
        </div>
      </section>
    </>
  );
}
