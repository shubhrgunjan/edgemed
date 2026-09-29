import React, { useState, type FormEvent } from 'react';
import {
  AlertTriangle,
  ClipboardList,
  HeartPulse,
  Pill,
  Sparkles,
  Stethoscope,
  ShieldCheck,
  LockKeyhole,
} from 'lucide-react';

export type StructuredMemoryPayload = {
  title: string;
  content: string;
  subject: string;
  category: 'OBSERVATION' | 'ALLERGY' | 'MEDICATION' | 'VITAL_SIGN' | 'NOTE';
  privacy: 'SENSITIVE' | 'HIGHLY_SENSITIVE';
  importance: number;
};

export type EntryType = 'STANDARD' | 'VITAL_SIGN' | 'OBSERVATION' | 'MEDICATION' | 'ALLERGY' | 'NOTE';

export const QUICK_ENTRY_TYPES: Array<{
  type: EntryType;
  title: string;
  description: string;
  category: 'OBSERVATION' | 'ALLERGY' | 'MEDICATION' | 'VITAL_SIGN' | 'NOTE';
  badge: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  accentColor: string;
}> = [
  {
    type: 'VITAL_SIGN',
    title: 'Log Vitals',
    description: 'BP, Heart Rate, SpO2, Temperature, Resp Rate',
    category: 'VITAL_SIGN',
    badge: 'Vitals',
    icon: HeartPulse,
    accentColor: 'var(--ctp-teal, #179299)',
  },
  {
    type: 'OBSERVATION',
    title: 'Observation',
    description: 'Symptoms, physical exam findings, acute changes',
    category: 'OBSERVATION',
    badge: 'Finding',
    icon: Stethoscope,
    accentColor: 'var(--ctp-blue, #1e66f5)',
  },
  {
    type: 'MEDICATION',
    title: 'Medication',
    description: 'Dose, route, frequency, indication, schedule',
    category: 'MEDICATION',
    badge: 'Medication',
    icon: Pill,
    accentColor: 'var(--ctp-mauve, #8839ef)',
  },
  {
    type: 'ALLERGY',
    title: 'Allergy / Alert',
    description: 'Allergen, reaction severity, verification status',
    category: 'ALLERGY',
    badge: 'Alert',
    icon: AlertTriangle,
    accentColor: 'var(--ctp-peach, #fe640b)',
  },
  {
    type: 'NOTE',
    title: 'SBAR Note',
    description: 'Situation, Background, Assessment, Recommendation',
    category: 'NOTE',
    badge: 'Handoff',
    icon: ClipboardList,
    accentColor: 'var(--ctp-yellow, #df8e1d)',
  },
];

/**
 * Quick-Entry Cards Section shown in the workspace
 */
export function QuickEntryCards({
  onSelectType,
}: {
  onSelectType: (type: EntryType) => void;
}) {
  return (
    <div className="quick-entry-section">
      <div className="section-title-row">
        <div>
          <h3>Quick-entry logging</h3>
          <p className="section-sub">Standardized synthetic observation templates for clinical workflows</p>
        </div>
      </div>

      <div className="quick-entry-grid">
        {QUICK_ENTRY_TYPES.map(card => {
          const Icon = card.icon;
          return (
            <button
              key={card.type}
              type="button"
              className="quick-card"
              onClick={() => onSelectType(card.type)}
            >
              <div className="quick-card-top">
                <span className="quick-card-icon" style={{ color: card.accentColor, backgroundColor: `color-mix(in srgb, ${card.accentColor} 12%, transparent)` }}>
                  <Icon size={20} />
                </span>
                <span className="quick-badge" style={{ color: card.accentColor, borderColor: `color-mix(in srgb, ${card.accentColor} 30%, transparent)` }}>
                  {card.badge}
                </span>
              </div>
              <b className="quick-card-title">{card.title}</b>
              <p className="quick-card-desc">{card.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Structured Observation Form Modal Body
 */
export function StructuredObservationForm({
  initialType = 'STANDARD',
  initialSubject,
  busy,
  onSave,
  onCancel,
}: {
  initialType?: EntryType;
  initialSubject?: string;
  busy: boolean;
  onSave: (payload: StructuredMemoryPayload) => Promise<void>;
  onCancel: () => void;
}) {
  const [entryType, setEntryType] = useState<EntryType>(initialType);
  const [subject, setSubject] = useState(initialSubject || 'SYN-001');
  const [privacy, setPrivacy] = useState<'SENSITIVE' | 'HIGHLY_SENSITIVE'>('SENSITIVE');
  const [importance, setImportance] = useState(0.5);

  // Standard fields (kept for backward-compatibility with tests)
  const [standardTitle, setStandardTitle] = useState('');
  const [standardContent, setStandardContent] = useState('');
  const [standardCategory, setStandardCategory] = useState<'OBSERVATION' | 'ALLERGY' | 'MEDICATION' | 'VITAL_SIGN' | 'NOTE'>('OBSERVATION');

  // Vitals fields
  const [systolic, setSystolic] = useState('120');
  const [diastolic, setDiastolic] = useState('80');
  const [heartRate, setHeartRate] = useState('72');
  const [respRate, setRespRate] = useState('16');
  const [temperature, setTemperature] = useState('37.0');
  const [spO2, setSpO2] = useState('98');
  const [vitalsRemark, setVitalsRemark] = useState('Patient resting comfortably, hemodynamically stable.');

  // Clinical Observation fields
  const [finding, setFinding] = useState('Bilateral basilar crackles on auscultation');
  const [system, setSystem] = useState('Respiratory');
  const [severity, setSeverity] = useState('Moderate');
  const [onset, setOnset] = useState('Onset 4 hours ago');
  const [observationPlan, setObservationPlan] = useState('Patient reports mild dyspnea on exertion. Continue oxygen and monitor hourly.');

  // Medication fields
  const [drugName, setDrugName] = useState('Amoxicillin');
  const [dosage, setDosage] = useState('500 mg');
  const [route, setRoute] = useState('Oral');
  const [frequency, setFrequency] = useState('TID (Three times daily)');
  const [indication, setIndication] = useState('Lower respiratory tract infection prophylaxis');

  // Allergy fields
  const [allergen, setAllergen] = useState('Penicillin');
  const [reaction, setReaction] = useState('Maculopapular rash, pruritus');
  const [allergySeverity, setAllergySeverity] = useState('Moderate');
  const [verification, setVerification] = useState('Confirmed');
  const [contraindication, setContraindication] = useState('Avoid all beta-lactam class antibiotics.');

  // SBAR Note fields
  const [situation, setSituation] = useState('Transfer from Emergency to Inpatient Ward');
  const [background, setBackground] = useState('48h post-admission with community acquired pneumonia, vitals improving.');
  const [assessment, setAssessment] = useState('Afebrile for 12 hours, oxygen saturation 98% on room air.');
  const [recommendation, setRecommendation] = useState('Repeat vitals in 4 hours, encourage ambulation, oral stepdown medication.');

  const [validationError, setValidationError] = useState('');

  // Generate title and content based on entryType
  function buildPayload(): StructuredMemoryPayload {
    if (entryType === 'STANDARD') {
      return {
        title: standardTitle.trim(),
        content: standardContent.trim(),
        subject: subject.trim(),
        category: standardCategory,
        privacy,
        importance,
      };
    }

    if (entryType === 'VITAL_SIGN') {
      const title = `Vitals: BP ${systolic}/${diastolic}, HR ${heartRate} bpm, SpO2 ${spO2}%, Temp ${temperature}°C`;
      const content = `[SYNTHETIC VITAL SIGNS RECORD]
Subject: ${subject}
Blood Pressure: ${systolic}/${diastolic} mmHg
Heart Rate: ${heartRate} bpm
Respiratory Rate: ${respRate} /min
Body Temperature: ${temperature} °C
Oxygen Saturation (SpO2): ${spO2}%
Clinical Context: ${vitalsRemark}
Integrity: Synthetic observation captured on local edge server.`;
      return { title, content, subject, category: 'VITAL_SIGN', privacy, importance };
    }

    if (entryType === 'OBSERVATION') {
      const title = `Observation: ${finding} (${system})`;
      const content = `[SYNTHETIC CLINICAL OBSERVATION]
Subject: ${subject}
Organ System: ${system}
Primary Finding: ${finding}
Acuity / Severity: ${severity}
Timeline: ${onset}
Clinical Assessment: ${observationPlan}
Storage: Pinned local vector embeddings generated on device.`;
      return { title, content, subject, category: 'OBSERVATION', privacy, importance };
    }

    if (entryType === 'MEDICATION') {
      const title = `Medication: ${drugName} ${dosage} ${route} ${frequency}`;
      const content = `[SYNTHETIC MEDICATION ADMINISTRATION]
Subject: ${subject}
Medication Name: ${drugName}
Dosage & Unit: ${dosage}
Route: ${route}
Frequency / Schedule: ${frequency}
Indication: ${indication}
Formulary Check: Verified against synthetic local reference list.`;
      return { title, content, subject, category: 'MEDICATION', privacy, importance };
    }

    if (entryType === 'ALLERGY') {
      const title = `Allergy Alert: ${allergen} - ${reaction} (${allergySeverity})`;
      const content = `[SYNTHETIC ALLERGY & ADVERSE REACTION]
Subject: ${subject}
Allergen: ${allergen}
Adverse Reaction: ${reaction}
Severity: ${allergySeverity}
Status: ${verification}
Clinical Guidance: ${contraindication}
Safety Boundary: Critical local alert; flagged for all future orders.`;
      return { title, content, subject, category: 'ALLERGY', privacy, importance: Math.max(importance, 0.8) };
    }

    // SBAR Note
    const title = `SBAR Note: ${subject} - ${situation}`;
    const content = `[SYNTHETIC SBAR CLINICAL NOTE]
Subject: ${subject}
Situation: ${situation}
Background: ${background}
Assessment: ${assessment}
Recommendation: ${recommendation}
Governance: Workspace-scoped clinical note. Retained in canonical vault.`;
    return { title, content, subject, category: 'NOTE', privacy, importance };
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setValidationError('');

    const payload = buildPayload();
    if (!payload.title || payload.title.length > 160) {
      setValidationError('Title must be between 1 and 160 characters.');
      return;
    }
    if (!payload.content || payload.content.length > 12000) {
      setValidationError('Observation content must be between 1 and 12,000 characters.');
      return;
    }
    if (!/^SYN-[0-9]{3,6}$/.test(payload.subject)) {
      setValidationError('Subject must match the synthetic format SYN-xxx (e.g. SYN-001).');
      return;
    }

    await onSave(payload);
  }

  const preview = buildPayload();

  return (
    <form className="structured-form" onSubmit={handleSubmit}>
      {/* Type Switcher Tabs */}
      <div className="template-tabs" role="tablist" aria-label="Observation template">
        <button
          type="button"
          role="tab"
          aria-selected={entryType === 'STANDARD'}
          className={`tab-btn ${entryType === 'STANDARD' ? 'active' : ''}`}
          onClick={() => setEntryType('STANDARD')}
        >
          Freeform note
        </button>
        {QUICK_ENTRY_TYPES.map(q => (
          <button
            key={q.type}
            type="button"
            role="tab"
            aria-selected={entryType === q.type}
            className={`tab-btn ${entryType === q.type ? 'active' : ''}`}
            onClick={() => setEntryType(q.type)}
          >
            {q.badge}
          </button>
        ))}
      </div>

      <p className="form-scope-note">
        {privacy === 'HIGHLY_SENSITIVE' ? (
          <span>
            <LockKeyhole size={14} style={{ verticalAlign: -2 }} /> Personal note — visible only to you on this device.
          </span>
        ) : (
          <span>
            <ShieldCheck size={14} style={{ verticalAlign: -2 }} /> Workspace note — shared with colleagues in your ward.
          </span>
        )}
      </p>

      {/* Common Subject and Privacy row */}
      <div className="form-row">
        <label>
          Synthetic subject
          <input
            name="subject"
            value={subject}
            onChange={e => setSubject(e.target.value)}
            pattern="SYN-[0-9]{3,6}"
            placeholder="SYN-001"
            required
          />
        </label>
        <label>
          Privacy scope
          <select
            name="privacy"
            value={privacy}
            onChange={e => setPrivacy(e.target.value as 'SENSITIVE' | 'HIGHLY_SENSITIVE')}
          >
            <option value="SENSITIVE">Shared with workspace</option>
            <option value="HIGHLY_SENSITIVE">Personal · only me</option>
          </select>
        </label>
      </div>

      {/* Conditional Template Form Body */}
      {entryType === 'STANDARD' && (
        <>
          <label>
            Title
            <input
              name="title"
              value={standardTitle}
              onChange={e => setStandardTitle(e.target.value)}
              placeholder="Summary of synthetic observation"
              maxLength={160}
              required
            />
          </label>
          <label>
            Observation
            <textarea
              name="content"
              value={standardContent}
              onChange={e => setStandardContent(e.target.value)}
              placeholder="Clinical observation, symptoms, or findings..."
              rows={5}
              maxLength={12000}
              required
            />
          </label>
          <div className="form-row">
            <label>
              Category
              <select
                name="category"
                value={standardCategory}
                onChange={e => setStandardCategory(e.target.value as any)}
              >
                <option value="OBSERVATION">OBSERVATION</option>
                <option value="ALLERGY">ALLERGY</option>
                <option value="MEDICATION">MEDICATION</option>
                <option value="VITAL_SIGN">VITAL_SIGN</option>
                <option value="NOTE">NOTE</option>
              </select>
            </label>
            <label>
              Importance (0.0 – 1.0)
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={importance}
                onChange={e => setImportance(parseFloat(e.target.value) || 0.5)}
              />
            </label>
          </div>
        </>
      )}

      {entryType === 'VITAL_SIGN' && (
        <div className="template-fields">
          <div className="form-row-3">
            <label>
              Systolic BP (mmHg)
              <input type="number" value={systolic} onChange={e => setSystolic(e.target.value)} required min="50" max="260" />
            </label>
            <label>
              Diastolic BP (mmHg)
              <input type="number" value={diastolic} onChange={e => setDiastolic(e.target.value)} required min="30" max="160" />
            </label>
            <label>
              Heart Rate (bpm)
              <input type="number" value={heartRate} onChange={e => setHeartRate(e.target.value)} required min="30" max="240" />
            </label>
          </div>

          <div className="form-row-3">
            <label>
              Body Temp (°C)
              <input type="number" step="0.1" value={temperature} onChange={e => setTemperature(e.target.value)} required min="32" max="44" />
            </label>
            <label>
              SpO2 (%)
              <input type="number" value={spO2} onChange={e => setSpO2(e.target.value)} required min="50" max="100" />
            </label>
            <label>
              Resp Rate (/min)
              <input type="number" value={respRate} onChange={e => setRespRate(e.target.value)} required min="6" max="60" />
            </label>
          </div>

          <label>
            Clinical Context / Remarks
            <input
              value={vitalsRemark}
              onChange={e => setVitalsRemark(e.target.value)}
              placeholder="e.g. Resting vitals, post-treatment, asymptomatic"
            />
          </label>
        </div>
      )}

      {entryType === 'OBSERVATION' && (
        <div className="template-fields">
          <div className="form-row">
            <label>
              Organ System
              <select value={system} onChange={e => setSystem(e.target.value)}>
                <option value="Respiratory">Respiratory</option>
                <option value="Cardiovascular">Cardiovascular</option>
                <option value="Gastrointestinal">Gastrointestinal</option>
                <option value="Neurological">Neurological</option>
                <option value="Musculoskeletal">Musculoskeletal</option>
                <option value="Dermatological">Dermatological</option>
                <option value="General">General / Constitutional</option>
              </select>
            </label>
            <label>
              Severity
              <select value={severity} onChange={e => setSeverity(e.target.value)}>
                <option value="Mild">Mild</option>
                <option value="Moderate">Moderate</option>
                <option value="Severe">Severe / Acute</option>
              </select>
            </label>
          </div>

          <label>
            Primary Symptom / Finding
            <input
              value={finding}
              onChange={e => setFinding(e.target.value)}
              placeholder="e.g. Persistent cough, dull abdominal pain"
              required
            />
          </label>

          <div className="form-row">
            <label>
              Onset & Timeline
              <input value={onset} onChange={e => setOnset(e.target.value)} placeholder="e.g. Past 2 days" />
            </label>
          </div>

          <label>
            Detailed Clinical Assessment
            <textarea
              value={observationPlan}
              onChange={e => setObservationPlan(e.target.value)}
              rows={3}
              placeholder="Clinical examination findings and notes..."
              required
            />
          </label>
        </div>
      )}

      {entryType === 'MEDICATION' && (
        <div className="template-fields">
          <div className="form-row">
            <label>
              Medication Name
              <input value={drugName} onChange={e => setDrugName(e.target.value)} placeholder="e.g. Amoxicillin, Paracetamol" required />
            </label>
            <label>
              Dosage & Unit
              <input value={dosage} onChange={e => setDosage(e.target.value)} placeholder="e.g. 500 mg, 1 g" required />
            </label>
          </div>

          <div className="form-row">
            <label>
              Route
              <select value={route} onChange={e => setRoute(e.target.value)}>
                <option value="Oral">Oral (PO)</option>
                <option value="Intravenous">Intravenous (IV)</option>
                <option value="Subcutaneous">Subcutaneous (SC)</option>
                <option value="Inhalation">Inhalation</option>
                <option value="Topical">Topical</option>
              </select>
            </label>
            <label>
              Frequency
              <select value={frequency} onChange={e => setFrequency(e.target.value)}>
                <option value="Once">Once</option>
                <option value="BID (Twice daily)">BID (Twice daily)</option>
                <option value="TID (Three times daily)">TID (Three times daily)</option>
                <option value="QID (Four times daily)">QID (Four times daily)</option>
                <option value="PRN (As needed)">PRN (As needed)</option>
              </select>
            </label>
          </div>

          <label>
            Indication / Reason
            <input value={indication} onChange={e => setIndication(e.target.value)} placeholder="e.g. Pain relief, antibiotic therapy" required />
          </label>
        </div>
      )}

      {entryType === 'ALLERGY' && (
        <div className="template-fields">
          <div className="form-row">
            <label>
              Allergen / Substance
              <input value={allergen} onChange={e => setAllergen(e.target.value)} placeholder="e.g. Penicillin, NSAIDs, Latex" required />
            </label>
            <label>
              Severity
              <select value={allergySeverity} onChange={e => setAllergySeverity(e.target.value)}>
                <option value="Mild">Mild (local rash/itching)</option>
                <option value="Moderate">Moderate (urticaria/swelling)</option>
                <option value="Severe">Severe (anaphylaxis/airway)</option>
              </select>
            </label>
          </div>

          <div className="form-row">
            <label>
              Reaction Manifestation
              <input value={reaction} onChange={e => setReaction(e.target.value)} placeholder="e.g. Urticaria, swelling, wheezing" required />
            </label>
            <label>
              Verification Status
              <select value={verification} onChange={e => setVerification(e.target.value)}>
                <option value="Confirmed">Confirmed</option>
                <option value="Suspected">Suspected</option>
                <option value="Historical">Historical Report</option>
              </select>
            </label>
          </div>

          <label>
            Clinical Guidance / Contraindication
            <input value={contraindication} onChange={e => setContraindication(e.target.value)} placeholder="e.g. Avoid all beta-lactam class antibiotics" />
          </label>
        </div>
      )}

      {entryType === 'NOTE' && (
        <div className="template-fields">
          <label>
            Situation (S)
            <input value={situation} onChange={e => setSituation(e.target.value)} placeholder="Immediate clinical situation or transfer reason" required />
          </label>
          <label>
            Background (B)
            <textarea value={background} onChange={e => setBackground(e.target.value)} rows={2} placeholder="Admission details, baseline clinical state..." required />
          </label>
          <label>
            Assessment (A)
            <textarea value={assessment} onChange={e => setAssessment(e.target.value)} rows={2} placeholder="Current vitals, examination, clinical status..." required />
          </label>
          <label>
            Recommendation (R)
            <input value={recommendation} onChange={e => setRecommendation(e.target.value)} placeholder="Next steps, monitoring frequency, medications" required />
          </label>
        </div>
      )}

      {/* Live Preview Box for structured templates */}
      {entryType !== 'STANDARD' && (
        <div className="preview-box">
          <span className="preview-label">
            <Sparkles size={13} style={{ verticalAlign: -2 }} /> Live Structured Preview
          </span>
          <b className="preview-title">{preview.title}</b>
          <pre className="preview-content">{preview.content}</pre>
        </div>
      )}

      {validationError && (
        <p role="alert" className="error">
          {validationError}
        </p>
      )}

      <div className="form-actions">
        <button type="button" className="secondary" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button type="submit" className="primary" disabled={busy}>
          {busy ? 'Saving...' : 'Save locally'}
        </button>
      </div>
    </form>
  );
}
