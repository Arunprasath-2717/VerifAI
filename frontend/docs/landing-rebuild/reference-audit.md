# VerifAI reference audit — 2026-11-01

Method: Firecrawl URL maps and live markdown/branding scrape for the three websites; desktop Playwright runtime inspection attempted. Screenshots shared by the user were also examined. Text describing reference functionality is **reference content**, not a claim about VerifAI.

## MotionSites — https://motionsites.ai/
- Live map: templates, sections, 3D websites, backgrounds, app prompts, academy and lesson pages.
- Live homepage scrape: Featured/Popular/Recent controls, many category chips (Apps, Hero, Landing Page, SaaS, AI, etc.), dense masonry-style cards with thumbnails, names and categories. The site showcases hover and scroll ideas through labeled examples.
- Inspired implementation: VerifAI's original category-controlled gallery of product states; cards get slight image motion and a click-to-inspect dialog. No copied screenshots or branding.
- Runtime behavior: record separately if Chromium can reach the public page.

## Sparkdesign — https://rbp-sparkdesign-template.vercel.app/
- Scraped hierarchy: airy introduction, visual workspace mockups, feedback-on-canvas, multiple storytelling chapters, projects with category filters, illustrative plans, FAQ and footer.
- Branding scrape: bright light aesthetic, Instrument Sans, large comfortable text, thin lines, restrained image framing; sparse UI chrome.
- Inspired implementation: sections with wide negative space, alternating light surfaces, diagrams and editorial headings. VerifAI has no invented customer quotes or pricing.

## KRAFT — https://rbp-ai-saas-template.vercel.app/
- Scraped hierarchy: bold headline and prompt modes, idea-to-result narrative, draggable designs, comparative evidence, testimonials, pricing, accordion and waitlist.
- Distinctive visual: deep top, light blue-gray lower atmosphere, large monospaced title, off-white composer with compact mode chips and submit arrow.
- Inspired implementation: immersive hero with type-driven choreography, functional draft composer, scroll transition, comparison demo, and final CTA. No copied brands, metrics, testimonials or logos.
- KRAFT numeric results/testimonials and prices are not portable facts about VerifAI.

## Product grounding
VerifAI is an existing React/Vite + FastAPI application. Existing routes include /chat, /verify, /leaderboard, /reports, /settings, /privacy, /terms and /login. Authentication guards application routes. Public landing may showcase an explicitly illustrative comparison while links open the actual workspace. No public pricing or authentic testimonial data verified.

## Constraints
Original HTML/SVG product mockups only; avoid reference screenshots and unlicensed imagery. No neon, bloom, bright radial spotlights, luminous halos or decorative particles. Animations respect reduced motion and don't block content.

## Browser runtime inspection (Playwright on Pikachu)
- **MotionSites:** navigation to the live website timed out from Chromium; Firecrawl map and markdown scrape did succeed. Specific hover/drag timings are **not observed**. Filters/categories and card structure are supported by the scrape and user screenshot.
- **Sparkdesign:** Chromium loaded desktop page. It exposed an editable/interactive concept template with comment resolution, version switching, process states and project category filters. Scrollable document approximately 9.5k CSS pixels at desktop (environment specific). The page's own content says some interactions are local demos.
- **KRAFT:** Chromium loaded desktop page. Heading/composer/mode controls, image/process sections, sample benchmark/testimonial/pricing blocks and FAQ controls were visible. Scrollable document approximately 10k CSS pixels in the test environment. Marketing metrics in that template were not reused.
- **Mobile references:** user-provided captures are used for visual direction, but all dynamic mobile reference behaviors were not exhaustively verified. The VerifAI implementation itself was tested at multiple mobile widths.
- Reference screenshot files used only for visual study; no image, reference CSS, logo, source code, or builder badge was copied into VerifAI.
