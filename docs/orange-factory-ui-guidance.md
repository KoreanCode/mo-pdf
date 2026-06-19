# O'range Factory UI Guidance

## Context and goals

This PDF utility must feel like an O'range Factory content tool: clean, functional, implementation-focused, and keyboard-first. The UI must preserve the PDF upload, region selection, and download workflow while using token-driven styling.

## Design tokens and foundations

- Typography must use `--font-family-stack` with Pretendard Variable first and system fallbacks after it.
- Body text must use `--font-size-lg`, base weight `400`, and the base line-height token.
- Component copy should use `--font-size-sm`, `--font-size-md`, `--font-size-lg`, `--font-size-2xl`, and `--font-size-3xl` only.
- Component spacing must use `--space-1` through `--space-8`.
- Component radius must use `--radius-xs`, `--radius-sm`, or `--radius-md`.
- Component styling must consume semantic tokens such as `--semantic-page-bg`, `--semantic-page-text`, `--semantic-accent`, `--semantic-surface`, and `--semantic-border`.
- Component rules must not use one-off hex values outside foundation token definitions.

## Component-level rules

### Navigation

- Navigation must contain the product identity, one primary route back to the app, and one contextual action.
- Navigation links must define default, hover, focus-visible, active, disabled, loading, and error-compatible states through semantic tokens.
- Navigation should remain a single row on desktop and stack on small screens.
- Keyboard users must be able to tab to every navigation control.

### Buttons

- Buttons must use `.button` plus a variant class: `.button-primary`, `.button-secondary`, or `.button-quiet`.
- Buttons must define default, hover, focus-visible, active, disabled, loading, and error states.
- Button labels must describe the action, such as `편집 시작` or `선택 영역 블러 PDF 다운로드`.
- Buttons should fill available width only on narrow screens or when the container requires it.
- Touch targets must be at least 44px high.

### Fields

- File and number fields must use tokenized spacing, border, radius, typography, and focus-visible states.
- Fields must define default, hover, focus-visible, active, disabled, loading, and error states.
- Invalid fields must use `aria-invalid="true"` or native invalid state.
- Long filenames must wrap without breaking the tool panel layout.

### Cards and panels

- Cards must be used only for functional groups: upload panel, settings panel, and page previews.
- Page cards must use compact density because the page can contain many previews.
- Known density expectations are cards 60, links 16, buttons 11, and navigation 3; component rules must stay compact enough for those densities.
- Cards must define default, hover, focus-within, disabled, loading, and error-compatible states.
- Long page content must scroll naturally in the document rather than inside nested cards.

### Region editor

- Region selection must support pointer drag, touch drag, and keyboard operation.
- Keyboard users must be able to add a region with Enter or Space, move it with arrow keys, resize it with Shift plus arrow keys, and delete it with Delete or Backspace.
- Region overlays must use accent tokens and must remain visible on light PDF previews.
- Empty state must disable download, undo, and clear actions until at least one valid region exists.

## Accessibility requirements and testable acceptance criteria

- Every interactive control must be reachable with Tab.
- Every focused interactive control must show a visible focus indicator.
- All text and controls must meet WCAG 2.2 AA contrast against their background.
- Buttons must have descriptive labels that pass a screen-reader name check.
- Status messages must use `role="alert"` for errors and `role="status"` for non-error notices.
- Region count must use `aria-live="polite"` so assistive tech receives updates.
- Keyboard region creation, movement, resizing, and deletion must work without pointer input.
- Reduced-motion users must not receive non-essential animated transitions.

## Content and tone standards with examples

- Copy must be concise, confident, and implementation-focused.
- Primary actions must describe outcomes.
- Good: `편집 시작`, `선택 영역 블러 PDF 다운로드`, `새 PDF 업로드`.
- Avoid: `확인`, `처리`, `시작하기` when the target action is ambiguous.
- Error text must state the issue and the next recoverable action where possible.

## Anti-patterns and prohibited implementations

- Do not add low-contrast muted text on black surfaces.
- Do not hide focus indicators.
- Do not introduce one-off spacing, font sizes, or colors for local fixes.
- Do not use nested cards for page sections.
- Do not ship pointer-only editor behavior.
- Do not use ambiguous button labels.
- Do not add decorative gradients or unrelated visual assets.

## QA checklist

- [ ] Upload screen uses O'range Factory tokens and semantic CSS variables.
- [ ] Editor screen uses compact panels and page previews without nested cards.
- [ ] Buttons show default, hover, focus-visible, active, disabled, loading, and error-compatible states.
- [ ] Inputs show default, hover, focus-visible, active, disabled, loading, and error states.
- [ ] Region editor works with pointer, touch, and keyboard.
- [ ] Download is disabled when no region is selected.
- [ ] Long filenames wrap inside the settings panel.
- [ ] Small screens stack navigation, settings, and pages without overlap.
- [ ] Status messages expose alert/status roles.
- [ ] Package ZIP includes this guidance document.
