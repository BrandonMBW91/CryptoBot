# Kraken Trading Bot - Quick Start

## You're All Set! 🚀

Your Kraken bot is configured and ready to run with your API credentials.

## Run the Bot

```bash
python kraken_trading_bot.py
```

## What You'll See

A beautiful live dashboard with:
- 📊 Real-time portfolio tracking
- 📈 Open positions with P/L
- 🔥 Market heat visualization
- 🎯 Trading signals
- 💼 Trade history
- 📉 Performance statistics

## Trading Pairs

Currently monitoring (Kraken format):
- **XXBTZUSD** - Bitcoin/USD
- **XETHZUSD** - Ethereum/USD
- **SOLUSD** - Solana/USD

### To Add More Pairs

Edit `kraken_config.json`:
```json
"assets": {
  "crypto": [
    "XXBTZUSD",
    "XETHZUSD",
    "SOLUSD",
    "ADAUSD",     // Cardano
    "MATICUSD",   // Polygon
    "AVAXUSD"     // Avalanche
  ]
}
```

**Common Kraken Pair Names:**
- Bitcoin: `XXBTZUSD` or `XBTUSD`
- Ethereum: `XETHZUSD` or `ETHUSD`
- Solana: `SOLUSD`
- Cardano: `ADAUSD`
- Polygon: `MATICUSD`
- Avalanche: `AVAXUSD`
- Polkadot: `DOTUSD`

## Bot Settings

Current configuration in `kraken_config.json`:

```json
{
  "trading": {
    "maxPositionSizePercent": 5,    // 5% of portfolio per trade
    "stopLossPercent": 2,            // 2% stop loss
    "takeProfitPercent": 4,          // 4% take profit
    "minNotionalUsd": 10,            // $10 minimum order
    "cycleSeconds": 60               // Analyze every 60 seconds
  }
}
```

### Conservative Settings (Lower Risk)
```json
{
  "maxPositionSizePercent": 2,
  "stopLossPercent": 1.5,
  "takeProfitPercent": 3
}
```

### Aggressive Settings (Higher Risk)
```json
{
  "maxPositionSizePercent": 10,
  "stopLossPercent": 3,
  "takeProfitPercent": 6
}
```

## How It Works

### Signal Generation
The bot analyzes each crypto pair using:
- **RSI** (Relative Strength Index) - Overbought/oversold
- **MACD** (Moving Average Convergence Divergence) - Momentum
- **SMA** (Simple Moving Average) - Trend direction

Signals with strength ≥55 trigger automatic trades.

### Risk Management
- **Adaptive Position Sizing** - Reduces position size after losses
- **Drawdown Protection** - Automatically scales back after 2-3 consecutive losses
- **Symbol Locking** - Prevents duplicate orders (60s cooldown)
- **ATR-Based Stops** - Dynamic stop-loss and take-profit based on volatility

### Dashboard Controls
- **Ctrl+C** - Stop the bot gracefully
- **Auto-refresh** - Dashboard updates every second
- **Analysis cycle** - Runs every 60 seconds (configurable)

## Logs

Check `kraken-bot.log` for detailed activity:
```bash
# View real-time logs
tail -f kraken-bot.log

# Windows
Get-Content kraken-bot.log -Wait
```

## Safety Features

✅ **Configuration Validation** - Verifies settings before starting
✅ **API Error Handling** - Continues running despite temporary failures
✅ **Rate Limiting** - Respects Kraken API limits
✅ **Graceful Shutdown** - Clean exit on Ctrl+C
✅ **File Logging** - Complete audit trail with rotation

## Kraken API Notes

- **Rate Limits**: 1 second between requests (built into bot)
- **OHLC Interval**: 5-minute candles for analysis
- **Order Type**: Market orders (instant execution)
- **Pair Format**: Kraken uses specific pair names (XXBTZUSD, not BTC-USD)

## Troubleshooting

### "Configuration error: API key..."
➜ API credentials in config file are invalid or missing permissions

### "HTTP Error: 401"
➜ API key/secret incorrect or API key doesn't have trading permissions

### "Rate limit exceeded"
➜ Bot has rate limiting built-in, but check if you're running multiple instances

### Empty dashboard or no data
➜ Check Kraken API status and verify pair names are correct

### No trades executing
➜ Check signal strength (must be ≥55), verify buying power, review logs

## Testing Tips

1. **Start Small** - Begin with 1-2% position sizes
2. **Monitor First** - Watch for 24 hours before scaling up
3. **Check Signals** - Verify signals make sense for market conditions
4. **Review Logs** - Look for errors or issues
5. **Test Pairs** - Start with 1-2 pairs, expand gradually

## Performance Expectations

- **Memory**: ~50-100MB
- **CPU**: <5%
- **Network**: ~1-2 API calls per minute per pair
- **Disk**: ~1MB logs per day

## Comparison to Coinbase Bot

| Feature | Kraken Bot | Coinbase Bot |
|---------|-----------|--------------|
| Dashboard | ✅ Same | ✅ Same |
| Strategy | ✅ Identical | ✅ Identical |
| Risk Mgmt | ✅ Identical | ✅ Identical |
| API Format | Kraken REST | Coinbase Advanced |
| Pair Names | XXBTZUSD | BTC-USD |
| Rate Limit | 1 req/sec | 10 req/sec |

## Support

- **Logs**: Check `kraken-bot.log`
- **Config**: Verify `kraken_config.json`
- **Kraken Status**: https://status.kraken.com/
- **API Docs**: https://docs.kraken.com/rest/

---

## Disclaimer

⚠️ **IMPORTANT**: This bot is for educational purposes. Cryptocurrency trading involves substantial risk. Test with small amounts first. Past performance doesn't guarantee future results. Use at your own risk.

---

**Happy Trading!** 🚀

Your bot is ready to go with your Kraken credentials already configured!
