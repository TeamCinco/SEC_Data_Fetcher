import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="SEC Filing Downloader",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 SEC Filing Downloader")
st.markdown("### Download 10-K and 10-Q filings with direct Excel links")
st.markdown("---")

# Load your CSV
@st.cache_data
def load_data():
    df = pd.read_csv('sec_filing_urls.csv.gz')
    df['filing_date'] = pd.to_datetime(df['filing_date'])
    return df

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

try:
    df = load_data()
    
    # Search interface
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.text_input("Enter Ticker Symbol", "AAPL", key="ticker").upper().strip()
    
    with col2:
        filing_type = st.selectbox("Filing Type", ["10-K", "10-Q", "All"], key="filing_type")
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Search logic
    if search_button or ticker:
        # Filter by ticker
        results = df[df['ticker'] == ticker].copy()
        
        # Filter by filing type if not "All"
        if filing_type != "All":
            results = results[results['filing_type'] == filing_type]
        
        # Sort by date descending (most recent first)
        results = results.sort_values('filing_date', ascending=False)
        
        if len(results) > 0:
            # Company Info Header
            stock_info = get_stock_info(ticker)
            
            if stock_info:
                st.markdown("---")
                
                # Company name and description
                st.markdown(f"## {stock_info['name']}")
                
                # Key info row
                info_cols = st.columns(3)
                with info_cols[0]:
                    st.markdown(f"**Sector:** {stock_info['sector'] or 'N/A'}")
                with info_cols[1]:
                    st.markdown(f"**Industry:** {stock_info['industry'] or 'N/A'}")
                with info_cols[2]:
                    employees = f"{stock_info['employees']:,}" if stock_info['employees'] else "N/A"
                    st.markdown(f"**Employees:** {employees}")
                
                # Company description
                if stock_info['description']:
                    with st.expander("📋 Company Overview", expanded=False):
                        st.write(stock_info['description'])
                
                st.markdown("---")
                
                # Stock Price & Market Metrics
                st.subheader("📊 Stock & Market Data")
                price_cols = st.columns(6)
                
                with price_cols[0]:
                    price_display = f"${stock_info['price']:.2f}" if stock_info['price'] else "N/A"
                    change_display = f"{stock_info['change']:.2f}%" if stock_info['change'] else "N/A"
                    st.metric("Stock Price", price_display, change_display)
                
                with price_cols[1]:
                    st.metric("Market Cap", format_number(stock_info['market_cap']))
                
                with price_cols[2]:
                    st.metric("Enterprise Value", format_number(stock_info['enterprise_value']))
                
                with price_cols[3]:
                    high_52w = f"${stock_info['52w_high']:.2f}" if stock_info['52w_high'] else "N/A"
                    st.metric("52W High", high_52w)
                
                with price_cols[4]:
                    low_52w = f"${stock_info['52w_low']:.2f}" if stock_info['52w_low'] else "N/A"
                    st.metric("52W Low", low_52w)
                
                with price_cols[5]:
                    beta_display = f"{stock_info['beta']:.2f}" if stock_info['beta'] else "N/A"
                    st.metric("Beta", beta_display)
                
                # Valuation Metrics
                st.subheader("💰 Valuation Ratios")
                val_cols = st.columns(6)
                
                with val_cols[0]:
                    pe_display = f"{stock_info['pe_ratio']:.2f}" if stock_info['pe_ratio'] else "N/A"
                    st.metric("P/E Ratio", pe_display)
                
                with val_cols[1]:
                    fwd_pe = f"{stock_info['forward_pe']:.2f}" if stock_info['forward_pe'] else "N/A"
                    st.metric("Forward P/E", fwd_pe)
                
                with val_cols[2]:
                    peg = f"{stock_info['peg_ratio']:.2f}" if stock_info['peg_ratio'] else "N/A"
                    st.metric("PEG Ratio", peg)
                
                with val_cols[3]:
                    pb = f"{stock_info['price_to_book']:.2f}" if stock_info['price_to_book'] else "N/A"
                    st.metric("Price/Book", pb)
                
                with val_cols[4]:
                    ps = f"{stock_info['price_to_sales']:.2f}" if stock_info['price_to_sales'] else "N/A"
                    st.metric("Price/Sales", ps)
                
                with val_cols[5]:
                    ev_rev = f"{stock_info['ev_to_revenue']:.2f}" if stock_info['ev_to_revenue'] else "N/A"
                    st.metric("EV/Revenue", ev_rev)
                
                # Profitability & Growth Metrics
                st.subheader("📈 Profitability & Growth")
                profit_cols = st.columns(6)
                
                with profit_cols[0]:
                    profit_margin = f"{stock_info['profit_margin']*100:.2f}%" if stock_info['profit_margin'] else "N/A"
                    st.metric("Profit Margin", profit_margin)
                
                with profit_cols[1]:
                    op_margin = f"{stock_info['operating_margin']*100:.2f}%" if stock_info['operating_margin'] else "N/A"
                    st.metric("Operating Margin", op_margin)
                
                with profit_cols[2]:
                    roe = f"{stock_info['roe']*100:.2f}%" if stock_info['roe'] else "N/A"
                    st.metric("ROE", roe)
                
                with profit_cols[3]:
                    roa = f"{stock_info['roa']*100:.2f}%" if stock_info['roa'] else "N/A"
                    st.metric("ROA", roa)
                
                with profit_cols[4]:
                    rev_growth = f"{stock_info['revenue_growth']*100:.2f}%" if stock_info['revenue_growth'] else "N/A"
                    st.metric("Revenue Growth", rev_growth)
                
                with profit_cols[5]:
                    earn_growth = f"{stock_info['earnings_growth']*100:.2f}%" if stock_info['earnings_growth'] else "N/A"
                    st.metric("Earnings Growth", earn_growth)
                
                # Share Statistics
                st.subheader("📉 Share Statistics")
                share_cols = st.columns(3)
                
                with share_cols[0]:
                    shares_out = f"{stock_info['shares_outstanding']/1e9:.2f}B" if stock_info['shares_outstanding'] else "N/A"
                    st.metric("Shares Outstanding", shares_out)
                
                with share_cols[1]:
                    float_sh = f"{stock_info['float_shares']/1e9:.2f}B" if stock_info['float_shares'] else "N/A"
                    st.metric("Float", float_sh)
                
                with share_cols[2]:
                    avg_vol = f"{stock_info['avg_volume']/1e6:.2f}M" if stock_info['avg_volume'] else "N/A"
                    st.metric("Avg Volume", avg_vol)
            
            st.markdown("---")
            st.success(f"Found {len(results)} filings for {ticker}")
            
            # Display results
            for _, row in results.iterrows():
                with st.container():
                    col_date, col_type, col_links = st.columns([1, 1, 3])
                    
                    with col_date:
                        st.markdown(f"**{row['filing_date'].strftime('%Y-%m-%d')}**")
                    
                    with col_type:
                        st.markdown(f"`{row['filing_type']}`")
                    
                    with col_links:
                        link_col1, link_col2, link_col3 = st.columns(3)
                        
                        with link_col1:
                            if pd.notna(row.get('excel_url')):
                                st.link_button("📊 Download Excel", row['excel_url'], use_container_width=True)
                            else:
                                st.button("📊 No Excel", disabled=True, use_container_width=True)
                        
                        with link_col2:
                            if pd.notna(row.get('filing_url')):
                                st.link_button("📄 View Filing", row['filing_url'], use_container_width=True)
                            else:
                                st.button("📄 No Filing", disabled=True, use_container_width=True)
                        
                        with link_col3:
                            # Build TXT URL from accession number
                            if pd.notna(row.get('accession_number')):
                                accession_clean = row['accession_number'].replace('-', '')
                                txt_url = f"https://www.sec.gov/Archives/edgar/data/{row['cik']}/{accession_clean}/{row['accession_number']}.txt"
                                st.link_button("📝 Raw TXT", txt_url, use_container_width=True)
                    
                    st.markdown("---")
        
        else:
            st.warning(f"No filings found for {ticker}. Try a different ticker symbol.")
    
    # Sidebar with info
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This tool provides direct access to SEC filings (10-K annual reports and 10-Q quarterly reports) 
        with Excel downloads when available, plus comprehensive company metrics.
        
        **Features:**
        - Direct Excel downloads (Financial_Report.xlsx)
        - HTML filing viewer
        - Raw TXT format
        - Real-time stock price & market data
        - Valuation ratios (P/E, PEG, P/B, P/S, EV/Revenue)
        - Profitability metrics (Margins, ROE, ROA)
        - Growth rates (Revenue, Earnings)
        - Share statistics
        
        **Supported Filings:**
        - 10-K (Annual Reports)
        - 10-Q (Quarterly Reports)
        
        **Data Sources:**
        - SEC EDGAR Database
        - Yahoo Finance API
        """)
        
        st.markdown("---")
        
        # Stats
        st.header("Database Stats")
        total_filings = len(df[df['status'] == 'found'])
        total_tickers = df['ticker'].nunique()
        excel_available = len(df[df.get('excel_url').notna()]) if 'excel_url' in df.columns else 0
        
        st.metric("Total Filings", f"{total_filings:,}")
        st.metric("Companies", f"{total_tickers:,}")
        st.metric("Excel Available", f"{excel_available:,}")

except FileNotFoundError:
    st.error("⚠️ CSV file not found. Please ensure 'sec_filing_urls.csv.gz' is in the same directory as this app.")
    st.info("Run your data collection script first to generate the CSV file.")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please check your CSV file format and try again.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Built with Streamlit | Data from SEC EDGAR & Yahoo Finance</div>",
    unsafe_allow_html=True
)