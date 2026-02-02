import sqlite3
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the database with the schema."""
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
        
    with get_connection() as conn:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
    print(f"Database initialized at {DB_PATH}")

def save_snapshot(data: Dict[str, Any]) -> int:
    """Save a market snapshot and return the ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market_snapshots (
                session, htf_trend, htf_structure, key_resistance_level,
                liquidity_event_type, has_large_wick, consecutive_bullish_candles,
                atr_value, rsi_divergence, vwap_distance, volume_spike,
                spread_value, news_event_proximity_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['session'], data['htf_trend'], data['htf_structure'], data['key_resistance_level'],
            data['liquidity_event_type'], data['has_large_wick'], data['consecutive_bullish_candles'],
            data['atr_value'], data['rsi_divergence'], data['vwap_distance'], data['volume_spike'],
            data['spread_value'], data['news_event_proximity_minutes']
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
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM trade_outcomes 
            JOIN trade_plans ON trade_outcomes.plan_id = trade_plans.id
            JOIN market_snapshots ON trade_plans.snapshot_id = market_snapshots.id
            ORDER BY trade_outcomes.id DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
