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

# Function to fetch financial metrics
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
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
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
ticker = st.sidebar.text_input('Enter Stock Ticker', 'ADBE', key='stock_ticker')
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

# Display financial metrics
st.header('Key Financial Metrics')
with st.spinner('Fetching data...'):
    if ticker:
        revenue, market_cap, pe_ratio = fetch_financial_metrics(ticker)
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Revenue", value=revenue)
        col2.metric(label="Market Capitalization", value=market_cap)
        col3.metric(label="P/E Ratio", value=pe_ratio)

# Update the dashboard based on user input
if st.sidebar.button('Update Dashboard'):
    data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])
    data = process_data(data)
    data = add_technical_indicators(data)
    
    last_close, change, pct_change, high, low, volume = calculate_metrics(data)
    
    # Display stock metrics in one line
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({pct_change:.2f}%)")
    col2.metric("High", f"{high:.2f} USD")
    col3.metric("Low", f"{low:.2f} USD")
    col4.metric("Volume", f"{volume:,}")
    
    # Generate the stock price chart
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'],
                                     high=data['High'],
                                     low=data['Low'],
                                     close=data['Close']))
    else:
        fig = px.line(data, x='Datetime', y='Close', title=f"{ticker} Stock Prices")
    
    # Add selected technical indicators
    for indicator in indicators:
        if indicator == 'SMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20'))
        elif indicator == 'EMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20'))
    
    # Finalize chart layout
    fig.update_layout(title=f"{ticker} Stock Price Chart",
                      xaxis_title='Time',
                      yaxis_title='Price (USD)',
                      height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display historical data
    st.subheader('Historical Stock Data')
    st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])
    
    # Display technical indicators
    st.subheader('Technical Indicators')
    st.dataframe(data[['Datetime', 'SMA_20', 'EMA_20']])

# Sidebar section for real-time stock prices
st.sidebar.header('Track Popular Stocks')
stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT']
for symbol in stock_symbols:
    real_time_data = fetch_stock_data(symbol, '1d', '1m')
    if not real_time_data.empty:
        real_time_data = process_data(real_time_data)
        last_price = float(real_time_data['Close'].iloc[-1])
        first_open = float(real_time_data['Open'].iloc[0])
        change = last_price - first_open
        pct_change = (change / first_open) * 100
        st.sidebar.metric(f"{symbol}", f"{last_price:.2f} USD", f"{change:.2f} ({pct_change:.2f}%)")

# Add footer information
st.sidebar.subheader('About This Dashboard')
st.sidebar.info('This dashboard was built to explore stock data and technical indicators interactively. Created as an original adaptation inspired by online resources.')
