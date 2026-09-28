import { useMemo, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, ArrowRight, Check, FileText, LockKeyhole, Plus, Search, ShieldCheck, Trash2, X } from 'lucide-react';
import { ThemeToggle } from './theme';
import art from '../../assets/edgemed-memory-art.png';
import './demo.css';

type Note = { id: string; title: string; content: string; category: string; created: number };
const initial: Note[] = [
  { id: '1', title: 'Persistent cough and fever', content: 'Synthetic subject SYN-001 reports a persistent cough and raised temperature for three days.', category: 'Observation', created: 1 },
  { id: '2', title: 'Penicillin allergy reported', content: 'Synthetic subject SYN-002 reports a rash after penicillin exposure.', category: 'Allergy', created: 2 },
  { id: '3', title: 'Blood pressure reading', content: 'Synthetic subject SYN-003 has a recorded blood pressure reading for follow-up.', category: 'Vital sign', created: 3 },
  { id: '4', title: 'Hydration follow-up', content: 'Synthetic subject SYN-004 describes dizziness after low fluid intake.', category: 'Observation', created: 4 },
];
const words = (value: string) => value.toLowerCase().match(/[a-z0-9]+/g) ?? [];

function Demo() {
  const [notes, setNotes] = useState<Note[]>(initial), [query, setQuery] = useState('');
  const [activeQuery, setActiveQuery] = useState(''), [selected, setSelected] = useState<Note | null>(null);
  const [adding, setAdding] = useState(false), [notice, setNotice] = useState('');
  const matches = useMemo(() => {
    if (!activeQuery) return [...notes].sort((a, b) => b.created - a.created);
    const terms = words(activeQuery);
    return notes.map(note => {
      const title = words(note.title), content = words(note.content);
      return { note, score: terms.reduce((score, term) => score + title.filter(t => t === term).length * 3 + content.filter(t => t === term).length, 0) };
    }).filter(entry => entry.score > 0).sort((a, b) => b.score - a.score || b.note.created - a.note.created).map(entry => entry.note);
  }, [notes, activeQuery]);
  function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const data = new FormData(e.currentTarget);
    const title = String(data.get('title') ?? '').trim(), content = String(data.get('content') ?? '').trim();
    if (!title || !content) return;
    setNotes(previous => [{ id: crypto.randomUUID(), title, content, category: String(data.get('category') ?? 'Observation'), created: Date.now() }, ...previous]);
    setAdding(false); setActiveQuery(''); setQuery(''); setNotice('Synthetic note saved in this browser tab. It will disappear on refresh.');
  }
  function remove(id: string) { setNotes(previous => previous.filter(note => note.id !== id)); setSelected(null); setNotice('Note removed from this browser tab.'); }
  return <div className="demo-shell">
    <header className="demo-header"><div className="demo-brand"><ShieldCheck aria-hidden="true" />EdgeMed<span>.</span></div><nav aria-label="Demo navigation"><a href="#explore">Explore</a><a href="#how-it-works">How it works</a></nav><ThemeToggle /></header>
    <main>
      <section className="demo-hero"><div><p className="demo-eyebrow">PUBLIC SYNTHETIC DEMO</p><h1>Memory that stays close to care.</h1><p>Explore a safe browser sample of capture and search. Every example is synthetic. Notes you add stay in this tab and disappear when you refresh.</p><a className="demo-primary" href="#explore">Try the demo <ArrowRight size={17} /></a></div><img src={art} alt="Illustration of connected memory cards inside a protected circle" /></section>
      <section className="demo-banner" role="status"><LockKeyhole size={18} /><span>Browser sample: no login, no server storage, no patient data. Search here uses exact words; the installable app runs local semantic search.</span></section>
      <section id="explore" className="demo-workspace"><div className="demo-section-heading"><div><p className="demo-eyebrow">EXPLORE THE WORKSPACE</p><h2>Find what matters in the sample.</h2><p>{notes.length} synthetic notes in this tab</p></div><button className="demo-primary" onClick={() => setAdding(true)}><Plus size={17} /> Add note</button></div>
        {notice && <div className="demo-notice" role="status"><Check size={17} />{notice}<button aria-label="Dismiss notice" onClick={() => setNotice('')}><X size={15} /></button></div>}
        <form className="demo-search" onSubmit={e => { e.preventDefault(); setActiveQuery(query.trim()); }}><Search size={20} /><input aria-label="Search synthetic notes" placeholder="Try penicillin, cough, pressure…" value={query} onChange={e => setQuery(e.target.value)} /><button type="submit">Search</button></form>
        {activeQuery && <div className="demo-result-caption"><span>{matches.length} keyword matches for “{activeQuery}”</span><button onClick={() => { setActiveQuery(''); setQuery(''); }}>Clear search</button></div>}
        <div className="demo-grid">{matches.map(note => <button className="demo-card" key={note.id} onClick={() => setSelected(note)}><span className="demo-card-icon"><FileText size={20} /></span><span className="demo-card-body"><strong>{note.title}</strong><span>{note.category}</span><small>{note.content}</small></span><ArrowRight size={16} /></button>)}{matches.length === 0 && <div className="demo-empty">No matching synthetic notes. Try another exact word or add an example.</div>}</div>
      </section>
      <section id="how-it-works" className="demo-info"><div><Activity size={21} /><h2>What the full app adds</h2><p>The installable Mac app adds an encrypted vault, on-device semantic retrieval, staff workspaces, and optional reviewed-reference synchronization. Those features require a local server and are outside this public browser sample.</p></div><div><ShieldCheck size={21} /><h2>Designed for careful demos</h2><p>Use invented examples only. This page makes no API requests and keeps new notes in memory until the tab is closed or refreshed. Never enter patient information.</p></div></section>
    </main><footer>EdgeMed · Synthetic research prototype · No clinical use</footer>
    {adding && <div className="demo-overlay" onMouseDown={e => { if (e.target === e.currentTarget) setAdding(false); }}><div className="demo-dialog" role="dialog" aria-modal="true" aria-label="Add synthetic note"><div className="demo-dialog-head"><h2>Add a synthetic note</h2><button aria-label="Close add note" onClick={() => setAdding(false)}><X /></button></div><p>Use invented details only. This note stays in your browser tab.</p><form onSubmit={add}><label>Title<input name="title" required maxLength={160} /></label><label>Category<select name="category"><option>Observation</option><option>Allergy</option><option>Vital sign</option><option>Medication</option></select></label><label>Note<textarea name="content" required rows={5} maxLength={3000} /></label><button className="demo-primary" type="submit">Save in this tab</button></form></div></div>}
    {selected && <div className="demo-overlay" onMouseDown={e => { if (e.target === e.currentTarget) setSelected(null); }}><div className="demo-dialog" role="dialog" aria-modal="true" aria-label="Synthetic note detail"><div className="demo-dialog-head"><h2>{selected.title}</h2><button aria-label="Close detail" onClick={() => setSelected(null)}><X /></button></div><p className="demo-eyebrow">{selected.category.toUpperCase()} · SYNTHETIC</p><div className="demo-note-content">{selected.content}</div><button className="demo-danger" onClick={() => remove(selected.id)}><Trash2 size={16} /> Remove from this tab</button></div></div>}
  </div>;
}
createRoot(document.getElementById('root')!).render(<Demo />);
