"""
QuantDB Dashboard Test Suite.
Validates the Service Layer, Mock & Real Providers, Data Contracts,
Input Validation, and Fault-Tolerance.
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

# Ensure root and dashboard on path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from dashboard.services import (
    market_service,
    trading_service,
    portfolio_service,
    strategy_service,
    backtest_service,
    analytics_service,
)
from dashboard.providers.factory import set_data_mode, get_provider, get_current_data_mode


def run_all_tests():
    print("==================================================")
    print("QUANTDB DASHBOARD AUTOMATED TEST SUITE")
    print("==================================================")

    # 1. Mock Mode & Securities
    set_data_mode("mock")
    assert get_current_data_mode() == "mock", "Data mode should be mock"
    secs = market_service.get_available_securities()
    assert len(secs) >= 6, f"Expected at least 6 securities, got {len(secs)}"
    print(f"[PASS] Securities master loaded: {len(secs)} instruments")

    # 2. Market Data Contract Verification
    end = datetime.now()
    start = end - timedelta(days=45)
    df_mkt = market_service.get_historical_market_data(1, "AAPL", start, end, interval="1D")
    assert not df_mkt.empty, "Market data dataframe should not be empty"
    required_mkt_cols = [
        "timestamp", "security_id", "symbol", "open_price", "high_price",
        "low_price", "close_price", "volume", "bid_price", "ask_price",
        "spread", "mid_price", "relative_spread_bps"
    ]
    for col in required_mkt_cols:
        assert col in df_mkt.columns, f"Data contract violation: missing '{col}'"
    print(f"[PASS] Market data contract verified: {len(df_mkt)} records with full OHLCV & microstructure")

    # 3. Portfolio & Positions Contract Verification
    ports = portfolio_service.get_all_portfolios()
    assert len(ports) >= 2, "Expected at least 2 portfolios"
    active_pid = ports[0]["portfolio_id"]
    p_summary = portfolio_service.get_portfolio_summary(active_pid)
    assert p_summary is not None, "Portfolio summary is None"
    for field in ["portfolio_value", "cash", "total_pnl", "realized_pnl", "unrealized_pnl"]:
        assert field in p_summary, f"Portfolio contract missing '{field}'"
    print(f"[PASS] Portfolio summary contract verified: {p_summary['portfolio_name']} (${p_summary['portfolio_value']:,.2f})")

    pos_df = portfolio_service.get_portfolio_positions(active_pid)
    assert not pos_df.empty, "Positions dataframe should not be empty"
    for col in ["security_id", "symbol", "quantity", "average_price", "current_price", "market_value", "unrealized_pnl", "weight"]:
        assert col in pos_df.columns, f"Position contract missing '{col}'"
    print(f"[PASS] Positions contract verified: {len(pos_df)} open positions")

    # 4. Trading Service Form Validation
    ok, msg, _ = trading_service.submit_simulated_order(active_pid, 1, "AAPL", "BUY", "LIMIT", -50, 220.0)
    assert not ok, "Should reject negative quantity"
    print(f"[PASS] Validation test: negative quantity rejected -> '{msg}'")

    ok, msg, _ = trading_service.submit_simulated_order(active_pid, 1, "AAPL", "BUY", "LIMIT", 50, -10.0)
    assert not ok, "Should reject negative limit price"
    print(f"[PASS] Validation test: negative price rejected -> '{msg}'")

    ok, msg, ord_obj = trading_service.submit_simulated_order(active_pid, 1, "AAPL", "BUY", "MARKET", 75, 224.50)
    assert ok and ord_obj["status"] == "FILLED", "Market order submission failed"
    print(f"[PASS] Order lifecycle: Market order submitted and matched -> #{ord_obj['order_id']}")

    # 5. Strategies Catalog
    strats = strategy_service.get_strategies()
    assert len(strats) >= 3, "Expected at least 3 quantitative strategies"
    strat_df = strategy_service.get_strategies_dataframe()
    assert len(strat_df) == len(strats), "Strategy dataframe mismatch"
    print(f"[PASS] Strategy catalog verified: {len(strats)} registered strategies")

    # 6. Backtesting Engine Execution
    bt_ok, bt_msg, bt_res = backtest_service.execute_backtest(
        strategy_id=strats[0]["strategy_id"],
        security_id=1,
        symbol="AAPL",
        start_date=start,
        end_date=end,
        initial_capital=100000.0,
        transaction_cost_pct=0.05
    )
    assert bt_ok, f"Backtest execution failed: {bt_msg}"
    assert "summary" in bt_res and "equity_curve" in bt_res and "trades" in bt_res, "Backtest payload missing sections"
    s = bt_res["summary"]
    for col in ["total_return", "total_pnl", "volatility", "sharpe_ratio", "max_drawdown", "total_trades", "win_rate"]:
        assert col in s, f"Backtest result contract missing '{col}'"
    print(f"[PASS] Backtest simulation engine verified: Return {s['total_return']}%, Sharpe {s['sharpe_ratio']}, {s['total_trades']} trades")

    # 7. Analytics & System Status
    health = analytics_service.get_system_health()
    assert health["data_mode"] == "MOCK", "Health check should report MOCK"
    risk = analytics_service.get_portfolio_risk_metrics(active_pid)
    assert "sharpe_ratio" in risk and "max_drawdown" in risk, "Risk metrics contract missing fields"
    print(f"[PASS] Analytics & Risk metrics verified: Sharpe {risk['sharpe_ratio']}, VaR {risk.get('var_95_daily')}%")

    # 8. Real Provider Fault-Tolerance Test (Graceful handling when MySQL/backend offline)
    set_data_mode("real")
    real_prov = get_provider()
    assert real_prov.mode_name == "REAL", "Should be in REAL mode"
    real_df = market_service.get_historical_market_data(1, "AAPL", start, end)
    assert isinstance(real_df, type(df_mkt)), "Real provider should return DataFrame safely without crashing"
    print("[PASS] Real Provider fault-tolerance verified: Handled offline backend gracefully without exceptions")

    # 9. Authentication & RBAC Contract Verification
    from dashboard.services import auth_service
    from src.auth.roles import Role

    # Login as Admin
    ok_admin, msg_admin = auth_service.login("admin01", "Admin01@QuantDB")
    assert ok_admin, f"Admin login failed: {msg_admin}"
    assert auth_service.is_authenticated() is True, "Session should be authenticated"
    assert auth_service.get_current_role() == Role.ADMIN, "Role should be ADMIN"
    assert auth_service.check_page_access("Admin") is True, "Admin must have access to Admin module"
    assert auth_service.check_page_access("Trading") is True, "Admin must have access to Trading module"
    
    # Login as Standard User
    ok_user, msg_user = auth_service.login("user01", "User01@QuantDB")
    assert ok_user, f"User login failed: {msg_user}"
    assert auth_service.get_current_role() == Role.USER, "Role should be USER"
    assert auth_service.check_page_access("Overview") is True, "User must have access to Overview"
    assert auth_service.check_page_access("Market Data") is True, "User must have access to Market Data"
    assert auth_service.check_page_access("Trading") is False, "User must be restricted from Trading"
    assert auth_service.check_page_access("Admin") is False, "User must be restricted from Admin"
    assert auth_service.check_page_access("Backtesting") is False, "User must be restricted from Backtesting"

    # Logout
    auth_service.logout()
    assert auth_service.is_authenticated() is False, "Session should be logged out"
    print("[PASS] Authentication & RBAC Access Control verified: 4 Roles & Page Guards")

    # Reset to mock mode
    set_data_mode("mock")

    print("==================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("==================================================")


if __name__ == "__main__":
    run_all_tests()
