# EchoMatrix Dashboard Design System

## Design pipeline

### Canva
Use Canva for:
- brand exploration;
- visual moodboards;
- dashboard concept boards;
- presentation-ready design references;
- typography and visual-direction experiments.

Canva outputs are references, not the implementation source of truth.

### Figma
Use Figma for:
- final desktop/mobile layouts;
- design tokens;
- component library;
- responsive behavior;
- loading/error/empty states;
- interaction prototypes;
- developer handoff.

Figma is the authoritative UI specification before frontend implementation.

## Product feel

EchoMatrix should feel like a serious financial intelligence command center: premium, technical, calm, information-dense without becoming cluttered, and clearly simulation-first.

Avoid anime/glitch styling, decorative noise, excessive gradients and fake terminal aesthetics.

## Core screens

1. **Command Center** — equity, cash, exposure, system status, current cycle and major decision.
2. **Market Intelligence** — asset cards, market state, research context and signal summaries.
3. **Decision Trace** — visual lifecycle from market observation through memory.
4. **AI Core** — model/provider status, reasoning summaries and confidence context.
5. **Risk** — risk decisions, constraints, rejected actions and explanations.
6. **Simulation** — simulated account, positions, fills, P/L and equity curve.
7. **Memory** — observations, decisions, outcomes and lessons.
8. **System Health** — service status, latency, dependency failures and readiness.
9. **Wealth Movement** — long-term goals and capital-preservation milestones.
10. **Settings** — provider configuration and system preferences; secrets are never displayed after storage.

## Component foundations

- responsive shell;
- sidebar/bottom navigation;
- asset card;
- KPI card;
- status badge;
- decision card;
- lifecycle timeline;
- chart container;
- position row;
- memory entry;
- service-health row;
- modal/drawer;
- confirmation state;
- error boundary;
- skeleton/loading state.

## Interaction rules

- Every decision shown in the UI should be traceable to a workflow/cycle ID.
- The UI must distinguish AI opinion from risk approval.
- A simulated action must be visually labelled as simulation.
- Errors should identify the failing service rather than display generic failure text.
- The dashboard must never invent state when the backend is unavailable.
- Start/stop controls affect simulation lifecycle only in this phase.

## Responsive strategy

Desktop is the primary command-center experience. Mobile is a companion control/monitoring experience. Asset cards may use horizontal swipe on mobile, while tables become stacked cards.

## Accessibility

Target WCAG 2.2 AA practices: keyboard navigation, readable contrast, visible focus states, semantic controls, reduced-motion support and non-color-only status communication.
