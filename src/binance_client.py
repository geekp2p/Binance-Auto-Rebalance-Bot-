"""
Binance API Client Wrapper
"""
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class BinanceClient:
    def __init__(self, testnet=False):
        load_dotenv()

        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')

        if not api_key or not api_secret:
            raise ValueError("Binance API credentials not found in .env file")

        self.client = Client(api_key, api_secret, testnet=testnet)
        self.testnet = testnet

        logger.info(f"Binance client initialized (testnet={testnet})")

    def get_current_price(self, symbol):
        """Get current market price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            raise

    def get_account_balance(self, asset='USDT'):
        """Get account balance for specific asset"""
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return {
                'free': float(balance['free']),
                'locked': float(balance['locked']),
                'total': float(balance['free']) + float(balance['locked'])
            }
        except BinanceAPIException as e:
            logger.error(f"Error getting balance for {asset}: {e}")
            raise

    def create_limit_order(self, symbol, side, quantity, price):
        """Create a limit order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,  # 'BUY' or 'SELL'
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            logger.info(f"Order created: {side} {quantity} {symbol} @ {price}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error creating order: {e}")
            raise

    def create_market_order(self, symbol, side, quantity):
        """Create a market order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Market order created: {side} {quantity} {symbol}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error creating market order: {e}")
            raise

    def get_open_orders(self, symbol=None):
        """Get all open orders"""
        try:
            return self.client.get_open_orders(symbol=symbol)
        except BinanceAPIException as e:
            logger.error(f"Error getting open orders: {e}")
            raise

    def cancel_order(self, symbol, order_id):
        """Cancel an order"""
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order cancelled: {order_id}")
            return result
        except BinanceAPIException as e:
            logger.error(f"Error cancelling order: {e}")
            raise

    def get_historical_klines(self, symbol, interval, start_str, end_str=None):
        """Get historical klines/candlestick data"""
        try:
            klines = self.client.get_historical_klines(
                symbol, interval, start_str, end_str
            )
            return klines
        except BinanceAPIException as e:
            logger.error(f"Error getting historical data: {e}")
            raise
