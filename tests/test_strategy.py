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
    - base_gap: 0.5% (0.005) - realistic gap between ladders
    - fibonacci: [1,1,2,3,5,8,13,21,34,55] - standard Fibonacci sequence
    - Total swing: 71.5% at ladder 10
    """
    return {
        "enabled": True,
        "name": "BTC Conservative",
        "pair": "BTCUSDT",
        "description": "Conservative BTC strategy with 10 Fibonacci ladders",
        "ladder_config": {
            "base_gap": 0.005,  # 0.5% base gap (realistic)
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
        """Test that 10 ladders are calculated correctly with Fibonacci gaps

        With base_gap=0.5% and Fibonacci [1,1,2,3,5,8,13,21,34,55]:
        - Ladder 1:  0.5% gap,  0.5% cumulative (buy at -0.5%)
        - Ladder 2:  0.5% gap,  1.0% cumulative (buy at -1.0%)
        - Ladder 3:  1.0% gap,  2.0% cumulative (buy at -2.0%)
        - Ladder 4:  1.5% gap,  3.5% cumulative (buy at -3.5%)
        - Ladder 5:  2.5% gap,  6.0% cumulative (buy at -6.0%)
        - Ladder 6:  4.0% gap, 10.0% cumulative (buy at -10.0%)
        - Ladder 7:  6.5% gap, 16.5% cumulative (buy at -16.5%)
        - Ladder 8: 10.5% gap, 27.0% cumulative (buy at -27.0%)
        - Ladder 9: 17.0% gap, 44.0% cumulative (buy at -44.0%)
        - Ladder 10: 27.5% gap, 71.5% cumulative (buy at -71.5%)
        """
        assert len(strategy.ladders) == 10

        # Check first ladder
        assert strategy.ladders[0]['level'] == -1
        assert strategy.ladders[0]['fibonacci'] == 1
        assert strategy.ladders[0]['gap_percent'] == 0.005  # 0.5%

        # Check cumulative gaps (Fibonacci: 1,1,2,3,5,8,13,21,34,55 × 0.005)
        expected_gaps = [0.005, 0.01, 0.02, 0.035, 0.06, 0.10, 0.165, 0.27, 0.44, 0.715]
        for i, ladder in enumerate(strategy.ladders):
            assert abs(ladder['cumulative_gap_percent'] - expected_gaps[i]) < 0.0001

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
