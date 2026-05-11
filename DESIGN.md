---
name: Phi AI Gateway
description: Dark-mode developer platform with indigo accent. Terminal-inspired, high-contrast, utilitarian.
colors:
  # ── Surface palette (darkest → lightest) ──
  surface: "#030712"
  surface-dim: "#030712"
  surface-bright: "#1f2937"
  surface-container-lowest: "#030712"
  surface-container-low: "#111827"
  surface-container: "#111827"
  surface-container-high: "#1f2937"
  surface-container-highest: "#374151"
  on-surface: "#f3f4f6"
  on-surface-variant: "#9ca3af"
  on-surface-muted: "#6b7280"
  inverse-surface: "#f3f4f6"
  inverse-on-surface: "#1f2937"
  outline: "#1f2937"
  outline-variant: "#374151"
  surface-tint: "#4f46e5"
  # ── Primary palette (indigo) ──
  primary: "#4f46e5"
  on-primary: "#ffffff"
  primary-container: "#312e81"
  on-primary-container: "#a5b4fc"
  primary-hover: "#6366f1"
  primary-fixed: "#eef2ff"
  primary-fixed-dim: "#c7d2fe"
  on-primary-fixed: "#1e1b4b"
  on-primary-fixed-variant: "#3730a3"
  # ── Full indigo scale ──
  indigo-50: "#eef2ff"
  indigo-100: "#e0e7ff"
  indigo-200: "#c7d2fe"
  indigo-300: "#a5b4fc"
  indigo-400: "#818cf8"
  indigo-500: "#6366f1"
  indigo-600: "#4f46e5"
  indigo-700: "#4338ca"
  indigo-800: "#3730a3"
  indigo-900: "#312e81"
  indigo-950: "#1e1b4b"
  # ── Accent: success ──
  success: "#4ade80"
  on-success: "#052e16"
  success-container: "#14532d"
  on-success-container: "#86efac"
  # ── Accent: error ──
  error: "#ef4444"
  on-error: "#ffffff"
  error-container: "#7f1d1d"
  on-error-container: "#fca5a5"
  # ── Accent: warning ──
  warning: "#fcd34d"
  on-warning: "#451a03"
  warning-container: "#78350f"
  on-warning-container: "#fde68a"
  # ── Neutral (gray) scale ──
  neutral-50: "#f9fafb"
  neutral-100: "#f3f4f6"
  neutral-200: "#e5e7eb"
  neutral-300: "#d1d5db"
  neutral-400: "#9ca3af"
  neutral-500: "#6b7280"
  neutral-600: "#4b5563"
  neutral-700: "#374151"
  neutral-800: "#1f2937"
  neutral-900: "#111827"
  neutral-950: "#030712"
  # ── Code / terminal ──
  terminal-text: "#4ade80"
  terminal-comment: "#6b7280"
typography:
  display:
    fontFamily: Inter
    fontSize: 72px
    fontWeight: "800"
    lineHeight: 1.1
    letterSpacing: -0.02em
  h1:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: "800"
    lineHeight: 1.1
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: "700"
    lineHeight: 1.2
  h3:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: "600"
    lineHeight: 1.4
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 1.6
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 1.6
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 1.5
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: "500"
    lineHeight: 1.4
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: "500"
    lineHeight: 1.3
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 1.3
  mono-md:
    fontFamily: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 1.6
  mono-sm:
    fontFamily: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 1.5
rounded:
  sm: 4px
  DEFAULT: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  2xl: 32px
  3xl: 40px
  4xl: 48px
  5xl: 64px
  6xl: 96px
  container-padding: 24px
  section-gap: 96px
  card-gap: 16px
  element-gap: 8px
shadows:
  sm: "0 1px 2px 0 rgba(0, 0, 0, 0.3)"
  md: "0 4px 6px -1px rgba(0, 0, 0, 0.4)"
  lg: "0 10px 15px -3px rgba(0, 0, 0, 0.5)"
  xl: "0 20px 25px -5px rgba(0, 0, 0, 0.6)"
  2xl: "0 25px 50px -12px rgba(0, 0, 0, 0.7)"
  phi-sm: "0 4px 6px -1px rgba(79, 70, 229, 0.25)"
  phi-lg: "0 10px 15px -3px rgba(79, 70, 229, 0.40)"
motion:
  duration-fast: 150ms
  duration-normal: 200ms
  duration-slow: 300ms
  easing-default: ease-in-out
components:
  card:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  card-hover:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline-variant}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-md}"
    rounded: "{rounded.DEFAULT}"
    padding: 8px 16px
    shadow: "{shadows.phi-sm}"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    shadow: "{shadows.phi-lg}"
  button-secondary:
    backgroundColor: transparent
    textColor: "{colors.on-surface-variant}"
    borderColor: "{colors.outline-variant}"
    typography: "{typography.label-md}"
    rounded: "{rounded.DEFAULT}"
    padding: 8px 16px
  button-secondary-hover:
    borderColor: "{colors.on-surface-muted}"
    textColor: "{colors.on-surface}"
  button-danger:
    backgroundColor: "#dc2626"
    textColor: "{colors.on-error}"
    typography: "{typography.label-md}"
    rounded: "{rounded.DEFAULT}"
    padding: 8px 16px
  button-danger-hover:
    backgroundColor: "#ef4444"
  input-field:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    typography: "{typography.body-md}"
    rounded: "{rounded.DEFAULT}"
    padding: 8px 12px
  input-field-focus:
    borderColor: "{colors.primary-hover}"
    ringColor: "{colors.primary-hover}"
    ringWidth: 1px
  badge-free:
    backgroundColor: "{colors.neutral-700}"
    textColor: "{colors.neutral-300}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    padding: 2px 8px
  badge-pro:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    padding: 2px 8px
  badge-team:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.on-warning-container}"
    typography: "{typography.caption}"
    rounded: "{rounded.full}"
    padding: 2px 8px
  stat-card:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
  stat-value:
    typography: "{typography.h2}"
    textColor: "{colors.on-surface}"
  stat-label:
    typography: "{typography.body-sm}"
    textColor: "{colors.on-surface-variant}"
  sidebar:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline}"
    width: 256px
  sidebar-link-active:
    backgroundColor: "{colors.surface-container-high}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.DEFAULT}"
  sidebar-link-default:
    backgroundColor: transparent
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.DEFAULT}"
  nav-bar:
    backgroundColor: "rgba(3, 7, 18, 0.9)"
    borderColor: "rgba(31, 41, 55, 0.5)"
    backdropBlur: 8px
  terminal-window:
    backgroundColor: "{colors.surface-container}"
    borderColor: "{colors.outline}"
    rounded: "{rounded.lg}"
  terminal-titlebar:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.outline}"
  terminal-text:
    typography: "{typography.mono-sm}"
    textColor: "{colors.terminal-text}"
  hero-gradient:
    backgroundGradient: "radial-gradient(ellipse at 50% 0%, #312e81 0%, transparent 60%)"
  heading-gradient:
    backgroundGradient: "linear-gradient(135deg, #818cf8, #6366f1)"
    backgroundClip: text
    textFillColor: transparent
---

# Phi AI Gateway — Design System

## Overview

Phi AI Gateway is a dark-mode developer platform for AI agent infrastructure. The visual identity is rooted in **utilitarian minimalism**: high-contrast text on near-black surfaces, with a single indigo accent driving all interactive elements. The aesthetic borrows from terminal interfaces and code editors — monospace typography for endpoints and API keys, green-on-black syntax highlighting for code blocks, and a color palette that stays out of the developer's way.

The emotional register is **professional, focused, and slightly futuristic**. It should feel like a well-designed CLI tool got a GUI — no gradients, no glassmorphism, no decorative flourishes. Every element earns its place.

The brand personality: **technical but not cold, capable but not boastful**. Think Stripe's documentation, not a consumer fintech app.

## Colors

The palette is built on a single accent color — **Indigo (#4f46e5)** — floating in a dark neutral ocean. This constraint is intentional: with only one accent, the hierarchy is unambiguous. If it's indigo, it's interactive. If it's gray, it's structural.

### Surface Hierarchy

The dark background is not a single flat color but a subtle progression of four gray stops that create depth without borders:

- **surface (#030712):** The deepest layer — the page background. Near-black with a hint of blue.
- **surface-container (#111827):** Cards, the sidebar, and any "raised" container. One step above the page.
- **surface-container-high (#1f2937):** Input fields, hover states, and active sidebar links. The "pressed closer to the user" layer.
- **outline (#1f2937):** Borders and dividers. Same value as container-high so borders are visible but not distracting.

### Semantic Roles

- **primary (#4f46e5):** The sole action color. Used on buttons, focus rings, links, badge-pro text, and nowhere else. Hover lightens to **primary-hover (#6366f1)**.
- **success (#4ade80):** Terminal green — used for code text, active status indicators, and the terminal window dots. Not used for buttons or alerts.
- **error (#ef4444):** Danger buttons, delete actions, and revoked status. Hover lightens to (#ef4444).
- **warning (#fcd34d):** Used only for the team-tier badge. Amber-on-dark for high visibility without competing with primary.

### In Code

- Background: `bg-gray-950`
- Cards / sidebar: `bg-gray-900`
- Inputs / hover states: `bg-gray-800`
- Primary buttons / CTAs: `bg-phi-600` → hover `bg-phi-500`
- Body text: `text-gray-100`
- Descriptions: `text-gray-400`
- Muted / captions: `text-gray-500`
- Borders: `border-gray-800` (default), `border-gray-700` (subtle)

## Typography

The system uses a single typeface: **Inter**. This was chosen for its excellent legibility at small sizes (critical for dashboards and code-heavy interfaces) and its neutral, unopinionated character — it does not impose a personality on the product.

### Scale

A 9-level type scale covers every use case from hero headlines to badge captions:

| Token | Size | Weight | Use |
|-------|------|--------|-----|
| `display` | 72px | 800 | Landing page hero (responsive: 48px on mobile) |
| `h1` | 48px | 800 | Page titles, section headlines |
| `h2` | 30px | 700 | Section headers, stat values |
| `h3` | 20px | 600 | Card titles, subsection headers |
| `body-lg` | 18px | 400 | Hero description text |
| `body-md` | 16px | 400 | Body copy, form labels |
| `body-sm` | 14px | 400 | Feature descriptions, list items |
| `label-md` | 14px | 500 | Button text, nav links, form labels |
| `label-sm` | 12px | 500 | Badge text |
| `caption` | 12px | 400 | Version numbers, legal text, metadata |
| `mono-md` | 14px | 400 | API endpoints, code blocks |
| `mono-sm` | 12px | 400 | Key prefixes (`phi-sk-...`), inline code |

### Rules

- **Headings use Inter Bold or Extrabold.** Tight line-height (1.1–1.2) for display and h1; relaxed slightly (1.4) for h3.
- **Body text uses Inter Regular.** Line-height of 1.5–1.6 for long-form readability.
- **Monospace is reserved for code, endpoints, and API keys.** Never use monospace for marketing copy or UI labels.
- **No uppercase for headings.** The system uses sentence case throughout.
- **The brand name "φ Gateway" uses the Greek phi character**, rendered in whatever weight the surrounding context demands.

## Layout & Spacing

The layout uses a **max-width container** model — content centers at `max-w-7xl` (1280px) on large screens, with generous horizontal padding (`24px` on mobile, `48px` on desktop). There is no CSS grid framework; the few multi-column layouts use Tailwind's grid or flex utilities directly.

### Spacing Scale

All spacing derives from a `4px` base unit. The most frequently used stops:

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Sidebar link gaps, badge padding |
| `sm` | 8px | Button internal padding, element gaps |
| `md` | 12px | Input padding, sidebar link padding |
| `lg` | 16px | Card grid gaps, nav link gaps |
| `xl` | 24px | Card internal padding, section horizontal padding |
| `3xl` | 40px | Section intro spacing |
| `6xl` | 96px | Section vertical separation |

### Rules

- **Cards:** 24px internal padding, 16px gap between cards in a grid.
- **Sections:** 96px vertical padding is the standard. Sections with a tinted background (`bg-gray-950/50`) alternate with pure `bg-gray-950` to create visual rhythm.
- **Sidebar:** Fixed width at 256px. The main content area fills remaining space with scroll.
- **Nav:** Sticky top, 16px horizontal padding, 16px vertical. Backdrop blur on scroll.

## Elevation & Depth

The system is deliberately **flat**. There are no shadows on cards, no layered z-indices. Depth is communicated through background color alone:

```
surface (page) → surface-container (card) → surface-container-high (input)
```

The only exceptions:
- **Hero section:** Uses a radial gradient (`#312e81` at 50% 0%, fading to transparent) to create a subtle glow behind the heading. This is the most decorative element in the entire system.
- **CTA buttons:** Use a colored box-shadow (`shadow-phi-600/25`, increasing to `/40` on hover) to suggest clickability. This is the one place shadow is used functionally.
- **Terminal window:** Uses `shadow-2xl` to mimic a floating terminal in documentation screenshots.

### Focus & Interaction

- Focus rings use `ring-1 ring-phi-500` — a single-pixel indigo outline. No offset, no animation.
- Hover transitions use `transition-colors` (200ms) — background colors shift, borders lighten. No scale transforms, no lift.
- The sticky nav uses `backdrop-blur` to remain legible over scrolled content.

## Shapes

Every interactive element uses **rounded corners** — the system has no sharp rectangles. The radius hierarchy:

| Token | Value | Applied to |
|-------|-------|-----------|
| `sm` | 4px | Inline code snippets |
| `DEFAULT` | 8px | Buttons, inputs, sidebar links |
| `lg` | 12px | Cards, hero CTA buttons, pricing cards |
| `full` | 9999px | Badges, numbered step indicators, feature icon containers |

### Rules

- **Cards:** Always `rounded-lg` (12px). The softer corner differentiates cards from the page background.
- **Buttons:** `rounded-lg` for standard; `rounded-xl` for hero CTAs to give them more physical presence.
- **Inputs:** `rounded-lg` to match button radius. The focus ring should not change the border radius.
- **Never use sharp corners (`rounded-none`).** If an element has a border, it has a radius.

## Components

### Buttons

Three variants, all sharing the same `rounded-lg` + `py-2 px-4` base:

- **primary:** Solid indigo (`bg-phi-600`) with white text. Has a subtle indigo glow (`shadow-phi-600/25`). Hover lightens to `bg-phi-500`.
- **secondary:** Transparent background with gray-300 text and a gray-600 border. Hover lightens the border and text toward white. Used for "Learn More" and "See How" CTAs.
- **danger:** Solid red-600. Used exclusively for destructive actions (revoke key, delete conversation). Hover lightens to red-500.

### Cards

Every card uses the same base: `bg-gray-900 border border-gray-800 rounded-xl p-6`. Feature cards add `hover:border-gray-700` for subtle interactivity. Pricing cards use `border-phi-700` (2px) for the "Popular" tier to make it stand out.

### Badges

Three tier badges, all `rounded-full text-xs font-medium`:

- **badge-free:** Gray bg (`#374151`), gray text (`#d1d5db`). Neutral, understated.
- **badge-pro:** Indigo bg (`#312e81`), indigo text (`#a5b4fc`). Uses the primary palette to signal upgrade.
- **badge-team:** Amber bg (`#78350f`), amber text (`#fde68a`). Warmer color to differentiate from pro.

### Stat Cards

A specialized card variant for the dashboard overview: centers content, displays a large bold number (`text-3xl font-bold text-white`) and a small gray label below (`text-sm text-gray-400`). Used for total requests, tokens, cost, and active keys.

### Sidebar

Dark (`bg-gray-900`) with a right border (`border-r border-gray-800`). Fixed at 256px wide. Links use `rounded-lg` with `px-3 py-2`. Active state: `bg-gray-800 text-white`. Default state: `text-gray-400` with hover to white. The brand lockup sits at the top with a bottom border separator.

### Terminal Window

A decorative component used in the landing page to show code examples. Dark background (`bg-gray-900`) with `rounded-xl` and `shadow-2xl`. The title bar has three colored dots (red, yellow, green) mimicking macOS window chrome. Code text is `font-mono text-green-400` on the near-black background.

## Do's and Don'ts

### Do
- Use the indigo accent **only** for interactive elements and the pro badge.
- Keep backgrounds near-black (`#030712`, `#111827`, `#1f2937`). Never introduce a light background.
- Use `text-gray-100` for all body copy; `text-gray-400` for descriptions; `text-gray-500` for the most subdued text.
- Give every section 96px of vertical breathing room.
- Use `rounded-lg` (12px) for all cards and `rounded-lg` (8px) for all buttons.
- Put API endpoints and key prefixes in `font-mono` at `text-sm`.

### Don't
- Do not use shadows for depth — use background color progression instead. The one exception is CTA button glow.
- Do not introduce a second accent color. Indigo is the only color that means "click me."
- Do not use uppercase text. Sentence case everywhere.
- Do not add gradients outside of the hero section and the brand heading gradient.
- Do not use rounded-sm (4px) for anything except inline code.
- Do not make the sidebar wider than 256px.
