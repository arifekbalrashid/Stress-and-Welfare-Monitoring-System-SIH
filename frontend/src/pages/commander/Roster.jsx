import { useState, useEffect } from 'react';
import { commanderAPI } from '../../services/api';
import { Users, ArrowUpDown, AlertTriangle } from 'lucide-react';

const METRIC_THRESHOLDS = {
  duty_hours: { warn: 50, label: 'Duty Hours', unit: 'hrs/wk' },
  night_shifts: { warn: 8, label: 'Night Shifts', unit: '/mo' },
  consecutive_duty_days: { warn: 12, label: 'Consec. Days', unit: 'days' },
  rest_hours: { warn: 5, warnBelow: true, label: 'Rest', unit: 'hrs/day' },
  leave_gap_days: { warn: 45, label: 'Leave Gap', unit: 'days' },
  deployment_days: { warn: 40, label: 'Deployment', unit: 'days' },
};

export default function Roster() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState('duty_hours');
  const [sortAsc, setSortAsc] = useState(false);

  useEffect(() => {
    commanderAPI.getRoster()
      .then(res => setData(res.data.data))
      .finally(() => setLoading(false));
  }, []);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  if (loading) return (
    <div>
      <div className="page-header"><h1 className="page-title">Unit Roster</h1></div>
      <div className="skeleton h-64 w-full" />
    </div>
  );

  if (!data) return null;

  const sorted = [...(data.items || [])].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    return sortAsc ? av - bv : bv - av;
  });

  const isWarning = (key, val) => {
    if (val == null) return false;
    const t = METRIC_THRESHOLDS[key];
    if (!t) return false;
    return t.warnBelow ? val < t.warn : val > t.warn;
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Unit Roster</h1>
        <p className="page-subtitle">{data.unit_name}</p>
      </div>

      <div className="card mb-3 text-xs text-surface-500 flex items-center gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
        <span>Highlighted values exceed recommended thresholds. This view shows operational data only — no wellness or risk data is displayed.</span>
      </div>

      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Personnel</th>
              {Object.entries(METRIC_THRESHOLDS).map(([key, cfg]) => (
                <th key={key}>
                  <button
                    onClick={() => handleSort(key)}
                    className="flex items-center gap-1 hover:text-accent-600 transition-colors"
                  >
                    {cfg.label}
                    <ArrowUpDown className={`w-3 h-3 ${sortKey === key ? 'text-accent-600' : 'text-surface-300'}`} />
                  </button>
                </th>
              ))}
              <th>Period</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr key={p.service_id}>
                <td>
                  <div>
                    <p className="font-medium text-surface-800">{p.first_name} {p.last_name}</p>
                    <p className="text-xs text-surface-400">{p.rank} · {p.service_id}</p>
                  </div>
                </td>
                {Object.entries(METRIC_THRESHOLDS).map(([key, cfg]) => (
                  <td key={key} className={isWarning(key, p[key]) ? 'text-amber-600 font-semibold' : ''}>
                    {p[key] != null ? `${p[key]} ${cfg.unit}` : '—'}
                  </td>
                ))}
                <td className="text-xs text-surface-400">{p.period}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-surface-400 text-center mt-4">
        {sorted.length} personnel · Sorted by {METRIC_THRESHOLDS[sortKey]?.label} ({sortAsc ? 'ascending' : 'descending'})
      </p>
    </div>
  );
}
