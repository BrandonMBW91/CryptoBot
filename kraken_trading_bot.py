#!/usr/bin/env python3
"""
Kraken Trading Bot - Complete Version
Multi-strategy trading bot with adaptive risk management and live dashboard
"""

import os
import json
import time
import signal
import logging
import threading
import base64
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Optional
from logging.handlers import RotatingFileHandler

import requests
import pandas as pd
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

from dashboard import dashboard
from discord_notifier import DiscordNotifier


# Set up logging
def setup_logging():
    logger = logging.getLogger("kraken-bot")
    logger.setLevel(logging.INFO)

    try:
        file_handler = RotatingFileHandler(
            "kraken-bot.log",
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

    def __init__(self, config_file: str = "kraken_config.json"):
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
        required_sections = ["kraken", "trading", "assets"]
        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(f"Missing required config section: {section}")

        if "apiKey" not in self.config["kraken"] or "apiSecret" not in self.config["kraken"]:
            raise ConfigurationError("Missing apiKey or apiSecret in kraken config")

        if "crypto" not in self.config["assets"] or not self.config["assets"]["crypto"]:
            raise ConfigurationError("No crypto assets specified in config")

    @property
    def kraken(self) -> dict:
        return self.config["kraken"]

    @property
    def trading(self) -> dict:
        return self.config["trading"]

    @property
    def assets(self) -> dict:
        return self.config["assets"]


class KrakenClient:
    """Kraken API client wrapper"""

    def __init__(self, config: Config):
        api_key = os.environ.get("KRAKEN_API_KEY") or config.kraken["apiKey"]
        api_secret = os.environ.get("KRAKEN_API_SECRET") or config.kraken["apiSecret"]

        if not api_key or not api_secret:
            raise ConfigurationError("API key or secret is empty")

        if api_key == "YOUR_KRAKEN_API_KEY":
            raise ConfigurationError("API key has not been configured")

        self.api_key = api_key
        self.api_secret = api_secret
        self.api_url = "https://api.kraken.com"
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Kraken rate limit
        self.config = config  # Store config reference

        logger.info("Kraken client initialized")

    def _get_kraken_signature(self, urlpath: str, data: dict, secret: str) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()

    def _rate_limit(self):
        """Rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _public_request(self, endpoint: str, params: dict = None) -> dict:
        """Make public API request"""
        self._rate_limit()
        url = f"{self.api_url}/0/public/{endpoint}"

        try:
            response = requests.get(url, params=params or {}, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('error') and len(data['error']) > 0:
                raise Exception(f"Kraken API error: {data['error']}")

            return data.get('result', {})
        except Exception as e:
            logger.error(f"Public request error: {e}")
            raise

    def _private_request(self, endpoint: str, params: dict = None) -> dict:
        """Make private API request"""
        self._rate_limit()
        url = f"{self.api_url}/0/private/{endpoint}"
        urlpath = f"/0/private/{endpoint}"

        params = params or {}
        params['nonce'] = str(int(time.time() * 1000))

        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._get_kraken_signature(urlpath, params, self.api_secret)
        }

        try:
            response = requests.post(url, headers=headers, data=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('error') and len(data['error']) > 0:
                raise Exception(f"Kraken API error: {data['error']}")

            return data.get('result', {})
        except Exception as e:
            logger.error(f"Private request error: {e}")
            raise

    def get_account(self) -> Dict:
        """Get account balance"""
        try:
            balance = self._private_request('Balance')

            # Calculate total USD value
            total_usd = 0.0
            usd_balance = float(balance.get('ZUSD', 0))
            total_usd += usd_balance

            # Add crypto values by getting current prices
            for currency, amount in balance.items():
                amount_float = float(amount)
                if amount_float > 0 and currency not in ['ZUSD', 'USD']:
                    # Find matching trading pair
                    for symbol in self.config.assets.get('crypto', []):
                        if symbol.startswith(currency) or symbol.startswith('X' + currency) or symbol.startswith('Z' + currency):
                            try:
                                current_price = self.get_ticker(symbol)
                                if current_price:
                                    crypto_value = amount_float * current_price
                                    total_usd += crypto_value
                                    logger.debug(f"Added {currency}: {amount_float:.4f} @ ${current_price:.4f} = ${crypto_value:.2f}")
                                    break
                            except Exception as e:
                                logger.error(f"Error getting price for {symbol}: {e}")

            return {
                'equity': total_usd,
                'buying_power': usd_balance,
                'cash': usd_balance
            }
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return {'equity': 0, 'buying_power': 0, 'cash': 0}

    def get_ohlc(self, pair: str, interval: int = 5, since: int = None) -> pd.DataFrame:
        """Get OHLC data"""
        try:
            params = {'pair': pair, 'interval': interval}
            if since:
                params['since'] = since

            data = self._public_request('OHLC', params)

            # Get the first pair key (Kraken returns pair-specific keys)
            pair_key = next(iter(data.keys())) if data else None
            if not pair_key or pair_key == 'last':
                return pd.DataFrame()

            ohlc_data = data[pair_key]

            if not ohlc_data:
                return pd.DataFrame()

            rows = []
            for candle in ohlc_data:
                rows.append({
                    'timestamp': datetime.fromtimestamp(int(candle[0]), tz=timezone.utc),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[6])
                })

            if not rows:
                return pd.DataFrame()

            df = pd.DataFrame(rows).set_index('timestamp')
            return df

        except Exception as e:
            logger.error(f"Error getting OHLC for {pair}: {e}")
            return pd.DataFrame()

    def get_ticker(self, pair: str) -> Optional[float]:
        """Get current ticker price"""
        try:
            data = self._public_request('Ticker', {'pair': pair})
            pair_key = next(iter(data.keys())) if data else None

            if not pair_key:
                return None

            ticker = data[pair_key]
            return float(ticker['c'][0])  # Last trade closed array

        except Exception as e:
            logger.error(f"Error getting ticker for {pair}: {e}")
            return None

    def place_order(self, pair: str, side: str, volume: float, ordertype: str = 'market') -> Optional[Dict]:
        """Place order"""
        try:
            params = {
                'pair': pair,
                'type': side.lower(),
                'ordertype': ordertype,
                'volume': str(volume)
            }

            result = self._private_request('AddOrder', params)
            logger.info(f"Order placed: {side.upper()} {volume} {pair}")
            return result

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return None

    def get_open_orders(self) -> dict:
        """Get open orders"""
        try:
            return self._private_request('OpenOrders')
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return {}


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
    def calculate_ema(bars: pd.DataFrame, period: int) -> float:
        if len(bars) < period:
            return bars['close'].iloc[-1]
        ema = EMAIndicator(bars['close'], window=period)
        return ema.ema_indicator().iloc[-1]

    @staticmethod
    def calculate_atr(bars: pd.DataFrame, period: int = 14) -> float:
        if len(bars) < period:
            return 0.0
        atr = AverageTrueRange(bars['high'], bars['low'], bars['close'], window=period)
        return atr.average_true_range().iloc[-1]


class TradingStrategy:
    """Enhanced trading strategy with multiple confirmations"""

    def __init__(self, config: Config):
        self.name = "Smart Crypto Trading"
        self.config = config
        self.min_signal_strength = 45

    def analyze(self, symbol: str, bars: pd.DataFrame) -> Dict:
        """Analyze and generate signal with multiple confirmations"""
        if len(bars) < 50:
            return {'signal': 'NEUTRAL', 'strength': 0}

        try:
            # Calculate indicators
            rsi = TechnicalAnalysis.calculate_rsi(bars, 14)
            macd = TechnicalAnalysis.calculate_macd(bars)
            sma20 = TechnicalAnalysis.calculate_sma(bars, 20)
            sma50 = TechnicalAnalysis.calculate_sma(bars, 50)
            ema12 = TechnicalAnalysis.calculate_ema(bars, 12)
            ema26 = TechnicalAnalysis.calculate_ema(bars, 26)
            atr = TechnicalAnalysis.calculate_atr(bars, 14)

            current_price = bars['close'].iloc[-1]
            prev_close = bars['close'].iloc[-2]
            volume = bars['volume'].iloc[-1]
            avg_volume = bars['volume'].tail(20).mean()

            strength = 0
            signal = 'NEUTRAL'
            confirmations = []

            # === BUY SIGNALS ===

            # Strong oversold with RSI
            if rsi < 30:
                strength += 35
                signal = 'BUY'
                confirmations.append("RSI oversold <30")
            elif rsi < 40:
                strength += 20
                signal = 'BUY'
                confirmations.append("RSI oversold <40")

            # MACD bullish crossover
            if macd['histogram'] > 0:
                if signal == 'BUY':
                    strength += 25
                    confirmations.append("MACD bullish")
                # MACD just crossed positive (strong confirmation)
                if macd['macd'] > macd['signal'] and macd['histogram'] > 0:
                    if signal == 'BUY':
                        strength += 15
                        confirmations.append("MACD crossover")

            # Price above moving averages (trend confirmation)
            if current_price > sma20:
                if signal == 'BUY':
                    strength += 15
                    confirmations.append("Above SMA20")
            if current_price > sma50:
                if signal == 'BUY':
                    strength += 10
                    confirmations.append("Above SMA50")

            # EMA momentum
            if ema12 > ema26:
                if signal == 'BUY':
                    strength += 10
                    confirmations.append("EMA bullish")

            # Volume confirmation (higher volume = stronger signal)
            if volume > avg_volume * 1.5:
                if signal == 'BUY':
                    strength += 15
                    confirmations.append("High volume")
            elif volume > avg_volume * 1.2:
                if signal == 'BUY':
                    strength += 8
                    confirmations.append("Above avg volume")

            # Price momentum
            if current_price > prev_close:
                if signal == 'BUY':
                    strength += 5
                    confirmations.append("Bullish candle")

            # === SELL SIGNALS ===

            # Reset for SELL signals
            if signal != 'BUY':
                strength = 0
                confirmations = []

                # Strong overbought with RSI
                if rsi > 70:
                    strength += 35
                    signal = 'SELL'
                    confirmations.append("RSI overbought >70")
                elif rsi > 60:
                    strength += 20
                    signal = 'SELL'
                    confirmations.append("RSI overbought >60")

                # MACD bearish
                if macd['histogram'] < 0:
                    if signal == 'SELL':
                        strength += 25
                        confirmations.append("MACD bearish")
                    if macd['macd'] < macd['signal'] and macd['histogram'] < 0:
                        if signal == 'SELL':
                            strength += 15
                            confirmations.append("MACD crossover")

                # Price below moving averages
                if current_price < sma20:
                    if signal == 'SELL':
                        strength += 15
                        confirmations.append("Below SMA20")
                if current_price < sma50:
                    if signal == 'SELL':
                        strength += 10
                        confirmations.append("Below SMA50")

                # EMA momentum
                if ema12 < ema26:
                    if signal == 'SELL':
                        strength += 10
                        confirmations.append("EMA bearish")

                # Volume confirmation
                if volume > avg_volume * 1.5:
                    if signal == 'SELL':
                        strength += 15
                        confirmations.append("High volume")
                elif volume > avg_volume * 1.2:
                    if signal == 'SELL':
                        strength += 8
                        confirmations.append("Above avg volume")

                # Price momentum
                if current_price < prev_close:
                    if signal == 'SELL':
                        strength += 5
                        confirmations.append("Bearish candle")

            # Quality filter: Require at least 3 confirmations for high confidence
            min_confirmations = 3
            if len(confirmations) < min_confirmations and signal != 'NEUTRAL':
                # Reduce strength if not enough confirmations
                strength = int(strength * 0.7)

            return {
                'signal': signal,
                'strength': min(strength, 100),
                'price': current_price,
                'rsi': round(rsi, 2),
                'macd': round(macd['histogram'], 4),
                'confirmations': confirmations,
                'volume_ratio': round(volume / avg_volume, 2),
                'atr': round(atr, 2)
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

    def __init__(self, config_file='kraken_config.json'):
        self.config = Config(config_file)
        self.client = KrakenClient(self.config)
        self.risk_manager = AdaptiveRiskManager(self.config)
        self.portfolio_tracker = PortfolioTracker()
        self.strategy = TradingStrategy(self.config)
        self.is_running = False
        self.products = self.config.assets['crypto']
        self.initial_equity = 0
        self.positions = {}

        # Discord notifiers
        discord_config = self.config.config.get('discord', {})
        self.discord_trading = DiscordNotifier(discord_config.get('webhookTrading', ''))
        self.discord_errors = DiscordNotifier(discord_config.get('webhookErrors', ''))
        self.discord_summary = DiscordNotifier(discord_config.get('webhookDailySummary', ''))
        self.daily_summary_time = discord_config.get('dailySummaryTime', '10:00')
        self.last_summary_date = None

        # Dashboard thread
        self.dashboard_thread = None
        self.dashboard_running = False

    def _recover_positions(self):
        """Recover open positions from Kraken account"""
        try:
            balance = self.client._private_request('Balance')
            logger.info("Recovering open positions from account...")

            for currency, amount in balance.items():
                amount_float = float(amount)
                if amount_float > 0 and currency not in ['ZUSD', 'USD']:
                    # This is a crypto position - try to find matching symbol
                    for symbol in self.products:
                        # Match currency to symbol (e.g., APE -> APEUSD)
                        if symbol.startswith(currency) or symbol.startswith('X' + currency) or symbol.startswith('Z' + currency):
                            # Get current price
                            current_price = self.client.get_ticker(symbol)
                            if current_price:
                                # We don't know the entry price, so use current price
                                # This means unrealized P/L will be 0 until we track it
                                self.positions[symbol] = {
                                    'symbol': symbol,
                                    'qty': amount_float,
                                    'avg_entry_price': current_price,  # Unknown, using current
                                    'current_price': current_price,
                                    'unrealized_pl': 0,
                                    'unrealized_plpc': 0
                                }
                                logger.info(f"Recovered position: {symbol} - {amount_float:.4f} @ ${current_price:.4f}")
                                break
        except Exception as e:
            logger.error(f"Error recovering positions: {e}")

    def initialize(self):
        """Initialize engine"""
        logger.info("Initializing Trading Engine...")

        # Get account info
        account = self.client.get_account()
        self.initial_equity = account['equity']

        # Recover any open positions from account
        self._recover_positions()

        # Update dashboard platform name
        dashboard.platform_name = 'KRAKEN'

        # Initialize dashboard
        dashboard.initialize()

        # Start dashboard update thread
        self.dashboard_running = True
        self.dashboard_thread = threading.Thread(target=self._update_dashboard_loop, daemon=True)
        self.dashboard_thread.start()

        logger.info(f"Bot started - Equity: ${self.initial_equity:.2f}")

        # Send Discord startup notification
        self.discord_trading.send_startup_notification(
            equity=self.initial_equity,
            symbols=self.products
        )

    def _update_dashboard_loop(self):
        """Dashboard update loop"""
        while self.dashboard_running:
            try:
                dashboard.render()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Dashboard error: {e}")

    def _check_daily_summary(self):
        """Check if it's time to send daily summary"""
        try:
            now = datetime.now()
            current_date = now.date()
            current_time = now.strftime('%H:%M')

            # Check if we haven't sent summary today and it's past the scheduled time
            if self.last_summary_date != current_date:
                target_hour, target_minute = map(int, self.daily_summary_time.split(':'))
                if now.hour > target_hour or (now.hour == target_hour and now.minute >= target_minute):
                    # Get current account info
                    account = self.client.get_account()
                    equity = account.get('equity', 0)
                    daily_pl = equity - self.initial_equity
                    daily_pl_percent = (daily_pl / self.initial_equity * 100) if self.initial_equity > 0 else 0

                    # Get stats
                    stats = self.portfolio_tracker.get_daily_stats()

                    # Build portfolio dict
                    portfolio = {
                        'equity': equity,
                        'daily_pl': daily_pl,
                        'daily_pl_percent': daily_pl_percent,
                        'positions': len(self.positions)
                    }

                    # Send Discord daily summary
                    self.discord_summary.send_daily_summary(stats, portfolio)
                    self.last_summary_date = current_date
                    logger.info(f"Daily summary sent at {current_time}")

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            self.discord_errors.send_error_alert('Daily Summary Error', str(e))

    def analyze_symbol(self, symbol: str):
        """Analyze symbol"""
        try:
            bars = self.client.get_ohlc(symbol, interval=5)
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
            self.discord_errors.send_error_alert('Analysis Error', str(e), symbol)

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
                    'current_price': signal['price'],
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

                # Send Discord trade notification
                self.discord_trading.send_trade_notification(
                    trade_type='BUY',
                    symbol=symbol,
                    qty=qty,
                    price=signal['price'],
                    strength=signal['strength'],
                    confirmations=signal.get('confirmations', [])
                )

        except Exception as e:
            logger.error(f"Failed to execute buy: {e}")
            self.discord_errors.send_error_alert('Buy Order Failed', str(e), symbol)
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

                # Calculate P/L for Discord notification
                pl = (exit_price - entry_price) * qty
                pl_percent = ((exit_price - entry_price) / entry_price) * 100

                del self.positions[symbol]

                # Add to dashboard
                dashboard.add_trade({
                    'symbol': symbol,
                    'action': 'SELL',
                    'qty': f"{qty:.4f}",
                    'timestamp': datetime.now().isoformat()
                })

                logger.info(f"SELL {symbol}: {qty:.4f} @ ${exit_price:.2f} - {'WIN' if is_win else 'LOSS'}")

                # Send Discord position closed notification
                self.discord_trading.send_position_closed(
                    symbol=symbol,
                    qty=qty,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    pl=pl,
                    pl_percent=pl_percent
                )

        except Exception as e:
            logger.error(f"Failed to execute sell: {e}")
            self.discord_errors.send_error_alert('Sell Order Failed', str(e), symbol)

    def _update_position_prices(self):
        """Update current prices for all open positions"""
        for symbol in list(self.positions.keys()):
            try:
                current_price = self.client.get_ticker(symbol)
                if current_price:
                    position = self.positions[symbol]
                    entry_price = position['avg_entry_price']
                    qty = position['qty']
                    unrealized_pl = (current_price - entry_price) * qty
                    unrealized_plpc = ((current_price - entry_price) / entry_price) * 100

                    self.positions[symbol]['current_price'] = current_price
                    self.positions[symbol]['unrealized_pl'] = unrealized_pl
                    self.positions[symbol]['unrealized_plpc'] = unrealized_plpc
            except Exception as e:
                logger.error(f"Error updating price for {symbol}: {e}")

    def run_analysis_cycle(self):
        """Run analysis cycle"""
        # Check if it's time for daily summary
        self._check_daily_summary()

        # Update current prices for open positions
        self._update_position_prices()

        # Update account
        account = self.client.get_account()
        equity = account.get('equity', 0)
        daily_pl = equity - self.initial_equity
        daily_pl_percent = (daily_pl / self.initial_equity * 100) if self.initial_equity > 0 else 0

        # Update dashboard
        dashboard.update_portfolio({
            'equity': equity,
            'buying_power': account.get('buying_power', 0),
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
                bars = self.client.get_ohlc(symbol, interval=5)
                if not bars.empty:
                    signal = self.strategy.analyze(symbol, bars)
                    # Add to signals regardless of strength
                    dashboard.add_signal({
                        'symbol': symbol,
                        'signal': signal['signal'],
                        'strength': signal['strength'],
                        'timestamp': datetime.now().isoformat(),
                        'strategy': self.strategy.name
                    })

                    # Market heat shows signals >= 10 strength (lower threshold for visibility)
                    if signal['strength'] >= 10 and signal['signal'] != 'NEUTRAL':
                        market_heat.append({
                            'symbol': symbol,
                            'direction': signal['signal'],
                            'strength': signal['strength']
                        })
                        confirmations = signal.get('confirmations', [])
                        conf_str = ', '.join(confirmations[:3]) if confirmations else 'None'
                        logger.info(f"{symbol}: {signal['signal']} {signal['strength']:.0f} | "
                                  f"RSI:{signal.get('rsi', 0):.1f} Vol:{signal.get('volume_ratio', 0):.1f}x | {conf_str}")

                    # Only execute trades >= 55 strength
                    if signal['signal'] != 'NEUTRAL' and signal['strength'] >= 55:
                        if signal['signal'] == 'BUY':
                            self.execute_buy(symbol, signal, bars)
                        elif signal['signal'] == 'SELL':
                            self.execute_sell(symbol, signal)
            except Exception as e:
                logger.error(f"Error with {symbol}: {e}")

        dashboard.update_market_heat(market_heat)
        logger.info(f"Market Heat: {len(market_heat)} signals detected")

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

        # Send Discord shutdown notification
        try:
            account = self.client.get_account()
            stats = self.portfolio_tracker.get_daily_stats()
            self.discord_trading.send_shutdown_notification(
                equity=account.get('equity', 0),
                stats=stats
            )
        except Exception as e:
            logger.error(f"Error sending shutdown notification: {e}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Kraken Trading Bot - Complete Version")
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
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease update kraken_config.json with your API credentials")
        return 1
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
