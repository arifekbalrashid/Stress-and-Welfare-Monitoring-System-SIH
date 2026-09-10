import { useState, useEffect, useRef } from 'react';
import { Globe, Check } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' },
];

export default function LanguageMenu() {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (langCode) => {
    i18n.changeLanguage(langCode);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={menuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="account-avatar flex items-center justify-center bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100"
        title="Change Language"
      >
        <Globe className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="account-menu">
          <div className="py-1">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleSelect(lang.code)}
                className="account-menu-item flex items-center justify-between w-full"
              >
                <span>{lang.label}</span>
                {i18n.resolvedLanguage === lang.code && <Check className="w-4 h-4 text-blue-600" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
