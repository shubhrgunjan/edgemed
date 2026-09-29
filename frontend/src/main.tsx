import { useEffect, useRef, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, Check, ChevronRight, FileText, GitBranch, HardDrive, LockKeyhole, LogOut, Menu, Plus, RefreshCw, Search, ShieldCheck, Wifi, WifiOff, X } from 'lucide-react';
import './style.css';
import { ThemeToggle } from './theme';
import { Brand, Dialog } from './ui';
import { VisualLoggingWorkspace } from './logging';
import { StructuredObservationForm, type EntryType, type StructuredMemoryPayload } from './quick-entry';
import type { Memory, Status, Sync } from './charts';

type Event = { action: string; time: number; device: string };
let csrf = '', epoch = 0;
const requests = new Set<AbortController>();
function invalidate() { epoch++; csrf = ''; requests.forEach(c => c.abort()); requests.clear(); }
async function api(path: string, method = 'GET', data?: unknown) {
  const generation = epoch, controller = new AbortController(); requests.add(controller);
  try {
    const res = await fetch('/api' + path, { method, credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: data === undefined ? undefined : JSON.stringify(data) });
    const body = await res.json();
    if (generation !== epoch) throw new DOMException('Previous session', 'AbortError');
    if (!res.ok) {
      if (res.status === 401 && path !== '/login') window.dispatchEvent(new CustomEvent('session-expired'));
      throw new Error(typeof body.detail === 'string' ? body.detail : 'Check the submitted fields.');
    }
    return body;
  } finally { requests.delete(controller); }
}
const date = (t?: number) => t ? new Date(t * 1000).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Not yet';
const connectionLabels: Record<string, string> = { connected: 'Shared service connected', unavailable: 'Shared service unavailable', paused: 'Sharing paused', unknown: 'Checking shared service', stale: 'Shared status out of date', attention: 'Sharing needs attention', verification_error: 'Sharing verification failed' };

function App() {
  const [user, setUser] = useState(''), [role, setRole] = useState(''), [checking, setChecking] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null), closeMenuButton = useRef<HTMLButtonElement>(null);
  const [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false);
  const [view, setView] = useState('Memory'), [query, setQuery] = useState(''), [offset, setOffset] = useState(0);
  const [memories, setMemories] = useState<Memory[]>([]), [results, setResults] = useState<Memory[] | null>(null);
  const [status, setStatus] = useState<Status | null>(null), [sync, setSync] = useState<Sync | null>(null), [ready, setReady] = useState(false);
  const [events, setEvents] = useState<Event[]>([]), [selected, setSelected] = useState<Memory | null>(null);
  const [addingType, setAddingType] = useState<EntryType | null>(null), [chosen, setChosen] = useState(''), [matched, setMatched] = useState('');
  const [timing, setTiming] = useState<{ backend: number; roundtrip: number } | null>(null);
  const selectedId = useRef<string | null>(null), searchOrder = useRef(0), generation = useRef(-1);

  function clear() {
    invalidate(); searchOrder.current++; selectedId.current = null; generation.current = -1;
    setUser(''); setRole(''); setMemories([]); setResults(null); setSelected(null); setStatus(null); setSync(null); setEvents([]);
    setQuery(''); setAddingType(null); setChosen(''); setMatched(''); setTiming(null); setNotice(''); setError(''); setBusy(false); setView('Memory'); setOffset(0); setReady(false); setMenuOpen(false);
  }
  const ignoreAbort = (e: Error) => { if (e.name !== 'AbortError') setError(e.message); };
  async function poll() {
    const [s, y] = await Promise.all([api('/status'), user === 'operator' ? api('/sync/status') : Promise.resolve(null)]); setStatus(s); setSync(y); setReady(true);
    if (generation.current !== s.generation) {
      generation.current = s.generation;
      if (view !== 'Sharing & activity') await list();
      if (selectedId.current) {
        const id = selectedId.current;
        try { const detail = await api(`/memories/${id}`); if (selectedId.current === id) setSelected(detail); }
        catch (e) { if ((e as Error).message === 'Record not found') closeInspector(); else throw e; }
      }
    }
  }
  async function list() { setMemories(await api(`/memories?limit=100&offset=${offset}&conflicts=${view === 'Needs review'}`)); }
  async function inspect(m: Memory) {
    selectedId.current = m.id; setMatched(m.matched_revision_id ?? ''); setChosen('');
    const detail = await api(`/memories/${m.id}`);
    if (selectedId.current === m.id) setSelected(detail);
  }
  function closeInspector() { selectedId.current = null; setSelected(null); setChosen(''); }
  async function action(fn: () => Promise<unknown>, message: string) {
    if (busy) return;
    const current = epoch;
    setBusy(true); setError('');
    try {
      await fn(); if (current !== epoch) return;
      await Promise.all([poll(), list()]); setResults(null); setNotice(message);
      if (selectedId.current) {
        const detail = await api(`/memories/${selectedId.current}`); setSelected(detail); setChosen('');
      }
    } catch (e) { if (current === epoch) ignoreAbort(e as Error); }
    finally { if (current === epoch) setBusy(false); }
  }
  useEffect(() => {
    api('/session').then(s => { csrf = s.csrf; setRole(s.role); setUser(s.username); }).catch(() => {}).finally(() => setChecking(false));
    const expired = () => { clear(); setError('Your session ended. Sign in again.'); };
    window.addEventListener('session-expired', expired);
    return () => window.removeEventListener('session-expired', expired);
  }, []);
  useEffect(() => {
    if (!menuOpen) return;
    closeMenuButton.current?.focus();
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setMenuOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => { window.removeEventListener('keydown', onKey); menuButton.current?.focus(); };
  }, [menuOpen]);
  useEffect(() => {
    if (!user) return;
    let stopped = false, timer: ReturnType<typeof setTimeout>;
    async function tick() {
      try { if (!document.hidden) await poll(); }
      catch (e) { if ((e as Error).name !== 'AbortError' && !stopped) setReady(false); }
      if (!stopped) timer = setTimeout(tick, document.hidden ? 15000 : 5000);
    }
    tick();
    let lastActivity = 0;
    const activity = (e: globalThis.Event) => {
      if (e.isTrusted && Date.now() - lastActivity > 30000) { lastActivity = Date.now(); api('/session/activity', 'POST').catch(() => {}); }
    };
    window.addEventListener('pointerdown', activity); window.addEventListener('keydown', activity);
    return () => { stopped = true; clearTimeout(timer); window.removeEventListener('pointerdown', activity); window.removeEventListener('keydown', activity); };
  }, [user, view, offset]);
  useEffect(() => {
    if (!user) return;
    if (view === 'Sharing & activity') api('/activity').then(setEvents).catch(ignoreAbort);
    else list().catch(ignoreAbort);
  }, [user, view, offset]);
  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); const d = new FormData(e.currentTarget); setBusy(true); setError('');
    try { const s = await api('/login', 'POST', { username: d.get('username'), password: d.get('password') }); csrf = s.csrf; setRole(s.role); setUser(s.username); }
    catch (e) { ignoreAbort(e as Error); } finally { setBusy(false); }
  }
  async function logout() {
    const token = csrf;
    clear();
    try {
      const response = await fetch('/api/logout', { method: 'POST', credentials: 'same-origin', headers: { 'X-CSRF-Token': token } });
      if (!response.ok && response.status !== 401) throw new Error();
    } catch { setError('Workspace hidden. Server sign-out could not be confirmed; close the local app to fully lock it.'); }
  }
  async function search(e: FormEvent) {
    e.preventDefault(); const order = ++searchOrder.current;
    if (!query.trim()) { setResults(null); return; }
    setBusy(true); setError(''); const start = performance.now();
    try {
      const r = await api('/search', 'POST', { query, mode: 'hybrid' });
      if (order === searchOrder.current) { setResults(r.results); setTiming({ backend: r.elapsed_ms, roundtrip: performance.now() - start }); }
    } catch (e) { ignoreAbort(e as Error); } finally { if (order === searchOrder.current) setBusy(false); }
  }

  if (checking) return <div className="loading">Opening local workspace…</div>;
  if (!user) return <main className="login"><div className="login-intro"><ThemeToggle /><Brand /><p className="eyebrow">Local memory workspace</p><h1>Keep working.<br />Even offline.</h1><p>Capture synthetic observations and find them in your protected local workspace.</p><div className="pills"><span><HardDrive size={16} /> Search stays local</span><span><ShieldCheck size={16} /> Protected storage on this device</span></div></div>
    <form className="login-card" onSubmit={login}><LockKeyhole aria-hidden="true" /><h2>Unlock your workspace</h2><p>Sign in with your locally provisioned account.</p><label>Username<input name="username" defaultValue="operator" autoComplete="username" required /></label><label>Password<input name="password" type="password" autoComplete="current-password" required /></label>{error && <p role="alert" className="error">{error}</p>}<button className="primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in locally'}</button><small>Five minutes of inactivity hides the workspace. Full vault lock is a separate local operation.</small></form><footer>Synthetic data only · Informational research prototype</footer></main>;

  const pending = (sync?.counts?.pending ?? 0) + (sync?.counts?.retry_wait ?? 0);
  const shown = results ?? memories;
  const navItems = user === 'operator'
    ? ['Memory', 'Visual logging', 'Needs review', 'Sharing & activity']
    : ['Memory', 'Visual logging', 'Needs review'];

  return <div className="shell">{menuOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
    <aside className={`sidebar ${menuOpen ? 'open' : ''}`} role={menuOpen ? 'dialog' : undefined} aria-modal={menuOpen ? true : undefined} aria-label="Workspace navigation"><Brand /><button ref={closeMenuButton} className="icon-button sidebar-close" aria-label="Close navigation" onClick={() => setMenuOpen(false)}><X /></button><div className="workspace"><b>{status?.workspace ?? user}</b><small>{status?.deployment === 'hospital_lan' ? 'Hospital LAN demo · synthetic' : 'Synthetic memory workspace'}</small></div>
      <nav aria-label="Primary">
        {navItems.map(v => (
          <button className={view === v ? 'active' : ''} aria-current={view === v ? 'page' : undefined} key={v} onClick={() => { setView(v); setOffset(0); setResults(null); closeInspector(); setMenuOpen(false); }}>
            {v === 'Memory' ? <FileText /> : v === 'Visual logging' ? <Activity /> : v === 'Needs review' ? <GitBranch /> : <RefreshCw />}
            {v}
            {v === 'Needs review' && !!status?.conflicts && <span className="count">{status.conflicts}</span>}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom"><p><LockKeyhole /> Highly sensitive notes are personal.</p><button onClick={logout}><LogOut size={17} />Sign out</button><small>Sign-out hides records; the local vault remains mounted.</small></div>
    </aside>

    <main className="main" inert={menuOpen}>
      <header className="topbar">
        <button ref={menuButton} className="icon-button mobile-menu" aria-label="Open navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(true)}><Menu /></button>
        <span className="topbar-context"><span>{status?.deployment === 'hospital_lan' ? status.workspace : status?.device ?? 'Device'}</span><ChevronRight size={15} /><strong>{view}</strong></span>
        <div className="topbar-actions"><span className="synthetic">Synthetic data</span><ThemeToggle /></div>
      </header>

      <div className="page">
        <div className="page-heading">
          <div>
            <p className="eyebrow">{status?.deployment === 'hospital_lan' ? `Workspace ${status.workspace}` : 'Local workspace'}</p>
            <h1>{view === 'Memory' ? 'Memory explorer' : view === 'Visual logging' ? 'Visual logging & monitoring' : view}</h1>
            <p>{view === 'Memory' ? 'Capture an observation. Find it when you need it.' : view === 'Visual logging' ? 'Fast structured data entry, real-time observation monitoring, and telemetry status.' : view === 'Needs review' ? role === 'admin' ? 'Compare current branches before choosing a resolution.' : 'An administrator can review and resolve conflicting branches.' : 'See what is waiting, what was accepted, and what happened.'}</p>
          </div>
          <button className="primary" onClick={() => setAddingType('STANDARD')}><Plus size={16} />Add observation</button>
        </div>

        <div className="status-row" role="status">
          <span className={ready ? 'good' : 'warn'}><HardDrive size={16} />{ready ? 'Local workspace ready' : 'Local service unavailable — saving cannot be confirmed'}</span>
          {user === 'operator' && <><span>{sync?.connection === 'connected' ? <Wifi size={16} /> : <WifiOff size={16} />}{connectionLabels[sync?.connection ?? 'unknown']}</span><button onClick={() => setView('Sharing & activity')}>{pending} approved updates pending</button></>}
          <button onClick={() => setView('Needs review')}>{status?.conflicts ?? 0} conflicts</button>
        </div>

        {error && <div className="error banner" role="alert">{error}<button className="icon" aria-label="Dismiss error" onClick={() => setError('')}><X size={16} /></button></div>}
        {notice && <div className="notice banner" role="status"><Check size={16} />{notice}<button className="icon" aria-label="Dismiss notice" onClick={() => setNotice('')}><X size={16} /></button></div>}
        {status?.worker_error && <div className="error banner">{status.worker_error}</div>}

        {view === 'Visual logging' ? (
          <VisualLoggingWorkspace
            memories={memories}
            status={status}
            sync={sync}
            ready={ready}
            role={role}
            onInspect={m => inspect(m).catch(ignoreAbort)}
            onOpenAdd={type => setAddingType(type || 'STANDARD')}
            onGoToReview={() => { setView('Needs review'); setOffset(0); }}
            onRefresh={() => { poll().catch(ignoreAbort); list().catch(ignoreAbort); }}
          />
        ) : view !== 'Sharing & activity' ? (
          <>
            <div className="toolbar">
              <form className="search" onSubmit={search}>
                <Search size={18} />
                <input aria-label="Search memory" placeholder="Search local memory by meaning or exact words…" value={query} onChange={e => setQuery(e.target.value)} />
                <button disabled={busy}>Search</button>
              </form>
              {role === 'admin' && <button className="secondary" disabled={busy} onClick={() => action(() => api('/demo/seed', 'POST'), 'Synthetic examples are ready.')}>Load examples</button>}
            </div>

            <div className="list-heading">
              <span>{results ? `${shown.length} local results` : view === 'Needs review' ? `${status?.conflicts ?? 0} needing review` : `${status?.total ?? 0} saved · ${status?.indexed ?? 0} searchable`}</span>
              {results && <><small>{timing?.backend} ms backend · {timing?.roundtrip.toFixed(1)} ms round trip</small><button onClick={() => { setResults(null); setQuery(''); }}>Clear search</button></>}
            </div>

            <div className="memory-table">
              {shown.map(m => (
                <button className="memory-row" key={m.id} onClick={() => inspect(m).catch(ignoreAbort)}>
                  <span className="record-icon"><FileText size={20} /></span>
                  <span className="memory-name">
                    <b>{m.title}</b>
                    <small>{m.subject ?? 'Reviewed shared reference'} · {m.category.toLowerCase().replaceAll('_', ' ')}</small>
                    {m.content && <span className="excerpt">{m.content}</span>}
                  </span>
                  <span className="record-flags">
                    <span className={'badge ' + (m.fixture ? 'teal' : '')}>{m.fixture ? 'Approved reference' : m.privacy === 'HIGHLY_SENSITIVE' ? 'Personal' : 'Workspace'}</span>
                    <span className={m.conflicting ? 'warn' : 'state'}>{m.conflicting ? 'Needs review' : m.index_state === 'indexed' ? 'Searchable' : 'Indexing'}</span>
                  </span>
                  <ChevronRight size={16} />
                </button>
              ))}
              {shown.length === 0 && (
                <div className="empty">
                  <FileText />
                  <h3>{view === 'Needs review' ? 'No conflicts to review' : results ? 'No matching memories' : 'No observations yet'}</h3>
                  <p>{view === 'Needs review' ? 'New conflicts will appear here for review.' : results ? 'Try a different phrase or clear your search.' : 'Add an observation or load synthetic examples to try local search.'}</p>
                  {!results && view === 'Memory' && <button className="secondary" onClick={() => setAddingType('STANDARD')}>Create first observation</button>}
                </div>
              )}
            </div>

            {!results && (view === 'Needs review' ? (status?.conflicts ?? 0) > 0 : (status?.total ?? 0) > 0) && (
              <div className="pagination">
                <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>Previous</button>
                <span>Page {offset / 100 + 1} of {Math.max(1, Math.ceil((view === 'Needs review' ? status?.conflicts ?? 0 : status?.total ?? 0) / 100))}</span>
                <button disabled={memories.length < 100} onClick={() => setOffset(offset + 100)}>Next</button>
              </div>
            )}
          </>
        ) : (
          <>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>{connectionLabels[sync?.connection ?? 'unknown']}</h2>
                  <p>Only reviewed synthetic reference variants can leave this device.</p>
                  <small>Last verified contact: {date(sync?.last_sync)}</small>
                </div>
                <div className="actions">
                  <button className="secondary" disabled={busy} onClick={() => action(() => api('/sync/transport', 'POST', { enabled: !sync?.enabled }), sync?.enabled ? 'Sharing paused. Local work continues.' : 'Sharing enabled; checking the shared service.')}>{sync?.enabled ? 'Pause sharing' : 'Enable sharing'}</button>
                  <button className="primary" disabled={busy || !sync?.enabled} onClick={() => action(() => api('/sync', 'POST'), 'Sharing attempt finished. Check the status below.')}>Sync now</button>
                </div>
              </div>
              {sync?.error && <p className="error">{sync.error}</p>}
              <div className="queue-summary">
                <b>{pending} waiting / retrying</b>
                <span>{sync?.counts?.failed ?? 0} need attention</span>
                <span>{sync?.counts?.acknowledged ?? 0} accepted centrally</span>
              </div>
              <p className="muted">Central acceptance does not confirm receipt on another device. Check Device B to demonstrate delivery.</p>
              {sync?.items.length ? (
                sync.items.slice(-40).reverse().map(item => (
                  <div className="queue-item" key={item.id}>
                    <span>Approved reference update<small>{item.attempts} attempts{item.error ? ` · ${item.error}` : ''}</small></span>
                    <span className="badge">{item.state === 'acknowledged' ? 'Accepted centrally' : item.state.replaceAll('_', ' ')}</span>
                  </div>
                ))
              ) : (
                <div className="empty">No approved updates waiting. Private observations never enter this queue.</div>
              )}
              <details>
                <summary>Reference cache and diagnostics</summary>
                <p>Search always runs locally. A signed reference-cache refresh is optional.</p>
                <button className="secondary" disabled={busy || !sync?.enabled} onClick={() => action(() => api('/sync/reference-snapshot', 'POST'), 'Signed reference cache verified and activated.')}>Refresh reference cache</button>
                <p>Encrypted vault: {status?.vault ? 'Verified at startup' : 'Test environment'} · SQLCipher + Qdrant Edge</p>
              </details>
            </section>
            <section className="panel">
              <h2><Activity size={20} /> Activity history</h2>
              <button className="secondary" onClick={() => api('/activity').then(setEvents).catch(ignoreAbort)}>Refresh activity</button>
              <div className="timeline">
                {events.map((e, i) => (
                  <div key={i}>
                    <b>{e.action.replaceAll('_', ' ')}</b>
                    <span>{e.device}</span>
                    <time>{date(e.time)}</time>
                  </div>
                ))}
                {events.length === 0 && <p className="muted">No activity recorded yet.</p>}
              </div>
              <small>Metadata-only audit events. Chaining is verified at startup; it does not prove protection against whole-store rollback.</small>
            </section>
          </>
        )}

        <footer>Local memory · Explicit sharing · Human review</footer>
      </div>
    </main>

    {addingType !== null && (
      <Dialog title="Add observation" onClose={() => setAddingType(null)}>
        <StructuredObservationForm
          initialType={addingType}
          busy={busy}
          onSave={async (payload: StructuredMemoryPayload) => {
            await action(async () => {
              await api('/memories', 'POST', payload);
              setAddingType(null);
            }, 'Saved on the protected server. Search indexing follows automatically.');
          }}
          onCancel={() => setAddingType(null)}
        />
      </Dialog>
    )}

    {selected && (
      <Dialog title="Memory inspector" onClose={closeInspector}>
        <span className="badge">{selected.fixture ? 'Approved synthetic reference' : selected.privacy === 'HIGHLY_SENSITIVE' ? 'Personal · only you' : 'Shared in workspace'}</span>
        <h3>{selected.title}</h3>
        <p>{selected.subject ?? 'Reviewed reference'}</p>
        {selected.conflicting && <p className="warning">Multiple current branches exist. {role === 'admin' ? 'Choose a resolution below.' : 'Ask your workspace administrator to resolve them.'}</p>}
        <div className="note-content">{selected.revisions?.find(r => r.id === matched)?.content ?? selected.content}</div>
        {matched && <small>Search matched revision {matched.slice(0, 8)}.</small>}
        <p className="policy-box"><ShieldCheck size={18} />{selected.reason}</p>

        {selected.conflicting && role === 'admin' && (
          <section>
            <h3>Compare current branches</h3>
            <div className="branches">
              {selected.revisions?.filter(r => selected.heads.includes(r.id)).map(r => (
                <label className="branch" key={r.id}>
                  <input type="radio" name="chosen" value={r.id} checked={chosen === r.id} onChange={() => setChosen(r.id)} />
                  <b>{r.device} · {date(r.created)}</b>
                  <span>{r.content}</span>
                </label>
              ))}
            </div>
            <p>A new revision will preserve the history of both branches.</p>
            <button className="primary" disabled={busy || !chosen} onClick={() => action(() => api(`/memories/${selected.id}/resolve`, 'POST', { parents: selected.heads, chosen }), 'Conflict resolved with a new revision.')}>Confirm chosen branch</button>
          </section>
        )}

        <details>
          <summary>Revision history ({selected.revisions?.length ?? 1})</summary>
          {selected.revisions?.map(r => (
            <div className="revision" key={r.id}>
              <b>{selected.heads.includes(r.id) ? 'Current branch' : 'Previous revision'}</b>
              <small>{r.device} · {date(r.created)}</small>
              <p>{r.content}</p>
            </div>
          ))}
        </details>

        {selected.fixture && role === 'admin' ? (
          <section>
            <h3>Reviewed reference edits</h3>
            <p>Select a predefined synthetic variant to demonstrate sharing.</p>
            <div className="actions">
              {[1, 2].map(v => (
                <button className="secondary" disabled={busy || selected.conflicting} key={v} onClick={() => action(() => api(`/memories/${selected.id}/reference-variant`, 'POST', { parent: selected.heads[0], variant: v }), `Approved variant ${v} saved and queued.`)}>Save variant {v}</button>
              ))}
            </div>
          </section>
        ) : !selected.fixture && !selected.conflicting ? (
          <form onSubmit={e => {
            e.preventDefault();
            const d = new FormData(e.currentTarget);
            action(() => api(`/memories/${selected.id}/revisions`, 'POST', { parent: selected.heads[0], content: d.get('content') }), 'Revision saved locally.');
          }}>
            <label>Add a corrected observation<textarea name="content" required maxLength={12000} /></label>
            <button className="secondary" disabled={busy}>Save revision</button>
          </form>
        ) : null}

        {(role === 'admin' || selected.privacy === 'HIGHLY_SENSITIVE') && (
          <details className="danger-zone">
            <summary>Archive / deletion</summary>
            <p>Remove from active search. Protected revision history is retained.</p>
            <button className="danger" disabled={busy} onClick={() => action(async () => { await api(`/memories/${selected.id}`, 'DELETE'); closeInspector(); }, 'Memory removed from active search.')}>Remove from active memory</button>
          </details>
        )}
      </Dialog>
    )}
  </div>;
}
createRoot(document.getElementById('root')!).render(<App />);
