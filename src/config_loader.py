import json
from typing import List, Dict, Optional
import os

def load_trading_config(config_path='trading_config.json') -> Dict:
    """Load and validate trading configuration"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Trading config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Validate structure
    if 'active_instruments' not in config:
        raise ValueError("Config must contain 'active_instruments'")
    
    if len(config['active_instruments']) == 0:
        raise ValueError("At least one instrument must be configured")
    
    return config

def get_enabled_instruments(config: Dict) -> List[Dict]:
    """Get only enabled instruments from config"""
    return [i for i in config['active_instruments'] if i.get('enabled', False)]

def get_instrument_by_name(config: Dict, display_name: str) -> Optional[Dict]:
    """Get instrument configuration by display name"""
    for instrument in config['active_instruments']:
        if instrument['display_name'] == display_name:
            return instrument
    return None

def get_asset_settings(config: Dict, asset_class: str) -> Dict:
    """Get analysis settings for specific asset class"""
    return config.get('analysis_settings', {}).get(asset_class, {})

def get_risk_settings(config: Dict) -> Dict:
    """Get global risk settings"""
    return config.get('risk_settings', {
        'risk_per_instrument_percent': 1.0,
        'max_concurrent_trades': 3,
        'max_alerts_per_run': 5
    })
