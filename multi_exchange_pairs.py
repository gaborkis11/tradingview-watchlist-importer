#!/usr/bin/env python3
"""
TradingView Watchlist Importer
Fetches trading pairs from Binance and Kraken exchanges
Exports TradingView-compatible watchlist files
"""

import requests
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
import re

# Pandas optional - only needed for CSV export
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("ℹ️  Pandas not installed - CSV export will not be available")
    print("   To install: pip3 install pandas\n")

class ExchangeFetcher:
    """Base class for exchange queries"""

    def __init__(self):
        self.name = ""
        self.api_url = ""

    def fetch_pairs(self, quote_assets: List[str]) -> Dict[str, Any]:
        """Abstract method for fetching pairs"""
        raise NotImplementedError

class BinanceFetcher(ExchangeFetcher):
    """Binance API fetcher"""

    def __init__(self):
        self.name = "Binance"
        self.api_url = "https://api.binance.com/api/v3/exchangeInfo"

    def fetch_pairs(self, quote_assets: List[str]) -> Dict[str, Any]:
        """Fetch Binance trading pairs"""
        try:
            print(f"🔄 Connecting to Binance API...")
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()

            results = {}
            all_pairs = []

            for asset in quote_assets:
                results[asset] = []

            for symbol in data['symbols']:
                if symbol['quoteAsset'] in quote_assets and symbol['status'] == 'TRADING':
                    quote = symbol['quoteAsset']
                    pair_info = {
                        'symbol': symbol['symbol'],
                        'baseAsset': symbol['baseAsset'],
                        'quoteAsset': quote,
                        'exchange': 'Binance'
                    }
                    results[quote].append(pair_info)
                    all_pairs.append(pair_info)

            return {
                'exchange': 'Binance',
                'results': results,
                'all_pairs': all_pairs,
                'total': len(all_pairs)
            }

        except Exception as e:
            print(f"❌ Error connecting to Binance API: {e}")
            return None

class KrakenFetcher(ExchangeFetcher):
    """Kraken API fetcher"""

    def __init__(self):
        self.name = "Kraken"
        self.api_url = "https://api.kraken.com/0/public/AssetPairs"
        # Kraken asset name conversions
        self.asset_map = {
            'USD': ['ZUSD', 'USD'],
            'USDT': ['USDT'],
            'USDC': ['USDC'],
            'EUR': ['ZEUR', 'EUR'],
            'GBP': ['ZGBP', 'GBP'],
            'JPY': ['ZJPY', 'JPY'],
            'CAD': ['ZCAD', 'CAD'],
            'AUD': ['ZAUD', 'AUD'],
            'CHF': ['CHF'],
            'DAI': ['DAI'],
            'BUSD': ['BUSD']
        }

    def fetch_pairs(self, quote_assets: List[str]) -> Dict[str, Any]:
        """Fetch Kraken trading pairs"""
        try:
            print(f"🔄 Connecting to Kraken API...")
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()

            if data['error']:
                print(f"❌ Kraken API error: {data['error']}")
                return None

            results = {}
            all_pairs = []

            for asset in quote_assets:
                results[asset] = []

            # Kraken asset names for search
            search_assets = {}
            for asset in quote_assets:
                if asset in self.asset_map:
                    search_assets[asset] = self.asset_map[asset]
                else:
                    search_assets[asset] = [asset]

            # Process pairs
            for pair_name, pair_info in data['result'].items():
                # Only spot pairs (no .d suffix for futures)
                if '.d' in pair_name:
                    continue

                # Determine quote asset
                quote_asset_kraken = pair_info.get('quote', '')
                base_asset_kraken = pair_info.get('base', '')

                # Check if this is a searched quote asset
                for original_asset, kraken_names in search_assets.items():
                    if quote_asset_kraken in kraken_names:
                        # Normalize base asset name (remove X prefix)
                        base_clean = base_asset_kraken
                        if base_clean.startswith('X') and len(base_clean) == 4:
                            base_clean = base_clean[1:]
                        elif base_clean.startswith('Z') and len(base_clean) == 4:
                            base_clean = base_clean[1:]

                        # Normalize symbol
                        altname = pair_info.get('altname', pair_name)

                        # TradingView format for Kraken
                        # wsname is usually the correct format (e.g., "BTC/USD")
                        wsname = pair_info.get('wsname', '')
                        if wsname:
                            # wsname format: "BTC/USD" -> convert to "BTCUSD"
                            tv_symbol = wsname.replace('/', '')
                        else:
                            tv_symbol = altname

                        pair_data = {
                            'symbol': tv_symbol,  # TradingView compatible
                            'baseAsset': base_clean,
                            'quoteAsset': original_asset,
                            'exchange': 'Kraken',
                            'kraken_pair': pair_name,
                            'wsname': wsname,
                            'altname': altname
                        }

                        results[original_asset].append(pair_data)
                        all_pairs.append(pair_data)
                        break

            return {
                'exchange': 'Kraken',
                'results': results,
                'all_pairs': all_pairs,
                'total': len(all_pairs)
            }

        except Exception as e:
            print(f"❌ Error connecting to Kraken API: {e}")
            return None

def get_exchange_choice() -> List[str]:
    """Exchange selection"""
    print("\n🏦 SELECT EXCHANGE:")
    print("="*50)
    print("1. 🟨 Binance")
    print("2. 🟣 Kraken")
    print("3. 🌐 Both")
    print("="*50)

    while True:
        choice = input("\nSelect (1-3): ").strip()
        if choice == '1':
            return ['binance']
        elif choice == '2':
            return ['kraken']
        elif choice == '3':
            return ['binance', 'kraken']
        else:
            print("❌ Invalid choice!")

def get_asset_choice() -> List[str]:
    """Quote asset selection"""
    print("\n🪙 SELECT TRADING PAIRS:")
    print("="*50)
    print("1. 💵 USD pairs")
    print("2. 💰 USDT pairs")
    print("3. 🪙 USDC pairs")
    print("4. 📊 USD + USDT + USDC")
    print("5. 💶 EUR pairs")
    print("6. 🌍 All major stablecoins/fiat (USD, USDT, USDC, EUR, GBP)")
    print("7. ✏️  Custom selection")
    print("="*50)

    while True:
        choice = input("\nSelect (1-7): ").strip()
        if choice == '1':
            return ['USD']
        elif choice == '2':
            return ['USDT']
        elif choice == '3':
            return ['USDC']
        elif choice == '4':
            return ['USD', 'USDT', 'USDC']
        elif choice == '5':
            return ['EUR']
        elif choice == '6':
            return ['USD', 'USDT', 'USDC', 'EUR', 'GBP']
        elif choice == '7':
            custom = input("Enter comma-separated (e.g., USDT,EUR,DAI): ").strip().upper()
            assets = [a.strip() for a in custom.split(',') if a.strip()]
            if assets:
                return assets
            else:
                print("❌ Please enter at least one asset!")
        else:
            print("❌ Invalid choice!")

def display_results(all_results: List[Dict[str, Any]], quote_assets: List[str]):
    """Display results"""

    print("\n" + "="*70)
    print("📊 TRADING PAIRS SUMMARY")
    print(f"⏰ Query time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 Selected asset(s): {', '.join(quote_assets)}")
    print("="*70)

    # Statistics by exchange
    grand_total = 0
    for result in all_results:
        if result:
            print(f"\n🏦 {result['exchange']}:")
            print("-" * 40)

            for asset in quote_assets:
                count = len(result['results'].get(asset, []))
                if count > 0:
                    print(f"   {asset}: {count} pairs")

            print(f"   📊 Total: {result['total']} pairs")
            grand_total += result['total']

    if len(all_results) > 1:
        print(f"\n🌐 GRAND TOTAL: {grand_total} pairs")

    # Display options
    print("\n" + "="*70)
    print("DISPLAY OPTIONS:")
    print("1. Detailed list by exchange")
    print("2. Comparison table")
    print("3. Find common pairs")
    print("4. Skip")

    display_choice = input("\nSelect (1-4): ").strip()

    if display_choice == '1':
        # Detailed list
        for result in all_results:
            if result:
                print(f"\n{'='*70}")
                print(f"🏦 {result['exchange']} PAIRS")
                print('='*70)

                for asset in quote_assets:
                    pairs = result['results'].get(asset, [])
                    if pairs:
                        print(f"\n📋 {asset} pairs ({len(pairs)} items):")
                        print("-" * 50)

                        # Sort and display
                        sorted_pairs = sorted(pairs, key=lambda x: x['symbol'])
                        columns = 4
                        symbols = [p['symbol'] for p in sorted_pairs]

                        for i in range(0, len(symbols), columns):
                            row = symbols[i:i+columns]
                            print("  ".join(f"{s:15}" for s in row))

    elif display_choice == '2':
        # Comparison table
        if len(all_results) > 1:
            print(f"\n{'='*70}")
            print("📊 COMPARISON TABLE")
            print('='*70)

            # Collect all base assets
            all_bases = set()
            for result in all_results:
                if result:
                    for pair in result['all_pairs']:
                        all_bases.add(pair['baseAsset'])

            # Sort alphabetically
            sorted_bases = sorted(all_bases)

            # Table header
            header = f"{'Base Asset':12}"
            for result in all_results:
                if result:
                    header += f" | {result['exchange']:10}"
            print(header)
            print("-" * len(header))

            # Rows
            for base in sorted_bases[:20]:  # First 20 base assets
                row = f"{base:12}"
                for result in all_results:
                    if result:
                        # Count pairs
                        count = 0
                        for pair in result['all_pairs']:
                            if pair['baseAsset'] == base:
                                count += 1

                        if count > 0:
                            row += f" | {'✓ ' + str(count):10}"
                        else:
                            row += f" | {'':10}"
                print(row)

            if len(sorted_bases) > 20:
                print(f"\n... and {len(sorted_bases) - 20} more base assets")

    elif display_choice == '3':
        # Common pairs
        if len(all_results) > 1:
            print(f"\n{'='*70}")
            print("🔄 COMMON PAIRS")
            print('='*70)

            # Create sets
            exchanges_pairs = {}
            for result in all_results:
                if result:
                    exchange = result['exchange']
                    pairs_set = set()
                    for pair in result['all_pairs']:
                        # Normalized format: BASE/QUOTE
                        normalized = f"{pair['baseAsset']}/{pair['quoteAsset']}"
                        pairs_set.add(normalized)
                    exchanges_pairs[exchange] = pairs_set

            # Find common pairs
            if len(exchanges_pairs) == 2:
                exchanges = list(exchanges_pairs.keys())
                common = exchanges_pairs[exchanges[0]] & exchanges_pairs[exchanges[1]]
                only_first = exchanges_pairs[exchanges[0]] - exchanges_pairs[exchanges[1]]
                only_second = exchanges_pairs[exchanges[1]] - exchanges_pairs[exchanges[0]]

                print(f"\n✅ Available on both exchanges: {len(common)} pairs")
                if len(common) > 0:
                    print("Examples:", ", ".join(sorted(common)[:10]))

                print(f"\n🟨 Only on {exchanges[0]}: {len(only_first)} pairs")
                if len(only_first) > 0:
                    print("Examples:", ", ".join(sorted(only_first)[:10]))

                print(f"\n🟣 Only on {exchanges[1]}: {len(only_second)} pairs")
                if len(only_second) > 0:
                    print("Examples:", ", ".join(sorted(only_second)[:10]))

def save_results(all_results: List[Dict[str, Any]], quote_assets: List[str]):
    """Save results to files"""
    import os

    # Create export directory if it doesn't exist
    export_dir = "export"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        print(f"📁 Created export directory: {export_dir}/")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exchanges = "_".join([r['exchange'] for r in all_results if r])
    assets = "_".join(quote_assets)

    # JSON save
    json_filename = os.path.join(export_dir, f"{exchanges}_{assets}_pairs_{timestamp}.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'quote_assets': quote_assets,
            'exchanges': all_results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON saved: {json_filename}")

    # CSV save if pandas available
    if PANDAS_AVAILABLE:
        all_pairs = []
        for result in all_results:
            if result:
                all_pairs.extend(result['all_pairs'])

        if all_pairs:
            df = pd.DataFrame(all_pairs)
            csv_filename = os.path.join(export_dir, f"{exchanges}_{assets}_pairs_{timestamp}.csv")
            df.to_csv(csv_filename, index=False)
            print(f"✅ CSV saved: {csv_filename}")

    # TXT list - BASIC
    txt_filename = os.path.join(export_dir, f"{exchanges}_{assets}_list_{timestamp}.txt")
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Trading Pairs List\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Quote Asset(s): {', '.join(quote_assets)}\n")
        f.write("="*50 + "\n")

        for result in all_results:
            if result:
                f.write(f"\n{result['exchange']} ({result['total']} pairs)\n")
                f.write("-"*30 + "\n")

                for asset in quote_assets:
                    pairs = result['results'].get(asset, [])
                    if pairs:
                        f.write(f"\n{asset} pairs:\n")
                        for pair in sorted(pairs, key=lambda x: x['symbol']):
                            f.write(f"  {pair['symbol']}\n")

    print(f"✅ TXT list saved: {txt_filename}")

    # TradingView export question
    tv_choice = input("\n📈 Generate TradingView watchlist files? (y/n): ").lower()
    if tv_choice == 'y':
        print("\n📊 Generating TradingView watchlist files...")
        print("   (These include exchange prefix: KRAKEN:BTCUSD)")

        for result in all_results:
            if result:
                exchange_name = result['exchange'].upper()
                tv_filename = os.path.join(export_dir, f"TradingView_{exchange_name}_{assets}_{timestamp}.txt")

                with open(tv_filename, 'w', encoding='utf-8') as f:
                    # TradingView import needs simple list, one symbol per line
                    # Add exchange prefix
                    for asset in quote_assets:
                        pairs = result['results'].get(asset, [])
                        for pair in sorted(pairs, key=lambda x: x['symbol']):
                            # TradingView format: EXCHANGE:SYMBOL
                            f.write(f"{exchange_name}:{pair['symbol']}\n")

                print(f"   ✅ TradingView list ({exchange_name}): {tv_filename}")

        # COMBINED TradingView list (if multiple exchanges)
        if len(all_results) > 1:
            tv_combined = os.path.join(export_dir, f"TradingView_ALL_{assets}_{timestamp}.txt")
            with open(tv_combined, 'w', encoding='utf-8') as f:
                for result in all_results:
                    if result:
                        exchange_name = result['exchange'].upper()
                        for asset in quote_assets:
                            pairs = result['results'].get(asset, [])
                            for pair in sorted(pairs, key=lambda x: x['symbol']):
                                f.write(f"{exchange_name}:{pair['symbol']}\n")
            print(f"   ✅ TradingView combined list: {tv_combined}")

        print("\n💡 TIP: Import the TradingView_[EXCHANGE]_*.txt file into TradingView!")
        print("   This ensures you'll see charts from the correct exchange!")
        print(f"\n📂 All files saved in: {os.path.abspath(export_dir)}/")

def main():
    """Main program"""
    print("🚀 TradingView Watchlist Importer")
    print("    Supported exchanges: Binance, Kraken")
    print("="*70)

    # User selections
    exchanges = get_exchange_choice()
    quote_assets = get_asset_choice()

    # Fetch data
    all_results = []

    if 'binance' in exchanges:
        binance = BinanceFetcher()
        result = binance.fetch_pairs(quote_assets)
        all_results.append(result)

    if 'kraken' in exchanges:
        kraken = KrakenFetcher()
        result = kraken.fetch_pairs(quote_assets)
        all_results.append(result)

    # Display results
    if any(all_results):
        display_results(all_results, quote_assets)

        # Save
        save_choice = input("\n💾 Save results to files? (y/n): ").lower()
        if save_choice == 'y':
            save_results(all_results, quote_assets)

        print("\n✨ Done!")
    else:
        print("❌ Failed to fetch data.")

if __name__ == "__main__":
    main()
