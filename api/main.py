"""FastAPI adapter for the existing QuantDB provider and quant services."""
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from dashboard.providers.factory import get_provider
from dashboard.mock.backtests import get_latest_backtest_summary

app = FastAPI(title="QuantDB API", version="1.0.0", description="HTTP interface for QuantDB research and paper trading.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def records(value: Any):
    if isinstance(value, pd.DataFrame):
        return value.astype(object).where(pd.notna(value), None).to_dict(orient="records")
    if isinstance(value, list):
        return value
    return value

class OrderRequest(BaseModel):
    portfolio_id: int = 1
    security_id: int
    symbol: str
    side: str
    order_type: str = "MARKET"
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

class BacktestRequest(BaseModel):
    strategy_id: int
    security_id: int
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=100000, gt=0)
    transaction_cost_pct: float = Field(default=0.05, ge=0, le=5)
    parameters: dict = {}

@app.get("/api/v1/health")
def health():
    return get_provider().get_system_status()

@app.get("/api/v1/overview")
def overview():
    p = get_provider()
    return {"market": records(p.get_market_overview()), "portfolios": p.get_portfolios(), "health": p.get_system_status(), "risk": p.get_risk_metrics(1), "backtest": get_latest_backtest_summary()}

@app.get("/api/v1/securities")
def securities(): return get_provider().get_securities()

@app.get("/api/v1/exchanges")
def exchanges(): return get_provider().get_exchanges()

@app.get("/api/v1/market-data/{security_id}")
def market_data(security_id: int, symbol: str = "RELIANCE", days: int = 180):
    end = datetime.now(); start = end - timedelta(days=max(1, min(days, 3650)))
    try: return records(get_provider().get_market_data(security_id, symbol, start, end, "1D"))
    except Exception as exc: raise HTTPException(503, str(exc)) from exc

@app.get("/api/v1/portfolios")
def portfolios(): return get_provider().get_portfolios()

@app.get("/api/v1/portfolios/{portfolio_id}")
def portfolio(portfolio_id: int):
    p = get_provider(); result = p.get_portfolio(portfolio_id)
    if result is None: raise HTTPException(404, "Portfolio not found")
    return {"summary": result, "positions": records(p.get_positions(portfolio_id)), "equity": records(p.get_portfolio_equity_curve(portfolio_id))}

@app.get("/api/v1/orders")
def orders(): return records(get_provider().get_orders())

@app.post("/api/v1/orders")
def submit_order(payload: OrderRequest):
    try: return get_provider().submit_order(**payload.dict())
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/trades")
def trades(): return records(get_provider().get_trades())

@app.get("/api/v1/strategies")
def strategies(): return get_provider().get_strategies()

@app.post("/api/v1/backtests")
def run_backtest(payload: BacktestRequest):
    try:
        from dashboard.services.backtest_service import execute_backtest
        ok, message, result = execute_backtest(**payload.dict())
        if not ok: raise HTTPException(400, message)
        return result
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/analytics/risk")
def risk(portfolio_id: int = 1): return get_provider().get_risk_metrics(portfolio_id)

@app.get("/api/v1/reports")
def reports(): return {"risk": get_provider().get_risk_metrics(1), "backtest": get_latest_backtest_summary()}

class ModeRequest(BaseModel):
    mode: str

@app.post("/api/v1/mode")
def set_mode(payload: ModeRequest):
    from dashboard.providers.factory import set_data_mode
    try:
        set_data_mode(payload.mode)
        return {"mode": payload.mode.lower(), "status": "updated"}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/database/tables")
def database_tables():
    from src.database.connection import get_connection
    conn = get_connection(use_pool=False)
    if not conn or not conn.is_connected():
        return [
            {"name": t, "type": "BASE TABLE", "row_count": 0}
            for t in ["users", "exchanges", "securities", "market_data", "orders", "trades", "portfolios", "positions", "strategies", "backtests", "backtest_results", "risk_metrics"]
        ]
    try:
        cur = conn.cursor()
        cur.execute("SHOW FULL TABLES")
        raw = cur.fetchall()
        result = []
        for name, t_type in raw:
            try:
                cur.execute(f"SELECT COUNT(*) FROM `{name}`")
                cnt = cur.fetchone()[0]
            except Exception:
                cnt = 0
            result.append({
                "name": name,
                "type": "VIEW" if "VIEW" in t_type.upper() else "BASE TABLE",
                "row_count": cnt
            })
        return result
    finally:
        conn.close()

@app.get("/api/v1/database/tables/{table_name}")
def table_records(table_name: str, limit: int = 50):
    import re
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise HTTPException(400, "Invalid table name")
    from src.database.connection import get_connection
    conn = get_connection(use_pool=False)
    if not conn or not conn.is_connected():
        raise HTTPException(503, "Database connection offline")
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM `{table_name}` LIMIT {min(limit, 100)}")
        rows = cur.fetchall()
        clean_rows = []
        for r in rows:
            clean_r = {}
            for k, v in r.items():
                if hasattr(v, "isoformat"):
                    clean_r[k] = v.isoformat()
                elif hasattr(v, "__float__"):
                    clean_r[k] = float(v)
                else:
                    clean_r[k] = v
            clean_rows.append(clean_r)
        return {"table": table_name, "count": len(clean_rows), "records": clean_rows}
    finally:
        conn.close()

@app.get("/api/v1/database/schema")
def schema():
    return {"mode": "MOCK" if get_provider().__class__.__name__ == "MockProvider" else "REAL", "tables": ["users", "exchanges", "securities", "market_data", "orders", "trades", "portfolios", "positions", "strategies", "backtests", "backtest_results", "risk_metrics"]}

