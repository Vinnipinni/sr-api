# sr-api

A small FastAPI service that fetches market data and finds the support and
resistance levels in it.

## Why

I built a support/resistance trading strategy in JavaScript first. This is the
same level-detection logic rewritten as a Python API, so the analysis can be
called from anywhere instead of living inside one script.

## Endpoints

| Endpoint | What it does |
|---|---|
| `GET /health` | Liveness check |
| `GET /candles` | OHLCV candles for a symbol and interval |
| `GET /levels` | Support and resistance levels, sorted by distance from price |

`/levels` takes `symbol`, `interval`, `k`, `tol_pct` and `min_touches`.

## How the levels are found

1. **Pivots.** A bar is a swing high if its high is above every high within `k`
   bars either side. Swing lows are the mirror image.
2. **Clustering.** Pivots within `tol_pct` of each other are the same level, not
   two — they get merged, and the level's price becomes a running average of the
   pivots that formed it. The number of merges is the level's strength.
3. **Filtering.** A level needs at least `min_touches` before it counts.
   Resistance is what sits above the current price, support what sits below.

## Running it

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000/docs for the interactive API docs, which
FastAPI generates from the code.

## Data

Candles come from Binance's public REST endpoint. No API key, no orders, read
only.