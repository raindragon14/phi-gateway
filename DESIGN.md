---
# Design tokens for Phi AI Gateway
# Follows design.md spec: https://github.com/google-labs-code/design.md
schema: design.md/v1

tokens:
  colors:
    - name: background-primary
      value: "#0a0a0f"
      description: Main page background
    - name: background-surface
      value: "#12121a"
      description: Card, section, and interactive element backgrounds
    - name: background-elevated
      value: "#0e1015"
      description: Terminal body, inset elements, plan cards
    - name: background-terminal-bar
      value: "#161820"
      description: Terminal window title bar
    - name: border-default
      value: "#1a1a2e"
      description: Standard border for cards, sections, dividers
    - name: border-hover
      value: "#2a2a3e"
      description: Border color on hover for interactive cards
    - name: text-primary
      value: "#e1e1e8"
      description: Primary body text
    - name: text-heading
      value: "#ffffff"
      description: Headings and emphasized text
    - name: text-secondary
      value: "#888888"
      description: Secondary descriptions, hero subtitle
    - name: text-muted
      value: "#666666"
      description: Card body text, muted labels
    - name: text-subtle
      value: "#444444"
      description: Footer text, very subtle labels
    - name: accent-primary
      value: "#6366f1"
      description: Primary accent (indigo-500). Used for headings emphasis, buttons, icons, links
    - name: accent-primary-hover
      value: "#5558e0"
      description: Accent on hover for buttons
    - name: accent-soft
      value: "#a5b4fc"
      description: Softer accent for card titles and subtle highlights
    - name: terminal-dim
      value: "#555555"
      description: Dim prefix in terminal ($)
    - name: terminal-command
      value: "#6366f1"
      description: Command text in terminal
    - name: terminal-output
      value: "#666666"
      description: Output text in terminal
    - name: terminal-body-bg
      value: "#0e1015"
      description: Terminal content background
    - name: terminal-border
      value: "#1e2030"
      description: Terminal window border
  typography:
    - name: font-primary
      value: "'Inter', system-ui, -apple-system, sans-serif"
      description: Primary font for all UI text
    - name: font-mono
      value: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace"
      description: Monospace font for terminal, code, and endpoint paths
    - name: heading-hero-size
      value: "38px"
      description: Hero heading font size
    - name: heading-hero-weight
      value: "800"
      description: Hero heading font weight
    - name: heading-hero-spacing
      value: "-0.5px"
      description: Hero heading letter spacing
    - name: heading-section-size
      value: "15px"
      description: Section heading size
    - name: heading-section-weight
      value: "700"
      description: Section heading weight
    - name: card-title-size
      value: "13px"
      description: Card title size
    - name: card-title-weight
      value: "600"
      description: Card title weight
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
      value: "1.5"
      description: Default line height
    - name: line-height-mono
      value: "1.65"
      description: Monospace line height for terminal
  spacing:
    - name: page-padding
      value: "24px 28px"
      description: Outer page padding
    - name: section-gap
      value: "10px"
      description: Gap between grid items, sections, and cards
    - name: card-padding
      value: "16px"
      description: Standard card internal padding
    - name: section-padding
      value: "18px"
      description: Internal padding for larger section containers
    - name: header-margin-bottom
      value: "28px"
      description: Space below header
    - name: hero-margin-bottom
      value: "28px"
      description: Space below hero section
    - name: grid-margin-bottom
      value: "24px"
      description: Space below feature grid
    - name: button-padding
      value: "8px 18px"
      description: Button internal padding
  radii:
    - name: card-radius
      value: "10px"
      description: Standard border radius for cards, sections, terminal
    - name: button-radius
      value: "7px"
      description: Button border radius
    - name: chip-radius
      value: "5px"
      description: Smaller radius for endpoint chips and badges
    - name: avatar-radius
      value: "50%"
      description: Circular elements like step numbers and favicon
    - name: favicon-radius
      value: "6px"
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
      description: No shadows - flat design
  motion:
    - name: transition-fast
      value: "0.15s"
      description: Quick transitions for buttons and hover states
    - name: transition-standard
      value: "0.2s"
      description: Standard transitions for cards and interactive elements
    - name: easing-default
      value: "ease"
      description: Default easing function (implicit via CSS transition)
  breakpoints:
    - name: mobile-max
      value: "720px"
      description: Breakpoint where layouts collapse to single-column
  layout:
    - name: page-max-width
      value: "880px"
      description: Maximum content width
    - name: grid-columns
      value: "4"
      description: Number of columns in desktop feature grid
    - name: terminal-min-width
      value: "340px"
      description: Minimum width of terminal panel in hero
---

# Phi AI Gateway Design System

## Overview

Phi AI Gateway uses a dark, minimalistic aesthetic optimized for developer audiences. The design prioritizes readability, information density, and a terminal-inspired feel that resonates with the target audience of AI developers and indie hackers.

## Visual Identity

### Dark Mode by Default

The interface uses a deep near-black background (`#0a0a0f`) that reduces eye strain and creates a focused environment. Cards and interactive surfaces float slightly above the background at `#12121a`, creating subtle depth without shadows. This flat-dark approach is common in developer tools like VS Code and linear.app.

### Indigo as Signal

A single accent color, indigo-500 (`#6366f1`), is used sparingly for interactive elements, key headings, and the phi brand. Everything else uses a monochromatic gray scale from `#e1e1e8` (primary text) down to `#444` (footer). This restraint prevents visual noise and creates clear hierarchy.

### Terminal as Hero

The hero section features a macOS-style terminal window with red/yellow/green dots, monospace font, and colored command output. This immediately signals to developers: "this is a tool for you." The terminal acts as both a visual hook and a quick-start demonstration.

### Typography

- **Inter** at sizes 11-38px handles all UI text. Its clean, neutral character works well at both display and micro sizes.
- **JetBrains Mono** is used exclusively in the terminal and endpoint paths, creating clear separation between code and prose.
- No italic, no serif, no decorative fonts. The palette is deliberately small.

### Layout Strategy

The page fits in a single viewport on a 900px-tall screen. Four-column feature grids collapse to two columns on mobile. The hero uses a side-by-side layout (text on left, terminal on right) that stacks vertically on narrow screens. No scroll-triggering or long-form content - everything is above the fold.

### Buttons and Links

Primary buttons use the solid indigo fill. Secondary buttons use a bordered transparent background. All external links (GitHub, Docs) open in new tabs to keep the landing page as a persistent reference point. Navigation links are subtle (`#777`) to avoid competing with the hero.

### No Gradients, No Shadows

The design is flat. Depth is communicated through background layering alone (page -> card -> inset). No box-shadows, no gradients, no blurs. This keeps the CSS minimal and the visual clean.

### Responsive Behavior

At 720px and below, layouts collapse: hero stacks, grids go to 2 columns, terminal loses min-width, font sizes reduce slightly. The design works on phones but is optimized for desktop where developers typically evaluate tools.
