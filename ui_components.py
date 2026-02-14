"""
UI components for the Streamlit app
"""
import streamlit as st
import pandas as pd
from stock_data import format_number


def render_company_header(stock_info):
    """Render company name and basic info"""
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


def render_stock_metrics(stock_info):
    """Render stock price and market metrics"""
    st.markdown("---")
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


def render_valuation_metrics(stock_info):
    """Render valuation ratios"""
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


def render_profitability_metrics(stock_info):
    """Render profitability and growth metrics"""
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


def render_share_statistics(stock_info):
    """Render share statistics"""
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


def render_filing_row(row):
    """Render a single filing row with Excel generation capability"""
    with st.container():
        col_date, col_type, col_links = st.columns([1, 1, 3])
        
        with col_date:
            st.markdown(f"**{row['filing_date'].strftime('%Y-%m-%d')}**")
        
        with col_type:
            st.markdown(f"`{row['filing_type']}`")
        
        with col_links:
            link_col1, link_col2, link_col3 = st.columns(3)
            
            with link_col1:
                # Check if SEC Excel URL exists AND is valid
                has_sec_excel = pd.notna(row.get('excel_url')) and str(row.get('excel_url')).strip() != ''
                
                if has_sec_excel:
                    # SEC Excel is available - but might be a broken link
                    # Show both download and generate options
                    st.link_button("📊 Download Excel", row['excel_url'], use_container_width=True)
                    
                    # Also show generate option as backup
                    button_key = f"gen_excel_{row['accession_number']}"
                    backup_button_key = f"backup_btn_{row['accession_number']}"
                    
                    if st.button("🔧 Generate Excel (Backup)", use_container_width=True, key=backup_button_key, help="Use if SEC download fails"):
                        with st.spinner("Parsing XBRL and generating Excel..."):
                            try:
                                from xbrl_parser import parse_xbrl_to_excel
                                import tempfile
                                import os
                                
                                # Create temp output file
                                output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                                output_path = output_file.name
                                output_file.close()
                                
                                # Parse XBRL to Excel
                                result = parse_xbrl_to_excel(row['filing_url'], output_path)
                                
                                if result:
                                    # Read the file
                                    with open(output_path, 'rb') as f:
                                        excel_data = f.read()
                                    
                                    # Store in session state
                                    st.session_state[button_key] = excel_data
                                    
                                    # Clean up temp file
                                    os.unlink(output_path)
                                    
                                    st.success("✅ Excel generated successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to generate Excel file")
                            except Exception as e:
                                st.error(f"❌ Error generating Excel: {str(e)}")
                    
                    # Show download button if generated
                    if button_key in st.session_state:
                        excel_data = st.session_state[button_key]
                        # Ensure it's bytes
                        if isinstance(excel_data, bytes):
                            st.download_button(
                                label="⬇️ Download Generated Excel",
                                data=excel_data,
                                file_name=f"{row['ticker']}_{row['filing_type']}_{row['filing_date'].strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key=f"dl_gen_{row['accession_number']}"
                            )
                        else:
                            st.error(f"❌ Invalid data format in cache. Please regenerate.")
                            # Clear invalid data
                            del st.session_state[button_key]
                
                else:
                    # No SEC Excel - generate from XBRL
                    button_key = f"gen_excel_{row['accession_number']}"
                    
                    # Check if already generated
                    if button_key in st.session_state:
                        # Already generated - show download button
                        excel_data = st.session_state[button_key]
                        # Ensure it's bytes
                        if isinstance(excel_data, bytes):
                            st.download_button(
                                label="⬇️ Download Generated Excel",
                                data=excel_data,
                                file_name=f"{row['ticker']}_{row['filing_type']}_{row['filing_date'].strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                                key=f"dl_{row['accession_number']}"
                            )
                        else:
                            st.error(f"❌ Invalid data format in cache. Please regenerate.")
                            # Clear invalid data
                            del st.session_state[button_key]
                    else:
                        # Not yet generated - show generate button
                        gen_button_key = f"gen_btn_{row['accession_number']}"
                        if st.button("📊 Generate Excel", use_container_width=True, key=gen_button_key, type="primary"):
                            with st.spinner("Parsing XBRL and generating Excel..."):
                                try:
                                    from xbrl_parser import parse_xbrl_to_excel
                                    import tempfile
                                    import os
                                    
                                    # Create temp output file
                                    output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
                                    output_path = output_file.name
                                    output_file.close()
                                    
                                    # Parse XBRL to Excel
                                    result = parse_xbrl_to_excel(row['filing_url'], output_path)
                                    
                                    if result:
                                        # Read the file
                                        with open(output_path, 'rb') as f:
                                            excel_data = f.read()
                                        
                                        # Verify it's bytes
                                        if not isinstance(excel_data, bytes):
                                            st.error("❌ Generated file has invalid format")
                                        else:
                                            # Store in session state
                                            st.session_state[button_key] = excel_data
                                            
                                            st.success("✅ Excel generated successfully!")
                                            st.rerun()  # Rerun to show download button
                                        
                                        # Clean up temp file
                                        os.unlink(output_path)
                                    else:
                                        st.error("❌ Failed to generate Excel file. The filing may not contain XBRL data.")
                                except Exception as e:
                                    st.error(f"❌ Error generating Excel: {str(e)}")
            
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


def render_sidebar(tickers):
    """Render sidebar with info and stats"""
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This tool provides direct access to SEC filings (10-K annual reports and 10-Q quarterly reports) 
        with Excel downloads when available, plus comprehensive company metrics.
        
        **Features:**
        - Direct Excel downloads (Financial_Report.xlsx)
        - Auto-generate Excel from XBRL when SEC file unavailable
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
        - SEC EDGAR Database (Live API)
        - Yahoo Finance API
        """)
        
        st.markdown("---")
        
        # Stats
        st.header("Database Stats")
        total_companies = len(tickers)
        
        st.metric("Total Companies", f"{total_companies:,}")
        st.metric("Data Source", "SEC EDGAR API")
        st.metric("Update Frequency", "Real-time")