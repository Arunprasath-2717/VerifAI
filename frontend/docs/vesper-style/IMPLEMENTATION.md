# VerifAI / Vesper-inspired landing reconstruction — 2026-11-01

Source: user-provided *Pasted text.txt* single-screen Vesper.ai reference specification. The implementation adapts its style, motion schedule, media, and responsive system to the **existing VerifAI React/Vite application** without altering authentication or product routes. No unsupported Vesper marketing claims, numbers, characters, or logos have been copied.

## Implemented
- Single viewport on desktop: dark #000 background, accessible logo + four functional navigation links, metallic pills, bottom-centered two-line headline, gray Instrument Serif italic emphasis, primary and secondary CTA, and exactly three non-numeric product proof points.
- Mobile: responsive stacked proof points and CTA controls; hamburger with blurred full-screen panel; Escape/overlay/selection/resize close menu.
- Entrance sequences CSS-keyframed in user-specified staggered order with React animation-end cleanup and two-requestAnimationFrame fallback. Reduced motion supported.
- Media: downloaded the **exact CloudFront URL explicitly included in the uploaded user reference** (10.04s, 1920×1080, HEVC) into public/vesper-style/media/hero-source.mp4 and converted it to playable H.264 yuv420p 1280×720 fast-start public/vesper-style/media/hero-browser.mp4 (~3.1MB) after checking browser compatibility. Downloaded file is user-supplied reference media, usage rights must be confirmed separately before public deployment.
- Fonts: self-hosted Latin subset Inter variable and Instrument Serif italic WOFF2 from Google Fonts, both using font-display: swap. No font assets are included in downloadable deliverables or exposed separately here.
- Application routes preserved: /login, /signup, /chat, /verify, /reports, /dashboard. GitHub link points to project repository. A custom SVG favicon replaces default browser missing favicon response.

## Validation
- TypeScript and production build passed.
- Chromium checked at 1920×1080, 1440×900, 1280×800, 1024×768, 900×900, 768×1024, 390×844, 360×800, and 320×650: no detected horizontal overflow, no JS/network errors, fixed one-screen desktop.
- Video H.264 readyState 4, currentTime advancing and paused=false on both desktop and mobile.
- Mobile menu opens and closes with Escape after transition.
- Real browser screenshots used to refine mobile media framing and typography contrast.

## Scope/limitations
- This is the complete **public landing** style refresh, not a restyle of the authenticated workspace or login pages.
- Only the reference's described static page style is recreated; 3D, WebGL, extra sections and invented business metrics were intentionally omitted in accordance with its strict layout.
- Lighthouse, Safari testing and public deployment not performed. License for supplied CloudFront footage should be confirmed before commercial publication.
