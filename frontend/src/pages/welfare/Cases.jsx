import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { welfareAPI } from '../../services/api';
import { Search, Filter, AlertCircle, TrendingUp, TrendingDown, Minus, ChevronRight, Clock } from 'lucide-react';
import { formatDateTime, capitalize } from '../../utils/formatters';

export default function Cases() {
  const [cases, setCases] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [showHighRiskPrompt, setShowHighRiskPrompt] = useState(false);
  
  const [filters, setFilters] = useState({
    risk_level: '',
    trend: '',
    review_status: '',
    search: ''
  });
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
  }, [filters.risk_level, filters.trend, filters.review_status]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const res = await welfareAPI.getCases(filters);
      setCases(res.data.data.items);
      if (res.data.data.summary) {
        const sum = res.data.data.summary;
        setSummary(sum);
        
        // Show popup only if there is any high risk, we haven't prompted yet, and no risk filter is currently applied
        const hasPrompted = sessionStorage.getItem('hasPromptedHighRisk');
        if (!hasPrompted && sum.high > 0 && !filters.risk_level) {
          setShowHighRiskPrompt(true);
          sessionStorage.setItem('hasPromptedHighRisk', 'true');
        }
      }
    } catch (err) {
      setError('Unable to load welfare cases.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'increasing': return <span className="flex items-center text-risk-elevated font-medium text-xs"><TrendingUp className="w-3.5 h-3.5 mr-1"/> Increasing</span>;
      case 'decreasing': return <span className="flex items-center text-risk-low font-medium text-xs"><TrendingDown className="w-3.5 h-3.5 mr-1"/> Decreasing</span>;
      default: return <span className="flex items-center text-surface-500 font-medium text-xs"><Minus className="w-3.5 h-3.5 mr-1"/> Stable</span>;
    }
  };

  const getStatusBadge = (status) => {
    const key = status?.toLowerCase();
    const map = {
      'needs_review': 'badge-warning',
      'under_review': 'badge-info',
      'monitoring': 'badge-elevated',
      'intervention_recorded': 'badge-low',
      'follow_up': 'badge-moderate',
      'closed': 'badge-neutral'
    };
    // fallback if no custom class created
    let badgeClass = map[key];
    if (badgeClass === 'badge-warning') badgeClass = 'bg-amber-100 text-amber-800';
    else if (badgeClass === 'badge-info') badgeClass = 'bg-blue-100 text-blue-800';
    else if (badgeClass === 'badge-elevated') badgeClass = 'badge-elevated';
    else if (badgeClass === 'badge-low') badgeClass = 'badge-low';
    else if (badgeClass === 'badge-moderate') badgeClass = 'badge-moderate';
    else badgeClass = 'badge-neutral';
    
    // Better to just use design system badges
    let displayClass = 'badge-neutral';
    if (key === 'needs_review') displayClass = 'badge-high';
    if (key === 'under_review') displayClass = 'badge-elevated';
    if (key === 'intervention_recorded') displayClass = 'badge-low';
    if (key === 'monitoring' || key === 'follow_up') displayClass = 'badge-moderate';

    const label = key ? capitalize(key.replace('_', ' ')) : 'Closed';
    return <span className={`badge ${displayClass}`}>{label}</span>;
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
        <p className="text-sm font-medium text-surface-800 mb-4">{error}</p>
        <button onClick={fetchCases} className="btn btn-outline btn-sm">Try again</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {showHighRiskPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/10 backdrop-blur-sm transition-all duration-300">
          <div 
            onClick={() => {
              handleFilterChange('risk_level', 'high');
              setShowHighRiskPrompt(false);
            }}
            className="bg-white/95 backdrop-blur-md rounded-2xl p-6 max-w-sm w-full mx-4 shadow-[0_20px_50px_rgba(0,0,0,0.1)] border border-white cursor-pointer hover:scale-[1.02] transition-transform duration-300 relative group overflow-hidden"
          >
            {/* Subtle animated background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-red-50 to-transparent opacity-50 pointer-events-none" />
            
            <button 
              onClick={(e) => {
                e.stopPropagation();
                setShowHighRiskPrompt(false);
              }}
              className="absolute top-4 right-4 text-surface-400 hover:text-surface-600 p-1 rounded-full hover:bg-surface-100 transition-colors z-20"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
            
            <div className="relative z-10 flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-sm">
                <AlertCircle className="w-6 h-6 text-red-500" />
              </div>
              <h3 className="text-xl font-medium text-surface-900 mb-2">
                Attention Required
              </h3>
              <p className="text-sm text-surface-600 mb-1">
                There are <span className="font-semibold text-red-600">{summary?.high}</span> personnel identified with high stress risk.
              </p>
              <p className="text-xs font-medium text-accent-500 mt-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300 translate-y-2 group-hover:translate-y-0">
                Click anywhere to filter &rarr;
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 1. Header */}
      <div className="page-header mb-2">
        <h1 className="page-title">Cases</h1>
        <p className="page-subtitle">Review welfare indicators and follow up on cases requiring attention.</p>
      </div>

      {/* 2. Summary */}
      {summary && (
        <div className="text-sm text-surface-700 bg-surface-50 px-4 py-3 rounded-md border border-surface-200">
          <strong>{summary.total_assessed}</strong> personnel assessed &middot;{' '}
          <span className={summary.high > 0 ? 'font-semibold text-risk-high' : ''}>{summary.high} High</span> &middot;{' '}
          <span className={summary.elevated > 0 ? 'font-semibold text-risk-elevated' : ''}>{summary.elevated} Elevated</span> &middot;{' '}
          <span>{summary.moderate} Moderate</span> &middot;{' '}
          <span>{summary.low} Low</span>
          {summary.increasing > 0 && <span className="ml-2 pl-2 border-l border-surface-300 text-surface-600"><TrendingUp className="inline w-3 h-3 mr-1 mb-0.5"/> {summary.increasing} increasing</span>}
        </div>
      )}

      {/* 3. Risk Filter Tabs */}
      <div className="filter-tabs">
        {[
          { id: '', label: 'All', count: summary?.total_assessed },
          { id: 'high', label: 'High', count: summary?.high },
          { id: 'elevated', label: 'Elevated', count: summary?.elevated },
          { id: 'moderate', label: 'Moderate', count: summary?.moderate },
          { id: 'low', label: 'Low', count: summary?.low }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => handleFilterChange('risk_level', tab.id)}
            className={`filter-tab ${filters.risk_level === tab.id ? 'filter-tab-active' : ''}`}
          >
            {tab.label} <span className="filter-tab-count">{tab.count ?? 0}</span>
          </button>
        ))}
      </div>

      {/* 4. Search and Filters */}
      <div className="filter-bar">
        <div className="relative flex-grow max-w-xs">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
          <input 
            type="text" 
            placeholder="Search by ID or Name..." 
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-surface-200 rounded focus:ring-1 focus:ring-accent-500 outline-none bg-surface-50"
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
          />
        </div>
        
        <div className="flex items-center gap-2 ml-auto">
          <Filter className="w-4 h-4 text-surface-400" />
          <select 
            className="filter-select"
            value={filters.trend}
            onChange={(e) => handleFilterChange('trend', e.target.value)}
          >
            <option value="">Trend: All</option>
            <option value="increasing">Increasing</option>
            <option value="stable">Stable</option>
            <option value="decreasing">Decreasing</option>
          </select>

          <select 
            className="filter-select"
            value={filters.review_status}
            onChange={(e) => handleFilterChange('review_status', e.target.value)}
          >
            <option value="">Status: All</option>
            <option value="needs_review">Needs review</option>
            <option value="under_review">Under review</option>
            <option value="monitoring">Monitoring</option>
            <option value="intervention_recorded">Intervention</option>
            <option value="follow_up">Follow-up</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* 5. Case Table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Personnel</th>
              <th>Unit</th>
              <th>Welfare Indicator</th>
              <th>Trend</th>
              <th>Review Status</th>
              <th>Last Assessed</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(3)].map((_, i) => (
                <tr key={i}>
                  <td colSpan="7" className="px-4 py-4"><div className="skeleton h-8 w-full" /></td>
                </tr>
              ))
            ) : cases.filter(c => 
                !filters.search || 
                c.service_id.toLowerCase().includes(filters.search.toLowerCase()) ||
                `${c.first_name} ${c.last_name}`.toLowerCase().includes(filters.search.toLowerCase())
              ).length === 0 ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-sm text-surface-500">
                  {filters.risk_level || filters.trend || filters.review_status || filters.search 
                    ? 'No cases match your filters.' 
                    : 'All current welfare indicators are stable. Cases requiring review will appear here when identified.'}
                </td>
              </tr>
            ) : (
              cases.filter(c => 
                !filters.search || 
                c.service_id.toLowerCase().includes(filters.search.toLowerCase()) ||
                `${c.first_name} ${c.last_name}`.toLowerCase().includes(filters.search.toLowerCase())
              ).map(c => (
                <tr 
                  key={c.personnel_id} 
                  onClick={() => navigate(`/w/cases/${c.personnel_id}`)}
                  className="cursor-pointer group"
                >
                  <td>
                    <div className="text-sm font-medium text-surface-900">{c.first_name} {c.last_name}</div>
                    <div className="text-xs text-surface-500">{c.service_id}</div>
                  </td>
                  <td className="text-sm text-surface-600">{c.unit_name}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold tabular-nums text-surface-900">{Math.round(c.risk_score)}</span>
                      <span className={`badge ${
                        c.risk_level === 'high' ? 'badge-high' :
                        c.risk_level === 'elevated' ? 'badge-elevated' :
                        c.risk_level === 'moderate' ? 'badge-moderate' : 'badge-low'
                      }`}>
                        {capitalize(c.risk_level)}
                      </span>
                    </div>
                  </td>
                  <td>{getTrendIcon(c.trend)}</td>
                  <td>{getStatusBadge(c.review_status)}</td>
                  <td className="text-xs text-surface-500">
                    <div className="flex items-center"><Clock className="w-3 h-3 mr-1.5 opacity-70"/> {formatDateTime(c.last_prediction_at)}</div>
                  </td>
                  <td className="text-right">
                    <button className="text-accent-600 hover:text-accent-800 text-xs font-medium flex items-center justify-end w-full group-hover:translate-x-1 transition-transform">
                      View case <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
