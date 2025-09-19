# 📈 TradingView Watchlist Importer

Fetch **real-time SPOT trading pairs** from Binance and Kraken exchanges via API and generate TradingView-compatible watchlist files.

## 🎯 Core Functionality

This tool:
- Fetches **SPOT market** trading pairs from **Binance** and **Kraken**
- Uses official public APIs (no authentication required)
- Generates TradingView watchlist files with correct exchange prefixes
- Updates in real-time - always get the current tradeable pairs

**Currently supported:** Binance Spot, Kraken Spot
**Future updates:** More exchanges can be added based on demand

## ✨ Key Features

- 📊 **SPOT pairs only** - No futures or derivatives
- 🔄 **Real-time data** - Always current trading pairs
- 🎯 **Filter by quote asset** - USD, USDT, USDC, EUR, etc.
- 📁 **TradingView ready** - Import with correct exchange charts (BINANCE:BTCUSDT, KRAKEN:BTCUSD)
- 💾 **Multiple formats** - JSON, CSV, TXT exports

## 🚀 Quick Start

### Installation
```bash
