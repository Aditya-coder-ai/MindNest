import { useState, useMemo, useEffect } from 'react';
import { getInsightsData, getAllEntries, getWeeklyData } from '../store.js';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import MoodGraph from '../components/MoodGraph.jsx';
import './Insights.css';

ChartJS.register(ArcElement, Tooltip, Legend);

const MOOD_COLORS = {
  Happy: '#fbbf24',
  Sad: '#60a5fa',
  Angry: '#d88c94',
  Anxious: '#9b7bbd',
  Calm: '#4db8a4',
  Tired: '#94a3b8',
};

const MOOD_EMOJIS = {
  Happy: '😊', Sad: '😔', Angry: '😡', Anxious: '😰', Calm: '😌', Tired: '😴',
};

export default function Insights() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAllEntries().then(data => {
      setEntries(data);
      setLoading(false);
    });
  }, []);

  const insights = useMemo(() => getInsightsData(entries), [entries]);
  const weeklyData = useMemo(() => getWeeklyData(entries), [entries]);

  if (loading) return null;

  if (!insights) {
    return (
      <div className="insights fade-in" id="insights-page">
        <header className="page-header slide-up">
          <h1 className="page-title">🧠 Emotional Insights</h1>
          <p className="page-sub">Understand your emotional patterns</p>
        </header>
        <div className="empty-state slide-up stagger-1">
          <span className="empty-icon">🔍</span>
          <h3>Not enough data yet</h3>
          <p>Add a few journal entries to unlock your personalized insights.</p>
        </div>
      </div>
    );
  }

  const doughnutData = {
    labels: insights.moodDistribution.map(([m]) => m),
    datasets: [{
      data: insights.moodDistribution.map(([, c]) => c),
      backgroundColor: insights.moodDistribution.map(([m]) => MOOD_COLORS[m] || '#a78bfa'),
      borderWidth: 3,
      borderColor: '#ffffff',
      hoverBorderWidth: 0,
      hoverOffset: 8,
    }],
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '68%',
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e1b4b',
        titleColor: '#e0d9ff',
        bodyColor: '#ffffff',
        padding: 12,
        cornerRadius: 12,
        titleFont: { family: 'Poppins', size: 11 },
        bodyFont: { family: 'Poppins', size: 13, weight: 600 },
        callbacks: {
          label: (ctx) => {
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
            const pct = Math.round((ctx.raw / total) * 100);
            return `${ctx.label}: ${pct}% (${ctx.raw} entries)`;
          },
        },
      },
    },
  };

  // Generate pattern insights
  const patternInsights = [];

  // Time-based pattern
  const eveningEntries = entries.filter(e => {
    const h = new Date(e.date).getHours();
    return h >= 20 || h < 4;
  });
  if (eveningEntries.length >= 2) {
    const lateStress = eveningEntries.filter(e => e.stressLevel === 'High').length;
    if (lateStress > eveningEntries.length * 0.4) {
      patternInsights.push({
        icon: '🌙',
        text: 'You tend to feel more stressed during late-night sessions. Consider winding down earlier.',
      });
    }
  }

  // Positivity trend
  if (insights.avgPositivity > 65) {
    patternInsights.push({
      icon: '🌟',
      text: `Your average positivity is ${insights.avgPositivity}% — that's really good! Keep doing what works.`,
    });
  } else if (insights.avgPositivity < 40) {
    patternInsights.push({
      icon: '💛',
      text: `Your average positivity is ${insights.avgPositivity}%. Remember, it's okay to ask for help when needed.`,
    });
  }

  // Most common mood insight
  patternInsights.push({
    icon: MOOD_EMOJIS[insights.mostCommonMood] || '🔮',
    text: `Your most frequent mood is "${insights.mostCommonMood}" — recorded ${insights.mostCommonCount} time${insights.mostCommonCount > 1 ? 's' : ''}.`,
  });

  if (insights.streak > 1) {
    patternInsights.push({
      icon: '🔥',
      text: `Amazing ${insights.streak}-day journaling streak! Consistency builds self-awareness.`,
    });
  }

  return (
    <div className="insights fade-in" id="insights-page">
      <header className="page-header slide-up">
        <h1 className="page-title">🧠 Emotional Insights</h1>
        <p className="page-sub">Understand your emotional patterns</p>
      </header>

      {/* Stats overview */}
      <div className="insight-stats slide-up stagger-1">
        <div className="stat-card card">
          <span className="stat-icon">📝</span>
          <span className="stat-value">{insights.totalEntries}</span>
          <span className="stat-label">Total Entries</span>
        </div>
        <div className="stat-card card">
          <span className="stat-icon">{MOOD_EMOJIS[insights.mostCommonMood] || '🔮'}</span>
          <span className="stat-value">{insights.mostCommonMood}</span>
          <span className="stat-label">Top Mood</span>
        </div>
        <div className="stat-card card">
          <span className="stat-icon">💫</span>
          <span className="stat-value">{insights.avgPositivity}%</span>
          <span className="stat-label">Avg Positivity</span>
        </div>
        <div className="stat-card card">
          <span className="stat-icon">🔥</span>
          <span className="stat-value">{insights.streak}</span>
          <span className="stat-label">Day Streak</span>
        </div>
      </div>

      {/* Mood distribution */}
      <section className="insight-chart slide-up stagger-2">
        <div className="card">
          <h3 className="section-title">🎯 Mood Distribution</h3>
          <div className="chart-layout">
            <div className="chart-wrap">
              <Doughnut data={doughnutData} options={doughnutOptions} />
            </div>
            <div className="chart-legend">
              {insights.moodDistribution.map(([mood, count]) => {
                const total = insights.totalEntries;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={mood} className="legend-item">
                    <span className="legend-dot" style={{ background: MOOD_COLORS[mood] }} />
                    <span className="legend-mood">{MOOD_EMOJIS[mood]} {mood}</span>
                    <span className="legend-pct">{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Weekly trend */}
      <section className="slide-up stagger-3">
        <div className="card">
          <h3 className="section-title">📈 Weekly Trend</h3>
          <MoodGraph data={weeklyData} />
        </div>
      </section>

      {/* Pattern insights */}
      <section className="pattern-section slide-up stagger-4">
        <h3 className="section-title">🔍 Pattern Analysis</h3>
        <div className="pattern-list">
          {patternInsights.map((p, i) => (
            <div key={i} className="pattern-card card">
              <span className="pattern-icon">{p.icon}</span>
              <p className="pattern-text">{p.text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
