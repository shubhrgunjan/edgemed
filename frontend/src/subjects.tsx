import React, { useState, useMemo } from 'react';
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  ExternalLink,
  FileText,
  Filter,
  Flame,
  GitBranch,
  HeartPulse,
  Info,
  LockKeyhole,
  Pill,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Stethoscope,
  Thermometer,
  User,
  Users,
  Wind,
  X,
} from 'lucide-react';

import type { Memory, Status } from './charts';
import type { EntryType } from './quick-entry';

/**
 * Category styling map for consistent badges and icons
 */
const CATEGORY_MAP: Record<
  string,
  { label: string; icon: React.ComponentType<{ size?: number; className?: string }>; color: string }
> = {
  OBSERVATION: { label: 'Observation', icon: Stethoscope, color: 'var(--ctp-blue, #1e66f5)' },
  VITAL_SIGN: { label: 'Vital Signs', icon: HeartPulse, color: 'var(--ctp-teal, #179299)' },
  MEDICATION: { label: 'Medication', icon: Pill, color: 'var(--ctp-mauve, #8839ef)' },
  ALLERGY: { label: 'Allergy / Alert', icon: AlertTriangle, color: 'var(--ctp-peach, #fe640b)' },
  NOTE: { label: 'Clinical Note', icon: ClipboardList, color: 'var(--ctp-yellow, #df8e1d)' },
};

/**
 * Format timestamp in human-readable clinical format
 */
const formatDate = (t?: number) =>
  t
    ? new Date(t * 1000).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Unknown time';

const formatShortDate = (t?: number) =>
  t
    ? new Date(t * 1000).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—';

/**
 * Parse structured vitals data from real stored Memory records
 */
type VitalReading = {
  time: number;
  memoryId: string;
  heartRate?: number;
  temperature?: number;
  systolic?: number;
  diastolic?: number;
  spO2?: number;
  respRate?: number;
  rawText: string;
};

function parseVitalsFromMemories(memories: Memory[]): VitalReading[] {
  const readings: VitalReading[] = [];

  for (const m of memories) {
    if (m.category !== 'VITAL_SIGN') continue;
    const text = `${m.title} ${m.content || ''}`;

    // 1. Heart Rate (bpm)
    const hrMatch = text.match(/(?:hr|heart\s*rate)\s*[:=]?\s*(\d{2,3})/i) || text.match(/(\d{2,3})\s*bpm/i);
    const hr = hrMatch ? parseInt(hrMatch[1], 10) : undefined;

    // 2. Blood Pressure (systolic / diastolic mmHg)
    const bpMatch =
      text.match(/(?:bp|blood\s*pressure)\s*[:=]?\s*(\d{2,3})\s*[/]\s*(\d{2,3})/i) ||
      text.match(/(\d{2,3})\s*[/]\s*(\d{2,3})\s*(?:mmhg)?/i);
    const systolic = bpMatch ? parseInt(bpMatch[1], 10) : undefined;
    const diastolic = bpMatch ? parseInt(bpMatch[2], 10) : undefined;

    // 3. Body Temperature (°C)
    const tempMatch =
      text.match(/(?:temp(?:erature)?)\s*[:=]?\s*(\d{2}(?:\.\d)?)/i) ||
      text.match(/(\d{2}(?:\.\d)?)\s*°?\s*c\b/i);
    const temp = tempMatch ? parseFloat(tempMatch[1]) : undefined;

    // 4. Oxygen Saturation SpO2 (%)
    const spo2Match =
      text.match(/(?:spo2|oxygen\s*saturation)\s*(?:\(spo2\))?\s*[:=]?\s*(\d{2,3})/i) ||
      text.match(/(\d{2,3})\s*%\s*(?:spo2)?/i);
    const spo2 = spo2Match ? parseInt(spo2Match[1], 10) : undefined;

    // 5. Respiratory Rate (/min)
    const rrMatch =
      text.match(/(?:rr|resp(?:iratory)?\s*rate)\s*[:=]?\s*(\d{1,2})/i) ||
      text.match(/(\d{1,2})\s*\/\s*min/i);
    const rr = rrMatch ? parseInt(rrMatch[1], 10) : undefined;

    if (hr || systolic || temp || spo2 || rr) {
      readings.push({
        time: m.created,
        memoryId: m.id,
        heartRate: hr && hr >= 30 && hr <= 220 ? hr : undefined,
        temperature: temp && temp >= 33 && temp <= 43 ? temp : undefined,
        systolic: systolic && systolic >= 60 && systolic <= 260 ? systolic : undefined,
        diastolic: diastolic && diastolic >= 30 && diastolic <= 160 ? diastolic : undefined,
        spO2: spo2 && spo2 >= 60 && spo2 <= 100 ? spo2 : undefined,
        respRate: rr && rr >= 6 && rr <= 60 ? rr : undefined,
        rawText: text,
      });
    }
  }

  // Sort chronological (oldest to newest for trend curves)
  return readings.sort((a, b) => a.time - b.time);
}

/**
 * Parsed Allergy Structure from real stored memories
 */
type ParsedAllergy = {
  id: string;
  allergen: string;
  reaction: string;
  severity: string;
  status: string;
  guidance: string;
  created: number;
  memory: Memory;
};

function parseAllergies(memories: Memory[]): ParsedAllergy[] {
  return memories
    .filter(m => m.category === 'ALLERGY')
    .map(m => {
      const text = `${m.title}\n${m.content || ''}`;

      const allergenMatch = text.match(/Allergen:\s*([^\n\r]+)/i) || text.match(/Allergy(?:\s+Alert)?:\s*([^\n\r-]+)/i);
      const allergen = allergenMatch ? allergenMatch[1].trim() : m.title.replace(/^Allergy(?:\s+Alert)?:\s*/i, '').trim();

      const reactionMatch = text.match(/(?:Adverse\s+)?Reaction:\s*([^\n\r]+)/i);
      const reaction = reactionMatch ? reactionMatch[1].trim() : 'Adverse clinical reaction documented';

      const severityMatch = text.match(/Severity:\s*([^\n\r]+)/i) || text.match(/\((Severe|Moderate|Mild)\)/i);
      const severity = severityMatch ? severityMatch[1].trim() : 'Moderate';

      const statusMatch = text.match(/Status:\s*([^\n\r]+)/i);
      const status = statusMatch ? statusMatch[1].trim() : 'Confirmed';

      const guidanceMatch = text.match(/(?:Clinical\s+Guidance|Contraindication|Avoid):\s*([^\n\r]+)/i);
      const guidance = guidanceMatch
        ? guidanceMatch[1].trim()
        : 'Avoid direct administration; verify with ordering clinician before compounding.';

      return {
        id: m.id,
        allergen,
        reaction,
        severity,
        status,
        guidance,
        created: m.created,
        memory: m,
      };
    });
}

/**
 * Parsed Medication Structure from real stored memories
 */
type ParsedMedication = {
  id: string;
  drugName: string;
  dosage: string;
  route: string;
  frequency: string;
  indication: string;
  created: number;
  memory: Memory;
};

function parseMedications(memories: Memory[]): ParsedMedication[] {
  return memories
    .filter(m => m.category === 'MEDICATION')
    .map(m => {
      const text = `${m.title}\n${m.content || ''}`;

      const explicitDrugMatch = text.match(/Medication\s+Name:\s*([^\n\r]+)/i);
      const fallbackDrugMatch = text.match(/Medication:\s*([^\n\r]+)/i);
      let drugName = explicitDrugMatch
        ? explicitDrugMatch[1].trim()
        : fallbackDrugMatch
        ? fallbackDrugMatch[1].trim().replace(/\s+\d+.*$/, '')
        : m.title.replace(/^Medication:\s*/i, '').replace(/\s+\d+.*$/, '').trim();

      const dosageMatch = text.match(/Dosage(?:\s*&\s*Unit)?:\s*([^\n\r]+)/i);
      const dosage = dosageMatch ? dosageMatch[1].trim() : 'Standard dose';

      const routeMatch = text.match(/Route:\s*([^\n\r]+)/i);
      const route = routeMatch ? routeMatch[1].trim() : 'Oral';

      const freqMatch = text.match(/Frequency(?:\s*\/\s*Schedule)?:\s*([^\n\r]+)/i);
      const frequency = freqMatch ? freqMatch[1].trim() : 'Scheduled';

      const indMatch = text.match(/Indication:\s*([^\n\r]+)/i);
      const indication = indMatch ? indMatch[1].trim() : 'Clinical maintenance';

      return {
        id: m.id,
        drugName,
        dosage,
        route,
        frequency,
        indication,
        created: m.created,
        memory: m,
      };
    });
}

/**
 * Interactive SVG Sparkline Component for Vitals
 */
function VitalTrendChart({
  title,
  unit,
  points,
  getValue,
  color,
  normalRange,
  criticalHigh,
  criticalLow,
}: {
  title: string;
  unit: string;
  points: VitalReading[];
  getValue: (p: VitalReading) => number | undefined;
  color: string;
  normalRange?: { min: number; max: number };
  criticalHigh?: number;
  criticalLow?: number;
}) {
  const validPoints = points
    .map(p => ({ time: p.time, value: getValue(p) }))
    .filter((p): p is { time: number; value: number } => p.value !== undefined);

  if (validPoints.length === 0) {
    return (
      <div className="vital-card empty-vital">
        <div className="vital-card-header">
          <span className="vital-name">{title}</span>
          <span className="vital-unit">{unit}</span>
        </div>
        <p className="vital-empty-text">No recorded readings</p>
      </div>
    );
  }

  const latest = validPoints[validPoints.length - 1];
  const isHigh = criticalHigh !== undefined && latest.value >= criticalHigh;
  const isLow = criticalLow !== undefined && latest.value <= criticalLow;

  if (validPoints.length === 1) {
    return (
      <div className={`vital-card single-reading ${isHigh || isLow ? 'alert' : ''}`}>
        <div className="vital-card-header">
          <span className="vital-name">{title}</span>
          <span className="vital-badge-tag">{formatShortDate(latest.time)}</span>
        </div>
        <div className="vital-value-row">
          <span className="vital-big-value" style={{ color }}>
            {latest.value}
          </span>
          <span className="vital-unit">{unit}</span>
        </div>
        <div className="vital-single-sub">
          <span className="vital-status-pill">1 recorded observation</span>
          {normalRange && (
            <span className="vital-normal-range">
              Normal: {normalRange.min}–{normalRange.max} {unit}
            </span>
          )}
        </div>
      </div>
    );
  }

  // 2+ readings: SVG chart
  const minVal = Math.min(...validPoints.map(p => p.value));
  const maxVal = Math.max(...validPoints.map(p => p.value));
  const range = maxVal - minVal || 1;
  const width = 240;
  const height = 56;
  const padX = 8;
  const padY = 8;

  const coords = validPoints.map((p, idx) => {
    const x = padX + (idx / (validPoints.length - 1)) * (width - padX * 2);
    const y = height - padY - ((p.value - minVal) / range) * (height - padY * 2);
    return { x, y, value: p.value, time: p.time };
  });

  const polylinePoints = coords.map(c => `${c.x},${c.y}`).join(' ');

  return (
    <div className={`vital-card ${isHigh || isLow ? 'alert' : ''}`}>
      <div className="vital-card-header">
        <span className="vital-name">{title}</span>
        <div className="vital-header-right">
          <span className="vital-reading-count">{validPoints.length} logs</span>
          <span className="vital-badge-tag">{formatShortDate(latest.time)}</span>
        </div>
      </div>

      <div className="vital-value-row">
        <span className="vital-big-value" style={{ color }}>
          {latest.value}
        </span>
        <span className="vital-unit">{unit}</span>
        {isHigh && <span className="vital-alert-pill high">High</span>}
        {isLow && <span className="vital-alert-pill low">Low</span>}
      </div>

      <div className="vital-chart-container">
        <svg viewBox={`0 0 ${width} ${height}`} className="vital-svg" role="img" aria-label={`${title} trend chart`}>
          {/* Subtle normal range zone if provided */}
          {normalRange && minVal < normalRange.max && maxVal > normalRange.min && (
            <line
              x1={padX}
              y1={height / 2}
              x2={width - padX}
              y2={height / 2}
              stroke="var(--border-subtle)"
              strokeDasharray="2,3"
            />
          )}

          {/* Trend line */}
          <polyline
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={polylinePoints}
          />

          {/* Individual measurement points */}
          {coords.map((c, i) => (
            <circle
              key={i}
              cx={c.x}
              cy={c.y}
              r={i === coords.length - 1 ? 4 : 3}
              fill={i === coords.length - 1 ? color : 'var(--bg-canvas)'}
              stroke={color}
              strokeWidth="2"
            >
              <title>{`${c.value} ${unit} at ${formatDate(c.time)}`}</title>
            </circle>
          ))}
        </svg>
      </div>

      <div className="vital-stats-footer">
        <span>Min: {minVal}</span>
        {normalRange && (
          <span className="normal-hint">
            Ref: {normalRange.min}–{normalRange.max}
          </span>
        )}
        <span>Max: {maxVal}</span>
      </div>
    </div>
  );
}

/**
 * Dual Blood Pressure Trend Chart Component
 */
function BloodPressureChart({ readings }: { readings: VitalReading[] }) {
  const bpPoints = readings
    .filter(r => r.systolic !== undefined && r.diastolic !== undefined)
    .map(r => ({
      time: r.time,
      systolic: r.systolic!,
      diastolic: r.diastolic!,
    }));

  if (bpPoints.length === 0) {
    return (
      <div className="vital-card empty-vital">
        <div className="vital-card-header">
          <span className="vital-name">Blood Pressure</span>
          <span className="vital-unit">mmHg</span>
        </div>
        <p className="vital-empty-text">No recorded BP readings</p>
      </div>
    );
  }

  const latest = bpPoints[bpPoints.length - 1];
  const isHigh = latest.systolic >= 140 || latest.diastolic >= 90;

  if (bpPoints.length === 1) {
    return (
      <div className={`vital-card single-reading ${isHigh ? 'alert' : ''}`}>
        <div className="vital-card-header">
          <span className="vital-name">Blood Pressure</span>
          <span className="vital-badge-tag">{formatShortDate(latest.time)}</span>
        </div>
        <div className="vital-value-row">
          <span className="vital-big-value" style={{ color: 'var(--ctp-peach, #fe640b)' }}>
            {latest.systolic}
          </span>
          <span className="vital-slash">/</span>
          <span className="vital-big-value" style={{ color: 'var(--ctp-teal, #179299)' }}>
            {latest.diastolic}
          </span>
          <span className="vital-unit">mmHg</span>
          {isHigh && <span className="vital-alert-pill high">Elevated</span>}
        </div>
        <div className="vital-single-sub">
          <span className="vital-status-pill">1 recorded observation</span>
          <span className="vital-normal-range">Normal: &lt;120/&lt;80 mmHg</span>
        </div>
      </div>
    );
  }

  const allVals = [...bpPoints.map(p => p.systolic), ...bpPoints.map(p => p.diastolic)];
  const minVal = Math.min(...allVals);
  const maxVal = Math.max(...allVals);
  const range = maxVal - minVal || 1;
  const width = 240;
  const height = 56;
  const padX = 8;
  const padY = 8;

  const sysCoords = bpPoints.map((p, idx) => {
    const x = padX + (idx / (bpPoints.length - 1)) * (width - padX * 2);
    const y = height - padY - ((p.systolic - minVal) / range) * (height - padY * 2);
    return { x, y, value: p.systolic, time: p.time };
  });

  const diaCoords = bpPoints.map((p, idx) => {
    const x = padX + (idx / (bpPoints.length - 1)) * (width - padX * 2);
    const y = height - padY - ((p.diastolic - minVal) / range) * (height - padY * 2);
    return { x, y, value: p.diastolic, time: p.time };
  });

  return (
    <div className={`vital-card ${isHigh ? 'alert' : ''}`}>
      <div className="vital-card-header">
        <span className="vital-name">Blood Pressure</span>
        <div className="vital-header-right">
          <span className="vital-reading-count">{bpPoints.length} logs</span>
          <span className="vital-badge-tag">{formatShortDate(latest.time)}</span>
        </div>
      </div>

      <div className="vital-value-row">
        <span className="vital-big-value" style={{ color: 'var(--ctp-peach, #fe640b)' }}>
          {latest.systolic}
        </span>
        <span className="vital-slash">/</span>
        <span className="vital-big-value" style={{ color: 'var(--ctp-teal, #179299)' }}>
          {latest.diastolic}
        </span>
        <span className="vital-unit">mmHg</span>
        {isHigh && <span className="vital-alert-pill high">Stage 1+</span>}
      </div>

      <div className="vital-chart-container">
        <svg viewBox={`0 0 ${width} ${height}`} className="vital-svg" role="img" aria-label="Blood pressure trend chart">
          {/* Systolic curve */}
          <polyline
            fill="none"
            stroke="var(--ctp-peach, #fe640b)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={sysCoords.map(c => `${c.x},${c.y}`).join(' ')}
          />
          {/* Diastolic curve */}
          <polyline
            fill="none"
            stroke="var(--ctp-teal, #179299)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={diaCoords.map(c => `${c.x},${c.y}`).join(' ')}
          />

          {sysCoords.map((c, i) => (
            <circle
              key={`sys-${i}`}
              cx={c.x}
              cy={c.y}
              r={i === sysCoords.length - 1 ? 4 : 2.5}
              fill="var(--ctp-peach, #fe640b)"
            >
              <title>{`Systolic: ${c.value} mmHg at ${formatDate(c.time)}`}</title>
            </circle>
          ))}
          {diaCoords.map((c, i) => (
            <circle
              key={`dia-${i}`}
              cx={c.x}
              cy={c.y}
              r={i === diaCoords.length - 1 ? 4 : 2.5}
              fill="var(--ctp-teal, #179299)"
            >
              <title>{`Diastolic: ${c.value} mmHg at ${formatDate(c.time)}`}</title>
            </circle>
          ))}
        </svg>
      </div>

      <div className="vital-stats-footer">
        <span style={{ color: 'var(--ctp-peach, #fe640b)' }}>● Sys: {latest.systolic}</span>
        <span className="normal-hint">Ref: &lt;120/&lt;80</span>
        <span style={{ color: 'var(--ctp-teal, #179299)' }}>● Dia: {latest.diastolic}</span>
      </div>
    </div>
  );
}

/**
 * Main Subjects Workspace Component
 */
export function SubjectsWorkspace({
  memories,
  status,
  role,
  onInspect,
  onOpenAdd,
  onGoToReview,
  onRefresh,
}: {
  memories: Memory[];
  status: Status | null;
  role: string;
  onInspect: (m: Memory) => void;
  onOpenAdd: (type?: EntryType, subject?: string) => void;
  onGoToReview: () => void;
  onRefresh?: () => void;
}) {
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  const [subjectSearch, setSubjectSearch] = useState('');
  const [timelineCategory, setTimelineCategory] = useState<string | null>(null);
  const [timelineSearch, setTimelineSearch] = useState('');
  const [onlyConflicts, setOnlyConflicts] = useState(false);
  const [mobileView, setMobileView] = useState<'roster' | 'chart'>('roster');

  // Group and aggregate canonical subjects directly from memories array
  const subjectsMap = useMemo(() => {
    const map = new Map<
      string,
      {
        id: string;
        observations: Memory[];
        lastActivity: number;
        hasConflicts: boolean;
        hasAllergies: boolean;
        categoryCounts: Record<string, number>;
      }
    >();

    for (const m of memories) {
      // Subjects are synthetic identifiers (e.g. SYN-001, SYN-002)
      if (!m.subject) continue;
      const subId = m.subject.trim();

      if (!map.has(subId)) {
        map.set(subId, {
          id: subId,
          observations: [],
          lastActivity: m.created,
          hasConflicts: false,
          hasAllergies: false,
          categoryCounts: {
            OBSERVATION: 0,
            VITAL_SIGN: 0,
            MEDICATION: 0,
            ALLERGY: 0,
            NOTE: 0,
          },
        });
      }

      const entry = map.get(subId)!;
      entry.observations.push(m);
      if (m.created > entry.lastActivity) entry.lastActivity = m.created;
      if (m.conflicting) entry.hasConflicts = true;
      if (m.category === 'ALLERGY') entry.hasAllergies = true;
      if (entry.categoryCounts[m.category] !== undefined) {
        entry.categoryCounts[m.category]++;
      } else {
        entry.categoryCounts.OBSERVATION = (entry.categoryCounts.OBSERVATION || 0) + 1;
      }
    }

    return map;
  }, [memories]);

  // List of subject summaries sorted by ID
  const subjectsList = useMemo(() => {
    const list = Array.from(subjectsMap.values());
    // Natural synthetic subject ordering: SYN-001, SYN-002, etc.
    return list.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));
  }, [subjectsMap]);

  // Filtered subject list for roster search
  const filteredSubjects = useMemo(() => {
    if (!subjectSearch.trim()) return subjectsList;
    const q = subjectSearch.toLowerCase().trim();
    return subjectsList.filter(s => {
      if (s.id.toLowerCase().includes(q)) return true;
      return s.observations.some(
        o => o.title.toLowerCase().includes(q) || (o.content && o.content.toLowerCase().includes(q))
      );
    });
  }, [subjectsList, subjectSearch]);

  // Auto-select first subject if none selected and subjects exist (for desktop)
  const activeSubjectId = selectedSubjectId ?? (subjectsList.length > 0 ? subjectsList[0].id : null);
  const activeSubjectData = activeSubjectId ? subjectsMap.get(activeSubjectId) : null;

  // Selected subject's observations sorted newest first
  const subjectObservations = useMemo(() => {
    if (!activeSubjectData) return [];
    return [...activeSubjectData.observations].sort((a, b) => b.created - a.created);
  }, [activeSubjectData]);

  // Filtered timeline observations for active subject
  const filteredTimeline = useMemo(() => {
    return subjectObservations.filter(m => {
      if (timelineCategory && m.category !== timelineCategory) return false;
      if (onlyConflicts && !m.conflicting) return false;
      if (timelineSearch.trim()) {
        const q = timelineSearch.toLowerCase().trim();
        const matchTitle = m.title.toLowerCase().includes(q);
        const matchContent = m.content ? m.content.toLowerCase().includes(q) : false;
        if (!matchTitle && !matchContent) return false;
      }
      return true;
    });
  }, [subjectObservations, timelineCategory, onlyConflicts, timelineSearch]);

  // Parsed clinical collections for active subject
  const vitalReadings = useMemo(() => parseVitalsFromMemories(subjectObservations), [subjectObservations]);
  const allergies = useMemo(() => parseAllergies(subjectObservations), [subjectObservations]);
  const medications = useMemo(() => parseMedications(subjectObservations), [subjectObservations]);
  const conflictObservations = useMemo(() => subjectObservations.filter(m => m.conflicting), [subjectObservations]);

  // Handlers for subject selection
  const handleSelectSubject = (id: string) => {
    setSelectedSubjectId(id);
    setTimelineCategory(null);
    setTimelineSearch('');
    setOnlyConflicts(false);
    setMobileView('chart');
  };

  const handleClearSubject = () => {
    setSelectedSubjectId(null);
    setMobileView('roster');
  };

  return (
    <div className="subjects-workspace">
      {/* 1. LEFT PANEL: Synthetic Subject Roster Sidebar */}
      <aside className={`subject-roster-panel ${mobileView === 'chart' ? 'mobile-hidden' : ''}`}>
        <div className="roster-header">
          <div className="roster-header-top">
            <div className="roster-title-box">
              <Users size={18} className="roster-icon" />
              <h3>Synthetic Subjects</h3>
            </div>
            <span className="roster-count-badge">{filteredSubjects.length} subjects</span>
          </div>
          <p className="roster-sub">Isolated local test cohort from SQLCipher vault</p>

          <div className="roster-search-bar">
            <Search size={15} />
            <input
              placeholder="Search SYN-001, vitals, allergies…"
              value={subjectSearch}
              onChange={e => setSubjectSearch(e.target.value)}
              aria-label="Search synthetic subjects"
            />
            {subjectSearch && (
              <button
                className="icon-clear"
                onClick={() => setSubjectSearch('')}
                aria-label="Clear subject search"
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>

        <div className="roster-list" role="list" aria-label="Synthetic subject list">
          {filteredSubjects.map(sub => {
            const isSelected = activeSubjectId === sub.id;
            return (
              <div
                key={sub.id}
                role="listitem"
                className={`subject-roster-card ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectSubject(sub.id)}
                tabIndex={0}
                onKeyDown={e => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleSelectSubject(sub.id);
                  }
                }}
              >
                <div className="roster-card-top">
                  <div className="roster-id-row">
                    <User size={15} className="user-icon" />
                    <b className="subject-id-text">{sub.id}</b>
                  </div>
                  <span className="roster-obs-count">
                    {sub.observations.length} log{sub.observations.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="roster-card-meta">
                  <span className="roster-time">Active: {formatShortDate(sub.lastActivity)}</span>
                </div>

                {/* Status Badges */}
                <div className="roster-badges-row">
                  {sub.hasConflicts && (
                    <span className="roster-badge warning" title="Branch divergence requires human review">
                      <GitBranch size={11} /> Needs review
                    </span>
                  )}
                  {sub.hasAllergies && (
                    <span className="roster-badge alert" title="Documented confirmed drug allergy">
                      <AlertTriangle size={11} /> Allergy alert
                    </span>
                  )}
                  {sub.categoryCounts.VITAL_SIGN > 0 && (
                    <span className="roster-badge vitals">
                      <HeartPulse size={11} /> {sub.categoryCounts.VITAL_SIGN} vitals
                    </span>
                  )}
                  {sub.categoryCounts.MEDICATION > 0 && (
                    <span className="roster-badge meds">
                      <Pill size={11} /> {sub.categoryCounts.MEDICATION} meds
                    </span>
                  )}
                </div>

                <div className="roster-card-hover-arrow">
                  <ChevronRight size={15} />
                </div>
              </div>
            );
          })}

          {filteredSubjects.length === 0 && (
            <div className="roster-empty">
              <Users size={24} />
              <p>No synthetic subjects match &ldquo;{subjectSearch}&rdquo;</p>
              <button className="secondary btn-sm" onClick={() => setSubjectSearch('')}>
                Reset filter
              </button>
            </div>
          )}
        </div>

        <div className="roster-footer">
          <button
            className="secondary roster-add-btn"
            onClick={() => onOpenAdd('STANDARD', activeSubjectId || 'SYN-001')}
          >
            <Plus size={15} /> Log new synthetic observation
          </button>
        </div>
      </aside>

      {/* 2. RIGHT PANEL: Consolidated Patient Chart Workspace */}
      <section className={`patient-chart-panel ${mobileView === 'roster' ? 'mobile-hidden' : ''}`}>
        {activeSubjectData ? (
          <>
            {/* Mobile Back Button to Roster */}
            <div className="chart-mobile-nav">
              <button className="btn-back-roster" onClick={() => setMobileView('roster')}>
                <ArrowLeft size={16} /> Back to Subject Roster
              </button>
              <span className="mobile-active-id">{activeSubjectData.id}</span>
            </div>

            {/* 1. OVERVIEW SECTION */}
            <div className="chart-overview-card">
              <div className="overview-header-row">
                <div>
                  <div className="overview-badge-row">
                    <span className="eyebrow-badge">SYNTHETIC CLINICAL SUBJECT</span>
                    <span className="privacy-pill">
                      <LockKeyhole size={11} /> Local SQLCipher Vault
                    </span>
                  </div>
                  <h2 className="overview-subject-title">{activeSubjectData.id}</h2>
                  <p className="overview-subtext">
                    Consolidated synthetic electronic health chart · Zero external telemetry egress
                  </p>
                </div>

                <div className="overview-actions">
                  <button
                    className="primary btn-sm"
                    onClick={() => onOpenAdd('VITAL_SIGN', activeSubjectData.id)}
                  >
                    <Plus size={15} /> Log vitals
                  </button>
                  <button
                    className="secondary btn-sm"
                    onClick={() => onOpenAdd('STANDARD', activeSubjectData.id)}
                  >
                    <Plus size={15} /> Add note
                  </button>
                  {selectedSubjectId && (
                    <button className="icon-button" title="Clear selection" onClick={handleClearSubject}>
                      <X size={16} />
                    </button>
                  )}
                </div>
              </div>

              {/* Subject Clinical Metrics Bar */}
              <div className="overview-metrics-bar">
                <div className="metric-item">
                  <span className="metric-label">Total Observations</span>
                  <b className="metric-value">{activeSubjectData.observations.length}</b>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Last Recorded Activity</span>
                  <b className="metric-value">{formatDate(activeSubjectData.lastActivity)}</b>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Allergies Documented</span>
                  <b className={`metric-value ${allergies.length > 0 ? 'text-alert' : 'text-good'}`}>
                    {allergies.length > 0 ? `${allergies.length} Alert` : 'None (NKDA)'}
                  </b>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Review State</span>
                  <b className={`metric-value ${conflictObservations.length > 0 ? 'text-warn' : 'text-good'}`}>
                    {conflictObservations.length > 0
                      ? `${conflictObservations.length} Divergent Branch`
                      : 'Consistent (No Conflicts)'}
                  </b>
                </div>
              </div>
            </div>

            {/* 6. REVIEW & CONFLICT ALERT (if applicable) */}
            {conflictObservations.length > 0 && (
              <div className="subject-conflict-banner" role="alert">
                <div className="conflict-banner-left">
                  <GitBranch size={18} className="conflict-icon" />
                  <div>
                    <b>Divergent Branch History Needs Review</b>
                    <p>
                      {conflictObservations.length} observation(s) for {activeSubjectData.id} contain conflicting
                      edits requiring administrator resolution.
                    </p>
                  </div>
                </div>
                <div className="conflict-banner-actions">
                  <button className="primary btn-sm" onClick={() => onInspect(conflictObservations[0])}>
                    Compare branches
                  </button>
                  <button className="secondary btn-sm" onClick={onGoToReview}>
                    Open Needs Review workspace
                  </button>
                </div>
              </div>
            )}

            {/* 3. ALLERGIES SECTION (Always prominent for clinical safety) */}
            <div className="chart-section allergies-section">
              <div className="chart-section-title-row">
                <div className="title-with-icon">
                  <AlertTriangle
                    size={18}
                    style={{ color: allergies.length > 0 ? 'var(--ctp-peach, #fe640b)' : 'var(--success)' }}
                  />
                  <h3>Allergies &amp; Adverse Reaction Alerts</h3>
                </div>
                <span className={`allergy-status-badge ${allergies.length > 0 ? 'alert' : 'clean'}`}>
                  {allergies.length > 0 ? `${allergies.length} Documented Alert` : 'NKDA Documented'}
                </span>
              </div>

              {allergies.length > 0 ? (
                <div className="allergy-cards-grid">
                  {allergies.map(allergy => (
                    <div
                      key={allergy.id}
                      className="allergy-alert-card"
                      onClick={() => onInspect(allergy.memory)}
                      role="button"
                      tabIndex={0}
                      title="Click to view full record and revision history in Inspector"
                      onKeyDown={e => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onInspect(allergy.memory);
                        }
                      }}
                    >
                      <div className="allergy-card-top">
                        <div className="allergen-title-box">
                          <span className="allergy-warning-sign">⚠️</span>
                          <strong className="allergen-name">{allergy.allergen}</strong>
                        </div>
                        <span className="allergy-severity-pill">{allergy.severity}</span>
                      </div>

                      <div className="allergy-detail-row">
                        <span className="detail-tag">Reaction:</span>
                        <span className="detail-val">{allergy.reaction}</span>
                      </div>

                      <div className="allergy-guidance-box">
                        <span className="guidance-tag">Clinical Guidance:</span>
                        <p className="guidance-text">{allergy.guidance}</p>
                      </div>

                      <div className="allergy-card-footer">
                        <span className="allergy-time">{formatShortDate(allergy.created)}</span>
                        <span className="inspect-link">
                          Inspect record <ChevronRight size={13} />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="allergy-clean-card">
                  <CheckCircle2 size={20} className="clean-icon" />
                  <div className="clean-text">
                    <b>No Known Drug Allergies (NKDA)</b>
                    <p>No adverse reaction or allergy observations exist in canonical storage for {activeSubjectData.id}.</p>
                  </div>
                </div>
              )}
            </div>

            {/* 2. VITALS SECTION (SVG Sparklines / Trends from real data) */}
            <div className="chart-section vitals-section">
              <div className="chart-section-title-row">
                <div className="title-with-icon">
                  <Activity size={18} style={{ color: 'var(--ctp-teal, #179299)' }} />
                  <h3>Longitudinal Vital Signs Trend</h3>
                </div>
                <div className="vitals-section-meta">
                  <span className="vitals-count-tag">{vitalReadings.length} measurement sessions</span>
                  <button
                    className="secondary btn-xs"
                    onClick={() => onOpenAdd('VITAL_SIGN', activeSubjectData.id)}
                  >
                    <Plus size={13} /> Add vitals
                  </button>
                </div>
              </div>

              <div className="vitals-grid">
                {/* Heart Rate */}
                <VitalTrendChart
                  title="Heart Rate"
                  unit="bpm"
                  points={vitalReadings}
                  getValue={r => r.heartRate}
                  color="var(--ctp-teal, #179299)"
                  normalRange={{ min: 60, max: 100 }}
                  criticalHigh={110}
                  criticalLow={50}
                />

                {/* Blood Pressure (Dual Curve) */}
                <BloodPressureChart readings={vitalReadings} />

                {/* Body Temperature */}
                <VitalTrendChart
                  title="Body Temperature"
                  unit="°C"
                  points={vitalReadings}
                  getValue={r => r.temperature}
                  color="var(--ctp-peach, #fe640b)"
                  normalRange={{ min: 36.5, max: 37.5 }}
                  criticalHigh={38.0}
                />

                {/* Oxygen Saturation SpO2 */}
                <VitalTrendChart
                  title="Oxygen Saturation (SpO₂)"
                  unit="%"
                  points={vitalReadings}
                  getValue={r => r.spO2}
                  color="var(--ctp-blue, #1e66f5)"
                  normalRange={{ min: 95, max: 100 }}
                  criticalLow={94}
                />
              </div>
            </div>

            {/* 4. MEDICATIONS SECTION */}
            <div className="chart-section medications-section">
              <div className="chart-section-title-row">
                <div className="title-with-icon">
                  <Pill size={18} style={{ color: 'var(--ctp-mauve, #8839ef)' }} />
                  <h3>Active Medication Observations</h3>
                </div>
                <span className="meds-count-tag">{medications.length} active entries</span>
              </div>

              {medications.length > 0 ? (
                <div className="medications-grid">
                  {medications.map(med => (
                    <div
                      key={med.id}
                      className="medication-card"
                      onClick={() => onInspect(med.memory)}
                      role="button"
                      tabIndex={0}
                      title="Click to view full medication record in Inspector"
                      onKeyDown={e => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onInspect(med.memory);
                        }
                      }}
                    >
                      <div className="med-card-top">
                        <div className="med-icon-box">
                          <Pill size={16} />
                        </div>
                        <div className="med-name-col">
                          <b className="med-drug-name">{med.drugName}</b>
                          <span className="med-dose-pill">
                            {med.dosage} · {med.route}
                          </span>
                        </div>
                      </div>

                      <div className="med-details-row">
                        <span className="med-detail-tag">Schedule:</span>
                        <span className="med-detail-val">{med.frequency}</span>
                      </div>

                      <div className="med-details-row">
                        <span className="med-detail-tag">Indication:</span>
                        <span className="med-detail-val">{med.indication}</span>
                      </div>

                      <div className="med-card-footer">
                        <span className="med-time">Recorded: {formatShortDate(med.created)}</span>
                        <span className="inspect-link">
                          Inspect <ChevronRight size={13} />
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="medications-empty-card">
                  <Pill size={20} className="empty-med-icon" />
                  <div>
                    <b>No active synthetic medications documented</b>
                    <p>No medication observations exist in local storage for {activeSubjectData.id}.</p>
                  </div>
                  <button
                    className="secondary btn-xs"
                    onClick={() => onOpenAdd('MEDICATION', activeSubjectData.id)}
                  >
                    <Plus size={13} /> Prescribe / Log Medication
                  </button>
                </div>
              )}
            </div>

            {/* 5. CHRONOLOGICAL TIMELINE SECTION */}
            <div className="chart-section timeline-section">
              <div className="chart-section-title-row">
                <div className="title-with-icon">
                  <Clock size={18} style={{ color: 'var(--accent)' }} />
                  <h3>Chronological Observation History</h3>
                </div>
                <span className="timeline-count-tag">{filteredTimeline.length} of {subjectObservations.length} logs</span>
              </div>

              {/* Timeline Toolbar & Category Filters */}
              <div className="timeline-toolbar-box">
                <div className="timeline-search-field">
                  <Search size={15} />
                  <input
                    placeholder={`Filter ${activeSubjectData.id} records by keyword…`}
                    value={timelineSearch}
                    onChange={e => setTimelineSearch(e.target.value)}
                    aria-label="Filter subject observation timeline"
                  />
                  {timelineSearch && (
                    <button className="icon-clear" onClick={() => setTimelineSearch('')}>
                      <X size={13} />
                    </button>
                  )}
                </div>

                <div className="timeline-pills-row">
                  <button
                    className={`timeline-pill ${timelineCategory === null ? 'active' : ''}`}
                    onClick={() => setTimelineCategory(null)}
                  >
                    All ({subjectObservations.length})
                  </button>
                  {Object.entries(CATEGORY_MAP).map(([cat, info]) => {
                    const count = activeSubjectData.categoryCounts[cat] || 0;
                    if (count === 0) return null;
                    return (
                      <button
                        key={cat}
                        className={`timeline-pill ${timelineCategory === cat ? 'active' : ''}`}
                        onClick={() => setTimelineCategory(timelineCategory === cat ? null : cat)}
                      >
                        <span className="pill-dot" style={{ backgroundColor: info.color }} />
                        {info.label} ({count})
                      </button>
                    );
                  })}
                  {activeSubjectData.hasConflicts && (
                    <button
                      className={`timeline-pill warn ${onlyConflicts ? 'active' : ''}`}
                      onClick={() => setOnlyConflicts(!onlyConflicts)}
                    >
                      <GitBranch size={12} /> Needs Review Only
                    </button>
                  )}
                </div>
              </div>

              {/* Chronological List of Cards */}
              <div className="subject-timeline-stream">
                {filteredTimeline.map(m => {
                  const catInfo = CATEGORY_MAP[m.category] || CATEGORY_MAP.OBSERVATION;
                  const Icon = catInfo.icon;

                  return (
                    <div
                      key={m.id}
                      className={`timeline-item-card ${m.conflicting ? 'conflicted' : ''}`}
                      onClick={() => onInspect(m)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={e => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          onInspect(m);
                        }
                      }}
                    >
                      <div
                        className="timeline-item-icon-box"
                        style={{
                          backgroundColor: `color-mix(in srgb, ${catInfo.color} 12%, transparent)`,
                          color: catInfo.color,
                        }}
                      >
                        <Icon size={16} />
                      </div>

                      <div className="timeline-item-body">
                        <div className="timeline-item-header">
                          <div className="item-header-meta">
                            <span
                              className="cat-badge"
                              style={{ color: catInfo.color, borderColor: `color-mix(in srgb, ${catInfo.color} 30%, transparent)` }}
                            >
                              {catInfo.label}
                            </span>
                            <span className="privacy-badge">
                              {m.privacy === 'HIGHLY_SENSITIVE' ? 'Personal Note' : 'Workspace Record'}
                            </span>
                            {m.conflicting && (
                              <span className="conflict-badge">
                                <GitBranch size={11} /> Needs review
                              </span>
                            )}
                          </div>
                          <time className="item-timestamp">{formatDate(m.created)}</time>
                        </div>

                        <h4 className="item-title">{m.title}</h4>
                        {m.content && <p className="item-excerpt">{m.content}</p>}

                        <div className="item-footer">
                          <span className="inspect-prompt">
                            Inspect record &amp; revisions <ChevronRight size={13} />
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {filteredTimeline.length === 0 && (
                  <div className="timeline-empty-box">
                    <FileText size={24} />
                    <h4>No observations match the selected filters</h4>
                    <p>Try clearing your category filter or keyword search.</p>
                    <button
                      className="secondary btn-sm"
                      onClick={() => {
                        setTimelineCategory(null);
                        setTimelineSearch('');
                        setOnlyConflicts(false);
                      }}
                    >
                      Reset filters
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          /* Empty state when no synthetic subjects exist yet in memories */
          <div className="chart-empty-workspace">
            <Users size={36} className="empty-icon" />
            <h2>No Synthetic Subjects Recorded Yet</h2>
            <p>
              Observations captured with subject IDs like <code>SYN-001</code>, <code>SYN-002</code> automatically
              populate this clinical workspace.
            </p>
            <div className="empty-actions">
              <button className="primary" onClick={() => onOpenAdd('STANDARD', 'SYN-001')}>
                <Plus size={16} /> Create first subject observation
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
