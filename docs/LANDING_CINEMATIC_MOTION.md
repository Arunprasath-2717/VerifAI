# VerifAI cinematic landing — motion and source notes

The October 2026 landing redesign is an original implementation, inspired by the editorial scale, layered scroll experience, and atmospheric product reveals of the Shopify Winter '26 Editions site. No Shopify imagery, scripts, or proprietary source were copied.

Source references consulted:
- https://www.shopify.com/editions/winter2026 — story rhythm, visual layering, navigation hierarchy, spatial section transitions.
- https://animejs.com/documentation/events/onscroll/ — scroll synchronization model. Actual Anime.js is used here to animate the orbit, deliberately separate from scroll-linked Motion.
- https://reactbits.dev/c/text-animations and https://reactbits.dev/c/backgrounds — restrained text, atmospheric visual concepts; composed with existing React primitives instead of copying effects.
- https://ui.aceternity.com/components/hero-parallax and https://ui.aceternity.com/components/3d-card-effect — depth, staged perspective, directional scroll movement; custom CSS 3D.
- https://21st.dev/community/components/explore/scroll-animation-component — sticky-scroll storytelling, cinematic product framing.
- https://www.cult-ui.com/docs — motion as meaningful feedback and interaction, not decoration.
- https://magicui.design/docs/components/scroll-progress and https://magicui.design/docs/components/orbiting-circles — top progress indicator, spatial orbit metaphor.
- https://github.com/darkroomengineering/lenis — dedicated smooth scrolling; instantiated only while public landing is mounted.

Implementation:
- Main feature is a long cinematic hero with a sticky scene, scroll-linked 3D perspective, layered model response surfaces, and scene-to-scene text choreography. Uses Motion's scroll/spring hooks.
- Lenis handles desktop fine-pointer scrolling only; touch devices keep native momentum. Both honor reduced-motion settings.
- Anime.js provides the slow orbit motion; videos pause on hidden tabs or out-of-view.
- Product illustrations use actual HTML/CSS, not scraped templates or external assets.
- Claims and verdicts in artwork are explicitly illustrative. No fake live data.
- The hero never blocks scrolling and anchors link to real sections. Authentication-related links respect signed-in state.

