#!/usr/bin/env python3
"""
Coinbase Trading Bot - DEMO MODE
Shows the dashboard with simulated data (no real trading)
"""

import time
import random
import signal
import threading
from datetime import datetime
from coinbase_dashboard import dashboard


class DemoEngine:
    """Demo trading engine with simulated data"""

    def __init__(self):
        self.is_running = False
        self.dashboard_running = False
        self.dashboard_thread = None
        self.equity = 10000.0
        self.initial_equity = 10000.0
        self.positions = {}
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'MATIC-USD']

    def initialize(self):
        """Initialize demo mode"""
        print("=" * 60)
        print("Coinbase Trading Bot - DEMO MODE")
        print("Simulated data only - No real trading")
        print("=" * 60)

        dashboard.initialize()

        # Start dashboard update thread
        self.dashboard_running = True
        self.dashboard_thread = threading.Thread(target=self._update_dashboard_loop, daemon=True)
        self.dashboard_thread.start()

        time.sleep(1)

    def _update_dashboard_loop(self):
        """Dashboard update loop"""
        while self.dashboard_running:
            try:
                dashboard.render()
                time.sleep(1)
            except Exception as e:
                pass

    def generate_mock_signal(self, symbol: str):
        """Generate random signal"""
        signal_type = random.choice(['BUY', 'SELL', 'NEUTRAL', 'NEUTRAL'])
        strength = random.randint(20, 95)

        signal_data = {
            'symbol': symbol,
            'signal': signal_type,
            'strength': strength,
            'timestamp': datetime.now().isoformat(),
            'strategy': 'Demo Strategy'
        }

        dashboard.add_signal(signal_data)
        return signal_data

    def simulate_trade(self):
        """Simulate a random trade"""
        if random.random() > 0.7:  # 30% chance of trade
            symbol = random.choice(self.symbols)
            action = random.choice(['BUY', 'SELL'])

            if action == 'BUY' and len(self.positions) < 5:
                # Simulate buy
                price = random.uniform(20000, 100000) if 'BTC' in symbol else random.uniform(1000, 5000)
                qty = random.uniform(0.01, 0.1)

                self.positions[symbol] = {
                    'symbol': symbol,
                    'qty': qty,
                    'avg_entry_price': price,
                    'unrealized_pl': 0,
                    'unrealized_plpc': 0
                }

                dashboard.add_trade({
                    'symbol': symbol,
                    'action': 'BUY',
                    'qty': f"{qty:.4f}",
                    'timestamp': datetime.now().isoformat()
                })

                self.trade_count += 1

            elif action == 'SELL' and symbol in self.positions:
                # Simulate sell
                is_win = random.random() > 0.4  # 60% win rate
                if is_win:
                    self.win_count += 1
                    pl_change = random.uniform(50, 500)
                else:
                    self.loss_count += 1
                    pl_change = -random.uniform(20, 200)

                self.equity += pl_change

                dashboard.add_trade({
                    'symbol': symbol,
                    'action': 'SELL',
                    'qty': f"{self.positions[symbol]['qty']:.4f}",
                    'timestamp': datetime.now().isoformat()
                })

                del self.positions[symbol]

    def update_positions(self):
        """Update position P/L"""
        for symbol, pos in self.positions.items():
            # Simulate price movement
            change_percent = random.uniform(-0.05, 0.05)
            current_price = pos['avg_entry_price'] * (1 + change_percent)
            pl = (current_price - pos['avg_entry_price']) * pos['qty']
            pl_percent = ((current_price - pos['avg_entry_price']) / pos['avg_entry_price'])

            pos['unrealized_pl'] = pl
            pos['unrealized_plpc'] = pl_percent

    def run_analysis_cycle(self):
        """Run simulated analysis cycle"""
        # Update equity with random drift
        drift = random.uniform(-10, 20)
        self.equity += drift

        daily_pl = self.equity - self.initial_equity
        daily_pl_percent = (daily_pl / self.initial_equity * 100)

        # Update positions
        self.update_positions()

        # Update dashboard
        dashboard.update_portfolio({
            'equity': self.equity,
            'buying_power': self.equity * 0.8,
            'daily_pl': daily_pl,
            'daily_pl_percent': daily_pl_percent,
            'positions': len(self.positions),
            'max_positions': 5,
            'emergency_stop': False
        })

        total_trades = self.trade_count
        win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0

        dashboard.update_daily_stats({
            'total_trades': total_trades,
            'winning_trades': self.win_count,
            'losing_trades': self.loss_count,
            'win_rate': win_rate,
            'total_pl': daily_pl,
            'lifetime_total': total_trades,
            'lifetime_wins': self.win_count,
            'lifetime_losses': self.loss_count,
            'lifetime_win_rate': win_rate
        })

        dashboard.update_positions(list(self.positions.values()))

        # Generate signals and market heat
        market_heat = []
        for symbol in self.symbols:
            signal = self.generate_mock_signal(symbol)
            if signal['strength'] >= 20:
                market_heat.append({
                    'symbol': symbol,
                    'direction': signal['signal'],
                    'strength': signal['strength']
                })

        dashboard.update_market_heat(market_heat)

        # Simulate trades
        self.simulate_trade()

    def start(self):
        """Start demo bot"""
        self.is_running = True

        cycle_count = 0
        while self.is_running:
            try:
                next_time = time.time() + 5  # Every 5 seconds for demo
                dashboard.set_next_analysis_time(next_time)

                self.run_analysis_cycle()
                cycle_count += 1

                # Every 10 cycles, clear hot signals
                if cycle_count % 10 == 0:
                    dashboard.clear_hot_signals()

                sleep_time = max(0, next_time - time.time())
                if self.is_running and sleep_time > 0:
                    time.sleep(sleep_time)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

    def stop(self):
        """Stop demo bot"""
        self.is_running = False
        self.dashboard_running = False
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=2)
        dashboard.destroy()
        print("\n\nDemo bot stopped")


def main():
    """Main entry point"""

    def signal_handler(sig, frame):
        engine.stop()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        engine = DemoEngine()
        engine.initialize()
        engine.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
