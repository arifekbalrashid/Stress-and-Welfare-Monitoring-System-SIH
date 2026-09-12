import { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import { Upload, CheckCircle, AlertCircle, FileSpreadsheet, Keyboard, Download, Activity } from 'lucide-react';

const TABS = [
  { id: 'file', label: 'File Import', icon: FileSpreadsheet },
  { id: 'manual', label: 'Manual Entry', icon: Keyboard },
];

const EMPTY_FORM = {
  service_id: '',
  period_start: '',
  period_end: '',
  duty_hours: '',
  night_shifts: '',
  consecutive_duty_days: '',
  rest_hours: '',
  deployment_days: '',
  leave_gap_days: '',
};

export default function AdminImport() {
  const [tab, setTab] = useState('file');

  // File import state
  const [file, setFile] = useState(null);
  const [fileResult, setFileResult] = useState(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileError, setFileError] = useState('');

  // Manual entry state
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [manualResult, setManualResult] = useState(null);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualError, setManualError] = useState('');

  const [importStatus, setImportStatus] = useState(undefined);

  // Personnel list for autocomplete
  const [personnel, setPersonnel] = useState([]);
  useEffect(() => {
    adminAPI.getPersonnel({ page_size: 100 })
      .then(r => setPersonnel(r.data.data?.items || []))
      .catch(() => {});
      
    adminAPI.getImportStatus()
      .then(r => setImportStatus(r.data.data?.latest_import_date || null))
      .catch(() => setImportStatus(null));
  }, []);

  const daysSinceImport = importStatus 
    ? Math.floor((new Date() - new Date(importStatus)) / (1000 * 60 * 60 * 24)) 
    : null;

  const showReminder = daysSinceImport !== null && daysSinceImport > 14;

  // ---- File Import ----
  const handleUpload = async () => {
    if (!file) return;
    setFileLoading(true);
    setFileError('');
    setFileResult(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await adminAPI.importData(formData);
      setFileResult(res.data.data);
      setImportStatus(new Date().toISOString()); // refresh status
    } catch (err) {
      setFileError(err.response?.data?.detail || 'Import failed.');
    } finally {
      setFileLoading(false);
    }
  };

  // ---- Manual Entry ----
  const handleFormChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!form.service_id || !form.period_start || !form.period_end) return;

    setManualLoading(true);
    setManualError('');
    setManualResult(null);

    // Convert empty strings to null for numeric fields
    const payload = { ...form };
    ['duty_hours', 'rest_hours'].forEach(k => {
      payload[k] = payload[k] ? parseFloat(payload[k]) : null;
    });
    ['night_shifts', 'consecutive_duty_days', 'deployment_days', 'leave_gap_days'].forEach(k => {
      payload[k] = payload[k] ? parseInt(payload[k]) : null;
    });

    try {
      const res = await adminAPI.addOperationalData(payload);
      setManualResult(res.data);
      setForm({ ...EMPTY_FORM });
      setImportStatus(new Date().toISOString()); // refresh status
    } catch (err) {
      setManualError(err.response?.data?.detail || 'Could not save record.');
    } finally {
      setManualLoading(false);
    }
  };

  const downloadTemplate = () => {
    const headers = 'service_id,period_start,period_end,duty_hours,night_shifts,consecutive_duty_days,rest_hours,deployment_days,leave_gap_days,training_hours';
    const sample = 'p1024,2026-09-01,2026-09-30,48,6,12,6.5,15,30,4';
    const blob = new Blob([headers + '\n' + sample + '\n'], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'operational_data_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="page-header"><h1 className="page-title">Import Operational Data</h1></div>

      {showReminder && (
        <div className="card flex items-start gap-3 bg-amber-50 border-amber-200 mb-6">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-800">Biweekly Data Import Reminder</p>
            <p className="text-xs text-amber-700 mt-1">
              It has been {daysSinceImport} days since the last operational data update. Please import the latest data to keep risk assessments accurate.
            </p>
          </div>
        </div>
      )}
      
      {importStatus === null && (
        <div className="card flex items-start gap-3 bg-blue-50 border-blue-200 mb-6">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800">No Data Imported Yet</p>
            <p className="text-xs text-blue-700 mt-1">
              Please upload your first operational data file to get started with risk assessments.
            </p>
          </div>
        </div>
      )}

      {/* Tab Switcher */}
      <div className="filter-tabs mb-6">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); setFileError(''); setManualError(''); }}
            className={`filter-tab flex items-center gap-2 ${tab === t.id ? 'filter-tab-active' : ''}`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ================= FILE IMPORT TAB ================= */}
      {tab === 'file' && (
        <div>
          <div className="card mb-4">
            <div className="border-2 border-dashed border-surface-200 bg-surface-50 rounded-lg p-8 text-center transition-colors hover:border-accent-400">
              <Upload className="w-8 h-8 text-surface-300 mx-auto mb-3" />
              <input
                type="file" accept=".csv,.xlsx,.xls" id="file-upload"
                onChange={e => { setFile(e.target.files[0]); setFileResult(null); setFileError(''); }}
                className="hidden"
              />
              <label htmlFor="file-upload" className="btn btn-secondary cursor-pointer inline-flex">
                {file ? file.name : 'Choose File'}
              </label>
              <p className="text-xs text-surface-400 mt-3">
                Supported formats: <strong>.csv</strong> and <strong>.xlsx</strong>
              </p>
              <p className="text-[0.65rem] text-surface-400 mt-1 max-w-sm mx-auto">
                Required columns: service_id, period_start, period_end, duty_hours, night_shifts, consecutive_duty_days, rest_hours, deployment_days, leave_gap_days
              </p>
            </div>

            <div className="flex gap-2 mt-4">
              <button onClick={handleUpload} disabled={!file || fileLoading} className="btn btn-primary flex-1">
                {fileLoading ? 'Importing…' : 'Import Data'}
              </button>
              <button onClick={downloadTemplate} className="btn btn-outline flex items-center gap-1.5">
                <Download className="w-3.5 h-3.5" /> Template
              </button>
            </div>
          </div>

          {fileError && (
            <div className="card flex items-start gap-3 bg-red-50 border-red-200 mb-4">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-600">{fileError}</p>
            </div>
          )}

          {fileResult && (
            <div className="card">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-surface-800">{fileResult.imported} records imported</span>
              </div>
              {fileResult.errors?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-surface-500 mb-1">Errors ({fileResult.errors.length}):</p>
                  <div className="bg-surface-50 rounded-lg p-3 max-h-40 overflow-y-auto border border-surface-200">
                    {fileResult.errors.map((e, i) => (
                      <p key={i} className="text-xs text-red-500">{e}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ================= MANUAL ENTRY TAB ================= */}
      {tab === 'manual' && (
        <div>
          <form onSubmit={handleManualSubmit} className="card space-y-6">

            {/* Personnel + Period */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="input-label">Service ID *</label>
                <select
                  name="service_id" value={form.service_id} onChange={handleFormChange}
                  className="input" required
                >
                  <option value="">Select personnel</option>
                  {personnel.map(p => (
                    <option key={p.service_id} value={p.service_id}>
                      {p.service_id} — {p.first_name} {p.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">Period Start *</label>
                <input type="date" name="period_start" value={form.period_start} onChange={handleFormChange} className="input" required />
              </div>
              <div>
                <label className="input-label">Period End *</label>
                <input type="date" name="period_end" value={form.period_end} onChange={handleFormChange} className="input" required />
              </div>
            </div>

            {/* Metric Fields */}
            <div>
              <div className="section-label">
                <div className="section-label-icon"><Activity /></div>
                Operational Metrics
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="input-label">Duty Hours <span className="text-surface-400 font-normal">(hrs/wk)</span></label>
                  <input type="number" step="0.1" name="duty_hours" value={form.duty_hours} onChange={handleFormChange} className="input" placeholder="e.g. 48" />
                </div>
                <div>
                  <label className="input-label">Night Shifts <span className="text-surface-400 font-normal">(/mo)</span></label>
                  <input type="number" name="night_shifts" value={form.night_shifts} onChange={handleFormChange} className="input" placeholder="e.g. 6" />
                </div>
                <div>
                  <label className="input-label">Consecutive Duty Days</label>
                  <input type="number" name="consecutive_duty_days" value={form.consecutive_duty_days} onChange={handleFormChange} className="input" placeholder="e.g. 12" />
                </div>
                <div>
                  <label className="input-label">Rest Hours <span className="text-surface-400 font-normal">(hrs/day)</span></label>
                  <input type="number" step="0.1" name="rest_hours" value={form.rest_hours} onChange={handleFormChange} className="input" placeholder="e.g. 6.5" />
                </div>
                <div>
                  <label className="input-label">Deployment Days</label>
                  <input type="number" name="deployment_days" value={form.deployment_days} onChange={handleFormChange} className="input" placeholder="e.g. 15" />
                </div>
                <div>
                  <label className="input-label">Leave Gap <span className="text-surface-400 font-normal">(days)</span></label>
                  <input type="number" name="leave_gap_days" value={form.leave_gap_days} onChange={handleFormChange} className="input" placeholder="e.g. 30" />
                </div>
              </div>
            </div>

            {manualError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-600">{manualError}</p>
              </div>
            )}

            {manualResult && (
              <div className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-green-700">
                  Record saved for <strong>{manualResult.data?.personnel_name}</strong> (ID: {manualResult.data?.id})
                </p>
              </div>
            )}

            <div className="pt-2">
              <button type="submit" disabled={manualLoading || !form.service_id || !form.period_start || !form.period_end} className="btn btn-primary w-full">
                {manualLoading ? 'Saving…' : 'Save Record'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
