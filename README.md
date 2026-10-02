# Dynamic Stock Performance Analyzer

An interactive Streamlit dashboard for exploring stock prices, company fundamentals, and technical indicators. Search for a company by name, choose a matching ticker, and view its price chart and history alongside a small market watchlist.

**Live app:** [Dynamic Stock Performance Analyzer](https://dynamicstockanalyzerapp-a5xybqbmegubcpd3jmsyj8.streamlit.app/)

**Source:** [GitHub repository](https://github.com/meenakshi-sethi/dynamic_stock_analyzer_streamlit)

## Features

- Search Yahoo Finance by company name or ticker and select from matching equities.
- View candlestick or line charts for supported periods, with optional 20-period SMA and EMA overlays.
- Review price, period high and low, volume, revenue, market capitalization, and P/E ratio.
- Browse price history and technical indicators in separate tables.
- Refresh the selected stock and market watchlist automatically every five minutes, or use **Refresh data now**.
- Track AAPL, GOOGL, AMZN, and MSFT in the market watchlist.

## Run Locally

Requirements: Python 3.10 or newer.

```bash
git clone https://github.com/meenakshi-sethi/dynamic_stock_analyzer_streamlit.git
cd dynamic_stock_analyzer_streamlit
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run dynamic_stock_analyzer_with_streamlit.py
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

## Use the Dashboard

1. Enter a company name, such as `Apple`, or a ticker, such as `AAPL`.
2. Select **Find ticker** and choose the intended company when searching by name.
3. Choose a time period, chart type, and optional technical indicators in the sidebar.
4. View the chart and tables on the main page. Data refreshes every five minutes; **Refresh data now** forces a new fetch.

## Data Notes

Prices and company information come from Yahoo Finance through `yfinance`. This is periodic polling, not a streaming feed. Availability, freshness, and intraday intervals depend on Yahoo Finance; quotes may be delayed or unavailable. This dashboard is for informational and educational use, not investment advice.

## Technology

Python, Streamlit, pandas, yfinance, Plotly, `ta`, and `tzdata`.

## License

MIT. See [LICENSE](LICENSE).
