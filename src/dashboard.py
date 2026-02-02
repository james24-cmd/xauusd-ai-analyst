import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Path adjustment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import fetch_data
from src.analysis_engine import XAUUSD_Analyst
from src.risk_manager import RiskManager
from src.database import get_recent_outcomes

# Page Config
st.set_page_config(
    page_title="XAUUSD AI Terminal",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Terminal" Look
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #FAFAFA; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #262730; color: white; border: 1px solid #4B4B4B; }
    .stButton>button:hover { background-color: #3e404d; border-color: #FAFAFA; color: #FAFAFA; }
    .metric-box { border: 1px solid #333; padding: 20px; border-radius: 5px; background-color: #161920; margin-bottom: 15px; }
    .trend-up { color: #00BFFF !important; font-weight: bold; }
    .trend-down { color: #FF4444 !important; font-weight: bold; }
    .pip-box { font-size: 1.2em; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0; }
    .pip-up { background: linear-gradient(135deg, #001a33, #003366); border: 1px solid #00BFFF; }
    .pip-down { background: linear-gradient(135deg, #330000, #660000); border: 1px solid #FF4444; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🤖 AI Control Panel")
session_state = st.sidebar.radio("Force Session", ["AUTO", "LONDON", "NEW_YORK"])

if st.sidebar.button("🔄 Refresh Analysis"):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("Status: **ONLINE**")

# Main Layout
col1, col2 = st.columns([3, 1])

with col1:
    st.header("📉 Market Overview (XAUUSD / GC=F)")
    
    # 1. Fetch Data
    try:
        df = fetch_data(symbol="GC=F", period="5d", interval="15m")
        latest = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        # Calculate Pip Movement and Change
        pip_change = (latest['Close'] - prev_candle['Close']) * 10  # Gold: 1 pip = $0.10
        pct_change = ((latest['Close'] - prev_candle['Close']) / prev_candle['Close']) * 100
        daily_open = df[df.index.date == df.index[-1].date()]['Open'].iloc[0]
        daily_pct_change = ((latest['Close'] - daily_open) / daily_open) * 100
        
        # Determine Trend Direction
        is_bullish = latest['Close'] > prev_candle['Close']
        trend_class = "trend-up" if is_bullish else "trend-down"
        trend_text = "▲ BULLISH" if is_bullish else "▼ BEARISH"
        pip_class = "pip-up" if is_bullish else "pip-down"
        
        # Chart with colored background based on trend
        fig = go.Figure(data=[go.Candlestick(x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='Price',
                        increasing_line_color='#00BFFF',  # Blue for up
                        decreasing_line_color='#FF4444'   # Red for down
                        )])
                        
        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'], line=dict(color='orange', width=1), name='VWAP'))
        
        # Add 20 SMA
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='#888888', width=1, dash='dot'), name='SMA 20'))
        
        fig.update_layout(
            template='plotly_dark',
            xaxis_rangeslider_visible=False,
            height=550,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")
        df = pd.DataFrame() # Empty to prevent crash
        latest = None

with col2:
    st.header("🧠 Analysis")
    
    if latest is not None and not df.empty:
        # --- TREND INDICATOR ---
        st.markdown(f"""
        <div class="metric-box" style="text-align: center;">
            <h2 class="{trend_class}">{trend_text}</h2>
            <p style="font-size: 2em; margin: 0;">${latest['Close']:.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # --- PIP & CHANGE BOX ---
        pip_arrow = "▲" if is_bullish else "▼"
        st.markdown(f"""
        <div class="pip-box {pip_class}">
            <span style="font-size: 1.5em;">{pip_arrow} {abs(pip_change):.1f} pips</span><br>
            <span style="opacity: 0.8;">{pct_change:+.2f}% (Candle)</span><br>
            <span style="opacity: 0.8;">{daily_pct_change:+.2f}% (Daily)</span>
        </div>
        """, unsafe_allow_html=True)
        
        # --- KEY METRICS ---
        st.markdown(f"""
        <div class="metric-box">
            <p><b>RSI:</b> <span style="color:{'#FF4444' if latest['RSI']>70 else '#00FF00' if latest['RSI']<30 else '#888888'}">{latest['RSI']:.1f}</span></p>
            <p><b>ATR:</b> {latest['ATR']:.2f}</p>
            <p><b>VWAP:</b> ${latest['VWAP']:.2f}</p>
            <p><b>Spread:</b> ~{(latest['High'] - latest['Low']):.2f}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🔍 AI Verdict")
        
        # Run Logic
        risk_manager = RiskManager()
        
        # Handle Session
        if session_state == "AUTO":
             session_name = risk_manager.check_session(datetime.utcnow()) or "CLOSED"
        else:
            session_name = session_state
            
        st.caption(f"Session: {session_name}")
        
        if session_name == "CLOSED" and session_state == "AUTO":
            st.warning("Market Closed")
        else:
            analyst = XAUUSD_Analyst(risk_manager)
            result = analyst.analyze_market(df)
            
            if result['verdict'] == "VALID SETUP":
                st.success("✅ VALID SHORT SETUP")
                st.code(str(result['plan']), language='json')
                
                # Display SMC Data
                if 'smc' in result:
                    st.markdown("### 📊 Smart Money Concepts")
                    smc = result['smc']
                    pd_zone = smc['premium_discount']
                    
                    st.markdown(f"""
                    <div class="metric-box">
                        <p><b>Zone:</b> <span style="color: {'#00FF00' if 'Premium' in pd_zone['zone'] else '#FF4444'}">{pd_zone['zone']}</span> ({pd_zone['position']:.1%})</p>
                        <p><b>Order Blocks:</b> {len(smc['order_blocks']['bearish'])} Bearish</p>
                        <p><b>Fair Value Gaps:</b> {len(smc['fair_value_gaps'])} Active</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if smc['market_structure_shift']:
                        mss = smc['market_structure_shift']
                        st.info(f"🔄 {mss['type']}: {mss['implication']}")
                        
            else:
                st.error(f"❌ {result['verdict']}")
                st.warning(f"Reason: {result['reason']}")
                
                # Show SMC even on no-trade
                if 'smc' in result:
                    smc = result['smc']
                    pd_zone = smc['premium_discount']
                    st.caption(f"SMC Zone: {pd_zone['zone']} ({pd_zone['position']:.1%})")

# Bottom Section: Learning & History
st.markdown("---")
st.subheader("📚 Self-Learning & History")

outcomes = get_recent_outcomes(limit=10)
if outcomes:
    st.dataframe(pd.DataFrame(outcomes))
else:
    st.info("No historical trade outcomes recorded yet.")
