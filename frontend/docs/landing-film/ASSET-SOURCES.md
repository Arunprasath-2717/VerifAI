# VerifAI / CINEMA — authentic asset provenance

The four-section public landing uses real stock photography and video, **not AI-generated images**. No reference website screenshots, logos, template source code, or watermarks are part of the visuals.

## Visible media

| On-page element | Local file | Source | License |
|---|---|---|---|
| Hero aerial sea video | `landing-film/coast-source.mp4` | ArtHouse Studio, [Pexels #4631568](https://www.pexels.com/video/aerial-view-of-ocean-waves-4631568/) | [Pexels License](https://www.pexels.com/legal-pages/license/) |
| Hero poster | `landing-film/ocean-poster.jpg` | Frame captured from the licensed Pexels #4631568 source above | Same |
| Closing background video | `landing-film/coast-secondary-source.mp4` | Polina, [Pexels #7587023](https://www.pexels.com/video/drone-footage-of-ocean-waves-crashing-on-rocks-7587023/) | Pexels License |
| Closing video poster | `landing-film/closing-poster.jpg` | Frame from Pexels #7587023 | Same |
| Low-angle architecture | `landing-film/architecture.jpg` | [Unsplash photo-1486406146926-c627a92ad1ab](https://unsplash.com/photos/1486406146926-c627a92ad1ab) | [Unsplash License](https://unsplash.com/license) |
| Earth / atmosphere photograph | `landing-film/earth.jpg` | [Unsplash photo-1446776811953-b23d57bd21aa](https://images.unsplash.com/photo-1446776811953-b23d57bd21aa) | Unsplash License |
| Mountains (reduced-motion poster fallback) | `landing-film/summit.jpg` | [Unsplash photo-1464822759023-fed622ff2c3b](https://images.unsplash.com/photo-1464822759023-fed622ff2c3b) | Unsplash License |
| Subtle hero photographic texture | `landing-film/cliffs.jpg` | [Unsplash photo-1465982046896-5172ca240f27](https://images.unsplash.com/photo-1465982046896-5172ca240f27) | Unsplash License |

Additional downloaded editorial stills under `landing-film/` are reserved for iteration and are not loaded by the current page. The videos have been downloaded locally rather than hotlinked.

## Implementation
- Landing route: `src/pages/LandingPage.tsx`
- Scoped styles: `src/pages/LandingPage.css`
- Self-hosted fonts: Space Grotesk + Instrument Serif, fetched from Google Fonts with an OFL license; fallback stacks supplied.
- Motion: Motion for React scroll-linked transforms, CSS perspective/3D object rotation, masked headline reveal, synced staged story, pointer-following cursor, hover states, reduced-motion fallbacks.
- Navigation and CTA preserve real app routes; the marketing page does not generate simulated model outputs.
