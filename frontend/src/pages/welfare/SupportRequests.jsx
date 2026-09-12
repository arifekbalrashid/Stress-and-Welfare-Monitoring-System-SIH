import { useState, useEffect } from 'react';
import { welfareAPI } from '../../services/api';
import { formatDateTime, capitalize } from '../../utils/formatters';
import {
  Inbox, AlertCircle, Clock, CheckCircle2, Loader2, XCircle,
  Filter, ChevronDown, MessageSquare, User, Briefcase, Heart, Calendar, HelpCircle, Database
} from 'lucide-react';

const CATEGORY_CONFIG = {
  workload:  { label: 'Workload', icon: Briefcase, color: 'text-blue-700', bg: 'bg-blue-50', border: 'border-blue-200' },
  personal:  { label: 'Personal', icon: User, color: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-200' },
  health:    { label: 'Health', icon: Heart, color: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200' },
  leave:            { label: 'Leave', icon: Calendar, color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' },
  data_correction:   { label: 'Data Correction', icon: Database, color: 'text-cyan-700', bg: 'bg-cyan-50', border: 'border-cyan-200' },
  other:             { label: 'Other', icon: HelpCircle, color: 'text-surface-600', bg: 'bg-surface-50', border: 'border-surface-200' },
};

const STATUS_CONFIG = {
  submitted:    { label: 'New', bg: 'bg-amber-100', text: 'text-amber-800', icon: Inbox },
  acknowledged: { label: 'Acknowledged', bg: 'bg-blue-100', text: 'text-blue-800', icon: CheckCircle2 },
  in_progress:  { label: 'In Progress', bg: 'bg-indigo-100', text: 'text-indigo-800', icon: Loader2 },
  resolved:     { label: 'Resolved', bg: 'bg-emerald-100', text: 'text-emerald-800', icon: CheckCircle2 },
  closed:       { label: 'Closed', bg: 'bg-surface-100', text: 'text-surface-600', icon: XCircle },
};

const STATUS_ACTIONS = {
  submitted:    [{ value: 'acknowledged', label: 'Acknowledge' }, { value: 'in_progress', label: 'Start working' }],
  acknowledged: [{ value: 'in_progress', label: 'Start working' }, { value: 'resolved', label: 'Mark resolved' }],
  in_progress:  [{ value: 'resolved', label: 'Mark resolved' }],
  resolved:     [{ value: 'closed', label: 'Close' }],
  closed:       [],
};

export default function SupportRequests() {
  const [requests, setRequests] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(null);
  const [expandedId, setExpandedId] = useState(null);

  const [filters, setFilters] = useState({
    status: '',
    category: '',
  });

  useEffect(() => {
    fetchRequests();
  }, [filters.status, filters.category]);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const res = await welfareAPI.getSupportRequests(filters);
      setRequests(res.data.data.items);
      setSummary(res.data.data.summary);
    } catch (err) {
      setError('Unable to load support requests.');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (requestId, newStatus) => {
    setUpdating(requestId);
    try {
      await welfareAPI.updateSupportRequestStatus(requestId, newStatus);
      await fetchRequests();
    } catch (err) {
      // Silently fail
    } finally {
      setUpdating(null);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
        <p className="text-sm font-medium text-surface-800 mb-4">{error}</p>
        <button onClick={fetchRequests} className="btn btn-outline btn-sm">Try again</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* 1. Header */}
      <div className="page-header mb-2">
        <h1 className="page-title">Support Requests</h1>
        <p className="page-subtitle">Review and respond to support requests submitted by personnel.</p>
      </div>

      {/* 2. Summary */}
      {summary && (
        <div className="text-sm text-surface-700 bg-surface-50 px-4 py-3 rounded-md border border-surface-200">
          <strong>{summary.total}</strong> total requests &middot;{' '}
          <span className={summary.submitted > 0 ? 'font-semibold text-amber-600' : ''}>{summary.submitted} New</span> &middot;{' '}
          <span className={summary.acknowledged > 0 ? 'font-semibold text-blue-600' : ''}>{summary.acknowledged} Acknowledged</span> &middot;{' '}
          <span className={summary.in_progress > 0 ? 'font-semibold text-indigo-600' : ''}>{summary.in_progress} In Progress</span> &middot;{' '}
          <span>{summary.resolved} Resolved</span> &middot;{' '}
          <span>{summary.closed} Closed</span>
        </div>
      )}

      {/* 3. Status Filter Tabs */}
      <div className="filter-tabs">
        {[
          { id: '', label: 'All', count: summary?.total },
          { id: 'submitted', label: 'New', count: summary?.submitted },
          { id: 'acknowledged', label: 'Acknowledged', count: summary?.acknowledged },
          { id: 'in_progress', label: 'In Progress', count: summary?.in_progress },
          { id: 'resolved', label: 'Resolved', count: summary?.resolved },
          { id: 'closed', label: 'Closed', count: summary?.closed },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => handleFilterChange('status', tab.id)}
            className={`filter-tab ${filters.status === tab.id ? 'filter-tab-active' : ''}`}
          >
            {tab.label} <span className="filter-tab-count">{tab.count ?? 0}</span>
          </button>
        ))}
      </div>

      {/* 4. Category Filter */}
      <div className="filter-bar">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-surface-400" />
          <select
            className="filter-select"
            value={filters.category}
            onChange={(e) => handleFilterChange('category', e.target.value)}
          >
            <option value="">Category: All</option>
            <option value="workload">Workload</option>
            <option value="personal">Personal</option>
            <option value="health">Health</option>
            <option value="leave">Leave</option>
            <option value="data_correction">Data Correction</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* 5. Request List */}
      <div className="space-y-3">
        {loading ? (
          [...Array(3)].map((_, i) => (
            <div key={i} className="card"><div className="skeleton h-20 w-full" /></div>
          ))
        ) : requests.length === 0 ? (
          <div className="card text-center py-12">
            <Inbox className="w-8 h-8 text-surface-300 mx-auto mb-3" />
            <p className="text-sm text-surface-500">
              {filters.status || filters.category
                ? 'No requests match your filters.'
                : 'No support requests have been submitted yet.'}
            </p>
          </div>
        ) : (
          requests.map(req => {
            const cat = CATEGORY_CONFIG[req.category] || CATEGORY_CONFIG.other;
            const st = STATUS_CONFIG[req.status] || STATUS_CONFIG.submitted;
            const actions = STATUS_ACTIONS[req.status] || [];
            const CatIcon = cat.icon;
            const isExpanded = expandedId === req.id;

            return (
              <div
                key={req.id}
                className={`card-flat p-0 overflow-hidden transition-all ${
                  req.status === 'submitted' ? 'border-amber-200 shadow-[0_2px_8px_rgba(251,191,36,0.15)]' : ''
                }`}
              >
                {/* Card Header — always visible */}
                <div
                  className="px-4 py-3.5 flex items-start gap-4 cursor-pointer hover:bg-surface-50/50 transition-colors"
                  onClick={() => setExpandedId(isExpanded ? null : req.id)}
                >
                  {/* Category icon */}
                  <div className={`flex-shrink-0 w-9 h-9 rounded-lg ${cat.bg} flex items-center justify-center mt-0.5`}>
                    <CatIcon className={`w-4 h-4 ${cat.color}`} />
                  </div>

                  {/* Main content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`px-2 py-0.5 rounded-full text-[0.65rem] font-semibold tracking-wide uppercase ${st.bg} ${st.text}`}>
                        {st.label}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[0.65rem] font-medium tracking-wide uppercase ${cat.bg} ${cat.color} border ${cat.border}`}>
                        {cat.label}
                      </span>
                    </div>
                    <p className="text-sm text-surface-800 mt-1.5 line-clamp-2">{req.description}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-surface-400">
                      <span className="font-medium text-surface-600">{req.first_name} {req.last_name}</span>
                      <span>&middot;</span>
                      <span>{req.rank}</span>
                      <span>&middot;</span>
                      <span>{req.unit_name}</span>
                      <span>&middot;</span>
                      <span className="flex items-center"><Clock className="w-3 h-3 mr-1" />{formatDateTime(req.created_at)}</span>
                    </div>
                  </div>

                  {/* Expand indicator */}
                  <ChevronDown className={`w-4 h-4 text-surface-400 flex-shrink-0 mt-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                </div>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="px-4 py-3 bg-surface-50/50 border-t border-surface-100">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Full description */}
                      <div>
                        <p className="text-xs font-medium text-surface-400 uppercase tracking-wide mb-1.5">Full Message</p>
                        <p className="text-sm text-surface-700 leading-relaxed bg-white p-3 rounded-md border border-surface-200">
                          <MessageSquare className="w-3.5 h-3.5 inline mr-1.5 text-surface-400 -mt-0.5" />
                          {req.description}
                        </p>
                      </div>

                      {/* Personnel details */}
                      <div>
                        <p className="text-xs font-medium text-surface-400 uppercase tracking-wide mb-1.5">Personnel Details</p>
                        <div className="bg-white p-3 rounded-md border border-surface-200 text-sm space-y-1.5">
                          <div className="flex justify-between">
                            <span className="text-surface-500">Name</span>
                            <span className="text-surface-800 font-medium">{req.first_name} {req.last_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-surface-500">Service ID</span>
                            <span className="text-surface-800 font-medium">{req.service_id}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-surface-500">Rank</span>
                            <span className="text-surface-800">{req.rank}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-surface-500">Unit</span>
                            <span className="text-surface-800">{req.unit_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-surface-500">Submitted</span>
                            <span className="text-surface-800">{formatDateTime(req.created_at)}</span>
                          </div>
                          {req.updated_at && req.updated_at !== req.created_at && (
                            <div className="flex justify-between">
                              <span className="text-surface-500">Last Updated</span>
                              <span className="text-surface-800">{formatDateTime(req.updated_at)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    {actions.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-surface-200 flex items-center gap-2">
                        <span className="text-xs text-surface-400 mr-1">Update status:</span>
                        {actions.map(action => (
                          <button
                            key={action.value}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStatusUpdate(req.id, action.value);
                            }}
                            disabled={updating === req.id}
                            className={`btn btn-sm ${
                              action.value === 'resolved' || action.value === 'closed'
                                ? 'btn-secondary'
                                : 'btn-primary'
                            } ${updating === req.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            {updating === req.id ? 'Updating...' : action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
