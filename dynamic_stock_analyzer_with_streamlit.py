# Importing necessary libraries
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import ta  # For technical indicators

## PART 1: Functions for Fetching, Processing, and Enhancing Stock Data ##

# Function to fetch stock data
@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker, period, interval):
    end_date = datetime.now()
    if period == '1wk':  # Adjusting start date for weekly data
        start_date = end_date - timedelta(days=7)
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        data = yf.download(ticker, period=period, interval=interval)
    # Flatten MultiIndex if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    return data

# Search Yahoo Finance for matching company equities.
@st.cache_data(ttl=3600, show_spinner=False)
def search_tickers(query):
    quotes = yf.Search(query, max_results=10).quotes
    return [
        {
            'symbol': quote['symbol'],
            'name': quote.get('shortname') or quote['symbol'],
        }
        for quote in quotes
        if quote.get('quoteType') == 'EQUITY' and quote.get('symbol')
    ]

# Function to fetch financial metrics
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_financial_metrics(ticker):
    # Using Yahoo Finance for real-time financial data
    ticker_data = yf.Ticker(ticker)
    info = ticker_data.info
    revenue = info.get('totalRevenue', 'N/A')
    market_cap = info.get('marketCap', 'N/A')
    pe_ratio = info.get('trailingPE', 'N/A')
    if revenue != 'N/A':
        revenue = f"${revenue / 1e9:.2f}B"
    if market_cap != 'N/A':
        market_cap = f"${market_cap / 1e9:.2f}B"
    return revenue, market_cap, pe_ratio

# Processing data for timezone and format compatibility
def process_data(data):
    if data.index.tz is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('America/New_York')
    data.reset_index(inplace=True)
    data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

# Function to calculate key metrics from stock data
def calculate_metrics(data):
    last_close = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[0]
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = data['High'].max()
    low = data['Low'].min()
    volume = data['Volume'].sum()
    return last_close, change, pct_change, high, low, volume

# Adding SMA and EMA technical indicators
def add_technical_indicators(data):
    # Adding SMA and EMA as basic examples
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['EMA_20'] = ta.trend.ema_indicator(data['Close'], window=20)
    return data

# PART 2: Building the Custom Dashboard UI ##

# Setting up the dashboard layout
st.set_page_config(layout="wide")
st.title('Dynamic Stock Performance Analyzer')  

# Sidebar for user inputs
st.sidebar.header('Customize Your View')
company_query = st.sidebar.text_input('Company name or ticker', 'ADBE', key='company_query')
if st.sidebar.button('Find ticker', key='find_ticker'):
    query = company_query.strip()
    st.session_state['ticker_search_query'] = query
    st.session_state['ticker_search_error'] = None
    st.session_state['ticker_search_results'] = []
    if query:
        try:
            st.session_state['ticker_search_results'] = search_tickers(query)
        except Exception as error:
            st.session_state['ticker_search_error'] = str(error)

query = company_query.strip()
if st.session_state.get('ticker_search_query') == query:
    ticker_matches = st.session_state.get('ticker_search_results', [])
    search_error = st.session_state.get('ticker_search_error')
else:
    ticker_matches = []
    search_error = None

if ticker_matches:
    ticker_options = {
        f"{match['name']} ({match['symbol']})": match['symbol']
        for match in ticker_matches
    }
    selected_company = st.sidebar.selectbox('Matching companies', list(ticker_options))
    ticker = ticker_options[selected_company]
elif st.session_state.get('ticker_search_query') == query:
    ticker = ''
    if search_error:
        st.sidebar.error(f'Ticker search failed: {search_error}')
    elif query:
        st.sidebar.warning('No matching companies found. Enter a ticker or try another name.')
else:
    ticker = query.upper()

time_period = st.sidebar.selectbox('Select Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
chart_type = st.sidebar.selectbox('Select Chart Type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect('Select Technical Indicators', ['SMA 20', 'EMA 20'])

# Mapping time periods to intervals
interval_mapping = {
    '1d': '1m',
    '1wk': '30m',
    '1mo': '1d',
    '1y': '1wk',
    'max': '1wk'
}

st.sidebar.caption('Yahoo Finance data refreshes every 5 minutes and may be delayed.')
if st.sidebar.button('Refresh data now'):
    st.cache_data.clear()

st.header('Key Financial Metrics')
if ticker:
    try:
        revenue, market_cap, pe_ratio = fetch_financial_metrics(ticker)
        metric_columns = st.columns(3)
        metric_columns[0].metric('Revenue', revenue)
        metric_columns[1].metric('Market capitalization', market_cap)
        metric_columns[2].metric('P/E ratio', pe_ratio)
    except Exception as error:
        st.warning(f'Financial metrics are unavailable for {ticker}: {error}')


@st.fragment(run_every='5m')
def render_stock_dashboard(selected_ticker, period, interval, selected_chart_type, selected_indicators):
    st.caption(f"Prices refresh every 5 minutes · Last updated {datetime.now().astimezone().strftime('%H:%M:%S %Z')}")
    if not selected_ticker:
        st.info('Search for a company or enter a ticker to view its stock chart.')
        return

    try:
        data = fetch_stock_data(selected_ticker, period, interval)
        if data.empty:
            st.warning(f'No price history was returned for {selected_ticker}. Check the ticker or try another time period.')
            return
        data = process_data(data)
        data = add_technical_indicators(data)
        last_close, change, pct_change, high, low, volume = calculate_metrics(data)
    except Exception as error:
        st.error(f'Could not load price history for {selected_ticker}: {error}')
        return

    metric_columns = st.columns(4)
    metric_columns[0].metric(
        f'{selected_ticker} last price', f'{last_close:.2f} USD',
        f'{change:.2f} ({pct_change:.2f}%)',
    )
    metric_columns[1].metric('Period high', f'{high:.2f} USD')
    metric_columns[2].metric('Period low', f'{low:.2f} USD')
    metric_columns[3].metric('Period volume', f'{volume:,.0f}')

    fig = go.Figure()
    if selected_chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(
            x=data['Datetime'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=selected_ticker,
        ))
    else:
        fig.add_trace(go.Scatter(
            x=data['Datetime'], y=data['Close'], name=selected_ticker,
            mode='lines',
        ))

    indicator_columns = {'SMA 20': 'SMA_20', 'EMA 20': 'EMA_20'}
    for indicator in selected_indicators:
        column = indicator_columns[indicator]
        fig.add_trace(go.Scatter(
            x=data['Datetime'], y=data[column], name=indicator, mode='lines',
        ))

    fig.update_layout(
        title=f'{selected_ticker} · {period} price history',
        xaxis_title='Time (US Eastern)',
        yaxis_title='Price (USD)',
        height=520,
        template='plotly_white',
        margin=dict(l=16, r=16, t=56, b=16),
        xaxis_rangeslider_visible=False,
    )
    st.plotly_chart(fig, width='stretch')

    history_tab, indicators_tab = st.tabs(['Price history', 'Technical indicators'])
    with history_tab:
        st.dataframe(
            data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']],
            width='stretch',
        )
    with indicators_tab:
        st.dataframe(data[['Datetime', 'SMA_20', 'EMA_20']], width='stretch')


render_stock_dashboard(
    ticker, time_period, interval_mapping[time_period], chart_type, indicators,
)


@st.fragment(run_every='5m')
def render_market_watch():
    st.subheader('Market watch')
    st.caption(f"Updated {datetime.now().astimezone().strftime('%H:%M:%S %Z')} · Yahoo Finance quotes")
    quote_columns = st.columns(4)
    for column, symbol in zip(quote_columns, ['AAPL', 'GOOGL', 'AMZN', 'MSFT']):
        try:
            quote_data = fetch_stock_data(symbol, '1d', '1m')
            if quote_data.empty:
                column.metric(symbol, 'Unavailable')
                continue
            last_price = float(quote_data['Close'].iloc[-1])
            first_open = float(quote_data['Open'].iloc[0])
            change = last_price - first_open
            pct_change = (change / first_open) * 100 if first_open else 0
            column.metric(
                symbol, f'{last_price:.2f} USD',
                f'{change:+.2f} ({pct_change:+.2f}%)',
            )
        except Exception:
            column.metric(symbol, 'Unavailable')


render_market_watch()
st.caption('Market data is provided by Yahoo Finance, may be delayed, and is for informational purposes only.')
