import { useState, useEffect, useRef, useMemo } from 'react';
import { setUserName } from '../store.js';
import logo from '../assets/logo.png';
import './WelcomePage.css';

const generateParticles = () => Array.from({ length: 30 }, (_, i) => ({
  id: i,
  left: Math.random() * 100,
  size: Math.random() * 6 + 2,
  delay: Math.random() * 12,
  duration: Math.random() * 10 + 12,
  opacity: Math.random() * 0.5 + 0.15,
}));

/* ---------- floating particles ---------- */
function Particles() {
  const particles = useMemo(() => generateParticles(), []);

  return (
    <div className="particles" aria-hidden="true">
      {particles.map(p => (
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

/* ---------- Welcome Page ---------- */
export default function WelcomePage({ onStart }) {
  const [name, setName] = useState('');
  const [step, setStep] = useState(0); // 0 = splash, 1 = name input
  const inputRef = useRef(null);

  useEffect(() => {
    if (step === 1 && inputRef.current) inputRef.current.focus();
  }, [step]);

  const handleGetStarted = () => setStep(1);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = name.trim() || 'Friend';
    setUserName(trimmed);
    onStart();
  };

  return (
    <div className="welcome" id="welcome-page">
      <Particles />

      {/* Breathing orbs */}
      <div className="orb orb-1" aria-hidden="true" />
      <div className="orb orb-2" aria-hidden="true" />
      <div className="orb orb-3" aria-hidden="true" />

      <div className="welcome-content">
        {step === 0 ? (
          <div className="welcome-splash fade-in">
            <div className="welcome-logo-wrap">
              <img src={logo} alt="MindNest Logo" className="welcome-logo-img" />
            </div>
            <h1 className="welcome-title slide-up stagger-1">MindNest</h1>
            <p className="welcome-tagline slide-up stagger-2">
              Track. Understand. Grow.
            </p>
            <p className="welcome-sub slide-up stagger-3">
              Your personal AI mood companion — journal your thoughts, understand your emotions, and grow every day.
            </p>
            <button
              className="btn-primary welcome-btn slide-up stagger-4"
              onClick={handleGetStarted}
              id="get-started-btn"
            >
              Get Started
              <span className="btn-arrow">→</span>
            </button>
          </div>
        ) : (
          <form className="welcome-form fade-in" onSubmit={handleSubmit}>
            <div className="welcome-logo-wrap welcome-logo-small">
              <img src={logo} alt="MindNest" className="welcome-logo-img" />
            </div>
            <h2 className="welcome-form-title slide-up stagger-1">
              What should we call you?
            </h2>
            <p className="welcome-form-sub slide-up stagger-2">
              Let's personalize your experience
            </p>
            <input
              ref={inputRef}
              className="welcome-input slide-up stagger-3"
              type="text"
              placeholder="Enter your name…"
              value={name}
              onChange={e => setName(e.target.value)}
              maxLength={30}
              id="name-input"
            />
            <button
              type="submit"
              className="btn-primary welcome-btn slide-up stagger-4"
              id="continue-btn"
            >
              Continue
              <span className="btn-arrow">→</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
