# Design System

This document describes the visual and interaction conventions for the Weekly Growth Journal interface. The implementation source of truth for theme tokens is `frontend/src/styles.css`; shared controls live in `frontend/src/components/ui/`.

## Product feel

The interface should feel calm, private, and thoughtful. Weekly reflection is personal work, so keep screens focused and low-pressure. Use clear language, generous spacing, and a steady visual hierarchy. Avoid gamification, streak pressure, numerical growth scores, and busy dashboards; they are outside the initial product scope.

## Visual foundations

### Color

Use semantic theme tokens rather than hard-coded color values in route or component styles:

- `background` and `foreground` for the page canvas and default text.
- `card` and `card-foreground` for contained content.
- `primary` for the main action and important interactive elements.
- `secondary` and `muted` for supporting surfaces and low-emphasis information.
- `accent` sparingly to highlight a key moment or section label.
- `destructive` only for destructive actions and their feedback.
- `border`, `input`, and `ring` for control boundaries and focus treatment.
- `observation` / `observation-foreground` and `hypothesis` / `hypothesis-foreground` to distinguish evidence-based observations from interpretations.

The existing palette is warm off-white with deep green primary tones and a restrained warm accent. Preserve readable contrast in both light and dark themes. If a semantic color is needed, define it in both `:root` and `.dark`, then register it in `@theme inline`. Theme colors use `oklch()` as required by `styles.css`.

### Typography

- Use the existing sans-serif stack (`Figtree`, then system sans-serif) for body copy, form labels, navigation, and controls.
- Use the existing serif stack (`Fraunces`, then Georgia) for page headings and occasional reflective emphasis.
- Use semantic heading levels in document order. Do not choose heading tags only for their visual size.
- Keep paragraphs and labels direct and easy to scan; avoid long blocks of instructional copy inside the reflection flow.

### Shape, spacing, and elevation

- Use the shared radius tokens, based on the existing `0.75rem` base radius.
- Use rounded cards for grouped content, with borders and restrained soft shadows. Avoid stacking many nested cards.
- Keep a readable maximum content width and comfortable vertical spacing. On small screens, use a single column and let controls fill the available width.
- Group related actions together and make the primary action visually distinct from secondary actions.

## Page patterns

- **Home:** Put the current week's status and start/continue action first, followed by the current commitment and links to past reviews.
- **Reflection:** Keep the five prompts in a predictable order, with one clearly labeled text area per prompt. Free writing and AI follow-up questions are optional and visually separate from required reflection content.
- **Feedback report:** Group takeaways, strengths, challenges, and recurring patterns under clear headings. Show the supporting evidence with each insight. Label observations and hypotheses in text as well as color. Provide direct controls to accept, reject, or correct each interpretation.
- **History:** Present reviews in chronological order with the week and completion status easy to scan. Keep data deletion available but visually separated from routine navigation and require confirmation.
- **Empty and error states:** Explain what happened in plain language and offer the next useful action. Do not imply that the user's reflection was saved when the save failed.

## Components and interaction

- Reuse the existing Radix/shadcn-style components in `frontend/src/components/ui/` before creating a new control.
- Use the shared `Button` variants (`default`, `secondary`, `outline`, `ghost`, `link`, `destructive`) consistently. Reserve `default` for the main action on a screen.
- Inputs and text areas need persistent visible labels; placeholder text is an example, not a label.
- Every interactive control must be keyboard operable, have a visible focus state, and expose an accessible name. Preserve native button, link, input, and form semantics.
- Show loading and disabled states for asynchronous actions. Prevent duplicate submissions while saving or generating a report.
- Use confirmation for irreversible deletion. Do not place a destructive action beside the primary completion action without separation.
- Give success and failure feedback through the existing toast pattern, while keeping important persistent state visible on the page.

## Responsive and accessible behavior

- Design for narrow mobile widths first, then enhance spacing and layout at larger breakpoints.
- Avoid horizontal scrolling for the reflection, report, and history flows.
- Do not rely on color alone to communicate status, evidence type, errors, or completion state.
- Maintain sufficient text and control contrast, logical tab order, descriptive labels, and visible focus indicators.
- Respect reduced-motion preferences for any non-essential animation. Motion should never be needed to understand a state change.
- Keep touch targets comfortable on mobile and do not make small icon-only controls the only way to perform an action.

## Adding or changing styles

1. Check whether an existing semantic token or UI component already fits.
2. Prefer semantic utility classes such as `bg-card`, `text-muted-foreground`, `border-border`, and `focus-visible:ring-ring` over raw palette values.
3. If introducing a theme color, add light and dark values in `styles.css` and register the token in `@theme inline`.
4. Keep route-specific styling close to the route only when it cannot be expressed through shared tokens or components.
5. Review the affected screen at mobile and desktop widths, including keyboard focus, empty state, loading state, and error state where applicable.
