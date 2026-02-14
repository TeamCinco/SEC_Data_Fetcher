# 📊 SEC Filing Downloader & Financial Parser

A real-time tool to download SEC filings (10-K/10-Q) and instantly convert them into structured Excel files—even when the official SEC Excel version isn't available yet.

## 🚀 Purpose

When a company files a report, the SEC takes time to generate an "Interactive Data" Excel file. This project skips the wait by parsing the **Inline XBRL (iXBRL)** directly from the HTML filing to create a clean, multi-sheet Excel workbook for immediate analysis.

## ✨ Key Features

* **Direct Downloads**: Fetches 10-K and 10-Q filings directly from the SEC EDGAR API.
* **Smart Parsing**: Dynamically extracts financial statements (Balance Sheet, Income, Cash Flow) without needing hardcoded labels.
* **Stock Insights**: Displays real-time market data, valuation ratios (P/E, P/S), and profitability metrics for the searched ticker.
* **User-Friendly Dashboard**: Built with Streamlit for a clean, searchable interface.

## 📂 Project Structure

* `streamlit_app.py`: The main entry point and web dashboard.
* `xbrl_parser.py`: The engine that turns raw HTML/XBRL into Excel.
* `data_loader.py`: Handles all API calls to the SEC.
* `stock_data.py`: Fetches real-time market metrics from Yahoo Finance.
* `ui_components.py`: Houses the visual elements for the dashboard.

## 🛠️ Quick Start

1. **Install dependencies**:
```bash
pip install streamlit pandas openpyxl beautifulsoup4 requests yfinance

```


2. **Run the app**:
```bash
streamlit run streamlit_app.py

```


3. **Search for a ticker**: Enter symbols like `AAPL`, `PYPL`, or `TSLA` to find and download their latest filings.
