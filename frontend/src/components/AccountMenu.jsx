import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { personnelAPI } from '../services/api';
import { ROLES } from '../utils/constants';
import { useTranslation } from 'react-i18next';

export default function AccountMenu() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [personnelData, setPersonnelData] = useState(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (user?.role === ROLES.PERSONNEL) {
      personnelAPI.getMe()
        .then(res => setPersonnelData(res.data.data))
        .catch(() => {});
    }
  }, [user]);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNavigation = (path) => {
    setIsOpen(false);
    navigate(path);
  };

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
    navigate('/login');
  };

  const initials = personnelData 
    ? `${personnelData.first_name[0] || ''}${personnelData.last_name[0] || ''}`.toUpperCase()
    : user?.username?.substring(0, 2).toUpperCase() || 'U';

  const displayName = personnelData 
    ? `${personnelData.first_name} ${personnelData.last_name}`
    : user?.username;

  return (
    <div className="relative" ref={menuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="account-avatar"
        aria-label="Account menu"
      >
        {initials || 'U'}
      </button>

      {isOpen && (
        <div className="account-menu">
          {/* Identity Block */}
          <div className="account-menu-identity">
            <p className="account-menu-name">{displayName}</p>
            {personnelData ? (
              <p className="account-menu-role">{personnelData.service_id}</p>
            ) : (
              <p className="account-menu-role">{user?.role}</p>
            )}
          </div>

          {/* Navigation Links */}
          {user?.role === ROLES.PERSONNEL && (
            <div className="py-1">
              <button 
                onClick={() => handleNavigation('/p/profile')}
                className="account-menu-item"
              >
                {t('account.profile')}
              </button>
              <button 
                onClick={() => handleNavigation('/p/profile')}
                className="account-menu-item"
              >
                {t('account.change_password')}
              </button>
              <button 
                onClick={() => handleNavigation('/p/consent')}
                className="account-menu-item"
              >
                {t('account.privacy_consent')}
              </button>
            </div>
          )}

          {user?.role === ROLES.PERSONNEL && <div className="account-menu-divider" />}

          {/* Sign Out */}
          <div className="py-1">
            <button 
              onClick={handleLogout}
              className="account-menu-item account-menu-item-danger"
            >
              {t('account.sign_out')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
