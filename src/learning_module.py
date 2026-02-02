from .database import get_recent_outcomes
import pandas as pd
from tabulate import tabulate

class SelfLearningModule:
    def __init__(self):
        pass

    def generate_weekly_report(self):
        outcomes = get_recent_outcomes(limit=200)
        
        if not outcomes:
            return "NO STRUCTURAL CONCLUSIONS – SAMPLE TOO SMALL"
            
        df = pd.DataFrame(outcomes)
        
        # Calculate Win Rate by Session
        session_stats = df.groupby('session')['outcome'].value_counts(normalize=True).unstack().fillna(0)
        
        # Calculate Expectancy by Liquidity Type
        liquidity_stats = df.groupby('liquidity_event_type')['realized_r_multiple'].mean()
        
        report = f"""
        📊 SELF-LEARNING REVIEW – XAUUSD
        ================================
        Sample Size: {len(df)} trades
        
        REGIME ANALYSIS
        ---------------
        {tabulate(session_stats, headers='keys', tablefmt='grid')}
        
        FILTER STRENGTH (Avg R:R Outcome)
        ---------------------------------
        {tabulate(liquidity_stats.to_frame(), headers=['Avg R Multiple'], tablefmt='grid')}
        
        RECOMMENDATIONS
        ---------------
        [Based on the stats above, avoid conditions with < 0 expectancy]
        """
        
        return report
