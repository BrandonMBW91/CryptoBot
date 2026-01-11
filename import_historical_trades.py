#!/usr/bin/env python3
"""
Import historical trades into the trading stats file
Use this to populate all-time stats from your Discord notifications or logs
"""

import json
from datetime import datetime

def create_trading_stats():
    """Create or update trading_stats.json with historical trades"""

    # Example trades - modify this list with your actual trade history
    historical_trades = [
        # Example format:
        # {
        #     'symbol': 'BTCUSD',
        #     'entry_price': 50000.0,
        #     'exit_price': 51000.0,
        #     'qty': 0.01,
        #     'pl': 10.0,  # Net P/L after fees
        #     'pl_percent': 2.0,
        #     'gross_pl': 10.0,
        #     'gross_pl_percent': 2.0,
        #     'entry_fee': 0.0,
        #     'exit_fee': 0.0,
        #     'timestamp': '2025-01-11T16:53:00'  # ISO format
        # },

        # Add your trades here from Discord/logs
        # You can copy the format from Discord notifications
    ]

    # Load existing stats if file exists
    try:
        with open('trading_stats.json', 'r') as f:
            data = json.load(f)
            existing_trades = data.get('all_time_trades', [])
    except FileNotFoundError:
        existing_trades = []

    # Combine with historical trades (avoid duplicates)
    all_trades = existing_trades + historical_trades

    # Save updated stats
    data = {
        'all_time_trades': all_trades,
        'last_updated': datetime.now().isoformat()
    }

    with open('trading_stats.json', 'w') as f:
        json.dump(data, f, indent=2)

    wins = [t for t in all_trades if t.get('pl', 0) > 0]
    losses = [t for t in all_trades if t.get('pl', 0) <= 0]
    total_pl = sum(t.get('pl', 0) for t in all_trades)
    win_rate = (len(wins) / len(all_trades) * 100) if all_trades else 0

    print(f"\nTrading Stats Updated!")
    print(f"=" * 50)
    print(f"Total Trades: {len(all_trades)}")
    print(f"Wins: {len(wins)}")
    print(f"Losses: {len(losses)}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total P/L: ${total_pl:.2f}")
    print(f"\nStats saved to trading_stats.json")
    print(f"Restart the bot to see updated all-time stats")

if __name__ == '__main__':
    print("Historical Trade Import Tool")
    print("=" * 50)
    print("\nEdit this file to add your historical trades,")
    print("then run it to update trading_stats.json")
    print("\nExample trade format is shown in the code.")

    # Uncomment the line below after adding your trades
    # create_trading_stats()

    print("\nUncomment the 'create_trading_stats()' call to execute.")
