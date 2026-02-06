"""
Test Email Alert System
This script sends a test trade alert to verify email configuration is working
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.email_alerts import send_trade_alert

print("🧪 Testing Email Alert System...\n")
print("=" * 60)

# Create a realistic mock trade setup
mock_plan = {
    "direction": "SHORT",
    "entry_zone_start": 2645.50,
    "entry_zone_end": 2647.00,
    "stop_loss": 2653.20,
    "tp1": 2629.00,
    "tp2": 2615.00,
    "estimated_rr": 2.5,
    "probability_score": 0.78
}

mock_data = {
    "session": "LONDON",
    "instrument": "XAU/USD (TEST)",
    "htf_trend": "Bearish",
    "htf_structure": "LH",
    "key_resistance_level": 2648.50,
    "liquidity_event_type": "Local High Sweep",
    "has_large_wick": True,
    "consecutive_bullish_candles": 2,
    "atr_value": 8.5,
    "rsi_divergence": True,
    "vwap_distance": 12.3,
    "volume_spike": False,
    "spread_value": 0.5,
    "news_event_proximity_minutes": 999
}

print("📧 Sending TEST trade alert...")
print(f"\nInstrument: {mock_data['instrument']}")
print(f"Direction: {mock_plan['direction']}")
print(f"Entry: {mock_plan['entry_zone_start']}")
print(f"Stop Loss: {mock_plan['stop_loss']}")
print(f"Take Profit 1: {mock_plan['tp1']}")
print(f"R:R Ratio: {mock_plan['estimated_rr']}")
print(f"Probability: {mock_plan['probability_score'] * 100}%")
print("\n" + "=" * 60)

try:
    send_trade_alert(mock_plan, mock_data)
    print("\n✅ TEST EMAIL SENT SUCCESSFULLY!")
    print("\n📬 Check your email inbox for:")
    print("   Subject: 🚨 XAUUSD Short Setup - Premium Zone Rejection")
    print("   From: Your configured EMAIL_USER")
    print("   To: Your configured EMAIL_RECIPIENT")
    print("\n⚠️  Note: This is a TEST alert with mock data")
    print("   Real alerts will have live market data")
except Exception as e:
    print(f"\n❌ ERROR sending email: {e}")
    print("\nPossible issues:")
    print("   - EMAIL_USER, EMAIL_PASSWORD, or EMAIL_RECIPIENT not set")
    print("   - Invalid Gmail App Password")
    print("   - Network/firewall blocking SMTP")

print("\n" + "=" * 60)
