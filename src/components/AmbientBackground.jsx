import { useMemo } from 'react';
import './AmbientBackground.css';

export default function AmbientBackground() {
  // Generate random static values so they don't change on re-renders
  const stars = useMemo(() => Array.from({ length: 15 }).map((_, i) => ({
    id: `star-${i}`,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    delay: `${Math.random() * 4}s`,
    size: `${Math.random() * 2 + 1}px`
  })), []);

  const bubbles = useMemo(() => Array.from({ length: 8 }).map((_, i) => ({
    id: `bubble-${i}`,
    left: `${Math.random() * 100}%`,
    delay: `${Math.random() * 8}s`,
    duration: `${Math.random() * 10 + 15}s`,
    size: `${Math.random() * 40 + 20}px`
  })), []);

  const leaves = useMemo(() => Array.from({ length: 6 }).map((_, i) => ({
    id: `leaf-${i}`,
    left: `${Math.random() * 100}%`,
    delay: `${Math.random() * 10}s`,
    duration: `${Math.random() * 15 + 20}s`
  })), []);

  return (
    <div className="ambient-bg" aria-hidden="true">
      {/* 1. Meditation Breathing Orb (center backdrop glow) */}
      <div className="ambient-meditation-orb" />

      {/* 2. Floating Clouds */}
      <div className="ambient-cloud cloud-1">☁️</div>
      <div className="ambient-cloud cloud-2">☁️</div>
      <div className="ambient-cloud cloud-3">☁️</div>

      {/* 3. Glowing Particles & Stars */}
      {stars.map((star) => (
        <div
          key={star.id}
          className="ambient-star"
          style={{
            left: star.left,
            top: star.top,
            width: star.size,
            height: star.size,
            animationDelay: star.delay
          }}
        />
      ))}

      {/* 4. Soft Bubbles */}
      {bubbles.map((bubble) => (
        <div
          key={bubble.id}
          className="ambient-bubble"
          style={{
            left: bubble.left,
            width: bubble.size,
            height: bubble.size,
            animationDelay: bubble.delay,
            animationDuration: bubble.duration
          }}
        />
      ))}

      {/* 5. Tiny Floating Leaves */}
      {leaves.map((leaf) => (
        <div
          key={leaf.id}
          className="ambient-leaf"
          style={{
            left: leaf.left,
            animationDelay: leaf.delay,
            animationDuration: leaf.duration
          }}
        >
          🍃
        </div>
      ))}

      {/* 6. Sparkles */}
      <div className="ambient-sparkle sp-1">✨</div>
      <div className="ambient-sparkle sp-2">✨</div>
      <div className="ambient-sparkle sp-3">✨</div>
      <div className="ambient-sparkle sp-4">✨</div>

      {/* 7. Pastel Gradient Orbs */}
      <div className="ambient-pastel-orb pastel-orb-1" />
      <div className="ambient-pastel-orb pastel-orb-2" />
      <div className="ambient-pastel-orb pastel-orb-3" />
    </div>
  );
}
