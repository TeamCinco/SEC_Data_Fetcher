"""
Stock data fetching and formatting utilities
"""
import streamlit as st


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_info(ticker):
    """Fetch comprehensive stock data from Yahoo Finance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        
        return {
            'name': info.get('longName', ticker),
            'price': info.get('currentPrice', info.get('regularMarketPrice')),
            'change': info.get('regularMarketChangePercent'),
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'ev_to_revenue': info.get('enterpriseToRevenue'),
            'ev_to_ebitda': info.get('enterpriseToEbitda'),
            'profit_margin': info.get('profitMargins'),
            'operating_margin': info.get('operatingMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'beta': info.get('beta'),
            '52w_high': info.get('fiftyTwoWeekHigh'),
            '52w_low': info.get('fiftyTwoWeekLow'),
            'avg_volume': info.get('averageVolume'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'employees': info.get('fullTimeEmployees'),
            'description': info.get('longBusinessSummary'),
        }
    except:
        return None


def format_number(num):
    """Format large numbers into readable format"""
    if num is None:
        return "N/A"
    if num >= 1e12:
        return f"${num/1e12:.2f}T"
    elif num >= 1e9:
        return f"${num/1e9:.2f}B"
    elif num >= 1e6:
        return f"${num/1e6:.2f}M"
    else:
        return f"${num:,.0f}"
