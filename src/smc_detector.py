"""
Smart Money Concepts (SMC) Detection Module

Implements institutional trading concepts:
- Order Blocks
- Fair Value Gaps (FVG)
- Premium/Discount Zones (Fibonacci)
- Market Structure Shifts (MSS)
- Break of Structure (BOS)
- Change of Character (ChOCH)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class SMC_Detector:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.swing_lookback = 5  # Bars to look for swing highs/lows
        
    def detect_order_blocks(self, direction='bearish') -> List[Dict]:
        """
        Detect Order Blocks - zones where institutions placed large orders.
        
        Bearish OB: Last bullish candle before strong bearish move
        Bullish OB: Last bearish candle before strong bullish move
        """
        order_blocks = []
        
        for i in range(self.swing_lookback, len(self.df) - 1):
            current = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]
            
            if direction == 'bearish':
                # Look for bullish candle followed by strong bearish move
                is_bullish = current['Close'] > current['Open']
                strong_bearish = (next_candle['Close'] < current['Low']) and \
                                (next_candle['Close'] < next_candle['Open'])
                
                if is_bullish and strong_bearish:
                    order_blocks.append({
                        'type': 'Bearish OB',
                        'index': i,
                        'top': current['High'],
                        'bottom': current['Low'],
                        'strength': abs(next_candle['Close'] - current['Low'])
                    })
            
            elif direction == 'bullish':
                # Look for bearish candle followed by strong bullish move
                is_bearish = current['Close'] < current['Open']
                strong_bullish = (next_candle['Close'] > current['High']) and \
                                (next_candle['Close'] > next_candle['Open'])
                
                if is_bearish and strong_bullish:
                    order_blocks.append({
                        'type': 'Bullish OB',
                        'index': i,
                        'top': current['High'],
                        'bottom': current['Low'],
                        'strength': abs(next_candle['Close'] - current['High'])
                    })
        
        # Return most recent and strongest OBs
        if order_blocks:
            order_blocks = sorted(order_blocks, key=lambda x: x['strength'], reverse=True)
            return order_blocks[:3]  # Top 3
        return []
    
    def detect_fvg(self) -> List[Dict]:
        """
        Detect Fair Value Gaps - imbalances in price action.
        
        Bearish FVG: Gap between candle[i-2].low and candle[i].high
        Bullish FVG: Gap between candle[i-2].high and candle[i].low
        """
        fvgs = []
        
        for i in range(2, len(self.df)):
            candle_before = self.df.iloc[i - 2]
            candle_middle = self.df.iloc[i - 1]
            candle_current = self.df.iloc[i]
            
            # Bearish FVG
            if candle_before['Low'] > candle_current['High']:
                gap_size = candle_before['Low'] - candle_current['High']
                fvgs.append({
                    'type': 'Bearish FVG',
                    'index': i,
                    'top': candle_before['Low'],
                    'bottom': candle_current['High'],
                    'size': gap_size
                })
            
            # Bullish FVG
            elif candle_before['High'] < candle_current['Low']:
                gap_size = candle_current['Low'] - candle_before['High']
                fvgs.append({
                    'type': 'Bullish FVG',
                    'index': i,
                    'top': candle_current['Low'],
                    'bottom': candle_before['High'],
                    'size': gap_size
                })
        
        # Return most recent unfilled FVGs
        return fvgs[-5:] if fvgs else []
    
    def calculate_premium_discount(self) -> Dict:
        """
        Calculate Premium/Discount zones using Fibonacci levels.
        
        Premium: 0.5 - 1.0 (expensive, good for shorts)
        Equilibrium: 0.5
        Discount: 0.0 - 0.5 (cheap, good for longs)
        """
        recent_data = self.df.tail(50)  # Last 50 candles
        high = recent_data['High'].max()
        low = recent_data['Low'].min()
        current_price = self.df['Close'].iloc[-1]
        
        range_size = high - low
        
        # Fibonacci levels
        levels = {
            '1.0 (High)': high,
            '0.786': high - (range_size * 0.214),
            '0.618 (Golden)': high - (range_size * 0.382),
            '0.5 (Equilibrium)': high - (range_size * 0.5),
            '0.382': high - (range_size * 0.618),
            '0.236': high - (range_size * 0.764),
            '0.0 (Low)': low
        }
        
        # Determine current zone
        position = (current_price - low) / range_size if range_size > 0 else 0.5
        
        if position > 0.618:
            zone = "Premium"
            strength = "STRONG SHORT ZONE"
        elif position > 0.5:
            zone = "Premium (Weak)"
            strength = "MODERATE SHORT ZONE"
        elif position > 0.382:
            zone = "Equilibrium"
            strength = "NEUTRAL ZONE"
        else:
            zone = "Discount"
            strength = "LONG ZONE (Skip for short-only)"
        
        return {
            'current_price': float(current_price),
            'position': float(position),
            'zone': zone,
            'strength': strength,
            'levels': {k: float(v) for k, v in levels.items()}
        }
    
    def detect_market_structure_shift(self) -> Optional[Dict]:
        """
        Detect Market Structure Shift (MSS) / Change of Character (ChOCH).
        
        Bearish MSS: Break below previous higher low
        Bullish MSS: Break above previous lower high
        """
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(self.swing_lookback, len(self.df) - self.swing_lookback):
            window = self.df.iloc[i - self.swing_lookback:i + self.swing_lookback + 1]
            current = self.df.iloc[i]
            
            # Swing High
            if current['High'] == window['High'].max():
                swing_highs.append({'index': i, 'price': current['High']})
            
            # Swing Low
            if current['Low'] == window['Low'].min():
                swing_lows.append({'index': i, 'price': current['Low']})
        
        # Check for MSS
        current_price = self.df['Close'].iloc[-1]
        
        # Bearish MSS: Broke below recent higher low
        if len(swing_lows) >= 2:
            recent_lows = swing_lows[-2:]
            if recent_lows[1]['price'] > recent_lows[0]['price']:  # Higher low formed
                if current_price < recent_lows[1]['price']:  # Now broke below it
                    return {
                        'type': 'Bearish MSS',
                        'broken_level': recent_lows[1]['price'],
                        'strength': 'Strong',
                        'implication': 'Trend reversal to downside'
                    }
        
        # Bullish MSS: Broke above recent lower high
        if len(swing_highs) >= 2:
            recent_highs = swing_highs[-2:]
            if recent_highs[1]['price'] < recent_highs[0]['price']:  # Lower high formed
                if current_price > recent_highs[1]['price']:  # Now broke above it
                    return {
                        'type': 'Bullish MSS',
                        'broken_level': recent_highs[1]['price'],
                        'strength': 'Strong',
                        'implication': 'Trend reversal to upside (avoid shorts)'
                    }
        
        return None
    
    def analyze_all(self) -> Dict:
        """
        Run all SMC analysis and return comprehensive results.
        """
        return {
            'order_blocks': {
                'bearish': self.detect_order_blocks('bearish'),
                'bullish': self.detect_order_blocks('bullish')
            },
            'fair_value_gaps': self.detect_fvg(),
            'premium_discount': self.calculate_premium_discount(),
            'market_structure_shift': self.detect_market_structure_shift()
        }

def format_smc_summary(smc_data: Dict) -> str:
    """Format SMC data for display."""
    pd_zone = smc_data['premium_discount']
    mss = smc_data['market_structure_shift']
    
    summary = f"""
    SMC Analysis:
    - Zone: {pd_zone['zone']} ({pd_zone['position']:.1%})
    - {pd_zone['strength']}
    - OB Found: {len(smc_data['order_blocks']['bearish'])} Bearish
    - FVGs: {len(smc_data['fair_value_gaps'])} Active
    """
    
    if mss:
        summary += f"\n- MSS: {mss['type']} - {mss['implication']}"
    
    return summary.strip()

if __name__ == "__main__":
    # Test with sample data
    import yfinance as yf
    df = yf.download("GC=F", period="5d", interval="15m", progress=False)
    
    smc = SMC_Detector(df)
    results = smc.analyze_all()
    
    print(format_smc_summary(results))
