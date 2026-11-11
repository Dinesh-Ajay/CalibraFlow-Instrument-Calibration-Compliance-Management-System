import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import {
  CalendarCheck,
  Plus,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Search,
  Filter,
  X,
  Calculator,
  Calendar
} from 'lucide-react';

const CalibrationPage = () => {
  const { hasRole, user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'events';

  const [activeTab, setActiveTab] = useState(initialTab);
  const [events, setEvents] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [overdue, setOverdue] = useState([]);
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  // Record Calibration Modal
  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false);
  const [selectedAssetId, setSelectedAssetId] = useState('');
  const [measuredValue, setMeasuredValue] = useState(100.0);
  const [referenceValue, setReferenceValue] = useState(100.0);
  const [tolerance, setTolerance] = useState(2.0);
  const [notes, setNotes] = useState('');
  const [performedBy, setPerformedBy] = useState(user?.full_name || 'Maintenance Tech');

  // Live error calculation
  const errorVal = referenceValue !== 0
    ? Math.abs((measuredValue - referenceValue) / referenceValue) * 100
    : Math.abs(measuredValue - referenceValue);
  const isPass = errorVal <= tolerance;

  const fetchData = async () => {
    try {
      setLoading(true);
      const [evRes, upRes, ovRes, asRes] = await Promise.all([
        api.get('/calibration/events'),
        api.get('/calibration/upcoming'),
        api.get('/calibration/overdue'),
        api.get('/assets')
      ]);
      setEvents(evRes.data);
      setUpcoming(upRes.data);
      setOverdue(ovRes.data);
      setAssets(asRes.data);
      if (asRes.data.length > 0 && !selectedAssetId) {
        setSelectedAssetId(asRes.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load calibration data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  const handleScanSchedules = async () => {
    try {
      setScanning(true);
      const res = await api.post('/calibration/scan-schedules');
      alert(`Schedule Scan Complete!\nScanned: ${res.data.total_scanned}\nOverdue Flagged: ${res.data.overdue_identified}\nUpcoming Flagged: ${res.data.upcoming_identified}\nWork Orders Created: ${res.data.work_orders_created}`);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  const handleRecordCalibration = async (e) => {
    e.preventDefault();
    try {
      await api.post('/calibration/events', {
        asset_id: parseInt(selectedAssetId),
        measured_value: parseFloat(measuredValue),
        reference_value: parseFloat(referenceValue),
        tolerance: parseFloat(tolerance),
        performed_by: performedBy,
        certificate_required: true,
        notes: notes
      });
      setIsRecordModalOpen(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record calibration');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Calibration & Schedule Management</h1>
          <p className="text-xs text-slate-500">Monitor upcoming and overdue calibration due dates, record verification events, and calculate measurement error.</p>
        </div>
        <div className="flex items-center space-x-2">
          {hasRole(['Maintenance Engineer', 'Production Planner', 'Administrator']) && (
            <button
              onClick={handleScanSchedules}
              disabled={scanning}
              className="flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-2xs transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${scanning ? 'animate-spin text-blue-600' : 'text-slate-500'}`} />
              <span>Scan & Update Due Dates</span>
            </button>
          )}

          {hasRole(['Maintenance Engineer', 'Administrator']) && (
            <button
              onClick={() => setIsRecordModalOpen(true)}
              className="flex items-center space-x-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Record Calibration</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-4">
          <button
            onClick={() => handleTabChange('events')}
            className={`py-2.5 px-3 border-b-2 font-medium text-xs flex items-center gap-1.5 ${
              activeTab === 'events'
                ? 'border-blue-600 text-blue-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <CalendarCheck className="w-4 h-4" />
            <span>Calibration History ({events.length})</span>
          </button>

          <button
            onClick={() => handleTabChange('upcoming')}
            className={`py-2.5 px-3 border-b-2 font-medium text-xs flex items-center gap-1.5 ${
              activeTab === 'upcoming'
                ? 'border-amber-500 text-amber-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Upcoming Due ({upcoming.length})</span>
          </button>

          <button
            onClick={() => handleTabChange('overdue')}
            className={`py-2.5 px-3 border-b-2 font-medium text-xs flex items-center gap-1.5 ${
              activeTab === 'overdue'
                ? 'border-rose-600 text-rose-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Overdue Instruments ({overdue.length})</span>
          </button>
        </nav>
      </div>

      {/* Tab 1: All Calibration Events */}
      {activeTab === 'events' && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Calibration Code</th>
                  <th className="py-3 px-4">Instrument Asset</th>
                  <th className="py-3 px-4">Calibration Date</th>
                  <th className="py-3 px-4">Measured</th>
                  <th className="py-3 px-4">Reference</th>
                  <th className="py-3 px-4">Error / Tolerance</th>
                  <th className="py-3 px-4">Result</th>
                  <th className="py-3 px-4">Calculated Next Due</th>
                  <th className="py-3 px-4">Technician</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-900">{ev.calibration_code}</td>
                    <td className="py-3 px-4">
                      <p className="font-semibold text-blue-600">{ev.asset_code}</p>
                      <p className="text-[10px] text-slate-400">{ev.asset_name}</p>
                    </td>
                    <td className="py-3 px-4 text-slate-600 whitespace-nowrap">{ev.calibration_date.substring(0, 10)}</td>
                    <td className="py-3 px-4 font-mono">{ev.measured_value}</td>
                    <td className="py-3 px-4 font-mono text-slate-500">{ev.reference_value}</td>
                    <td className="py-3 px-4">
                      <span className={`font-semibold ${ev.result === 'PASS' ? 'text-slate-700' : 'text-rose-600'}`}>
                        {ev.measurement_error}%
                      </span>
                      <span className="text-slate-400 text-[10px]"> / {ev.tolerance}%</span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={ev.result} />
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap font-medium text-slate-700">
                      {ev.calculated_next_due_date ? ev.calculated_next_due_date.substring(0, 10) : 'None'}
                    </td>
                    <td className="py-3 px-4 text-slate-600">{ev.performed_by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Upcoming */}
      {activeTab === 'upcoming' && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
          <div className="p-4 bg-amber-50/50 border-b border-amber-100 flex items-center justify-between">
            <p className="text-xs text-amber-800">
              Instruments due within the next 14 days. Work orders should be generated to schedule routine service.
            </p>
          </div>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Asset Code</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Production Line</th>
                <th className="py-3 px-4">Last Calibration</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {upcoming.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-mono font-bold text-blue-600">{u.asset_code}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{u.asset_name}</td>
                  <td className="py-3 px-4 text-slate-700">{u.production_line}</td>
                  <td className="py-3 px-4 text-slate-500">{u.last_calibration_date?.substring(0, 10) || 'None'}</td>
                  <td className="py-3 px-4 font-bold text-amber-700">{u.next_due_date?.substring(0, 10)}</td>
                  <td className="py-3 px-4"><StatusBadge status="UPCOMING" /></td>
                </tr>
              ))}
              {upcoming.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-slate-400">No instruments currently in upcoming due window.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Overdue */}
      {activeTab === 'overdue' && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
          <div className="p-4 bg-rose-50/60 border-b border-rose-100 flex items-center justify-between">
            <p className="text-xs text-rose-800 font-medium">
              Overdue instruments are strictly <strong>BLOCKED</strong> from production use unless an emergency extension is approved by a Quality Engineer.
            </p>
          </div>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Asset Code</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Production Line</th>
                <th className="py-3 px-4">Last Calibration</th>
                <th className="py-3 px-4">Overdue Since</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {overdue.map((o) => (
                <tr key={o.id} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-mono font-bold text-rose-600">{o.asset_code}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{o.asset_name}</td>
                  <td className="py-3 px-4 text-slate-700">{o.production_line}</td>
                  <td className="py-3 px-4 text-slate-500">{o.last_calibration_date?.substring(0, 10) || 'None'}</td>
                  <td className="py-3 px-4 font-bold text-rose-700">{o.next_due_date?.substring(0, 10)}</td>
                  <td className="py-3 px-4"><StatusBadge status="OVERDUE" /></td>
                </tr>
              ))}
              {overdue.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-slate-400">Zero overdue instruments! All plant assets compliant.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Record Calibration Modal */}
      {isRecordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Calculator className="w-5 h-5 text-blue-600" />
                <span>Execute & Record Calibration Event</span>
              </h3>
              <button onClick={() => setIsRecordModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleRecordCalibration} className="mt-4 space-y-4 text-xs">
              <div>
                <label className="block font-medium text-slate-700">Target Instrument Asset</label>
                <select
                  value={selectedAssetId}
                  onChange={(e) => setSelectedAssetId(e.target.value)}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2 font-medium"
                >
                  {assets.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.asset_code} - {a.asset_name} ({a.production_line})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-700">Reference Standard Value</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={referenceValue}
                    onChange={(e) => setReferenceValue(parseFloat(e.target.value) || 0)}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2 font-mono"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Measured Reading</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={measuredValue}
                    onChange={(e) => setMeasuredValue(parseFloat(e.target.value) || 0)}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700">Permitted Tolerance Limit (%)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  required
                  value={tolerance}
                  onChange={(e) => setTolerance(parseFloat(e.target.value) || 0)}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2 font-mono"
                />
              </div>

              {/* Real-time calculated measurement error and result badge */}
              <div className={`p-4 rounded-xl border flex items-center justify-between ${
                isPass ? 'bg-emerald-50/70 border-emerald-200' : 'bg-rose-50/70 border-rose-200'
              }`}>
                <div>
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Calculated Measurement Error</p>
                  <p className="text-xl font-bold font-mono text-slate-900 mt-0.5">
                    {errorVal.toFixed(2)}% <span className="text-xs font-normal text-slate-500">(Tolerance: {tolerance}%)</span>
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Derived Decision</p>
                  <StatusBadge status={isPass ? 'PASS' : 'FAIL'} size="lg" />
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700">Performed By (Technician / Metrologist)</label>
                <input
                  type="text"
                  required
                  value={performedBy}
                  onChange={(e) => setPerformedBy(e.target.value)}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700">Observations & Calibration Notes</label>
                <textarea
                  rows="2"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Environmental temp 21°C, calibrated using certified deadweight tester..."
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                ></textarea>
              </div>

              <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsRecordModalOpen(false)}
                  className="px-3 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
                >
                  Commit Immutable Calibration Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalibrationPage;
