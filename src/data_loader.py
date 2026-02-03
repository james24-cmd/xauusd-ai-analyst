import yfinance as yf
import pandas as pd
import numpy as np
import time

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()

def calculate_vwap(df):
    v = df['Volume'].values
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    return df.assign(VWAP=(tp * v).cumsum() / v.cumsum())['VWAP']

def fetch_data(symbol="GC=F", period="5d", interval="15m"):
    """
    Fetches market data from Yahoo Finance.
    Defaults to Gold Futures (GC=F) which tracks XAUUSD.
    """
    print(f"Fetching data for {symbol}...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if not df.empty:
                break
                
            print(f"Attempt {attempt+1}/{max_retries} failed: Empty DataFrame. Retrying...")
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {e}. Retrying...")
            
        time.sleep(2)
        
    if df.empty:
        raise ValueError(f"Failed to fetch data for {symbol} after {max_retries} attempts.")
        
    # YFinance MultiIndex cleanup
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Calculate indicators needed for analysis manually
    df['RSI'] = calculate_rsi(df['Close'])
    df['ATR'] = calculate_atr(df)
    
    # Simple VWAP calculation
    df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    
    return df

def get_latest_price(df):
    return df['Close'].iloc[-1]
