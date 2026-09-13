# EchoMatrix Commerce Brain

EchoMatrix is now being extended from the financial intelligence foundation into a modular **e-commerce intelligence operating system**.

## Principle

> Build the brain first. Give the brain a body later.

The commerce layer coordinates specialized domain agents before any storefront, payment provider, shipping provider, or external commerce connector is attached.

## Current flow

`Customer Request -> Customer Intelligence -> Product Intelligence -> Inventory Intelligence -> Commerce Finance -> Order Management -> Decision -> Memory`

The first implementation is intentionally **simulation/intelligence only**. It does not charge cards, place real orders, modify inventory in an external system, or call payment providers.

## Services planned

- `commerce-brain` — central orchestration and decision trace
- `product-intelligence` — catalog, variants, product matching and product knowledge
- `customer-intelligence` — profiles, preferences and customer context
- `inventory-intelligence` — availability, stock state and demand signals
- `commerce-finance` — pricing, totals, fees and profitability context
- `order-management` — cart/order state machine and fulfillment readiness
- `customer-support` — support reasoning and escalation
- `commerce-analytics` — sales, product and customer intelligence
- `commerce-memory` — observations, decisions, outcomes and lessons

## First vertical slice

The first working slice is the orchestrator plus five domain agents. It accepts a customer request, gathers independent domain assessments, produces a single traceable commerce decision, and explicitly reports that no external transaction was executed.

## Safety boundary

External payments, live order placement and other irreversible commerce actions remain disabled until the architecture, authorization model, audit trail and integration contracts are independently validated.
