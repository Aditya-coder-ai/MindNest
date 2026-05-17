import { useState, useRef, useEffect } from 'react';
import { getUserName, checkAIAvailable, sendWellnessMessage } from '../store.js';
import './Wellness.css';

const QUICK_PROMPTS = [
  "I feel overwhelmed",
  "I can't sleep",
  "I'm feeling anxious",
  "I feel happy today",
  "I'm stressed about work",
  "I feel lonely",
];

export default function Wellness() {
  const name = getUserName() || 'Friend';
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: `Hi ${name}! I'm your wellness companion. Tell me how you're feeling, and I'll offer supportive guidance. I'm here to support you, not replace professional care.`,
    },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [aiOnline, setAiOnline] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  useEffect(() => {
    async function init() {
      const available = await checkAIAvailable();
      setAiOnline(available);
    }
    init();
  }, []);

  const sendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg = { role: 'user', text: trimmed };
    const history = [...messages, userMsg].map(({ role, text: content }) => ({
      role,
      text: content,
    }));

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setTyping(true);

    try {
      const response = await sendWellnessMessage(trimmed, history, name);
      setMessages(prev => [...prev, { role: 'assistant', text: response.reply }]);
    } catch (error) {
      console.error('Wellness chat failed:', error);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: "I couldn't reach the wellness service right now. Please make sure the AI backend is running and try again.",
        },
      ]);
      setAiOnline(false);
    } finally {
      setTyping(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="wellness fade-in" id="wellness-page">
      <header className="page-header slide-up">
        <h1 className="page-title">💚 Wellness Assistant</h1>
        <p className="page-sub">
          {aiOnline === false ? 'Backend offline' : 'Gemini-powered supportive companion'}
        </p>
      </header>

      {/* Chat area */}
      <div className="chat-container slide-up stagger-1">
        <div className="chat-messages" id="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.role === 'assistant' && <span className="bubble-avatar">🌿</span>}
              <div className="bubble-content">
                <p>{msg.text}</p>
              </div>
            </div>
          ))}
          {typing && (
            <div className="chat-bubble assistant">
              <span className="bubble-avatar">🌿</span>
              <div className="bubble-content typing-indicator">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick prompts */}
        <div className="quick-prompts">
          {QUICK_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              className="quick-btn"
              onClick={() => sendMessage(prompt)}
              disabled={typing}
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input */}
        <form className="chat-input-wrap" onSubmit={handleSubmit}>
          <input
            className="chat-input"
            type="text"
            placeholder="Tell me how you're feeling…"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={typing}
            id="wellness-input"
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!input.trim() || typing}
            id="send-btn"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>
      </div>

      {/* Disclaimer */}
      <p className="wellness-disclaimer slide-up stagger-2">
        🔒 This is a supportive tool, not a substitute for professional mental health care.
        If you're in crisis, please contact a mental health professional or helpline.
      </p>
    </div>
  );
}
