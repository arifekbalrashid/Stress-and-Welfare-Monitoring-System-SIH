import { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import { formatDateTime } from '../../utils/formatters';

export default function AdminAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    adminAPI.getAuditLogs({ page, page_size: 20 })
      .then(r => {
        setLogs(r.data.data?.items || []);
        setTotal(r.data.data?.total || 0);
      })
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Audit Logs</h1>
        <p className="page-subtitle">{total} records</p>
      </div>

      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="skeleton h-12 w-full" />)}</div>
      ) : logs.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-sm text-surface-400">No audit logs yet.</p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th><th>Reason</th></tr>
              </thead>
              <tbody>
                {logs.map(l => (
                  <tr key={l.id}>
                    <td className="text-xs text-surface-400">{formatDateTime(l.created_at)}</td>
                    <td className="font-medium text-surface-700">{l.actor_username || `User #${l.actor_user_id}`}</td>
                    <td><span className="badge badge-neutral">{l.action}</span></td>
                    <td className="text-surface-500">{l.resource_type} #{l.resource_id}</td>
                    <td className="text-xs text-surface-400">{l.reason || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {total > 20 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="btn btn-ghost btn-sm">
                Previous
              </button>
              <span className="text-xs text-surface-400">Page {page}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total} className="btn btn-ghost btn-sm">
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
