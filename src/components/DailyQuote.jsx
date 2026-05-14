import { useState, useEffect } from 'react';
import { getDailyQuote } from '../data/quotes.js';
import './DailyQuote.css';

const CATEGORY_ICONS = {
  mindfulness: '🧘',
  wellness: '💚',
  meditation: '🪷',
  'self-care': '🌸',
  affirmation: '✨',
  gratitude: '🙏',
};

/**
 * Daily quote card that refreshes each day.
 * Shows a curated mindfulness/wellness quote with gentle animations.
 */
export default function DailyQuote() {
  const [quote, setQuote] = useState(null);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const q = getDailyQuote();
    setQuote(q);
    // Slight delay for entrance animation
    const timer = setTimeout(() => setRevealed(true), 200);
    return () => clearTimeout(timer);
  }, []);

  if (!quote) return null;

  const icon = CATEGORY_ICONS[quote.category] || '💫';

  return (
    <div className={`daily-quote-card ${revealed ? 'daily-quote-revealed' : ''}`} id="daily-quote">
      <div className="dq-glow" aria-hidden="true" />
      <div className="dq-header">
        <span className="dq-icon">{icon}</span>
        <span className="dq-badge">Daily Inspiration</span>
      </div>
      <blockquote className="dq-text">
        "{quote.text}"
      </blockquote>
      <cite className="dq-author">— {quote.author}</cite>
      <div className="dq-category">
        <span className="dq-category-tag">{quote.category}</span>
      </div>
    </div>
  );
}
