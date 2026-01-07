#!/usr/bin/env python3
"""
Discord Notifier for Trading Bot
Sends trade notifications, errors, and daily summaries
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Discord webhook notifier"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url and webhook_url != "YOUR_DISCORD_WEBHOOK_URL")

    def _send_webhook(self, embed: Dict) -> bool:
        """Send webhook to Discord"""
        if not self.enabled:
            return False

        try:
            payload = {"embeds": [embed]}
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    def send_trade_notification(self, trade_type: str, symbol: str, qty: float,
                               price: float, strength: int, confirmations: list) -> bool:
        """Send trade notification"""

        # Color based on trade type
        color = 0x00FF00 if trade_type == "BUY" else 0xFF0000  # Green for BUY, Red for SELL

        # Emoji
        emoji = "📈" if trade_type == "BUY" else "📉"

        # Confirmation text
        conf_text = "\n".join([f"✓ {conf}" for conf in confirmations[:5]])

        embed = {
            "title": f"{emoji} {trade_type} Signal Executed",
            "color": color,
            "fields": [
                {"name": "Symbol", "value": symbol, "inline": True},
                {"name": "Quantity", "value": f"{qty:.4f}", "inline": True},
                {"name": "Price", "value": f"${price:.2f}", "inline": True},
                {"name": "Signal Strength", "value": f"{strength}/100", "inline": True},
                {"name": "Position Value", "value": f"${qty * price:.2f}", "inline": True},
                {"name": "Confirmations", "value": conf_text or "None", "inline": False}
            ],
            "footer": {"text": "Kraken Trading Bot"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)

    def send_position_closed(self, symbol: str, qty: float, entry_price: float,
                            exit_price: float, pl: float, pl_percent: float) -> bool:
        """Send position closed notification"""

        # Color based on profit/loss
        color = 0x00FF00 if pl > 0 else 0xFF0000

        # Emoji
        emoji = "✅" if pl > 0 else "❌"
        result = "WIN" if pl > 0 else "LOSS"

        embed = {
            "title": f"{emoji} Position Closed - {result}",
            "color": color,
            "fields": [
                {"name": "Symbol", "value": symbol, "inline": True},
                {"name": "Quantity", "value": f"{qty:.4f}", "inline": True},
                {"name": "Entry Price", "value": f"${entry_price:.2f}", "inline": True},
                {"name": "Exit Price", "value": f"${exit_price:.2f}", "inline": True},
                {"name": "Profit/Loss", "value": f"${pl:+.2f}", "inline": True},
                {"name": "P/L %", "value": f"{pl_percent:+.2f}%", "inline": True}
            ],
            "footer": {"text": "Kraken Trading Bot"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)

    def send_error_alert(self, error_type: str, message: str, symbol: Optional[str] = None) -> bool:
        """Send error alert"""

        embed = {
            "title": "⚠️ Error Alert",
            "color": 0xFFAA00,  # Orange
            "fields": [
                {"name": "Error Type", "value": error_type, "inline": True},
                {"name": "Symbol", "value": symbol or "N/A", "inline": True},
                {"name": "Message", "value": message[:1000], "inline": False}
            ],
            "footer": {"text": "Kraken Trading Bot"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)

    def send_daily_summary(self, stats: Dict, portfolio: Dict) -> bool:
        """Send daily summary"""

        # Calculate metrics
        win_rate = stats.get('win_rate', 0)
        total_trades = stats.get('total_trades', 0)
        winning_trades = stats.get('winning_trades', 0)
        losing_trades = stats.get('losing_trades', 0)
        total_pl = stats.get('total_pl', 0)

        equity = portfolio.get('equity', 0)
        daily_pl = portfolio.get('daily_pl', 0)
        daily_pl_percent = portfolio.get('daily_pl_percent', 0)
        positions = portfolio.get('positions', 0)

        # Color based on daily P/L
        color = 0x00FF00 if daily_pl >= 0 else 0xFF0000

        # Performance emoji
        if win_rate >= 65:
            perf_emoji = "🔥"
        elif win_rate >= 55:
            perf_emoji = "✅"
        elif win_rate >= 45:
            perf_emoji = "⚠️"
        else:
            perf_emoji = "❌"

        embed = {
            "title": f"📊 Daily Summary - {datetime.now().strftime('%B %d, %Y')}",
            "color": color,
            "fields": [
                {"name": "💰 Portfolio", "value": f"${equity:.2f}", "inline": True},
                {"name": "📈 Daily P/L", "value": f"${daily_pl:+.2f} ({daily_pl_percent:+.2f}%)", "inline": True},
                {"name": "📍 Open Positions", "value": str(positions), "inline": True},
                {"name": "🎯 Total Trades", "value": str(total_trades), "inline": True},
                {"name": "✅ Wins / ❌ Losses", "value": f"{winning_trades} / {losing_trades}", "inline": True},
                {"name": f"{perf_emoji} Win Rate", "value": f"{win_rate:.1f}%", "inline": True},
                {"name": "💵 Total P/L Today", "value": f"${total_pl:+.2f}", "inline": False}
            ],
            "footer": {"text": "Kraken Trading Bot - Daily Summary"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)

    def send_startup_notification(self, equity: float, symbols: list) -> bool:
        """Send bot startup notification"""

        symbol_list = ", ".join(symbols)

        embed = {
            "title": "🚀 Trading Bot Started",
            "color": 0x00D9FF,  # Cyan
            "fields": [
                {"name": "Status", "value": "✅ Active", "inline": True},
                {"name": "Starting Equity", "value": f"${equity:.2f}", "inline": True},
                {"name": "Trading Pairs", "value": f"{len(symbols)} symbols", "inline": True},
                {"name": "Symbols", "value": symbol_list, "inline": False}
            ],
            "footer": {"text": "Kraken Trading Bot"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)

    def send_shutdown_notification(self, equity: float, stats: Dict) -> bool:
        """Send bot shutdown notification"""

        total_trades = stats.get('lifetime_total', 0)
        win_rate = stats.get('lifetime_win_rate', 0)

        embed = {
            "title": "🛑 Trading Bot Stopped",
            "color": 0xFF0000,  # Red
            "fields": [
                {"name": "Status", "value": "Shutdown", "inline": True},
                {"name": "Final Equity", "value": f"${equity:.2f}", "inline": True},
                {"name": "Lifetime Trades", "value": str(total_trades), "inline": True},
                {"name": "Lifetime Win Rate", "value": f"{win_rate:.1f}%", "inline": True}
            ],
            "footer": {"text": "Kraken Trading Bot"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)

    def send_hot_signal_alert(self, signals: list) -> bool:
        """Send hot signal alert (signals approaching trade threshold)"""

        if not signals:
            return False

        signal_text = "\n".join([
            f"• **{sig['symbol']}** - {sig['signal']} ({sig['strength']}/100)"
            for sig in signals[:5]
        ])

        embed = {
            "title": "🔥 Hot Signals Detected!",
            "color": 0xFF4500,  # Orange-red
            "description": f"**{len(signals)} strong signal(s)** approaching trade threshold",
            "fields": [
                {"name": "Signals", "value": signal_text, "inline": False}
            ],
            "footer": {"text": "Kraken Trading Bot - Market Heat Alert"},
            "timestamp": datetime.utcnow().isoformat()
        }

        return self._send_webhook(embed)
