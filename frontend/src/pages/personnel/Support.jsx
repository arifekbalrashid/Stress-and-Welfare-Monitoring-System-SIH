import { useState, useEffect } from 'react';
import { supportAPI } from '../../services/api';
import { CheckCircle, Send } from 'lucide-react';
import { formatDateTime, capitalize } from '../../utils/formatters';

const CATEGORIES = ['workload', 'personal', 'health', 'leave', 'data_correction', 'other'];

export default function SupportPage() {
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [reference, setReference] = useState('');
  const [loading, setLoading] = useState(false);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');

  const fetchRequests = () => {
    supportAPI.getRequests().then(res => setRequests(res.data.data?.items || [])).catch(() => {});
  };

  useEffect(() => {
    fetchRequests();
    
    // Auto-select category if passed in state
    if (window.history.state?.usr?.category) {
      setCategory(window.history.state.usr.category);
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!category) return;
    setLoading(true);
    try {
      const res = await supportAPI.submit({ category, description: description.trim() || '' });
      setReference(`WR-${res.data.data.id.toString().padStart(4, '0')}`);
      setSubmitted(true);
      setCategory('');
      setDescription('');
      fetchRequests();
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit request.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) return (
    <div>
      <div className="page-header"><h1 className="page-title">Request Support</h1></div>
      <div className="card text-center py-10 max-w-md mx-auto">
        <CheckCircle className="w-8 h-8 text-risk-low mx-auto mb-3" />
        <p className="text-sm font-medium text-surface-800">Request submitted</p>
        <div className="text-xs text-surface-500 mt-3 space-y-1">
          <p>Reference: <span className="font-mono font-medium">{reference}</span></p>
          <p>Status: <span className="font-medium">Submitted</span></p>
        </div>
        <p className="text-xs text-surface-400 mt-4 leading-relaxed">
          Your request will be reviewed by an authorized welfare officer.
        </p>
        <button onClick={() => setSubmitted(false)} className="btn btn-secondary btn-sm mt-5">
          Submit another request
        </button>
      </div>
    </div>
  );

  return (
    <div>
      <div className="page-header"><h1 className="page-title">Request Support</h1></div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="input-label">Category</label>
              <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
                <option value="">Select a category</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{capitalize(c)}</option>)}
              </select>
            </div>
            <div>
              <div className="flex justify-between items-baseline">
                <label className="input-label">Description (optional)</label>
              </div>
              <p className="text-[0.65rem] text-surface-400 mb-1.5">You do not need to share sensitive personal details.</p>
              <textarea
                className="input" rows={4} value={description}
                onChange={e => setDescription(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <button type="submit" className="btn btn-primary w-full" disabled={loading || !category}>
              {loading ? 'Submitting…' : 'Submit request'}
            </button>
          </form>
        </div>

        {requests.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-3">Previous Requests</h3>
            <div className="space-y-2">
              {requests.map(r => (
                <div key={r.id} className="card py-3 px-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-surface-800">WR-{r.id.toString().padStart(4, '0')}</p>
                    <p className="text-xs text-surface-400">{capitalize(r.category)}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-medium text-surface-600">{capitalize(r.status)}</p>
                    <p className="text-[0.65rem] text-surface-400">{new Date(r.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
