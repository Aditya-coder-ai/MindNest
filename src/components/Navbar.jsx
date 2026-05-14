import { NavLink, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase.js';
import logo from '../assets/logo.png';
import './Navbar.css';

const NAV_ITEMS = [
  { to: '/',         icon: '🏠', label: 'Home' },
  { to: '/history',  icon: '📅', label: 'History' },
  { to: '/insights', icon: '🧠', label: 'Insights' },
  { to: '/wellness', icon: '💚', label: 'Wellness' },
];

export default function Navbar() {
  const navigate = useNavigate();
  const user = auth.currentUser;
  const [showProfile, setShowProfile] = useState(false);

  const handleLogout = async () => {
    try {
      await signOut(auth);
      localStorage.removeItem('mindnest_user_name');
      navigate('/');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  return (
    <nav className="navbar glass" id="main-nav">
      <div className="navbar-brand">
        <img src={logo} alt="MindNest" className="navbar-logo-img" />
        <span className="navbar-title">MindNest</span>
      </div>
      <ul className="navbar-links">
        {NAV_ITEMS.map(item => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              id={`nav-${item.label.toLowerCase()}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          </li>
        ))}
      </ul>

      {/* User Profile Button */}
      <div className="navbar-user-wrap">
        <button
          className="navbar-avatar-btn"
          onClick={() => setShowProfile(!showProfile)}
          title={user?.displayName || user?.email || 'Profile'}
          id="profile-btn"
        >
          {user?.photoURL ? (
            <img src={user.photoURL} alt="" className="navbar-avatar-img" referrerPolicy="no-referrer" />
          ) : (
            <span className="navbar-avatar-fallback">
              {(user?.displayName || user?.email || '?')[0].toUpperCase()}
            </span>
          )}
        </button>

        {/* Profile Dropdown */}
        {showProfile && (
          <div className="profile-dropdown glass scale-in" id="profile-dropdown">
            <div className="profile-header">
              {user?.photoURL ? (
                <img src={user.photoURL} alt="" className="profile-photo" referrerPolicy="no-referrer" />
              ) : (
                <div className="profile-photo-fallback">
                  {(user?.displayName || user?.email || '?')[0].toUpperCase()}
                </div>
              )}
              <div className="profile-info">
                <p className="profile-name">{user?.displayName || 'MindNest User'}</p>
                <p className="profile-email">{user?.email || ''}</p>
              </div>
            </div>
            <div className="profile-meta">
              <div className="profile-meta-item">
                <span>🆔</span>
                <span className="profile-uid">{user?.uid?.slice(0, 12)}…</span>
              </div>
              <div className="profile-meta-item">
                <span>📅</span>
                <span>Joined {user?.metadata?.creationTime ? new Date(user.metadata.creationTime).toLocaleDateString() : '—'}</span>
              </div>
              <div className="profile-meta-item">
                <span>🔐</span>
                <span>{user?.providerData?.[0]?.providerId === 'google.com' ? 'Google Account' : 'Email & Password'}</span>
              </div>
            </div>
            <button className="profile-logout-btn" onClick={handleLogout} id="dropdown-logout-btn">
              🚪 Sign Out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}
