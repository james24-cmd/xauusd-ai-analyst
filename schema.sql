-- Database Schema for XAUUSD Analyst & Self-Learning Module

-- Table: market_snapshots
-- Captures the state of the market at the time of analysis.
CREATE TABLE market_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    session VARCHAR(20) NOT NULL, -- London, New York, etc.
    
    -- HTF Context
    htf_trend VARCHAR(20),       -- Bearish, Bullish, Ranging
    htf_structure VARCHAR(50),   -- HH, LH, Range...
    key_resistance_level DECIMAL(10, 2),
    
    -- Liquidity & Exhaustion
    liquidity_event_type VARCHAR(50), -- Asian Sweep, Prev High Sweep...
    has_large_wick BOOLEAN,
    consecutive_bullish_candles INT,
    atr_value DECIMAL(10, 4),
    
    -- Confirmation Metrics
    rsi_divergence BOOLEAN,
    vwap_distance DECIMAL(10, 2),
    volume_spike BOOLEAN,
    spread_value DECIMAL(10, 4),
    
    -- Metadata
    news_event_proximity_minutes INT
);

-- Table: trade_plans
-- Stores the generated manual trade plans (valid setups).
CREATE TABLE trade_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    direction VARCHAR(5) DEFAULT 'SHORT',
    entry_zone_start DECIMAL(10, 2),
    entry_zone_end DECIMAL(10, 2),
    stop_loss DECIMAL(10, 2),
    tp1 DECIMAL(10, 2),
    tp2 DECIMAL(10, 2),
    estimated_rr DECIMAL(5, 2),
    probability_score DECIMAL(5, 2), -- The internal 70%+ check
    
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, EXECUTED, CANCELLED, IGNORED
    
    FOREIGN KEY (snapshot_id) REFERENCES market_snapshots(id)
);

-- Table: trade_outcomes
-- Stores the actual results for VALIDATED setups (input for learning).
-- This is what the "Self-Learning" module reads.
CREATE TABLE trade_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER,
    
    entry_price DECIMAL(10, 2),
    exit_price DECIMAL(10, 2),
    
    outcome VARCHAR(10), -- WIN, LOSS, BREAK_EVEN
    realized_r_multiple DECIMAL(5, 2),
    pnl_percent DECIMAL(5, 2),
    
    comments TEXT,
    
    FOREIGN KEY (plan_id) REFERENCES trade_plans(id)
);

-- Table: learning_logs
-- Stores the output of the Weekly Review (Mode 2)
CREATE TABLE learning_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    sample_size INT,
    
    high_performing_conditions TEXT,
    loss_prone_conditions TEXT,
    strongest_filters TEXT,
    regime_notes TEXT,
    
    action_items TEXT -- e.g., "Tighten VWAP filter to > 10.0"
);

-- Index for fast retrieval during learning mode
CREATE INDEX idx_snapshot_session ON market_snapshots(session);
CREATE INDEX idx_outcome_r ON trade_outcomes(realized_r_multiple);
