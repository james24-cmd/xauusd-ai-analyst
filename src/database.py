import sqlite3
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database with the schema and ensure updates."""
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
        
    try:
        with get_connection() as conn:
            with open(SCHEMA_PATH, 'r') as f:
                # We don't want to wipe the DB every time, so be careful here
                conn.executescript(f.read())
    except sqlite3.OperationalError:
        # Ignore "table already exists" errors to allow migration to proceed
        pass
    except Exception as e:
        print(f"[Database] Init Warning: {e}")
            
    # Check for new columns and add them if missing (Schema Migration)
    _ensure_smc_columns()
    print(f"Database initialized/verified at {DB_PATH}")

def _ensure_smc_columns():
    """Add SMC columns to market_snapshots if they don't exist."""
    new_columns = {
        'premium_position': 'FLOAT',
        'in_premium_zone': 'BOOLEAN',
        'bearish_ob_count': 'INT',
        'bullish_ob_count': 'INT',
        'fvg_count': 'INT',
        'has_bearish_mss': 'BOOLEAN',
        'has_bullish_mss': 'BOOLEAN',
        # Outcome columns (initially added by email_checker, now standardized here)
        'outcome': 'TEXT',
        'realized_r_multiple': 'FLOAT',
        'outcome_recorded_at': 'TIMESTAMP'
    }
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(market_snapshots)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        
        for col_name, col_type in new_columns.items():
            if col_name not in existing_cols:
                print(f"[Database] Migrating: Adding column {col_name}...")
                try:
                    cursor.execute(f"ALTER TABLE market_snapshots ADD COLUMN {col_name} {col_type} DEFAULT 0")
                except Exception as e:
                    print(f"Migration error for {col_name}: {e}")

def save_snapshot(data: Dict[str, Any]) -> int:
    """Save a market snapshot and return the ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Ensure optional SMC keys exist in data (default to 0 if missing from old logic)
        smc_defaults = {
            'premium_position': 0.0, 'in_premium_zone': 0, 
            'bearish_ob_count': 0, 'bullish_ob_count': 0, 
            'fvg_count': 0, 'has_bearish_mss': 0, 'has_bullish_mss': 0
        }
        for k, v in smc_defaults.items():
            if k not in data:
                data[k] = v

        cursor.execute("""
            INSERT INTO market_snapshots (
                session, htf_trend, htf_structure, key_resistance_level,
                liquidity_event_type, has_large_wick, consecutive_bullish_candles,
                atr_value, rsi_divergence, vwap_distance, volume_spike,
                spread_value, news_event_proximity_minutes,
                
                premium_position, in_premium_zone, bearish_ob_count,
                bullish_ob_count, fvg_count, has_bearish_mss, has_bullish_mss
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['session'], data['htf_trend'], data['htf_structure'], data['key_resistance_level'],
            data['liquidity_event_type'], data['has_large_wick'], data['consecutive_bullish_candles'],
            data['atr_value'], data['rsi_divergence'], data['vwap_distance'], data['volume_spike'],
            data['spread_value'], data['news_event_proximity_minutes'],
            
            data['premium_position'], data['in_premium_zone'], data['bearish_ob_count'],
            data['bullish_ob_count'], data['fvg_count'], data['has_bearish_mss'], data['has_bullish_mss']
        ))
        return cursor.lastrowid

def save_trade_plan(snapshot_id: int, plan: Dict[str, Any]):
    """Save a valid trade plan."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO trade_plans (
                snapshot_id, direction, entry_zone_start, entry_zone_end,
                stop_loss, tp1, tp2, estimated_rr, probability_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id, plan['direction'], plan['entry_zone_start'], plan['entry_zone_end'],
            plan['stop_loss'], plan['tp1'], plan['tp2'], plan['estimated_rr'],
            plan['probability_score'], 'PENDING'
        ))

def get_recent_outcomes(limit=100):
    """Fetch recent trade outcomes for learning."""
    # Updated to pull from market_snapshots directly where outcome is set
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        
        # We need data + smc + outcome
        # Since we put everything in market_snapshots table now (including outcome via update), simpler query
        cursor = conn.execute("""
            SELECT * FROM market_snapshots 
            WHERE outcome IS NOT NULL 
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
