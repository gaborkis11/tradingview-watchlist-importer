#!/usr/bin/env python3
"""
Multi-Exchange Trading Pairs Fetcher
Támogatott tőzsdék: Binance, Kraken
Lekérdezi a választott stablecoin/fiat kereskedési párokat
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
import re

# Pandas opcionális - csak CSV exporthoz kell
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("ℹ️  Pandas nincs telepítve - CSV export nem lesz elérhető")
    print("   Telepítéshez: pip3 install pandas\n")

class ExchangeFetcher:
    """Alap osztály a tőzsde lekérdezésekhez"""

    def __init__(self):
        self.name = ""
        self.api_url = ""

    def fetch_pairs(self, quote_assets: List[str]) -> Dict[str, Any]:
        """Absztrakt metódus a párok lekérdezéséhez"""
        raise NotImplementedError

class BinanceFetcher(ExchangeFetcher):
    """Binance API lekérdező"""

    def __init__(self):
        self.name = "Binance"
        self.api_url = "https://api.binance.com/api/v3/exchangeInfo"

    def fetch_pairs(self, quote_assets: List[str]) -> Dict[str, Any]:
        """Binance párok lekérdezése"""
        try:
            print(f"🔄 Kapcsolódás a Binance API-hoz...")
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
            print(f"❌ Hiba a Binance API hívásnál: {e}")
            return None

class KrakenFetcher(ExchangeFetcher):
    """Kraken API lekérdező"""

    def __init__(self):
        self.name = "Kraken"
        self.api_url = "https://api.kraken.com/0/public/AssetPairs"
        # Kraken asset név konverziók
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
        """Kraken párok lekérdezése"""
        try:
            print(f"🔄 Kapcsolódás a Kraken API-hoz...")
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()

            if data['error']:
                print(f"❌ Kraken API hiba: {data['error']}")
                return None

            results = {}
            all_pairs = []

            for asset in quote_assets:
                results[asset] = []

            # Kraken asset nevek a kereséshez
            search_assets = {}
            for asset in quote_assets:
                if asset in self.asset_map:
                    search_assets[asset] = self.asset_map[asset]
                else:
                    search_assets[asset] = [asset]

            # Párok feldolgozása
            for pair_name, pair_info in data['result'].items():
                # Csak spot párok (nincs .d suffix a futures-höz)
                if '.d' in pair_name:
                    continue

                # Quote asset meghatározása
                quote_asset_kraken = pair_info.get('quote', '')
                base_asset_kraken = pair_info.get('base', '')

                # Ellenőrizzük hogy ez egy keresett quote asset-e
                for original_asset, kraken_names in search_assets.items():
                    if quote_asset_kraken in kraken_names:
                        # Normalizáljuk a base asset nevét (X prefix eltávolítása)
                        base_clean = base_asset_kraken
                        if base_clean.startswith('X') and len(base_clean) == 4:
                            base_clean = base_clean[1:]
                        elif base_clean.startswith('Z') and len(base_clean) == 4:
                            base_clean = base_clean[1:]

                        # Normalizáljuk a szimbólumot
                        altname = pair_info.get('altname', pair_name)

                        # TradingView formátum a Kraken-hez
                        # A wsname általában a helyes formátum (pl: "BTC/USD")
                        wsname = pair_info.get('wsname', '')
                        if wsname:
                            # wsname formátum: "BTC/USD" -> átalakítás "BTCUSD"-re
                            tv_symbol = wsname.replace('/', '')
                        else:
                            tv_symbol = altname

                        pair_data = {
                            'symbol': tv_symbol,  # TradingView kompatibilis
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
            print(f"❌ Hiba a Kraken API hívásnál: {e}")
            return None

def get_exchange_choice() -> List[str]:
    """Tőzsde választás"""
    print("\n🏦 VÁLASSZ TŐZSDÉT:")
    print("="*50)
    print("1. 🟨 Binance")
    print("2. 🟣 Kraken")
    print("3. 🌐 Mindkettő")
    print("="*50)

    while True:
        choice = input("\nVálassz (1-3): ").strip()
        if choice == '1':
            return ['binance']
        elif choice == '2':
            return ['kraken']
        elif choice == '3':
            return ['binance', 'kraken']
        else:
            print("❌ Érvénytelen választás!")

def get_asset_choice() -> List[str]:
    """Quote asset választás"""
    print("\n🪙 VÁLASZD KI A KERESKEDÉSI PÁROKAT:")
    print("="*50)
    print("1. 💵 USD párok")
    print("2. 💰 USDT párok")
    print("3. 🪙 USDC párok")
    print("4. 📊 USD + USDT + USDC")
    print("5. 💶 EUR párok")
    print("6. 🌍 Minden főbb stablecoin/fiat (USD, USDT, USDC, EUR, GBP)")
    print("7. ✏️  Egyéni választás")
    print("="*50)

    while True:
        choice = input("\nVálassz (1-7): ").strip()
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
            custom = input("Add meg vesszővel elválasztva (pl: USDT,EUR,DAI): ").strip().upper()
            assets = [a.strip() for a in custom.split(',') if a.strip()]
            if assets:
                return assets
            else:
                print("❌ Legalább egy asset-et adj meg!")
        else:
            print("❌ Érvénytelen választás!")

def display_results(all_results: List[Dict[str, Any]], quote_assets: List[str]):
    """Eredmények megjelenítése"""

    print("\n" + "="*70)
    print("📊 KERESKEDÉSI PÁROK ÖSSZESÍTÉSE")
    print(f"⏰ Lekérdezés: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 Keresett asset(ek): {', '.join(quote_assets)}")
    print("="*70)

    # Tőzsdénkénti statisztika
    grand_total = 0
    for result in all_results:
        if result:
            print(f"\n🏦 {result['exchange']}:")
            print("-" * 40)

            for asset in quote_assets:
                count = len(result['results'].get(asset, []))
                if count > 0:
                    print(f"   {asset}: {count} pár")

            print(f"   📊 Összesen: {result['total']} pár")
            grand_total += result['total']

    if len(all_results) > 1:
        print(f"\n🌐 MINDÖSSZESEN: {grand_total} pár")

    # Részletes lista opció
    print("\n" + "="*70)
    print("MEGJELENÍTÉSI OPCIÓK:")
    print("1. Részletes lista tőzsdénként")
    print("2. Összehasonlító táblázat")
    print("3. Közös párok keresése")
    print("4. Kihagyás")

    display_choice = input("\nVálassz (1-4): ").strip()

    if display_choice == '1':
        # Részletes lista
        for result in all_results:
            if result:
                print(f"\n{'='*70}")
                print(f"🏦 {result['exchange']} PÁROK")
                print('='*70)

                for asset in quote_assets:
                    pairs = result['results'].get(asset, [])
                    if pairs:
                        print(f"\n📋 {asset} párok ({len(pairs)} db):")
                        print("-" * 50)

                        # Rendezés és megjelenítés
                        sorted_pairs = sorted(pairs, key=lambda x: x['symbol'])
                        columns = 4
                        symbols = [p['symbol'] for p in sorted_pairs]

                        for i in range(0, len(symbols), columns):
                            row = symbols[i:i+columns]
                            print("  ".join(f"{s:15}" for s in row))

    elif display_choice == '2':
        # Összehasonlító táblázat
        if len(all_results) > 1:
            print(f"\n{'='*70}")
            print("📊 ÖSSZEHASONLÍTÓ TÁBLÁZAT")
            print('='*70)

            # Gyűjtsük össze az összes base asset-et
            all_bases = set()
            for result in all_results:
                if result:
                    for pair in result['all_pairs']:
                        all_bases.add(pair['baseAsset'])

            # Rendezzük ABC sorrendbe
            sorted_bases = sorted(all_bases)

            # Táblázat fejléc
            header = f"{'Base Asset':12}"
            for result in all_results:
                if result:
                    header += f" | {result['exchange']:10}"
            print(header)
            print("-" * len(header))

            # Sorok
            for base in sorted_bases[:20]:  # Első 20 base asset
                row = f"{base:12}"
                for result in all_results:
                    if result:
                        # Megszámoljuk hány párja van
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
                print(f"\n... és még {len(sorted_bases) - 20} base asset")

    elif display_choice == '3':
        # Közös párok
        if len(all_results) > 1:
            print(f"\n{'='*70}")
            print("🔄 KÖZÖS PÁROK")
            print('='*70)

            # Készítsünk halmazokat
            exchanges_pairs = {}
            for result in all_results:
                if result:
                    exchange = result['exchange']
                    pairs_set = set()
                    for pair in result['all_pairs']:
                        # Normalizált formátum: BASE/QUOTE
                        normalized = f"{pair['baseAsset']}/{pair['quoteAsset']}"
                        pairs_set.add(normalized)
                    exchanges_pairs[exchange] = pairs_set

            # Közös párok keresése
            if len(exchanges_pairs) == 2:
                exchanges = list(exchanges_pairs.keys())
                common = exchanges_pairs[exchanges[0]] & exchanges_pairs[exchanges[1]]
                only_first = exchanges_pairs[exchanges[0]] - exchanges_pairs[exchanges[1]]
                only_second = exchanges_pairs[exchanges[1]] - exchanges_pairs[exchanges[0]]

                print(f"\n✅ Mindkét tőzsdén elérhető: {len(common)} pár")
                if len(common) > 0:
                    print("Példák:", ", ".join(sorted(common)[:10]))

                print(f"\n🟨 Csak {exchanges[0]}: {len(only_first)} pár")
                if len(only_first) > 0:
                    print("Példák:", ", ".join(sorted(only_first)[:10]))

                print(f"\n🟣 Csak {exchanges[1]}: {len(only_second)} pár")
                if len(only_second) > 0:
                    print("Példák:", ", ".join(sorted(only_second)[:10]))

def save_results(all_results: List[Dict[str, Any]], quote_assets: List[str]):
    """Eredmények mentése"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exchanges = "_".join([r['exchange'] for r in all_results if r])
    assets = "_".join(quote_assets)

    # JSON mentés
    json_filename = f"{exchanges}_{assets}_pairs_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'quote_assets': quote_assets,
            'exchanges': all_results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON mentve: {json_filename}")

    # CSV mentés ha van pandas
    if PANDAS_AVAILABLE:
        all_pairs = []
        for result in all_results:
            if result:
                all_pairs.extend(result['all_pairs'])

        if all_pairs:
            df = pd.DataFrame(all_pairs)
            csv_filename = f"{exchanges}_{assets}_pairs_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"✅ CSV mentve: {csv_filename}")

    # TXT lista - ALAPVETŐ
    txt_filename = f"{exchanges}_{assets}_list_{timestamp}.txt"
    with open(txt_filename, 'w', encoding='utf-8') as f:
        f.write(f"Kereskedési Párok Lista\n")
        f.write(f"Időpont: {timestamp}\n")
        f.write(f"Quote Asset(ek): {', '.join(quote_assets)}\n")
        f.write("="*50 + "\n")

        for result in all_results:
            if result:
                f.write(f"\n{result['exchange']} ({result['total']} pár)\n")
                f.write("-"*30 + "\n")

                for asset in quote_assets:
                    pairs = result['results'].get(asset, [])
                    if pairs:
                        f.write(f"\n{asset} párok:\n")
                        for pair in sorted(pairs, key=lambda x: x['symbol']):
                            f.write(f"  {pair['symbol']}\n")

    print(f"✅ TXT lista mentve: {txt_filename}")

    # TradingView export kérdése
    tv_choice = input("\n📈 Szeretnél TradingView formátumú listát is? (i/n): ").lower()
    if tv_choice == 'i':
        print("\n📊 TradingView formátumú listák generálása...")
        print("   (Ezek tartalmazzák a tőzsde prefixet: KRAKEN:BTCUSD)")

        for result in all_results:
            if result:
                exchange_name = result['exchange'].upper()
                tv_filename = f"TradingView_{exchange_name}_{assets}_{timestamp}.txt"

                with open(tv_filename, 'w', encoding='utf-8') as f:
                    # TradingView importhoz egyszerű lista kell, soronként egy szimbólum
                    # Tőzsde prefix hozzáadása
                    for asset in quote_assets:
                        pairs = result['results'].get(asset, [])
                        for pair in sorted(pairs, key=lambda x: x['symbol']):
                            # TradingView formátum: EXCHANGE:SYMBOL
                            f.write(f"{exchange_name}:{pair['symbol']}\n")

                print(f"   ✅ TradingView lista ({exchange_name}): {tv_filename}")

        # KOMBINÁLT TradingView lista (ha több tőzsde van)
        if len(all_results) > 1:
            tv_combined = f"TradingView_ALL_{assets}_{timestamp}.txt"
            with open(tv_combined, 'w', encoding='utf-8') as f:
                for result in all_results:
                    if result:
                        exchange_name = result['exchange'].upper()
                        for asset in quote_assets:
                            pairs = result['results'].get(asset, [])
                            for pair in sorted(pairs, key=lambda x: x['symbol']):
                                f.write(f"{exchange_name}:{pair['symbol']}\n")
            print(f"   ✅ TradingView kombinált lista: {tv_combined}")

        print("\n💡 TIP: Importáld a TradingView_[EXCHANGE]_*.txt fájlt a TradingView-ba!")
        print("   Így garantáltan a megfelelő tőzsde chart-jait fogod látni!")

def main():
    """Fő program"""
    print("🚀 Multi-Exchange Trading Pairs Fetcher")
    print("    Támogatott tőzsdék: Binance, Kraken")
    print("="*70)

    # Választások
    exchanges = get_exchange_choice()
    quote_assets = get_asset_choice()

    # Lekérdezések
    all_results = []

    if 'binance' in exchanges:
        binance = BinanceFetcher()
        result = binance.fetch_pairs(quote_assets)
        all_results.append(result)

    if 'kraken' in exchanges:
        kraken = KrakenFetcher()
        result = kraken.fetch_pairs(quote_assets)
        all_results.append(result)

    # Eredmények megjelenítése
    if any(all_results):
        display_results(all_results, quote_assets)

        # Mentés
        save_choice = input("\n💾 Szeretnéd menteni az eredményeket? (i/n): ").lower()
        if save_choice == 'i':
            save_results(all_results, quote_assets)

        print("\n✨ Kész!")
    else:
        print("❌ Nem sikerült adatokat lekérdezni.")

if __name__ == "__main__":
    main()
