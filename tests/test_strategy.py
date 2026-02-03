"""
Tests for Strategy module
"""
import pytest
import json
import tempfile
import os

from src.strategy import Strategy


@pytest.fixture
def sample_config():
    """Create a sample strategy config - realistic 10 ladders with Fibonacci

    Uses real production values:
    - base_gap: 0.8% (0.008) - realistic gap between ladders
    - max_gap: 15% (0.15) - cap per level
    - fibonacci: [1,1,2,3,5,8,13,21,34,55] - standard Fibonacci sequence
    - Compound formula: buy_multiplier = ∏(1 - gap_i)
    """
    return {
        "enabled": True,
        "name": "BTC Conservative",
        "pair": "BTCUSDT",
        "description": "Conservative BTC strategy with 10 Fibonacci ladders",
        "ladder_config": {
            "base_gap": 0.008,  # 0.8% base gap (realistic)
            "max_gap": 0.15,    # 15% max gap per level
            "ladders": 10,
            "fibonacci": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
            "unit_size_btc": 0.001
        },
        "capital_allocation": {
            "max_allocation_percent": 0.25,
            "reserve_percent": 0.10
        },
        "risk_management": {
            "safety_multiplier": 1.5,
            "stop_loss_percent": -0.30,
            "take_profit_percent": 0.25
        },
        "execution": {
            "auto_rebalance": True,
            "rebalance_interval_hours": 24,
            "min_profit_to_close": 0.005
        }
    }


@pytest.fixture
def strategy(sample_config):
    """Create a Strategy instance with temp config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_config, f)
        temp_path = f.name

    try:
        strategy = Strategy(temp_path)
        yield strategy
    finally:
        os.unlink(temp_path)


class TestStrategy:
    def test_load_config(self, strategy, sample_config):
        """Test that config is loaded correctly"""
        assert strategy.config['name'] == sample_config['name']
        assert strategy.config['pair'] == sample_config['pair']

    def test_ladder_calculation(self, strategy):
        """Test that 10 ladders are calculated correctly with compound Fibonacci gaps

        With base_gap=0.8%, max_gap=15%, Fibonacci [1,1,2,3,5,8,13,21,34,55]:
        Compound formula: buy_multiplier = ∏(1 - min(base_gap * fib, max_gap))

        Level  Fib  Raw Gap  Capped   Multiplier    Cumulative Drop
        -1     1    0.8%     0.8%     0.992000      0.8%
        -2     1    0.8%     0.8%     0.984064      1.6%
        -3     2    1.6%     1.6%     0.968319      3.2%
        -4     3    2.4%     2.4%     0.945079      5.5%
        -5     5    4.0%     4.0%     0.907276      9.3%
        -6     8    6.4%     6.4%     0.849210      15.1%
        -7     13   10.4%    10.4%    0.760892      23.9%
        -8     21   15.0%    15.0%    0.646759      35.3%  (capped)
        -9     34   15.0%    15.0%    0.549745      45.0%  (capped)
        -10    55   15.0%    15.0%    0.467283      53.3%  (capped)
        """
        assert len(strategy.ladders) == 10

        # Check first ladder
        assert strategy.ladders[0]['level'] == -1
        assert strategy.ladders[0]['fibonacci'] == 1
        assert strategy.ladders[0]['gap_percent'] == 0.008  # 0.8%

        # Compute expected compound multipliers
        base_gap = 0.008
        max_gap = 0.15
        fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        expected_multiplier = 1.0
        for i, fib in enumerate(fibonacci):
            gap = min(base_gap * fib, max_gap)
            expected_multiplier *= (1 - gap)
            expected_cumulative = 1 - expected_multiplier
            assert abs(strategy.ladders[i]['cumulative_gap_percent'] - expected_cumulative) < 0.0001
            assert strategy.ladders[i]['buy_price_multiplier'] > 0  # Never negative

        # Check all ladder levels are negative (buy below market)
        for i, ladder in enumerate(strategy.ladders):
            assert ladder['level'] == -(i + 1)

    def test_martingale_units(self, strategy):
        """Test Martingale unit doubling for 10 ladders"""
        expected_units = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
        for i, ladder in enumerate(strategy.ladders):
            assert ladder['units'] == expected_units[i]

        # Total units should be 2^10 - 1 = 1023
        total_units = sum(ladder['units'] for ladder in strategy.ladders)
        assert total_units == 1023

    def test_update_prices(self, strategy):
        """Test price updates"""
        current_price = 50000

        strategy.update_prices(current_price)

        # Check that buy prices are below current price
        for ladder in strategy.ladders:
            assert ladder['buy_price'] < current_price
            assert ladder['usdt_cost'] > 0

    def test_get_pending_ladders(self, strategy):
        """Test pending ladders filter for 10 ladders"""
        pending = strategy.get_pending_ladders()
        assert len(pending) == 10  # All should be pending initially

        # Mark one as active
        strategy.ladders[0]['status'] = 'active'
        pending = strategy.get_pending_ladders()
        assert len(pending) == 9

    def test_get_active_ladders(self, strategy):
        """Test active ladders filter"""
        active = strategy.get_active_ladders()
        assert len(active) == 0  # None should be active initially

        # Mark one as active
        strategy.ladders[0]['status'] = 'active'
        active = strategy.get_active_ladders()
        assert len(active) == 1

    def test_to_dict(self, strategy):
        """Test dictionary export"""
        strategy.update_prices(50000)
        result = strategy.to_dict()

        assert 'name' in result
        assert 'pair' in result
        assert 'ladders' in result
        assert 'total_swing' in result
        assert 'required_capital' in result
