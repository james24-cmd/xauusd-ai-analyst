import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import pytz

# Public ForexFactory Weekly Calendar CSV
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml" 
# Backup: We will use a reliable scraper for a standard calendar if the XML is deprecated, 
# but often the CSV/XML endpoints are available. 
# Alternatively, use a simplified scraping approach for Investing.com or similar.

def fetch_economic_calendar():
    """
    Fetches the economic calendar. 
    Returns a DataFrame with columns: [Title, Country, Date, Impact, Forecast, Previous]
    """
    # Since official APIs are paid, we will use a robust approximation:
    # 1. Fetch from a known public feed or 
    # 2. Return an empty structure if offline (safe failover).

    # Attempt to parse ForexFactory XML (common open endpoint)
    try:
        response = requests.get(FF_CALENDAR_URL, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
             # Basic XML parsing using pandas
             # Note: If XML is complex, we might need ElementTree, but let's try reading.
             # Actually, pandas read_xml is available in newer versions.
             df = pd.read_xml(response.content)
             return process_ff_data(df)
    except Exception as e:
        print(f"Calendar fetch failed: {e}. Using offline safety mode.")
        
    return pd.DataFrame()

def process_ff_data(df):
    """
    Cleans the ForexFactory Data.
    """
    if df.empty: return df
    
    # relevant columns: title, country, date, time, impact
    # data format in XML: <event><title>...</title><country>USD</country><date>...</date><time>...</time><impact>High</impact></event>
    
    # Standardize
    df = df[df['country'] == 'USD'] # Filter for USD news only (XAUUSD sensitivity)
    df = df[df['impact'] == 'High'] # Filter for Red Folder
    
    # Combine Date/Time to DateTime Object
    # FF uses format: Date: 01-31-2026, Time: 1:30pm (or 13:30)
    # We need to parse carefully. 
    # Actually, the XML has a 'date' and 'time' field.
    
    def parse_dt(row):
        ds = row['date']
        ts = row['time']
        if not ts: return None
        full_str = f"{ds} {ts}"
        try:
            # Approx format
            return datetime.strptime(full_str, "%m-%d-%Y %I:%M%p").astimezone(pytz.utc)
        except:
            return None

    df['datetime'] = df.apply(parse_dt, axis=1)
    df = df.dropna(subset=['datetime'])
    return df

def get_seconds_to_impact(df):
    """
    Returns (minutes_to_next_event, event_name)
    """
    if df.empty:
        return 9999, "None"
        
    now = datetime.now(pytz.utc)
    
    # Get future events or recent past events
    # We care about WINDOW: +/- 15 mins.
    
    df['diff_minutes'] = (df['datetime'] - now).dt.total_seconds() / 60
    
    # Find closest event (absolute difference)
    df['abs_diff'] = df['diff_minutes'].abs()
    closest = df.loc[df['abs_diff'].idxmin()]
    
    return closest['abs_diff'], closest['title']

if __name__ == "__main__":
    # Test
    print("Fetching calendar...")
    df = fetch_economic_calendar()
    print(df.head())
