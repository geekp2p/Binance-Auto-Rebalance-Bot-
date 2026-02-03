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
        truncated = False

        for i in range(num_ladders):
            fib = fibonacci[i]
            gap = base_gap * fib
            cumulative_gap += gap

            # Stop if buy price would go to zero or negative
            if cumulative_gap >= 1.0:
                truncated = True
                logger.warning(f"Truncating ladders at level {-(i+1)}: cumulative gap {cumulative_gap:.2%} "
                             f"would produce negative prices. Only {i} of {num_ladders} levels created.")
                break

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

        logger.info(f"Calculated {len(self.ladders)} ladders with total swing: "
                    f"{self.ladders[-1]['cumulative_gap_percent']:.2%}" if self.ladders else "No ladders calculated")

    def update_prices(self, current_price):
        """Update ladder prices based on current market price"""
        # Calculate base USDT per unit at level -1 for true Martingale
        first_ladder_buy_price = current_price * self.ladders[0]['buy_price_multiplier']
        unit_size_key = f"unit_size_{self.config['pair'][:3].lower()}"
        unit_size = self.config['ladder_config'].get(unit_size_key, 0.01)
        base_usdt_per_unit = first_ladder_buy_price * unit_size

        for ladder in self.ladders:
            ladder['buy_price'] = current_price * ladder['buy_price_multiplier']
            ladder['sell_price'] = current_price * ladder['sell_price_multiplier']

            if ladder['buy_price'] <= 0 or ladder['sell_price'] <= 0:
                logger.error(f"Invalid price at level {ladder['level']}: "
                           f"buy=${ladder['buy_price']:.2f}, sell=${ladder['sell_price']:.2f}. Skipping.")
                continue

            # True Martingale: USDT cost doubles each level (units × base_usdt_per_unit)
            ladder['usdt_cost'] = ladder['units'] * base_usdt_per_unit
            # Calculate BTC amount based on USDT cost and buy price
            ladder['btc_amount'] = ladder['usdt_cost'] / ladder['buy_price']

    def get_active_ladders(self):
        """Get ladders that are currently active (bought but not sold)"""
        return [l for l in self.ladders if l['status'] == 'active']

    def get_pending_ladders(self):
        """Get ladders that are waiting to be triggered"""
        return [l for l in self.ladders if l['status'] == 'pending']

    def all_ladders_closed(self):
        """Check if all ladders have completed their cycle (all closed)"""
        return all(l['status'] == 'closed' for l in self.ladders if l['status'] != 'pending') and \
               any(l['status'] == 'closed' for l in self.ladders)

    def reset_ladders(self):
        """Reset all closed ladders back to pending for a new cycle"""
        reset_count = 0
        for ladder in self.ladders:
            if ladder['status'] == 'closed':
                ladder['status'] = 'pending'
                reset_count += 1
        logger.info(f"Reset {reset_count} ladders to pending for new cycle")

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
