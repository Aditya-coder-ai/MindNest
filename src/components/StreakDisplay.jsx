import { getCurrentStreak, getStreakData } from '../data/streaks.js';
import './StreakDisplay.css';

/**
 * Streak display widget showing current and longest streaks.
 * Includes a visual flame animation and motivational messaging.
 */
export default function StreakDisplay() {
  const current = getCurrentStreak();
  const data = getStreakData();

  // Determine flame intensity based on streak length
  const intensity = current >= 30 ? 'blazing' : current >= 7 ? 'strong' : current >= 3 ? 'warm' : 'spark';

  return (
    <div className="streak-display" id="streak-display">
      <div className="streak-main">
        <div className={`streak-flame-wrap streak-${intensity}`}>
          <span className="streak-flame-emoji">
            {current >= 30 ? '🔥' : current >= 7 ? '🔥' : current >= 3 ? '🌟' : '✨'}
          </span>
          {current >= 3 && <div className="streak-flame-glow" />}
        </div>
        <div className="streak-info">
          <span className="streak-count">{current}</span>
          <span className="streak-label">day streak</span>
        </div>
      </div>

      <div className="streak-stats">
        <div className="streak-stat">
          <span className="streak-stat-value">{data.longestStreak || 0}</span>
          <span className="streak-stat-label">Best</span>
        </div>
        <div className="streak-divider" />
        <div className="streak-stat">
          <span className="streak-stat-value">{data.totalDays || 0}</span>
          <span className="streak-stat-label">Total</span>
        </div>
      </div>

      {current === 0 && (
        <p className="streak-message streak-encourage">
          Start journaling today to begin your streak! 🌱
        </p>
      )}
      {current >= 1 && current < 3 && (
        <p className="streak-message streak-growing">
          Keep going! You're building a great habit 💪
        </p>
      )}
      {current >= 3 && current < 7 && (
        <p className="streak-message streak-growing">
          Amazing consistency! {7 - current} more day{7 - current !== 1 ? 's' : ''} to a full week! 🌿
        </p>
      )}
      {current >= 7 && (
        <p className="streak-message streak-fire">
          You're on fire! Your wellness journey is thriving! 🦋
        </p>
      )}
    </div>
  );
}
