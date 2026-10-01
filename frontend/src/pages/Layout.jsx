import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth.jsx';

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const out = () => { logout(); nav('/login'); };
  return (
    <div className="page">
      <nav className="topnav">
        <Link to="/" className="brand">🎓 Student Portal</Link>
        <div className="links">
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/students">Students</NavLink>
          <NavLink to="/search">Search Lab</NavLink>
        </div>
        <div className="userbox">
          <span className="muted small">{user?.name}</span>
          <button onClick={out}>Logout</button>
        </div>
      </nav>
      {children}
      <footer className="muted small">Python API :5001 (JWT + SQLite) · React portal · ops counted per query in <code>search_algorithms.py</code></footer>
    </div>
  );
}
