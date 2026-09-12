import { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import { capitalize } from '../../utils/formatters';
import { Plus, Building2, Pencil } from 'lucide-react';

const ROLES = ['personnel', 'welfare_officer', 'commander', 'admin'];
const UNIT_ROLES = ['welfare_officer', 'commander'];

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', password: '', role: '', assigned_unit_id: '' });
  const [error, setError] = useState('');

  // Inline edit state
  const [editingId, setEditingId] = useState(null);
  const [editUnit, setEditUnit] = useState('');

  const fetchAll = () => {
    Promise.all([
      adminAPI.getUsers({ page_size: 50 }).then(r => setUsers(r.data.data?.items || [])),
      adminAPI.getUnits().then(r => setUnits(r.data.data || [])),
    ]).finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    const payload = { ...form };
    if (payload.assigned_unit_id) {
      payload.assigned_unit_id = parseInt(payload.assigned_unit_id);
    } else {
      delete payload.assigned_unit_id;
    }
    try {
      await adminAPI.createUser(payload);
      setShowForm(false);
      setForm({ username: '', email: '', password: '', role: '', assigned_unit_id: '' });
      fetchAll();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user.');
    }
  };

  const toggleActive = async (user) => {
    await adminAPI.updateUser(user.id, { is_active: !user.is_active });
    fetchAll();
  };

  const handleUnitChange = async (userId, unitId) => {
    try {
      await adminAPI.updateUser(userId, {
        assigned_unit_id: unitId ? parseInt(unitId) : 0,
      });
      setEditingId(null);
      fetchAll();
    } catch (err) {
      console.error(err);
    }
  };

  const needsUnit = (role) => UNIT_ROLES.includes(role);

  if (loading) return (
    <div>
      <div className="page-header"><h1 className="page-title">User Management</h1></div>
      <div className="skeleton h-48 w-full" />
    </div>
  );

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <h1 className="page-title">User Management</h1>
          <button className="btn btn-primary btn-sm" onClick={() => setShowForm(!showForm)}>
            <Plus className="w-3.5 h-3.5" /> Add User
          </button>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card mb-4 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="input-label">Username</label>
              <input className="input" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required />
            </div>
            <div>
              <label className="input-label">Email</label>
              <input className="input" type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
            </div>
            <div>
              <label className="input-label">Password</label>
              <input className="input" type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required />
            </div>
            <div>
              <label className="input-label">Role</label>
              <select className="input" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value, assigned_unit_id: '' }))} required>
                <option value="">Select role</option>
                {ROLES.map(r => <option key={r} value={r}>{capitalize(r)}</option>)}
              </select>
            </div>
          </div>

          {/* Unit assignment — shown only for WO / Commander */}
          {needsUnit(form.role) && (
            <div>
              <label className="input-label flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-accent-600" />
                Assigned Unit
                <span className="text-xs text-surface-400 font-normal ml-1">
                  ({form.role === 'commander' ? 'This commander will oversee personnel in this unit' : 'This officer will handle welfare cases for this unit'})
                </span>
              </label>
              <select
                className="input"
                value={form.assigned_unit_id}
                onChange={e => setForm(f => ({ ...f, assigned_unit_id: e.target.value }))}
              >
                <option value="">No unit (sees all personnel)</option>
                {units.map(u => <option key={u.id} value={u.id}>{u.name} — {u.location || 'N/A'}</option>)}
              </select>
            </div>
          )}

          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" className="btn btn-primary btn-sm">Create</button>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="table-container">
        <table className="table">
          <thead>
            <tr><th>Username</th><th>Email</th><th>Role</th><th>Assigned Unit</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td className="font-medium text-surface-800">{u.username}</td>
                <td className="text-surface-500">{u.email}</td>
                <td><span className="badge badge-neutral">{capitalize(u.role)}</span></td>
                <td>
                  {needsUnit(u.role) ? (
                    editingId === u.id ? (
                      <select
                        className="input text-xs py-1"
                        value={editUnit}
                        onChange={e => handleUnitChange(u.id, e.target.value)}
                        onBlur={() => setEditingId(null)}
                        autoFocus
                      >
                        <option value="">No unit assigned</option>
                        {units.map(unit => <option key={unit.id} value={unit.id}>{unit.name}</option>)}
                      </select>
                    ) : (
                      <button
                        className="flex items-center gap-1 text-xs hover:text-accent-600 transition-colors group"
                        onClick={() => { setEditingId(u.id); setEditUnit(u.assigned_unit_id || ''); }}
                      >
                        {u.assigned_unit_name ? (
                          <span className="flex items-center gap-1">
                            <Building2 className="w-3 h-3 text-accent-500" />
                            {u.assigned_unit_name}
                          </span>
                        ) : (
                          <span className="text-surface-400 italic">Not assigned</span>
                        )}
                        <Pencil className="w-3 h-3 text-surface-300 group-hover:text-accent-500 ml-1" />
                      </button>
                    )
                  ) : (
                    <span className="text-xs text-surface-300">—</span>
                  )}
                </td>
                <td>
                  <span className={`badge ${u.is_active ? 'badge-low' : 'badge-high'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>
                  <button onClick={() => toggleActive(u)} className="btn btn-ghost btn-sm text-xs">
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
