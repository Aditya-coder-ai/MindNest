import { NavLink, useNavigate } from 'react-router-dom';
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
      <button
        className="navbar-logout"
        onClick={handleLogout}
        title="Sign Out"
        id="logout-btn"
      >
        <span className="logout-icon">🚪</span>
        <span className="logout-label">Logout</span>
      </button>
    </nav>
  );
}
