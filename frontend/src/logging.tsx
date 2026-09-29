import React, { useState, useMemo } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowUpDown,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  FileText,
  Filter,
  GitBranch,
  HeartPulse,
  LockKeyhole,
  Pill,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  X,
} from 'lucide-react';

import {
  CategoryDonut,
  SubjectBarChart,
  TelemetryGrid,
  VitalsSparkline,
  type Memory,
  type Status,
  type Sync,
} from './charts';
import { QuickEntryCards, type EntryType } from './quick-entry';

const CATEGORY_MAP: Record<string, { label: string; icon: React.ComponentType<{ size?: number; className?: string }>; color: string }> = {
  OBSERVATION: { label: 'Observation', icon: Stethoscope, color: 'var(--ctp-blue, #1e66f5)' },
  VITAL_SIGN: { label: 'Vital Signs', icon: HeartPulse, color: 'var(--ctp-teal, #179299)' },
  MEDICATION: { label: 'Medication', icon: Pill, color: 'var(--ctp-mauve, #8839ef)' },
  ALLERGY: { label: 'Allergy / Alert', icon: AlertTriangle, color: 'var(--ctp-peach, #fe640b)' },
  NOTE: { label: 'Clinical Note', icon: ClipboardList, color: 'var(--ctp-yellow, #df8e1d)' },
};

export function VisualLoggingWorkspace({
  memories,
  status,
  sync,
  ready,
  role,
  onInspect,
  onOpenAdd,
  onGoToReview,
  onRefresh,
}: {
  memories: Memory[];
  status: Status | null;
  sync: Sync | null;
  ready: boolean;
  role: string;
  onInspect: (m: Memory) => void;
  onOpenAdd: (type?: EntryType) => void;
  onGoToReview: () => void;
  onRefresh: () => void;
}) {
  // Timeline Filters
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [selectedPrivacy, setSelectedPrivacy] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  // Extract unique subjects from actual memories
  const availableSubjects = useMemo(() => {
    const set = new Set<string>();
    for (const m of memories) {
      if (m.subject) set.add(m.subject);
    }
    return Array.from(set).sort();
  }, [memories]);

  // Filter memories
  const filteredMemories = useMemo(() => {
    return memories
      .filter(m => {
        if (selectedCategory && m.category !== selectedCategory) return false;
        if (selectedSubject) {
          if (selectedSubject === 'Shared reference' && m.subject !== null) return false;
          if (selectedSubject !== 'Shared reference' && m.subject !== selectedSubject) return false;
        }
        if (selectedPrivacy) {
          if (selectedPrivacy === 'PERSONAL' && m.privacy !== 'HIGHLY_SENSITIVE') return false;
          if (selectedPrivacy === 'WORKSPACE' && (m.privacy !== 'SENSITIVE' || m.fixture)) return false;
          if (selectedPrivacy === 'REFERENCE' && !m.fixture) return false;
        }
        if (selectedStatus) {
          if (selectedStatus === 'CONFLICT' && !m.conflicting) return false;
          if (selectedStatus === 'INDEXED' && m.index_state !== 'indexed') return false;
          if (selectedStatus === 'PENDING' && m.index_state === 'indexed') return false;
        }
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          const matchTitle = m.title.toLowerCase().includes(q);
          const matchContent = (m.content || '').toLowerCase().includes(q);
          const matchSubject = (m.subject || '').toLowerCase().includes(q);
          const matchCat = m.category.toLowerCase().includes(q);
          if (!matchTitle && !matchContent && !matchSubject && !matchCat) return false;
        }
        return true;
      })
      .sort((a, b) => (sortOrder === 'desc' ? b.created - a.created : a.created - b.created));
  }, [memories, selectedCategory, selectedSubject, selectedPrivacy, selectedStatus, searchQuery, sortOrder]);

  const hasActiveFilters = Boolean(
    selectedCategory || selectedSubject || selectedPrivacy || selectedStatus || searchQuery.trim()
  );

  function resetFilters() {
    setSelectedCategory(null);
    setSelectedSubject(null);
    setSelectedPrivacy(null);
    setSelectedStatus(null);
    setSearchQuery('');
  }

  const conflictsCount = status?.conflicts ?? 0;

  const formatDate = (t: number) => {
    return new Date(t * 1000).toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="logging-workspace">
      {/* 1. Top Telemetry Status Strip */}
      <section className="workspace-section" aria-label="System status telemetry">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">Local telemetry & health</span>
            <h2>System status indicators</h2>
          </div>
          <button className="secondary btn-sm" onClick={onRefresh} title="Refresh local status">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
        <TelemetryGrid status={status} sync={sync} ready={ready} />
      </section>

      {/* 2. Quick-Entry Clinical Logging Cards */}
      <section className="workspace-section" aria-label="Quick-entry clinical forms">
        <QuickEntryCards onSelectType={type => onOpenAdd(type)} />
      </section>

      {/* 3. Real-Data Analytics & Charts */}
      <section className="workspace-section" aria-label="Visual data analytics">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">Real data analytics</span>
            <h2>Observation monitoring</h2>
          </div>
        </div>

        <div className="charts-grid">
          <CategoryDonut
            memories={memories}
            selectedCategory={selectedCategory}
            onSelectCategory={cat => setSelectedCategory(cat)}
          />
          <SubjectBarChart
            memories={memories}
            selectedSubject={selectedSubject}
            onSelectSubject={sub => setSelectedSubject(sub)}
          />
        </div>

        {/* Vital Signs Trend Sparkline if vitals exist */}
        <VitalsSparkline memories={memories} subject={selectedSubject} />
      </section>

      {/* 4. Conflict Warning / Needs Review Banner */}
      {conflictsCount > 0 && (
        <div className="conflict-alert-banner" role="alert">
          <div className="conflict-alert-content">
            <GitBranch size={20} className="conflict-icon" />
            <div>
              <b>{conflictsCount} conflicting observation branch{conflictsCount === 1 ? '' : 'es'} detected</b>
              <p>Concurrent offline edits produced diverging branches in the canonical SQLCipher store.</p>
            </div>
          </div>
          <button className="primary btn-sm" onClick={onGoToReview}>
            Review & resolve
          </button>
        </div>
      )}

      {/* 5. Real-Time Observation Timeline */}
      <section className="workspace-section timeline-section" aria-label="Real-time observation timeline">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">Chronological feed</span>
            <h2>Observation timeline</h2>
          </div>
          <button className="primary btn-sm" onClick={() => onOpenAdd('STANDARD')}>
            <Plus size={15} /> Add observation
          </button>
        </div>

        {/* Interactive Filters Bar */}
        <div className="timeline-toolbar">
          {/* Search box within timeline */}
          <div className="timeline-search">
            <Search size={16} />
            <input
              type="search"
              aria-label="Filter observation timeline"
              placeholder="Filter timeline by symptom, drug, subject..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="icon-sm" onClick={() => setSearchQuery('')} aria-label="Clear filter search">
                <X size={14} />
              </button>
            )}
          </div>

          {/* Quick Category filter buttons */}
          <div className="category-filter-pills" role="radiogroup" aria-label="Category filter">
            <button
              type="button"
              className={`pill-btn ${selectedCategory === null ? 'active' : ''}`}
              onClick={() => setSelectedCategory(null)}
            >
              All ({memories.length})
            </button>
            {Object.entries(CATEGORY_MAP).map(([cat, info]) => {
              const count = memories.filter(m => m.category === cat).length;
              if (count === 0 && selectedCategory !== cat) return null;
              return (
                <button
                  key={cat}
                  type="button"
                  className={`pill-btn ${selectedCategory === cat ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                >
                  <span className="dot" style={{ backgroundColor: info.color }} />
                  {info.label} ({count})
                </button>
              );
            })}
          </div>

          {/* Dropdown selectors for Subject, Privacy, Status, and Sort */}
          <div className="filter-dropdowns">
            {availableSubjects.length > 0 && (
              <select
                aria-label="Filter by subject"
                value={selectedSubject ?? ''}
                onChange={e => setSelectedSubject(e.target.value || null)}
                className="select-filter"
              >
                <option value="">All subjects</option>
                {availableSubjects.map(s => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
                <option value="Shared reference">Shared references</option>
              </select>
            )}

            <select
              aria-label="Filter by privacy"
              value={selectedPrivacy ?? ''}
              onChange={e => setSelectedPrivacy(e.target.value || null)}
              className="select-filter"
            >
              <option value="">All scopes</option>
              <option value="WORKSPACE">Workspace (Shared)</option>
              <option value="PERSONAL">Personal (Private)</option>
              <option value="REFERENCE">Approved Reference</option>
            </select>

            <select
              aria-label="Filter by status"
              value={selectedStatus ?? ''}
              onChange={e => setSelectedStatus(e.target.value || null)}
              className="select-filter"
            >
              <option value="">All statuses</option>
              <option value="INDEXED">Searchable</option>
              <option value="PENDING">Indexing</option>
              {conflictsCount > 0 && <option value="CONFLICT">Needs review</option>}
            </select>

            <button
              type="button"
              className="secondary btn-sm sort-btn"
              onClick={() => setSortOrder(prev => (prev === 'desc' ? 'asc' : 'desc'))}
              title={`Sorting: ${sortOrder === 'desc' ? 'Newest first' : 'Oldest first'}`}
            >
              <ArrowUpDown size={14} /> {sortOrder === 'desc' ? 'Newest' : 'Oldest'}
            </button>
          </div>
        </div>

        {/* Active Filters Reset Bar */}
        {hasActiveFilters && (
          <div className="active-filters-bar">
            <span>
              Showing <b>{filteredMemories.length}</b> of {memories.length} observations
            </span>
            <button className="chart-reset" onClick={resetFilters}>
              Reset all filters
            </button>
          </div>
        )}

        {/* Timeline Stream */}
        <div className="timeline-stream">
          {filteredMemories.length === 0 ? (
            <div className="timeline-empty">
              <ClipboardList size={32} />
              <h4>No observations match your filters</h4>
              <p>Try clearing your search query or selecting a different filter.</p>
              {hasActiveFilters && (
                <button className="secondary" onClick={resetFilters}>
                  Clear filters
                </button>
              )}
            </div>
          ) : (
            filteredMemories.map(m => {
              const catInfo = CATEGORY_MAP[m.category] || CATEGORY_MAP.OBSERVATION;
              const Icon = catInfo.icon;
              return (
                <article
                  key={m.id}
                  className={`timeline-card ${m.conflicting ? 'has-conflict' : ''}`}
                  onClick={() => onInspect(m)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onInspect(m);
                    }
                  }}
                  aria-label={`Observation: ${m.title}`}
                >
                  <div className="timeline-node">
                    <span className="timeline-icon-box" style={{ color: catInfo.color, backgroundColor: `color-mix(in srgb, ${catInfo.color} 15%, var(--bg-canvas))` }}>
                      <Icon size={18} />
                    </span>
                    <span className="timeline-line" />
                  </div>

                  <div className="timeline-content-card">
                    <div className="timeline-card-header">
                      <div className="header-meta">
                        <span className="badge-cat" style={{ color: catInfo.color, borderColor: `color-mix(in srgb, ${catInfo.color} 30%, transparent)` }}>
                          {catInfo.label}
                        </span>
                        <span className="badge-sub">{m.subject || 'Shared reference'}</span>
                        <span className="badge-time">
                          <Clock size={12} style={{ verticalAlign: -1 }} /> {formatDate(m.created)}
                        </span>
                      </div>

                      <div className="header-badges">
                        {m.fixture ? (
                          <span className="badge teal">Approved reference</span>
                        ) : m.privacy === 'HIGHLY_SENSITIVE' ? (
                          <span className="badge purple">
                            <LockKeyhole size={11} style={{ verticalAlign: -1 }} /> Personal
                          </span>
                        ) : (
                          <span className="badge">Workspace</span>
                        )}

                        {m.conflicting ? (
                          <span className="badge warn">
                            <GitBranch size={11} style={{ verticalAlign: -1 }} /> Needs review
                          </span>
                        ) : m.index_state === 'indexed' ? (
                          <span className="badge good">
                            <CheckCircle2 size={11} style={{ verticalAlign: -1 }} /> Searchable
                          </span>
                        ) : (
                          <span className="badge">Indexing</span>
                        )}
                      </div>
                    </div>

                    <h4 className="timeline-card-title">{m.title}</h4>

                    {m.content && <p className="timeline-card-excerpt">{m.content}</p>}

                    <div className="timeline-card-footer">
                      <span className="inspect-prompt">
                        Inspect & edit <ChevronRight size={14} />
                      </span>
                    </div>
                  </div>
                </article>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}
