# MALIK SKILLS design system

## Direction

The visual language is editorial and technical: generous rounded cards, measured connector lines, a compact monogram, one strong information hierarchy and concise factual copy. It takes functional inspiration from a professional GitHub profile system but is an original implementation and does not reuse the reference repository's source or artwork.

## Palette

| Token | Light | Dark | Role |
| --- | --- | --- | --- |
| Background | `#F5F8F4` | `#0A1712` | Artboard surface |
| Surface | `#FFFFFF` | `#11241B` | Panels |
| Raised | `#E1EEE6` | `#193426` | Tracks and subdued surfaces |
| Border | `#C6D9CC` | `#2B4A38` | Grouping only |
| Foreground | `#10261A` | `#F3F7F4` | Primary text |
| Muted | `#466254` | `#A8BBB0` | Supporting text |
| Emerald accent | `#167A46` | `#45C47A` | Information-bearing emphasis |
| Forest secondary | `#0F6237` | `#1C8C58` | Secondary emphasis |
| Mint | `#76C99B` | `#9BE7BE` | Small connection details |

The palette avoids a fluorescent dominant green. Primary foreground/background combinations were selected for readable contrast; low-contrast borders are decorative grouping elements and never carry essential text alone.

## Type, geometry and components

SVGs use `Arial, Helvetica, sans-serif`, so rendering has no remote font dependency. Desktop display text is 62–96 units, headings 23–39, body 20–27 and metadata 17–23. Mobile display text is 40–48, headings 21–28 and metadata 16–21.

The desktop grid is 1200 units wide with 56-unit outer margins; mobile is 480 units wide with 28-unit margins. Cards use 14–24 unit radii, 2-unit grouping strokes and 2.5–7 unit signal strokes. The core components are:

- an asymmetric dark hero with an M monogram and connected system nodes;
- project cards with words and conceptual diagrams in one composition;
- technology cards carrying candid state labels rather than progress bars;
- an open six-step timeline;
- a data dashboard whose scale is explicitly repository counts.

## Responsive and theme behavior

Each README image fills its container. `<picture>` chooses a 480-unit mobile composition at a maximum viewport width of 760 px, then applies dark-theme variants using `prefers-color-scheme`. The contribution picture puts `prefers-reduced-motion` sources before the animated sources, so users who request reduced motion get a static calendar. GitHub renders the selected image source; no client JavaScript or custom README CSS is assumed.

Project artwork is explicitly labelled as a concept diagram, never a product screenshot. Technology cards explain scope through direct text, and backend remains visually central without claiming seniority or equal mastery across the stack.
