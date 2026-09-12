# EchoMatrix Brain Contract

## Purpose

EchoMatrix is built as an AI financial and wealth operating system. The first implementation target is a simulation-first intelligence platform. The brain must become coherent and testable before the dashboard becomes the primary product surface.

## Canonical lifecycle

```text
MARKET DATA
    ↓
RESEARCH / CONTEXT
    ↓
STRATEGY INTELLIGENCE
    ↓
AI ANALYSIS (Gemini / Groq)
    ↓
RISK DECISION
    ↓
CAPITAL ALLOCATION
    ↓
ORCHESTRATION DECISION
    ↓
SIMULATION
    ↓
PORTFOLIO STATE
    ↓
OUTCOME
    ↓
INTELLIGENCE MEMORY
    └──────────────→ future analysis
```

Every cycle should have a correlation/workflow identifier so events from every service can be reconstructed as one decision trace.

## Service responsibilities

- **market-data**: normalized market observations; no trading decisions.
- **research-intelligence**: contextual research inputs and evidence; no execution authority.
- **strategy-engine**: candidate strategy/signal generation; no execution authority.
- **ai-core**: model reasoning through the configured Gemini/Groq providers; no execution authority.
- **risk-engine**: independent risk gate. A rejected decision cannot be executed or simulated as approved.
- **capital-allocation-engine**: determines bounded simulated capital allocation after risk approval.
- **orchestration-engine**: converts approved decisions into the next lifecycle action.
- **simulation-engine**: simulation-only fills and account state; never sends broker/exchange orders.
- **portfolio-engine**: authoritative simulated positions, balances and equity state.
- **workflow-engine**: lifecycle/event trace.
- **persistence-layer**: durable-storage abstraction. The brain must not depend directly on a particular database implementation.
- **intelligence-memory**: stores observations, decisions, outcomes and lessons; hydrates on startup and mirrors records through persistence.
- **integration-pipeline**: canonical coordinator for the complete cycle.
- **api-gateway**: public nervous-system boundary for clients and diagnostics.

## Non-negotiable boundaries

1. The brain is simulation-first.
2. AI providers never receive authority to place orders.
3. Risk remains independent of AI confidence.
4. Allocation happens only after risk approval.
5. Simulation is the only execution implementation in the current phase.
6. Memory records must distinguish observation, decision, outcome and lesson.
7. Provider credentials are runtime secrets and never belong in source control.
8. Every cycle should be observable through workflow events and diagnostics.
9. Dashboard state is derived from backend state; the dashboard is not the source of truth.
10. Real-money broker/exchange execution is out of scope for this phase.

## Memory contract

A memory record should contain at minimum:

- `memory_id`
- `memory_type`: observation | decision | outcome | lesson
- `timestamp`
- `workflow_id` when applicable
- `asset`
- `payload`
- optional `tags`

Memory retrieval should support exact identifiers, keyword search and later semantic/vector retrieval without changing callers.

## Brain readiness criteria

The brain is ready for dashboard integration only when:

- every core service imports successfully in CI;
- the integration pipeline can complete a simulation cycle without bypassing domain services;
- a cycle writes memory records;
- memory can hydrate from persistence after restart;
- diagnostics identify unhealthy dependencies;
- failure at any stage produces an attributable workflow event;
- duplicate runtime implementations are either removed or explicitly marked as legacy.

## Dashboard contract

The dashboard consumes stable API contracts. It must not embed business logic that belongs in the brain. The UI should visualize:

- current simulated equity and cash;
- exposure and positions;
- latest cycle and decision trace;
- AI reasoning summary;
- risk decision;
- allocation decision;
- simulation fills;
- memory/lessons;
- system health;
- future wealth-goal state.

## Design workflow

The dashboard design workflow is:

1. **Canva** — visual direction, moodboards, presentation concepts and brand exploration.
2. **Figma** — authoritative product UI system, components, layouts, states and developer handoff.
3. **Implementation** — React/web frontend consumes the stable EchoMatrix API contracts.

Canva is the inspiration/visual exploration layer. Figma is the source of truth for implementation geometry and component behavior.
