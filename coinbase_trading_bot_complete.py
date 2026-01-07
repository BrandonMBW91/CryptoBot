#!/usr/bin/env python3
"""
Coinbase Trading Bot - Complete Version
Multi-strategy trading bot with adaptive risk management and live dashboard
"""

import os
import json
import time
import signal
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from logging.handlers import RotatingFileHandler

import pandas as pd
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from coinbase.rest import RESTClient
from coinbase_dashboard import dashboard


# Set up logging
def setup_logging():
    logger = logging.getLogger("coinbase-bot")
    logger.setLevel(logging.INFO)

    try:
        file_handler = RotatingFileHandler(
            "coinbase-bot.log",
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")

    return logger


logger = setup_logging()


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class Config:
    """Configuration manager"""

    def __init__(self, config_file: str = "coinbase_config.json"):
        try:
            if not os.path.exists(config_file):
                raise ConfigurationError(f"Config file not found: {config_file}")

            with open(config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            self._validate_config()
            logger.info(f"Configuration loaded from {config_file}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")

    def _validate_config(self):
        """Validate configuration"""
        required_sections = ["coinbase", "trading", "assets"]
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required config section: {section}")

        if "apiKey" not in self.config["coinbase"] or "apiSecret" not in self.config["coinbase"]:
            raise ConfigurationError("Missing apiKey or apiSecret in coinbase config")

        if "crypto" not in self.config["assets"] or not self.config["assets"]["crypto"]:
            raise ConfigurationError("No crypto assets specified in config")

    @property
    def coinbase(self) -> dict:
        return self.config["coinbase"]

    @property
    def trading(self) -> dict:
        return self.config["trading"]

    @property
    def assets(self) -> dict:
        return self.config["assets"]


class CoinbaseClient:
    """Coinbase API client wrapper"""

    def __init__(self, config: Config):
        api_key = os.environ.get("COINBASE_API_KEY") or config.coinbase["apiKey"]
        api_secret = os.environ.get("COINBASE_API_SECRET") or config.coinbase["apiSecret"]

        if not api_key or not api_secret:
            raise ConfigurationError("API key or secret is empty")

        # Normalize newlines and add PEM header/footer if missing
        api_secret = api_secret.replace("\\n", "\n").replace("`n", "\n").strip()

        # Add PEM wrapper if not present
        if not api_secret.startswith("-----BEGIN"):
            api_secret = f"-----BEGIN EC PRIVATE KEY-----\n{api_secret}\n-----END EC PRIVATE KEY-----"

        try:
            self.client = RESTClient(api_key=api_key, api_secret=api_secret)
            logger.info("Coinbase REST client initialized")
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Coinbase client: {e}")

        self.last_request_time = 0
        self.min_request_interval = 0.1

    def _rate_limit(self):
        """Rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def get_account(self) -> Dict:
        """Get account information"""
        try:
            self._rate_limit()
            accounts = self.client.get_accounts()

            # Parse response
            if hasattr(accounts, 'accounts'):
                accounts_list = accounts.accounts
            elif hasattr(accounts, 'to_dict'):
                accounts_list = accounts.to_dict().get('accounts', [])
            elif isinstance(accounts, dict):
                accounts_list = accounts.get('accounts', [])
            else:
                accounts_list = []

            total_value = 0.0
            usd_balance = 0.0

            for acc in accounts_list:
                if hasattr(acc, 'available_balance'):
                    currency = acc.available_balance.currency if hasattr(acc.available_balance, 'currency') else 'USD'
                    value = float(acc.available_balance.value) if hasattr(acc.available_balance, 'value') else 0.0
                elif isinstance(acc, dict):
                    currency = acc.get('currency', 'USD')
                    value = float(acc.get('available_balance', {}).get('value', 0))
                else:
                    continue

                if currency == 'USD':
                    usd_balance += value
                    total_value += value

            return {
                'equity': total_value,
                'buying_power': usd_balance,
                'cash': usd_balance
            }

        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return {'equity': 0, 'buying_power': 0, 'cash': 0}

    def get_candles(self, product_id: str, granularity: str, limit: int = 200) -> pd.DataFrame:
        """Get historical candles"""
        try:
            self._rate_limit()
            end = int(datetime.now(timezone.utc).timestamp())
            start = end - limit * 300

            resp = self.client.get_candles(
                product_id=product_id,
                start=str(start),
                end=str(end),
                granularity=granularity,
            )

            # Handle response
            candles = None
            if hasattr(resp, "candles"):
                candles = resp.candles
            elif hasattr(resp, "to_dict"):
                try:
                    candles = resp.to_dict().get("candles")
                except Exception:
                    candles = None
            elif isinstance(resp, dict):
                candles = resp.get("candles")

            if not candles:
                return pd.DataFrame()

            rows = []
            for c in candles:
                try:
                    def _get(obj, key):
                        if isinstance(obj, dict):
                            return obj.get(key)
                        return getattr(obj, key, None)

                    start_ts = _get(c, "start")
                    if start_ts is None:
                        continue

                    rows.append({
                        "timestamp": datetime.fromtimestamp(int(start_ts), tz=timezone.utc),
                        "open": float(_get(c, "open")),
                        "high": float(_get(c, "high")),
                        "low": float(_get(c, "low")),
                        "close": float(_get(c, "close")),
                        "volume": float(_get(c, "volume") or 0),
                    })
                except (ValueError, TypeError):
                    continue

            if not rows:
                return pd.DataFrame()

            df = pd.DataFrame(rows).sort_values("timestamp").set_index("timestamp")
            return df

        except Exception as e:
            logger.error(f"Error getting candles for {product_id}: {e}")
            return pd.DataFrame()

    def place_order(self, product_id: str, side: str, size: float) -> Optional[Dict]:
        """Place market order"""
        try:
            self._rate_limit()

            order = self.client.market_order(
                product_id=product_id,
                side=side.lower(),
                size=str(size)
            )

            logger.info(f"Order placed: {side.upper()} {size} {product_id}")
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None


class TechnicalAnalysis:
    """Technical analysis calculations"""

    @staticmethod
    def calculate_rsi(bars: pd.DataFrame, period: int = 14) -> float:
        if len(bars) < period:
            return 50.0
        rsi = RSIIndicator(bars['close'], window=period)
        return rsi.rsi().iloc[-1]

    @staticmethod
    def calculate_macd(bars: pd.DataFrame) -> Dict:
        if len(bars) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        macd = MACD(bars['close'])
        return {
            'macd': macd.macd().iloc[-1],
            'signal': macd.macd_signal().iloc[-1],
            'histogram': macd.macd_diff().iloc[-1]
        }

    @staticmethod
    def calculate_sma(bars: pd.DataFrame, period: int) -> float:
        if len(bars) < period:
            return bars['close'].iloc[-1]
        sma = SMAIndicator(bars['close'], window=period)
        return sma.sma_indicator().iloc[-1]

    @staticmethod
    def calculate_atr(bars: pd.DataFrame, period: int = 14) -> float:
        if len(bars) < period:
            return 0.0
        atr = AverageTrueRange(bars['high'], bars['low'], bars['close'], window=period)
        return atr.average_true_range().iloc[-1]


class TradingStrategy:
    """Trading strategy implementation"""

    def __init__(self, config: Config):
        self.name = "Crypto Day Trading"
        self.timeframe = "FIVE_MINUTE"
        self.config = config
        self.min_signal_strength = 45

    def analyze(self, symbol: str, bars: pd.DataFrame) -> Dict:
        """Analyze and generate signal"""
        if len(bars) < 50:
            return {'signal': 'NEUTRAL', 'strength': 0}

        try:
            # Calculate indicators
            rsi = TechnicalAnalysis.calculate_rsi(bars, 14)
            macd = TechnicalAnalysis.calculate_macd(bars)
            sma = TechnicalAnalysis.calculate_sma(bars, 20)
            current_price = bars['close'].iloc[-1]

            strength = 0
            signal = 'NEUTRAL'

            # RSI signals
            if rsi < 30:
                strength += 30
                signal = 'BUY'
            elif rsi > 70:
                strength += 30
                signal = 'SELL'
            elif rsi < 40:
                strength += 15
                signal = 'BUY'
            elif rsi > 60:
                strength += 15
                signal = 'SELL'

            # MACD signals
            if macd['histogram'] > 0 and signal == 'BUY':
                strength += 20
            elif macd['histogram'] < 0 and signal == 'SELL':
                strength += 20

            # Price vs SMA
            if current_price > sma and signal == 'BUY':
                strength += 15
            elif current_price < sma and signal == 'SELL':
                strength += 15

            return {
                'signal': signal,
                'strength': min(strength, 100),
                'price': current_price,
                'rsi': round(rsi, 2)
            }

        except Exception as e:
            logger.error(f"Error in strategy analysis: {e}")
            return {'signal': 'NEUTRAL', 'strength': 0}


class AdaptiveRiskManager:
    """Adaptive risk management"""

    def __init__(self, config: Config):
        self.config = config
        self.base_position_size_percent = config.trading['maxPositionSizePercent']
        self.base_stop_loss_percent = config.trading['stopLossPercent']
        self.base_take_profit_percent = config.trading['takeProfitPercent']
        self.consecutive_losses = 0
        self.position_size_multiplier = 1.0
        self.symbol_locks = {}

    def calculate_position_size(self, price: float, portfolio_value: float) -> float:
        """Calculate position size"""
        position_percent = self.base_position_size_percent * self.position_size_multiplier
        position_value = portfolio_value * (position_percent / 100)
        qty = position_value / price
        return max(qty, 0)

    def calculate_stop_loss(self, entry_price: float, bars: pd.DataFrame) -> float:
        """Calculate stop loss"""
        atr = TechnicalAnalysis.calculate_atr(bars, 14)
        if atr > 0:
            atr_percent = (atr / entry_price) * 100
            stop_loss_percent = max(atr_percent * 2, self.base_stop_loss_percent)
            stop_loss_percent = min(stop_loss_percent, 5)
        else:
            stop_loss_percent = self.base_stop_loss_percent
        return entry_price * (1 - stop_loss_percent / 100)

    def calculate_take_profit(self, entry_price: float, bars: pd.DataFrame) -> float:
        """Calculate take profit"""
        atr = TechnicalAnalysis.calculate_atr(bars, 14)
        if atr > 0:
            atr_percent = (atr / entry_price) * 100
            take_profit_percent = max(atr_percent * 3, self.base_take_profit_percent)
            take_profit_percent = min(take_profit_percent, 10)
        else:
            take_profit_percent = self.base_take_profit_percent
        return entry_price * (1 + take_profit_percent / 100)

    def record_trade_result(self, is_win: bool):
        """Record trade result"""
        if is_win:
            self.consecutive_losses = 0
            self.position_size_multiplier = 1.0
        else:
            self.consecutive_losses += 1
            if self.consecutive_losses >= 2:
                self.position_size_multiplier = 0.66
            if self.consecutive_losses >= 3:
                self.position_size_multiplier = 0.33

    def acquire_lock(self, symbol: str) -> bool:
        """Acquire lock for symbol"""
        if symbol in self.symbol_locks:
            lock_time = self.symbol_locks[symbol]
            if time.time() - lock_time < 60:
                return False
        self.symbol_locks[symbol] = time.time()
        return True

    def release_lock(self, symbol: str):
        """Release lock"""
        self.symbol_locks.pop(symbol, None)


class PortfolioTracker:
    """Portfolio tracking and statistics"""

    def __init__(self):
        self.closed_positions = []
        self.all_time_closed_positions = []
        self.open_positions_entry = {}

    def record_entry(self, symbol: str, price: float, qty: float):
        """Record entry"""
        self.open_positions_entry[symbol] = {
            'price': price,
            'qty': qty,
            'timestamp': datetime.now()
        }

    def record_exit(self, symbol: str, exit_price: float, qty: float):
        """Record exit"""
        if symbol not in self.open_positions_entry:
            return

        entry = self.open_positions_entry[symbol]
        realized_pl = (exit_price - entry['price']) * qty
        realized_pl_percent = ((exit_price - entry['price']) / entry['price']) * 100

        trade = {
            'symbol': symbol,
            'entry_price': entry['price'],
            'exit_price': exit_price,
            'qty': qty,
            'pl': realized_pl,
            'pl_percent': realized_pl_percent,
            'timestamp': datetime.now()
        }

        self.closed_positions.append(trade)
        self.all_time_closed_positions.append(trade)
        self.open_positions_entry.pop(symbol, None)

        logger.info(f"Realized P/L for {symbol}: ${realized_pl:.2f} ({realized_pl_percent:.2f}%)")

    def get_daily_stats(self) -> Dict:
        """Get statistics"""
        wins = [t for t in self.closed_positions if t['pl'] > 0]
        losses = [t for t in self.closed_positions if t['pl'] < 0]

        lifetime_wins = [t for t in self.all_time_closed_positions if t['pl'] > 0]
        lifetime_losses = [t for t in self.all_time_closed_positions if t['pl'] < 0]

        return {
            'total_trades': len(self.closed_positions),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': (len(wins) / len(self.closed_positions) * 100) if self.closed_positions else 0,
            'total_pl': sum(t['pl'] for t in self.closed_positions),
            'lifetime_total': len(self.all_time_closed_positions),
            'lifetime_wins': len(lifetime_wins),
            'lifetime_losses': len(lifetime_losses),
            'lifetime_win_rate': (len(lifetime_wins) / len(self.all_time_closed_positions) * 100) if self.all_time_closed_positions else 0
        }


class TradingEngine:
    """Main trading engine"""

    def __init__(self, config_file='coinbase_config.json'):
        self.config = Config(config_file)
        self.client = CoinbaseClient(self.config)
        self.risk_manager = AdaptiveRiskManager(self.config)
        self.portfolio_tracker = PortfolioTracker()
        self.strategy = TradingStrategy(self.config)
        self.is_running = False
        self.products = self.config.assets['crypto']
        self.initial_equity = 0
        self.positions = {}

        # Dashboard thread
        self.dashboard_thread = None
        self.dashboard_running = False

    def initialize(self):
        """Initialize engine"""
        logger.info("Initializing Trading Engine...")

        # Get account info
        account = self.client.get_account()
        self.initial_equity = account['equity']

        # Initialize dashboard
        dashboard.initialize()

        # Start dashboard update thread
        self.dashboard_running = True
        self.dashboard_thread = threading.Thread(target=self._update_dashboard_loop, daemon=True)
        self.dashboard_thread.start()

        logger.info(f"Bot started - Equity: ${self.initial_equity:.2f}")

    def _update_dashboard_loop(self):
        """Dashboard update loop"""
        while self.dashboard_running:
            try:
                dashboard.render()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Dashboard error: {e}")

    def analyze_symbol(self, symbol: str):
        """Analyze symbol"""
        try:
            bars = self.client.get_candles(symbol, self.strategy.timeframe, 100)
            if bars.empty:
                return None

            signal = self.strategy.analyze(symbol, bars)

            # Add to dashboard
            dashboard.add_signal({
                'symbol': symbol,
                'signal': signal['signal'],
                'strength': signal['strength'],
                'timestamp': datetime.now().isoformat(),
                'strategy': self.strategy.name
            })

            if signal['signal'] == 'NEUTRAL' or signal['strength'] < 55:
                return None

            # Execute based on signal
            if signal['signal'] == 'BUY':
                self.execute_buy(symbol, signal, bars)
            elif signal['signal'] == 'SELL':
                self.execute_sell(symbol, signal)

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")

    def execute_buy(self, symbol: str, signal: Dict, bars: pd.DataFrame):
        """Execute buy"""
        if symbol in self.positions:
            return

        if not self.risk_manager.acquire_lock(symbol):
            return

        try:
            account = self.client.get_account()
            portfolio_value = account['equity']
            qty = self.risk_manager.calculate_position_size(signal['price'], portfolio_value)

            if qty * signal['price'] < self.config.trading.get('minNotionalUsd', 10):
                self.risk_manager.release_lock(symbol)
                return

            # Place order
            order = self.client.place_order(symbol, 'buy', qty)
            if order:
                self.portfolio_tracker.record_entry(symbol, signal['price'], qty)
                self.positions[symbol] = {
                    'symbol': symbol,
                    'qty': qty,
                    'avg_entry_price': signal['price'],
                    'unrealized_pl': 0,
                    'unrealized_plpc': 0
                }

                # Add to dashboard
                dashboard.add_trade({
                    'symbol': symbol,
                    'action': 'BUY',
                    'qty': f"{qty:.4f}",
                    'timestamp': datetime.now().isoformat()
                })

                logger.info(f"BUY {symbol}: {qty:.4f} @ ${signal['price']:.2f}")

        except Exception as e:
            logger.error(f"Failed to execute buy: {e}")
        finally:
            self.risk_manager.release_lock(symbol)

    def execute_sell(self, symbol: str, signal: Dict):
        """Execute sell"""
        if symbol not in self.positions:
            return

        try:
            position = self.positions[symbol]
            entry_price = position['avg_entry_price']
            exit_price = signal['price']
            qty = position['qty']
            is_win = exit_price > entry_price

            order = self.client.place_order(symbol, 'sell', qty)
            if order:
                self.portfolio_tracker.record_exit(symbol, exit_price, qty)
                self.risk_manager.record_trade_result(is_win)
                del self.positions[symbol]

                # Add to dashboard
                dashboard.add_trade({
                    'symbol': symbol,
                    'action': 'SELL',
                    'qty': f"{qty:.4f}",
                    'timestamp': datetime.now().isoformat()
                })

                logger.info(f"SELL {symbol}: {qty:.4f} @ ${exit_price:.2f} - {'WIN' if is_win else 'LOSS'}")

        except Exception as e:
            logger.error(f"Failed to execute sell: {e}")

    def run_analysis_cycle(self):
        """Run analysis cycle"""
        # Update account
        account = self.client.get_account()
        equity = account['equity']
        daily_pl = equity - self.initial_equity
        daily_pl_percent = (daily_pl / self.initial_equity * 100) if self.initial_equity > 0 else 0

        # Update dashboard
        dashboard.update_portfolio({
            'equity': equity,
            'buying_power': account['buying_power'],
            'daily_pl': daily_pl,
            'daily_pl_percent': daily_pl_percent,
            'positions': len(self.positions),
            'max_positions': 10,
            'emergency_stop': False
        })

        stats = self.portfolio_tracker.get_daily_stats()
        dashboard.update_daily_stats(stats)
        dashboard.update_positions(list(self.positions.values()))

        # Analyze symbols
        market_heat = []
        for symbol in self.products:
            try:
                bars = self.client.get_candles(symbol, self.strategy.timeframe, 100)
                if not bars.empty:
                    signal = self.strategy.analyze(symbol, bars)
                    if signal['strength'] >= 20:
                        market_heat.append({
                            'symbol': symbol,
                            'direction': signal['signal'],
                            'strength': signal['strength']
                        })
                self.analyze_symbol(symbol)
            except Exception as e:
                logger.error(f"Error with {symbol}: {e}")

        dashboard.update_market_heat(market_heat)

        # Log stats
        logger.info(f"Stats - Today: {stats['total_trades']} trades, "
                   f"W/L: {stats['winning_trades']}/{stats['losing_trades']}, "
                   f"Win Rate: {stats['win_rate']:.1f}%")

    def start(self):
        """Start bot"""
        self.is_running = True
        logger.info("Bot started - Running analysis every 60 seconds")

        while self.is_running:
            try:
                next_time = time.time() + 60
                dashboard.set_next_analysis_time(next_time)

                self.run_analysis_cycle()

                sleep_time = max(0, next_time - time.time())
                if self.is_running and sleep_time > 0:
                    time.sleep(sleep_time)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)

    def stop(self):
        """Stop bot"""
        self.is_running = False
        self.dashboard_running = False
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=2)
        dashboard.destroy()
        logger.info("Bot stopped")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Coinbase Trading Bot - Complete Version")
    print("=" * 60)

    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        engine.stop()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        engine = TradingEngine()
        engine.initialize()
        engine.start()
    except ConfigurationError as e:
        logger.critical(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
