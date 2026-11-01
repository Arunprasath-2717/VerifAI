# VerifAI landing page — QA results (2026-11-01)
Tested against the local React/Vite site on Pikachu, http://localhost:3000/.

## Build and route integrity
- `npm run lint` — PASS (TypeScript noEmit)
- `npm run build` — PASS
- Existing authenticated and legal routes remain unchanged; public home route still maps to LandingPage.

## Responsive visual audit
Tested Chromium viewports: 1440×900, 1280×800, 1024×768, 768×1024, 390×844, 360×800.
- Every viewport: no horizontal overflow; 10 main content sections, header and footer.
- No JavaScript errors in final interaction pass at 1440×900 and 390×844.
- Gallery cards and desktop-to-mobile layout adapt with CSS grids; sticky method becomes non-sticky on mobile.
- Responsive screenshots captured locally under /tmp/verifai-v2-* on Pikachu.

## Interaction QA
- Composer: empty input shows accessible validation; mode chips update `aria-pressed`; valid draft opens an explicitly disclosed preview; Cmd/Ctrl+Enter works; Escape closes; sessionStorage draft preserved in browser when available.
- Draft is **not** sent to a real AI service by the landing page, and does **not** auto-populate an authenticated workspace; copy/paste may be needed.
- Product tabs: selected tab changes interface mockup and explanation.
- Gallery filter: Models, Evidence and Workflow show expected two cards after exit animation; filters and modal work with pointer; Escape closes.
- Gallery dialogs: focus moves to close button and returns to opening card on dismissal.
- Horizontal reel: arrow controls change scroll position (desktop +475px, 390px mobile +286px in test); keyboard arrow and pointer drag implemented.
- Slider: actual range input changes clipped evidence illustration and value; examples are non-live and labeled.
- FAQ: native accessible details can expand/collapse.
- Mobile nav: toggles and closes with Escape; anchors navigate to content.
- Sticky storytelling: tested all four states at scroll positions. Desktop pinned; mobile and reduced-motion fallbacks remove pinning.
- CTA destinations: auth-aware /login or existing authenticated app routes; no invented signup/waitlist submissions.

## Known limitations / not measured
- Lighthouse scores, LCP and INP **not measured**; do not treat targets as guarantees.
- Live AI API calls, provider credentials, authentication, and backend verification workflows were not exercised by marketing-page tests.
- No real customer quotes, benchmark figures or pricing were added; the requested template sections were replaced with genuine use cases and truthful product capability explanations.
- No WebGL was added: the four-step DOM composition is the deliberate scroll-frame sequence, to reduce fragility and runtime weight.
- MotionSites public page timed out in Chromium, although Firecrawl research was successful.
