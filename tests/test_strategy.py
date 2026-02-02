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
    """Create a sample strategy config"""
    return {
        "enabled": True,
        "name": "Test Strategy",
        "pair": "BTCUSDT",
        "description": "Test strategy for unit tests",
        "ladder_config": {
            "base_gap": 0.01,
            "ladders": 4,
            "fibonacci": [1, 1, 2, 3],
            "unit_size_btc": 0.01
        },
        "capital_allocation": {
            "max_allocation_percent": 0.20,
            "reserve_percent": 0.10
        },
        "risk_management": {
            "safety_multiplier": 1.5,
            "stop_loss_percent": -0.25,
            "take_profit_percent": 0.20
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
        """Test that ladders are calculated correctly"""
        assert len(strategy.ladders) == 4

        # Check first ladder
        assert strategy.ladders[0]['level'] == -1
        assert strategy.ladders[0]['fibonacci'] == 1
        assert strategy.ladders[0]['gap_percent'] == 0.01

        # Check cumulative gaps
        expected_gaps = [0.01, 0.02, 0.04, 0.07]
        for i, ladder in enumerate(strategy.ladders):
            assert abs(ladder['cumulative_gap_percent'] - expected_gaps[i]) < 0.0001

    def test_martingale_units(self, strategy):
        """Test Martingale unit doubling"""
        expected_units = [1, 2, 4, 8]
        for i, ladder in enumerate(strategy.ladders):
            assert ladder['units'] == expected_units[i]

    def test_update_prices(self, strategy):
        """Test price updates"""
        current_price = 50000

        strategy.update_prices(current_price)

        # Check that buy prices are below current price
        for ladder in strategy.ladders:
            assert ladder['buy_price'] < current_price
            assert ladder['usdt_cost'] > 0

    def test_get_pending_ladders(self, strategy):
        """Test pending ladders filter"""
        pending = strategy.get_pending_ladders()
        assert len(pending) == 4  # All should be pending initially

        # Mark one as active
        strategy.ladders[0]['status'] = 'active'
        pending = strategy.get_pending_ladders()
        assert len(pending) == 3

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
