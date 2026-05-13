import { useState, useRef, useEffect, useMemo } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  updateProfile,
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth';
import { auth } from '../firebase.js';
import logo from '../assets/logo.png';
import mascot from '../assets/mascot.png';
import './AuthPage.css';

/* ---------- floating particles (reused from WelcomePage) ---------- */
const generateParticles = () =>
  Array.from({ length: 25 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    size: Math.random() * 6 + 2,
    delay: Math.random() * 12,
    duration: Math.random() * 10 + 12,
    opacity: Math.random() * 0.5 + 0.15,
  }));

function Particles() {
  const particles = useMemo(() => generateParticles(), []);
  return (
    <div className="particles" aria-hidden="true">
      {particles.map((p) => (
        <span
          key={p.id}
          className="particle"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.duration}s`,
            opacity: p.opacity,
          }}
        />
      ))}
    </div>
  );
}

/* ---------- Auth Page ---------- */
export default function AuthPage() {
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const emailRef = useRef(null);

  useEffect(() => {
    emailRef.current?.focus();
  }, [mode]);

  const toggleMode = () => {
    setMode((m) => (m === 'login' ? 'signup' : 'login'));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'signup') {
        const cred = await createUserWithEmailAndPassword(auth, email, password);
        if (name.trim()) {
          await updateProfile(cred.user, { displayName: name.trim() });
        }
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
      // Auth state listener in App.jsx will handle the redirect
    } catch (err) {
      const code = err.code || '';
      if (code === 'auth/user-not-found' || code === 'auth/invalid-credential')
        setError('Invalid email or password');
      else if (code === 'auth/email-already-in-use')
        setError('An account with this email already exists');
      else if (code === 'auth/weak-password')
        setError('Password must be at least 6 characters');
      else if (code === 'auth/invalid-email')
        setError('Please enter a valid email address');
      else setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
    } catch (err) {
      if (err.code !== 'auth/popup-closed-by-user') {
        setError('Google sign-in failed. Try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page" id="auth-page">
      <Particles />

      {/* Breathing orbs */}
      <div className="orb orb-1" aria-hidden="true" />
      <div className="orb orb-2" aria-hidden="true" />
      <div className="orb orb-3" aria-hidden="true" />

      {/* Mascot — left side (pointing right toward form) */}
      <div className="auth-mascot auth-mascot-left" aria-hidden="true">
        <img src={mascot} alt="" className="mascot-img" />
      </div>

      {/* Mascot — right side (flipped, pointing left toward form) */}
      <div className="auth-mascot auth-mascot-right" aria-hidden="true">
        <img src={mascot} alt="" className="mascot-img" />
      </div>

      <div className="auth-container">
        {/* Logo + Brand */}
        <div className="auth-brand fade-in">
          <div className="auth-logo-wrap">
            <img src={logo} alt="MindNest Logo" className="auth-logo-img" />
          </div>
          <h1 className="auth-title slide-up stagger-1">MindNest</h1>
          <p className="auth-tagline slide-up stagger-2">
            {mode === 'login'
              ? 'Welcome back to your safe space'
              : 'Begin your journey of self-discovery'}
          </p>
        </div>

        {/* Auth Card */}
        <div className="auth-card glass slide-up stagger-3" id="auth-card">
          <div className="auth-tabs">
            <button
              className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
              onClick={() => { setMode('login'); setError(''); }}
              id="login-tab"
            >
              Sign In
            </button>
            <button
              className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
              onClick={() => { setMode('signup'); setError(''); }}
              id="signup-tab"
            >
              Sign Up
            </button>
            <div className={`auth-tab-indicator ${mode === 'signup' ? 'right' : ''}`} />
          </div>

          <form className="auth-form" onSubmit={handleSubmit}>
            {/* Name field — signup only */}
            {mode === 'signup' && (
              <div className="auth-field slide-up">
                <label className="auth-label" htmlFor="auth-name">
                  <span className="auth-field-icon">👤</span> Display Name
                </label>
                <input
                  id="auth-name"
                  type="text"
                  className="auth-input"
                  placeholder="What should we call you?"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={30}
                />
              </div>
            )}

            {/* Email */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-email">
                <span className="auth-field-icon">✉️</span> Email
              </label>
              <input
                ref={emailRef}
                id="auth-email"
                type="email"
                className="auth-input"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            {/* Password */}
            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-password">
                <span className="auth-field-icon">🔒</span> Password
              </label>
              <div className="auth-password-wrap">
                <input
                  id="auth-password"
                  type={showPassword ? 'text' : 'password'}
                  className="auth-input"
                  placeholder={mode === 'signup' ? 'Min. 6 characters' : 'Enter your password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  className="auth-toggle-pw"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="auth-error scale-in" id="auth-error">
                <span>⚠️</span> {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              className="btn-primary auth-submit"
              disabled={loading}
              id="auth-submit-btn"
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  {mode === 'login' ? 'Signing in…' : 'Creating account…'}
                </>
              ) : (
                <>
                  {mode === 'login' ? '🔑 Sign In' : '🚀 Create Account'}
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="auth-divider">
            <span>or continue with</span>
          </div>

          {/* Google Sign-In */}
          <button
            className="auth-google-btn"
            onClick={handleGoogleSignIn}
            disabled={loading}
            id="google-signin-btn"
          >
            <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Google
          </button>

          {/* Toggle mode link */}
          <p className="auth-switch">
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button className="auth-switch-btn" onClick={toggleMode}>
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
