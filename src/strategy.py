"""
Strategy Configuration and Ladder Calculation
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class Strategy:
    def __init__(self, config_path):
        self.config = self._load_config(config_path)
        self.ladders = []
        self._calculate_ladders()

    def _load_config(self, config_path):
        """Load strategy configuration from JSON"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded strategy: {config['name']}")
        return config

    def _calculate_ladders(self):
        """Calculate ladder levels based on Fibonacci gaps"""
        ladder_config = self.config['ladder_config']
        base_gap = ladder_config['base_gap']
        fibonacci = ladder_config['fibonacci']
        num_ladders = ladder_config['ladders']

        # Placeholder starting price (will be updated with real price)
        starting_price = 50000  # This will be set dynamically

        cumulative_gap = 0
        self.ladders = []

        for i in range(num_ladders):
            fib = fibonacci[i]
            gap = base_gap * fib
            cumulative_gap += gap

            ladder = {
                'level': -(i + 1),
                'fibonacci': fib,
                'gap_percent': gap,
                'cumulative_gap_percent': cumulative_gap,
                'buy_price_multiplier': 1 - cumulative_gap,
                'sell_price_multiplier': 1 - (cumulative_gap - gap) if i > 0 else 1.0,
                'units': 2 ** i,  # Martingale: 1, 2, 4, 8, 16, 32...
                'status': 'pending'
            }

            self.ladders.append(ladder)

        logger.info(f"Calculated {num_ladders} ladders with total swing: {cumulative_gap:.2%}")

    def update_prices(self, current_price):
        """Update ladder prices based on current market price"""
        for ladder in self.ladders:
            ladder['buy_price'] = current_price * ladder['buy_price_multiplier']
            ladder['sell_price'] = current_price * ladder['sell_price_multiplier']

            # Calculate unit size in base currency
            unit_size_key = f"unit_size_{self.config['pair'][:3].lower()}"
            unit_size = self.config['ladder_config'].get(unit_size_key, 0.01)
            ladder['btc_amount'] = ladder['units'] * unit_size
            ladder['usdt_cost'] = ladder['btc_amount'] * ladder['buy_price']

    def get_active_ladders(self):
        """Get ladders that are currently active (bought but not sold)"""
        return [l for l in self.ladders if l['status'] == 'active']

    def get_pending_ladders(self):
        """Get ladders that are waiting to be triggered"""
        return [l for l in self.ladders if l['status'] == 'pending']

    def calculate_required_capital(self):
        """Calculate total capital required if all ladders are triggered"""
        return sum(ladder['usdt_cost'] for ladder in self.ladders)

    def to_dict(self):
        """Export strategy as dictionary"""
        return {
            'name': self.config['name'],
            'pair': self.config['pair'],
            'ladders': self.ladders,
            'total_swing': self.ladders[-1]['cumulative_gap_percent'],
            'required_capital': self.calculate_required_capital()
        }
