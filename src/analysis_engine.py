import pandas as pd
from typing import Dict, Any
from .news_loader import fetch_economic_calendar, get_seconds_to_impact
from .smc_detector import SMC_Detector
from .ml_classifier import SetupSuccessClassifier

class MarketAnalyst:
    def __init__(self, risk_manager, instrument_name="XAU/USD", asset_class="forex", target_direction="SHORT"):
        self.instrument_name = instrument_name
        self.asset_class = asset_class
        self.risk_manager = risk_manager
        self.news_df = fetch_economic_calendar()
        self.ml_classifier = SetupSuccessClassifier()
        self.target_direction = target_direction  # 'SHORT', 'LONG', 'BOTH'

    def analyze_market(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Executes the 5-step Master System Prompt logic + SMC Analysis.
        Now supports LONG (Bullish) and SHORT (Bearish) based on target_direction.
        """
        # --- SMC ANALYSIS FIRST ---
        smc = SMC_Detector(df)
        smc_data = smc.analyze_all()
        
        # --- CHECK NEWS (Global Filter) ---
        mins_to_event, event_name = get_seconds_to_impact(self.news_df)
        if mins_to_event <= 15:
            return {
                "verdict": "NO TRADE", 
                "reason": f"High Impact News: {event_name} in {mins_to_event:.0f} min", 
                "data": {"news_event_proximity_minutes": mins_to_event}
            }

        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        # --- STEP 1: HTF CONTEXT (Trend) ---
        # RELAXED: Only check 50 SMA for trend direction
        sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
        
        if current_candle['Close'] < sma_50:
            trend = "Bearish"
        elif current_candle['Close'] > sma_50:
            trend = "Bullish"
        else:
            trend = "Ranging" # Rare to be exact match

        # === SHORT ANALYSIS (Original) ===
        if self.target_direction in ['SHORT', 'BOTH']:
            if trend == "Bullish":
                # For SHORT, we abort if bullish (unless in BOTH mode we just skip to checking LONG)
                if self.target_direction == 'SHORT':
                    return {"verdict": "NO TRADE", "reason": "Strong Bullish Momentum", "data": {}}
            
            # If Bearish or Ranging, check for Short
            if trend != "Bullish":
                short_result = self._analyze_short_setup(df, smc_data, trend, current_candle, prev_candle)
                if short_result['verdict'] == "VALID SETUP":
                    return short_result
                    
        # === LONG ANALYSIS (New) ===
        if self.target_direction in ['LONG', 'BOTH']:
            if trend == "Bearish":
                if self.target_direction == 'LONG':
                    return {"verdict": "NO TRADE", "reason": "Strong Bearish Momentum", "data": {}}
            
            if trend != "Bearish":
                long_result = self._analyze_long_setup(df, smc_data, trend, current_candle, prev_candle)
                if long_result['verdict'] == "VALID SETUP":
                    return long_result

        return {"verdict": "NO TRADE", "reason": "No valid setup found in requested direction", "data": {"instrument": self.instrument_name}}

    def _analyze_short_setup(self, df, smc_data, trend, current_candle, prev_candle):
        """Original Bearish analysis logic"""
        # Check Premium/Discount Zone
        pd_zone = smc_data['premium_discount']
        # RELAXED: Allow Equilibrium for all assets
        valid_zones = ['Premium', 'Premium (Weak)', 'Equilibrium']
        
        if pd_zone['zone'] not in valid_zones:
            return {"verdict": "NO TRADE", "reason": f"Not in Premium Zone (Current: {pd_zone['zone']})", "data": {}, "smc": smc_data}

        # Check for Bullish MSS (avoid shorts)
        mss = smc_data['market_structure_shift']
        if mss and mss['type'] == 'Bullish MSS':
            return {"verdict": "NO TRADE", "reason": "Bullish Market Structure Shift detected", "data": {}, "smc": smc_data}

        # Liquidity Sweep (Highs)
        lookback = 10
        recent_high = df['High'].iloc[-lookback:-1].max()
        liquidity_event = "Local High Sweep" if current_candle['High'] > recent_high else None
        
        # Exhaustion
        body_size = abs(current_candle['Close'] - current_candle['Open'])
        upper_wick = current_candle['High'] - max(current_candle['Close'], current_candle['Open'])
        # RELAXED: Reduced from 1.5x to 1.0x
        is_exhaustion = upper_wick >= (body_size * 1.0)

        if not liquidity_event:
            return {"verdict": "NO TRADE", "reason": "No Liquidity Sweep (Highs)", "data": {}}

        # RSI Div
        rsi_div = (current_candle['High'] > prev_candle['High'] and current_candle['RSI'] < prev_candle['RSI'])
        
        if not rsi_div and not is_exhaustion:
            return {"verdict": "NO TRADE", "reason": "No Confirmation (RSI/Wick)", "data": {}}

        # Build Setup
        entry_price = current_candle['Close']
        stop_loss = current_candle['High'] + (current_candle['High'] - current_candle['Low']) * 0.1
        risk = stop_loss - entry_price
        tp1 = entry_price - (risk * 2)
        rr_ratio = (entry_price - tp1) / risk if risk > 0 else 0
        
        # ... (ML and Validation Logic similar to before, summarized for brevity/common function)
        return self._finalize_setup(entry_price, stop_loss, tp1, rr_ratio, "SHORT", trend, liquidity_event, is_exhaustion, rsi_div, current_candle, smc_data)

    def _analyze_long_setup(self, df, smc_data, trend, current_candle, prev_candle):
        """New Bullish analysis logic"""
        # Check Premium/Discount Zone
        pd_zone = smc_data['premium_discount']
        # RELAXED: Allow Equilibrium for all assets
        valid_zones = ['Discount', 'Discount (Weak)', 'Equilibrium']
        
        if pd_zone['zone'] not in valid_zones:
            return {"verdict": "NO TRADE", "reason": f"Not in Discount Zone (Current: {pd_zone['zone']})", "data": {}, "smc": smc_data}

        # Check for Bearish MSS (avoid longs)
        mss = smc_data['market_structure_shift']
        if mss and mss['type'] == 'Bearish MSS':
            return {"verdict": "NO TRADE", "reason": "Bearish Market Structure Shift detected", "data": {}, "smc": smc_data}

        # Liquidity Sweep (Lows)
        lookback = 10
        recent_low = df['Low'].iloc[-lookback:-1].min()
        liquidity_event = "Local Low Sweep" if current_candle['Low'] < recent_low else None
        
        # Exhaustion (Lower Wick)
        body_size = abs(current_candle['Close'] - current_candle['Open'])
        lower_wick = min(current_candle['Close'], current_candle['Open']) - current_candle['Low']
        # RELAXED: Reduced from 1.5x to 1.0x
        is_exhaustion = lower_wick >= (body_size * 1.0)

        if not liquidity_event:
            return {"verdict": "NO TRADE", "reason": "No Liquidity Sweep (Lows)", "data": {}}

        # RSI Div (Bullish: Lower Low in Price, Higher Low in RSI)
        rsi_div = (current_candle['Low'] < prev_candle['Low'] and current_candle['RSI'] > prev_candle['RSI'])
        
        if not rsi_div and not is_exhaustion:
            return {"verdict": "NO TRADE", "reason": "No Confirmation (RSI/Wick)", "data": {}}

        # Build Setup
        entry_price = current_candle['Close']
        stop_loss = current_candle['Low'] - (current_candle['High'] - current_candle['Low']) * 0.1
        risk = entry_price - stop_loss
        tp1 = entry_price + (risk * 2)
        rr_ratio = (tp1 - entry_price) / risk if risk > 0 else 0
        
        return self._finalize_setup(entry_price, stop_loss, tp1, rr_ratio, "LONG", trend, liquidity_event, is_exhaustion, rsi_div, current_candle, smc_data)

    def _finalize_setup(self, entry, sl, tp1, rr, direction, trend, liq_event, exhaust, rsi, candle, smc_data):
        setup_data = {
            "session": "Unknown",
            "htf_trend": trend,
            "htf_structure": "LH" if direction == "SHORT" else "HL",
            "key_resistance_level": 0.0,
            "liquidity_event_type": liq_event,
            "has_large_wick": bool(exhaust),
            "consecutive_bullish_candles": 0,
            "atr_value": float(candle['ATR']),
            "rsi_divergence": bool(rsi),
            "vwap_distance": float(abs(candle['Close'] - candle['VWAP'])),
            "volume_spike": False,
            "spread_value": 0.0,
            "news_event_proximity_minutes": 999,
            
            # SMC Features
            "premium_position": float(smc_data['premium_discount']['position']),
            "in_premium_zone": 1 if 'Premium' in smc_data['premium_discount']['zone'] else 0,
            "bearish_ob_count": len(smc_data['order_blocks']['bearish']),
            "bullish_ob_count": len(smc_data['order_blocks']['bullish']),
            "fvg_count": len(smc_data['fair_value_gaps']),
            "has_bearish_mss": 1 if (smc_data['market_structure_shift'] and smc_data['market_structure_shift']['type'] == 'Bearish MSS') else 0,
            "has_bullish_mss": 1 if (smc_data['market_structure_shift'] and smc_data['market_structure_shift']['type'] == 'Bullish MSS') else 0
        }
        
        ml_prob = self.ml_classifier.predict_success_probability(setup_data, smc_data)
        
        is_valid, risk_msg = self.risk_manager.validate_setup(rr, spread=0.1, prob_score=ml_prob)
        
        if not is_valid:
            return {"verdict": "NO TRADE", "reason": risk_msg, "data": setup_data}
            
        trade_plan = {
            "direction": direction,
            "entry_zone_start": float(entry),
            "entry_zone_end": float(entry + 1.0 if direction == "SHORT" else entry - 1.0),
            "stop_loss": float(sl),
            "tp1": float(tp1),
            "tp2": 0.0,
            "estimated_rr": float(rr),
            "probability_score": float(ml_prob)
        }

        return {
            "verdict": "VALID SETUP",
            "reason": "All checks passed",
            "data": setup_data,
            "plan": trade_plan,
            "smc": smc_data
        }
