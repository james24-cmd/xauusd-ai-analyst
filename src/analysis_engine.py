import pandas as pd
from typing import Dict, Any
from .news_loader import fetch_economic_calendar, get_seconds_to_impact
from .smc_detector import SMC_Detector
from .ml_classifier import SetupSuccessClassifier

class MarketAnalyst:
    def __init__(self, risk_manager, instrument_name="XAU/USD", asset_class="forex"):
        self.instrument_name = instrument_name
        self.asset_class = asset_class
        self.risk_manager = risk_manager
        self.news_df = fetch_economic_calendar()
        self.ml_classifier = SetupSuccessClassifier()

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes the 5-step Master System Prompt logic + SMC Analysis.
        """
        # --- SMC ANALYSIS FIRST ---
        smc = SMC_Detector(df)
        smc_data = smc.analyze_all()
        
        # Asset-specific thresholds
        if self.asset_class == "crypto":
            premium_threshold = 0.6  # Crypto more volatile, be lenient
        else:
            premium_threshold = 0.5  # Forex standard
        
        # Check Premium/Discount Zone (only trade shorts in premium)
        pd_zone = smc_data['premium_discount']
        
        # For crypto, we're more lenient with premium zones
        if self.asset_class == "crypto":
            valid_zones = ['Premium', 'Premium (Weak)', 'Equilibrium']
        else:
            valid_zones = ['Premium', 'Premium (Weak)']
        
        if pd_zone['zone'] not in valid_zones:
            return {
                "verdict": "NO TRADE",
                "reason": f"Not in Premium Zone (Current: {pd_zone['zone']})",
                "data": {"smc_zone": pd_zone['zone'], "instrument": self.instrument_name},
                "smc": smc_data
            }
        
        # Check for Bullish MSS (avoid shorts)
        mss = smc_data['market_structure_shift']
        if mss and mss['type'] == 'Bullish MSS':
            return {
                "verdict": "NO TRADE",
                "reason": "Bullish Market Structure Shift detected",
                "data": {},
                "smc": smc_data
            }
        
        # --- CHECK NEWS ---
        mins_to_event, event_name = get_seconds_to_impact(self.news_df)
        if mins_to_event <= 15:
            return {
                "verdict": "NO TRADE", 
                "reason": f"High Impact News: {event_name} in {mins_to_event:.0f} min", 
                "data": {"news_event_proximity_minutes": mins_to_event}
            }

        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        # --- STEP 1: HTF CONTEXT ---
        # Simple trend filter: Price < 50 SMA AND Price < 200 SMA = Bearish
        sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
        
        if current_candle['Close'] < sma_50 and current_candle['Close'] < sma_200:
            trend = "Bearish"
        elif current_candle['Close'] > sma_50 and current_candle['Close'] > sma_200:
            trend = "Bullish"
        else:
            trend = "Ranging"
            
        if trend == "Bullish":
            return {"verdict": "NO TRADE", "reason": "Strong Bullish Momentum", "data": {}}

        # --- STEP 2: LIQUIDITY & EXHAUSTION ---
        # Detect simple liquidity sweep: Current High > Previous 10 Highs but Close < Open (Rejection)
        lookback = 10
        recent_high = df['High'].iloc[-lookback:-1].max()
        
        liquidity_event = None
        if current_candle['High'] > recent_high:
            liquidity_event = "Local High Sweep"
        
        # Exhaustion: Large upper wick
        body_size = abs(current_candle['Close'] - current_candle['Open'])
        upper_wick = current_candle['High'] - max(current_candle['Close'], current_candle['Open'])
        is_exhaustion = upper_wick > (body_size * 1.5) # Wick is 1.5x body
        
        if not liquidity_event:
            return {"verdict": "NO TRADE", "reason": "No Liquidity Sweep", "data": {"instrument": self.instrument_name}}

        # --- STEP 3: CONFIRMATION METRICS ---
        rsi_div = False
        if current_candle['High'] > prev_candle['High'] and current_candle['RSI'] < prev_candle['RSI']:
            rsi_div = True # Bearish Divergence
            
        if not rsi_div and not is_exhaustion:
             return {"verdict": "NO TRADE", "reason": "No Confirmation (RSI/Wick)", "data": {}}

        # --- STEP 4: PROBABILITY (ML-Enhanced) ---
        # Get ML prediction
        ml_prob = self.ml_classifier.predict_success_probability(setup_data, smc_data)
        
        # Use ML probability if model is trained, otherwise use rule-based
        prob_score = ml_prob
        
        # --- BUILD PLAN ---
        entry_price = current_candle['Close']
        stop_loss = current_candle['High'] + (current_candle['High'] - current_candle['Low']) * 0.1 # Slight buffer
        risk = stop_loss - entry_price
        tp1 = entry_price - (risk * 2) # 1:2 RR
        
        rr_ratio = (entry_price - tp1) / risk if risk > 0 else 0
        
        setup_data = {
            "session": "Unknown", # Filled by main
            "htf_trend": trend,
            "htf_structure": "LH",
            "key_resistance_level": float(recent_high),
            "liquidity_event_type": liquidity_event,
            "has_large_wick": bool(is_exhaustion),
            "consecutive_bullish_candles": 0,
            "atr_value": float(current_candle['ATR']),
            "rsi_divergence": bool(rsi_div),
            "vwap_distance": float(abs(current_candle['Close'] - current_candle['VWAP'])),
            "volume_spike": False,
            "spread_value": 0.0, # Placeholder
            "news_event_proximity_minutes": 999
        }
        
        # Risk Check
        is_valid, risk_msg = self.risk_manager.validate_setup(rr_ratio, spread=0.1, prob_score=prob_score)
        
        if not is_valid:
            return {"verdict": "NO TRADE", "reason": risk_msg, "data": setup_data}
            
        trade_plan = {
            "direction": "SHORT",
            "entry_zone_start": float(entry_price),
            "entry_zone_end": float(entry_price + 1.0),
            "stop_loss": float(stop_loss),
            "tp1": float(tp1),
            "tp2": 0.0,
            "estimated_rr": float(rr_ratio),
            "probability_score": float(prob_score)
        }

        return {
            "verdict": "VALID SETUP",
            "reason": "All checks passed (SMC + Traditional)",
            "data": setup_data,
            "plan": trade_plan,
            "smc": smc_data
        }
