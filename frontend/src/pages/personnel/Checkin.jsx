import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { wellnessAPI } from '../../services/api';
import { Clock, CalendarCheck } from 'lucide-react';

const Question = ({ label, name, value, onChange, leftLabel, rightLabel, helperText }) => (
  <div className="card">
    <label className="block text-[1rem] font-medium text-surface-900 mb-1 leading-snug">{label}</label>
    {helperText && <p className="text-sm text-surface-500 mb-5">{helperText}</p>}
    <div className={!helperText ? "mt-5" : ""}>
      <div className="flex justify-between text-xs font-medium text-surface-500 mb-3 px-1">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      <div className="flex gap-2 sm:gap-3 justify-between">
        {[1, 2, 3, 4, 5].map(val => (
          <label key={val} className="relative flex-1 cursor-pointer group">
            <input 
              type="radio" 
              name={name} 
              value={val} 
              checked={value === val} 
              onChange={onChange} 
              className="sr-only" 
            />
            <div className={`h-10 sm:h-11 flex items-center justify-center rounded-xl text-sm font-semibold transition-all duration-200 border ${
              value === val 
                ? 'bg-accent-500 border-accent-500 text-white shadow-md transform scale-[1.02]' 
                : 'bg-surface-50 border-surface-200 text-surface-700 group-hover:bg-surface-100 group-hover:border-surface-300'
            }`}>
              {val}
            </div>
          </label>
        ))}
      </div>
    </div>
  </div>
);

export default function Checkin() {
  const [form, setForm] = useState({
    sleep_quality: null,
    energy_level: null,
    workload_score: null,
    wellbeing_score: null,
    recovery_score: null
  });
  
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cooldown, setCooldown] = useState(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    wellnessAPI.getCheckinStatus()
      .then(r => setCooldown(r.data.data))
      .catch(() => setCooldown({ can_submit: true }));
  }, []);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: Number(e.target.value) }));
  };

  const answeredCount = Object.values(form).filter(v => v !== null).length;
  const isComplete = answeredCount === 5;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isComplete) return;

    setLoading(true);
    setError('');
    
    try {
      await wellnessAPI.submitCheckin(form);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit data.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) return (
    <div className="max-w-xl mx-auto py-16 text-center">
      <h1 className="page-title mb-6">Check-in submitted</h1>
      <p className="text-surface-600 mb-10 leading-relaxed text-sm">
        Thank you for completing your weekly wellbeing check-in.<br/>
        {t('checkin.privacy_note', 'Your responses have been recorded according to your privacy and consent settings.')}
      </p>
      <button onClick={() => navigate('/p/dashboard')} className="btn btn-secondary px-8 py-2.5">
        Return to dashboard
      </button>
    </div>
  );

  if (cooldown === null) return (
    <div>
      <div className="page-header"><h1 className="page-title">Wellness Check-in</h1></div>
      <div className="space-y-4">
        <div className="skeleton h-12 w-1/3" />
        <div className="skeleton h-32 w-full rounded-[14px]" />
        <div className="skeleton h-32 w-full rounded-[14px]" />
      </div>
    </div>
  );

  if (!cooldown.can_submit) {
    const nextDate = new Date(cooldown.next_allowed);
    return (
      <div className="max-w-2xl mx-auto py-12 text-center">
        <Clock className="w-8 h-8 text-amber-500 mx-auto mb-4" />
        <h1 className="page-title mb-2">{t('checkin.already_submitted', 'Check-in already submitted this week')}</h1>
        
        <div className="mt-8 card inline-block text-left">
          <div className="flex items-center gap-3 text-surface-800">
            <CalendarCheck className="w-5 h-5 text-accent-500" />
            <span className="font-medium text-sm">{t('checkin.next_available', 'Next check-in available in')} 
              {cooldown.days_remaining > 0
                ? ` ${cooldown.days_remaining} day${cooldown.days_remaining !== 1 ? 's' : ''}`
                : ` ${cooldown.hours_remaining} hour${cooldown.hours_remaining !== 1 ? 's' : ''}`
              }
            </span>
          </div>
          <p className="text-sm text-surface-500 mt-2 ml-8">
            {nextDate.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })}
          </p>
        </div>
        <div className="mt-10">
          <button onClick={() => navigate('/p/dashboard')} className="btn btn-secondary px-6">
            {t('checkin.return_to_dashboard', 'Return to dashboard')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">{t('checkin.title', 'Weekly wellbeing check-in')}</h1>
        <div className="flex items-center gap-2 mt-3 text-xs font-medium text-surface-500 uppercase tracking-wider">
          <span>Voluntary</span>
          {cooldown.last_submitted && (
            <>
              <span>·</span>
              <span>Last submitted {new Date(cooldown.last_submitted).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
            </>
          )}
        </div>
      </div>

      {/* Progress */}
      <div className="mb-5 flex items-center gap-4">
        <span className="text-sm font-semibold text-surface-700">{answeredCount} of 5 {t('checkin.answered', 'answered')}</span>
        <div className="flex gap-2">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className={`w-2 h-2 rounded-full transition-colors duration-300 ${i <= answeredCount ? 'bg-accent-500' : 'bg-surface-200'}`} />
          ))}
        </div>
      </div>

      {error && <p className="text-sm text-red-500 mb-6">{error}</p>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Question 
          label={t('checkin.sleep_quality', 'How would you rate your sleep quality this week?')}
          name="sleep_quality"
          value={form.sleep_quality}
          onChange={handleChange}
          leftLabel={t('checkin.very_low', 'Very low')}
          rightLabel={t('checkin.very_good', 'Very good')}
          helperText={t('checkin.helper_sleep', 'Think about your typical experience this week.')}
        />

        <Question 
          label={t('checkin.energy_level', 'How would you describe your energy levels?')}
          name="energy_level"
          value={form.energy_level}
          onChange={handleChange}
          leftLabel={t('checkin.very_low', 'Very low')}
          rightLabel={t('checkin.very_good', 'Very good')}
        />

        <Question 
          label={t('checkin.workload', 'How manageable has your workload felt?')}
          name="workload_score"
          value={form.workload_score}
          onChange={handleChange}
          leftLabel={t('checkin.very_difficult', 'Very difficult to manage')}
          rightLabel={t('checkin.highly_manageable', 'Highly manageable')}
        />

        <Question 
          label={t('checkin.wellbeing_score', 'How would you rate your overall wellbeing this week?')}
          name="wellbeing_score"
          value={form.wellbeing_score}
          onChange={handleChange}
          leftLabel={t('checkin.very_low', 'Very low')}
          rightLabel={t('checkin.very_good', 'Very good')}
        />

        <Question 
          label={t('checkin.recovery', 'How well have you been able to recover between duties?')}
          name="recovery_score"
          value={form.recovery_score}
          onChange={handleChange}
          leftLabel={t('checkin.very_poorly', 'Very poorly')}
          rightLabel={t('checkin.very_well', 'Very well')}
        />

        <div className="pt-5 pb-4 flex flex-col items-end gap-3 border-t border-surface-200">
          <div className="flex flex-col sm:flex-row items-end sm:items-center gap-4 w-full sm:w-auto">
            {!isComplete && (
              <span className="text-sm text-surface-500 font-medium">
                {t('checkin.answer_all', 'Please answer all five questions before submitting.')}
              </span>
            )}
            <button
              type="submit"
              disabled={loading || !isComplete}
              className="btn btn-primary px-8 py-2.5 w-full sm:w-auto text-sm font-semibold"
            >
              {loading ? t('checkin.submitting', 'Submitting...') : t('checkin.submit', 'Submit check-in')}
            </button>
          </div>

        </div>
      </form>
    </div>
  );
}
