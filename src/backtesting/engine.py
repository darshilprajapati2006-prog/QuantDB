"""
QuantDB Backtesting Engine.

Flow:
Historical Market Data
        ↓
Strategy
        ↓
Trading Signals
        ↓
Simulated Orders
        ↓
Simulated Trades
        ↓
Portfolio / Positions
        ↓
P&L
        ↓
Risk Metrics
        ↓
Backtest Result

Academic/simulation use only.
No real-money trading.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.backtesting.strategies import generate_signals


class BacktestEngine:
    """
    Historical backtesting engine for QuantDB.

    Parameters
    ----------
    strategy:
        Strategy name, e.g. 'moving_average', 'momentum',
        or 'mean_reversion'.

    security:
        Security identifier or symbol.

    historical_data:
        Pandas DataFrame containing historical prices.

    start_date:
        Backtest start date.

    end_date:
        Backtest end date.

    initial_capital:
        Starting simulated capital.

    transaction_cost:
        Transaction cost as a decimal fraction.
        Example: 0.001 = 0.1%.
    """

    def __init__(
        self,
        strategy: str,
        security: Any,
        historical_data: pd.DataFrame,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        initial_capital: float = 100000.0,
        transaction_cost: float = 0.0,
        strategy_parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive.")

        if transaction_cost < 0:
            raise ValueError("Transaction cost cannot be negative.")

        if not isinstance(historical_data, pd.DataFrame):
            raise TypeError("historical_data must be a pandas DataFrame.")

        if historical_data.empty:
            raise ValueError("Historical data cannot be empty.")

        self.strategy = strategy
        self.security = security
        self.historical_data = historical_data.copy()
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = float(initial_capital)
        self.transaction_cost = float(transaction_cost)
        self.strategy_parameters = strategy_parameters or {}

        self.data = self._prepare_data()

    # ============================================================
    # DATA PREPARATION
    # ============================================================

    def _prepare_data(self) -> pd.DataFrame:
        """Validate, normalize and filter historical market data."""

        data = self.historical_data.copy()

        # Support both QuantDB and common pandas column names.
        column_map = {}

        if "close_price" in data.columns:
            column_map["close_price"] = "close"
        elif "close" in data.columns:
            column_map["close"] = "close"
        else:
            raise ValueError(
                "Historical data must contain 'close_price' or 'close'."
            )

        if "timestamp" in data.columns:
            column_map["timestamp"] = "timestamp"
        elif "date" in data.columns:
            column_map["date"] = "timestamp"

        data = data.rename(columns=column_map)

        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(
                data["timestamp"],
                errors="coerce",
            )

            data = data.dropna(subset=["timestamp"])
            data = data.sort_values("timestamp")

            if self.start_date is not None:
                start = pd.to_datetime(self.start_date)
                data = data[data["timestamp"] >= start]

            if self.end_date is not None:
                end = pd.to_datetime(self.end_date)
                data = data[data["timestamp"] <= end]

        data["close"] = pd.to_numeric(
            data["close"],
            errors="coerce",
        )

        data = data.dropna(subset=["close"])

        if data.empty:
            raise ValueError(
                "No valid historical data remains after filtering."
            )

        if (data["close"] <= 0).any():
            raise ValueError("Close prices must be positive.")

        data = data.reset_index(drop=True)

        return data

    # ============================================================
    # SIGNAL GENERATION
    # ============================================================

    def _generate_signals(self) -> pd.Series:
        """Generate BUY/SELL/HOLD signals using the selected strategy."""

        return generate_signals(
            self.data["close"],
            self.strategy,
            **self.strategy_parameters,
        )

    # ============================================================
    # SIMULATION
    # ============================================================

    def _simulate(self, signals: pd.Series) -> tuple:
        """
        Simulate orders, trades, positions and portfolio equity.

        Long-only simulation:
        - BUY opens/increases a position.
        - SELL reduces/closes a position.
        - No short selling.
        """

        cash = self.initial_capital
        quantity = 0.0
        average_price = 0.0

        trades = []
        equity_records = []

        for index, row in self.data.iterrows():

            price = float(row["close"])
            signal = str(signals.iloc[index])

            timestamp = (
                row["timestamp"]
                if "timestamp" in self.data.columns
                else index
            )

            # ----------------------------------------------------
            # BUY
            # ----------------------------------------------------

            if signal == "BUY":

                available_cash = cash

                if available_cash > 0:

                    buy_quantity = available_cash / (
                        price * (1.0 + self.transaction_cost)
                    )

                    if buy_quantity > 0:

                        gross_value = buy_quantity * price
                        transaction_fee = (
                            gross_value * self.transaction_cost
                        )

                        total_cost = gross_value + transaction_fee

                        if total_cost <= cash + 1e-12:

                            old_quantity = quantity

                            if old_quantity > 0:
                                average_price = (
                                    (
                                        average_price * old_quantity
                                        + price * buy_quantity
                                    )
                                    / (old_quantity + buy_quantity)
                                )
                            else:
                                average_price = price

                            quantity += buy_quantity
                            cash -= total_cost

                            trades.append(
                                {
                                    "timestamp": timestamp,
                                    "security": self.security,
                                    "side": "BUY",
                                    "quantity": buy_quantity,
                                    "price": price,
                                    "gross_value": gross_value,
                                    "transaction_cost": transaction_fee,
                                    "pnl": 0.0,
                                }
                            )

            # ----------------------------------------------------
            # SELL
            # ----------------------------------------------------

            elif signal == "SELL" and quantity > 0:

                sell_quantity = quantity

                gross_value = sell_quantity * price
                transaction_fee = (
                    gross_value * self.transaction_cost
                )

                net_proceeds = gross_value - transaction_fee

                realized_pnl = (
                    (price - average_price) * sell_quantity
                    - transaction_fee
                )

                cash += net_proceeds

                quantity = 0.0
                average_price = 0.0

                trades.append(
                    {
                        "timestamp": timestamp,
                        "security": self.security,
                        "side": "SELL",
                        "quantity": sell_quantity,
                        "price": price,
                        "gross_value": gross_value,
                        "transaction_cost": transaction_fee,
                        "pnl": realized_pnl,
                    }
                )

            # ----------------------------------------------------
            # PORTFOLIO EQUITY
            # ----------------------------------------------------

            market_value = quantity * price
            equity = cash + market_value

            unrealized_pnl = 0.0

            if quantity > 0:
                unrealized_pnl = (
                    price - average_price
                ) * quantity

            equity_records.append(
                {
                    "timestamp": timestamp,
                    "price": price,
                    "cash": cash,
                    "position_quantity": quantity,
                    "market_value": market_value,
                    "equity": equity,
                    "unrealized_pnl": unrealized_pnl,
                }
            )

        # --------------------------------------------------------
        # CLOSE ANY OPEN POSITION AT FINAL PRICE
        # --------------------------------------------------------

        if quantity > 0:

            final_price = float(self.data["close"].iloc[-1])

            timestamp = (
                self.data["timestamp"].iloc[-1]
                if "timestamp" in self.data.columns
                else len(self.data) - 1
            )

            gross_value = quantity * final_price

            transaction_fee = (
                gross_value * self.transaction_cost
            )

            net_proceeds = gross_value - transaction_fee

            realized_pnl = (
                (final_price - average_price) * quantity
                - transaction_fee
            )

            cash += net_proceeds

            trades.append(
                {
                    "timestamp": timestamp,
                    "security": self.security,
                    "side": "SELL",
                    "quantity": quantity,
                    "price": final_price,
                    "gross_value": gross_value,
                    "transaction_cost": transaction_fee,
                    "pnl": realized_pnl,
                    "reason": "END_OF_BACKTEST",
                }
            )

            quantity = 0.0

            # Update final equity after liquidation.
            if equity_records:
                equity_records[-1]["cash"] = cash
                equity_records[-1]["position_quantity"] = 0.0
                equity_records[-1]["market_value"] = 0.0
                equity_records[-1]["equity"] = cash
                equity_records[-1]["unrealized_pnl"] = 0.0

        trades_df = pd.DataFrame(trades)
        equity_df = pd.DataFrame(equity_records)

        return trades_df, equity_df

    # ============================================================
    # PERFORMANCE METRICS
    # ============================================================

    @staticmethod
    def _calculate_metrics(
        initial_capital: float,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame,
    ) -> Dict[str, float]:
        """Calculate requested backtest performance and risk metrics."""

        if equity_df.empty:
            raise ValueError("Equity curve cannot be empty.")

        final_equity = float(equity_df["equity"].iloc[-1])

        total_pnl = final_equity - initial_capital

        total_return = (
            total_pnl / initial_capital
            if initial_capital != 0
            else 0.0
        )

        equity_returns = (
            equity_df["equity"]
            .pct_change()
            .replace([np.inf, -np.inf], np.nan)
            .dropna()
        )

        # --------------------------------------------------------
        # Volatility
        # --------------------------------------------------------

        if len(equity_returns) > 1:
            volatility = float(equity_returns.std(ddof=1))
        else:
            volatility = 0.0

        # --------------------------------------------------------
        # Sharpe Ratio
        # --------------------------------------------------------

        if len(equity_returns) > 1:
            std = float(equity_returns.std(ddof=1))

            if std != 0:
                sharpe_ratio = float(
                    equity_returns.mean() / std
                )
            else:
                sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0

        # --------------------------------------------------------
        # Maximum Drawdown
        # --------------------------------------------------------

        running_max = equity_df["equity"].cummax()

        drawdown = (
            equity_df["equity"] / running_max
        ) - 1.0

        max_drawdown = float(drawdown.min())

        # --------------------------------------------------------
        # Trade statistics
        # --------------------------------------------------------

        total_trades = len(trades_df)

        if not trades_df.empty and "side" in trades_df.columns:
            realized_trades = trades_df[
                trades_df["side"] == "SELL"
            ]

            winning_trades = int(
                (realized_trades["pnl"] > 0).sum()
            )

            losing_trades = int(
                (realized_trades["pnl"] < 0).sum()
            )

            closed_trades = len(realized_trades)

            if closed_trades > 0:
                win_rate = (
                    winning_trades / closed_trades
                ) * 100.0
            else:
                win_rate = 0.0

        else:
            winning_trades = 0
            losing_trades = 0
            win_rate = 0.0

        return {
            "total_return": float(total_return),
            "total_pnl": float(total_pnl),
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_trades": int(total_trades),
            "winning_trades": int(winning_trades),
            "losing_trades": int(losing_trades),
            "win_rate": float(win_rate),
        }

    # ============================================================
    # PUBLIC API
    # ============================================================

    def run(self) -> Dict[str, Any]:
        """
        Execute the complete backtest.

        Returns
        -------
        dict
            Backtest result containing:
            - strategy
            - security
            - start_date
            - end_date
            - initial_capital
            - final_equity
            - performance metrics
            - trades
            - equity_curve
        """

        signals = self._generate_signals()

        self.data["signal"] = signals

        trades_df, equity_df = self._simulate(
            signals
        )

        metrics = self._calculate_metrics(
            initial_capital=self.initial_capital,
            equity_df=equity_df,
            trades_df=trades_df,
        )

        result = {
            "strategy": self.strategy,
            "security": self.security,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "final_equity": float(
                equity_df["equity"].iloc[-1]
            ),
            **metrics,
            "trades": trades_df,
            "equity_curve": equity_df,
        }

        return result


def run_backtest(
    strategy: str,
    security: Any,
    historical_data: pd.DataFrame,
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    initial_capital: float = 100000.0,
    transaction_cost: float = 0.0,
    strategy_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function for running a backtest.

    This is the main function the backend/frontend can call.
    """

    engine = BacktestEngine(
        strategy=strategy,
        security=security,
        historical_data=historical_data,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        transaction_cost=transaction_cost,
        strategy_parameters=strategy_parameters,
    )

    return engine.run()