/* =========================================================
   MindNest — local-first data helpers (localStorage)
   + Real AI Backend Integration (Python ML Model)
   + Firebase Firestore Integration (Production DB)
   + Per-User Data Isolation (Firebase Auth UID)
   ========================================================= */

import { db, auth } from './firebase.js';
import { collection, addDoc, getDocs, query, orderBy, doc, setDoc, getDoc } from 'firebase/firestore';
import { updateProfile } from 'firebase/auth';

const STORAGE_KEY = 'mindnest_entries';
const NAME_KEY = 'mindnest_user_name';

/* ─── AI Backend config ─── */
const AI_API_URL = 'http://localhost:5000/api';
let _aiAvailable = null; // null = unknown, true/false = checked

/**
 * Get the currently authenticated user's UID.
 * Returns null if no user is signed in.
 */
function getCurrentUserId() {
  return auth.currentUser?.uid || null;
}

/**
 * Shape of an entry:
 * {
 *   id: string,
 *   date: string (ISO),
 *   text: string,
 *   mood: string (emoji key),
 *   moodLabel: string,
 *   positivity: number (0-100),
 *   stressLevel: string,
 *   insight: string,
 *   aiPowered: boolean,
 *   confidence: number,
 * }
 */

export async function getAllEntries() {
  const uid = getCurrentUserId();
  if (!uid) return [];

  try {
    // Each user's entries are stored under users/{uid}/entries
    const q = query(collection(db, "users", uid, "entries"), orderBy("date", "desc"));
    const querySnapshot = await getDocs(q);
    const entries = [];
    querySnapshot.forEach((doc) => {
      entries.push({ id: doc.id, ...doc.data() });
    });
    return entries;
  } catch (e) {
    console.error("Failed to fetch from Firestore, falling back to local", e);
    // Fallback to localStorage (user-scoped key)
    try {
      return JSON.parse(localStorage.getItem(`${STORAGE_KEY}_${uid}`) || '[]');
    } catch {
      return [];
    }
  }
}

export async function saveEntry(entry) {
  const uid = getCurrentUserId();
  if (!uid) {
    console.error("No user signed in — cannot save entry");
    return [];
  }

  const newEntry = { ...entry, date: new Date().toISOString() };
  
  try {
    // Save under users/{uid}/entries
    await addDoc(collection(db, "users", uid, "entries"), newEntry);
    return await getAllEntries(); // Get updated list from DB
  } catch (e) {
    console.error("Failed to save to Firestore, falling back to local", e);
    // Fallback to localStorage (user-scoped key)
    const entries = await getAllEntries();
    entries.unshift({ ...newEntry, id: crypto.randomUUID() });
    localStorage.setItem(`${STORAGE_KEY}_${uid}`, JSON.stringify(entries));
    return entries;
  }
}

export function getUserName() {
  // Prefer Firebase Auth displayName, fallback to localStorage
  if (auth.currentUser?.displayName) {
    return auth.currentUser.displayName;
  }
  return localStorage.getItem(NAME_KEY) || '';
}

export async function setUserName(name) {
  localStorage.setItem(NAME_KEY, name);
  // Also update Firebase Auth profile
  if (auth.currentUser) {
    try {
      await updateProfile(auth.currentUser, { displayName: name });
    } catch (e) {
      console.warn("Failed to update displayName in Firebase Auth:", e);
    }
  }
}

/**
 * Get the date when the current user's account was created.
 * Returns an ISO string or null if unavailable.
 */
export function getUserJoinDate() {
  return auth.currentUser?.metadata?.creationTime || null;
}


/* ===================================================================
   AI Backend — Real ML Model Integration
   =================================================================== */

/**
 * Check if the Python AI backend is running.
 * Caches the result so we only check once per session.
 */
export async function checkAIAvailable() {
  if (_aiAvailable !== null) return _aiAvailable;
  try {
    const res = await fetch(`${AI_API_URL}/health`, { signal: AbortSignal.timeout(2000) });
    const data = await res.json();
    _aiAvailable = data.status === 'healthy';
    console.log(`🌿 AI Backend: ${_aiAvailable ? '✅ Connected' : '❌ Unavailable'}`);
    if (_aiAvailable) {
      console.log(`   Model accuracy: ${data.model_accuracy}%`);
    }
  } catch {
    _aiAvailable = false;
    console.log('🌿 AI Backend: ❌ Offline — using local fallback');
  }
  return _aiAvailable;
}

/**
 * Analyze mood using the real AI backend (Python ML model).
 * Falls back to local keyword analysis if backend is unavailable.
 *
 * @param {string} text - Journal entry text
 * @param {string|null} selectedMood - User-selected mood emoji key
 * @returns {Promise<object>} - Analysis result
 */
export async function analyzeMoodAI(text, selectedMood = null) {
  const isAI = await checkAIAvailable();

  if (isAI && text.trim()) {
    try {
      const res = await fetch(`${AI_API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, selectedMood }),
        signal: AbortSignal.timeout(5000),
      });

      if (res.ok) {
        const data = await res.json();
        return {
          ...data,
          aiPowered: true,
        };
      }
    } catch (err) {
      console.warn('AI request failed, using local fallback:', err.message);
    }
  }

  // Fallback to local keyword-based analysis
  return analyzeMoodLocal(text, selectedMood);
}

/**
 * Send a wellness chat message to the backend.
 * Uses Gemini when configured and falls back to a server-side canned reply.
 *
 * @param {string} message
 * @param {Array<{role: string, text: string}>} history
 * @param {string} userName
 * @returns {Promise<{reply: string, aiPowered: boolean, provider: string}>}
 */
export async function sendWellnessMessage(message, history = [], userName = 'Friend') {
  const trimmedMessage = message.trim();
  if (!trimmedMessage) {
    throw new Error('Message cannot be empty');
  }

  const res = await fetch(`${AI_API_URL}/wellness-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: trimmedMessage,
      history,
      userName,
    }),
    signal: AbortSignal.timeout(10000),
  });

  if (!res.ok) {
    throw new Error(`Wellness chat request failed with status ${res.status}`);
  }

  return res.json();
}


/* ===================================================================
   Local Fallback — Keyword-based mood analysis
   (Used when Python AI backend is not running)
   =================================================================== */

const MOOD_KEYWORDS = {
  happy: ['happy', 'great', 'amazing', 'wonderful', 'fantastic', 'good', 'love', 'joy', 'awesome', 'excellent', 'delighted', 'cheerful', 'elated', 'proud', 'celebrate', 'smile', 'laugh'],
  sad: ['sad', 'unhappy', 'depressed', 'down', 'miss', 'cry', 'tears', 'heartbreak', 'gloomy', 'grief', 'miserable', 'sorrow', 'blue', 'melancholy', 'hopeless'],
  angry: ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'rage', 'hate', 'upset', 'outraged', 'livid', 'resentful', 'bitter', 'hostile'],
  anxious: ['anxious', 'worried', 'nervous', 'stressed', 'overwhelmed', 'panic', 'fear', 'tense', 'restless', 'uneasy', 'dread', 'apprehensive', 'exam', 'deadline', 'pressure'],
  calm: ['calm', 'peaceful', 'relaxed', 'serene', 'content', 'tranquil', 'chill', 'mindful', 'meditate', 'balanced', 'quiet', 'zen', 'soothing', 'rested'],
  tired: ['tired', 'exhausted', 'sleepy', 'drained', 'fatigue', 'burnt', 'burnout', 'weary', 'drowsy', 'lethargic', 'sluggish', 'sleep'],
  grateful: ['grateful', 'thankful', 'appreciate', 'blessed', 'gratitude', 'treasure', 'cherish', 'fortunate', 'kindness', 'generous', 'warmth', 'giving', 'thanks'],
  lonely: ['lonely', 'alone', 'isolated', 'abandoned', 'forgotten', 'invisible', 'disconnected', 'outsider', 'excluded', 'unwanted', 'neglected', 'rejected', 'solitude'],
  excited: ['excited', 'thrilled', 'eager', 'enthusiasm', 'adrenaline', 'pumped', 'stoked', 'buzzing', 'giddy', 'exhilarated', 'ecstatic', 'anticipation', 'adventure'],
  frustrated: ['frustrated', 'stuck', 'roadblock', 'failure', 'setback', 'defeated', 'blocked', 'helpless', 'powerless', 'obstacle', 'impossible', 'exasperated', 'aggravated'],
};

const MOOD_META = {
  happy:      { emoji: '😊', label: 'Happy',      color: '#fbbf24', positivityBase: 82 },
  sad:        { emoji: '😔', label: 'Sad',        color: '#60a5fa', positivityBase: 25 },
  angry:      { emoji: '😡', label: 'Angry',      color: '#fb7185', positivityBase: 18 },
  anxious:    { emoji: '😰', label: 'Anxious',    color: '#c084fc', positivityBase: 30 },
  calm:       { emoji: '😌', label: 'Calm',       color: '#34d399', positivityBase: 75 },
  tired:      { emoji: '😴', label: 'Tired',      color: '#94a3b8', positivityBase: 40 },
  grateful:   { emoji: '🙏', label: 'Grateful',   color: '#f0abfc', positivityBase: 88 },
  lonely:     { emoji: '🥀', label: 'Lonely',     color: '#7dd3fc', positivityBase: 20 },
  excited:    { emoji: '🎉', label: 'Excited',    color: '#fcd34d', positivityBase: 85 },
  frustrated: { emoji: '😤', label: 'Frustrated', color: '#fdba74', positivityBase: 22 },
};

const STRESS_LEVELS = {
  happy: 'Low',
  calm: 'Low',
  grateful: 'Low',
  excited: 'Low',
  sad: 'Moderate',
  tired: 'Moderate',
  lonely: 'Moderate',
  anxious: 'High',
  angry: 'High',
  frustrated: 'High',
};

const INSIGHTS = {
  happy: [
    "Your positivity is radiating today! Keep nurturing what brings you joy.",
    "Great mood detected! Consider journaling what made you feel this way to revisit later.",
    "You're in a wonderful headspace. This is the perfect time for creative tasks!",
  ],
  sad: [
    "It's okay to feel down sometimes. Be gentle with yourself today.",
    "Consider reaching out to a friend or doing something comforting.",
    "This feeling is temporary. Try a short walk or listening to your favorite song.",
  ],
  angry: [
    "Take a few deep breaths. Your feelings are valid, but let's channel them wisely.",
    "Try writing down what's frustrating you — it can help process the emotion.",
    "Physical activity like a brisk walk can help release built-up tension.",
  ],
  anxious: [
    "Try the 4-7-8 breathing technique: inhale 4s, hold 7s, exhale 8s.",
    "Ground yourself: name 5 things you see, 4 you hear, 3 you feel.",
    "You're stronger than your worries. Break tasks into smaller steps.",
  ],
  calm: [
    "Beautiful balance today! Protect this peace — you've earned it.",
    "Your calmness is a superpower. Consider meditating to deepen it.",
    "A calm mind makes the best decisions. Well done on finding your center.",
  ],
  tired: [
    "Rest is productive too. Consider a power nap or gentle stretching.",
    "Your body is asking for recovery. Honor that signal.",
    "Try limiting screen time before bed tonight for better sleep quality.",
  ],
  grateful: [
    "Gratitude rewires your brain for happiness. You're doing something beautiful.",
    "Counting your blessings amplifies joy — keep this practice going!",
    "A grateful heart is a magnet for miracles. Your perspective is inspiring.",
  ],
  lonely: [
    "Loneliness is a signal, not a sentence. Consider reaching out to someone today.",
    "You are worthy of connection. Try joining a community or group activity.",
    "Being alone is not the same as being lonely — nurture your relationship with yourself.",
  ],
  excited: [
    "Channel this incredible energy into something creative or productive!",
    "Your excitement is contagious — share it with someone who matters to you.",
    "Savor this feeling! Write down what's making you this excited to remember it later.",
  ],
  frustrated: [
    "Frustration often means you care deeply. Take a step back and reassess your approach.",
    "Try breaking the problem into smaller, manageable pieces.",
    "Remember: every expert was once a beginner. Progress isn't always linear.",
  ],
};

const SUGGESTIONS = {
  happy: [
    { icon: '✨', text: 'Share your joy with someone you care about' },
    { icon: '📝', text: "Write down 3 things you're grateful for" },
    { icon: '🎵', text: 'Create a feel-good playlist for days like this' },
  ],
  sad: [
    { icon: '🫂', text: 'Reach out to a friend or family member' },
    { icon: '🍵', text: 'Make yourself a warm drink and rest' },
    { icon: '🎧', text: 'Listen to comforting music or a podcast' },
  ],
  angry: [
    { icon: '🧘', text: 'Try 5 minutes of deep breathing exercises' },
    { icon: '🏃', text: 'Go for a walk or do some physical activity' },
    { icon: '📖', text: 'Write about what triggered this feeling' },
  ],
  anxious: [
    { icon: '🌬️', text: 'Practice box breathing: 4-4-4-4 pattern' },
    { icon: '🌿', text: 'Step outside for fresh air and sunlight' },
    { icon: '📋', text: 'Make a to-do list to organize your thoughts' },
  ],
  calm: [
    { icon: '🧘', text: 'Try a 10-minute guided meditation' },
    { icon: '📚', text: 'Read something inspiring or creative' },
    { icon: '🌅', text: 'Enjoy the moment — you deserve this peace' },
  ],
  tired: [
    { icon: '😴', text: 'Take a 20-minute power nap' },
    { icon: '💧', text: 'Stay hydrated — drink a glass of water' },
    { icon: '📵', text: 'Reduce screen time before sleeping tonight' },
  ],
  grateful: [
    { icon: '💌', text: 'Write a thank-you note to someone special' },
    { icon: '🌟', text: 'Start a gratitude journal — list 5 blessings' },
    { icon: '🤗', text: 'Pay it forward with a random act of kindness' },
  ],
  lonely: [
    { icon: '📱', text: "Call or text someone you haven't spoken to in a while" },
    { icon: '🏘️', text: 'Join a local community group or online forum' },
    { icon: '🐾', text: 'Spend time with a pet or visit an animal shelter' },
  ],
  excited: [
    { icon: '📸', text: 'Capture this moment — take photos or journal it' },
    { icon: '🗣️', text: 'Share the excitement with your closest people' },
    { icon: '🎯', text: 'Channel this energy into your passion project' },
  ],
  frustrated: [
    { icon: '🔄', text: 'Take a 10-minute break and come back fresh' },
    { icon: '🧩', text: 'Break the problem into smaller, solvable pieces' },
    { icon: '💪', text: "Remember past challenges you've already overcome" },
  ],
};

/**
 * Local keyword-based mood analysis (fallback when AI server is offline).
 */
export function analyzeMoodLocal(text, selectedMood = null) {
  const lower = text.toLowerCase();

  const scores = {};
  for (const [mood, keywords] of Object.entries(MOOD_KEYWORDS)) {
    scores[mood] = keywords.reduce((score, kw) => score + (lower.includes(kw) ? 1 : 0), 0);
  }

  let detected = selectedMood || 'calm';
  let maxScore = 0;
  for (const [mood, score] of Object.entries(scores)) {
    if (score > maxScore) {
      maxScore = score;
      detected = mood;
    }
  }

  if (selectedMood && maxScore > 0 && detected !== selectedMood) {
    if (maxScore < 2) detected = selectedMood;
  }

  const meta = MOOD_META[detected];
  const jitter = Math.floor(Math.random() * 15) - 7;
  const positivity = Math.max(5, Math.min(98, meta.positivityBase + jitter));
  const insightPool = INSIGHTS[detected];
  const insight = insightPool[Math.floor(Math.random() * insightPool.length)];

  return {
    mood: detected,
    moodLabel: meta.label,
    emoji: meta.emoji,
    color: meta.color,
    positivity,
    stressLevel: STRESS_LEVELS[detected],
    insight,
    suggestions: SUGGESTIONS[detected],
    confidence: null,
    allProbabilities: null,
    aiPowered: false,
    vad: null,
  };
}

/** @deprecated Use analyzeMoodAI() instead — kept for backward compatibility */
export function analyzeMood(text, selectedMood = null) {
  return analyzeMoodLocal(text, selectedMood);
}

export function getMoodMeta() {
  return MOOD_META;
}


/* ===================================================================
   Stats helpers (unchanged)
   =================================================================== */

export function getWeeklyData(entries = []) {
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const now = new Date();
  const weekData = [];

  for (let i = 6; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const dayStr = days[d.getDay()];
    const dateStr = d.toDateString();

    const dayEntries = entries.filter(e => new Date(e.date).toDateString() === dateStr);
    const avgPositivity = dayEntries.length
      ? Math.round(dayEntries.reduce((s, e) => s + (e.positivity || 50), 0) / dayEntries.length)
      : null;

    const dominantMood = dayEntries.length
      ? dayEntries[0].moodLabel
      : null;

    weekData.push({ day: dayStr, positivity: avgPositivity, mood: dominantMood, date: dateStr });
  }

  return weekData;
}

export function getInsightsData(entries = []) {
  if (entries.length === 0) return null;

  const freq = {};
  entries.forEach(e => {
    const m = e.moodLabel || 'Unknown';
    freq[m] = (freq[m] || 0) + 1;
  });

  const sorted = Object.entries(freq).sort((a, b) => b[1] - a[1]);
  const mostCommon = sorted[0];

  const avgPositivity = Math.round(
    entries.reduce((s, e) => s + (e.positivity || 50), 0) / entries.length
  );

  let streak = 0;
  const checked = new Set();
  for (let i = 0; i < 365; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const ds = d.toDateString();
    if (entries.some(e => new Date(e.date).toDateString() === ds)) {
      streak++;
      checked.add(ds);
    } else {
      break;
    }
  }

  return {
    totalEntries: entries.length,
    mostCommonMood: mostCommon[0],
    mostCommonCount: mostCommon[1],
    moodDistribution: sorted,
    avgPositivity,
    streak,
  };
}
