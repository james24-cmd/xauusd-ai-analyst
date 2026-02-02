"""
ML-based Setup Success Classifier

Uses XGBoost to predict the probability of trade setup success based on:
- SMC indicators (OB, FVG, Premium/Discount)
- Traditional indicators (RSI, ATR, VWAP)
- Market structure (trend, liquidity events)

Philosophy: Enhance rule-based system, don't replace it.
"""

import pandas as pd
import numpy as np
import pickle
import os
from typing import Dict, Optional
from datetime import datetime

try:
    from xgboost import XGBClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[ML Classifier] XGBoost not installed. Running in rule-based mode only.")

class SetupSuccessClassifier:
    def __init__(self, model_path='models/setup_classifier.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_importance = {}
        
        if SKLEARN_AVAILABLE:
            self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    saved = pickle.load(f)
                    self.model = saved['model']
                    self.scaler = saved['scaler']
                    self.feature_importance = saved.get('importance', {})
                print(f"[ML Classifier] Model loaded from {self.model_path}")
            except Exception as e:
                print(f"[ML Classifier] Error loading model: {e}. Creating new.")
                self._create_new_model()
        else:
            self._create_new_model()
    
    def _create_new_model(self):
        """Create new untrained model."""
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        self.scaler = StandardScaler()
        print("[ML Classifier] New model created (untrained)")
    
    def extract_features(self, market_data: Dict, smc_data: Dict) -> pd.DataFrame:
        """
        Extract features from market data and SMC analysis.
        
        Features:
        - HTF trend (encoded)
        - Liquidity event presence
        - RSI divergence
        - Large wick presence
        - SMC premium/discount position
        - Order block count
        - FVG count
        - ATR normalized
        - VWAP distance
        - MSS presence
        """
        features = {
            # Traditional
            'trend_bearish': 1 if market_data.get('htf_trend') == 'Bearish' else 0,
            'trend_ranging': 1 if market_data.get('htf_trend') == 'Ranging' else 0,
            'has_liquidity_event': 1 if market_data.get('liquidity_event_type') else 0,
            'rsi_divergence': 1 if market_data.get('rsi_divergence') else 0,
            'large_wick': 1 if market_data.get('has_large_wick') else 0,
            'atr_value': market_data.get('atr_value', 0),
            'vwap_distance': market_data.get('vwap_distance', 0),
            
            # SMC
            'premium_position': smc_data['premium_discount']['position'],
            'in_premium': 1 if 'Premium' in smc_data['premium_discount']['zone'] else 0,
            'bearish_ob_count': len(smc_data['order_blocks']['bearish']),
            'bullish_ob_count': len(smc_data['order_blocks']['bullish']),
            'fvg_count': len(smc_data['fair_value_gaps']),
            'has_bearish_mss': 1 if (smc_data['market_structure_shift'] and 
                                     smc_data['market_structure_shift']['type'] == 'Bearish MSS') else 0,
            'has_bullish_mss': 1 if (smc_data['market_structure_shift'] and 
                                     smc_data['market_structure_shift']['type'] == 'Bullish MSS') else 0,
        }
        
        return pd.DataFrame([features])
    
    def predict_success_probability(self, market_data: Dict, smc_data: Dict) -> float:
        """
        Predict probability of setup success (0-100%).
        
        Returns:
            Probability score (0-100) or fallback to rule-based if model untrained
        """
        if not SKLEARN_AVAILABLE or self.model is None:
            return self._fallback_probability(market_data, smc_data)
        
        try:
            features = self.extract_features(market_data, smc_data)
            
            # Check if model is fitted
            if not hasattr(self.model, 'feature_importances_'):
                return self._fallback_probability(market_data, smc_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict probability
            prob = self.model.predict_proba(features_scaled)[0][1] * 100  # Class 1 (success)
            
            return float(prob)
            
        except Exception as e:
            print(f"[ML Classifier] Prediction error: {e}. Using fallback.")
            return self._fallback_probability(market_data, smc_data)
    
    def _fallback_probability(self, market_data: Dict, smc_data: Dict) -> float:
        """Rule-based probability when ML not available."""
        prob = 0
        
        # Traditional factors
        if market_data.get('htf_trend') == 'Bearish': prob += 30
        if market_data.get('liquidity_event_type'): prob += 25
        if market_data.get('rsi_divergence'): prob += 10
        if market_data.get('has_large_wick'): prob += 10
        
        # SMC factors
        pd_zone = smc_data['premium_discount']
        if pd_zone['position'] > 0.7: prob += 15
        if len(smc_data['order_blocks']['bearish']) > 0: prob += 10
        
        mss = smc_data['market_structure_shift']
        if mss and mss['type'] == 'Bearish MSS': prob += 10
        
        return min(prob, 100)
    
    def train_on_historical_data(self, historical_df: pd.DataFrame):
        """
        Train model on historical trade outcomes.
        
        Expected columns:
        - market_data (dict)
        - smc_data (dict)
        - outcome (0=loss, 1=win)
        """
        if not SKLEARN_AVAILABLE:
            print("[ML Classifier] XGBoost not available. Cannot train.")
            return
        
        if len(historical_df) < 20:
            print("[ML Classifier] Insufficient data for training (need 20+ samples)")
            return
        
        # Extract features
        feature_list = []
        labels = []
        
        for _, row in historical_df.iterrows():
            features = self.extract_features(row['market_data'], row['smc_data'])
            feature_list.append(features)
            labels.append(row['outcome'])
        
        X = pd.concat(feature_list, ignore_index=True)
        y = np.array(labels)
        
        # Fit scaler
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Store feature importance
        self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
        
        # Save model
        self._save_model()
        
        print(f"[ML Classifier] Model trained on {len(X)} samples")
        print(f"[ML Classifier] Top features: {sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]}")
    
    def _save_model(self):
        """Save trained model to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'importance': self.feature_importance,
                'trained_at': datetime.now().isoformat()
            }, f)
        
        print(f"[ML Classifier] Model saved to {self.model_path}")

if __name__ == "__main__":
    # Test
    classifier = SetupSuccessClassifier()
    
    test_market = {
        'htf_trend': 'Bearish',
        'liquidity_event_type': 'Asian Sweep',
        'rsi_divergence': True,
        'has_large_wick': True,
        'atr_value': 5.2,
        'vwap_distance': 3.5
    }
    
    test_smc = {
        'premium_discount': {'position': 0.75, 'zone': 'Premium'},
        'order_blocks': {'bearish': [1, 2], 'bullish': []},
        'fair_value_gaps': [1, 2, 3],
        'market_structure_shift': {'type': 'Bearish MSS'}
    }
    
    prob = classifier.predict_success_probability(test_market, test_smc)
    print(f"\nTest Prediction: {prob:.1f}% success probability")
