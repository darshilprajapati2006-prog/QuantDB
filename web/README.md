# QuantDB Web

React + TypeScript/Vite client for the existing QuantDB Python services. The Streamlit research dashboard remains available under `dashboard/`.

## Run locally

From the repository root, install Python dependencies and start the API:

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

In another terminal:

```bash
cd web
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000`. The API docs are at `http://localhost:8000/docs`. `DATA_MODE=mock` is the default; set `DATA_MODE=real` to use the existing real provider bridge and configured MySQL connection. Real mode reports database errors and does not silently convert the UI to synthetic market data.

## API surface

`api/main.py` exposes provider-backed health, overview, exchange and security catalogs, market history, portfolios and positions, simulated orders and trades, strategies, historical backtests, risk reports, and the relational schema inventory. Quantitative calculations and backtest execution remain in `src/` services. Paper orders are simulated only.

## Current integration limits

The inspected checkout does not contain Python source files under `src/auth/` and has no HTTP authentication API. Authentication and registration are therefore not represented as working frontend flows. The schema includes users and roles, but the API does not claim to authenticate users. Feature navigation currently provides API-backed data views; order submission is exposed in the API contract and can be expanded into a ticket UI once the user identity and authorization policy are defined.
