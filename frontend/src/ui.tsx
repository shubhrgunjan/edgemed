import { useEffect, useRef, type ReactNode } from 'react';
import { GitBranch, X } from 'lucide-react';

export function Brand() {
  return <div className="brand"><span className="brand-mark"><GitBranch aria-hidden="true" /></span><span>EdgeMed<span className="brand-dot">.</span></span></div>;
}

export function Dialog({ title, heading, onClose, children, closeOnBackdrop = false }: {
  title: string; heading?: ReactNode; onClose: () => void; children: ReactNode; closeOnBackdrop?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    const root = ref.current!;
    const controls = () => Array.from(root.querySelectorAll<HTMLElement>(
      'button:not([disabled]),input:not([disabled]),textarea:not([disabled]),select:not([disabled]),summary,[tabindex="0"]'
    )).filter(element => element.getClientRects().length > 0 &&
      (element.tagName === 'SUMMARY' || !element.closest('details:not([open])')));
    controls()[0]?.focus();
    function key(e: KeyboardEvent) {
      if (e.key === 'Escape') { e.preventDefault(); closeRef.current(); }
      if (e.key === 'Tab') {
        const nodes = controls(), first = nodes[0], last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
        if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
      }
    }
    root.addEventListener('keydown', key);
    return () => { root.removeEventListener('keydown', key); previous?.focus(); };
  }, []);
  return <div className="overlay" onMouseDown={e => { if (closeOnBackdrop && e.target === e.currentTarget) onClose(); }}>
    <div ref={ref} className="dialog" role="dialog" aria-modal="true" aria-label={title}>
      <div className="dialog-heading"><h2>{heading ?? title}</h2><button className="icon-button" aria-label={`Close ${title}`} onClick={onClose}><X /></button></div>
      {children}
    </div>
  </div>;
}
