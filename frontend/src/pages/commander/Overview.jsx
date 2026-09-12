import { useState, useEffect } from 'react';
import { commanderAPI } from '../../services/api';
import { RISK_LEVEL_LABELS } from '../../utils/constants';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, Area, AreaChart, CartesianGrid, Legend
} from 'recharts';
import {
  AlertTriangle, AlertCircle, Info, TrendingUp, Clock,
  Briefcase, Calendar, Moon, Coffee, Shield, Users
} from 'lucide-react';

const COLORS = {
  low: 'var(--color-risk-low)',
  moderate: 'var(--color-risk-moderate)',
  elevated: 'var(--color-risk-elevated)',
  high: 'var(--color-risk-high)',
};

const INSIGHT_ICONS = {
  workload: Briefcase,
  leave: Calendar,
  rest: Coffee,
  trend: TrendingUp,
  risk: AlertTriangle,
  engagement: Users,
};

const INSIGHT_STYLES = {
  critical: { bg: 'bg-red-50', border: 'border-red-200', icon: 'text-red-600', badge: 'bg-red-100 text-red-700' },
  warning:  { bg: 'bg-amber-50', border: 'border-amber-200', icon: 'text-amber-600', badge: 'bg-amber-100 text-amber-700' },
  info:     { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'text-blue-600', badge: 'bg-blue-100 text-blue-700' },
};

export default function CommanderOverview() {
  const [data, setData] = useState(null);
  const [trends, setTrends] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      commanderAPI.getOverview().then(res => setData(res.data.data)),
      commanderAPI.getTrends().then(res => setTrends(res.data.data)),
      commanderAPI.getInsights().then(res => setInsights(res.data.data)),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div>
      <div className="page-header"><h1 className="page-title">Unit Overview</h1></div>
      <div className="skeleton h-64 w-full" />
    </div>
  );

  if (!data) return null;

  const chartData = ['low', 'moderate', 'elevated', 'high'].map(level => ({
    name: RISK_LEVEL_LABELS[level],
    count: data.risk_distribution[level] || 0,
    level,
  }));

  const totalAssessed = data.assessed_personnel || 0;

  // Trend chart data
  const trendData = (trends?.months || []).map(m => ({
    month: m.month.slice(5), // "03", "04", etc.
    label: new Date(m.month + '-01').toLocaleDateString('en-IN', { month: 'short', year: '2-digit' }),
    avg: m.avg_risk_score,
    min: m.min_risk_score,
    max: m.max_risk_score,
    assessed: m.assessed_count,
  }));

  const insightItems = insights?.insights || [];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Unit Overview</h1>
        <p className="page-subtitle">{data.unit_name}</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="card text-center">
          <p className="text-2xl font-semibold text-surface-900">{data.total_personnel}</p>
          <p className="text-xs text-surface-400">Total Personnel</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-semibold text-surface-900">{totalAssessed}</p>
          <p className="text-xs text-surface-400">Assessed</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-semibold text-surface-900">{data.avg_risk_score}</p>
          <p className="text-xs text-surface-400">Avg Risk Score</p>
        </div>
        <div className="card text-center">
          <p className="text-2xl font-semibold text-risk-high">{data.risk_distribution.high || 0}</p>
          <p className="text-xs text-surface-400">High Risk</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Risk distribution chart */}
        <div className="card">
          <div className="section-label">
            <div className="section-label-icon"><AlertCircle /></div>
            Risk Distribution
          </div>
          {totalAssessed === 0 ? (
            <p className="text-sm text-surface-400 text-center py-8">No assessments yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} barSize={40}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#888' }} />
                <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#888' }} />
                <Tooltip cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry) => (
                    <Cell key={entry.level} fill={COLORS[entry.level]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Trends chart */}
        <div className="card">
          <div className="section-label">
            <div className="section-label-icon"><TrendingUp /></div>
            Risk Trend (Last 6 Months)
          </div>
          {trendData.length === 0 ? (
            <p className="text-sm text-surface-400 text-center py-8">No historical data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-accent-500)" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="var(--color-accent-500)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#888' }} />
                <YAxis domain={[0, 100]} axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#888' }} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 12 }}
                  formatter={(value, name) => {
                    const labels = { avg: 'Average', min: 'Minimum', max: 'Maximum' };
                    return [value, labels[name] || name];
                  }}
                />
                <Area type="monotone" dataKey="max" stroke="none" fill="var(--color-risk-elevated)" fillOpacity={0.08} />
                <Area type="monotone" dataKey="avg" stroke="var(--color-accent-600)" strokeWidth={2.5} fill="url(#riskGrad)" dot={{ r: 3, fill: 'var(--color-accent-600)' }} />
                <Line type="monotone" dataKey="min" stroke="var(--color-risk-low)" strokeWidth={1} strokeDasharray="4 4" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Actionable Insights */}
      {insightItems.length > 0 && (
        <div className="mb-6">
          <div className="section-label">
            <div className="section-label-icon"><Info /></div>
            Unit Insights & Alerts
          </div>
          <div className="space-y-3">
            {insightItems.map((insight, i) => {
              const style = INSIGHT_STYLES[insight.type] || INSIGHT_STYLES.info;
              const IconComp = INSIGHT_ICONS[insight.category] || AlertCircle;
              return (
                <div key={i} className={`p-4 rounded-lg border ${style.bg} ${style.border} flex items-start gap-3`}>
                  <IconComp className={`w-5 h-5 mt-0.5 flex-shrink-0 ${style.icon}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-surface-900">{insight.title}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[0.6rem] font-bold uppercase tracking-wide ${style.badge}`}>
                        {insight.type}
                      </span>
                    </div>
                    <p className="text-sm text-surface-700 leading-relaxed">{insight.text}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}


    </div>
  );
}
