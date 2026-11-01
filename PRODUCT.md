# VerifAI — Product Context

<!-- impeccable:product-schema 1 -->

## Platform
web

## Users
Users of generative AI who need to compare answers, inspect sources, or verify factual claims. More specific commercial audience/market fit is not yet confirmed.

## Product Purpose
VerifAI helps users move from AI-generated text to an inspectable, evidence-first workflow. Users can verify extracted claims or compare responses from multiple independent models and request synthesis and verification.

## Positioning
It distinguishes model agreement from factual evidence and refuses to convert missing sources or model failures into proof.

## Operating Context
Authenticated React web workspace with two principal entry points: Paste & Verify and concurrent multi-model chat. Verification results link claim-level evidence and source provenance; history and dashboard routes preserve previous runs.

## Capabilities and Constraints
- Claim extraction, evidence retrieval, and evidence-based outcomes.
- Model comparison and synthesis across up to three selected working models, based on provider availability and user configuration.
- User-owned provider keys supported where configured; no credential fields or keys may be exposed on the public landing.
- Evidence can be supported, contradicted, unknown, failed, or unavailable. Product UI must not fabricate citations, accuracy, live model responses, benchmark results or proof.
- Browser auth routes already implemented; public landing must retain functional navigation into /login, /dashboard, /chat, and /verify.
- React 19, Vite, TypeScript, Motion, Anime.js, Lenis; preserve application workflows and backend.

## Brand Commitments
The project and its previous messages establish the name VerifAI, an evidence-first tone, an explicitly cinematic 3D landing, and a request to remove the hero background video completely. New design must not reintroduce video.

## Evidence on Hand
Project README and existing frontend implementation. UI demonstration data are illustrative and should be labelled as such; no live results available to the marketing page.

## Product Principles
1. Evidence before confidence.
2. Preserve and expose uncertainty.
3. Inspectable source trails.
4. Beautiful storytelling must never obscure factual boundaries.
5. Respect performance, device constraints, and reduced-motion settings.

## Accessibility & Inclusion
Support responsive layouts, keyboard navigation, contrast, reduced motion, and operation without WebGL. No specific conformance certification has been confirmed.

## Open Decisions
Final target user personas, conversion metrics, case studies, validation claims, and marketing proof have not been confirmed and must not be invented.

