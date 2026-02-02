"""
Main Entry Point for Binance Auto Rebalance Bot
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json

from src.binance_client import BinanceClient
from src.strategy import Strategy
from src.portfolio import Portfolio
from src.order_manager import OrderManager
from src.martingale import MartingaleCalculator
from backtest.backtester import Backtester
from backtest.data_loader import DataLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_strategies(strategy_names):
    """Load strategy configurations"""
    strategies = []
    config_dir = Path('config/strategies')

    if 'all' in strategy_names:
        # Load all enabled strategies
        for config_file in config_dir.glob('*.json'):
            strategy = Strategy(config_file)
            if strategy.config.get('enabled', True):
                strategies.append(strategy)
    else:
        # Load specific strategies
        for name in strategy_names:
            config_file = config_dir / f"{name}.json"
            if config_file.exists():
                strategies.append(Strategy(config_file))
            else:
                logger.warning(f"Strategy config not found: {config_file}")

    logger.info(f"Loaded {len(strategies)} strategies")
    return strategies


def run_backtest(args):
    """Run backtest mode"""
    logger.info("=== BACKTEST MODE ===")

    # Initialize Binance client (for historical data only)
    client = BinanceClient(testnet=True)
    data_loader = DataLoader(client)

    # Load strategies
    strategies = load_strategies(args.strategies)

    for strategy in strategies:
        logger.info(f"\n{'='*60}")
        logger.info(f"Backtesting: {strategy.config['name']}")
        logger.info(f"{'='*60}")

        # Load historical data
        symbol = strategy.config['pair']
        data = data_loader.load_historical_data(
            symbol=symbol,
            interval='1h',
            start_date=args.start,
            end_date=args.end
        )

        # Run backtest
        backtester = Backtester(strategy, data)
        report = backtester.run()

        # Print report
        print(json.dumps(report, indent=2))

        # Save report
        report_file = f"logs/backtest_{strategy.config['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backtester.save_report(report_file)


def run_live_trading(args):
    """Run live trading mode"""
    logger.info("=== LIVE TRADING MODE ===")
    logger.warning("WARNING: LIVE TRADING IS ACTIVE - REAL MONEY AT RISK")

    # Initialize components
    client = BinanceClient(testnet=False)

    # Get total capital
    balance = client.get_account_balance('USDT')
    total_capital = balance['free']
    logger.info(f"Available capital: ${total_capital:.2f} USDT")

    portfolio = Portfolio(total_capital)
    order_manager = OrderManager(client, portfolio)

    # Load strategies
    strategies = load_strategies(args.strategies)

    # Initialize each strategy with current prices
    for strategy in strategies:
        current_price = client.get_current_price(strategy.config['pair'])
        strategy.update_prices(current_price)
        logger.info(f"Initialized {strategy.config['name']} at ${current_price:.2f}")

        # Place initial ladder orders
        order_manager.place_ladder_buy_orders(strategy, current_price)

    # Main trading loop
    logger.info("Starting trading loop...")
    try:
        while True:
            # Check filled orders
            filled = order_manager.check_filled_orders()

            if filled:
                logger.info(f"Processed {len(filled)} filled orders")

                # Place corresponding sell orders for filled buys
                for order_data in filled:
                    if order_data['type'] == 'BUY':
                        # Find the strategy
                        for strategy in strategies:
                            if strategy.config['name'] == order_data['strategy']:
                                order_manager.place_sell_order(strategy, order_data['ladder'])

            # Update portfolio statistics
            current_prices = {}
            for strategy in strategies:
                symbol = strategy.config['pair']
                current_prices[symbol] = client.get_current_price(symbol)

            stats = portfolio.get_statistics(current_prices)

            if len(filled) > 0:  # Only log when there's activity
                logger.info(f"Portfolio: ${stats['total_value']:.2f} | "
                           f"P&L: ${stats['total_pnl']:.2f} ({stats['roi_percent']:.2f}%) | "
                           f"Open: {stats['num_open_positions']} | "
                           f"Trades: {stats['num_trades']}")

            # Sleep before next iteration
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
        order_manager.cancel_all_orders()
        logger.info("All orders cancelled")

        # Print final statistics
        stats = portfolio.get_statistics(current_prices)
        print(f"\n{'='*60}")
        print("FINAL STATISTICS")
        print(f"{'='*60}")
        print(json.dumps(stats, indent=2))


def run_paper_trading(args):
    """Run paper trading mode (simulated with live data)"""
    logger.info("=== PAPER TRADING MODE ===")

    # Similar to live trading but with simulated orders
    client = BinanceClient(testnet=True)

    logger.info("Paper trading uses testnet - no real money at risk")
    run_live_trading(args)


def main():
    parser = argparse.ArgumentParser(description='Binance Auto Rebalance Bot')
    parser.add_argument('--mode', choices=['live', 'paper', 'backtest'], required=True,
                       help='Trading mode')
    parser.add_argument('--strategies', nargs='+', required=True,
                       help='Strategy names or "all"')
    parser.add_argument('--start', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='Backtest end date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Create necessary directories
    Path('logs').mkdir(exist_ok=True)
    Path('data/historical').mkdir(parents=True, exist_ok=True)

    # Run appropriate mode
    if args.mode == 'backtest':
        if not args.start or not args.end:
            parser.error("Backtest mode requires --start and --end dates")
        run_backtest(args)
    elif args.mode == 'live':
        run_live_trading(args)
    elif args.mode == 'paper':
        run_paper_trading(args)


if __name__ == '__main__':
    main()
