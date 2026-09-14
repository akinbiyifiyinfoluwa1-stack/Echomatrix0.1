# EchoMatrix Research Laboratory

The Research Laboratory is the next large simulation-first layer of EchoMatrix. It turns historical candle series into repeatable research artifacts without sending orders to brokers, exchanges, wallets, or other external execution systems.

## Pipeline

`OHLCV -> validation -> features -> policy ensemble -> paper portfolio -> performance metrics -> experiments -> stress scenarios`

## Capabilities

- strict OHLCV validation and duplicate/timestamp checks
- return, SMA, EMA, volatility, drawdown and volume features
- momentum, trend and mean-reversion policy ensemble
- fee-aware long-only paper portfolio with realized P&L
- equity curve, drawdown, win rate and profit-factor reporting
- parameter-grid experiment ranking
- deterministic up/down shock stress tests
- FastAPI endpoints for research, experiments and stress analysis

This service is intentionally **simulation-only**. It is a research instrument, not an order-execution service.
