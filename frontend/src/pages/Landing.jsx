import { Link } from 'react-router-dom';
import { Heart, ArrowRight, Users, ShieldCheck, Sprout } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function Landing() {
  const heroRef = useRef(null);
  const textRef = useRef(null);

  useEffect(() => {
    // Subtle fade-in on load
    const els = document.querySelectorAll('.land-fade');
    els.forEach((el, i) => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(18px)';
      setTimeout(() => {
        el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, 150 + i * 120);
    });
  }, []);

  return (
    <div className="land-root">
      {/* ─── HEADER ─── */}
      <header className="land-header">
        <div className="land-header-inner">
          <div className="land-logo">
            <div className="land-logo-icon">
              <Heart className="w-4.5 h-4.5 text-white" strokeWidth={2.2} />
            </div>
            <div className="land-logo-text">
              <span className="land-logo-name">SAATHI</span>
              <span className="land-logo-sub">Personnel Welfare Monitoring</span>
            </div>
          </div>

          {/* <nav className="land-nav">
            <a href="#how" className="land-nav-link">How it works</a>
            <a href="#privacy" className="land-nav-link">Privacy</a>
            <a href="#support" className="land-nav-link">Support</a>
          </nav> */}

          <div className="land-header-actions">
            <Link to="/login" className="land-btn-primary">Sign in <ArrowRight className="w-4 h-4" /></Link>
          </div>
        </div>
      </header>

      {/* ─── HERO ─── */}
      <section className="land-hero" ref={heroRef}>
        <div className="land-hero-bg">
          <img src="/images/hero.jpg" alt="" />
          <div className="land-hero-overlay" />
        </div>

        <div className="land-hero-content">
          <div className="land-hero-left land-fade">
            <div className="land-badge">
              <ShieldCheck className="w-3.5 h-3.5" />
              SIH 2026 Prototype
            </div>

            <h1 className="land-headline land-fade">
              Early welfare support,<br />
              <span className="land-headline-accent">built around people.</span>
            </h1>

            <p className="land-subtext land-fade">
              Identify changing workload and fatigue<br />patterns early.
            </p>

            <div className="land-hero-cta land-fade">
            </div>
          </div>

          <div className="land-hero-right land-fade">
            <div className="land-hero-words">
              <span>PEOPLE</span>
              <span>READINESS</span>
              <span>SAFER</span>
              <span>TOMORROW</span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── VALUES BAR ─── */}
      <section className="land-values land-fade">
        <div className="land-values-inner">
          <div className="land-value">
            <Users className="w-6 h-6" strokeWidth={1.5} />
            <div>
              <span className="land-value-title">People</span>
              <span className="land-value-sub">centred</span>
            </div>
          </div>
          <div className="land-value-sep" />
          <div className="land-value">
            <ShieldCheck className="w-6 h-6" strokeWidth={1.5} />
            <div>
              <span className="land-value-title">Privacy</span>
              <span className="land-value-sub">by design</span>
            </div>
          </div>
          <div className="land-value-sep" />
          <div className="land-value">
            <Sprout className="w-6 h-6" strokeWidth={1.5} />
            <div>
              <span className="land-value-title">Stronger</span>
              <span className="land-value-sub">tomorrow</span>
            </div>
          </div>
        </div>
      </section>


    </div>
  );
}
