import React, { useState, useMemo } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Clock,
  Cloud,
  CloudOff,
  Cpu,
  Database,
  Eye,
  FileSearch,
  Filter,
  FlaskConical,
  HardDrive,
  Info,
  LockKeyhole,
  Package,
  Play,
  RefreshCw,
  RotateCcw,
  Send,
  ServerCrash,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
  Signal,
  SquareX,
  Wifi,
  WifiOff,
  X,
  Zap,
} from 'lucide-react';

import type { Memory, Status, Sync } from './charts';

/** ─── Types ──────────────────────────────────────────────────────────────── */

type Event = { action: string; time: number; device: string };

type QueueItem = Sync['items'][number];
type QueueState = 'pending' | 'in_flight' | 'acknowledged' | 'retry_wait' | 'failed' | 'cancelled' | 'not_applicable';

/** ─── Helpers ────────────────────────────────────────────────────────────── */

const formatTs = (t?: number) =>
  t
    ? new Date(t * 1000).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—';

const formatAgo = (t?: number) => {
  if (!t) return '—';
  const diff = Math.floor((Date.now() / 1000 - t));
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};

const STATE_META: Record<
  QueueState,
  { label: string; color: string; icon: React.ComponentType<{ size?: number; className?: string }> }
> = {
  pending: { label: 'Pending', color: 'var(--ctp-yellow, #df8e1d)', icon: Clock },
  in_flight: { label: 'Sending…', color: 'var(--ctp-blue, #1e66f5)', icon: Send },
  acknowledged: { label: 'Accepted centrally', color: 'var(--ctp-green, #40a02b)', icon: BadgeCheck },
  retry_wait: { label: 'Retrying', color: 'var(--ctp-peach, #fe640b)', icon: RotateCcw },
  failed: { label: 'Failed', color: 'var(--ctp-red, #d20f39)', icon: AlertCircle },
  cancelled: { label: 'Cancelled', color: 'var(--ctp-overlay0, #9ca0b0)', icon: SquareX },
  not_applicable: { label: 'Not applicable', color: 'var(--ctp-overlay0, #9ca0b0)', icon: Info },
};

const CONNECTION_META: Record<
  string,
  { label: string; color: string; icon: React.ComponentType<{ size?: number; className?: string }> }
> = {
  connected: { label: 'Shared service connected', color: 'var(--ctp-green, #40a02b)', icon: Wifi },
  unavailable: { label: 'Shared service unavailable', color: 'var(--ctp-red, #d20f39)', icon: WifiOff },
  paused: { label: 'Sharing paused', color: 'var(--ctp-yellow, #df8e1d)', icon: CloudOff },
  unknown: { label: 'Checking shared service', color: 'var(--ctp-overlay0, #9ca0b0)', icon: Signal },
  stale: { label: 'Shared status out of date', color: 'var(--ctp-peach, #fe640b)', icon: AlertTriangle },
  attention: { label: 'Sharing needs attention', color: 'var(--ctp-peach, #fe640b)', icon: AlertTriangle },
  verification_error: { label: 'Sharing verification failed', color: 'var(--ctp-red, #d20f39)', icon: ShieldAlert },
};

/** ─── Sub-components ─────────────────────────────────────────────────────── */

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  sublabel,
  onClick,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  value: string | number;
  color?: string;
  sublabel?: string;
  onClick?: () => void;
}) {
  return (
    <button
      className={`sm-stat-card ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <span className="sm-stat-icon" style={{ color: color ?? 'var(--accent)' }}>
        <Icon size={18} />
      </span>
      <span className="sm-stat-value" style={{ color: color }}>
        {value}
      </span>
      <span className="sm-stat-label">{label}</span>
      {sublabel && <span className="sm-stat-sub">{sublabel}</span>}
    </button>
  );
}

function QueueItemRow({ item, index }: { item: QueueItem; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const meta = STATE_META[(item.state as QueueState)] ?? STATE_META.not_applicable;
  const StateIcon = meta.icon;

  return (
    <div className={`sm-queue-item ${item.state === 'failed' ? 'failed' : item.state === 'acknowledged' ? 'acked' : ''}`}>
      <button
        className="sm-queue-row"
        onClick={() => setExpanded(x => !x)}
        aria-expanded={expanded}
      >
        <span className="sm-queue-index">{index + 1}</span>
        <span className="sm-queue-label">
          <b>Approved synthetic reference update</b>
          <small>Operation {item.id.slice(0, 8)}… · {item.attempts} attempt{item.attempts !== 1 ? 's' : ''}{item.error ? ` · ${item.error}` : ''}</small>
        </span>
        <span className="sm-queue-state" style={{ color: meta.color }}>
          <StateIcon size={14} />
          {meta.label}
        </span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {expanded && (
        <div className="sm-queue-detail">
          <div className="sm-detail-grid">
            <div>
              <label>Operation ID</label>
              <code>{item.id}</code>
            </div>
            <div>
              <label>State</label>
              <span style={{ color: meta.color }}>{meta.label}</span>
            </div>
            <div>
              <label>Delivery attempts</label>
              <span>{item.attempts}</span>
            </div>
            {item.error && (
              <div className="sm-detail-error">
                <label>Last error</label>
                <span>{item.error}</span>
              </div>
            )}
          </div>
          <p className="sm-queue-note">
            <LockKeyhole size={12} />
            Private observations never enter this queue. Only explicitly approved synthetic reference variants can be shared.
          </p>
        </div>
      )}
    </div>
  );
}

function ConnectivityPanel({
  sync,
  busy,
  onToggleTransport,
  onSyncNow,
  onRefreshSnapshot,
  status,
}: {
  sync: Sync | null;
  busy: boolean;
  onToggleTransport: () => void;
  onSyncNow: () => void;
  onRefreshSnapshot: () => void;
  status: Status | null;
}) {
  const connMeta = CONNECTION_META[sync?.connection ?? 'unknown'] ?? CONNECTION_META.unknown;
  const ConnIcon = connMeta.icon;

  const pending = (sync?.counts?.pending ?? 0) + (sync?.counts?.retry_wait ?? 0);
  const failed = sync?.counts?.failed ?? 0;
  const acked = sync?.counts?.acknowledged ?? 0;

  return (
    <div className="sm-connectivity">
      {/* Connection status hero */}
      <div className="sm-conn-hero">
        <span className="sm-conn-icon" style={{ color: connMeta.color }}>
          <ConnIcon size={28} />
        </span>
        <div className="sm-conn-info">
          <h2>{connMeta.label}</h2>
          <p>Last verified contact: {formatAgo(sync?.last_sync)} ({formatTs(sync?.last_sync)})</p>
        </div>
        <div className="sm-conn-actions">
          <button
            className="secondary"
            disabled={busy}
            onClick={onToggleTransport}
          >
            {sync?.enabled ? (
              <><CloudOff size={15} /> Pause sharing</>
            ) : (
              <><Cloud size={15} /> Enable sharing</>
            )}
          </button>
          <button
            className="primary"
            disabled={busy || !sync?.enabled}
            onClick={onSyncNow}
          >
            <RefreshCw size={15} />
            Sync now
          </button>
        </div>
      </div>

      {sync?.error && (
        <div className="sm-conn-error">
          <AlertCircle size={16} />
          {sync.error}
        </div>
      )}

      {/* Queue summary stats */}
      <div className="sm-queue-stats">
        <StatCard
          icon={Clock}
          label="Waiting / retrying"
          value={pending}
          color={pending > 0 ? 'var(--ctp-yellow, #df8e1d)' : undefined}
        />
        <StatCard
          icon={AlertCircle}
          label="Need attention"
          value={failed}
          color={failed > 0 ? 'var(--ctp-red, #d20f39)' : undefined}
        />
        <StatCard
          icon={BadgeCheck}
          label="Accepted centrally"
          value={acked}
          color={acked > 0 ? 'var(--ctp-green, #40a02b)' : undefined}
        />
        <StatCard
          icon={LockKeyhole}
          label="Private (local only)"
          value={status?.local_only ?? 0}
          color="var(--ctp-mauve, #8839ef)"
          sublabel="Never shared"
        />
      </div>

      <p className="sm-queue-disclaimer">
        <Info size={13} />
        Central acceptance does not confirm receipt on another device. Check Device B to demonstrate delivery.
        Only explicitly approved synthetic reference variants can be queued. Private observations never appear here.
      </p>
    </div>
  );
}

function QueuePanel({
  sync,
  filter,
  onFilterChange,
}: {
  sync: Sync | null;
  filter: string;
  onFilterChange: (f: string) => void;
}) {
  const items = useMemo(() => {
    if (!sync?.items?.length) return [];
    const f = filter;
    if (f === 'all') return [...sync.items].reverse();
    return [...sync.items].filter(i => i.state === f).reverse();
  }, [sync, filter]);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const item of sync?.items ?? []) {
      c[item.state] = (c[item.state] ?? 0) + 1;
    }
    return c;
  }, [sync]);

  const filterOptions = [
    { value: 'all', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'in_flight', label: 'In flight' },
    { value: 'retry_wait', label: 'Retrying' },
    { value: 'acknowledged', label: 'Accepted' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' },
  ];

  return (
    <div className="sm-queue-panel">
      <div className="sm-queue-header">
        <h2><Package size={18} /> Outbound queue</h2>
        <div className="sm-filter-row">
          <Filter size={14} />
          {filterOptions.map(opt => (
            <button
              key={opt.value}
              className={`sm-filter-chip ${filter === opt.value ? 'active' : ''}`}
              onClick={() => onFilterChange(opt.value)}
            >
              {opt.label}
              {opt.value !== 'all' && counts[opt.value] ? (
                <span className="sm-chip-count">{counts[opt.value]}</span>
              ) : null}
            </button>
          ))}
        </div>
      </div>

      {items.length === 0 ? (
        <div className="sm-queue-empty">
          <ShieldCheck size={32} />
          <h3>No items in this view</h3>
          <p>
            {filter === 'all'
              ? 'No approved updates are queued. Private observations never enter this queue.'
              : `No ${filter.replaceAll('_', ' ')} items. Private observations are always kept local.`}
          </p>
        </div>
      ) : (
        <div className="sm-queue-list">
          {items.slice(0, 60).map((item, i) => (
            <QueueItemRow key={item.id} item={item} index={i} />
          ))}
          {items.length > 60 && (
            <p className="sm-queue-truncate">Showing 60 of {items.length} items. Older entries are retained in the encrypted outbox.</p>
          )}
        </div>
      )}
    </div>
  );
}

function ActivityPanel({
  events,
  onRefresh,
}: {
  events: Event[];
  onRefresh: () => void;
}) {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search.trim()) return events;
    const q = search.toLowerCase();
    return events.filter(
      e => e.action.toLowerCase().includes(q) || e.device.toLowerCase().includes(q),
    );
  }, [events, search]);

  const grouped = useMemo(() => {
    const byDay: Record<string, Event[]> = {};
    for (const e of filtered) {
      const day = new Date(e.time * 1000).toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
      if (!byDay[day]) byDay[day] = [];
      byDay[day].push(e);
    }
    return Object.entries(byDay);
  }, [filtered]);

  return (
    <div className="sm-activity-panel">
      <div className="sm-activity-header">
        <h2><Activity size={18} /> Activity history</h2>
        <div className="sm-activity-actions">
          <div className="sm-search-small">
            <FileSearch size={14} />
            <input
              placeholder="Filter events…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              aria-label="Filter activity events"
            />
            {search && (
              <button onClick={() => setSearch('')} aria-label="Clear filter">
                <X size={12} />
              </button>
            )}
          </div>
          <button className="secondary sm-btn-compact" onClick={onRefresh}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {grouped.length === 0 ? (
        <div className="sm-activity-empty">
          <Clock size={28} />
          <p>{search ? 'No matching events.' : 'No activity recorded yet.'}</p>
        </div>
      ) : (
        <div className="sm-activity-timeline">
          {grouped.map(([day, dayEvents]) => (
            <div key={day} className="sm-activity-day">
              <div className="sm-day-label">{day}</div>
              {dayEvents.map((e, i) => (
                <div key={i} className="sm-activity-event">
                  <span className="sm-event-dot" />
                  <div className="sm-event-body">
                    <b>{e.action.replaceAll('_', ' ')}</b>
                    <span>{e.device}</span>
                  </div>
                  <time className="sm-event-time">{formatAgo(e.time)}</time>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      <p className="sm-activity-note">
        <LockKeyhole size={12} />
        Metadata-only audit events. Chaining is verified at startup; it does not prove protection against whole-store rollback.
      </p>
    </div>
  );
}

function StoragePanel({ status }: { status: Status | null }) {
  const total = status?.total ?? 0;
  const indexed = status?.indexed ?? 0;
  const localOnly = status?.local_only ?? 0;
  const conflicts = status?.conflicts ?? 0;
  const indexPct = total > 0 ? Math.round((indexed / total) * 100) : 0;

  return (
    <div className="sm-storage-panel">
      <h2><HardDrive size={18} /> Storage & index status</h2>

      <div className="sm-storage-grid">
        <div className="sm-storage-card">
          <div className="sm-storage-label">Encrypted vault</div>
          <div className="sm-storage-value">
            {status?.vault ? (
              <><ShieldCheck size={16} style={{ color: 'var(--ctp-green, #40a02b)' }} /> Verified at startup</>
            ) : (
              <><ShieldOff size={16} style={{ color: 'var(--ctp-overlay0, #9ca0b0)' }} /> Test environment</>
            )}
          </div>
          {status?.database && <div className="sm-storage-sub">{status.database}</div>}
        </div>

        <div className="sm-storage-card">
          <div className="sm-storage-label">Vector engine</div>
          <div className="sm-storage-value">
            <Database size={16} style={{ color: 'var(--accent)' }} />
            {status?.engine ?? 'Qdrant Edge'}
          </div>
          {status?.model && <div className="sm-storage-sub">Model: {status.model}</div>}
        </div>

        <div className="sm-storage-card">
          <div className="sm-storage-label">Total records</div>
          <div className="sm-storage-value" style={{ color: 'var(--accent)' }}>
            <Database size={16} />{total}
          </div>
          <div className="sm-storage-sub">{localOnly} local only · {conflicts} in conflict</div>
        </div>

        <div className="sm-storage-card">
          <div className="sm-storage-label">Index coverage</div>
          <div className="sm-storage-value" style={{ color: indexPct === 100 ? 'var(--ctp-green, #40a02b)' : 'var(--ctp-yellow, #df8e1d)' }}>
            <Cpu size={16} />{indexPct}%
          </div>
          <div className="sm-storage-sub">{indexed} of {total} searchable</div>
        </div>
      </div>

      {/* Index progress bar */}
      <div className="sm-index-bar-wrap">
        <div className="sm-index-bar-header">
          <span>Search index</span>
          <span>{indexed}/{total} indexed</span>
        </div>
        <div className="sm-index-bar">
          <div
            className="sm-index-fill"
            style={{ width: `${indexPct}%` }}
            role="progressbar"
            aria-valuenow={indexPct}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      </div>

      {status?.worker_error && (
        <div className="sm-worker-error">
          <ServerCrash size={16} />
          <div>
            <b>Worker error</b>
            <p>{status.worker_error}</p>
          </div>
        </div>
      )}
    </div>
  );
}

/** Memory Lab — synthetic simulation controls */
function MemoryLabPanel({
  sync,
  busy,
  onToggleTransport,
  onSyncNow,
  onRefreshSnapshot,
}: {
  sync: Sync | null;
  busy: boolean;
  onToggleTransport: () => void;
  onSyncNow: () => void;
  onRefreshSnapshot: () => void;
}) {
  const [labStep, setLabStep] = useState<number | null>(null);

  const steps = [
    {
      icon: Play,
      title: 'Transport enabled',
      description: 'Sharing is currently ' + (sync?.enabled ? 'on' : 'off') + '. Approved reference records can leave this device.',
      color: 'var(--ctp-green, #40a02b)',
      action: sync?.enabled ? 'Pause transport' : 'Enable transport',
      onAction: onToggleTransport,
    },
    {
      icon: RefreshCw,
      title: 'Manual sync',
      description: 'Trigger an immediate sync attempt. Approved records in the outbox will be sent to the central service.',
      color: 'var(--ctp-blue, #1e66f5)',
      action: 'Sync now',
      onAction: onSyncNow,
      disabled: !sync?.enabled,
    },
    {
      icon: Package,
      title: 'Reference cache',
      description: 'Refresh the signed reference cache. Search always runs locally; this updates the shared reference index.',
      color: 'var(--ctp-mauve, #8839ef)',
      action: 'Refresh reference cache',
      onAction: onRefreshSnapshot,
      disabled: !sync?.enabled,
    },
    {
      icon: ShieldCheck,
      title: 'Policy invariants',
      description: 'Private observations (SENSITIVE, HIGHLY_SENSITIVE) are permanently local. No UI control can override privacy policy.',
      color: 'var(--ctp-teal, #179299)',
      readonly: true,
    },
    {
      icon: Eye,
      title: 'Canary check',
      description: 'In a real deployment, inject a recognizable synthetic canary into private notes and verify it never appears in the outbound queue, central stores, or network traffic.',
      color: 'var(--ctp-peach, #fe640b)',
      readonly: true,
    },
  ];

  return (
    <div className="sm-lab-panel">
      <div className="sm-lab-header">
        <h2><FlaskConical size={18} /> Memory Lab</h2>
        <p>
          Synthetic-only simulation controls. Use these to demonstrate the offline-first, privacy-by-default workflow
          without real patient data. Controls pause transport, replay sync, and inspect policy decisions.
        </p>
      </div>

      <div className="sm-lab-steps">
        {steps.map((step, i) => {
          const StepIcon = step.icon;
          return (
            <div
              key={i}
              className={`sm-lab-step ${labStep === i ? 'expanded' : ''}`}
            >
              <button
                className="sm-lab-step-header"
                onClick={() => setLabStep(labStep === i ? null : i)}
                aria-expanded={labStep === i}
              >
                <span className="sm-lab-step-num" style={{ background: step.color }}>
                  <StepIcon size={14} />
                </span>
                <span className="sm-lab-step-title">{step.title}</span>
                {labStep === i ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>

              {labStep === i && (
                <div className="sm-lab-step-body">
                  <p>{step.description}</p>
                  {!step.readonly && (
                    <button
                      className="primary sm-btn-compact"
                      disabled={busy || step.disabled}
                      onClick={step.onAction}
                    >
                      <ArrowRight size={14} />
                      {step.action}
                    </button>
                  )}
                  {step.readonly && (
                    <p className="sm-lab-invariant">
                      <LockKeyhole size={13} />
                      This is a hard system invariant, not a configurable option.
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="sm-lab-footnote">
        <Zap size={13} />
        Memory Lab scenarios are synthetic only. No real patient data is loaded, shared, or stored by this application.
      </div>
    </div>
  );
}

/** ─── Main export ────────────────────────────────────────────────────────── */

interface SyncMonitorWorkspaceProps {
  sync: Sync | null;
  status: Status | null;
  memories: Memory[];
  events: Event[];
  busy: boolean;
  ready: boolean;
  role: string;
  onToggleTransport: () => void;
  onSyncNow: () => void;
  onRefreshSnapshot: () => void;
  onRefreshActivity: () => void;
  onRefresh: () => void;
}

export function SyncMonitorWorkspace({
  sync,
  status,
  memories: _memories,
  events,
  busy,
  ready,
  role,
  onToggleTransport,
  onSyncNow,
  onRefreshSnapshot,
  onRefreshActivity,
  onRefresh,
}: SyncMonitorWorkspaceProps) {
  const [queueFilter, setQueueFilter] = useState('all');
  const [activeTab, setActiveTab] = useState<'queue' | 'activity' | 'storage' | 'lab'>('queue');

  const tabs: { id: typeof activeTab; label: string; icon: React.ComponentType<{ size?: number; className?: string }> }[] = [
    { id: 'queue', label: 'Outbound queue', icon: Package },
    { id: 'activity', label: 'Activity', icon: Activity },
    { id: 'storage', label: 'Storage & index', icon: HardDrive },
    ...(role === 'admin' ? [{ id: 'lab' as const, label: 'Memory Lab', icon: FlaskConical }] : []),
  ];

  return (
    <div className="sm-workspace">
      {/* Connectivity hero */}
      <ConnectivityPanel
        sync={sync}
        busy={busy}
        onToggleTransport={onToggleTransport}
        onSyncNow={onSyncNow}
        onRefreshSnapshot={onRefreshSnapshot}
        status={status}
      />

      {/* Ready / offline warning */}
      {!ready && (
        <div className="sm-offline-warn">
          <ServerCrash size={16} />
          Local service unavailable — saving and sync cannot be confirmed until the service restarts.
        </div>
      )}

      {/* Tabs */}
      <div className="sm-tabs" role="tablist" aria-label="Sync monitor sections">
        {tabs.map(tab => {
          const TabIcon = tab.icon;
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`sm-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <TabIcon size={15} />
              {tab.label}
            </button>
          );
        })}
        <button
          className="sm-tab-refresh"
          onClick={onRefresh}
          disabled={busy}
          aria-label="Refresh sync status"
        >
          <RefreshCw size={14} className={busy ? 'spin' : ''} />
        </button>
      </div>

      {/* Tab content */}
      <div className="sm-tab-content" role="tabpanel">
        {activeTab === 'queue' && (
          <QueuePanel
            sync={sync}
            filter={queueFilter}
            onFilterChange={setQueueFilter}
          />
        )}
        {activeTab === 'activity' && (
          <ActivityPanel
            events={events}
            onRefresh={onRefreshActivity}
          />
        )}
        {activeTab === 'storage' && (
          <StoragePanel status={status} />
        )}
        {activeTab === 'lab' && role === 'admin' && (
          <MemoryLabPanel
            sync={sync}
            busy={busy}
            onToggleTransport={onToggleTransport}
            onSyncNow={onSyncNow}
            onRefreshSnapshot={onRefreshSnapshot}
          />
        )}
      </div>

      {/* Reference cache action */}
      <details className="sm-diag-details">
        <summary>
          <ChevronRight size={14} />
          Reference cache &amp; diagnostics
        </summary>
        <div className="sm-diag-body">
          <p>Search always runs locally. A signed reference-cache refresh is optional and only updates the shared reference index.</p>
          <div className="sm-diag-actions">
            <button
              className="secondary"
              disabled={busy || !sync?.enabled}
              onClick={onRefreshSnapshot}
            >
              <Package size={14} />
              Refresh reference cache
            </button>
          </div>
          <p>
            Encrypted vault: {status?.vault ? 'Verified at startup' : 'Test environment'} ·{' '}
            {status?.engine ?? 'Qdrant Edge'} · SQLCipher
          </p>
        </div>
      </details>
    </div>
  );
}
