import { Outlet } from 'react-router-dom';
import { Heart } from 'lucide-react';

export default function AuthLayout() {
  return (
    <div className="auth-root">
      {/* ─── LEFT PANEL ─── */}
      <div className="auth-left">
        <header className="auth-left-header">
          <div className="auth-logo">
            <div className="auth-logo-icon">
              <Heart className="w-4.5 h-4.5 text-white" strokeWidth={2.2} />
            </div>
            <div className="auth-logo-text">
              <span className="auth-logo-name">SAATHI</span>
              <span className="auth-logo-sub">Personnel Welfare Monitoring</span>
            </div>
          </div>
        </header>

        <div className="auth-left-content">
          <div className="auth-left-label">
            <span className="auth-left-line" />
            <span>SIH 2026 Prototype</span>
          </div>

          <h1 className="auth-left-headline">
            Welfare today for a<br />
            <span className="auth-left-accent">stronger tomorrow.</span>
          </h1>

          <div className="auth-left-words">
            <span>PEOPLE</span>
            <span>READINESS</span>
            <span>SAFER TOMORROW</span>
          </div>
          <div className="auth-left-dash" />
        </div>

        <div className="auth-left-gradient" />
      </div>

      {/* ─── RIGHT PANEL ─── */}
      <div className="auth-right">
        <div className="auth-right-header" />

        <div className="auth-right-content">
          <Outlet />
        </div>


      </div>
    </div>
  );
}
