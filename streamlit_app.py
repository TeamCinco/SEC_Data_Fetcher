"""
SEC Filing Downloader - Main App
Streamlit application for downloading SEC filings with Excel exports
Fetches data dynamically from SEC API using ticker.json
"""
import streamlit as st
from data_loader import get_filings_for_ticker, get_company_info, load_ticker_data
from stock_data import get_stock_info
from ui_components import (
    render_company_header,
    render_stock_metrics,
    render_valuation_metrics,
    render_profitability_metrics,
    render_share_statistics,
    render_filing_row,
    render_sidebar
)


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


def main():
    """Main application logic"""
    try:
        # Load ticker data to check availability
        tickers = load_ticker_data()
        
        if not tickers:
            st.error("❌ No ticker data available. Please ensure ticker.json exists.")
            return
        
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
            # Check if ticker exists
            if ticker not in tickers:
                st.warning(f"❌ Ticker '{ticker}' not found in database. Please try a different ticker.")
                st.info(f"💡 Available tickers: {', '.join(list(tickers.keys())[:20])}...")
                return
            
            # Show loading message
            with st.spinner(f"Fetching filings for {ticker} from SEC..."):
                results = get_filings_for_ticker(ticker, filing_type)
            
            if len(results) > 0:
                # Company Info Header
                stock_info = get_stock_info(ticker)
                
                if stock_info:
                    render_company_header(stock_info)
                    render_stock_metrics(stock_info)
                    render_valuation_metrics(stock_info)
                    render_profitability_metrics(stock_info)
                    render_share_statistics(stock_info)
                
                st.markdown("---")
                st.success(f"Found {len(results)} filings for {ticker}")
                
                # Display results
                for _, row in results.iterrows():
                    render_filing_row(row)
            
            else:
                st.warning(f"No {filing_type} filings found for {ticker}.")
        
        # Sidebar with info
        render_sidebar(tickers)
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")


if __name__ == "__main__":
    main()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>Built with Streamlit | Data from SEC EDGAR & Yahoo Finance</div>",
        unsafe_allow_html=True
    )