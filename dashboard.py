#!/usr/bin/env python3
"""
Terminal Dashboard for Coinbase Trading Bot
Real-time display with portfolio stats, positions, and market heat
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    GRAY = '\033[90m'

    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Custom hex colors (256-color mode)
    @staticmethod
    def hex(color: str) -> str:
        """Convert hex color to closest ANSI 256 color"""
        if color == '#00D9FF':
            return '\033[38;5;45m'  # Cyan
        elif color == '#FFD700':
            return '\033[38;5;220m'  # Gold
        elif color == '#00FF00':
            return '\033[38;5;46m'  # Bright green
        elif color == '#FF0000':
            return '\033[38;5;196m'  # Red
        elif color == '#FF4500':
            return '\033[38;5;202m'  # Orange red
        elif color == '#FFA500':
            return '\033[38;5;214m'  # Orange
        elif color == '#4169E1':
            return '\033[38;5;69m'  # Royal blue
        return '\033[0m'


class CoinbaseDashboard:
    """Real-time terminal dashboard"""

    def __init__(self):
        self.trading_data = {
            'portfolio': {},
            'positions': [],
            'recent_trades': [],
            'signals': [],
            'daily_stats': {},
            'hot_signals': [],
            'market_heat': []
        }
        self.frame_count = 0
        self.next_analysis_time = None
        self.platform_name = 'COINBASE'
        self.trading_mode = 'LIVE TRADING'
        self.spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def initialize(self):
        """Initialize dashboard"""
        os.system('cls' if os.name == 'nt' else 'clear')
        # Hide cursor
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()
        self.render()

    def move_cursor(self, row: int, col: int):
        """Move cursor to position"""
        sys.stdout.write(f'\033[{row};{col}H')

    def clear_line(self):
        """Clear current line"""
        sys.stdout.write('\033[2K')

    def get_progress_bar(self, percent: float, width: int = 30) -> str:
        """Generate progress bar"""
        filled = min(width, max(0, round((percent / 100) * width)))
        empty = max(0, width - filled)

        if percent >= 80:
            color = Colors.GREEN
        elif percent >= 50:
            color = Colors.YELLOW
        elif percent >= 30:
            color = Colors.hex('#FFA500')
        else:
            color = Colors.RED

        return f"{color}{'█' * filled}{Colors.GRAY}{'░' * empty}{Colors.RESET}"

    def get_spinner(self) -> str:
        """Get spinner animation frame"""
        frame = self.spinner_frames[self.frame_count % len(self.spinner_frames)]
        return f"{Colors.CYAN}{frame}{Colors.RESET}"

    def get_heat_bar(self, percent: float, width: int = 20) -> str:
        """Generate heat bar"""
        filled = min(width, max(0, round((percent / 100) * width)))
        empty = max(0, width - filled)

        if percent >= 90:
            color = Colors.hex('#FF0000')  # Red hot
        elif percent >= 75:
            color = Colors.hex('#FF4500')  # Orange red
        elif percent >= 60:
            color = Colors.hex('#FFA500')  # Orange
        elif percent >= 40:
            color = Colors.hex('#FFD700')  # Gold
        else:
            color = Colors.hex('#4169E1')  # Cool blue

        return f"{color}{'█' * filled}{Colors.GRAY}{'░' * empty}{Colors.RESET}"

    def get_temperature_icon(self, percent: float) -> str:
        """Get temperature icon"""
        if percent >= 90:
            return f"{Colors.hex('#FF0000')}🔥{Colors.RESET}"
        elif percent >= 75:
            return f"{Colors.hex('#FF4500')}🌡️{Colors.RESET}"
        elif percent >= 60:
            return f"{Colors.hex('#FFA500')}♨️{Colors.RESET}"
        elif percent >= 40:
            return f"{Colors.hex('#FFD700')}💨{Colors.RESET}"
        else:
            return f"{Colors.hex('#4169E1')}❄️{Colors.RESET}"

    def pad_column(self, content: str, width: int = 49) -> str:
        """Pad content to exact column width"""
        # Strip ANSI codes to measure actual length
        import re
        stripped = re.sub(r'\033\[[0-9;]*m', '', content)

        # Count emoji characters (they take 2 visual spaces)
        emoji_count = len([c for c in stripped if ord(c) > 0x1F300])

        visual_length = len(stripped) + emoji_count
        padding = max(0, width - visual_length)
        return content + ' ' * padding

    def render(self):
        """Render dashboard"""
        try:
            self.frame_count += 1

            # Move to top-left
            self.move_cursor(1, 1)

            lines = []

            # Banner - 116 characters wide inner content
            title = f"🚀 {self.platform_name} TRADING BOT v2.0 - {self.trading_mode} 🚀"
            # Account for emojis (they take 2 visual spaces each, but count as fewer chars)
            emoji_count = title.count('🚀')
            visual_length = len(title) + emoji_count
            title_padding = max(0, (116 - visual_length) // 2)
            padded_title = ' ' * title_padding + title + ' ' * (116 - visual_length - title_padding)

            cyan = Colors.hex('#00D9FF')
            gold = Colors.hex('#FFD700')

            lines.append(f"{cyan}╔{'═' * 116}╗{Colors.RESET}")
            lines.append(f"{cyan}║{gold}{Colors.BOLD}{padded_title}{Colors.RESET}{cyan}║{Colors.RESET}")
            lines.append(f"{cyan}╚{'═' * 116}╝{Colors.RESET}")
            lines.append('')

            # Portfolio & Stats
            p = self.trading_data['portfolio']
            s = self.trading_data['daily_stats']

            if p.get('equity'):
                pl_color = Colors.GREEN if p['daily_pl'] >= 0 else Colors.RED
                pl_symbol = '▲' if p['daily_pl'] >= 0 else '▼'
                status_icon = '🛑' if p.get('emergency_stop') else '✅'
                status_color = Colors.RED if p.get('emergency_stop') else Colors.GREEN
                status_text = 'EMERGENCY STOP' if p.get('emergency_stop') else 'ACTIVE'
                position_usage = (p['positions'] / p.get('max_positions', 10)) * 100

                lines.append(f"{cyan}╔{'═' * 51}╦{'═' * 51}╗{Colors.RESET}")

                left_header = self.pad_column(f"{gold}{Colors.BOLD}💰 PORTFOLIO STATUS{Colors.RESET}")
                right_header = self.pad_column(f"{gold}{Colors.BOLD}📊 DAILY PERFORMANCE{Colors.RESET}")
                lines.append(f"{cyan}║ {left_header}║ {right_header}║{Colors.RESET}")

                lines.append(f"{cyan}╠{'═' * 51}╬{'═' * 51}╣{Colors.RESET}")

                left_row1 = self.pad_column(f"{Colors.CYAN}Status: {status_icon} {status_color}{Colors.BOLD}{status_text}{Colors.RESET}")
                right_row1 = self.pad_column(f"{Colors.CYAN}Today: {Colors.YELLOW}{s.get('total_trades', 0)}{Colors.GRAY} trades  {Colors.CYAN}All-Time: {Colors.YELLOW}{s.get('lifetime_total', 0)}{Colors.RESET}")
                lines.append(f"{cyan}║ {left_row1}║ {right_row1}║{Colors.RESET}")

                left_row2 = self.pad_column(f"{Colors.CYAN}Equity: {Colors.hex('#00FF00')}{Colors.BOLD}${p['equity']:.2f}{Colors.RESET}")
                right_row2 = self.pad_column(f"{Colors.CYAN}Today W/L: {Colors.GREEN}{s.get('winning_trades', 0)}{Colors.GRAY}/{Colors.RED}{s.get('losing_trades', 0)}{Colors.GRAY}  {Colors.CYAN}All W/L: {Colors.GREEN}{s.get('lifetime_wins', 0)}{Colors.GRAY}/{Colors.RED}{s.get('lifetime_losses', 0)}{Colors.RESET}")
                lines.append(f"{cyan}║ {left_row2}║ {right_row2}║{Colors.RESET}")

                left_row3 = self.pad_column(f"{Colors.CYAN}Buying Power: {Colors.YELLOW}${p['buying_power']:.2f}{Colors.RESET}")
                right_row3 = self.pad_column(f"{Colors.CYAN}Today Rate: {Colors.hex('#FFD700')}{s.get('win_rate', 0):.1f}%{Colors.GRAY}  {Colors.CYAN}All Rate: {Colors.hex('#FFD700')}{s.get('lifetime_win_rate', 0):.1f}%{Colors.RESET}")
                lines.append(f"{cyan}║ {left_row3}║ {right_row3}║{Colors.RESET}")

                left_row4 = self.pad_column(f"{Colors.CYAN}Daily P/L: {pl_symbol} {pl_color}{Colors.BOLD}${abs(p['daily_pl']):.2f}{Colors.RESET} {pl_color}({'+' if p['daily_pl_percent'] >= 0 else ''}{p['daily_pl_percent']:.2f}%){Colors.RESET}")
                right_row4 = self.pad_column(f"{Colors.CYAN}Total P/L: {pl_color}{Colors.BOLD}{'+' if p['daily_pl'] >= 0 else ''}${s.get('total_pl', 0):.2f}{Colors.RESET}")
                lines.append(f"{cyan}║ {left_row4}║ {right_row4}║{Colors.RESET}")

                left_row5 = self.pad_column(f"{Colors.CYAN}Positions: {Colors.YELLOW}{p['positions']}/{p.get('max_positions', 10)}{Colors.RESET}")

                # Activity indicator
                hot_signal_count = len(self.trading_data['hot_signals'])
                if hot_signal_count > 0:
                    activity_text = f"{Colors.CYAN}Activity: {Colors.hex('#FF4500')}🔥 {Colors.RED}{Colors.BOLD}{hot_signal_count} HOT{Colors.hex('#FF4500')} 🔥{Colors.RESET}"
                elif self.next_analysis_time:
                    seconds_until = max(0, int((self.next_analysis_time - datetime.now().timestamp()) * 1000) // 1000)
                    activity_text = f"{Colors.CYAN}Activity: {self.get_spinner()}{Colors.GRAY} Next scan in {seconds_until}s{Colors.RESET}"
                else:
                    activity_text = f"{Colors.CYAN}Activity: {self.get_spinner()}{Colors.GRAY} Analyzing...{Colors.RESET}"

                right_row5 = self.pad_column(activity_text)
                lines.append(f"{cyan}║ {left_row5}║ {right_row5}║{Colors.RESET}")

                left_row6 = self.pad_column(f"{self.get_progress_bar(position_usage, 45)} {Colors.GRAY}{position_usage:.0f}%{Colors.RESET}")
                right_row6 = self.pad_column('')
                lines.append(f"{cyan}║ {left_row6}║ {right_row6}║{Colors.RESET}")

                lines.append(f"{cyan}╚{'═' * 51}╩{'═' * 51}╝{Colors.RESET}")
            else:
                lines.append(f"{Colors.GRAY}Loading portfolio data...{Colors.RESET}")
                for _ in range(8):
                    lines.append('')

            lines.append('')

            # Positions and Market Heat
            lines.append(f"{cyan}╔{'═' * 51}╦{'═' * 51}╗{Colors.RESET}")

            left_header = self.pad_column(f"{gold}{Colors.BOLD}📈 OPEN POSITIONS{Colors.RESET}")
            right_header = self.pad_column(f"{gold}{Colors.BOLD}🔥 MARKET HEAT{Colors.RESET}")
            lines.append(f"{cyan}║ {left_header}║ {right_header}║{Colors.RESET}")

            lines.append(f"{cyan}╠{'═' * 51}╬{'═' * 51}╣{Colors.RESET}")

            max_rows = 8

            for i in range(max_rows):
                left_content = ''
                right_content = ''

                # Left side - Positions
                if i == 0:
                    if len(self.trading_data['positions']) == 0:
                        left_content = f"{Colors.GRAY}No open positions{Colors.RESET}"
                    else:
                        left_content = f"{Colors.CYAN}SYM    QTY    ENTRY    P/L $      P/L %{Colors.RESET}"
                elif i == 1 and len(self.trading_data['positions']) > 0:
                    left_content = f"{Colors.GRAY}{'─' * 49}{Colors.RESET}"
                elif i >= 2 and len(self.trading_data['positions']) > 0:
                    pos_index = i - 2
                    if pos_index < len(self.trading_data['positions']):
                        pos = self.trading_data['positions'][pos_index]
                        pl = pos['unrealized_pl']
                        pl_percent = pos['unrealized_plpc']
                        pl_color = Colors.GREEN if pl >= 0 else Colors.RED
                        pl_icon = '📈' if pl >= 0 else '📉'

                        # Format quantity with appropriate decimals (4 decimals for small amounts)
                        qty = pos['qty']
                        if qty < 0.01:
                            qty_str = f"{qty:<6.4f}"
                        else:
                            qty_str = f"{qty:<6.2f}"

                        left_content = (f"{pl_icon} {Colors.YELLOW}{pos['symbol']:<6}{Colors.RESET} "
                                      f"{Colors.WHITE}{qty_str}{Colors.RESET} "
                                      f"{Colors.WHITE}${pos['avg_entry_price']:<8.2f}{Colors.RESET} "
                                      f"{pl_color}{'+' if pl >= 0 else ''}${pl:<9.2f}{Colors.RESET} "
                                      f"{pl_color}{'+' if pl_percent >= 0 else ''}{pl_percent:.1f}%{Colors.RESET}")

                # Right side - Market Heat
                if i == 0:
                    if len(self.trading_data['market_heat']) == 0:
                        right_content = f"{Colors.GRAY}Scanning for opportunities...{Colors.RESET}"
                    else:
                        right_content = f"{Colors.CYAN}SYMBOL   DIR   STR  HEAT{Colors.RESET}"
                elif i == 1 and len(self.trading_data['market_heat']) > 0:
                    right_content = f"{Colors.GRAY}{'─' * 49}{Colors.RESET}"
                elif i >= 2 and len(self.trading_data['market_heat']) > 0:
                    heat_index = i - 2
                    if heat_index < len(self.trading_data['market_heat']):
                        heat = self.trading_data['market_heat'][heat_index]
                        signal_color = Colors.GREEN if heat['direction'] == 'BUY' else Colors.RED
                        heat_percent = (heat['strength'] / 55) * 100
                        heat_bar = self.get_heat_bar(heat_percent, 12)
                        temp_icon = self.get_temperature_icon(heat_percent)

                        right_content = (f"{Colors.YELLOW}{heat['symbol']:<8}{Colors.RESET} "
                                       f"{signal_color}{heat['direction'][:3]:<4}{Colors.RESET} "
                                       f"{Colors.WHITE}{heat['strength']:<3.0f}{Colors.RESET} "
                                       f"{temp_icon}{heat_bar}")

                left_padded = self.pad_column(left_content)
                right_padded = self.pad_column(right_content)
                lines.append(f"{cyan}║ {left_padded}║ {right_padded}║{Colors.RESET}")

            lines.append(f"{cyan}╚{'═' * 51}╩{'═' * 51}╝{Colors.RESET}")
            lines.append('')

            # Signals and Trades
            lines.append(f"{cyan}╔{'═' * 51}╦{'═' * 51}╗{Colors.RESET}")

            left_signal_header = self.pad_column(f"{gold}{Colors.BOLD}🎯 RECENT SIGNALS (Last 5){Colors.RESET}")
            right_trade_header = self.pad_column(f"{gold}{Colors.BOLD}💼 RECENT TRADES (Last 5){Colors.RESET}")
            lines.append(f"{cyan}║ {left_signal_header}║ {right_trade_header}║{Colors.RESET}")

            lines.append(f"{cyan}╠{'═' * 51}╬{'═' * 51}╣{Colors.RESET}")

            for i in range(5):
                left_content = ' ' * 49
                right_content = ' ' * 49

                if i < len(self.trading_data['signals']):
                    sig = self.trading_data['signals'][i]
                    time = datetime.fromisoformat(sig['timestamp']).strftime('%H:%M:%S')
                    signal_color = Colors.GREEN if sig['signal'] == 'BUY' else (Colors.RED if sig['signal'] == 'SELL' else Colors.YELLOW)
                    icon = '📈' if sig['signal'] == 'BUY' else '📉'

                    # Format: TIME ICON SIG SYM STR STRATEGY
                    left_content = (f"{Colors.GRAY}{time:<8} {Colors.RESET}{icon} "
                                  f"{signal_color}{Colors.BOLD}{sig['signal']:<4}{Colors.RESET} "
                                  f"{Colors.YELLOW}{sig['symbol']:<7}{Colors.RESET} "
                                  f"{Colors.WHITE}{sig['strength']:<3.0f}{Colors.RESET} "
                                  f"{Colors.GRAY}{sig.get('strategy', 'Default')[:13]:<13}{Colors.RESET}")
                elif i == 0 and len(self.trading_data['signals']) == 0:
                    left_content = f"{Colors.GRAY}No signals detected yet{Colors.RESET}"

                if i < len(self.trading_data['recent_trades']):
                    trade = self.trading_data['recent_trades'][i]
                    time = datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')
                    action_color = Colors.GREEN if trade['action'] == 'BUY' else Colors.RED
                    icon = '🟢' if trade['action'] == 'BUY' else '🔴'

                    # Format: TIME ICON ACTION SYM QTY
                    qty_text = f"Qty: {trade['qty']}"
                    right_content = (f"{Colors.GRAY}{time:<8} {Colors.RESET}{icon} "
                                   f"{action_color}{Colors.BOLD}{trade['action']:<4}{Colors.RESET} "
                                   f"{Colors.YELLOW}{trade['symbol']:<7}{Colors.RESET} "
                                   f"{Colors.WHITE}{qty_text:<20}{Colors.RESET}")
                elif i == 0 and len(self.trading_data['recent_trades']) == 0:
                    right_content = f"{Colors.GRAY}No trades executed yet{Colors.RESET}"

                lines.append(f"{cyan}║ {left_content}║ {right_content}║{Colors.RESET}")

            lines.append(f"{cyan}╚{'═' * 51}╩{'═' * 51}╝{Colors.RESET}")

            # Footer
            now = datetime.now()
            lines.append('')
            lines.append(f"{Colors.GRAY}  [Ctrl+C] Stop  │  {Colors.CYAN}Auto-update: Every 1s  │  "
                        f"{Colors.YELLOW}{now.strftime('%Y-%m-%d %H:%M:%S')}{Colors.GRAY}  │  "
                        f"{self.get_spinner()} {Colors.CYAN}Live{Colors.RESET}")

            # Print all lines
            for i, line in enumerate(lines):
                self.move_cursor(i + 1, 1)
                self.clear_line()
                sys.stdout.write(line)

            sys.stdout.flush()

        except Exception as error:
            # Log errors silently
            pass

    def update_portfolio(self, data: Dict):
        """Update portfolio data"""
        self.trading_data['portfolio'] = data

    def update_daily_stats(self, stats: Dict):
        """Update daily stats"""
        self.trading_data['daily_stats'] = stats

    def update_positions(self, positions: List):
        """Update positions"""
        self.trading_data['positions'] = positions

    def add_signal(self, signal: Dict):
        """Add signal to display"""
        self.trading_data['signals'].insert(0, signal)
        if len(self.trading_data['signals']) > 20:
            self.trading_data['signals'] = self.trading_data['signals'][:20]

        # Track hot signals
        if signal['strength'] >= 50:
            self.trading_data['hot_signals'].insert(0, signal)
            if len(self.trading_data['hot_signals']) > 5:
                self.trading_data['hot_signals'] = self.trading_data['hot_signals'][:5]

    def clear_hot_signals(self):
        """Clear hot signals"""
        self.trading_data['hot_signals'] = []

    def set_next_analysis_time(self, timestamp: float):
        """Set next analysis time"""
        self.next_analysis_time = timestamp

    def update_market_heat(self, heat_data: List[Dict]):
        """Update market heat display"""
        # Show all signals >= 10 strength, sorted by strength (lower threshold for better visibility)
        filtered = [h for h in heat_data if h['strength'] >= 10]
        self.trading_data['market_heat'] = sorted(filtered, key=lambda x: x['strength'], reverse=True)[:10]

    def add_trade(self, trade: Dict):
        """Add trade to display"""
        self.trading_data['recent_trades'].insert(0, trade)
        if len(self.trading_data['recent_trades']) > 20:
            self.trading_data['recent_trades'] = self.trading_data['recent_trades'][:20]

    def destroy(self):
        """Clean up dashboard"""
        # Show cursor
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()


# Global instance
dashboard = CoinbaseDashboard()
