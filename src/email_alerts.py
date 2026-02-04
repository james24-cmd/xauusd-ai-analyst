import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'email_config.json')

def load_email_config():
    """Load email configuration from JSON file or environment variables."""
    # Try loading from environment variables first (for GitHub Actions)
    if os.getenv('EMAIL_USER') and os.getenv('EMAIL_PASSWORD'):
        return {
            'enabled': True,
            'sender_email': os.getenv('EMAIL_USER'),
            'sender_password': os.getenv('EMAIL_PASSWORD'),
            'recipient_email': os.getenv('EMAIL_RECIPIENT', os.getenv('EMAIL_USER')),
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587
        }
    
    # Fallback to JSON file
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def send_trade_alert(trade_plan: dict, market_data: dict, trade_id: int = None):
    """
    Send an email alert when a valid trade setup is detected.
    
    Args:
        trade_plan: Dict with entry, SL, TP, RR, etc.
        market_data: Dict with current price, trend, session info.
        trade_id: Database ID for this trade (for outcome tracking)
    """
    config = load_email_config()
    
    if not config or not config.get('enabled', False):
        print("[Email Alert] Disabled or not configured. Skipping.")
        return False
    
    # Calculate position sizing
    account_balance = 10000  # Default, can be config'd
    risk_percent = 0.5  # 0.5% per trade
    risk_amount = account_balance * (risk_percent / 100)
    
    entry = trade_plan.get('entry_zone_start', 0)
    sl = trade_plan.get('stop_loss', 0)
    tp1 = trade_plan.get('tp1', 0)
    rr = trade_plan.get('estimated_rr', 0)
    instrument = market_data.get('instrument', 'XAUUSD')
    
    sl_distance = abs(entry - sl)
    
    # Lot size calculation (simplified for Gold: 1 lot = $1 per pip)
    lot_size = risk_amount / (sl_distance * 10) if sl_distance > 0 else 0
    
    # Suggested leverage based on lot size (rough estimate)
    suggested_leverage = min(100, max(10, int(lot_size * 10)))
    
    # Create mailto links for one-click tracking
    sender_email = config['sender_email']
    tracking_subject = f"OUTCOME: {instrument} Trade #{trade_id}"
    
    win_link = f"mailto:{sender_email}?subject={tracking_subject}&body=WIN%20%23{trade_id}"
    loss_link = f"mailto:{sender_email}?subject={tracking_subject}&body=LOSS%20%23{trade_id}"
    breakeven_link = f"mailto:{sender_email}?subject={tracking_subject}&body=BREAKEVEN%20%23{trade_id}"
    partial_link = f"mailto:{sender_email}?subject={tracking_subject}&body=PARTIAL%20%23{trade_id}"
    
    # Determine Logic based on Direction
    direction = trade_plan.get('direction', 'SHORT')
    is_long = direction == 'LONG'
    
    # Theme Colors
    color_main = "#00ff88" if is_long else "#ff6b6b" # Green for Long, Red for Short
    color_sl = "#ff4444" # Always Red for SL
    color_tp = "#00ff88" # Always Green for TP
    title_color = "#00ff88" if is_long else "#e94560"
    
    # Emojis & Titles
    emoji_action = "LONG ⬆️" if is_long else "SHORT ⬇️"
    emoji_signal = "🟢" if is_long else "📉"
    
    # Create email content
    subject = f"🚨 {instrument} {direction} ALERT - TRADE #{trade_id}" if trade_id else f"🚨 {instrument} {direction} ALERT"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #1a1a2e; color: #eaeaea; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: #16213e; border-radius: 10px; padding: 20px;">
            <h1 style="color: {title_color}; text-align: center;">{emoji_signal} {instrument} {direction} SIGNAL</h1>
            
            {f'<div style="text-align: center; background: #0f3460; padding: 10px; border-radius: 5px; margin-bottom: 15px;"><h3 style="color: {color_main}; margin: 0;">TRADE ID: #{trade_id}</h3></div>' if trade_id else ''}
            
            <div style="background: #0f3460; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h2 style="color: {color_main}; margin-top: 0;">📊 Trade Details</h2>
                <table style="width: 100%; color: #eaeaea;">
                    <tr><td><b>Direction:</b></td><td style="color: {color_main};"><b>{emoji_action}</b></td></tr>
                    <tr><td><b>Entry Zone:</b></td><td>${entry:.2f} - ${trade_plan.get('entry_zone_end', entry):.2f}</td></tr>
                    <tr><td><b>Stop Loss:</b></td><td style="color: {color_sl};">${sl:.2f}</td></tr>
                    <tr><td><b>Take Profit 1:</b></td><td style="color: {color_tp};">${tp1:.2f}</td></tr>
                    <tr><td><b>Risk:Reward:</b></td><td>1:{rr:.1f}</td></tr>
                </table>
            </div>
            
            <div style="background: #0f3460; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h2 style="color: #ffd700; margin-top: 0;">💰 Position Sizing</h2>
                <table style="width: 100%; color: #eaeaea;">
                    <tr><td><b>Risk Amount:</b></td><td>${risk_amount:.2f} ({risk_percent}%)</td></tr>
                    <tr><td><b>SL Distance:</b></td><td>{sl_distance:.2f} pips</td></tr>
                    <tr><td><b>Suggested Lot Size:</b></td><td>{lot_size:.2f} lots</td></tr>
                    <tr><td><b>Suggested Leverage:</b></td><td>1:{suggested_leverage}</td></tr>
                </table>
            </div>
            
            <div style="background: #0f3460; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h2 style="color: #00bfff; margin-top: 0;">📈 Market Context</h2>
                <table style="width: 100%; color: #eaeaea;">
                    <tr><td><b>Session:</b></td><td>{market_data.get('session', 'N/A')}</td></tr>
                    <tr><td><b>Trend:</b></td><td>{market_data.get('htf_trend', 'N/A')}</td></tr>
                    <tr><td><b>Liquidity Event:</b></td><td>{market_data.get('liquidity_event_type', 'N/A')}</td></tr>
                    <tr><td><b>Probability:</b></td><td>{trade_plan.get('probability_score', 0):.0f}%</td></tr>
                </table>
            </div>
            
            {f'''
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h2 style="color: white; margin-top: 0; text-align: center;">🎯 ONE-CLICK OUTCOME TRACKING</h2>
                <p style="text-align: center; color: white; margin-bottom: 15px;">Click a button below when your trade completes:</p>
                
                <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                    <a href="{win_link}" style="display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px;">✅ WIN</a>
                    <a href="{loss_link}" style="display: inline-block; background: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px;">❌ LOSS</a>
                    <a href="{breakeven_link}" style="display: inline-block; background: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px;">➖ BREAKEVEN</a>
                    <a href="{partial_link}" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 5px;">📊 PARTIAL</a>
                </div>
                
                <p style="text-align: center; color: white; font-size: 0.85em; margin-top: 15px; opacity: 0.9;">
                    Clicking a button will open your email app with a pre-filled message.<br/>
                    Just click Send to record the outcome! 🧠
                </p>
            </div>
            ''' if trade_id else ''}
            
            <div style="text-align: center; margin-top: 20px; padding: 15px; background: {title_color}; border-radius: 8px;">
                <p style="margin: 0; font-weight: bold; color: {'#000' if is_long else '#fff'}">⚠️ MANUAL EXECUTION REQUIRED</p>
                <p style="margin: 5px 0; font-size: 0.9em; color: {'#000' if is_long else '#fff'}">This is an analysis alert, NOT financial advice.</p>
            </div>
            
            <p style="text-align: center; color: #888; font-size: 0.8em; margin-top: 20px;">
                Generated by Multi-Asset AI Terminal | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
            </p>
        </div>
    </body>
    </html>
    """
    
    # Send email
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = config['sender_email']
        msg['To'] = config['recipient_email']
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.sendmail(config['sender_email'], config['recipient_email'], msg.as_string())
        
        print("[Email Alert] ✅ Trade alert sent successfully!")
        return True
        
    except Exception as e:
        print(f"[Email Alert] ❌ Failed to send: {e}")
        return False

if __name__ == "__main__":
    # Test
    test_plan = {
        'entry_zone_start': 2045.50,
        'entry_zone_end': 2046.00,
        'stop_loss': 2048.50,
        'tp1': 2040.00,
        'estimated_rr': 2.5,
        'probability_score': 75
    }
    test_market = {
        'session': 'LONDON',
        'htf_trend': 'Bearish',
        'liquidity_event_type': 'Asian Sweep'
    }
    send_trade_alert(test_plan, test_market)
