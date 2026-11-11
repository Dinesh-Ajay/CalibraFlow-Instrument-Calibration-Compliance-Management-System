import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { isModuleAllowed } from '../config/navigation';
import {
  Plus, Download, Bell, Box, Calendar, AlertTriangle, ShieldAlert,
  Database, Clock, ShieldCheck, Factory, Kanban, FileCheck2, Wrench, History
} from 'lucide-react';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { roles } = useAuth();
  const [data, setData] = useState(null);
  const [overdueAssets, setOverdueAssets] = useState([]);
  const [loading, setLoading] = useState(true);

  const isOperator = (roles?.includes('Plant Operator') || roles?.includes('operator')) && !roles?.includes('Administrator') && !roles?.includes('admin');
  const isQuality = (roles?.includes('Quality Engineer') || roles?.includes('quality_eng')) && !roles?.includes('Administrator') && !roles?.includes('admin');
  const isMaint = (roles?.includes('Maintenance Engineer') || roles?.includes('maint_eng')) && !roles?.includes('Administrator') && !roles?.includes('admin');
  const isPlanner = (roles?.includes('Production Planner') || roles?.includes('planner')) && !roles?.includes('Administrator') && !roles?.includes('admin');

  useEffect(() => {
    (async () => {
      try {
        const [summaryRes, assetsRes] = await Promise.all([
          api.get('/dashboard/summary'),
          api.get('/assets?limit=200')
        ]);
        setData(summaryRes.data || {});
        const allAssets = Array.isArray(assetsRes.data) ? assetsRes.data : (assetsRes.data?.items || []);
        setOverdueAssets(allAssets.filter(a => ['OVERDUE','FAILED','RESTRICTED'].includes(a.calibration_status) || a.operational_status !== 'ACTIVE').slice(0, 8));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const k = data?.kpis || {};
  const r = data?.rates || {};
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
    const a = document.createElement('a'); a.href = encodeURI(csv); a.download = `calibraflow_dashboard_${new Date().toISOString().slice(0,10)}.csv`; document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  // Role-tailored quick action cards
  const quickActions = useMemo(() => {
    const actions = [];
    if (isModuleAllowed('instruments', roles)) {
      actions.push({ to: '/instruments', label: 'Instrument register', sub: 'View instruments and availability', icon: Database, colorClass: '' });
    }
    if (isOperator) {
      actions.push({ to: '/production-use', label: 'Production usage gate', sub: 'Validate line availability', icon: Factory, colorClass: 'g' });
    } else if (isPlanner) {
      actions.push({ to: '/workflow-board', label: 'Workflow board', sub: 'Downtime coordination', icon: Kanban, colorClass: 'y' });
      actions.push({ to: '/work-orders', label: 'Work orders', sub: 'Schedule maintenance', icon: Wrench, colorClass: '' });
    } else if (isQuality) {
      actions.push({ to: '/certificates', label: 'Certificates', sub: 'Verify calibration certificates', icon: FileCheck2, colorClass: 'g' });
      actions.push({ to: '/data-quality', label: 'Data quality', sub: 'Validation & anomaly telemetry', icon: ShieldCheck, colorClass: 'y' });
    } else if (isMaint) {
      actions.push({ to: '/plans-events', label: 'Plans & events', sub: 'Execute calibrations', icon: Calendar, colorClass: 'y' });
      actions.push({ to: '/work-orders', label: 'Work orders', sub: 'Maintenance progress & downtime', icon: Wrench, colorClass: '' });
    } else {
      // Administrator
      actions.push({ to: '/plans-events', label: 'Plans & events', sub: 'Calibration intervals & routines', icon: Calendar, colorClass: 'y' });
      actions.push({ to: '/audit', label: 'Audit trail', sub: 'Immutable compliance history', icon: History, colorClass: '' });
      actions.push({ to: '/data-quality', label: 'Data quality', sub: 'Validation & anomaly telemetry', icon: ShieldCheck, colorClass: 'g' });
    }
    if (isModuleAllowed('alerts', roles) && actions.length < 4) {
      actions.push({ to: '/alerts', label: 'Alerts', sub: 'Compliance & operational alerts', icon: Bell, colorClass: 'r' });
    }
    return actions.slice(0, 4);
  }, [roles, isOperator, isPlanner, isQuality, isMaint]);

  if (loading) return <div className="pn"><p className="text-sm text-slate-500">Loading dashboard...</p></div>;

  return (
    <>
      <div className="bc">Home / Dashboard</div>
      <header className="hd">
        <div>
          <h1>Dashboard</h1>
          <p>
            {isOperator
              ? 'Plant Operator console: live instrument availability and production usage gating.'
              : isPlanner
              ? 'Production Planner console: calibration schedules, workflow status, and planned downtime.'
              : isQuality
              ? 'Quality Engineer console: compliance metrics, certificate verification, and audit review.'
              : isMaint
              ? 'Maintenance Engineer console: instrument calibrations, assigned work orders, and technical tasks.'
              : 'Enterprise calibration compliance and operational overview (database-backed).'}
          </p>
        </div>
        <div className="tb">
          {isOperator ? (
            <button className="btn" onClick={() => navigate('/production-use')}>
              <Factory size={18} />
              <span>Production gate</span>
            </button>
          ) : isModuleAllowed('work-orders', roles) ? (
            <button className="btn" onClick={() => navigate('/work-orders')}>
              <Plus size={18} />
              <span>Work orders</span>
            </button>
          ) : null}
          <button className="btn o" onClick={exportCsv}>
            <Download size={18} />
            <span>Export</span>
          </button>
        </div>
      </header>

      <div className="al">
        <span>
          <Bell size={20} /> {due30} instrument(s) due soon/upcoming and {overdue} overdue/at-risk.
        </span>
        <button className="btn" onClick={() => navigate('/alerts')}>View alerts</button>
      </div>

      <section className="kp">
        <div className="cd">
          <span className="ic"><Box size={26} /></span>
          <div>
            <small>Instruments in service</small>
            <b>{total.toLocaleString()}</b>
          </div>
        </div>
        <div className="cd">
          <span className="ic y"><Calendar size={26} /></span>
          <div>
            <small>Due soon / upcoming</small>
            <b className="y">{due30.toLocaleString()}</b>
          </div>
        </div>
        <div className="cd">
          <span className="ic r"><AlertTriangle size={26} /></span>
          <div>
            <small>Overdue</small>
            <b className="r">{overdue.toLocaleString()}</b>
          </div>
        </div>
        <div className="cd">
          <span className="ic r"><ShieldAlert size={26} /></span>
          <div>
            <small>Blocked production uses</small>
            <b className="r">{blocked.toLocaleString()}</b>
          </div>
        </div>
      </section>

      <section className="g2">
        <div className="pn">
          <h2>Calibration compliance</h2>
          <div className="dn">
            <div
              className="ring"
              style={{
                background: `conic-gradient(#16A34A 0% ${complianceRate}%, #E5EAF3 ${complianceRate}% 100%)`
              }}
            >
              <div>
                <b>{complianceRate}%</b>
                <small>compliant</small>
              </div>
            </div>
            <div className="text-sm space-y-1.5 text-slate-700">
              <div>Compliant: {Number(k.calibration_compliant || 0).toLocaleString()}</div>
              <div>Failed calibrations: {Number(k.failed_calibrations || 0).toLocaleString()}</div>
              <div>Missing certificates: {Number(k.missing_certificates || 0).toLocaleString()}</div>
              <div>Open impact assessments: {Number(k.pending_impact_assessments || 0).toLocaleString()}</div>
            </div>
          </div>
        </div>

        <div className="pn">
          <h2>Operational metrics</h2>
          <table>
            <tbody>
              <tr><td>Calibration success rate</td><td>{Number(r.calibration_success_rate || 0)}%</td></tr>
              <tr><td>Certificate verification rate</td><td>{Number(r.certificate_verification_rate || 0)}%</td></tr>
              <tr><td>Blocked usage rate</td><td>{Number(r.blocked_usage_rate || 0)}%</td></tr>
              <tr><td>Open/active work orders</td><td>{Number(k.open_work_orders || 0).toLocaleString()}</td></tr>
              <tr><td>Active assets</td><td>{Number(k.active_assets || 0).toLocaleString()}</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="g2">
        <div className="pn">
          <h2>
            Overdue / restricted instruments{' '}
            <Link to="/instruments" className="text-xs text-blue-600 font-semibold hover:underline">
              View instruments
            </Link>
          </h2>
          <table>
            <thead>
              <tr><th>Asset</th><th>Name</th><th>Due</th><th>Status</th></tr>
            </thead>
            <tbody>
              {overdueAssets.length ? (
                overdueAssets.map((a) => (
                  <tr key={a.id}>
                    <td>{a.asset_code}</td>
                    <td>{a.asset_name}</td>
                    <td>{formatDateSafe(a.next_due_date)}</td>
                    <td><StatusBadge status={a.calibration_status || a.operational_status} /></td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="text-center py-6 text-slate-500">
                    No overdue or restricted instruments found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="pn">
          <h2>Quick actions</h2>
          <section className="qc" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Link key={action.to} to={action.to}>
                  <span className={`ic ${action.colorClass || ''}`}><Icon size={22} /></span>
                  <div>
                    <b>{action.label}</b>
                    <small>{action.sub}</small>
                  </div>
                </Link>
              );
            })}
          </section>
        </div>
      </section>
    </>
  );
}
