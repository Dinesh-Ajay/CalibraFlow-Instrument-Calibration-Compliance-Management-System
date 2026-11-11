import React, { useState, useEffect } from 'react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import {
  Cpu,
  Plus,
  Search,
  Filter,
  Eye,
  Edit2,
  Calendar,
  MapPin,
  Tag,
  CheckCircle2,
  AlertTriangle,
  History,
  X,
  Clock,
  ArrowRight
} from 'lucide-react';

const AssetsPage = () => {
  const { hasRole } = useAuth();
  const [assets, setAssets] = useState([]);
  const [instrumentTypes, setInstrumentTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [lineFilter, setLineFilter] = useState('');

  // Modals
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [assetHistory, setAssetHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Form states
  const [formData, setFormData] = useState({
    asset_name: '',
    instrument_type_id: 1,
    serial_number: '',
    manufacturer: 'Yokogawa',
    model_number: 'EJA530E',
    plant_location: 'Building A - Sector 1',
    production_line: 'Line 1 - Bottling',
    calibration_interval_days: 90,
    custom_tolerance: 2.0,
    requires_calibration: true,
    requires_certificate: true,
  });

  const [editFormData, setEditFormData] = useState({
    asset_name: '',
    plant_location: '',
    production_line: '',
    calibration_interval_days: 90,
    operational_status: 'ACTIVE'
  });

  const fetchAssets = async () => {
    try {
      setLoading(true);
      const params = {};
      if (search) params.search = search;
      if (statusFilter) params.calibration_status = statusFilter;
      if (lineFilter) params.production_line = lineFilter;

      const res = await api.get('/assets', { params });
      setAssets(res.data);
    } catch (err) {
      console.error('Failed to fetch assets:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchInstrumentTypes = async () => {
    try {
      const res = await api.get('/instrument-types');
      setInstrumentTypes(res.data);
    } catch (err) {
      console.error('Failed to fetch instrument types:', err);
    }
  };

  useEffect(() => {
    fetchInstrumentTypes();
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [search, statusFilter, lineFilter]);

  const handleOpenAdd = () => {
    setFormData({
      asset_name: '',
      instrument_type_id: instrumentTypes[0]?.id || 1,
      serial_number: `SN-${Math.floor(100000 + Math.random() * 900000)}`,
      manufacturer: 'Yokogawa',
      model_number: 'EJA530E',
      plant_location: 'Building A - Sector 1',
      production_line: 'Line 1 - Bottling',
      calibration_interval_days: 90,
      custom_tolerance: 2.0,
      requires_calibration: true,
      requires_certificate: true,
    });
    setIsAddModalOpen(true);
  };

  const handleCreateAsset = async (e) => {
    e.preventDefault();
    try {
      await api.post('/assets', formData);
      setIsAddModalOpen(false);
      fetchAssets();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to register asset');
    }
  };

  const handleOpenEdit = (asset) => {
    setSelectedAsset(asset);
    setEditFormData({
      asset_name: asset.asset_name,
      plant_location: asset.plant_location,
      production_line: asset.production_line,
      calibration_interval_days: asset.calibration_interval_days,
      operational_status: asset.operational_status
    });
    setIsEditModalOpen(true);
  };

  const handleUpdateAsset = async (e) => {
    e.preventDefault();
    try {
      await api.put(`/assets/${selectedAsset.id}`, editFormData);
      setIsEditModalOpen(false);
      fetchAssets();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update asset');
    }
  };

  const handleViewHistory = async (asset) => {
    setSelectedAsset(asset);
    setIsHistoryDrawerOpen(true);
    setHistoryLoading(true);
    try {
      const res = await api.get(`/assets/${asset.id}/history`);
      setAssetHistory(res.data);
    } catch (err) {
      console.error('Failed to load asset history:', err);
    } finally {
      setHistoryLoading(false);
    }
  };

  const productionLines = [
    'Line 1 - Bottling',
    'Line 2 - Packaging',
    'Line 3 - Synthesis',
    'Line 4 - Quality Lab',
    'Line 5 - Assembly'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Instrument Asset Inventory</h1>
          <p className="text-xs text-slate-500">Manage plant measurement assets, calibration schedules, and tolerance standards.</p>
        </div>
        {hasRole(['Maintenance Engineer', 'Administrator']) && (
          <button
            onClick={handleOpenAdd}
            className="flex items-center space-x-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Register Instrument</span>
          </button>
        )}
      </div>

      {/* Search & Filters */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search code, name, serial..."
            className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-2.5 py-2 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Calibration Statuses</option>
            <option value="COMPLIANT">COMPLIANT</option>
            <option value="UPCOMING">UPCOMING</option>
            <option value="OVERDUE">OVERDUE</option>
            <option value="FAILED">FAILED</option>
            <option value="PENDING_CERTIFICATE">PENDING_CERTIFICATE</option>
          </select>

          <select
            value={lineFilter}
            onChange={(e) => setLineFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg px-2.5 py-2 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All Production Lines</option>
            {productionLines.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Asset Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Asset Code</th>
                <th className="py-3 px-4">Instrument Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Location / Line</th>
                <th className="py-3 px-4">Interval</th>
                <th className="py-3 px-4">Last Cal</th>
                <th className="py-3 px-4">Next Due Date</th>
                <th className="py-3 px-4">Cal Status</th>
                <th className="py-3 px-4">Ops Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {assets.map((asset) => (
                <tr key={asset.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-blue-600">{asset.asset_code}</td>
                  <td className="py-3 px-4">
                    <p className="font-semibold text-slate-900">{asset.asset_name}</p>
                    <p className="text-[10px] text-slate-400 font-mono">SN: {asset.serial_number} • {asset.manufacturer}</p>
                  </td>
                  <td className="py-3 px-4 text-slate-700 font-medium">
                    {asset.instrument_type_name || 'Standard'}
                  </td>
                  <td className="py-3 px-4">
                    <p className="text-slate-800 font-medium">{asset.production_line}</p>
                    <p className="text-[10px] text-slate-400">{asset.plant_location}</p>
                  </td>
                  <td className="py-3 px-4 text-slate-600">{asset.calibration_interval_days} d</td>
                  <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                    {asset.last_calibration_date ? asset.last_calibration_date.substring(0, 10) : 'None'}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap font-medium">
                    <span className={asset.calibration_status === 'OVERDUE' ? 'text-rose-600 font-bold' : 'text-slate-700'}>
                      {asset.next_due_date ? asset.next_due_date.substring(0, 10) : 'N/A'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={asset.calibration_status} />
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={asset.operational_status} size="xs" />
                  </td>
                  <td className="py-3 px-4 text-right whitespace-nowrap space-x-1">
                    <button
                      onClick={() => handleViewHistory(asset)}
                      title="View Telemetry & History"
                      className="p-1 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    {hasRole(['Maintenance Engineer', 'Administrator']) && (
                      <button
                        onClick={() => handleOpenEdit(asset)}
                        title="Edit Details"
                        className="p-1 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {assets.length === 0 && !loading && (
                <tr>
                  <td colSpan="10" className="py-8 text-center text-slate-400 text-xs">
                    No matching instruments found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Instrument Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Register New Measurement Instrument</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleCreateAsset} className="mt-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-700">Instrument Type</label>
                  <select
                    value={formData.instrument_type_id}
                    onChange={(e) => setFormData({ ...formData, instrument_type_id: parseInt(e.target.value) })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  >
                    {instrumentTypes.map((t) => (
                      <option key={t.id} value={t.id}>{t.type_name} ({t.measurement_unit})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Asset Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Steam Boiler Pressure Sensor"
                    value={formData.asset_name}
                    onChange={(e) => setFormData({ ...formData, asset_name: e.target.value })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block font-medium text-slate-700">Serial Number</label>
                  <input
                    type="text"
                    required
                    value={formData.serial_number}
                    onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Manufacturer</label>
                  <input
                    type="text"
                    required
                    value={formData.manufacturer}
                    onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Model Number</label>
                  <input
                    type="text"
                    required
                    value={formData.model_number}
                    onChange={(e) => setFormData({ ...formData, model_number: e.target.value })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-700">Production Line</label>
                  <select
                    value={formData.production_line}
                    onChange={(e) => setFormData({ ...formData, production_line: e.target.value })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  >
                    {productionLines.map((l) => (
                      <option key={l} value={l}>{l}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Plant Location</label>
                  <input
                    type="text"
                    required
                    value={formData.plant_location}
                    onChange={(e) => setFormData({ ...formData, plant_location: e.target.value })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-700">Calibration Interval (Days)</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={formData.calibration_interval_days}
                    onChange={(e) => setFormData({ ...formData, calibration_interval_days: parseInt(e.target.value) })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Acceptable Tolerance (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    required
                    value={formData.custom_tolerance}
                    onChange={(e) => setFormData({ ...formData, custom_tolerance: parseFloat(e.target.value) })}
                    className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-6 pt-2">
                <label className="flex items-center space-x-2 text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.requires_calibration}
                    onChange={(e) => setFormData({ ...formData, requires_calibration: e.target.checked })}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Requires Periodic Calibration</span>
                </label>
                <label className="flex items-center space-x-2 text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.requires_certificate}
                    onChange={(e) => setFormData({ ...formData, requires_certificate: e.target.checked })}
                    className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>Requires Quality Certificate</span>
                </label>
              </div>

              <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-3 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
                >
                  Save & Generate Asset ID
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Instrument Modal */}
      {isEditModalOpen && selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Update Asset: {selectedAsset.asset_code}</h3>
              <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleUpdateAsset} className="mt-4 space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-700">Asset Name</label>
                <input
                  type="text"
                  required
                  value={editFormData.asset_name}
                  onChange={(e) => setEditFormData({ ...editFormData, asset_name: e.target.value })}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                />
              </div>
              <div>
                <label className="block font-medium text-slate-700">Production Line</label>
                <select
                  value={editFormData.production_line}
                  onChange={(e) => setEditFormData({ ...editFormData, production_line: e.target.value })}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                >
                  {productionLines.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-medium text-slate-700">Plant Location</label>
                <input
                  type="text"
                  required
                  value={editFormData.plant_location}
                  onChange={(e) => setEditFormData({ ...editFormData, plant_location: e.target.value })}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                />
              </div>
              <div>
                <label className="block font-medium text-slate-700">Operational Status</label>
                <select
                  value={editFormData.operational_status}
                  onChange={(e) => setEditFormData({ ...editFormData, operational_status: e.target.value })}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                >
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="RESTRICTED">RESTRICTED</option>
                  <option value="MAINTENANCE">MAINTENANCE</option>
                  <option value="INACTIVE">INACTIVE</option>
                  <option value="RETIRED">RETIRED</option>
                </select>
              </div>
              <div>
                <label className="block font-medium text-slate-700">Calibration Interval (Days)</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={editFormData.calibration_interval_days}
                  onChange={(e) => setEditFormData({ ...editFormData, calibration_interval_days: parseInt(e.target.value) })}
                  className="mt-1 w-full border border-slate-300 rounded-lg p-2"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="px-3 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Asset History Slide-Out Drawer */}
      {isHistoryDrawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col">
            <div className="px-6 py-4 border-b border-slate-200 bg-slate-900 text-white flex justify-between items-center">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>{selectedAsset?.asset_code}</span>
                  <StatusBadge status={selectedAsset?.calibration_status} size="xs" />
                </h3>
                <p className="text-xs text-slate-300">{selectedAsset?.asset_name}</p>
              </div>
              <button onClick={() => setIsHistoryDrawerOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {historyLoading ? (
                <div className="flex justify-center py-12">
                  <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              ) : (
                <>
                  {/* Summary Details */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
                    <div>
                      <p className="text-[10px] text-slate-400 font-semibold uppercase">Line</p>
                      <p className="font-semibold text-slate-800">{selectedAsset?.production_line}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 font-semibold uppercase">Location</p>
                      <p className="font-semibold text-slate-800">{selectedAsset?.plant_location}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 font-semibold uppercase">Next Due</p>
                      <p className="font-semibold text-slate-800">{selectedAsset?.next_due_date?.substring(0, 10) || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-400 font-semibold uppercase">Ops State</p>
                      <p className="font-semibold text-slate-800">{selectedAsset?.operational_status}</p>
                    </div>
                  </div>

                  {/* Calibration Events Timeline */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <History className="w-4 h-4 text-blue-600" /> Calibration Events ({assetHistory?.calibration_events?.length || 0})
                    </h4>
                    <div className="border border-slate-200 rounded-lg overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-500 font-semibold">
                          <tr>
                            <th className="py-2 px-3">Code</th>
                            <th className="py-2 px-3">Date</th>
                            <th className="py-2 px-3">Error / Tol</th>
                            <th className="py-2 px-3">Result</th>
                            <th className="py-2 px-3">Tech</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {assetHistory?.calibration_events?.map((e) => (
                            <tr key={e.id}>
                              <td className="py-2 px-3 font-mono font-medium">{e.calibration_code}</td>
                              <td className="py-2 px-3 text-slate-600">{e.calibration_date.substring(0, 10)}</td>
                              <td className="py-2 px-3 text-slate-700">{e.measurement_error}% / {e.tolerance}%</td>
                              <td className="py-2 px-3"><StatusBadge status={e.result} size="xs" /></td>
                              <td className="py-2 px-3 text-slate-500">{e.performed_by}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Certificates */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">Quality Certificates ({assetHistory?.certificates?.length || 0})</h4>
                    <div className="border border-slate-200 rounded-lg overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-500 font-semibold">
                          <tr>
                            <th className="py-2 px-3">Certificate Code</th>
                            <th className="py-2 px-3">Number</th>
                            <th className="py-2 px-3">Expiry Date</th>
                            <th className="py-2 px-3">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {assetHistory?.certificates?.map((c) => (
                            <tr key={c.id}>
                              <td className="py-2 px-3 font-mono">{c.certificate_code}</td>
                              <td className="py-2 px-3 text-slate-700">{c.certificate_number}</td>
                              <td className="py-2 px-3 text-slate-600">{c.expiry_date.substring(0, 10)}</td>
                              <td className="py-2 px-3"><StatusBadge status={c.verification_status} size="xs" /></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Recent Production Uses */}
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">Production Usage History (Last 50)</h4>
                    <div className="border border-slate-200 rounded-lg overflow-hidden max-h-56 overflow-y-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 text-slate-500 font-semibold sticky top-0">
                          <tr>
                            <th className="py-2 px-3">Usage Timestamp</th>
                            <th className="py-2 px-3">Line</th>
                            <th className="py-2 px-3">Decision</th>
                            <th className="py-2 px-3">Reason</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {assetHistory?.production_uses?.map((u) => (
                            <tr key={u.id}>
                              <td className="py-2 px-3 text-slate-600 whitespace-nowrap">{u.usage_timestamp.substring(0, 16).replace('T', ' ')}</td>
                              <td className="py-2 px-3 text-slate-800">{u.production_line}</td>
                              <td className="py-2 px-3"><StatusBadge status={u.validation_decision} size="xs" /></td>
                              <td className="py-2 px-3 text-slate-500 truncate max-w-xs">{u.decision_reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetsPage;
