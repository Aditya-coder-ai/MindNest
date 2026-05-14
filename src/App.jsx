import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase.js';
import AuthPage from './pages/AuthPage.jsx';
import WelcomePage from './pages/WelcomePage.jsx';
import Dashboard from './pages/Dashboard.jsx';
import History from './pages/History.jsx';
import Insights from './pages/Insights.jsx';
import Wellness from './pages/Wellness.jsx';
import Navbar from './components/Navbar.jsx';
import AmbientBackground from './components/AmbientBackground.jsx';
import { getUserName } from './store.js';
import './App.css';

export default function App() {
  const [user, setUser] = useState(undefined); // undefined=loading, null=no user, object=user
  const [started, setStarted] = useState(!!getUserName());

  // Listen to Firebase Auth state
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    /* re-check on storage change (multi-tab) */
    const onStorage = () => setStarted(!!getUserName());
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  // Loading state — waiting for Firebase to resolve auth
  if (user === undefined) {
    return (
      <div className="auth-loading">
        <div className="auth-loading-spinner" />
        <p>Loading MindNest…</p>
      </div>
    );
  }

  // Not authenticated — show login page
  if (!user) {
    return <AuthPage />;
  }

  // Authenticated but hasn't set name — show welcome/onboarding
  if (!started) {
    return <WelcomePage onStart={() => setStarted(true)} />;
  }

  // Fully authenticated + onboarded
  return (
    <div className="app-shell">
      <AmbientBackground />
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
