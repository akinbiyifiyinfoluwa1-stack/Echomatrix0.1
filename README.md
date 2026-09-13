# EchoMatrix

AI Financial & Wealth Operating System — modular platform connecting market data, AI, simulation, risk management, capital allocation, execution, and wealth goals.

Core principle: **Build the brain first. Give the brain a body later.** Expand the body only when the system proves it needs more compute.

The repository now contains two compatible intelligence foundations:

- **Financial intelligence** — market/research/strategy/risk/allocation/simulation/memory.
- **Commerce intelligence** — customer/product/inventory/finance/order orchestration, initially simulation-only.

## Commerce brain

The commerce architecture follows the same modular pattern:

`Customer Request -> Specialized Domain Agents -> Orchestrator -> Decision Trace -> Memory`

The first vertical slice lives in `services/commerce-brain`. It coordinates customer, product, inventory, finance and order-management agents without performing external transactions.

### Run locally

```bash
cd services/commerce-brain
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

Then open:

- `GET /health`
- `GET /commerce/demo`
- `POST /commerce/plan`

## Safety / integration boundary

The commerce foundation does **not** charge cards, place live orders, alter external inventory, or call payment providers. External integrations will be added only after authorization, audit, idempotency, error handling and integration contracts are validated.

## Existing deployment

Cloud deployment is intended to be connected to this GitHub repository. Existing financial services remain separate while the commerce brain is developed as a new vertical.
