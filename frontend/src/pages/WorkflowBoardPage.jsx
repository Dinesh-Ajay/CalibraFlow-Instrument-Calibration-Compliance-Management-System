import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { Plus, Download, Wrench, AlertTriangle, ShieldCheck, Clock, FileBadge, X } from 'lucide-react';

const WorkflowBoardPage = () => {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const canCreateWo = hasRole(['Administrator', 'admin', 'Maintenance Engineer', 'maint_eng', 'Production Planner', 'planner']);
  const [loading, setLoading] = useState(true);
  const [boardData, setBoardData] = useState({
    dueSoon: [],
    workOrdersOpen: [],
    inCalibration: [],
    failedAction: [],
    certified: []
  });

  // Modal State
  const [showNewWoModal, setShowNewWoModal] = useState(false);
  const [newWoForm, setNewWoForm] = useState({
    asset_id: '',
    work_order_type: 'CALIBRATION',
    priority: 'HIGH',
    planned_downtime_minutes: 120,
    scheduled_start: new Date().toISOString().slice(0, 16),
    description: 'Scheduled calibration routine per calibration plan'
  });
  const [assetsList, setAssetsList] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const fetchBoardData = async () => {
    try {
      const [assetsRes, woRes, calRes, certRes, capaRes] = await Promise.all([
        api.get('/assets?limit=100'),
        api.get('/work-orders'),
        api.get('/calibration/events'),
        api.get('/certificates'),
        api.get('/corrective-actions')
      ]);

      const allAssets = Array.isArray(assetsRes.data) ? assetsRes.data : assetsRes.data?.items || [];
      const allWos = Array.isArray(woRes.data) ? woRes.data : woRes.data?.items || [];
      const allCals = Array.isArray(calRes.data) ? calRes.data : calRes.data?.items || [];
      const allCerts = Array.isArray(certRes.data) ? certRes.data : certRes.data?.items || [];
      const allCapas = Array.isArray(capaRes.data) ? capaRes.data : capaRes.data?.items || [];

      setAssetsList(allAssets);

      // 1. Due soon (UPCOMING or next due within 30 days)
      const dueSoon = allAssets
        .filter((a) => a.calibration_status === 'UPCOMING' || a.calibration_status === 'EXTENSION')
        .slice(0, 10);

      // 2. Work Order Open (ASSIGNED or OPEN)
      const workOrdersOpen = allWos
        .filter((w) => w.status === 'ASSIGNED' || w.status === 'OPEN')
        .slice(0, 10);

      // 3. In Calibration (IN_PROGRESS)
      const inCalibration = allWos
        .filter((w) => w.status === 'IN_PROGRESS')
        .concat(
          allCals.filter((c) => c.measured_value === null || c.result === null)
        )
        .slice(0, 10);

      // 4. Failed, action needed (FAILED calibrations, BLOCKED assets, or open CAPAs)
      const failedAction = allCapas
        .filter((c) => c.status !== 'CLOSED')
        .concat(
          allAssets.filter((a) => a.calibration_status === 'FAILED' || a.operational_status === 'BLOCKED')
        )
        .slice(0, 10);

      // 5. Certified (VERIFIED certificates)
      const certified = allCerts
        .filter((c) => c.verification_status === 'VERIFIED')
        .slice(0, 10);

      setBoardData({
        dueSoon,
        workOrdersOpen,
        inCalibration,
        failedAction,
        certified
      });
    } catch (err) {
      console.error('Failed to load workflow board data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBoardData();
  }, []);

  const handleCreateWorkOrder = async (e) => {
    e.preventDefault();
    if (!newWoForm.asset_id) {
      alert('Please select an asset.');
      return;
    }
    setSubmitting(true);
    try {
      await api.post('/work-orders', {
        asset_id: parseInt(newWoForm.asset_id),
        work_order_type: newWoForm.work_order_type,
        priority: newWoForm.priority,
        planned_downtime_minutes: parseInt(newWoForm.planned_downtime_minutes),
        scheduled_start: new Date(newWoForm.scheduled_start).toISOString(),
        description: newWoForm.description
      });
      setShowNewWoModal(false);
      fetchBoardData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create work order.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleExport = () => {
    const rows = [
      ['Column', 'Identifier', 'Details', 'Status'],
      ...boardData.dueSoon.map((a) => ['Due soon', a.asset_code, a.model_number || 'Sensor', a.calibration_status]),
      ...boardData.workOrdersOpen.map((w) => ['Work order open', w.work_order_code, `Asset ID ${w.asset_id}`, w.status]),
      ...boardData.inCalibration.map((c) => ['In calibration', c.calibration_code || c.work_order_code, 'Lab execution', 'In progress']),
      ...boardData.failedAction.map((f) => ['Failed, action needed', f.capa_code || f.asset_code, 'Impact assessment needed', 'Action Required']),
      ...boardData.certified.map((c) => ['Certified', c.certificate_code, `Valid until ${c.valid_until ? c.valid_until.slice(0, 10) : 'Active'}`, 'Verified'])
    ];
    const csvContent = "data:text/csv;charset=utf-8," + rows.map((e) => e.map((x) => `"${x}"`).join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `calibraflow_workflow_board_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-3">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Synchronizing calibration lifecycle workflow board...
        </p>
      </div>
    );
  }

  return (
    <>
      {/* Breadcrumb */}
      <div className="bc">Home / Workflow board</div>

      {/* Header */}
      <header className="hd">
        <div>
          <h1>Workflow board</h1>
          <p>Every move is written to the immutable audit trail</p>
        </div>
        <div className="tb">
          {canCreateWo && (
            <button className="btn" onClick={() => setShowNewWoModal(true)}>
              <Plus size={18} />
              <span>New work order</span>
            </button>
          )}
          <button className="btn o" onClick={handleExport}>
            <Download size={18} />
            <span>Export</span>
          </button>
        </div>
      </header>

      {/* 5-Column Workflow Lifecycle Board */}
      <section className="bd">
        {/* Column 1: Due Soon */}
        <div className="col o">
          <h2>
            Due soon <span>{boardData.dueSoon.length}</span>
          </h2>
          {boardData.dueSoon.length > 0 ? (
            boardData.dueSoon.map((item, idx) => (
              <div
                key={item.id || idx}
                className="it cursor-pointer hover:border-amber-300 transition-colors"
                onClick={() => navigate(`/instruments?search=${item.asset_code}`)}
              >
                <b>{item.asset_code}</b>
                <small>{item.model_number || 'Sensor asset'} · due {item.next_due_date ? new Date(item.next_due_date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : 'Soon'}</small>
                <span className="tg y">Due soon</span>
              </div>
            ))
          ) : (
            <div className="it text-slate-400">
              <small>No instruments currently due soon</small>
            </div>
          )}
        </div>

        {/* Column 2: Work Order Open */}
        <div className="col">
          <h2>
            Work order open <span>{boardData.workOrdersOpen.length}</span>
          </h2>
          {boardData.workOrdersOpen.length > 0 ? (
            boardData.workOrdersOpen.map((wo, idx) => (
              <div
                key={wo.id || idx}
                className="it cursor-pointer hover:border-blue-300 transition-colors"
                onClick={() => navigate('/work-orders')}
              >
                <b>{wo.work_order_code}</b>
                <small>{wo.asset_code || `Asset #${wo.asset_id}`} · downtime {Math.max(1, Math.round(Number(wo.planned_downtime_minutes || wo.downtime_minutes || 120) / 60))} h</small>
                <span className="tg g">{wo.status}</span>
              </div>
            ))
          ) : (
            <div className="it text-slate-400">
              <small>No open work orders</small>
            </div>
          )}
        </div>

        {/* Column 3: In Calibration */}
        <div className="col">
          <h2>
            In calibration <span>{boardData.inCalibration.length}</span>
          </h2>
          {boardData.inCalibration.length > 0 ? (
            boardData.inCalibration.map((cal, idx) => (
              <div
                key={cal.id || idx}
                className="it cursor-pointer hover:border-blue-400 transition-colors"
                onClick={() => navigate('/plans-events')}
              >
                <b>{cal.calibration_code || cal.work_order_code}</b>
                <small>Metrology vendor lab calibration</small>
                <span className="tg b">In progress</span>
              </div>
            ))
          ) : (
            <div className="it text-slate-400">
              <small>No calibrations in progress</small>
            </div>
          )}
        </div>

        {/* Column 4: Failed, Action Needed */}
        <div className="col f">
          <h2>
            Failed, action needed <span>{boardData.failedAction.length}</span>
          </h2>
          {boardData.failedAction.length > 0 ? (
            boardData.failedAction.map((fail, idx) => (
              <div
                key={fail.id || idx}
                className="it cursor-pointer hover:border-red-400 transition-colors"
                onClick={() => navigate('/alerts')}
              >
                <b>{fail.capa_code || fail.asset_code}</b>
                <small>Impact assessment & containment required</small>
                <span className="tg">Blocked</span>
              </div>
            ))
          ) : (
            <div className="it text-slate-400">
              <small>No failed actions pending</small>
            </div>
          )}
        </div>

        {/* Column 5: Certified */}
        <div className="col">
          <h2>
            Certified <span>{boardData.certified.length}</span>
          </h2>
          {boardData.certified.length > 0 ? (
            boardData.certified.map((cert, idx) => (
              <div
                key={cert.id || idx}
                className="it cursor-pointer hover:border-emerald-300 transition-colors"
                onClick={() => navigate('/certificates')}
              >
                <b>{cert.certificate_code}</b>
                <small>Valid until {cert.valid_until ? new Date(cert.valid_until).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Next Cycle'}</small>
                <span className="tg g">Valid</span>
              </div>
            ))
          ) : (
            <div className="it text-slate-400">
              <small>No verified certificates</small>
            </div>
          )}
        </div>
      </section>

      {/* Modal: New Work Order */}
      {showNewWoModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h2 className="text-base font-bold text-slate-900">Create Calibration Work Order</h2>
              <button
                onClick={() => setShowNewWoModal(false)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateWorkOrder} className="space-y-4 pt-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Target Instrument *</label>
                <select
                  className="fi w-full"
                  value={newWoForm.asset_id}
                  onChange={(e) => setNewWoForm({ ...newWoForm, asset_id: e.target.value })}
                  required
                >
                  <option value="">Select an instrument asset...</option>
                  {assetsList.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.asset_code} — {a.model_number || 'Sensor'} ({a.calibration_status})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Work Order Type</label>
                  <select
                    className="fi w-full"
                    value={newWoForm.work_order_type}
                    onChange={(e) => setNewWoForm({ ...newWoForm, work_order_type: e.target.value })}
                  >
                    <option value="CALIBRATION">Calibration</option>
                    <option value="CORRECTIVE_ACTION">Corrective Action (CAPA)</option>
                    <option value="PREVENTIVE_MAINTENANCE">Preventive Maintenance</option>
                    <option value="VERIFICATION">Verification</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
                  <select
                    className="fi w-full"
                    value={newWoForm.priority}
                    onChange={(e) => setNewWoForm({ ...newWoForm, priority: e.target.value })}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Planned Downtime (min)</label>
                  <input
                    type="number"
                    className="fi w-full"
                    value={newWoForm.planned_downtime_minutes}
                    onChange={(e) => setNewWoForm({ ...newWoForm, planned_downtime_minutes: e.target.value })}
                    min="10"
                    step="10"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Scheduled Start</label>
                  <input
                    type="datetime-local"
                    className="fi w-full"
                    value={newWoForm.scheduled_start}
                    onChange={(e) => setNewWoForm({ ...newWoForm, scheduled_start: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Description / Notes</label>
                <textarea
                  className="fi w-full h-20 py-2 resize-none"
                  value={newWoForm.description}
                  onChange={(e) => setNewWoForm({ ...newWoForm, description: e.target.value })}
                ></textarea>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  className="btn o"
                  onClick={() => setShowNewWoModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn"
                >
                  {submitting ? 'Creating...' : 'Create Work Order'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default WorkflowBoardPage;
