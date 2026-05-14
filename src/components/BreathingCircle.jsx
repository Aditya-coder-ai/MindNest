import { useState, useEffect, useCallback } from 'react';
import './BreathingCircle.css';

const PHASES = [
  { label: 'Breathe In', duration: 4000, scale: 1.3 },
  { label: 'Hold', duration: 4000, scale: 1.3 },
  { label: 'Breathe Out', duration: 6000, scale: 1 },
  { label: 'Rest', duration: 2000, scale: 1 },
];

/**
 * Breathing circle animation for guided meditation.
 * Uses a 4-4-6-2 breathing pattern.
 */
export default function BreathingCircle({ compact = false }) {
  const [isActive, setIsActive] = useState(false);
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [cycles, setCycles] = useState(0);

  const phase = PHASES[phaseIndex];

  const advancePhase = useCallback(() => {
    setPhaseIndex(prev => {
      const next = (prev + 1) % PHASES.length;
      if (next === 0) setCycles(c => c + 1);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!isActive) return;
    const timer = setTimeout(advancePhase, phase.duration);
    return () => clearTimeout(timer);
  }, [isActive, phaseIndex, phase.duration, advancePhase]);

  const handleToggle = () => {
    if (isActive) {
      setIsActive(false);
      setPhaseIndex(0);
      setCycles(0);
    } else {
      setIsActive(true);
      setPhaseIndex(0);
      setCycles(0);
    }
  };

  return (
    <div className={`breathing-widget ${compact ? 'breathing-compact' : ''}`}>
      <div className="breathing-circle-container" onClick={handleToggle}>
        <div
          className={`breathing-circle ${isActive ? 'breathing-active' : ''}`}
          style={{
            transform: isActive ? `scale(${phase.scale})` : 'scale(1)',
            transition: `transform ${phase.duration}ms ease-in-out`,
          }}
        >
          <div className="breathing-inner-ring" />
          <div className="breathing-core">
            {isActive ? (
              <span className="breathing-label">{phase.label}</span>
            ) : (
              <span className="breathing-label breathing-start">Start</span>
            )}
          </div>
        </div>
        {/* Ripple rings */}
        {isActive && (
          <>
            <div className="breathing-ripple ripple-1" style={{ animationDuration: `${phase.duration}ms` }} />
            <div className="breathing-ripple ripple-2" style={{ animationDuration: `${phase.duration * 1.5}ms` }} />
          </>
        )}
      </div>
      {isActive && (
        <div className="breathing-info fade-in">
          <span className="breathing-cycles">{cycles} cycle{cycles !== 1 ? 's' : ''}</span>
          <span className="breathing-tap">tap to stop</span>
        </div>
      )}
      {!isActive && (
        <p className="breathing-hint fade-in">Tap to begin breathing exercise</p>
      )}
    </div>
  );
}
