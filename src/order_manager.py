"""
Order Manager - Handle order placement and tracking
"""
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, binance_client, portfolio):
        self.client = binance_client
        self.portfolio = portfolio
        self.active_orders = {}  # {order_id: order_details}

    def place_ladder_buy_orders(self, strategy, current_price):
        """Place buy orders for all pending ladders, respecting balance and exchange filters"""
        orders_placed = []
        skipped_balance = 0
        skipped_price_filter = 0

        # Get current available USDT balance from exchange
        try:
            balance = self.client.get_account_balance('USDT')
            available_usdt = balance['free']
        except Exception as e:
            logger.error(f"Cannot fetch USDT balance, aborting order placement: {e}")
            return orders_placed

        symbol = strategy.config['pair']

        for ladder in strategy.get_pending_ladders():
            if ladder['buy_price'] >= current_price:
                continue  # Only place orders below current price

            # Estimate order cost (price × quantity)
            estimated_cost = ladder['buy_price'] * ladder['btc_amount']

            # Check if we have enough balance
            if estimated_cost > available_usdt:
                skipped_balance += 1
                logger.warning(f"Skipping level {ladder['level']}: need ${estimated_cost:.2f} "
                             f"but only ${available_usdt:.2f} USDT available")
                continue

            # Check PERCENT_PRICE_BY_SIDE filter
            ok, reason = self.client.check_percent_price_filter(symbol, 'BUY', ladder['buy_price'])
            if not ok:
                skipped_price_filter += 1
                logger.warning(f"Skipping level {ladder['level']}: {reason}")
                continue

            try:
                order = self.client.create_limit_order(
                    symbol=symbol,
                    side='BUY',
                    quantity=ladder['btc_amount'],
                    price=ladder['buy_price']
                )

                self.active_orders[order['orderId']] = {
                    'strategy': strategy.config['name'],
                    'level': ladder['level'],
                    'type': 'BUY',
                    'order': order,
                    'ladder': ladder
                }

                orders_placed.append(order)
                available_usdt -= estimated_cost  # Track remaining balance
                logger.info(f"Buy order placed: Level {ladder['level']} @ ${ladder['buy_price']:.2f}")

            except Exception as e:
                logger.error(f"Failed to place buy order for level {ladder['level']}: {e}")

        # Summary
        total = len(strategy.get_pending_ladders())
        logger.info(f"Order placement summary: {len(orders_placed)}/{total} placed"
                    + (f", {skipped_balance} skipped (insufficient balance)" if skipped_balance else "")
                    + (f", {skipped_price_filter} skipped (price filter)" if skipped_price_filter else ""))

        return orders_placed

    def place_sell_order(self, strategy, ladder):
        """Place sell order for an active ladder"""
        try:
            order = self.client.create_limit_order(
                symbol=strategy.config['pair'],
                side='SELL',
                quantity=ladder['btc_amount'],
                price=ladder['sell_price']
            )

            self.active_orders[order['orderId']] = {
                'strategy': strategy.config['name'],
                'level': ladder['level'],
                'type': 'SELL',
                'order': order,
                'ladder': ladder
            }

            logger.info(f"Sell order placed: Level {ladder['level']} @ ${ladder['sell_price']:.2f}")
            return order

        except Exception as e:
            logger.error(f"Failed to place sell order for level {ladder['level']}: {e}")
            return None

    def check_filled_orders(self):
        """Check which orders have been filled"""
        filled_orders = []

        for order_id, order_data in list(self.active_orders.items()):
            try:
                # Query order status
                status = self.client.client.get_order(
                    symbol=order_data['order']['symbol'],
                    orderId=order_id
                )

                if status['status'] == 'FILLED':
                    filled_orders.append(order_data)

                    # Update portfolio
                    if order_data['type'] == 'BUY':
                        self.portfolio.add_position(
                            strategy_name=order_data['strategy'],
                            ladder_level=order_data['level'],
                            buy_price=float(status['price']),
                            quantity=float(status['executedQty']),
                            cost=float(status['cummulativeQuoteQty'])
                        )

                        # Update ladder status
                        order_data['ladder']['status'] = 'active'

                        logger.info(f"Buy order filled: Level {order_data['level']}")

                    elif order_data['type'] == 'SELL':
                        self.portfolio.close_position(
                            strategy_name=order_data['strategy'],
                            ladder_level=order_data['level'],
                            sell_price=float(status['price']),
                            quantity=float(status['executedQty'])
                        )

                        # Update ladder status
                        order_data['ladder']['status'] = 'closed'

                        logger.info(f"Sell order filled: Level {order_data['level']}")

                    # Remove from active orders
                    del self.active_orders[order_id]

            except Exception as e:
                logger.error(f"Error checking order {order_id}: {e}")

        return filled_orders

    def cancel_all_orders(self, strategy_name=None):
        """Cancel all active orders (optionally for specific strategy)"""
        cancelled = []

        for order_id, order_data in list(self.active_orders.items()):
            if strategy_name is None or order_data['strategy'] == strategy_name:
                try:
                    self.client.cancel_order(
                        symbol=order_data['order']['symbol'],
                        order_id=order_id
                    )
                    cancelled.append(order_id)
                    del self.active_orders[order_id]
                except Exception as e:
                    logger.error(f"Failed to cancel order {order_id}: {e}")

        logger.info(f"Cancelled {len(cancelled)} orders")
        return cancelled
