"""
QuantDB Repository Layer

Provides a clean Python interface between the application
and the database query layer.
"""

from typing import Any, Optional

from .connection import get_connection
from . import queries


class Repository:
    """Database repository for QuantDB application operations."""

    def __init__(self):
        self.connection = None

    def _get_connection(self):
        """Create and return a database connection."""
        return get_connection()

    # =========================================================
    # USERS
    # =========================================================

    def get_user(self, user_id: int):
        conn = self._get_connection()
        try:
            return queries.get_user_by_id(conn, user_id)
        finally:
            conn.close()

    def get_user_by_email(self, email: str):
        conn = self._get_connection()
        try:
            return queries.get_user_by_email(conn, email)
        finally:
            conn.close()

    def get_user_by_username(self, username: str):
        conn = self._get_connection()
        try:
            return queries.get_user_by_username(conn, username)
        finally:
            conn.close()

    def get_user_by_identifier(self, identifier: str):
        conn = self._get_connection()
        try:
            return queries.get_user_by_identifier(conn, identifier)
        finally:
            conn.close()

    def get_users(self):
        conn = self._get_connection()
        try:
            return queries.get_all_users(conn)
        finally:
            conn.close()

    def update_user_role(self, user_id: int, role: str):
        conn = self._get_connection()
        try:
            return queries.update_user_role(conn, user_id, role)
        finally:
            conn.close()

    def update_user_status(self, user_id: int, status: str):
        conn = self._get_connection()
        try:
            return queries.update_user_status(conn, user_id, status)
        finally:
            conn.close()

    def update_user_password(self, user_id: int, password_hash: str):
        conn = self._get_connection()
        try:
            return queries.update_user_password(conn, user_id, password_hash)
        finally:
            conn.close()

    def create_user(
        self,
        username: str,
        name: str,
        email: str,
        password_hash: str,
        role: str,
        status: str = "ACTIVE",
    ):
        conn = self._get_connection()
        try:
            return queries.create_user(
                conn, username, name, email, password_hash, role, status
            )
        finally:
            conn.close()

    # =========================================================
    # SECURITIES
    # =========================================================

    def get_security(self, security_id: int):
        conn = self._get_connection()
        try:
            return queries.get_security_by_id(conn, security_id)
        finally:
            conn.close()

    def get_securities(self):
        conn = self._get_connection()
        try:
            return queries.get_all_securities(conn)
        finally:
            conn.close()

    # =========================================================
    # MARKET DATA
    # =========================================================

    def get_market_data(
        self,
        security_id: int,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ):
        conn = self._get_connection()
        try:
            return queries.get_market_data(
                conn,
                security_id,
                start_time,
                end_time,
            )
        finally:
            conn.close()

    # =========================================================
    # ORDERS
    # =========================================================

    def get_order(self, order_id: int):
        conn = self._get_connection()
        try:
            return queries.get_order_by_id(conn, order_id)
        finally:
            conn.close()

    def get_orders(self, user_id: Optional[int] = None):
        conn = self._get_connection()
        try:
            if user_id is not None:
                return queries.get_orders_by_user(conn, user_id)

            return queries.get_all_orders(conn)
        finally:
            conn.close()

    def create_order(
        self,
        user_id: int,
        security_id: int,
        order_type: str,
        side: str,
        quantity: float,
        order_price: Optional[float],
        order_status: str,
        order_time: str,
    ):
        conn = self._get_connection()

        try:
            result = queries.insert_order(
                conn,
                user_id,
                security_id,
                order_type,
                side,
                quantity,
                order_price,
                order_status,
                order_time,
            )

            conn.commit()
            return result

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    def update_order_status(
        self,
        order_id: int,
        order_status: str,
    ):
        conn = self._get_connection()

        try:
            result = queries.update_order_status(
                conn,
                order_id,
                order_status,
            )

            conn.commit()
            return result

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    # =========================================================
    # TRADES
    # =========================================================

    def get_trade(self, trade_id: int):
        conn = self._get_connection()
        try:
            return queries.get_trade_by_id(conn, trade_id)
        finally:
            conn.close()

    def get_trades(self, security_id: Optional[int] = None):
        conn = self._get_connection()
        try:
            if security_id is not None:
                return queries.get_trades_by_security(
                    conn,
                    security_id,
                )

            return queries.get_all_trades(conn)
        finally:
            conn.close()

    def create_trade(
        self,
        order_id: int,
        security_id: int,
        trade_side: str,
        quantity: float,
        execution_price: float,
        trade_time: str,
        transaction_cost: float,
    ):
        conn = self._get_connection()

        try:
            result = queries.insert_trade(
                conn,
                order_id,
                security_id,
                trade_side,
                quantity,
                execution_price,
                trade_time,
                transaction_cost,
            )

            conn.commit()
            return result

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    # =========================================================
    # PORTFOLIOS
    # =========================================================

    def get_portfolio(self, portfolio_id: int):
        conn = self._get_connection()
        try:
            return queries.get_portfolio_by_id(
                conn,
                portfolio_id,
            )
        finally:
            conn.close()

    def get_portfolios(self, user_id: Optional[int] = None):
        conn = self._get_connection()
        try:
            if user_id is not None:
                return queries.get_portfolios_by_user(
                    conn,
                    user_id,
                )

            return queries.get_all_portfolios(conn)
        finally:
            conn.close()

    # =========================================================
    # POSITIONS
    # =========================================================

    def get_position(
        self,
        portfolio_id: int,
        security_id: int,
    ):
        conn = self._get_connection()

        try:
            return queries.get_position(
                conn,
                portfolio_id,
                security_id,
            )
        finally:
            conn.close()

    def get_positions(self, portfolio_id: int):
        conn = self._get_connection()

        try:
            return queries.get_positions_by_portfolio(
                conn,
                portfolio_id,
            )
        finally:
            conn.close()

    # =========================================================
    # STRATEGIES
    # =========================================================

    def get_strategy(self, strategy_id: int):
        conn = self._get_connection()

        try:
            return queries.get_strategy_by_id(
                conn,
                strategy_id,
            )
        finally:
            conn.close()

    def get_strategies(self, user_id: Optional[int] = None):
        conn = self._get_connection()

        try:
            if user_id is not None:
                return queries.get_strategies_by_user(
                    conn,
                    user_id,
                )

            return queries.get_all_strategies(conn)
        finally:
            conn.close()

    def create_strategy(
        self,
        user_id: int,
        strategy_name: str,
        description: Optional[str],
        strategy_type: str,
        parameters: Optional[str],
        status: str,
        created_at: str,
    ):
        conn = self._get_connection()

        try:
            result = queries.insert_strategy(
                conn,
                user_id,
                strategy_name,
                description,
                strategy_type,
                parameters,
                status,
                created_at,
            )

            conn.commit()
            return result

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    # =========================================================
    # BACKTESTS
    # =========================================================

    def get_backtest(self, backtest_id: int):
        conn = self._get_connection()

        try:
            return queries.get_backtest_by_id(
                conn,
                backtest_id,
            )
        finally:
            conn.close()

    def get_backtests(self, strategy_id: Optional[int] = None):
        conn = self._get_connection()

        try:
            if strategy_id is not None:
                return queries.get_backtests_by_strategy(
                    conn,
                    strategy_id,
                )

            return queries.get_all_backtests(conn)
        finally:
            conn.close()

    # =========================================================
    # BACKTEST RESULTS
    # =========================================================

    def get_backtest_result(self, backtest_id: int):
        conn = self._get_connection()

        try:
            return queries.get_backtest_result(
                conn,
                backtest_id,
            )
        finally:
            conn.close()

    # =========================================================
    # RISK METRICS
    # =========================================================

    def get_risk_metrics(
        self,
        portfolio_id: Optional[int] = None,
        backtest_id: Optional[int] = None,
    ):
        conn = self._get_connection()

        try:
            return queries.get_risk_metrics(
                conn,
                portfolio_id,
                backtest_id,
            )
        finally:
            conn.close()


# =============================================================
# DEFAULT REPOSITORY INSTANCE
# =============================================================

repository = Repository()