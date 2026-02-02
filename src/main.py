import argparse
import sys
from datetime import datetime
from colorama import init, Fore, Style
import pandas as pd

# Fix import paths
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, save_snapshot, save_trade_plan
from src.risk_manager import RiskManager
from src.data_loader import fetch_data
from src.analysis_engine import XAUUSD_Analyst
from src.learning_module import SelfLearningModule
from src.email_alerts import send_trade_alert

init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(description="XAUUSD AI Analyst")
    parser.add_argument('--mode', choices=['live', 'review', 'startup'], required=True, help="Operating Mode")
    parser.add_argument('--session', choices=['LONDON', 'NEW_YORK'], help="Current Trading Session")
    
    args = parser.parse_args()
    
    if args.mode == 'startup':
        print(Fore.CYAN + "Initializing System...")
        init_db()
        print(Fore.GREEN + "System Ready.")
        
    elif args.mode == 'review':
        print(Fore.MAGENTA + "Starting Self-Learning Review...")
        learner = SelfLearningModule()
        report = learner.generate_weekly_report()
        print(report)
        
    elif args.mode == 'live':
        risk_manager = RiskManager()

        # Auto-detect session if not provided or set to AUTO
        if not args.session or args.session == 'AUTO':
            # Need a current UTC time for detection
            detected_session = risk_manager.check_session(datetime.utcnow())
            if not detected_session:
                print(Fore.YELLOW + "Market Closed (Outside London/New York hours). Analysis Skipped.")
                return
            args.session = detected_session
            print(Fore.CYAN + f"Session Auto-Detected: {args.session}")

        print(Fore.YELLOW + f"Starting Live Analysis for {args.session} Session...")
        
        # 1. Init Risk Manager & Check (Pass False for last_outcome for now, normally read from DB)
        is_safe, msg = risk_manager.can_trade()
        
        if not is_safe:
            print(Fore.RED + f"RISK STOP: {msg}")
            return

        # 2. Fetch Data
        try:
            # Using GC=F for Gold Futures as XAUUSD proxy in Yahoo Finance
            df = fetch_data(symbol="GC=F", period="5d", interval="15m")
        except Exception as e:
            print(Fore.RED + f"Data Fetch Error: {e}")
            return

        # 3. Analyze
        analyst = XAUUSD_Analyst(risk_manager)
        result = analyst.analyze_market(df)
        
        # 4. Output & Persist
        setup_data = result['data']
        setup_data['session'] = args.session
        
        if result['verdict'] == "VALID SETUP":
            print(Fore.GREEN + "\n✅ VALID SHORT SETUP DETECTED")
            print(Style.BRIGHT + str(result['plan']))
            
            # Save to DB
            snapshot_id = save_snapshot(setup_data)
            save_trade_plan(snapshot_id, result['plan'])
            print(Fore.CYAN + f"Trade Plan Saved to DB (ID: {snapshot_id})")
            
            # Send Email Alert
            send_trade_alert(result['plan'], setup_data)
            
            
        else:
            print(Fore.RED + f"\n❌ {result['verdict']}")
            print(f"Reason: {result['reason']}")
            # Optionally save failed snapshots too for learning why we didn't trade

if __name__ == "__main__":
    main()
