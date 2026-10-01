import React, { useState } from 'react';
import { apiBenchmark, apiSearch } from '../api.js';
import { OpsBars } from '../components/Charts.jsx';

/** Core assignment screen: single lookup ops + multi-query comparison on the real DB. */
export default function SearchLab() {
  const [roll, setRoll] = useState('');
  const [single, setSingle] = useState(null);
  const [queries, setQueries] = useState(100);
  const [bench, setBench] = useState(null);
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  const doSearch = async (e) => {
    e?.preventDefault(); setErr(''); setSingle(null);
    const target = roll.trim().toUpperCase();
    if (!target) { setErr('Enter a roll number'); return; }
    setBusy(true);
    try { setSingle(await apiSearch(target)); } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };

  const doBench = async () => {
    setErr(''); setBusy(true);
    try { setBench(await apiBenchmark(queries)); } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };

  return (
    <div>
      <section className="card">
        <h2>Single roll-number lookup</h2>
        <p className="muted">Full roll (25MVCSD0327) → 3-way ops count. Serial alone (0327) → every branch holding it, by full scan.</p>
        <form className="row" onSubmit={doSearch}>
          <input value={roll} onChange={(e) => setRoll(e.target.value)} placeholder="e.g. 25MVCSD0327 · 0327 · 99MVZZZ9999" />
          <button className="primary" disabled={busy}>{busy ? 'Searching…' : 'Search'}</button>
        </form>
        {single && single.mode === 'serial' && (
          <>
            <div className="found yes">Serial {single.target} found in {single.found.length} branch{single.found.length === 1 ? '' : 'es'} — linear scan of {single.dataset_size.toLocaleString('en-IN')} records ({single.linear.ops.toLocaleString('en-IN')} ops)</div>
            <table>
              <thead><tr><th>Roll</th><th>Name</th><th>Branch</th><th>Batch</th><th>CGPA</th></tr></thead>
              <tbody>{single.found.map((s) => (
                <tr key={s.roll_no}><td>{s.roll_no}</td><td>{s.name}</td><td>{s.branch}</td><td>’{s.batch}</td><td>{s.cgpa}</td></tr>
              ))}</tbody>
            </table>
            <p className="callout">{single.note}</p>
          </>
        )}
        {single && single.mode === 'full' && (
          <>
            <div className={`found ${single.found ? 'yes' : 'no'}`}>
              {single.found ? `Found — ${single.found.name} · ${single.found.branch} · Batch ’${single.found.batch} · CGPA ${single.found.cgpa}` : `Roll ${single.target} does not exist`}
            </div>
            <table>
              <thead><tr><th>Algorithm</th><th>Complexity</th><th>Operations</th></tr></thead>
              <tbody>
                <tr><td>Linear</td><td>O(n)</td><td>{single.linear.ops.toLocaleString('en-IN')}</td></tr>
                <tr><td>Binary</td><td>O(log n)</td><td>{single.binary.ops}</td></tr>
                <tr className="winner"><td>Hash</td><td>O(1)</td><td>{single.hash.ops}</td></tr>
              </tbody>
            </table>
            <p className="muted small">Dataset: {single.dataset_size.toLocaleString('en-IN')} records (live DB)</p>
          </>
        )}
      </section>

      <section className="card">
        <h2>Multi-query comparison</h2>
        <p className="muted">The assignment task: total operations for <b>many</b> roll-number searches over the full database.</p>
        <div className="row">
          <select value={queries} onChange={(e) => setQueries(Number(e.target.value))}>
            {[10, 50, 100, 500].map((q) => <option key={q} value={q}>{q} queries</option>)}
          </select>
          <button className="primary" onClick={doBench} disabled={busy}>{busy ? 'Running…' : 'Run comparison'}</button>
        </div>
        {bench && (
          <>
            <table>
              <thead><tr><th>Algorithm</th><th>Total ops</th><th>Avg / query</th><th>Time (µs)</th></tr></thead>
              <tbody>
                <tr><td>Linear O(n)</td><td>{bench.linear.total_ops.toLocaleString('en-IN')}</td><td>{bench.linear.avg_ops}</td><td>{bench.linear.time_us.toLocaleString('en-IN')}</td></tr>
                <tr><td>Binary O(log n)</td><td>{bench.binary.total_ops.toLocaleString('en-IN')}</td><td>{bench.binary.avg_ops}</td><td>{bench.binary.time_us.toLocaleString('en-IN')}</td></tr>
                <tr className="winner"><td>Hash O(1)</td><td>{bench.hash.total_ops.toLocaleString('en-IN')}</td><td>{bench.hash.avg_ops}</td><td>{bench.hash.time_us.toLocaleString('en-IN')}</td></tr>
              </tbody>
            </table>
            <h3>Total operations (log scale)</h3>
            <OpsBars linear={bench.linear.total_ops} binary={bench.binary.total_ops} hash={bench.hash.total_ops} />
            <p className="callout">Hash needs <b>{(bench.linear.total_ops / Math.max(bench.hash.total_ops, 1)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}× fewer operations</b> than linear for these {bench.num_queries} queries. One-time O(n) index → every query O(1).</p>
          </>
        )}
        {err && <p className="error">{err}</p>}
      </section>
    </div>
  );
}
