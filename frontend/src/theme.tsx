import { useState } from 'react';
import { Coffee, Moon } from 'lucide-react';

export type Flavor = 'latte' | 'mocha';
const KEY = 'edgemed-theme';

function initialFlavor(): Flavor {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === 'latte' || saved === 'mocha') return saved;
  } catch { /* Private browsing may disable storage. */ }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'mocha' : 'latte';
}

let current = initialFlavor();
document.documentElement.dataset.theme = current;

export function ThemeToggle() {
  const [flavor, setFlavor] = useState<Flavor>(current);
  function toggle() {
    const next = flavor === 'latte' ? 'mocha' : 'latte';
    current = next;
    document.documentElement.dataset.theme = next;
    setFlavor(next);
    try { localStorage.setItem(KEY, next); } catch { /* Theme stays active for this tab. */ }
  }
  return <button className="theme-switch" type="button" role="switch" aria-checked={flavor === 'mocha'}
    aria-label={`Theme: ${flavor}. Switch to ${flavor === 'latte' ? 'Mocha' : 'Latte'}`} onClick={toggle}>
    <span className="theme-track" aria-hidden="true"><Coffee /><Moon /><span className="theme-thumb" /></span>
    <span>{flavor === 'latte' ? 'Latte' : 'Mocha'}</span>
  </button>;
}
