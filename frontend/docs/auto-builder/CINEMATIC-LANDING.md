# VerifAI cinematic landing — AUTO-BUILDER workflow application

Reference: https://github.com/bsrikumar855-dot/ClaudeCODE-Autonomous-skills (Apache-2.0). Its documentation describes milestone-based engineering, bounded specialist tasks, independent QA and evidence-based delivery. We studied the repository and applied the workflow principles; this does not claim Claude Code subagents were executed.

## Scope / acceptance criteria
- Preserve user-requested 4 main sections: full-screen hero, vision, perspectives, resolution; then footer.
- Keep existing auth and application routes unchanged.
- Remove prompt input and UI-heavy site components from the new landing.
- Cinematic video with original non-AI stock sources and defensible licenses.
- Premium editorial text with real readable text nodes, responsive typography and motion accessible fallbacks.
- Smooth section camera/depth movement, visual continuity, interactive cursor and real controls.

## Milestones
1. **Discovery** VERIFIED — inspected existing frontend, original media, Github skill README and implementation/verification workflow. Preserved local project changes.
2. **Media design & implementation** VERIFIED — produced licensed-stock 12.72s 1280x720 crossfade film from pre-existing real space and coast sources using FFmpeg; 3.6MB with poster fallback. Existing separate perspective and resolution video remain.
3. **Typography and motion** VERIFIED — refined hero sizing and layered cinematic color grade, scroll-linked camera treatment for vision imagery/headline, section cues; reduced-motion fallback retained.
4. **Build and browser QA** VERIFIED — TypeScript noEmit and Vite build passed; Playwright at 1440x900 and 390x844: four content sections, no JS/network errors, no horizontal overflow; hero video readyState=4 with 12.72s duration, mobile nav opens and Escape closes.

## Explicit limitations
- No Claude Code 9-agent swarm was run, nor an independent reviewer. The AUTO-BUILDER repository is a workflow orchestration tool, not a bundle of visual animations.
- Full Lighthouse metrics, FPS during rapid scroll, and Safari testing were not measured.
- No deployment or push to GitHub was made.

## Asset record
- `public/cinema/threshold-film.mp4`: original FFmpeg montage of the previously downloaded real orbital imagery and Pexels coast footage.
- `public/cinema/threshold-poster.jpg`: first-second frame from the montage.
- Existing original licensed media sources and photographer/source details: `docs/cinema-rebuild/ASSETS.md`.
