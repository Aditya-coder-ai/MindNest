import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import WelcomePage from './pages/WelcomePage.jsx';
import Dashboard from './pages/Dashboard.jsx';
import History from './pages/History.jsx';
import Insights from './pages/Insights.jsx';
import Wellness from './pages/Wellness.jsx';
import Navbar from './components/Navbar.jsx';
import { getUserName } from './store.js';
import './App.css';

export default function App() {
  const [started, setStarted] = useState(!!getUserName());

  useEffect(() => {
    /* re-check on storage change (multi-tab) */
    const onStorage = () => setStarted(!!getUserName());
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  if (!started) {
    return <WelcomePage onStart={() => setStarted(true)} />;
  }

  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/wellness" element={<Wellness />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
