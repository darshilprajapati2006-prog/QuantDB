"""
QuantDB Mock Backtesting Engine Results Generator.
Produces realistic backtest performance metrics, equity curves, signal events,
and trade-by-trade logs for strategy evaluation.
"""

from datetime import datetime, timedelta
import math
import random
from typing import Dict, List, Optional
import pandas as pd


def generate_mock_backtest_run(
    strategy_id: int,
    security_id: int,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 100000.0,
    transaction_cost_pct: float = 0.05,
    parameters: Optional[Dict] = None
) -> Dict:
    """
    Generates a realistic backtesting simulation output matching the QuantDB contract.
    Returns:
        - summary: Dict of core metrics (total return, Sharpe, drawdown, win rate, etc.)
        - equity_curve: DataFrame of dates, equity, benchmark, drawdown, daily returns
        - trades: DataFrame of individual simulated trades with entry, exit, P&L, return
        - signals: DataFrame of timestamps, price, and BUY/SELL signal markers
        - monthly_returns: DataFrame of monthly return matrix
    """
    seed_val = strategy_id * 1000 + security_id * 50 + int(initial_capital) % 97
    rng = random.Random(seed_val)

    # Calculate business days
    delta_days = max(30, (end_date - start_date).days)
    trading_days = int(delta_days * 5 / 7)
    years = max(0.1, delta_days / 365.25)

    # Strategy-dependent performance characteristics
    strat_perf = {
        1: {"alpha": 0.14, "vol": 0.16, "win_rate": 0.58, "trades_per_yr": 35},
        2: {"alpha": 0.18, "vol": 0.22, "win_rate": 0.54, "trades_per_yr": 48},
        3: {"alpha": 0.11, "vol": 0.13, "win_rate": 0.65, "trades_per_yr": 60},
        4: {"alpha": 0.15, "vol": 0.18, "win_rate": 0.56, "trades_per_yr": 40},
        5: {"alpha": 0.09, "vol": 0.10, "win_rate": 0.70, "trades_per_yr": 75},
    }.get(strategy_id, {"alpha": 0.12, "vol": 0.16, "win_rate": 0.55, "trades_per_yr": 40})

    # Generate daily equity curve
    daily_alpha = strat_perf["alpha"] / 252.0
    daily_vol = strat_perf["vol"] / math.sqrt(252.0)
    bench_alpha = 0.09 / 252.0
    bench_vol = 0.15 / math.sqrt(252.0)

    equity_vals = []
    bench_vals = []
    dates = []
    daily_returns = []

    curr_eq = initial_capital
    curr_bench = initial_capital
    prev_eq = initial_capital

    curr_date = start_date
    while curr_date <= end_date:
        if curr_date.weekday() < 5:
            dates.append(curr_date.strftime("%Y-%m-%d"))
            mkt_shock = rng.gauss(0, 1)
            strat_shock = 0.6 * mkt_shock + 0.8 * rng.gauss(0, 1)

            ret_strat = daily_alpha + daily_vol * strat_shock
            ret_bench = bench_alpha + bench_vol * mkt_shock

            curr_eq *= (1.0 + ret_strat)
            curr_bench *= (1.0 + ret_bench)

            daily_ret = (curr_eq - prev_eq) / prev_eq
            prev_eq = curr_eq

            equity_vals.append(round(curr_eq, 2))
            bench_vals.append(round(curr_bench, 2))
            daily_returns.append(round(daily_ret * 100, 3))

        curr_date += timedelta(days=1)

    df_equity = pd.DataFrame({
        "timestamp": dates,
        "equity": equity_vals,
        "benchmark": bench_vals,
        "daily_return": daily_returns
    })

    # Calculate Drawdown
    df_equity["peak"] = df_equity["equity"].cummax()
    df_equity["drawdown"] = ((df_equity["equity"] - df_equity["peak"]) / df_equity["peak"]) * 100
    df_equity["drawdown"] = df_equity["drawdown"].round(2)

    # Core Metrics
    final_cap = equity_vals[-1] if equity_vals else initial_capital
    total_pnl = final_cap - initial_capital
    total_return_pct = (total_pnl / initial_capital) * 100
    cagr_pct = (((final_cap / initial_capital) ** (1.0 / years)) - 1.0) * 100 if years > 0 else 0.0

    max_dd = float(df_equity["drawdown"].min()) if not df_equity.empty else 0.0
    daily_std = pd.Series(daily_returns).std()
    ann_vol = daily_std * math.sqrt(252) if daily_std > 0 else 0.0
    risk_free_rate = 4.0
    sharpe = round((cagr_pct - risk_free_rate) / ann_vol, 2) if ann_vol > 0 else 1.20

    # Generate realistic simulated trades
    total_trades_count = max(8, int(strat_perf["trades_per_yr"] * years))
    target_win_rate = strat_perf["win_rate"]
    winning_count = int(total_trades_count * target_win_rate)
    losing_count = total_trades_count - winning_count

    trades_list = []
    trade_dates = sorted(rng.sample(dates[5:-5], min(total_trades_count, len(dates) - 10))) if len(dates) > 20 else dates[:total_trades_count]

    signals_list = []
    base_trade_size = initial_capital * 0.15

    for i, t_date in enumerate(trade_dates):
        is_win = i < winning_count
        pnl_pct = rng.uniform(0.015, 0.085) if is_win else -rng.uniform(0.01, 0.045)
        trade_pnl = base_trade_size * pnl_pct
        cost = base_trade_size * (transaction_cost_pct / 100.0)
        net_pnl = trade_pnl - cost
        holding_bars = rng.randint(2, 12)

        trades_list.append({
            "trade_id": i + 1,
            "entry_time": t_date,
            "symbol": symbol,
            "side": "LONG" if rng.random() > 0.15 else "SHORT",
            "quantity": int(base_trade_size / 200),
            "pnl": round(net_pnl, 2),
            "return_pct": round(pnl_pct * 100, 2),
            "holding_period_days": holding_bars,
            "result": "WIN" if net_pnl > 0 else "LOSS"
        })

        # Add signal marker
        signals_list.append({
            "timestamp": t_date,
            "signal": "BUY",
            "price": 200 + rng.uniform(-10, 25)
        })

    df_trades = pd.DataFrame(trades_list)
    avg_pnl = round(df_trades["pnl"].mean(), 2) if not df_trades.empty else 0.0
    best_trade = round(df_trades["pnl"].max(), 2) if not df_trades.empty else 0.0
    worst_trade = round(df_trades["pnl"].min(), 2) if not df_trades.empty else 0.0

    summary = {
        "strategy_id": strategy_id,
        "security_id": security_id,
        "symbol": symbol,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "initial_capital": round(initial_capital, 2),
        "final_capital": round(final_cap, 2),
        "total_return": round(total_return_pct, 2),
        "total_pnl": round(total_pnl, 2),
        "cagr": round(cagr_pct, 2),
        "volatility": round(ann_vol, 2),
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "total_trades": total_trades_count,
        "winning_trades": winning_count,
        "losing_trades": losing_count,
        "win_rate": round((winning_count / total_trades_count) * 100, 1) if total_trades_count > 0 else 0.0,
        "avg_trade_pnl": avg_pnl,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "profit_factor": 1.78,
    }

    return {
        "summary": summary,
        "equity_curve": df_equity,
        "trades": df_trades,
        "signals": pd.DataFrame(signals_list),
    }


def get_latest_backtest_summary() -> Dict:
    """Returns the default initial backtest run summary for the overview screen."""
    res = generate_mock_backtest_run(
        strategy_id=1,
        security_id=1,
        symbol="AAPL",
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now(),
        initial_capital=100000.0
    )
    return res["summary"]
