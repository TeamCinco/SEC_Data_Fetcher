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
    # Update this path to your actual CSV location
    df = pd.read_csv('sec_filing_urls.csv.gz')  # Pandas handles .gz automatically    # Convert filing_date to datetime for better sorting
    df['filing_date'] = pd.to_datetime(df['filing_date'])
    return df

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
            st.success(f"Found {len(results)} filings for {ticker}")
            
            # Display results
            st.markdown("---")
            
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
        with Excel downloads when available.
        
        **Features:**
        - Direct Excel downloads (Financial_Report.xlsx)
        - HTML filing viewer
        - Raw TXT format
        
        **Supported Filings:**
        - 10-K (Annual Reports)
        - 10-Q (Quarterly Reports)
        
        **Data Source:** SEC EDGAR Database
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
    st.error("⚠️ CSV file not found. Please ensure 'sec_filing_urls.csv' is in the same directory as this app.")
    st.info("Run your data collection script first to generate the CSV file.")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.info("Please check your CSV file format and try again.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Built with Streamlit | Data from SEC EDGAR</div>",
    unsafe_allow_html=True
)