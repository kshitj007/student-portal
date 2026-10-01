// Portal API client — JWT in localStorage, sent as Bearer token.
const BASE = 'http://localhost:5001';
const KEY = 'portal_token';

export const getToken = () => localStorage.getItem(KEY);
export const setToken = (t) => (t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY));

async function req(path, { method = 'GET', body } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) {
    setToken(null);
    throw new Error(data.error || 'Session expired — please login again');
  }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

export const apiHealth = () => fetch(`${BASE}/api/health`).then((r) => { if (!r.ok) throw new Error('down'); return r.json(); });
export const apiSignup = (name, email, password) => req('/api/auth/signup', { method: 'POST', body: { name, email, password } });
export const apiLogin = (email, password) => req('/api/auth/login', { method: 'POST', body: { email, password } });
export const apiMe = () => req('/api/me');
export const apiStats = () => req('/api/stats');
export const apiStudents = ({ query = '', branch = '', limit = 20, offset = 0 } = {}) =>
  req(`/api/students?query=${encodeURIComponent(query)}&branch=${encodeURIComponent(branch)}&limit=${limit}&offset=${offset}`);
export const apiStudentDetail = (roll) => req(`/api/students/${roll}`);
export const apiNextRoll = (batch, branch) => req(`/api/next-roll?batch=${batch}&branch=${encodeURIComponent(branch)}`);
export const apiAddStudent = (s) => req('/api/students', { method: 'POST', body: s });
export const apiSearch = (target) => req('/api/search', { method: 'POST', body: { target } });
export const apiBenchmark = (num_queries) => req('/api/benchmark', { method: 'POST', body: { num_queries } });
