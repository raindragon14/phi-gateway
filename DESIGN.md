---
# Design tokens for Phi AI Gateway
# Follows design.md spec: https://github.com/google-labs-code/design.md
schema: design.md/v1

tokens:
  colors:
    - name: background-primary
      value: "#000000"
      description: True black main page background for maximum contrast and snappy rendering
    - name: background-surface
      value: "#0a0a0a"
      description: Barely lifted background for cards and main sections
    - name: background-elevated
      value: "#121212"
      description: Inset elements, terminal body, and high-level structural components
    - name: background-terminal-bar
      value: "#1a1a1a"
      description: Terminal window title bar, ultra-minimal
    - name: border-default
      value: "#222222"
      description: Razor-thin, subtle border for structure without visual weight
    - name: border-hover
      value: "#333333"
      description: Border color on hover for interactive elements
    - name: text-primary
      value: "#ededed"
      description: Crisp, high-contrast primary text
    - name: text-heading
      value: "#ffffff"
      description: Pure white for critical headings to establish hierarchy
    - name: text-secondary
      value: "#a1a1aa"
      description: Classic technical gray for descriptions and subtitles
    - name: text-muted
      value: "#71717a"
      description: Muted text for data points and passive UI elements
    - name: text-subtle
      value: "#3f3f46"
      description: Extremely recessive text for footers and structural markers
    - name: accent-primary
      value: "#ededed"
      description: Primary accent is now high-contrast monochrome for a classic, serious look
    - name: accent-primary-hover
      value: "#ffffff"
      description: Accent hover state brightens slightly
    - name: accent-soft
      value: "#2d3748"
      description: A subtle slate-gray/blue for quiet highlights, avoiding "catchy" neons
    - name: terminal-dim
      value: "#52525b"
      description: Dim prefix in terminal ($)
    - name: terminal-command
      value: "#e4e4e7"
      description: Command text in terminal - stark and clear
    - name: terminal-output
      value: "#a1a1aa"
      description: Output text in terminal
    - name: terminal-body-bg
      value: "#050505"
      description: Deepest black/gray for terminal content
    - name: terminal-border
      value: "#1f1f1f"
      description: Sharp, minimal terminal window border
  typography:
    - name: font-primary
      value: "'Geist', 'Helvetica Neue', -apple-system, sans-serif"
      description: Classic, highly legible, professional sans-serif
    - name: font-mono
      value: "'Geist Mono', 'SF Mono', 'JetBrains Mono', monospace"
      description: Clinical, perfectly aligned monospace font for technical data
    - name: heading-hero-size
      value: "32px"
      description: Hero heading font size - scaled down for elegance
    - name: heading-hero-weight
      value: "500"
      description: Medium weight instead of ultra-bold. Feels more classic and confident.
    - name: heading-hero-spacing
      value: "-0.02em"
      description: Tight letter spacing for precision
    - name: heading-section-size
      value: "14px"
      description: Section headings are small, acting as functional labels
    - name: heading-section-weight
      value: "600"
      description: Semibold for clear, readable hierarchy
    - name: card-title-size
      value: "13px"
      description: Card title size
    - name: card-title-weight
      value: "500"
      description: Card title weight - kept light and snappy
    - name: body-size
      value: "13px"
      description: Slightly smaller body text for higher information density
    - name: body-small-size
      value: "11px"
      description: Microcopy and technical labels
    - name: label-size
      value: "10px"
      description: Utility labels, uppercase tracking
    - name: mono-size
      value: "12px"
      description: Monospace font size
    - name: line-height-body
      value: "1.6"
      description: Generous line height for reading technical documentation
    - name: line-height-mono
      value: "1.5"
      description: Tighter line height for code blocks to group logic
  spacing:
    - name: page-padding
      value: "32px 40px"
      description: Generous outer padding framing the UI
    - name: section-gap
      value: "1px"
      description: Used 1px gaps for grid layouts to create "hairline" dividers between flush cards
    - name: card-padding
      value: "20px"
      description: Ample breathing room inside cards
    - name: section-padding
      value: "24px"
      description: Internal padding for structural containers
    - name: header-margin-bottom
      value: "40px"
      description: Distinct separation between header and content
    - name: button-padding
      value: "6px 14px"
      description: Tighter, sharper buttons
  radii:
    - name: card-radius
      value: "4px"
      description: Sharp, classic technical corners (reduced from 10px)
    - name: button-radius
      value: "2px"
      description: Near-square buttons for a utilitarian feel
    - name: chip-radius
      value: "2px"
      description: Utilitarian badges and endpoint markers
    - name: avatar-radius
      value: "50%"
      description: Circular elements retained only for literal avatars
    - name: terminal-radius
      value: "4px"
      description: Subtle rounding for the terminal window, mimicking lightweight window managers
  borders:
    - name: border-width
      value: "1px"
      description: Hairline precision everywhere
    - name: border-style
      value: "solid"
      description: Standard border style
  shadows:
    - name: none
      value: "none"
      description: Strict flat design. Depth is established purely through layout and 1px borders.
  motion:
    - name: transition-instant
      value: "50ms"
      description: Nearly instant feedback for extreme snappiness
    - name: transition-fast
      value: "120ms"
      description: Very quick transitions for hover states
    - name: easing-snappy
      value: "cubic-bezier(0.2, 0, 0, 1)"
      description: Fast-out, slow-in easing that feels lightweight and highly responsive
  breakpoints:
    - name: mobile-max
      value: "720px"
      description: Collapse to single column
  layout:
    - name: page-max-width
      value: "960px"
      description: Slightly wider to accommodate dense technical data without feeling cramped
    - name: grid-columns
      value: "4"
      description: High-density layout capability
---

# Phi AI Gateway Design System

## Overview

Phi AI Gateway employs an ultra-minimalist, high-performance aesthetic designed for professional engineers. It rejects "trendy" SaaS design patterns (like heavy drop shadows, neon gradients, or overly bubbly border radii) in favor of a classic, utilitarian interface. The design feels inherently *fast*, prioritizing high information density, razor-sharp edges, and clinical typography.

## Visual Identity

### Absolute Flat & True Black

The interface uses pure black (`#000000`) for the root background. This creates infinite contrast on high-end displays and gives the app an incredibly lightweight, snappy feel. Cards and panels use extremely subtle shifts in gray (`#0a0a0a` to `#121212`) separated solely by 1px hairline borders (`#222222`). There are absolutely no shadows, glows, or blurs.

### Monochrome Over Color

We avoid "catchy" or loud accent colors. Instead, the UI relies heavily on a beautifully calibrated grayscale. "Accent" states are achieved by stepping up the contrast to pure white (`#ffffff`). The only colors introduced should be strictly functional (e.g., standard red/yellow/green for status indicators or standard terminal output syntax). This makes the platform feel like serious infrastructure, not a toy.

### Typography: Classic & Confident

- **Sans-Serif:** We use highly legible, classic neo-grotesque fonts (`Geist`, `Helvetica Neue`). Weights are kept to a confident Medium (`500`) rather than shouting with Extra Bold (`800`). Font sizes are slightly reduced to allow for greater data density.
- **Monospace Focus:** `Geist Mono` or `SF Mono` takes center stage. Because the surrounding UI is so quiet, code snippets, endpoint paths, and terminal outputs naturally draw the eye.

### Sharp Geometry

A hallmark of "classic tech" design is sharp corners. Border radii are strictly limited to `2px` or `4px`. This prevents the UI from feeling soft or playful, reinforcing a structured, architectural feel.

### Snappy Motion

Motion is near-instantaneous. Standard transitions happen in `50ms` to `120ms` using an aggressive cubic-bezier curve. When a developer hovers or clicks, the interface responds as fast as a native CLI tool.
