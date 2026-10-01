import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiLogin, apiSignup } from '../api.js';
import { useAuth } from '../auth.jsx';

export default function Login() {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('admin@univ.edu');
  const [password, setPassword] = useState('admin123');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setErr(''); setBusy(true);
    try {
      const d = mode === 'login' ? await apiLogin(email, password) : await apiSignup(name, email, password);
      login(d.token, d.user);
      nav('/');
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };

  return (
    <div className="page auth-page">
      <div className="card auth-card">
        <p className="kicker">University Student Portal</p>
        <h1>{mode === 'login' ? 'Welcome back' : 'Create staff account'}</h1>
        <p className="muted">JWT-secured portal · Python backend · demo: <code>admin@univ.edu / admin123</code></p>
        <form onSubmit={submit} className="form">
          {mode === 'signup' && (
            <label>Full name<input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Exam Officer" /></label>
          )}
          <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@univ.edu" /></label>
          <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="min 6 chars" /></label>
          {err && <p className="error">{err}</p>}
          <button className="primary" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Login' : 'Sign up'}</button>
        </form>
        <p className="muted small">
          {mode === 'login' ? <>No account? <button className="link" onClick={() => setMode('signup')}>Sign up</button></>
            : <>Have an account? <button className="link" onClick={() => setMode('login')}>Login</button></>}
        </p>
        <p className="muted small">Task focus: <Link to="/search">how roll-number search scales →</Link></p>
      </div>
    </div>
  );
}
