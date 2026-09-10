import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROLE_ROUTES } from '../utils/constants';
import { Heart, AlertCircle, User, Lock, Eye, EyeOff, ArrowRight, ShieldCheck } from 'lucide-react';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password.trim()) {
      setError('Please enter your credentials.');
      return;
    }
    try {
      const user = await login(username, password);
      navigate(ROLE_ROUTES[user.role] || '/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials.');
    }
  };

  return (
    <div className="login-card">
      {/* Card Header */}
      <div className="login-card-header">
        <div className="login-card-logo">
          <div className="login-card-logo-icon">
            <Heart className="w-4 h-4 text-white" strokeWidth={2.2} />
          </div>
          <div className="login-card-logo-text">
            <span className="login-card-logo-name">SAATHI</span>
            <span className="login-card-logo-sub">Personnel Welfare Monitoring</span>
          </div>
        </div>
      </div>



      {error && (
        <div className="login-error">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} id="login-form">
        <div className="login-fields">
          <div className="login-field">
            <label htmlFor="username" className="login-label">Personnel ID</label>
            <div className="login-input-wrap">
              <User className="login-input-icon" />
              <input
                id="username"
                type="text"
                className="login-input"
                placeholder="Enter your personnel ID"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
              />
            </div>
          </div>

          <div className="login-field">
            <label htmlFor="password" className="login-label">Password</label>
            <div className="login-input-wrap">
              <Lock className="login-input-icon" />
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className="login-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="login-eye"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
              </button>
            </div>
            <div className="login-forgot">
              <a href="#">Forgot password?</a>
            </div>
          </div>

          <button type="submit" className="login-submit" disabled={loading} id="login-submit">
            {loading ? 'Signing in…' : 'Sign in'} {!loading && <ArrowRight className="w-4 h-4" />}
          </button>

        </div>
      </form>

      {/* Demo credentials */}
      <div className="login-demo">
        <p className="login-demo-title">Demo</p>
        <div className="login-demo-grid">
          <span>Personnel:</span><span className="font-mono">p1024 / demo1234</span>
          <span>Welfare:</span><span className="font-mono">wo_sharma / demo1234</span>
          <span>Commander:</span><span className="font-mono">cmd_singh / demo1234</span>
          <span>Admin:</span><span className="font-mono">admin / admin1234</span>
        </div>
      </div>
    </div>
  );
}
