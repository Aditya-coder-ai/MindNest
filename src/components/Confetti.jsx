import { useEffect, useState, useMemo } from 'react';
import './Confetti.css';

/**
 * Confetti celebration component for streak milestones.
 * Renders colorful confetti particles that fall and fade out.
 */
export default function Confetti({ active, duration = 4000, onComplete }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (active) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onComplete?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [active, duration, onComplete]);

  const pieces = useMemo(() => {
    if (!active) return [];
    return Array.from({ length: 80 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 1.5,
      fallDuration: Math.random() * 2 + 2.5,
      size: Math.random() * 8 + 4,
      color: [
        '#a78bfa', '#c4b5fd', '#f0abfc', '#fda4af',
        '#fbbf24', '#34d399', '#7dd3fc', '#fb923c',
        '#e8a4a4', '#6dd0bc', '#b794d6', '#f5c4be',
      ][Math.floor(Math.random() * 12)],
      rotation: Math.random() * 360,
      rotSpeed: (Math.random() - 0.5) * 720,
      drift: (Math.random() - 0.5) * 100,
      shape: ['square', 'circle', 'strip'][Math.floor(Math.random() * 3)],
    }));
  }, [active]);

  if (!visible) return null;

  return (
    <div className="confetti-container" aria-hidden="true">
      {pieces.map(p => (
        <div
          key={p.id}
          className={`confetti-piece confetti-${p.shape}`}
          style={{
            left: `${p.left}%`,
            width: p.shape === 'strip' ? `${p.size * 0.4}px` : `${p.size}px`,
            height: p.shape === 'strip' ? `${p.size * 2}px` : `${p.size}px`,
            backgroundColor: p.color,
            animationDelay: `${p.delay}s`,
            animationDuration: `${p.fallDuration}s`,
            '--drift': `${p.drift}px`,
            '--rotation': `${p.rotation}deg`,
            '--rot-speed': `${p.rotSpeed}deg`,
          }}
        />
      ))}
    </div>
  );
}
