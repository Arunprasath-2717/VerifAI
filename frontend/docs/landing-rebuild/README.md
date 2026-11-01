# VerifAI / EDITION 02 landing page

## Location
- `src/pages/LandingPage.tsx` — sections, header, hero and footer.
- `src/pages/LandingPage.css` — fully scoped visual system.
- `src/pages/landing/PromptComposer.tsx` — draft composer and accessible preview.
- `src/pages/landing/InteractiveSections.tsx` — interactive gallery, tabs, scroll story, FAQ and comparison.
- `src/pages/landing/Visuals.tsx` — illustrations, reveals and dialog focus management.
- `src/pages/landing/landing-data.ts` — editable, project-grounded copy and demo data.
- `docs/landing-rebuild` — reference audit, design tokens, motion spec, asset manifest and tests.

## Run
```bash
cd /home/arun/Desktop/VerifAI/VerifAI/frontend
npm run dev
```
Visit http://localhost:3000/. Application routes remain attached to the existing router. To test type checking and production output: `npm run lint && npm run build`.

## Important behavior
Public composer is a **draft preview only**. It does not request AI responses or claim evidence checks. Users sign in via existing authentication flows. Copy/paste the draft into the app if necessary.

No paid reference media, brand logos, watermark removal, or third-party code was used. Visuals are original DOM/CSS/SVG compositions.
