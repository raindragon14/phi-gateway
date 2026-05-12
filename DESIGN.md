---
# Design tokens for Phi AI Gateway
# Follows design.md spec: https://github.com/google-labs-code/design.md
schema: design.md/v1

tokens:
  colors:
    - name: background-primary
      value: "#ffffff"
      description: Main page background (crisp white)
    - name: background-surface
      value: "#f8f9fa"
      description: Card, section, and interactive element backgrounds
    - name: background-elevated
      value: "#f1f3f5"
      description: Terminal body, inset elements, plan cards
    - name: background-terminal-bar
      value: "#e9ecef"
      description: Terminal window title bar
    - name: border-default
      value: "#dee2e6"
      description: Standard border for cards, sections, dividers
    - name: border-hover
      value: "#adb5bd"
      description: Border color on hover for interactive elements
    - name: text-primary
      value: "#212529"
      description: Primary body text (high contrast dark slate)
    - name: text-heading
      value: "#111111"
      description: Headings and emphasized text
    - name: text-secondary
      value: "#495057"
      description: Secondary descriptions, hero subtitle
    - name: text-muted
      value: "#868e96"
      description: Card body text, muted labels
    - name: text-subtle
      value: "#ced4da"
      description: Footer text, very subtle labels
    - name: accent-primary
      value: "#0f52ba"
      description: Primary accent (Sapphire/Engineering Blue)
    - name: accent-primary-hover
      value: "#0b3d8c"
      description: Accent on hover for buttons
    - name: accent-soft
      value: "#e7f0ff"
      description: Softer accent for subtle highlights
    - name: terminal-dim
      value: "#adb5bd"
      description: Dim prefix in terminal ($)
    - name: terminal-command
      value: "#0f52ba"
      description: Command text in terminal
    - name: terminal-output
      value: "#495057"
      description: Output text in terminal
    - name: terminal-body-bg
      value: "#f8f9fa"
      description: Terminal content background
    - name: terminal-border
      value: "#dee2e6"
      description: Terminal window border
  typography:
    - name: font-primary
      value: "'IBM Plex Sans', 'Helvetica Neue', 'Inter', system-ui, sans-serif"
      description: Primary font. Neo-grotesque, mechanical, highly legible.
    - name: font-mono
      value: "'IBM Plex Mono', 'SF Mono', 'Menlo', 'Consolas', monospace"
      description: Monospace font for terminal, code, and endpoint paths.
    - name: heading-hero-size
      value: "32px"
      description: Hero heading font size
    - name: heading-hero-weight
      value: "600"
      description: Hero heading font weight
    - name: heading-hero-spacing
      value: "-0.2px"
      description: Hero heading letter spacing
    - name: heading-section-size
      value: "16px"
      description: Section heading size
    - name: heading-section-weight
      value: "600"
      description: Section heading weight
    - name: card-title-size
      value: "14px"
      description: Card title size
    - name: card-title-weight
      value: "500"
      description: Card title weight (medium, not bold)
    - name: body-size
      value: "14px"
      description: Standard body text size
    - name: body-small-size
      value: "12px"
      description: Smaller body text for cards and descriptions
    - name: label-size
      value: "11px"
      description: Small labels, plan text, step descriptions
    - name: mono-size
      value: "12px"
      description: Monospace font size for terminal and endpoint paths
    - name: line-height-body
      value: "1.6"
      description: Default line height
    - name: line-height-mono
      value: "1.5"
      description: Monospace line height for terminal
  spacing:
    - name: page-padding
      value: "32px 40px"
      description: Outer page padding
    - name: section-gap
      value: "16px"
      description: Gap between grid items, sections, and cards
    - name: card-padding
      value: "20px"
      description: Standard card internal padding
    - name: section-padding
      value: "24px"
      description: Internal padding for larger section containers
    - name: header-margin-bottom
      value: "32px"
      description: Space below header
    - name: hero-margin-bottom
      value: "40px"
      description: Space below hero section
    - name: grid-margin-bottom
      value: "32px"
      description: Space below feature grid
    - name: button-padding
      value: "6px 16px"
      description: Button internal padding
  radii:
    - name: card-radius
      value: "4px"
      description: Sharp, structural border radius
    - name: button-radius
      value: "3px"
      description: Button border radius
    - name: chip-radius
      value: "2px"
      description: Radius for endpoint chips and badges
    - name: avatar-radius
      value: "50%"
      description: Circular elements like step numbers
    - name: favicon-radius
      value: "4px"
      description: Favicon outer rect radius
  borders:
    - name: border-width
      value: "1px"
      description: Standard border width
    - name: border-style
      value: "solid"
      description: Standard border style
  shadows:
    - name: none
      value: "none"
      description: No shadows - flat structural design
  motion:
    - name: transition-fast
      value: "0.1s"
      description: Near-instant transitions
    - name: transition-standard
      value: "0.15s"
      description: Standard transitions
    - name: easing-default
      value: "linear"
      description: Linear easing for mechanical feel
  breakpoints:
    - name: mobile-max
      value: "720px"
      description: Breakpoint where layouts collapse to single-column
  layout:
    - name: page-max-width
      value: "960px"
      description: Maximum content width
    - name: grid-columns
      value: "4"
      description: Number of columns in desktop feature grid
    - name: terminal-min-width
      value: "380px"
      description: Minimum width of terminal panel in hero
---

# Phi AI Gateway Design System

## Overview

Phi AI Gateway uses a light, highly structural, and classic engineering aesthetic optimized for professional developers and enterprise environments. The design avoids consumer trends in favor of extreme legibility, data density, and quiet confidence.

## Visual Identity

### The "Clean Tech" Light Mode

The interface is anchored by crisp white (`#ffffff`) offset by slate grays (`#f8f9fa` to `#212529`). This high-contrast, low-saturation approach mimics classic technical documentation and enterprise IDEs. Depth is completely flat; we rely on sharp 1px borders (`#dee2e6`) to separate spatial zones, creating a precise, wireframe-like layout.

### Engineering Blue as Signal

A classic Sapphire/Engineering Blue (`#0f52ba`) serves as the sole accent color. It is used with extreme restraint: only for active states, primary actions, and syntax highlighting. It commands attention without feeling trendy or playful.

### The Utility Terminal

The hero terminal is a utilitarian, light-themed console window with stark borders and subdued syntax colors. It communicates pure functionality over visual flair, treating code as the primary interface.

### Structural Typography

- **IBM Plex Sans** is the primary typeface. Its neo-grotesque, mechanical proportions bridge classic print and modern screen design. It feels inherently technical and serious.
- **IBM Plex Mono** handles all code, endpoints, and terminal blocks. Its distinct italics and sharp structural features make it highly legible for technical reading.
- **Weights and Sizing**: Maximum hero size is a restrained 32px. We use Medium (500) and Semi-Bold (600) for emphasis, avoiding heavy Bold (800) weights which read as loud.

### Layout Strategy

Grid-driven and rigidly structured. A wider 960px max-width accommodates dense technical information comfortably. Margins and paddings are slightly increased to give typography room to breathe while keeping everything above the fold.

### Borders over Backgrounds, Zero-Shadow Policy

No drop-shadows, blurs, or gradients. Interactive states use near-instant (0.1s) background color shifts and border darkening. Border radii are aggressively reduced to 2-4px, giving sharp, precise corners that communicate precision and reliability.
