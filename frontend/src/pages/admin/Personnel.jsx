import { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import { Plus, Building2, UserPlus, Users } from 'lucide-react';

export default function AdminPersonnel() {
  const [personnel, setPersonnel] = useState([]);
  const [units, setUnits] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Unit form
  const [showUnitForm, setShowUnitForm] = useState(false);
  const [unitForm, setUnitForm] = useState({ name: '', location: '', type: '' });

  // Personnel form
  const [showPersonnelForm, setShowPersonnelForm] = useState(false);
  const [pForm, setPForm] = useState({
    user_id: '', unit_id: '', service_id: '', first_name: '', last_name: '', rank: '', date_of_joining: '', contact_number: '',
  });
  const [pError, setPError] = useState('');
  const [pSuccess, setPSuccess] = useState('');

  const fetchAll = () => {
    Promise.all([
      adminAPI.getPersonnel({ page_size: 100 }).then(r => setPersonnel(r.data.data?.items || [])),
      adminAPI.getUnits().then(r => setUnits(r.data.data || [])),
      adminAPI.getUsers({ page_size: 100 }).then(r => setUsers(r.data.data?.items || [])),
    ]).finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  const handleCreateUnit = async (e) => {
    e.preventDefault();
    if (!unitForm.name) return;
    await adminAPI.createUnit(unitForm);
    setShowUnitForm(false);
    setUnitForm({ name: '', location: '', type: '' });
    fetchAll();
  };

  const handleCreatePersonnel = async (e) => {
    e.preventDefault();
    setPError('');
    setPSuccess('');
    if (!pForm.unit_id || !pForm.service_id || !pForm.first_name || !pForm.last_name) {
      setPError('Please fill all required fields.');
      return;
    }
    const payload = {
      ...pForm,
      user_id: pForm.user_id ? parseInt(pForm.user_id) : undefined,
      unit_id: parseInt(pForm.unit_id),
    };
    try {
      await adminAPI.createPersonnel(payload);
      setPSuccess(`Personnel ${pForm.first_name} ${pForm.last_name} added to unit.`);
      setPForm({ user_id: '', unit_id: '', service_id: '', first_name: '', last_name: '', rank: '', date_of_joining: '', contact_number: '' });
      fetchAll();
    } catch (err) {
      setPError(err.response?.data?.detail || 'Failed to create personnel.');
    }
  };

  if (loading) return (
    <div>
      <div className="page-header"><h1 className="page-title">Personnel & Units</h1></div>
      <div className="skeleton h-48 w-full rounded-[14px]" />
    </div>
  );

  return (
    <div>
      <div className="page-header"><h1 className="page-title">Personnel & Units</h1></div>

      {/* Units */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="section-label mb-0">
            <div className="section-label-icon"><Building2 /></div>
            Units ({units.length})
          </div>
          <button className="btn btn-sm btn-primary" onClick={() => setShowUnitForm(!showUnitForm)}>
            <Plus className="w-3.5 h-3.5" /> Add Unit
          </button>
        </div>

        {showUnitForm && (
          <form onSubmit={handleCreateUnit} className="p-3 bg-surface-50 border border-surface-100 rounded-lg mb-4 flex gap-2 items-end">
            <div className="flex-1">
              <label className="input-label">Name</label>
              <input className="input" value={unitForm.name} onChange={e => setUnitForm(f => ({ ...f, name: e.target.value }))} required />
            </div>
            <div className="flex-1">
              <label className="input-label">Location</label>
              <input className="input" value={unitForm.location} onChange={e => setUnitForm(f => ({ ...f, location: e.target.value }))} />
            </div>
            <div className="flex-1">
              <label className="input-label">Type</label>
              <select className="input" value={unitForm.type} onChange={e => setUnitForm(f => ({ ...f, type: e.target.value }))}>
                <option value="">Select</option>
                <option value="battalion">Battalion</option>
                <option value="company">Company</option>
                <option value="station">Station</option>
                <option value="post">Post</option>
              </select>
            </div>
            <button type="submit" className="btn btn-primary btn-sm">Create</button>
          </form>
        )}

        <div className="space-y-1.5">
          {units.map(u => (
            <div key={u.id} className="flex items-center justify-between p-2.5 bg-surface-50 border border-surface-100 rounded-lg">
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-accent-500" />
                <span className="text-sm font-medium text-surface-800">{u.name}</span>
                {u.location && <span className="text-xs text-surface-400">— {u.location}</span>}
                {u.type && <span className="badge badge-neutral text-[0.6rem]">{u.type}</span>}
              </div>
              <span className="text-xs font-medium text-surface-500">{u.personnel_count} personnel</span>
            </div>
          ))}
        </div>
      </div>

      {/* Add Personnel Form */}
      <div className="card mb-4">
        <div className="flex items-center justify-between mb-4">
          <div className="section-label mb-0">
            <div className="section-label-icon"><Users /></div>
            Personnel ({personnel.length})
          </div>
          <button className="btn btn-sm btn-primary" onClick={() => { setShowPersonnelForm(!showPersonnelForm); setPError(''); setPSuccess(''); }}>
            <UserPlus className="w-3.5 h-3.5" /> Add Personnel
          </button>
        </div>

        {showPersonnelForm && (
          <form onSubmit={handleCreatePersonnel} className="p-4 bg-surface-50 border border-surface-100 rounded-lg mb-6 space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div>
                <label className="input-label">Service ID *</label>
                <input className="input" placeholder="e.g. p1034" value={pForm.service_id} onChange={e => setPForm(f => ({ ...f, service_id: e.target.value }))} required />
              </div>
              <div>
                <label className="input-label">First Name *</label>
                <input className="input" value={pForm.first_name} onChange={e => setPForm(f => ({ ...f, first_name: e.target.value }))} required />
              </div>
              <div>
                <label className="input-label">Last Name *</label>
                <input className="input" value={pForm.last_name} onChange={e => setPForm(f => ({ ...f, last_name: e.target.value }))} required />
              </div>
              <div>
                <label className="input-label flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-accent-600" /> Assigned Unit *
                </label>
                <select className="input" value={pForm.unit_id} onChange={e => setPForm(f => ({ ...f, unit_id: e.target.value }))} required>
                  <option value="">Select unit</option>
                  {units.map(u => (
                    <option key={u.id} value={u.id}>{u.name} — {u.location || 'N/A'}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">Rank</label>
                <select className="input" value={pForm.rank} onChange={e => setPForm(f => ({ ...f, rank: e.target.value }))}>
                  <option value="">Select rank</option>
                  <option value="Constable">Constable</option>
                  <option value="Head Constable">Head Constable</option>
                  <option value="ASI">ASI</option>
                  <option value="SI">SI</option>
                  <option value="Inspector">Inspector</option>
                  <option value="DySP">DySP</option>
                  <option value="Commandant">Commandant</option>
                </select>
              </div>
              <div>
                <label className="input-label">Linked User Account</label>
                <select className="input" value={pForm.user_id} onChange={e => setPForm(f => ({ ...f, user_id: e.target.value }))}>
                  <option value="">Select user account</option>
                  {users.filter(u => u.role === 'personnel').map(u => (
                    <option key={u.id} value={u.id}>{u.username} ({u.email})</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="input-label">Date of Joining</label>
                <input type="date" className="input" value={pForm.date_of_joining} onChange={e => setPForm(f => ({ ...f, date_of_joining: e.target.value }))} />
              </div>
              <div>
                <label className="input-label">Contact Number</label>
                <input className="input" placeholder="+91-XXXXXXXXXX" value={pForm.contact_number} onChange={e => setPForm(f => ({ ...f, contact_number: e.target.value }))} />
              </div>
            </div>

            {pError && <p className="text-sm text-red-500">{pError}</p>}
            {pSuccess && <p className="text-sm text-green-600">{pSuccess}</p>}

            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary btn-sm">Add Personnel</button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowPersonnelForm(false)}>Cancel</button>
            </div>
          </form>
        )}

        {/* Personnel table */}
        <div className="table-container">
          <table className="table">
            <thead>
              <tr><th>Service ID</th><th>Name</th><th>Rank</th><th>Unit</th></tr>
            </thead>
            <tbody>
              {personnel.map(p => (
                <tr key={p.id}>
                  <td className="font-mono text-xs">{p.service_id}</td>
                  <td className="font-medium text-surface-800">{p.first_name} {p.last_name}</td>
                  <td>{p.rank || '—'}</td>
                  <td>
                    {p.unit_name ? (
                      <span className="flex items-center gap-1 text-sm">
                        <Building2 className="w-3 h-3 text-accent-500" />
                        {p.unit_name}
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
