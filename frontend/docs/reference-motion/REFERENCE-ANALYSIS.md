# VerifAI: cinematic reference video analysis and implementation
Date: 2026-11-01

## Source
- Uploaded source: `original-15f093aeaaa8db2dba3fc53bf15e0c67.mp4` (user-provided, 1600×1200, H.264, 30fps, 16.3667s; AAC audio).
- The video is a screen capture of another website, with browser-gray space surrounding an approximately 16:9 rounded website frame. Its graphics, text, and controls are baked into the video; it is not a standalone clean background footage file.
- No third-party site screenshot, name, pricing, endorsements, customer claims or logos are published as VerifAI page assets.

## Observed time-based storyboard
| Approximate video time | Observed reference | Implementation |
|---|---|---|
| 0–2s | Black hero, small centered green compute chip, large white headline reveals from blurred state; sweeping convergent emerald arcs behind text; compact dark centered nav | Original 3D processor-like chip built in CSS, masked typography entrance, clean self-rendered emerald video with two sweeping optical arcs, functional navigation |
| 2–5s | Hero remains black; dark inset icons/three capability blocks beneath CTA; scrolling begins exposing dark secondary panel | Dark verification section with linked three-step progression and scroll choreography |
| 5–7s | Black section headline: verification/trust theme, three small green circuit glyphs joined by fine lines | Three verification steps: compare responses, review claims, preserve evidence-aware synthesis |
| 7–11s | Hard transition to white/very pale mint; large dark-green heading; deep-black/green abstract optical art at left; mint list of AI risks at right | White-to-mint split with the same original looping arc video reframed, and project-grounded hallucination/conflicting-output/source-context challenges |
| 11–13s | White field with green dot motifs; green-accented solutions statement enters | White editorial transition, mint/accent type treatment |
| 13–16.37s | Deep forest-green panel expands below heading; large 'Verifiable' type at left and three trust pillars at right | Deep-emerald panel with large VERIFIABLE. statement, restrained dot motion and interactive three-stage explanation |

## Visual construction
- Palette: near-black #000704, deep forest #07523a, mint #dffbe8, luminous accent #2bda80, bright white #fbfffc.
- Text: self-hosted Inter, low-tracking large sans headings, soft mint secondary type; no embedded text images.
- Arc motion: generated from original vector geometry into a 7-second looping browser H.264 mp4 and PNG poster, `public/reference-motion/emerald-ribbons.mp4`, `emerald-ribbons.svg`, `emerald-poster.png`. These are original procedural assets, not exact extracted footage from the referenced website.
- Motion: entrance blur/translate, scroll-linked processor y and fade, perspective rotation, stepped verification reveals, secondary media shown only while intersecting viewport, solution-panel clip reveal; reduced-motion static frames.

## Application contract
- Exactly 4 main sections (hero plus three), then footer.
- Existing login, signup, dashboards, model chat, verification, reports and legal pages stay outside redesign scope.
- Functional controls: navigation anchor links, login/application CTA, keyboard/Escape mobile menu, solution controls (using existing shadcn-style Button), functional external GitHub/legal links.
- No invented customer testimonials, accuracy figures, pricing, live AI demo results or ungrounded verification guarantees.

## Verification
- npm run lint: passed.
- npm run build: passed.
- Playwright Chromium at 1440×900, 1280×800, 768×1024, 390×844, 360×800: no horizontal overflow or JS/network errors; exactly four main sections.
- Foreground hero video plays when visible, secondary arc video plays after scrolling into the challenge. Offscreen video is paused to preserve resources.
- Mobile menu opens and closes via Escape; solution controls change `aria-pressed`; reduced-motion mode has no autoplay video and shows the H1.
- Impeccable mechanical detector run once: `[]` (no reported findings).
- Not measured: Lighthouse, sustained FPS across hardware, Safari/WebKit, actual backend model/inference requests.
- This is a local Pikachu development implementation; it has not been deployed or committed.
