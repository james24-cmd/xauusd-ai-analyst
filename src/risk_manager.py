import json
import os
from datetime import datetime

class RiskManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prop_firm_config.json')
        self.config = self._load_config()
        self.rules = self.config['risk_rules_locked']
        self.filters = self.config['filters']
        
        # Runtime state (in a real app, this should be persisted to DB or file)
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.current_daily_drawdown = 0.0

    def _load_config(self):
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def check_session(self, current_time_utc: datetime) -> str:
        """Returns 'LONDON', 'NEW_YORK' or None."""
        current_str = current_time_utc.strftime("%H:%M")
        
        london_start = self.config['trading_hours']['london_start_utc']
        london_end = self.config['trading_hours']['london_end_utc']
        ny_start = self.config['trading_hours']['new_york_start_utc']
        ny_end = self.config['trading_hours']['new_york_end_utc']
        
        if london_start <= current_str <= london_end:
            return "LONDON"
        if ny_start <= current_str <= ny_end:
            return "NEW_YORK"
        return None

    def can_trade(self, last_outcome_was_loss: bool = False) -> tuple[bool, str]:
        """core risk logic: Returns (Allowed, Reason)"""
        
        if last_outcome_was_loss:
            self.consecutive_losses += 1
        
        if self.daily_trades >= self.rules['max_trades_per_day']:
            return False, "Max daily trades reached"
        
        if self.consecutive_losses >= self.rules['consecutive_loss_stop_count']:
            return False, "Stopped due to consecutive losses"
            
        if self.current_daily_drawdown >= self.rules['max_daily_drawdown_percent']:
            return False, "Max daily drawdown reached"

        return True, "OK"

    def validate_setup(self, rr_ratio: float, spread: float, prob_score: float) -> tuple[bool, str]:
        if rr_ratio < self.rules['min_risk_reward_ratio']:
            return False, f"R:R {rr_ratio} < {self.rules['min_risk_reward_ratio']}"
            
        if spread > self.filters['max_spread_pips']:
            return False, f"Spread {spread} > {self.filters['max_spread_pips']}"
            
        if prob_score < self.filters['min_probability_threshold']:
            return False, f"Probability {prob_score}% < {self.filters['min_probability_threshold']}%"
            
        return True, "Valid"
    
    def record_trade(self):
        self.daily_trades += 1
