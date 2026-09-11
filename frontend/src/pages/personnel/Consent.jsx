import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { consentAPI, personnelAPI } from '../../services/api';
import { Shield, Eye, User, Users, Server, Database, Activity, Lock, Clock } from 'lucide-react';
import { formatDateTime } from '../../utils/formatters';

export default function ConsentPage() {
  const [consents, setConsents] = useState({});
  const [accessHistory, setAccessHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    Promise.all([
      consentAPI.getAll().then(res => {
        const map = {};
        (res.data.data || []).forEach(c => { map[c.data_type] = c.status === 'granted'; });
        setConsents(map);
      }),
      personnelAPI.getDashboard().then(res => {
        setAccessHistory(res.data.data?.access_history || []);
      })
    ]).finally(() => setLoading(false));
  }, []);

  const toggle = async (dataType) => {
    const isGranted = consents[dataType];
    try {
      if (isGranted) {
        await consentAPI.withdraw(dataType);
      } else {
        await consentAPI.grant(dataType);
      }
      setConsents(prev => ({ ...prev, [dataType]: !isGranted }));
    } catch {}
  };

  if (loading) return (
    <div>
      <div className="page-header"><h1 className="page-title">{t('consent.title', 'Privacy & Consent')}</h1></div>
      <div className="skeleton h-64 w-full rounded-[14px]" />
    </div>
  );

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t('consent.title', 'Privacy & Consent')}</h1>
        <p className="page-subtitle">{t('consent.subtitle', 'Manage how your data is used for welfare assessment.')}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Data Types */}
        <div className="md:col-span-2 space-y-6">
          <section>
            <div className="section-label">
              <div className="section-label-icon"><Database /></div>
              {t('consent.required_data', 'Required Data')}
            </div>
            <div className="card">
              <p className="text-sm font-medium text-surface-800">{t('consent.operational_data', 'Operational Data')}</p>
              <p className="text-xs text-surface-500 mt-1">{t('consent.operational_data_desc', 'Duty hours, deployments, and leave info provided automatically by HR for baseline risk assessment.')}</p>
            </div>
          </section>

          <section>
            <div className="section-label">
              <div className="section-label-icon"><Activity /></div>
              {t('consent.voluntary_data', 'Voluntary Data')}
            </div>
            <div className="card space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-surface-800">{t('consent.wellness_checkins', 'Wellness Check-ins')}</p>
                  <p className="text-xs text-surface-500 mt-1">{t('consent.wellness_checkins_desc', 'Allow SAATHI to use your weekly wellness answers to improve support recommendations.')}</p>
                </div>
                <button 
                  onClick={() => toggle('wellness_checkin')} 
                  className={`toggle ${consents['wellness_checkin'] ? 'toggle-on' : 'toggle-off'}`}
                >
                  <div className="toggle-knob" />
                </button>
              </div>
              <div className="pt-3 border-t border-surface-100 flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-surface-800">{t('consent.unit_reporting', 'Unit Reporting')}</p>
                  <p className="text-xs text-surface-500 mt-1">{t('consent.unit_reporting_desc', 'Include your data in anonymized, unit-wide statistics (Commanders never see your individual answers).')}</p>
                </div>
                <button 
                  onClick={() => toggle('risk_sharing')} 
                  className={`toggle ${consents['risk_sharing'] ? 'toggle-on' : 'toggle-off'}`}
                >
                  <div className="toggle-knob" />
                </button>
              </div>
            </div>
          </section>
        </div>

        {/* Who can access */}
        <div className="space-y-6">
          <section>
            <div className="section-label">
              <div className="section-label-icon"><Lock /></div>
              {t('consent.who_sees_what', 'Who Sees What?')}
            </div>
            <div className="card space-y-4">
              <div className="flex gap-3">
                <User className="w-4 h-4 text-surface-400 mt-0.5" />
                <div><p className="text-sm font-medium text-surface-800">{t('consent.you', 'You')}</p><p className="text-[0.65rem] text-surface-500">{t('consent.everything', 'Everything')}</p></div>
              </div>
              <div className="flex gap-3">
                <Shield className="w-4 h-4 text-surface-400 mt-0.5" />
                <div><p className="text-sm font-medium text-surface-800">{t('consent.welfare_officer', 'Welfare Officer')}</p><p className="text-[0.65rem] text-surface-500">{t('consent.wo_desc', 'Only during active case reviews')}</p></div>
              </div>
              <div className="flex gap-3">
                <Users className="w-4 h-4 text-surface-400 mt-0.5" />
                <div><p className="text-sm font-medium text-surface-800">{t('consent.commander', 'Commander')}</p><p className="text-[0.65rem] text-surface-500">{t('consent.cmd_desc', 'Anonymized aggregates only')}</p></div>
              </div>
              <div className="flex gap-3">
                <Server className="w-4 h-4 text-surface-400 mt-0.5" />
                <div><p className="text-sm font-medium text-surface-800">{t('consent.admin', 'Admin')}</p><p className="text-[0.65rem] text-surface-500">{t('consent.admin_desc', 'Account management only')}</p></div>
              </div>
            </div>
          </section>

          {accessHistory.length > 0 && (
            <section>
              <div className="section-label">
                <div className="section-label-icon"><Clock /></div>
                {t('consent.recent_access', 'Recent Access')}
              </div>
              <div className="card space-y-3">
                {accessHistory.map((log, i) => (
                  <div key={i} className="flex gap-3">
                    <Eye className="w-3.5 h-3.5 text-surface-300 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-surface-800">{log.actor_role}</p>
                      <p className="text-[0.65rem] text-surface-500">{t('consent.viewed_case', 'Viewed your case')} • {formatDateTime(log.date)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
