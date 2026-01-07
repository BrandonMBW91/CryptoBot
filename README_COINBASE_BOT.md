# Coinbase Trading Bot - Complete Edition

A professional-grade cryptocurrency trading bot for Coinbase with a beautiful real-time dashboard, adaptive risk management, and multi-strategy analysis.

## Features

### 🎯 Core Trading Features
- **Multi-Strategy Analysis**: RSI, MACD, SMA-based technical analysis
- **Adaptive Risk Management**: Dynamic position sizing based on performance
- **Portfolio Tracking**: Complete trade history with P/L tracking
- **Market Heat Monitoring**: Real-time signal strength visualization
- **Automatic Order Execution**: Market orders with calculated sizing

### 📊 Live Dashboard
- **Real-Time Portfolio Stats**: Equity, buying power, daily P/L
- **Position Monitoring**: Track all open positions with live P/L
- **Signal Display**: Recent signals with strength indicators
- **Market Heat Map**: Visual representation of trading opportunities
- **Trade History**: Recent buy/sell executions
- **Animated Indicators**: Spinner, progress bars, heat bars

### 🛡️ Risk Management
- **Drawdown Protection**: Reduces position size after consecutive losses
- **ATR-Based Stops**: Dynamic stop-loss and take-profit levels
- **Symbol Locking**: Prevents duplicate orders
- **Position Limits**: Configurable maximum positions
- **Minimum Notional**: Ensures orders meet exchange minimums

### 🔄 Robustness
- **Retry Logic**: Exponential backoff for API failures
- **Rate Limiting**: Prevents API throttling
- **Error Recovery**: Continues running despite individual failures
- **Graceful Shutdown**: Clean exit on Ctrl+C
- **File Logging**: Rotating log files with detailed debugging

## Installation

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Create virtual environment (optional but recommended)
python -m venv Lib
source Lib/bin/activate  # On Windows: Lib\Scripts\activate
```

### Install Dependencies
```bash
pip install pandas ta coinbase-advanced-py
```

## Configuration

Edit `coinbase_config.json`:

```json
{
  "coinbase": {
    "apiKey": "organizations/{org_id}/apiKeys/{key_id}",
    "apiSecret": "-----BEGIN EC PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END EC PRIVATE KEY-----\n"
  },
  "trading": {
    "quoteCurrency": "USD",
    "maxPositionSizePercent": 5,
    "stopLossPercent": 2,
    "takeProfitPercent": 4,
    "minNotionalUsd": 10,
    "cycleSeconds": 60
  },
  "assets": {
    "crypto": [
      "BTC-USD",
      "ETH-USD",
      "SOL-USD"
    ]
  }
}
```

### API Credentials

**Option 1: Environment Variables (Recommended)**
```bash
# Windows (PowerShell)
$env:COINBASE_API_KEY = "organizations/your-org-id/apiKeys/your-key-id"
$env:COINBASE_API_SECRET = "-----BEGIN EC PRIVATE KEY-----\nYOUR_KEY\n-----END EC PRIVATE KEY-----"

# Linux/Mac
export COINBASE_API_KEY="organizations/your-org-id/apiKeys/your-key-id"
export COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR_KEY\n-----END EC PRIVATE KEY-----"
```

**Option 2: Config File**
Edit `coinbase_config.json` directly with your credentials.

## Usage

### Start the Bot
```bash
python coinbase_trading_bot_complete.py
```

### Dashboard Controls
- **Ctrl+C**: Stop the bot gracefully
- The dashboard updates automatically every second
- Analysis cycles run every 60 seconds (configurable)

## Dashboard Sections

### 1. Portfolio Status (Top Left)
- **Status**: Bot running status
- **Equity**: Total account value
- **Buying Power**: Available USD
- **Daily P/L**: Profit/Loss for the day
- **Positions**: Current open positions
- **Progress Bar**: Position capacity usage

### 2. Daily Performance (Top Right)
- **Today's Stats**: Trades, wins, losses
- **All-Time Stats**: Lifetime performance
- **Win Rates**: Success percentage
- **Total P/L**: Cumulative profit/loss
- **Activity**: Live status indicator

### 3. Open Positions (Bottom Left)
- Symbol, quantity, entry price
- Unrealized P/L in $ and %
- Visual indicators (📈 profit, 📉 loss)

### 4. Market Heat (Bottom Right)
- Symbols approaching trade threshold
- Signal direction (BUY/SELL)
- Signal strength (0-100)
- Visual heat bars and temperature icons

### 5. Recent Signals
- Last 5 trading signals generated
- Timestamp, direction, symbol
- Signal strength
- Strategy name

### 6. Recent Trades
- Last 5 executed trades
- Timestamp, action (BUY/SELL)
- Symbol and quantity

## Strategy Details

### Signal Generation
The bot uses a multi-indicator approach:

1. **RSI (Relative Strength Index)**
   - Oversold (<30): +30 strength for BUY
   - Overbought (>70): +30 strength for SELL
   - Mild oversold (<40): +15 strength for BUY
   - Mild overbought (>60): +15 strength for SELL

2. **MACD (Moving Average Convergence Divergence)**
   - Positive histogram + BUY signal: +20 strength
   - Negative histogram + SELL signal: +20 strength

3. **SMA (Simple Moving Average)**
   - Price above SMA + BUY signal: +15 strength
   - Price below SMA + SELL signal: +15 strength

**Trade Threshold**: Signals with strength ≥55 trigger trades

### Risk Management

#### Position Sizing
- Base: 5% of portfolio per position (configurable)
- Adjusted dynamically based on performance
- Minimum notional value: $10

#### Drawdown Protection
- 2 consecutive losses: Position size reduced to 3.3% (66% of base)
- 3 consecutive losses: Position size reduced to 1.65% (33% of base)
- Resets on winning trade

#### Stop Loss & Take Profit
- Dynamic calculation based on ATR (Average True Range)
- Stop Loss: 2x ATR or 2% minimum, 5% maximum
- Take Profit: 3x ATR or 4% minimum, 10% maximum

## File Structure

```
Crypto/
├── coinbase_trading_bot_complete.py  # Main bot with full features
├── coinbase_dashboard.py              # Terminal dashboard UI
├── coinbase_crypto_bot_v5_robust.py  # Robust analysis-only version
├── coinbase_config.json               # Configuration file
├── coinbase-bot.log                   # Log file (auto-created)
└── README_COINBASE_BOT.md            # This file
```

## Logging

Logs are written to `coinbase-bot.log` with automatic rotation:
- Max file size: 10MB
- Backup files: 5
- Log level: INFO (console), DEBUG (file)

## Safety Features

1. **Configuration Validation**: Checks for valid config before starting
2. **Credential Validation**: Ensures API keys are not placeholders
3. **Rate Limiting**: 100ms minimum between API requests
4. **Symbol Locking**: Prevents duplicate orders (60s cooldown)
5. **Error Isolation**: Individual symbol failures don't crash the bot
6. **Graceful Shutdown**: Handles SIGINT/SIGTERM properly

## Comparison: Analysis-Only vs Complete Bot

### Analysis-Only Bot (`v5_robust`)
- ✅ Market analysis and signal generation
- ✅ Portfolio monitoring (read-only)
- ✅ Technical indicators
- ✅ Logging and error handling
- ❌ No order execution
- ❌ No dashboard
- ❌ No trade tracking

### Complete Bot (Recommended)
- ✅ Everything from analysis-only
- ✅ **Live terminal dashboard**
- ✅ **Automatic order execution**
- ✅ **Trade tracking and P/L**
- ✅ **Adaptive risk management**
- ✅ **Position management**
- ✅ **Market heat visualization**

## Troubleshooting

### Dashboard Issues
**Problem**: Dashboard layout broken or misaligned
**Solution**:
- Ensure terminal is at least 120 characters wide
- Try resizing terminal window
- Use a terminal that supports ANSI colors (Windows Terminal, iTerm2, etc.)

**Problem**: Emojis not displaying
**Solution**: Use a modern terminal with Unicode support

### API Issues
**Problem**: "API key has not been configured"
**Solution**: Replace placeholder values in config with real credentials

**Problem**: Rate limiting errors
**Solution**: Increase `min_request_interval` in CoinbaseClient class

**Problem**: Empty candle data
**Solution**:
- Check if markets are open
- Verify product IDs are correct (e.g., "BTC-USD")
- Check Coinbase API status

### Trading Issues
**Problem**: No trades executing despite signals
**Solution**:
- Check if signal strength ≥55
- Verify sufficient buying power
- Check if symbol lock is active
- Review logs for specific errors

**Problem**: Position size too small
**Solution**: Increase `maxPositionSizePercent` in config

## Advanced Configuration

### Custom Trading Pairs
Add more crypto pairs to monitor:
```json
"assets": {
  "crypto": [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "AVAX-USD",
    "MATIC-USD"
  ]
}
```

### Adjust Risk Parameters
```json
"trading": {
  "maxPositionSizePercent": 3,    // More conservative
  "stopLossPercent": 1.5,          // Tighter stops
  "takeProfitPercent": 5,          // Higher targets
  "minNotionalUsd": 25,            // Larger minimum orders
  "cycleSeconds": 30               // More frequent analysis
}
```

### Modify Signal Threshold
In `TradingStrategy.analyze()`, change:
```python
if signal['signal'] == 'NEUTRAL' or signal['strength'] < 55:
    return None
```

To be more aggressive (lower threshold):
```python
if signal['signal'] == 'NEUTRAL' or signal['strength'] < 45:
    return None
```

## Performance Notes

- **Memory Usage**: ~50-100MB
- **CPU Usage**: Minimal (<5% on modern CPUs)
- **Network**: ~1-2 API requests per second during analysis
- **Disk I/O**: Minimal (log rotation only)

## Disclaimer

⚠️ **IMPORTANT**: This bot is for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Always test with small amounts first. Past performance does not guarantee future results. Use at your own risk.

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `coinbase-bot.log`
3. Verify configuration is correct
4. Ensure API credentials have proper permissions

---

**Happy Trading!** 🚀
