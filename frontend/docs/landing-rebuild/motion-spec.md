# Motion specification
| Element | Trigger | Motion | Timing / fallback |
|---|---|---|---|
| Main hero headline | first load | two clipped lines translate 32px → 0 with opacity | 800ms stagger 140ms; immediately visible with reduced motion |
| Composer | first load | translate 24px → 0, subtle opacity | 760ms, no input blocking |
| Section headings | scroll viewport | masked upward reveals | ~650–800ms; instant when reduced motion |
| Transition statement | scroll within section | restrained text translation + background interpolation through CSS | scrubbed; static fallback |
| Sticky story | scroll through 4 stages | stage progress and layered UI layouts; active labels change | pinned desktop, stacked mobile and reduced motion |
| Product gallery | tab/filter | selection underline, content fades into new filtered set | ~250ms, without document reflow loops |
| Showcase frames | hover/active tab | shift 4–10px, background and mock content update | 220–400ms |
| Compare slider | pointer/touch/keyboard | clip comparison layer at user-selected value | direct interactive position, no fake result metrics |
| FAQ | disclosure activation | animated height on details container | native details semantics / reduced motion |
| Final CTA | viewport entrance | typography rise and subtle surface shift | 700ms |
| Mobile nav | button | overlay panel enters from top | 300ms, closes on Escape and destination click |
