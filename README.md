# Binance Auto Rebalance Bot

Advanced multi-strategy cryptocurrency rebalancing bot using Fibonacci-Martingale approach.

## Features

- Multi-coin support (BTC, ETH, BNB, etc.)
- Multi-strategy execution (Conservative, Balanced, Aggressive)
- Fibonacci-based ladder spacing
- Martingale position sizing
- Comprehensive backtesting
- Fee calculation (0.1% Binance)
- Stop-loss protection
- Real-time portfolio tracking
- Detailed logging

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/binance-auto-rebalance.git
cd binance-auto-rebalance

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Binance API keys
```

## Configuration

### Strategy Configuration

Edit `config/strategies/*.json` files:

```json
{
  "name": "BTC Conservative",
  "pair": "BTC/USDT",
  "base_gap": 0.01,
  "ladders": 6,
  "unit_size": 0.01,
  "fibonacci": [1, 1, 2, 3, 5, 8],
  "safety_multiplier": 1.5,
  "stop_loss": -0.25
}
```

## Usage

### Live Trading

```bash
python main.py --mode live --strategies btc_conservative eth_balanced
```

### Backtesting

```bash
python main.py --mode backtest --strategies btc_conservative --start 2024-01-01 --end 2024-12-31
```

### Paper Trading

```bash
python main.py --mode paper --strategies all
```

## Strategy Examples

### Conservative (Low Risk)

- Base Gap: 1.0%
- Ladders: 6
- Total Swing: 20%
- Expected ROI: 5-10% per cycle

### Balanced (Medium Risk)

- Base Gap: 0.75%
- Ladders: 8
- Total Swing: 25%
- Expected ROI: 10-15% per cycle

### Aggressive (High Risk)

- Base Gap: 0.8%
- Ladders: 10
- Total Swing: 114.4%
- Expected ROI: 15-25% per cycle

## Project Structure

```
binance-auto-rebalance/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   ├── strategies/
│   │   ├── btc_conservative.json
│   │   ├── eth_balanced.json
│   │   └── bnb_aggressive.json
│   └── global_config.json
├── src/
│   ├── __init__.py
│   ├── binance_client.py
│   ├── strategy.py
│   ├── order_manager.py
│   ├── martingale.py
│   └── portfolio.py
├── backtest/
│   ├── __init__.py
│   ├── backtester.py
│   └── data_loader.py
├── tests/
│   ├── test_strategy.py
│   └── test_martingale.py
├── data/
│   └── historical/
├── logs/
└── main.py
```

## Example Output

```
=== BACKTEST REPORT ===
{
  "strategy": "BTC Conservative",
  "period": {
    "start": "2024-01-01",
    "end": "2024-12-31",
    "days": 365
  },
  "capital": {
    "initial": 10000.0,
    "final": 11245.67,
    "profit": 1245.67,
    "roi_percent": 12.46
  },
  "trades": {
    "total": 48,
    "winning": 46,
    "losing": 2,
    "win_rate": 95.83,
    "avg_profit": 25.95
  }
}
```

## Risk Warning

Cryptocurrency trading involves substantial risk. This bot is for educational purposes. Always:

- Start with small capital
- Use testnet first
- Monitor positions regularly
- Set appropriate stop-losses
- Never invest more than you can afford to lose

## License

MIT
