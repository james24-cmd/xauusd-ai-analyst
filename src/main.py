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
from src.analysis_engine import MarketAnalyst
from src.learning_module import SelfLearningModule
from src.email_alerts import send_trade_alert
from src.config_loader import load_trading_config, get_enabled_instruments

init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(description="Multi-Asset AI Trading Analyst")
    parser.add_argument('--mode', choices=['live', 'review', 'startup'], required=True, help="Operating Mode")
    parser.add_argument('--session', choices=['LONDON', 'NEW_YORK'], help="Current Trading Session")
    parser.add_argument('--symbol', help="Specific symbol to analyze (optional, e.g., 'XAU/USD')")
    
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
        # Load trading configuration
        try:
            config = load_trading_config('trading_config.json')
        except Exception as e:
            print(Fore.RED + f"Config Error: {e}")
            return
        
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

        print(Fore.YELLOW + f"Starting Multi-Asset Analysis for {args.session} Session...")
        
        # 1. Init Risk Manager & Check
        is_safe, msg = risk_manager.can_trade()
        
        if not is_safe:
            print(Fore.RED + f"RISK STOP: {msg}")
            return

        # Get instruments to analyze
        instruments = get_enabled_instruments(config)
        
        # Filter by symbol if specified
        if args.symbol:
            instruments = [i for i in instruments if i['display_name'] == args.symbol]
            if not instruments:
                print(Fore.RED + f"Symbol '{args.symbol}' not found in config")
                return
            print(Fore.CYAN + f"Analyzing single instrument: {args.symbol}")
        
        valid_setups = []
        
        # 2. Loop through each instrument
        for instrument in instruments:
            print(Fore.CYAN + f"\n{'='*50}")
            print(Fore.CYAN + f"Analyzing: {instrument['display_name']} ({instrument['asset_class'].upper()})")
            print(Fore.CYAN + f"{'='*50}")
            
            try:
                # Fetch Data
                df = fetch_data(
                    symbol=instrument['yahoo_symbol'],
                    period="5d",
                    interval="15m"
                )
            except Exception as e:
                print(Fore.RED + f"Data Fetch Error for {instrument['display_name']}: {e}")
                continue

            # 3. Analyze
            analyst = MarketAnalyst(
                risk_manager,
                instrument_name=instrument['display_name'],
                asset_class=instrument['asset_class']
            )
            result = analyst.analyze_market(df)
            
            # 4. Output & Persist
            setup_data = result.get('data', {})
            setup_data['session'] = args.session
            setup_data['instrument'] = instrument['display_name']
            
            if result['verdict'] == "VALID SETUP":
                print(Fore.GREEN + f"\n✅ VALID SHORT SETUP DETECTED: {instrument['display_name']}")
                print(Style.BRIGHT + str(result['plan']))
                
                # Save to DB
                snapshot_id = save_snapshot(setup_data)
                save_trade_plan(snapshot_id, result['plan'])
                print(Fore.CYAN + f"Trade Plan Saved to DB (ID: {snapshot_id})")
                
                # Collect for email
                valid_setups.append({
                    'instrument': instrument['display_name'],
                    'plan': result['plan'],
                    'data': setup_data
                })
            else:
                print(Fore.RED + f"\n❌ {result['verdict']}")
                print(f"Reason: {result['reason']}")
        
        # 5. Send consolidated email if any setups found
        if valid_setups:
            print(Fore.GREEN + f"\n{'='*50}")
            print(Fore.GREEN + f"📧 Sending Email Alert for {len(valid_setups)} Setup(s)")
            print(Fore.GREEN + f"{'='*50}")
            
            # For now, send individual emails (we'll create multi-asset email next)
            for setup in valid_setups:
                send_trade_alert(setup['plan'], setup['data'])
        else:
            print(Fore.YELLOW + f"\nNo valid setups found across {len(instruments)} instrument(s)")

if __name__ == "__main__":
    main()
