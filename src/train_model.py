"""
Script to retrain the ML model using feedback data from the database.
Rehydrates flattened DB rows into the structure expected by the classifier.
"""
import sys
import os
import pandas as pd

# Fix import paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_recent_outcomes
from src.ml_classifier import SetupSuccessClassifier

def rehydrate_smc_data(row):
    """Reconstruct SMC dictionary from flat DB columns."""
    
    # Reconstruct Premium/Discount
    # We only stored the float and valid bool, so we reconstruct 'zone' string for the classifier check
    pd_zone = "Premium" if row['in_premium_zone'] else "Discount"
    
    # Reconstruct Order Blocks (We stored counts, classifier checks len())
    bearish_obs = [0] * int(row.get('bearish_ob_count', 0))
    bullish_obs = [0] * int(row.get('bullish_ob_count', 0))
    
    # Reconstruct FVGs
    fvgs = [0] * int(row.get('fvg_count', 0))
    
    # Reconstruct MSS
    mss = None
    if row.get('has_bearish_mss'):
        mss = {'type': 'Bearish MSS'}
    elif row.get('has_bullish_mss'):
        mss = {'type': 'Bullish MSS'}
        
    return {
        'premium_discount': {
            'position': row['premium_position'],
            'zone': pd_zone
        },
        'order_blocks': {
            'bearish': bearish_obs,
            'bullish': bullish_obs
        },
        'fair_value_gaps': fvgs,
        'market_structure_shift': mss
    }

def train():
    print("🧠 Starting Self-Learning Protocol...")
    
    # 1. Fetch Data
    outcomes = get_recent_outcomes(limit=500)
    
    if not outcomes:
        print("⚠️ No trade outcomes found in database. Skipping training.")
        return
    
    print(f"📊 Found {len(outcomes)} training samples.")
    
    # 2. Prepare Data for Classifier
    training_data = []
    
    for row in outcomes:
        # Convert sqlite3.Row to dict
        row_dict = dict(row)
        
        # Prepare Inputs
        market_data = row_dict # Contains htf_trend, etc.
        smc_data = rehydrate_smc_data(row_dict)
        
        # Determine Label (Win = 1, Loss/BE = 0)
        # We use realized_r_multiple > 0.5 as "Success" (filters out BE/small wins)
        label = 1 if row_dict.get('realized_r_multiple', 0) > 0.5 else 0
        
        training_data.append({
            'market_data': market_data,
            'smc_data': smc_data,
            'outcome': label
        })
        
    df = pd.DataFrame(training_data)
    
    # 3. Train Model
    classifier = SetupSuccessClassifier()
    classifier.train_on_historical_data(df)
    
    print("✅ Model retraining complete.")

if __name__ == "__main__":
    train()
