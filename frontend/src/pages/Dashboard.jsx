import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiStats } from '../api.js';
import { Donut, HBars, OpsBars } from '../components/Charts.jsx';
import { branchName } from '../branches.js';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [err, setErr] = useState('');

  useEffect(() => { apiStats().then(setStats).catch((e) => setErr(e.message)); }, []);

  if (err) return <div className="page"><p className="error">{err}</p></div>;
  if (!stats) return <div className="page"><p className="muted">Loading dashboard…</p></div>;

  const branchData = Object.entries(stats.by_branch).sort().map(([label, value]) => ({ label: `${label} · ${branchName(label)}`, value }));
  const batchData = Object.entries(stats.by_batch).sort().map(([label, value]) => ({ label: `’${label}`, value }));
  const ops = stats.ops_snapshot;

  return (
    <div>
      <section className="stat-grid">
        <div className="card stat"><span>Total students</span><b>{stats.total_students.toLocaleString('en-IN')}</b></div>
        <div className="card stat"><span>Avg CGPA</span><b>{stats.avg_cgpa}</b></div>
        <div className="card stat"><span>Branches</span><b>{branchData.length}</b></div>
        <div className="card stat"><span>Hash ops / 100 queries</span><b className="win">{ops ? ops.hash.total_ops : '—'}</b></div>
      </section>

      <section className="grid2">
        <div className="card">
          <h2>Students by branch</h2>
          <HBars data={branchData} />
        </div>
        <div className="card">
          <h2>Students by batch</h2>
          <Donut data={batchData} />
        </div>
      </section>

      <section className="card">
        <h2>Recently added</h2>
        <table>
          <thead><tr><th>Roll</th><th>Name</th><th>Branch</th><th>Batch</th><th>CGPA</th></tr></thead>
          <tbody>{stats.latest.map((s) => (
            <tr key={s.roll_no}><td>{s.roll_no}</td><td>{s.name}</td><td title={branchName(s.branch)}>{s.branch}</td><td>’{s.batch}</td><td>{s.cgpa}</td></tr>
          ))}</tbody>
        </table>
      </section>

      <section className="card">
        <h2>Search cost snapshot — 100 roll-number lookups</h2>
        <p className="muted">The core assignment question, answered live from this database. Total comparisons for the same 100 queries:</p>
        {ops && <OpsBars linear={ops.linear.total_ops} binary={ops.binary.total_ops} hash={ops.hash.total_ops} />}
        <div className="verdict">
          <div><b>{(ops.linear.total_ops / Math.max(ops.hash.total_ops, 1)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}×</b><span>fewer ops: Hash vs Linear</span></div>
          <div><b>{(ops.binary.total_ops / Math.max(ops.hash.total_ops, 1)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}×</b><span>fewer ops: Hash vs Binary</span></div>
          <div><b>{ops.hash.avg_ops}/query</b><span>hash stays flat at O(1)</span></div>
        </div>
        <p><Link to="/search">Open Search Lab to run your own comparison →</Link></p>
      </section>
    </div>
  );
}
