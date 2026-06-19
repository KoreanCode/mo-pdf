# Brand Intro Image Asset Plan

## UI direction

The upload screen is a brand-introduction first screen for Orange Factory's local document blur tool. It should introduce the brand and the job of the app before the user uploads a file, while keeping the upload action visible in the first viewport.

## Substrate decision

- Product archetype: webpage entry screen for a local document editing app
- Primary interaction: choose or drop a PDF/image file
- Object count / data scale: one upload control, one brand scene, three workflow cues
- Precision requirements: visual trust and clear upload affordance; no pixel-level editor surface on the first screen
- Accessibility requirements: semantic DOM controls, visible focus, descriptive button labels, keyboard-reachable upload
- Responsive constraints: single-column stacking on small screens with upload before decorative media
- Recommended substrate: DOM/CSS layout with one generated bitmap hero asset
- Rejected alternatives: canvas scene, SVG-only mockup, multiple decorative illustrations
- Reason: the first screen needs brand context and trust, while the editor screen already handles precision work

## Asset inventory

### New generated asset

- File: `static/brand-hero-workbench.png`
- Role: first-screen hero image
- Use: placed inside the brand scene panel and cropped responsively with CSS
- Content: warm document workbench showing PDF pages, privacy blur masks, and Orange Factory orange/green accents
- Must avoid: readable personal data, real company marks, UI text, watermark, dense fake controls, dark stock-photo mood

### Existing reused assets

- File: `static/simbol_2.png`
- Role: compact brand mascot mark in nav and small scene signature
- Use rule: keep secondary so the app still feels like a document tool, not a mascot page

- File: `static/white-logo.png`
- Role: low-opacity background watermark only
- Use rule: decorative only; do not make it the main readable brand lockup

## Image generation prompt

Use case: productivity-visual
Asset type: website hero image for a local PDF privacy blur tool
Primary request: create a polished Orange Factory document workbench scene that communicates uploading a PDF, selecting sensitive regions, and exporting a blurred copy.
Scene/backdrop: warm clean desk or studio workbench with a laptop/tablet-like preview surface and printed document pages.
Subject: PDF pages with orange selection rectangles and soft privacy blur strips over data-like rows, plus subtle green completion accents.
Style/medium: high-quality 3D editorial illustration with practical UI/product detail, not a flat icon set.
Composition/framing: wide landscape hero image, strong subject in the center and right, enough calm negative space for web layout cropping.
Lighting/mood: bright, trustworthy, warm, clean, useful.
Color palette: Orange Factory orange, fresh green accents, cream paper, warm neutral background, dark ink details.
Text: no text.
Constraints: no logos, no readable personal data, no brand names, no watermark, no extra UI copy, no dark or blurred stock-photo look.
