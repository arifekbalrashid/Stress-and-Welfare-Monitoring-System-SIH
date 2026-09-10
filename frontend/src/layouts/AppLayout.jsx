import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROLES, DISCLAIMER_TEXT } from '../utils/constants';
import {
  LayoutDashboard, ClipboardCheck, Shield, HelpCircle, User,
  Users, FileUp, UserCog, Cpu, ScrollText, BarChart3, Heart, Menu, X, Globe
} from 'lucide-react';
import AccountMenu from '../components/AccountMenu';
import LanguageMenu from '../components/LanguageMenu';

const NAV_ITEMS = {
  [ROLES.PERSONNEL]: [
    { to: '/p/dashboard', label: 'nav.dashboard', icon: LayoutDashboard },
    { to: '/p/checkin', label: 'nav.checkin', icon: ClipboardCheck },
    { to: '/p/support', label: 'nav.support', icon: HelpCircle },
  ],
  [ROLES.WELFARE_OFFICER]: [
    { to: '/w/cases', label: 'nav.cases', icon: ClipboardCheck },
    { to: '/w/support-requests', label: 'nav.support_requests', icon: HelpCircle },
  ],
  [ROLES.COMMANDER]: [
    { to: '/c/overview', label: 'nav.unit_overview', icon: BarChart3 },
    { to: '/c/roster', label: 'nav.unit_roster', icon: Users },
  ],
  [ROLES.ADMIN]: [
    { to: '/a/personnel', label: 'nav.personnel_units', icon: Users },
    { to: '/a/import', label: 'nav.data_import', icon: FileUp },
    { to: '/a/users', label: 'nav.user_management', icon: UserCog },
    { to: '/a/audit', label: 'nav.audit_logs', icon: ScrollText },
  ],
};

const getPageTitleKey = (pathname) => {
  const routes = {
    '/p/dashboard': 'nav.dashboard',
    '/p/checkin': 'nav.checkin',
    '/p/support': 'nav.support',
    '/p/profile': 'account.profile',
    '/p/consent': 'account.privacy_consent',
    '/w/cases': 'nav.cases',
    '/w/support-requests': 'nav.support_requests',
    '/c/overview': 'nav.unit_overview',
    '/c/roster': 'nav.unit_roster',
    '/a/personnel': 'nav.personnel_units',
    '/a/import': 'nav.data_import',
    '/a/users': 'nav.user_management',
    '/a/audit': 'nav.audit_logs'
  };
  // Handle dynamic routes like /w/cases/:id
  if (pathname.startsWith('/w/cases/')) return 'nav.cases';
  return routes[pathname] || '';
};

export default function AppLayout() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const location = useLocation();
  const navItems = NAV_ITEMS[user?.role] || [];
  const pageTitleKey = getPageTitleKey(location.pathname);
  const pageTitle = pageTitleKey ? t(pageTitleKey) : '';
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      {/* Mobile sidebar overlay */}
      <div
        className={`app-sidebar-overlay ${sidebarOpen ? 'sidebar-open' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`app-sidebar ${sidebarOpen ? 'sidebar-open' : ''}`}>
        {/* Logo */}
        <div className="app-sidebar-brand">
          <div className="app-sidebar-logo">
            <Heart className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="app-sidebar-name">SAATHI</h1>
            <p className="app-sidebar-sub">Welfare Monitoring</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="app-sidebar-nav">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `app-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <Icon className="w-[18px] h-[18px]" />
              <span>{t(label)}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main container */}
      <div className="app-main">
        {/* Global Header */}
        <header className="app-header">
          <div className="app-header-left">
            <button
              className="app-sidebar-toggle"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              aria-label="Toggle navigation"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
          <div className="app-header-right flex items-center gap-3">
            <LanguageMenu />
            <AccountMenu />
          </div>
        </header>

        {/* Page Content */}
        <main className="app-content">
          <div className="app-content-container fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
