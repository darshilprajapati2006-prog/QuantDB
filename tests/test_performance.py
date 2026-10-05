import os
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import pytest

from src.utils.perf import perf_timer, is_perf_debug_enabled
from dashboard.components.charts import _downsample_for_chart
from dashboard.services.trading_service import invalidate_trading_cache, get_orders
from dashboard.services.market_service import get_available_securities, clear_market_service_cache
from dashboard.services.strategy_service import get_strategies, clear_strategy_service_cache


class TestPerformanceOptimizations:
    """Verifies production-level performance enhancements across QuantDB."""

    def test_perf_timer_quiet_in_production(self, capsys):
        """Verifies perf_timer does not log anything when debug mode is disabled."""
        with patch.dict(os.environ, {"QUANTDB_PERF_DEBUG": "0", "DEBUG": "0"}):
            with perf_timer("test operation"):
                _ = sum(range(100))
        captured = capsys.readouterr()
        assert "[PERF]" not in captured.out
        assert "[PERF]" not in captured.err

    def test_perf_timer_active_in_debug(self, capsys):
        """Verifies perf_timer outputs timing when debug mode is enabled."""
        with patch.dict(os.environ, {"QUANTDB_PERF_DEBUG": "1"}):
            with perf_timer("sample task"):
                _ = sum(range(100))
        captured = capsys.readouterr()
        assert "[PERF] sample task:" in captured.out

    def test_chart_downsampling_limits_large_series(self):
        """Verifies that large time-series datasets are downsampled without modifying endpoints."""
        dates = pd.date_range("2020-01-01", periods=2000, freq="15min")
        df_large = pd.DataFrame({
            "timestamp": dates,
            "open_price": np.linspace(100, 200, 2000),
            "high_price": np.linspace(101, 201, 2000),
            "low_price": np.linspace(99, 199, 2000),
            "close_price": np.linspace(100.5, 200.5, 2000),
            "volume": np.full(2000, 500),
        })

        downsampled = _downsample_for_chart(df_large, max_points=500)
        assert len(downsampled) <= 501
        assert downsampled["timestamp"].iloc[0] == df_large["timestamp"].iloc[0]
        assert downsampled["timestamp"].iloc[-1] == df_large["timestamp"].iloc[-1]
        # Original remains completely intact
        assert len(df_large) == 2000

    def test_chart_downsampling_preserves_small_series(self):
        """Verifies small datasets below max_points are not modified."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        df_small = pd.DataFrame({"timestamp": dates, "close_price": range(30)})
        downsampled = _downsample_for_chart(df_small, max_points=500)
        assert len(downsampled) == 30

    @patch("dashboard.services.market_service.get_provider")
    def test_market_securities_caching(self, mock_get_provider):
        """Verifies repeated calls to get_available_securities hit the cache."""
        clear_market_service_cache()
        mock_provider = MagicMock()
        mock_provider.get_securities.return_value = [{"symbol": "AAPL", "security_id": 1}]
        mock_get_provider.return_value = mock_provider

        res1 = get_available_securities()
        res2 = get_available_securities()

        assert res1 == res2
        # Should have called provider once due to caching
        assert mock_provider.get_securities.call_count == 1
        clear_market_service_cache()

    @patch("dashboard.services.strategy_service.get_provider")
    def test_strategy_caching(self, mock_get_provider):
        """Verifies repeated calls to get_strategies hit the cache."""
        clear_strategy_service_cache()
        mock_provider = MagicMock()
        mock_provider.get_strategies.return_value = [{"strategy_id": 1, "name": "SMA"}]
        mock_get_provider.return_value = mock_provider

        res1 = get_strategies()
        res2 = get_strategies()

        assert res1 == res2
        assert mock_provider.get_strategies.call_count == 1
        clear_strategy_service_cache()
