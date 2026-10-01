import React, { useEffect, useRef, useState } from 'react';
import { apiAddStudent, apiNextRoll, apiStudentDetail, apiStudents } from '../api.js';
import { BATCHES, BRANCHES, branchName } from '../branches.js';

const PAGE = 20;

export default function Students() {
  const [query, setQuery] = useState('');
  const [branch, setBranch] = useState('');
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [detail, setDetail] = useState(null);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [form, setForm] = useState({ roll_no: '', name: '', batch: '25', branch: 'CSD', cgpa: '' });
  const suggestedRef = useRef('');

  // Suggest the next sequential roll for the chosen batch+branch (serials run
  // 0001, 0002, … per batch+branch). Keeps a hand-typed custom roll untouched.
  useEffect(() => {
    let live = true;
    apiNextRoll(form.batch, form.branch).then((d) => {
      if (!live) return;
      const prev = suggestedRef.current;
      suggestedRef.current = d.roll;
      setForm((f) => (f.roll_no === '' || f.roll_no === prev ? { ...f, roll_no: d.roll } : f));
    }).catch(() => {});
    return () => { live = false; };
  }, [form.batch, form.branch]);

  const load = async (off = 0) => {
    setErr('');
    try {
      const d = await apiStudents({ query, branch, limit: PAGE, offset: off });
      setRows(d.students); setTotal(d.total); setOffset(off);
    } catch (e) { setErr(e.message); }
  };

  useEffect(() => { load(0); /* eslint-disable-next-line */ }, []);

  const search = (e) => { e?.preventDefault(); load(0); };

  const open = async (roll) => {
    try { setDetail(await apiStudentDetail(roll)); } catch (e) { setErr(e.message); }
  };

  const add = async (e) => {
    e.preventDefault(); setMsg(''); setErr('');
    try {
      const d = await apiAddStudent({
        roll_no: form.roll_no.trim().toUpperCase(), name: form.name,
        branch: form.branch, cgpa: Number(form.cgpa),
      });
      setMsg(`Added roll ${d.student.roll_no} — ${d.student.name}`);
      const { batch, branch } = form;
      suggestedRef.current = '';
      setForm({ roll_no: '', name: '', batch, branch, cgpa: '' });
      apiNextRoll(batch, branch).then((n) => {
        suggestedRef.current = n.roll;
        setForm((f) => (f.roll_no === '' ? { ...f, roll_no: n.roll } : f));
      }).catch(() => {});
      load(0);
    } catch (ex) { setErr(ex.message); }
  };

  return (
    <div className="students-layout">
      <div className="students-main">
      <section className="card">
        <h2>Search students</h2>
        <p className="muted small">Full roll (25MVCSD0327) · serial alone (0327 finds every branch) · or name.</p>
        <form className="inline-form" onSubmit={search}>
          <label className="grow">Roll no., serial, or name<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. 25MVCSD0327 · 0327 · Aarav" /></label>
          <label>Branch<select value={branch} onChange={(e) => setBranch(e.target.value)}>
            <option value="">All branches</option>
            {BRANCHES.map((b) => <option key={b.code} value={b.code}>{b.code} — {b.name}</option>)}
          </select></label>
          <button className="primary">Search</button>
        </form>
      </section>

      <section className="card">
        <h2>Records</h2>
        {err && <p className="error">{err}</p>}
        <p className="muted small">{total.toLocaleString('en-IN')} matching records</p>
        <table>
          <thead><tr><th>Roll</th><th>Name</th><th>Branch</th><th>Batch</th><th>CGPA</th><th /></tr></thead>
          <tbody>{rows.map((s) => (
            <tr key={s.roll_no}>
              <td>{s.roll_no}</td><td>{s.name}</td><td title={branchName(s.branch)}>{s.branch}</td><td>’{s.batch}</td><td>{s.cgpa}</td>
              <td><button className="link" onClick={() => open(s.roll_no)}>View</button></td>
            </tr>
          ))}</tbody>
        </table>
        <div className="row pager">
          <button disabled={offset === 0} onClick={() => load(offset - PAGE)}>← Prev</button>
          <span className="muted small">{offset + 1}–{offset + rows.length} of {total.toLocaleString('en-IN')}</span>
          <button disabled={offset + PAGE >= total} onClick={() => load(offset + PAGE)}>Next →</button>
        </div>
      </section>

      {detail && (
        <section className="card">
          <h2>Roll {detail.roll_no} — {detail.name}</h2>
          <p className="muted">Batch ’{detail.batch} · {detail.college} · {detail.branch} ({branchName(detail.branch)}) · Serial {detail.serial} · CGPA {detail.cgpa}</p>
          <table>
            <thead><tr><th>Algorithm</th><th>Complexity</th><th>Operations for this lookup</th></tr></thead>
            <tbody>
              <tr><td>Linear</td><td>O(n)</td><td>{detail.ops.linear.toLocaleString('en-IN')}</td></tr>
              <tr><td>Binary</td><td>O(log n)</td><td>{detail.ops.binary}</td></tr>
              <tr className="winner"><td>Hash</td><td>O(1)</td><td>{detail.ops.hash}</td></tr>
            </tbody>
          </table>
          <button className="link" onClick={() => setDetail(null)}>Close</button>
        </section>
      )}
      </div>

      <aside className="students-side">
        <section className="card">
          <h2>Add student</h2>
          <p className="muted small">Serials run 0001, 0002, … per batch+branch — the next roll is suggested. Same serial may exist in another branch; only the full roll must be unique.</p>
          <form className="form" onSubmit={add}>
            <label>Batch<select value={form.batch} onChange={(e) => setForm({ ...form, batch: e.target.value })}>{BATCHES.map((b) => <option key={b} value={String(b)}>20{b}</option>)}</select></label>
            <label>Branch<select value={form.branch} onChange={(e) => setForm({ ...form, branch: e.target.value })}>{BRANCHES.map((b) => <option key={b.code} value={b.code}>{b.code} — {b.name}</option>)}</select></label>
            <label>Roll no.<input value={form.roll_no} onChange={(e) => setForm({ ...form, roll_no: e.target.value.toUpperCase() })} placeholder="25MVCSD0327" required /></label>
            <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
            <label>CGPA<input value={form.cgpa} onChange={(e) => setForm({ ...form, cgpa: e.target.value })} inputMode="decimal" placeholder="0–10" required /></label>
            <button className="primary">Add record</button>
          </form>
          {msg && <p className="ok">{msg}</p>}
        </section>
      </aside>
    </div>
  );
}
