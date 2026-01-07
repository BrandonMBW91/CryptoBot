# Quick Start Guide - Coinbase Trading Bot

Get your bot running in 5 minutes!

## Step 1: Install Dependencies (1 min)

```bash
pip install pandas ta coinbase-advanced-py
```

## Step 2: Configure API Credentials (2 min)

### Get Your Coinbase API Keys
1. Go to https://www.coinbase.com/settings/api
2. Create new API key with trading permissions
3. Save your API Key ID and Private Key

### Set Environment Variables (Recommended)

**Windows (PowerShell):**
```powershell
$env:COINBASE_API_KEY = "organizations/your-org-id/apiKeys/your-key-id"
$env:COINBASE_API_SECRET = "-----BEGIN EC PRIVATE KEY-----`nYOUR_PRIVATE_KEY_HERE`n-----END EC PRIVATE KEY-----"
```

**Windows (Command Prompt):**
```cmd
set COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
set COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END EC PRIVATE KEY-----
```

**Linux/Mac:**
```bash
export COINBASE_API_KEY="organizations/your-org-id/apiKeys/your-key-id"
export COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END EC PRIVATE KEY-----"
```

### Or Edit Config File

Open `coinbase_config.json` and replace placeholders:
```json
{
  "coinbase": {
    "apiKey": "organizations/12345678-1234-1234-1234-123456789abc/apiKeys/abcd1234-5678-90ab-cdef-1234567890ab",
    "apiSecret": "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIB00GncuS4jrYlPMWzYTJk9BDrv/kU1AwTxf99tEYwFhoAoGCCqGSM49\nAwEHoUQDQgAEPLEBMMktPvk1uTNyW+r+J/MRlmdPLf8VnTH7QsS9H2QpcM6H9iVh\n7aK8k2VR3mnOslcQCxLygy8pXNHw2g3JWQ==\n-----END EC PRIVATE KEY-----"
  }
}
```

## Step 3: Configure Trading Pairs (30 sec)

Edit `coinbase_config.json` - choose your crypto:
```json
{
  "assets": {
    "crypto": [
      "BTC-USD",
      "ETH-USD",
      "SOL-USD"
    ]
  }
}
```

**Available pairs**: BTC-USD, ETH-USD, SOL-USD, AVAX-USD, MATIC-USD, LINK-USD, UNI-USD, and more

## Step 4: Run the Bot (30 sec)

```bash
python coinbase_trading_bot_complete.py
```

That's it! You should see the dashboard:

```
╔════════════════════════════════════════════════════╗
║  🚀 COINBASE TRADING BOT v2.0 - LIVE TRADING 🚀  ║
╚════════════════════════════════════════════════════╝

╔═══════════════════════════════╦═══════════════════════════════╗
║ 💰 PORTFOLIO STATUS           ║ 📊 DAILY PERFORMANCE         ║
╠═══════════════════════════════╬═══════════════════════════════╣
║ Status: ✅ ACTIVE             ║ Today: 0 trades               ║
║ Equity: $1,000.00             ║ All-Time: 0 trades            ║
║ Buying Power: $1,000.00       ║ Win Rate: 0.0%                ║
║ Daily P/L: ▲ $0.00 (+0.00%)   ║ Activity: ⠋ Analyzing...     ║
╚═══════════════════════════════╩═══════════════════════════════╝
```

## Step 5: Monitor and Control

### Dashboard Updates
- **Portfolio**: Updates every analysis cycle (60s)
- **Signals**: Shows as they're generated
- **Trades**: Displays when executed
- **Market Heat**: Updates in real-time

### Stop the Bot
Press **Ctrl+C** for graceful shutdown

### View Logs
```bash
# Real-time log monitoring
tail -f coinbase-bot.log

# Windows
Get-Content coinbase-bot.log -Wait
```

## Default Settings

The bot starts with safe defaults:
- **Position Size**: 5% of portfolio per trade
- **Stop Loss**: 2% (adjusted by ATR)
- **Take Profit**: 4% (adjusted by ATR)
- **Minimum Order**: $10
- **Analysis Cycle**: Every 60 seconds
- **Signal Threshold**: 55/100 strength

## Testing Tips

### Start Small
```json
{
  "trading": {
    "maxPositionSizePercent": 1,  // Only 1% per trade
    "minNotionalUsd": 10           // Small orders
  }
}
```

### Test with One Pair
```json
{
  "assets": {
    "crypto": [
      "BTC-USD"  // Just one for testing
    ]
  }
}
```

### Paper Trading First
- Test with small amounts ($50-100)
- Watch for 24-48 hours
- Verify signals make sense
- Check order execution

## Troubleshooting Quick Fixes

### "API key has not been configured"
➜ Replace placeholder values in config with real credentials

### Dashboard not displaying properly
➜ Resize terminal to at least 120 characters wide

### No signals generating
➜ Wait for market volatility; signals require strength ≥55

### Orders not executing
➜ Check buying power and minimum order size ($10 default)

### Rate limit errors
➜ Reduce number of crypto pairs being monitored

## Next Steps

Once running:

1. **Monitor for 24 hours** - Watch signal generation and market heat
2. **Review logs** - Check `coinbase-bot.log` for any errors
3. **Adjust settings** - Tune risk parameters based on your strategy
4. **Scale gradually** - Increase position sizes slowly
5. **Track performance** - Monitor win rate and P/L

## Safety Reminders

⚠️ **Important:**
- Start with small amounts
- Never risk more than you can afford to lose
- Keep API keys secure
- Monitor bot regularly
- Review trades daily
- Stop bot if behavior is unexpected

## Configuration Examples

### Conservative (Low Risk)
```json
{
  "trading": {
    "maxPositionSizePercent": 2,
    "stopLossPercent": 1.5,
    "takeProfitPercent": 3,
    "minNotionalUsd": 25
  }
}
```

### Moderate (Balanced)
```json
{
  "trading": {
    "maxPositionSizePercent": 5,
    "stopLossPercent": 2,
    "takeProfitPercent": 4,
    "minNotionalUsd": 10
  }
}
```

### Aggressive (Higher Risk)
```json
{
  "trading": {
    "maxPositionSizePercent": 10,
    "stopLossPercent": 3,
    "takeProfitPercent": 6,
    "minNotionalUsd": 10
  }
}
```

## Support

Need help?
1. Check `README_COINBASE_BOT.md` for detailed documentation
2. Review `FEATURES_COMPARISON.md` for feature details
3. Check logs: `coinbase-bot.log`
4. Verify configuration is correct

---

**You're all set!** The bot will analyze markets, generate signals, and execute trades automatically. Happy trading! 🚀
