# Ecometrics Market Data

The market-data service is the first sensory layer of the Ecometrics brain.

It defines canonical financial objects so future services do not need to understand every provider's proprietary format.

## Current scope

- Instrument model
- Asset-class taxonomy
- Market tick model
- OHLCV candle model
- Basic validation
- Demo API endpoints

## Run

```bash
cd services/market-data
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
