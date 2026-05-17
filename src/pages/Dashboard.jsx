import { useState, useEffect, useRef, useCallback } from 'react';
import {
  getUserName,
  analyzeMoodAI,
  checkAIAvailable,
  saveEntry,
  getWeeklyData,
  getAllEntries,
} from '../store.js';
import { recordStreak, getMilestoneMessage } from '../data/streaks.js';
import MoodGraph from '../components/MoodGraph.jsx';
import DailyQuote from '../components/DailyQuote.jsx';
import StreakDisplay from '../components/StreakDisplay.jsx';
import BreathingCircle from '../components/BreathingCircle.jsx';
import Confetti from '../components/Confetti.jsx';
import './Dashboard.css';

const MOODS = [
  { key: 'happy',      emoji: '😊', label: 'Happy' },
  { key: 'sad',        emoji: '😔', label: 'Sad' },
  { key: 'angry',      emoji: '😡', label: 'Angry' },
  { key: 'anxious',    emoji: '😰', label: 'Anxious' },
  { key: 'calm',       emoji: '😌', label: 'Calm' },
  { key: 'tired',      emoji: '😴', label: 'Tired' },
  { key: 'grateful',   emoji: '🙏', label: 'Grateful' },
  { key: 'lonely',     emoji: '🥀', label: 'Lonely' },
  { key: 'excited',    emoji: '🎉', label: 'Excited' },
  { key: 'frustrated', emoji: '😤', label: 'Frustrated' },
];

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return { text: 'Good Morning', icon: '☀️' };
  if (h < 17) return { text: 'Good Afternoon', icon: '🌤️' };
  if (h < 21) return { text: 'Good Evening', icon: '🌙' };
  return { text: 'Good Night', icon: '🌜' };
}

export default function Dashboard() {
  const name = getUserName() || 'Friend';
  const greeting = getGreeting();

  const [selectedMood, setSelectedMood] = useState(null);
  const [journalText, setJournalText] = useState('');
  const [result, setResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiOnline, setAiOnline] = useState(null); // null=checking, true/false
  const [weeklyData, setWeeklyData] = useState([]);
  const [recentEntries, setRecentEntries] = useState([]);
  const [showConfetti, setShowConfetti] = useState(false);
  const [milestoneMsg, setMilestoneMsg] = useState('');
  const [streakKey, setStreakKey] = useState(0); // force re-render of StreakDisplay
  const resultRef = useRef(null);

  // Check AI backend and load initial data on mount
  useEffect(() => {
    async function init() {
      const isOnline = await checkAIAvailable();
      setAiOnline(isOnline);
      const entries = await getAllEntries();
      setRecentEntries(entries.slice(0, 3));
      setWeeklyData(getWeeklyData(entries));
    }
    init();
  }, []);

  const handleConfettiComplete = useCallback(() => {
    setShowConfetti(false);
    setMilestoneMsg('');
  }, []);

  const handleAnalyze = async () => {
    if (!journalText.trim() && !selectedMood) return;
    setAnalyzing(true);

    try {
      // Call the real AI backend (with automatic fallback)
      const analysis = await analyzeMoodAI(journalText, selectedMood);

      const saved = await saveEntry({
        text: journalText,
        mood: analysis.mood,
        moodLabel: analysis.moodLabel,
        positivity: analysis.positivity,
        stressLevel: analysis.stressLevel,
        insight: analysis.insight,
        aiPowered: analysis.aiPowered || false,
        confidence: analysis.confidence || null,
        valence: analysis.vad?.valence || null,
        arousal: analysis.vad?.arousal || null,
        dominance: analysis.vad?.dominance || null,
      });

      setResult(analysis);
      setWeeklyData(getWeeklyData(saved));
      setRecentEntries(saved.slice(0, 3));

      // Record streak and check for milestones
      const { isMilestone, milestoneValue } = recordStreak();
      setStreakKey(k => k + 1); // force StreakDisplay refresh
      if (isMilestone) {
        setShowConfetti(true);
        setMilestoneMsg(getMilestoneMessage(milestoneValue));
      }

      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      console.error('Analysis failed:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedMood(null);
    setJournalText('');
    setResult(null);
  };

  return (
    <div className="dashboard fade-in" id="dashboard-page">
      {/* Confetti celebration */}
      <Confetti active={showConfetti} onComplete={handleConfettiComplete} />

      {/* Milestone toast */}
      {milestoneMsg && (
        <div className="milestone-toast scale-in" id="milestone-toast">
          <p>{milestoneMsg}</p>
        </div>
      )}

      {/* ─── AI Status Indicator ─── */}
      <div className="ai-status-bar slide-up">
        {aiOnline === null ? (
          <span className="ai-badge ai-checking">⏳ Checking AI model…</span>
        ) : aiOnline ? (
          <span className="ai-badge ai-online">🧠 AI + RAG Analysis Active</span>
        ) : (
          <span className="ai-badge ai-offline">💡 Classic Journaling Mode</span>
        )}
      </div>

      {/* ─── Greeting ─── */}
      <section className="greeting-section slide-up">
        <div className="greeting-icon">{greeting.icon}</div>
        <h1 className="greeting-text">
          {greeting.text}, <span className="greeting-name">{name}</span>
        </h1>
        <p className="greeting-sub">How are you feeling today?</p>
      </section>

      {/* ─── Daily Quote ─── */}
      <section className="daily-quote-section slide-up stagger-1">
        <DailyQuote />
      </section>

      {/* ─── Streak & Breathing Row ─── */}
      <section className="wellness-row slide-up stagger-2">
        <div className="wellness-row-item">
          <StreakDisplay key={streakKey} />
        </div>
        <div className="wellness-row-item breathing-card card">
          <h3 className="section-title breathing-title">🫧 Breathe</h3>
          <BreathingCircle compact />
        </div>
      </section>

      {/* ─── Mood Selector ─── */}
      <section className="mood-selector slide-up stagger-3" id="mood-selector">
        <div className="mood-grid">
          {MOODS.map((m) => (
            <button
              key={m.key}
              className={`mood-btn ${selectedMood === m.key ? 'selected' : ''}`}
              onClick={() => setSelectedMood(selectedMood === m.key ? null : m.key)}
              id={`mood-${m.key}`}
              aria-label={m.label}
            >
              <span className="mood-emoji">{m.emoji}</span>
              <span className="mood-label">{m.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* ─── Journal ─── */}
      <section className="journal-section slide-up stagger-4" id="journal-section">
        <div className="card journal-card">
          <div className="journal-header">
            <span className="journal-header-icon">📝</span>
            <span className="journal-header-text">Journal Entry</span>
          </div>
          <textarea
            className="journal-input"
            placeholder="Write about your day, thoughts, feelings…"
            value={journalText}
            onChange={e => setJournalText(e.target.value)}
            rows={4}
            id="journal-textarea"
          />
          <div className="journal-actions">
            <span className="char-count">{journalText.length} characters</span>
            <button
              className="btn-primary analyze-btn"
              onClick={handleAnalyze}
              disabled={analyzing || (!journalText.trim() && !selectedMood)}
              id="analyze-btn"
            >
              {analyzing ? (
                <>
                  <span className="spinner" />
                  Analyzing…
                </>
              ) : (
                <>
                  <span>✨</span>
                  Analyze Mood
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* ─── Result ─── */}
      {result && (
        <section className="result-section scale-in" ref={resultRef} id="result-section">
          <div className="result-card card">
            <div className="result-header">
              <span className="result-emoji">{result.emoji}</span>
              <div>
                <h3 className="result-mood">Feeling {result.moodLabel}</h3>
                <p className="result-date">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</p>
              </div>
              {/* AI Powered badge */}
              {result.aiPowered && (
                <span className="ai-powered-badge" title="Analyzed by trained ML model">
                  🧠 AI
                </span>
              )}
            </div>

            <div className="result-metrics">
              <div className="metric">
                <span className="metric-label">Positivity</span>
                <div className="metric-bar-bg">
                  <div
                    className="metric-bar"
                    style={{ width: `${result.positivity}%`, background: result.positivity > 60 ? 'var(--mint-400)' : result.positivity > 35 ? 'var(--amber-400)' : 'var(--rose-400)' }}
                  />
                </div>
                <span className="metric-value">{result.positivity}%</span>
              </div>
              <div className="metric">
                <span className="metric-label">Stress Level</span>
                <span className={`stress-badge stress-${result.stressLevel.toLowerCase()}`}>
                  {result.stressLevel}
                </span>
              </div>
              {/* AI Confidence — only shown when using real ML */}
              {result.confidence !== null && result.confidence !== undefined && (
                <div className="metric">
                  <span className="metric-label">AI Confidence</span>
                  <div className="metric-bar-bg">
                    <div
                      className="metric-bar"
                      style={{ width: `${result.confidence}%`, background: 'var(--lavender-400)' }}
                    />
                  </div>
                  <span className="metric-value">{result.confidence}%</span>
                </div>
              )}
            </div>

            {/* Class probabilities — only from real AI */}
            {result.allProbabilities && (
              <div className="probability-grid">
                <h4 className="prob-title">🎯 Emotion Probabilities</h4>
                <div className="prob-items">
                  {Object.entries(result.allProbabilities)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cls, prob]) => (
                      <div key={cls} className="prob-item">
                        <span className="prob-label">{cls}</span>
                        <div className="prob-bar-bg">
                          <div className="prob-bar" style={{ width: `${prob}%` }} />
                        </div>
                        <span className="prob-value">{prob}%</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* VAD Scores — NRC Lexicon */}
            {result.vad && (
              <div className="vad-section">
                <h4 className="vad-title">🧠 Emotional Dimensions (VAD)</h4>
                <div className="vad-grid">
                  <div className="vad-item">
                    <div className="vad-header">
                      <span className="vad-label">Valence</span>
                      <span className="vad-badge">{result.vad.valenceLabel}</span>
                    </div>
                    <div className="vad-bar-bg">
                      <div className="vad-bar vad-valence" style={{ width: `${result.vad.valence * 100}%` }} />
                    </div>
                    <span className="vad-value">{(result.vad.valence * 100).toFixed(0)}%</span>
                    <span className="vad-desc">Emotional positivity</span>
                  </div>
                  <div className="vad-item">
                    <div className="vad-header">
                      <span className="vad-label">Arousal</span>
                      <span className="vad-badge">{result.vad.arousalLabel}</span>
                    </div>
                    <div className="vad-bar-bg">
                      <div className="vad-bar vad-arousal" style={{ width: `${result.vad.arousal * 100}%` }} />
                    </div>
                    <span className="vad-value">{(result.vad.arousal * 100).toFixed(0)}%</span>
                    <span className="vad-desc">Emotional intensity</span>
                  </div>
                  <div className="vad-item">
                    <div className="vad-header">
                      <span className="vad-label">Dominance</span>
                      <span className="vad-badge">{result.vad.dominanceLabel}</span>
                    </div>
                    <div className="vad-bar-bg">
                      <div className="vad-bar vad-dominance" style={{ width: `${result.vad.dominance * 100}%` }} />
                    </div>
                    <span className="vad-value">{(result.vad.dominance * 100).toFixed(0)}%</span>
                    <span className="vad-desc">Sense of control</span>
                  </div>
                </div>
                {result.vad.matchedWords > 0 && (
                  <p className="vad-meta">
                    📚 Analyzed {result.vad.matchedWords} of {result.vad.totalWords} words via NRC VAD Lexicon
                  </p>
                )}
              </div>
            )}

            <div className="result-insight">
              <span className="insight-icon">💡</span>
              <p>{result.insight}</p>
            </div>

            {/* Suggestions */}
            <div className="result-suggestions">
              <h4 className="suggestions-title">AI Suggestions</h4>
              {result.suggestions.map((s, i) => (
                <div key={i} className="suggestion-item">
                  <span className="suggestion-icon">{s.icon}</span>
                  <span>{s.text}</span>
                </div>
              ))}
            </div>

            {/* RAG Context — Retrieved Knowledge */}
            {result.rag && result.rag.ragEnabled && result.rag.retrievedContext && (
              <div className="rag-section">
                <h4 className="rag-title">📚 Evidence-Based Insights <span className="rag-badge">RAG</span></h4>
                {result.rag.retrievedContext.map((ctx, i) => (
                  <div key={i} className="rag-card">
                    <div className="rag-card-header">
                      <span className="rag-category">{ctx.category}</span>
                      <span className="rag-relevance">{Math.round(ctx.relevance * 100)}% match</span>
                    </div>
                    <h5 className="rag-card-title">{ctx.title}</h5>
                    <p className="rag-card-content">{ctx.content}</p>
                    {ctx.source && (
                      <p className="rag-card-source">📖 {ctx.source}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            <button className="btn-secondary" onClick={handleReset} id="new-entry-btn">
              + New Entry
            </button>
          </div>
        </section>
      )}

      {/* ─── Mood Graph ─── */}
      <section className="graph-section slide-up stagger-5" id="mood-graph-section">
        <div className="card">
          <h3 className="section-title">📊 Weekly Mood Trend</h3>
          <MoodGraph data={weeklyData} />
        </div>
      </section>

      {/* ─── Recent Entries ─── */}
      {recentEntries.length > 0 && (
        <section className="recent-section slide-up stagger-6" id="recent-entries">
          <h3 className="section-title">📝 Recent Entries</h3>
          <div className="recent-list">
            {recentEntries.map((entry, i) => (
              <div key={entry.id || i} className="recent-card card">
                <div className="recent-header">
                  <span className="recent-date">
                    {new Date(entry.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                  </span>
                  <div className="recent-badges">
                    <span className="recent-mood">{entry.moodLabel}</span>
                    {entry.aiPowered && <span className="recent-ai-badge">🧠</span>}
                  </div>
                </div>
                <p className="recent-text">{entry.text || 'No journal entry'}</p>
                <div className="recent-stats">
                  <span>Positivity: {entry.positivity}%</span>
                  <span>Stress: {entry.stressLevel}</span>
                  {entry.confidence && <span>Confidence: {entry.confidence}%</span>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
