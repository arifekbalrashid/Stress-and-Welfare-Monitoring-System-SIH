import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { welfareAPI } from '../../services/api';
import { ArrowLeft, AlertCircle, TrendingUp, TrendingDown, Minus, Clock, Activity, FileText, BarChart3, Briefcase, HeartPulse, CheckSquare, List } from 'lucide-react';
import { formatDateTime } from '../../utils/formatters';

export default function CaseDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Intervention modal state
  const [showModal, setShowModal] = useState(false);
  const [interventionForm, setInterventionForm] = useState({
    intervention_type: 'counseling',
    notes: '',
    follow_up_date: ''
  });

  useEffect(() => {
    fetchCase();
  }, [id]);

  const fetchCase = async () => {
    try {
      const res = await welfareAPI.getCase(id);
      setData(res.data.data);
    } catch (err) {
      setError('Unable to load welfare case details.');
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (status) => {
    try {
      await welfareAPI.updateCaseStatus(id, status);
      fetchCase();
    } catch (err) {
      console.error(err);
    }
  };

  const handleInterventionSubmit = async (e) => {
    e.preventDefault();
    try {
      await welfareAPI.logIntervention({
        personnel_id: Number(id),
        risk_prediction_id: data.risk_prediction_id || null,
        intervention_type: interventionForm.intervention_type,
        notes: interventionForm.notes,
        follow_up_date: interventionForm.follow_up_date || null
      });
      // automatically set status to intervention_recorded
      await updateStatus('intervention_recorded');
      setShowModal(false);
      setInterventionForm({ intervention_type: 'counseling', notes: '', follow_up_date: '' });
    } catch (err) {
      console.error(err);
    }
  };

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'increasing': return <span className="flex items-center text-risk-elevated font-medium"><TrendingUp className="w-4 h-4 mr-1.5"/> Increasing</span>;
      case 'decreasing': return <span className="flex items-center text-risk-low font-medium"><TrendingDown className="w-4 h-4 mr-1.5"/> Decreasing</span>;
      default: return <span className="flex items-center text-surface-500 font-medium"><Minus className="w-4 h-4 mr-1.5"/> Stable</span>;
    }
  };

  if (loading) return <div className="p-8 text-center text-surface-500">Loading case details...</div>;
  if (error || !data) return (
    <div className="flex flex-col items-center justify-center py-20">
      <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
      <p className="text-sm font-medium text-surface-800 mb-4">{error}</p>
      <Link to="/w/cases" className="btn btn-outline btn-sm">Return to cases</Link>
    </div>
  );

  return (
    <div className="space-y-6 pb-20">
      <Link to="/w/cases" className="inline-flex items-center text-sm font-medium text-surface-500 hover:text-surface-900 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-1.5" /> Back to cases
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-surface-900 tracking-tight">{data.first_name} {data.last_name}</h1>
            <p className="text-sm text-surface-500 mt-1">{data.service_id} &middot; {data.unit_name}</p>
          </div>
          <div className="text-right flex gap-6">
            <div>
              <p className="text-xs text-surface-500 uppercase font-semibold tracking-wider mb-1">Welfare Indicator</p>
              <p className={`text-lg font-bold ${
                data.risk_level === 'high' ? 'text-risk-high' :
                data.risk_level === 'elevated' ? 'text-risk-elevated' :
                'text-surface-700'
              }`}>
                {Math.round(data.risk_score)} <span className="text-sm font-normal text-surface-500">/ 100</span> <span className="ml-1 text-sm capitalize">({data.risk_level})</span>
              </p>
            </div>
            <div>
              <p className="text-xs text-surface-500 uppercase font-semibold tracking-wider mb-1">Trend</p>
              <div className="mt-1">{getTrendIcon(data.trend)}</div>
            </div>
            <div>
              <p className="text-xs text-surface-500 uppercase font-semibold tracking-wider mb-1">Last Assessed</p>
              <p className="text-sm text-surface-700 font-medium mt-1">{formatDateTime(data.last_prediction_at)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Left Column */}
        <div className="space-y-6">
          
          {/* SHAP Factors */}
          <section className="card">
            <div className="section-label">
              <div className="section-label-icon"><BarChart3 /></div>
              Contributing factors to this model prediction
            </div>
            {data.shap_factors?.factors?.length > 0 ? (
              <div className="space-y-3">
                {data.shap_factors.factors.map((f, idx) => (
                  <div key={idx}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-surface-700 font-medium">{f.label}</span>
                      <span className="text-surface-500">{Math.round(f.impact * 100)}%</span>
                    </div>
                    <div className="w-full bg-surface-100 rounded-full h-1.5">
                      <div className="bg-accent-500 h-1.5 rounded-full" style={{ width: `${Math.round(f.impact * 100)}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-surface-500">No primary contributing factors identified.</p>
            )}
          </section>

          {/* Operational Context */}
          <section className="card">
            <div className="section-label">
              <div className="section-label-icon"><Briefcase /></div>
              Operational Context
            </div>
            {data.operational_context ? (
              <div className="grid grid-cols-2 gap-y-4 gap-x-2">
                <div><p className="text-xs text-surface-500">Duty Hours</p><p className="text-sm font-medium text-surface-900">{data.operational_context.duty_hours} hrs/week</p></div>
                <div><p className="text-xs text-surface-500">Night Shifts</p><p className="text-sm font-medium text-surface-900">{data.operational_context.night_shifts} / month</p></div>
                <div><p className="text-xs text-surface-500">Consecutive Duty</p><p className="text-sm font-medium text-surface-900">{data.operational_context.consecutive_duty_days} days</p></div>
                <div><p className="text-xs text-surface-500">Leave Gap</p><p className="text-sm font-medium text-surface-900">{data.operational_context.leave_gap_days} days</p></div>
                <div><p className="text-xs text-surface-500">Deployment</p><p className="text-sm font-medium text-surface-900">{data.operational_context.deployment_days} days</p></div>
                <div><p className="text-xs text-surface-500">Rest Hours</p><p className="text-sm font-medium text-surface-900">{data.operational_context.rest_hours} hrs/day</p></div>
              </div>
            ) : (
              <p className="text-sm text-surface-500">Operational data unavailable.</p>
            )}
          </section>

          {/* Voluntary Wellness Info */}
          <section className="card">
            <div className="section-label">
              <div className="section-label-icon"><HeartPulse /></div>
              Voluntary wellness information
              {!data.wellness_context && <span className="text-[0.65rem] font-normal text-surface-400 bg-surface-100 px-2 py-0.5 rounded ml-auto">Not provided</span>}
            </div>
            {data.wellness_context ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center text-sm border-b border-surface-50 pb-2"><span className="text-surface-600">Sleep quality</span><span className="font-medium text-surface-900">{data.wellness_context.sleep_quality} / 5</span></div>
                <div className="flex justify-between items-center text-sm border-b border-surface-50 pb-2"><span className="text-surface-600">Energy level</span><span className="font-medium text-surface-900">{data.wellness_context.energy_level} / 5</span></div>
                <div className="flex justify-between items-center text-sm border-b border-surface-50 pb-2"><span className="text-surface-600">Perceived workload</span><span className="font-medium text-surface-900">{data.wellness_context.workload_perception} / 5</span></div>
                <div className="flex justify-between items-center text-sm border-b border-surface-50 pb-2"><span className="text-surface-600">Recovery</span><span className="font-medium text-surface-900">{data.wellness_context.recovery} / 5</span></div>
                <div className="flex justify-between items-center text-sm"><span className="text-surface-600">Overall wellbeing</span><span className="font-medium text-surface-900">{data.wellness_context.wellbeing} / 5</span></div>
              </div>
            ) : (
              <p className="text-sm text-surface-500">Latest voluntary wellness information unavailable or consent withdrawn.</p>
            )}
          </section>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          
          {/* Data Availability */}
          <section className="card">
            <div className="section-label">
              <div className="section-label-icon"><CheckSquare /></div>
              Data Availability
            </div>
            <div className="space-y-2 text-sm text-surface-700">
              <div className="flex justify-between"><span>Operational data</span> <span>{data.data_availability?.operational ? '✓' : '—'}</span></div>
              <div className="flex justify-between"><span>Wellness data</span> <span>{data.data_availability?.wellness ? '✓' : '—'}</span></div>
              <div className="flex justify-between"><span>Historical data</span> <span>{data.data_availability?.historical ? '✓' : '—'}</span></div>
            </div>
          </section>

          {/* Recommendations */}
          <section className="card border-l-4 border-l-accent-500">
            <div className="section-label">
              <div className="section-label-icon"><AlertCircle className="text-accent-600" /></div>
              Recommendations for review
            </div>
            {data.recommendations?.length > 0 ? (
              <ul className="space-y-3">
                {data.recommendations.map((r, i) => (
                  <li key={i} className="text-sm text-surface-800 flex items-start">
                    <span className="mr-2 text-accent-500">•</span>
                    {r.text}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-surface-500">No specific welfare recommendations generated for this case.</p>
            )}
          </section>

          {/* Welfare Officer Decision */}
          <section className="card">
            <div className="section-label">
              <div className="section-label-icon"><FileText /></div>
              Welfare Officer Decision
            </div>
            
            <div className="mb-4">
              <p className="text-xs text-surface-500 mb-1">Current Review Status</p>
              <div className="text-sm font-medium capitalize flex items-center text-surface-800">
                <Activity className="w-4 h-4 mr-2 text-accent-500" />
                {data.review_status ? data.review_status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'Closed'}
              </div>
            </div>

            <div className="space-y-2">
              {data.review_status === 'closed' || data.review_status === 'needs_review' ? (
                <button onClick={() => updateStatus('under_review')} className="w-full btn btn-outline text-sm py-2">
                  Start Review
                </button>
              ) : null}
              
              <button onClick={() => setShowModal(true)} className="w-full btn btn-primary text-sm py-2">
                Record Intervention
              </button>
              
              {data.review_status !== 'monitoring' && (
                <button onClick={() => updateStatus('monitoring')} className="w-full btn btn-outline text-sm py-2">
                  Continue Monitoring
                </button>
              )}

              {data.review_status !== 'closed' && (
                <button onClick={() => updateStatus('closed')} className="w-full btn btn-ghost text-sm py-2 mt-2 text-surface-500 hover:text-red-600">
                  Close Case
                </button>
              )}
            </div>
          </section>

          {/* Intervention History */}
          {data.interventions?.length > 0 && (
            <section className="card">
              <div className="section-label">
                <div className="section-label-icon"><List /></div>
                Intervention History
              </div>
              <div className="space-y-4">
                {data.interventions.map(inv => (
                  <div key={inv.id} className="text-sm">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-surface-800 capitalize">{inv.intervention_type.replace('_', ' ')}</span>
                      <span className="text-xs text-surface-500">{formatDateTime(inv.created_at)}</span>
                    </div>
                    {inv.notes && <p className="text-surface-600 bg-surface-50 p-2 rounded text-xs italic mt-1">"{inv.notes}"</p>}
                    {inv.follow_up_date && <p className="text-xs text-accent-600 mt-1">Follow-up: {inv.follow_up_date}</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

        </div>
      </div>

      {/* Intervention Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Record Intervention</h3>
              <button onClick={() => setShowModal(false)} className="modal-close">&times;</button>
            </div>
            
            <div className="modal-body">
              <form onSubmit={handleInterventionSubmit} className="space-y-4">
                <div>
                  <label className="input-label">Type</label>
                  <select 
                    className="input"
                    value={interventionForm.intervention_type}
                    onChange={(e) => setInterventionForm(prev => ({...prev, intervention_type: e.target.value}))}
                    required
                  >
                    <option value="counseling">Welfare discussion / Counseling</option>
                    <option value="workload_adjustment">Workload review / Adjustment</option>
                    <option value="leave_recommendation">Leave / recovery review</option>
                    <option value="referral">Support referral</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label className="input-label">Optional notes</label>
                  <textarea 
                    className="input h-24 resize-none"
                    value={interventionForm.notes}
                    onChange={(e) => setInterventionForm(prev => ({...prev, notes: e.target.value}))}
                  ></textarea>
                </div>

                <div>
                  <label className="input-label">Follow-up date (Optional)</label>
                  <input 
                    type="date" 
                    className="input"
                    value={interventionForm.follow_up_date}
                    onChange={(e) => setInterventionForm(prev => ({...prev, follow_up_date: e.target.value}))}
                  />
                </div>

                <div className="pt-4 flex justify-end gap-3">
                  <button type="button" onClick={() => setShowModal(false)} className="btn btn-outline text-sm">Cancel</button>
                  <button type="submit" className="btn btn-primary text-sm">Save intervention</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
