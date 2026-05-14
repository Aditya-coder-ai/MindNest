/* ===================================================================
   MindNest — Streak Tracking System
   Tracks journal entry streaks with localStorage persistence
   =================================================================== */

const STREAK_KEY = 'mindnest_streak';

/**
 * Streak data shape:
 * {
 *   currentStreak: number,
 *   longestStreak: number,
 *   lastEntryDate: string (YYYY-MM-DD),
 *   totalDays: number,
 * }
 */

function getToday() {
  return new Date().toISOString().split('T')[0]; // YYYY-MM-DD
}

function getYesterday() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().split('T')[0];
}

/**
 * Load streak data from localStorage.
 */
export function getStreakData() {
  try {
    const raw = localStorage.getItem(STREAK_KEY);
    if (!raw) return { currentStreak: 0, longestStreak: 0, lastEntryDate: null, totalDays: 0 };
    return JSON.parse(raw);
  } catch {
    return { currentStreak: 0, longestStreak: 0, lastEntryDate: null, totalDays: 0 };
  }
}

/**
 * Save streak data to localStorage.
 */
function saveStreakData(data) {
  localStorage.setItem(STREAK_KEY, JSON.stringify(data));
}

/**
 * Record that an entry was made today.
 * Returns { streakData, isMilestone, milestoneValue } for celebration logic.
 */
export function recordStreak() {
  const today = getToday();
  const data = getStreakData();

  // Already recorded today — no change
  if (data.lastEntryDate === today) {
    return { streakData: data, isMilestone: false, milestoneValue: 0 };
  }

  const yesterday = getYesterday();
  const prevStreak = data.currentStreak;

  if (data.lastEntryDate === yesterday) {
    // Consecutive day → increment
    data.currentStreak += 1;
  } else if (data.lastEntryDate === null) {
    // First ever entry
    data.currentStreak = 1;
  } else {
    // Streak broken → reset to 1
    data.currentStreak = 1;
  }

  data.lastEntryDate = today;
  data.totalDays = (data.totalDays || 0) + 1;
  data.longestStreak = Math.max(data.longestStreak, data.currentStreak);

  saveStreakData(data);

  // Check for milestone celebrations
  const milestones = [3, 7, 14, 21, 30, 50, 75, 100, 150, 200, 365];
  const isMilestone = milestones.includes(data.currentStreak);

  return {
    streakData: data,
    isMilestone,
    milestoneValue: isMilestone ? data.currentStreak : 0,
  };
}

/**
 * Get the current streak, adjusting for broken streaks.
 * (e.g., if lastEntry was 2+ days ago, streak resets to 0)
 */
export function getCurrentStreak() {
  const data = getStreakData();
  const today = getToday();
  const yesterday = getYesterday();

  if (data.lastEntryDate === today || data.lastEntryDate === yesterday) {
    return data.currentStreak;
  }

  // Streak has been broken
  return 0;
}

/**
 * Get milestone message for a given streak value.
 */
export function getMilestoneMessage(days) {
  const messages = {
    3: "🌱 3-day streak! You're building a beautiful habit!",
    7: "🌿 One full week! Your consistency is inspiring!",
    14: "🌸 Two weeks strong! You're truly committed to your wellness!",
    21: "🦋 21 days — they say it takes this long to form a habit! You did it!",
    30: "🏆 One month! You are a wellness champion!",
    50: "⭐ 50 days! Half a century of self-care. Incredible!",
    75: "💎 75 days! Your dedication is truly remarkable!",
    100: "🎉 100 DAYS! A hundred days of caring for yourself. You're amazing!",
    150: "🌟 150 days! You've made self-reflection a way of life!",
    200: "👑 200 days! You're an absolute inspiration!",
    365: "🎊 ONE FULL YEAR! 365 days of mindful journaling. Legendary!",
  };
  return messages[days] || `🔥 ${days}-day streak! Keep going!`;
}
