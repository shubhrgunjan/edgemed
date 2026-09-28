# Frontend refinement plan

The existing React application, routes, requests, permissions, and data shapes stay in place. The app and public demo currently duplicate theme-switch styling, use raw palette colors directly, and mix control heights, radii, and spacing. The login has a gradient and oversized headline; the mobile app places all navigation in a cramped horizontal row. Results and sharing use too many boxed surfaces.

1. Define semantic Latte/Mocha colors, spacing, typography, radii, and control heights in one theme layer. Share button, field, status, brand, dialog, and theme-switch rules across the app and demo.
2. Tighten the app shell: stable 232px sidebar, 56px top bar, bounded content width, and a mobile navigation drawer. Keep synthetic-data and local-state cues visible without badge clutter.
3. Make search and results the Memory page focus. Use a compact status strip, scan-friendly record rows, small empty states, attached pagination, and restrained sharing/activity lists.
4. Rework login, add/inspect dialogs, review decisions, and the public browser demo with the same visual rules. Preserve all existing labels and request behavior needed by browser tests.
5. Build both frontend targets, run existing browser checks, and inspect wide, narrow, tablet, and mobile screenshots in Latte and Mocha. Fix wrapping, contrast, and focus regressions found there.
