import React from 'react';

const COLORS = ['#3b82f6', '#18a957', '#f5a524', '#e5484d', '#8b5cf6', '#14b8a6', '#ec4899'];

/** Horizontal bars: {label, value} — values scaled linearly. */
export function HBars({ data }) {
  const max = Math.max(1, ...data.map((d) => d.value));
  return (
    <div>
      {data.map((d, i) => (
        <div className="bar-row" key={d.label}>
          <span className="bar-label">{d.label}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${Math.max(3, (d.value / max) * 100)}%`, background: COLORS[i % COLORS.length] }} />
          </div>
          <span className="bar-val">{d.value.toLocaleString('en-IN')}</span>
        </div>
      ))}
    </div>
  );
}

/** Log-scale bars for ops comparison (linear dwarfs the rest otherwise). */
export function OpsBars({ linear, binary, hash }) {
  const rows = [
    { label: 'Linear O(n)', value: linear, color: '#e5484d' },
    { label: 'Binary O(log n)', value: binary, color: '#f5a524' },
    { label: 'Hash O(1)', value: hash, color: '#18a957' },
  ];
  const max = Math.max(linear, binary, hash);
  return (
    <div>
      {rows.map((r) => {
        const pct = Math.max(2, (Math.log10(r.value + 1) / Math.log10(max + 1)) * 100);
        return (
          <div className="bar-row" key={r.label}>
            <span className="bar-label">{r.label}</span>
            <div className="bar-track"><div className="bar-fill" style={{ width: `${pct}%`, background: r.color }} /></div>
            <span className="bar-val">{r.value.toLocaleString('en-IN')}</span>
          </div>
        );
      })}
    </div>
  );
}

/** Simple donut for year distribution. */
export function Donut({ data }) {
  const total = Math.max(1, data.reduce((a, d) => a + d.value, 0));
  let acc = 0;
  const segs = data.map((d, i) => {
    const frac = d.value / total;
    const seg = { ...d, start: acc, end: acc + frac, color: COLORS[i % COLORS.length] };
    acc += frac;
    return seg;
  });
  const polar = (f) => [50 + 38 * Math.cos(2 * Math.PI * f - Math.PI / 2), 50 + 38 * Math.sin(2 * Math.PI * f - Math.PI / 2)];
  return (
    <div className="donut-wrap">
      <svg viewBox="0 0 100 100" className="donut">
        <circle cx="50" cy="50" r="38" fill="none" stroke="#0b1428" strokeWidth="16" />
        {segs.map((s) => {
          const [x1, y1] = polar(s.start);
          const [x2, y2] = polar(s.end);
          const large = s.end - s.start > 0.5 ? 1 : 0;
          return <path key={s.label} d={`M ${x1} ${y1} A 38 38 0 ${large} 1 ${x2} ${y2}`} fill="none" stroke={s.color} strokeWidth="16" />;
        })}
        <text x="50" y="54" textAnchor="middle" fill="#eaf0ff" fontSize="13" fontWeight="700">{total.toLocaleString('en-IN')}</text>
      </svg>
      <div className="legend">
        {segs.map((s) => (
          <span key={s.label}><i style={{ background: s.color }} />{s.label}: {s.value.toLocaleString('en-IN')}</span>
        ))}
      </div>
    </div>
  );
}
