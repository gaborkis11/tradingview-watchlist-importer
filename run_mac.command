#!/bin/bash
# Trading Pairs Fetcher - macOS launcher

echo "🚀 Trading Pairs Fetcher indítása..."
echo "=================================="
echo ""

# Átváltás a script könyvtárába
cd "$(dirname "$0")"

# Python ellenőrzése
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nincs telepítve!"
    read -p "Nyomj Enter-t a kilépéshez..."
    exit 1
fi

# Script futtatása
python3 multi_exchange_pairs.py

# Várakozás bezárás előtt
echo ""
echo "=================================="
echo "✅ Program finished!"
read -p "Press Enter to close..."
