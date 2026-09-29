import React from 'react';
import { Database, HardDrive, Layers, LockKeyhole, Search, ShieldCheck, Wifi, WifiOff } from 'lucide-react';

export type Memory = {
  id: string;
  title: string;
  content?: string;
  subject: string | null;
  category: string;
  privacy: string;
  release: string;
  heads: string[];
  revisions?: Array<{ id: string; content: string; created: number; parents: string[]; variant: number; device: string }>;
  fixture: string | null;
  conflicting: boolean;
  index_state: string;
  created: number;
  matched_revision_id?: string;
  reason?: string;
};

export type Status = {
  generation: number;
  deployment: string;
  workspace: string;
  role: string;
  device: string;
  total: number;
  local_only: number;
  conflicts: number;
  indexed: number;
  vault: boolean;
  worker_error: string | null;
  database?: string;
  engine?: string;
  model?: string;
};

export type Sync = {
  enabled: boolean;
  connection: string;
  error: string | null;
  last_sync?: number;
  counts: Record<string, number>;
  items: Array<{ id: string; state: string; attempts: number; error: string | null }>;
};

const CATEGORY_COLORS: Record<string, { color: string; label: string }> = {
  OBSERVATION: { color: 'var(--ctp-blue, #1e66f5)', label: 'Observation' },
  VITAL_SIGN: { color: 'var(--ctp-teal, #179299)', label: 'Vital Signs' },
  MEDICATION: { color: 'var(--ctp-mauve, #8839ef)', label: 'Medication' },
  ALLERGY: { color: 'var(--ctp-peach, #fe640b)', label: 'Allergy / Alert' },
  NOTE: { color: 'var(--ctp-yellow, #df8e1d)', label: 'Clinical Note' },
};

/**
 * Interactive SVG Donut Chart for Categories
 */
export function CategoryDonut({
  memories,
  selectedCategory,
  onSelectCategory,
}: {
  memories: Memory[];
  selectedCategory: string | null;
  onSelectCategory: (cat: string | null) => void;
}) {
  const counts: Record<string, number> = {
    OBSERVATION: 0,
    VITAL_SIGN: 0,
    MEDICATION: 0,
    ALLERGY: 0,
    NOTE: 0,
  };

  for (const m of memories) {
    if (counts[m.category] !== undefined) {
      counts[m.category]++;
    } else {
      counts.OBSERVATION = (counts.OBSERVATION || 0) + 1;
    }
  }

  const total = memories.length;
  const categories = Object.keys(counts).filter(k => counts[k] > 0);

  // SVG coordinate calculations (center 80, 80; outer R 64, inner R 42)
  const cx = 80;
  const cy = 80;
  const R = 64;
  const r = 42;

  let cumulativeAngle = -Math.PI / 2;
  const slices = categories.map(cat => {
    const value = counts[cat];
    const fraction = total > 0 ? value / total : 0;
    const angle = fraction * 2 * Math.PI;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + angle;
    cumulativeAngle = endAngle;

    const x1 = cx + R * Math.cos(startAngle);
    const y1 = cy + R * Math.sin(startAngle);
    const x2 = cx + R * Math.cos(endAngle);
    const y2 = cy + R * Math.sin(endAngle);

    const ix1 = cx + r * Math.cos(endAngle);
    const iy1 = cy + r * Math.sin(endAngle);
    const ix2 = cx + r * Math.cos(startAngle);
    const iy2 = cy + r * Math.sin(startAngle);

    const largeArc = angle > Math.PI ? 1 : 0;
    const isSingle = categories.length === 1;

    const pathData = isSingle
      ? `M ${cx} ${cy - R} A ${R} ${R} 0 1 1 ${cx - 0.001} ${cy - R} L ${cx - 0.001} ${cy - r} A ${r} ${r} 0 1 0 ${cx} ${cy - r} Z`
      : `M ${x1} ${y1} A ${R} ${R} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${r} ${r} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;

    return {
      category: cat,
      count: value,
      percent: Math.round(fraction * 100),
      pathData,
      color: CATEGORY_COLORS[cat]?.color || 'var(--accent)',
      label: CATEGORY_COLORS[cat]?.label || cat,
    };
  });

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h3>Category distribution</h3>
          <p className="chart-sub">Real records by synthetic observation type</p>
        </div>
        {selectedCategory && (
          <button className="chart-reset" onClick={() => onSelectCategory(null)}>
            Show all
          </button>
        )}
      </div>

      <div className="donut-wrap">
        <svg viewBox="0 0 160 160" className="donut-svg" role="img" aria-label="Category distribution chart">
          {total === 0 ? (
            <circle cx={cx} cy={cy} r={(R + r) / 2} fill="none" stroke="var(--border-subtle)" strokeWidth={R - r} />
          ) : (
            slices.map(s => {
              const active = !selectedCategory || selectedCategory === s.category;
              return (
                <path
                  key={s.category}
                  d={s.pathData}
                  fill={s.color}
                  opacity={active ? 1 : 0.25}
                  className="donut-slice"
                  onClick={() => onSelectCategory(selectedCategory === s.category ? null : s.category)}
                  style={{ cursor: 'pointer', transition: 'opacity 150ms ease, transform 150ms ease' }}
                >
                  <title>{`${s.label}: ${s.count} (${s.percent}%)`}</title>
                </path>
              );
            })
          )}
          <text x={cx} y={cy - 2} textAnchor="middle" className="donut-count">
            {total}
          </text>
          <text x={cx} y={cy + 16} textAnchor="middle" className="donut-label">
            Records
          </text>
        </svg>

        <div className="donut-legend">
          {Object.entries(CATEGORY_COLORS).map(([cat, info]) => {
            const count = counts[cat] || 0;
            const pct = total > 0 ? Math.round((count / total) * 100) : 0;
            const isSelected = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                className={`legend-pill ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectCategory(isSelected ? null : cat)}
                title={`Filter by ${info.label}`}
              >
                <span className="legend-dot" style={{ backgroundColor: info.color }} />
                <span className="legend-name">{info.label}</span>
                <span className="legend-val">
                  {count} <small>({pct}%)</small>
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * Interactive Horizontal Bar Chart for Synthetic Subjects
 */
export function SubjectBarChart({
  memories,
  selectedSubject,
  onSelectSubject,
}: {
  memories: Memory[];
  selectedSubject: string | null;
  onSelectSubject: (sub: string | null) => void;
}) {
  const subjectCounts: Record<string, number> = {};
  for (const m of memories) {
    const s = m.subject || 'Shared reference';
    subjectCounts[s] = (subjectCounts[s] || 0) + 1;
  }

  const entries = Object.entries(subjectCounts).sort((a, b) => b[1] - a[1]);
  const max = entries.length > 0 ? Math.max(...entries.map(e => e[1])) : 1;

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h3>Observations by subject</h3>
          <p className="chart-sub">Volume distribution across synthetic clinical subjects</p>
        </div>
        {selectedSubject && (
          <button className="chart-reset" onClick={() => onSelectSubject(null)}>
            Show all
          </button>
        )}
      </div>

      <div className="bars-wrap">
        {entries.length === 0 ? (
          <p className="chart-empty">No subject data recorded yet.</p>
        ) : (
          entries.slice(0, 6).map(([subject, count]) => {
            const isSelected = selectedSubject === subject;
            const widthPct = Math.max(8, Math.round((count / max) * 100));
            return (
              <div
                key={subject}
                className={`subject-bar-row ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectSubject(isSelected ? null : subject)}
                role="button"
                tabIndex={0}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectSubject(isSelected ? null : subject);
                  }
                }}
              >
                <div className="subject-bar-label">
                  <b>{subject}</b>
                  <span>{count} log{count === 1 ? '' : 's'}</span>
                </div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: subject === 'Shared reference' ? 'var(--ctp-teal, #179299)' : 'var(--accent)',
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/**
 * Storage, Search, Index, and Sync Telemetry Header Grid
 */
export function TelemetryGrid({
  status,
  sync,
  ready,
}: {
  status: Status | null;
  sync: Sync | null;
  ready: boolean;
}) {
  const pendingUpdates = (sync?.counts?.pending ?? 0) + (sync?.counts?.retry_wait ?? 0);
  const total = status?.total ?? 0;
  const indexed = status?.indexed ?? 0;
  const indexPct = total > 0 ? Math.round((indexed / total) * 100) : 100;

  return (
    <div className="telemetry-grid">
      {/* 1. Storage Status Card */}
      <div className="telemetry-card">
        <div className="telemetry-icon-box storage">
          <HardDrive size={18} />
        </div>
        <div className="telemetry-body">
          <span className="telemetry-tag">Canonical Storage</span>
          <h4 className="telemetry-title">
            {status?.vault ? 'Encrypted Vault' : 'Local Database'}
          </h4>
          <p className="telemetry-desc">
            {status?.database || 'SQLCipher WAL'} · AES-256
          </p>
          <div className="telemetry-footer">
            <span className={status?.vault ? 'status-indicator green' : 'status-indicator blue'}>
              ● {ready ? 'Mounted & Active' : 'Offline'}
            </span>
            <small>Gen {status?.generation ?? 0}</small>
          </div>
        </div>
      </div>

      {/* 2. Retrieval Engine Status Card */}
      <div className="telemetry-card">
        <div className="telemetry-icon-box search">
          <Search size={18} />
        </div>
        <div className="telemetry-body">
          <span className="telemetry-tag">Retrieval Engine</span>
          <h4 className="telemetry-title">Qdrant Edge</h4>
          <p className="telemetry-desc">
            {status?.model ? 'bge-small-en-v1.5' : 'Local ONNX'} · Hybrid RRF
          </p>
          <div className="telemetry-footer">
            <span className="status-indicator green">● 100% Offline</span>
            <small>Zero egress</small>
          </div>
        </div>
      </div>

      {/* 3. Index Pipeline Status Card */}
      <div className="telemetry-card">
        <div className="telemetry-icon-box index">
          <Layers size={18} />
        </div>
        <div className="telemetry-body">
          <span className="telemetry-tag">Indexing Pipeline</span>
          <h4 className="telemetry-title">
            {indexed} / {total} Searchable
          </h4>
          <div className="mini-progress-track" title={`${indexPct}% Indexed`}>
            <div
              className="mini-progress-fill"
              style={{
                width: `${indexPct}%`,
                backgroundColor: status?.worker_error ? 'var(--warning)' : 'var(--success)',
              }}
            />
          </div>
          <div className="telemetry-footer">
            <span className={status?.worker_error ? 'status-indicator orange' : 'status-indicator green'}>
              ● {status?.worker_error ? 'Worker Delayed' : 'Continuous Index'}
            </span>
            <small>{total - indexed} pending</small>
          </div>
        </div>
      </div>

      {/* 4. Selective Sync Card */}
      <div className="telemetry-card">
        <div className="telemetry-icon-box sync">
          {sync?.connection === 'connected' ? <Wifi size={18} /> : <WifiOff size={18} />}
        </div>
        <div className="telemetry-body">
          <span className="telemetry-tag">Selective Sync</span>
          <h4 className="telemetry-title">
            {sync?.connection === 'connected' ? 'Shared Connected' : sync?.enabled ? 'Sharing Active' : 'Sharing Paused'}
          </h4>
          <p className="telemetry-desc">
            {pendingUpdates} approved reference{pendingUpdates === 1 ? '' : 's'} queued
          </p>
          <div className="telemetry-footer">
            <span className="status-indicator purple">
              <LockKeyhole size={11} style={{ verticalAlign: -1 }} /> Notes stay local
            </span>
            <small>{status?.device || 'edge-a'}</small>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Subject Vital Signs Trend Sparkline (derived from real VITAL_SIGN records)
 */
export function VitalsSparkline({ memories, subject }: { memories: Memory[]; subject?: string | null }) {
  const vitalNotes = memories
    .filter(m => m.category === 'VITAL_SIGN' && (!subject || m.subject === subject))
    .sort((a, b) => a.created - b.created);

  if (vitalNotes.length < 2) return null;

  // Extract numeric HR or Temp from title/content if present
  const points: Array<{ time: number; hr?: number; temp?: number }> = [];
  for (const m of vitalNotes) {
    const text = (m.title + ' ' + (m.content || '')).toLowerCase();
    const hrMatch = text.match(/hr\s*[:=]?\s*(\d{2,3})/i) || text.match(/(\d{2,3})\s*bpm/i);
    const tempMatch = text.match(/temp\s*[:=]?\s*(\d{2}(?:\.\d)?)/i) || text.match(/(\d{2}\.\d)\s*°?c/i);
    if (hrMatch || tempMatch) {
      points.push({
        time: m.created,
        hr: hrMatch ? parseInt(hrMatch[1], 10) : undefined,
        temp: tempMatch ? parseFloat(tempMatch[1]) : undefined,
      });
    }
  }

  const hrPoints = points.filter(p => p.hr !== undefined && p.hr >= 40 && p.hr <= 200);
  if (hrPoints.length < 2) return null;

  const minHr = Math.min(...hrPoints.map(p => p.hr!));
  const maxHr = Math.max(...hrPoints.map(p => p.hr!));
  const range = maxHr - minHr || 10;
  const width = 280;
  const height = 48;
  const padding = 6;

  const coords = hrPoints.map((p, idx) => {
    const x = padding + (idx / (hrPoints.length - 1)) * (width - padding * 2);
    const y = height - padding - ((p.hr! - minHr) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  const lastHr = hrPoints[hrPoints.length - 1].hr;

  return (
    <div className="vitals-sparkline-card">
      <div className="sparkline-header">
        <span className="sparkline-title">Heart Rate trend (Synthetic {subject || 'Cohort'})</span>
        <span className="sparkline-latest">{lastHr} bpm</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="sparkline-svg" aria-label="Heart rate trend line">
        <polyline
          fill="none"
          stroke="var(--ctp-teal, #179299)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={coords.join(' ')}
        />
        {hrPoints.map((p, idx) => {
          const x = padding + (idx / (hrPoints.length - 1)) * (width - padding * 2);
          const y = height - padding - ((p.hr! - minHr) / range) * (height - padding * 2);
          return <circle key={idx} cx={x} cy={y} r="3" fill="var(--ctp-teal, #179299)" />;
        })}
      </svg>
      <div className="sparkline-range">
        <span>Min: {minHr} bpm</span>
        <span>Max: {maxHr} bpm</span>
      </div>
    </div>
  );
}
