import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { personnelAPI } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { User } from 'lucide-react';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    personnelAPI.getMe()
      .then(res => setProfile(res.data.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div>
      <div className="page-header"><h1 className="page-title">Profile</h1></div>
      <div className="space-y-6">
        <div className="skeleton h-24 w-full rounded-[14px]" />
        <div className="skeleton h-48 w-full rounded-[14px]" />
      </div>
    </div>
  );

  if (error || !profile) return (
    <div className="py-10 text-center">
      <p className="text-surface-600 mb-4 text-sm">Unable to load personnel information.</p>
      <button onClick={() => window.location.reload()} className="btn btn-secondary px-6">
        Try again
      </button>
    </div>
  );

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Profile</h1>
        <p className="page-subtitle">Manage your personnel information and account settings.</p>
      </div>

      <div className="space-y-8">
        
        {/* PERSONNEL INFORMATION */}
        <section>
          <h2 className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-3">Personnel Information</h2>
          <div className="card">
            {/* Identity Block */}
            <div className="flex items-center gap-5 pb-5 border-b border-surface-100">
              <div className="w-14 h-14 rounded-full bg-surface-100 flex items-center justify-center shrink-0 border border-surface-200">
                <User className="w-6 h-6 text-surface-400" />
              </div>
              <div>
                <p className="text-lg font-semibold text-surface-900">{profile.first_name} {profile.last_name}</p>
                <p className="text-sm text-surface-600 mt-0.5">{profile.rank} &middot; {profile.service_id} &middot; {profile.unit_name || 'No Unit'}</p>
              </div>
            </div>

            {/* Metadata Grid */}
            <div className="pt-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-5 gap-x-12">
                <div>
                  <p className="text-[0.8rem] text-surface-500 mb-0.5">Name</p>
                  <p className="text-[0.95rem] font-medium text-surface-900">{profile.first_name} {profile.last_name}</p>
                </div>
                <div>
                  <p className="text-[0.8rem] text-surface-500 mb-0.5">Service ID</p>
                  <p className="text-[0.95rem] font-medium text-surface-900">{profile.service_id}</p>
                </div>
                <div>
                  <p className="text-[0.8rem] text-surface-500 mb-0.5">Rank</p>
                  <p className="text-[0.95rem] font-medium text-surface-900">{profile.rank}</p>
                </div>
                <div>
                  <p className="text-[0.8rem] text-surface-500 mb-0.5">Unit</p>
                  <p className="text-[0.95rem] font-medium text-surface-900">{profile.unit_name || '—'}</p>
                </div>
                <div>
                  <p className="text-[0.8rem] text-surface-500 mb-0.5">Date of joining</p>
                  <p className="text-[0.95rem] font-medium text-surface-900">{profile.date_of_joining || '—'}</p>
                </div>
              </div>
              
              <div className="mt-6 pt-5 border-t border-surface-100">
                <p className="text-xs text-surface-400">Personnel information is managed through authorized organizational records.</p>
              </div>
            </div>
          </div>
        </section>



      </div>
    </div>
  );
}
