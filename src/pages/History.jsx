import { useState, useMemo, useEffect } from 'react';
import { getAllEntries } from '../store.js';
import './History.css';

const MOOD_EMOJIS = {
  Happy: '😊', Sad: '😔', Angry: '😡', Anxious: '😰', Calm: '😌', Tired: '😴',
};

function groupByDate(entries) {
  const groups = {};
  entries.forEach(e => {
    const d = new Date(e.date).toLocaleDateString('en-US', {
      weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
    });
    if (!groups[d]) groups[d] = [];
    groups[d].push(e);
  });
  return Object.entries(groups);
}

export default function History() {
  const [entries, setEntries] = useState([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    getAllEntries().then(setEntries);
  }, []);

  const filtered = useMemo(() => {
    if (filter === 'all') return entries;
    return entries.filter(e => e.moodLabel === filter);
  }, [entries, filter]);

  const grouped = groupByDate(filtered);
  const moods = ['all', ...new Set(entries.map(e => e.moodLabel).filter(Boolean))];

  return (
    <div className="history fade-in" id="history-page">
      <header className="page-header slide-up">
        <h1 className="page-title">📅 Mood History</h1>
        <p className="page-sub">Review your emotional journey</p>
      </header>

      {/* Filter chips */}
      {entries.length > 0 && (
        <div className="filter-chips slide-up stagger-1">
          {moods.map(m => (
            <button
              key={m}
              className={`chip ${filter === m ? 'active' : ''}`}
              onClick={() => setFilter(m)}
            >
              {m === 'all' ? '🔮 All' : `${MOOD_EMOJIS[m] || ''} ${m}`}
            </button>
          ))}
        </div>
      )}

      {/* Entries */}
      {grouped.length === 0 ? (
        <div className="empty-state slide-up stagger-2">
          <span className="empty-icon">📝</span>
          <h3>No entries yet</h3>
          <p>Start journaling on the Dashboard to see your history here.</p>
        </div>
      ) : (
        <div className="history-timeline slide-up stagger-2">
          {grouped.map(([date, items]) => (
            <div key={date} className="timeline-group">
              <div className="timeline-date">{date}</div>
              {items.map((entry, i) => (
                <div key={entry.id || i} className="history-card card">
                  <div className="history-card-header">
                    <span className="history-emoji">{MOOD_EMOJIS[entry.moodLabel] || '😶'}</span>
                    <div className="history-meta">
                      <span className="history-mood">{entry.moodLabel}</span>
                      <span className="history-time">
                        {new Date(entry.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className="history-badges">
                      <span className="badge badge-pos">{entry.positivity}%</span>
                      <span className={`badge badge-stress stress-${(entry.stressLevel || 'low').toLowerCase()}`}>
                        {entry.stressLevel}
                      </span>
                    </div>
                  </div>
                  {entry.text && (
                    <p className="history-text">{entry.text}</p>
                  )}
                  {entry.insight && (
                    <div className="history-insight">
                      <span>💡</span>
                      <span>{entry.insight}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Entry count */}
      {entries.length > 0 && (
        <div className="history-footer slide-up stagger-3">
          <span>{filtered.length} entr{filtered.length === 1 ? 'y' : 'ies'} found</span>
        </div>
      )}
    </div>
  );
}
