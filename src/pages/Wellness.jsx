import { useState, useRef, useEffect } from 'react';
import { getUserName } from '../store.js';
import './Wellness.css';

/* ------- Simple AI-style responses ------- */
const RESPONSES = {
  overwhelmed: [
    "I hear you. Feeling overwhelmed is really tough. Take a deep breath — inhale for 4 seconds, hold for 4, exhale for 4. You've handled hard things before, and you can handle this too. 💜",
    "It sounds like a lot is on your plate. Try writing down everything that's weighing on you, then tackle just one small thing. Progress, not perfection. 🌱",
  ],
  stressed: [
    "Stress is your body's way of saying you care. But let's give it some relief — try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste. 🧘",
    "A 10-minute walk outside can reduce stress hormones by 20%. Even if you can't go outside, stretching at your desk helps! 🌿",
  ],
  sad: [
    "It's completely okay to feel sad. Your emotions are valid. Be kind to yourself right now — you deserve the same compassion you'd give a friend. 🫂",
    "When sadness visits, try to do one small comforting thing: a warm drink, a favorite song, or just resting. You don't have to be strong all the time. 💛",
  ],
  anxious: [
    "Anxiety often comes from worrying about the future. Let's bring you back to now: what's one thing you can control right now? Focus on that. The rest can wait. 🌊",
    "Try this: place your hand on your chest. Feel your heartbeat. You're here, you're alive, you're safe. Take it one moment at a time. 💜",
  ],
  lonely: [
    "Loneliness can be so heavy, but it doesn't mean you're alone in the world. Consider reaching out to someone — even a small 'hey, how are you?' can open a door. 💚",
    "Sometimes journaling can help when you feel lonely. Write a letter to your future self — they'll appreciate knowing what you went through. 📝",
  ],
  angry: [
    "Anger is a signal that something matters to you. That's not wrong — but let's channel it. Try clenching your fists for 10 seconds, then releasing. Feel the tension leave. 🔥",
    "Before reacting, try the STOP technique: Stop, Take a breath, Observe your feelings, Proceed with awareness. You've got this. 🧠",
  ],
  happy: [
    "That's wonderful to hear! 🎉 Savor this feeling — positive moments are like sunlight for your mental health. What made you feel this way?",
    "Joy is contagious! Consider sharing this feeling with someone you care about — spreading happiness amplifies it. ✨",
  ],
  sleep: [
    "Sleep is so important for emotional balance. Try a digital sunset — turn off screens 30 minutes before bed, dim the lights, and do some gentle reading or stretching. 🌙",
    "If your mind races at bedtime, try a 'brain dump': write down everything on your mind before you lie down. It helps clear the mental clutter. 📝",
  ],
  default: [
    "Thank you for sharing that with me. Your feelings are always valid. Remember: taking the time to check in with yourself is already a form of self-care. 🌿",
    "I'm here to listen. Mental wellness is a journey, not a destination. Every small step you take counts. What else is on your mind? 💜",
    "Self-awareness is the first step to emotional growth. The fact that you're here, reflecting on how you feel — that's powerful. 🌱",
  ],
};

function getResponse(text) {
  const lower = text.toLowerCase();
  const keyMap = {
    overwhelmed: ['overwhelm', 'too much', 'can\'t handle', 'breaking down', 'falling apart'],
    stressed: ['stress', 'pressure', 'tense', 'deadline', 'exam', 'work'],
    sad: ['sad', 'cry', 'tears', 'depressed', 'down', 'unhappy', 'grief', 'miss'],
    anxious: ['anxious', 'anxiety', 'worried', 'worry', 'panic', 'fear', 'scared', 'nervous'],
    lonely: ['lonely', 'alone', 'isolated', 'no one', 'nobody', 'no friends'],
    angry: ['angry', 'mad', 'furious', 'hate', 'frustrated', 'annoyed', 'irritated'],
    happy: ['happy', 'great', 'amazing', 'wonderful', 'good', 'excited', 'grateful'],
    sleep: ['sleep', 'insomnia', 'tired', 'rest', 'exhausted', 'can\'t sleep', 'awake'],
  };

  for (const [key, keywords] of Object.entries(keyMap)) {
    if (keywords.some(kw => lower.includes(kw))) {
      const pool = RESPONSES[key];
      return pool[Math.floor(Math.random() * pool.length)];
    }
  }

  const pool = RESPONSES.default;
  return pool[Math.floor(Math.random() * pool.length)];
}

const getRandomDelay = () => 800 + Math.random() * 800;

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
      text: `Hi ${name}! 👋 I'm your wellness companion. Tell me how you're feeling, and I'll offer supportive guidance. Remember, I'm here to help, not replace professional care. 💜`,
    },
  ]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const sendMessage = (text) => {
    if (!text.trim()) return;
    const userMsg = { role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setTyping(true);

    // Simulate AI thinking
    const delay = getRandomDelay();
    setTimeout(() => {
      const response = getResponse(text);
      setMessages(prev => [...prev, { role: 'assistant', text: response }]);
      setTyping(false);
    }, delay);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="wellness fade-in" id="wellness-page">
      <header className="page-header slide-up">
        <h1 className="page-title">💚 Wellness Assistant</h1>
        <p className="page-sub">Your supportive AI companion</p>
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
