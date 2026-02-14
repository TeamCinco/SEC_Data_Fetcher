"""
Data loading from ticker.json and SEC API
Fetches filing data dynamically instead of using pre-generated CSV
"""
import json
import aiohttp
import asyncio
import streamlit as st
from pathlib import Path
from datetime import datetime


@st.cache_data
def load_ticker_data():
    """Load ticker data from ticker.json"""
    ticker_file = Path('ticker.json')
    
    if not ticker_file.exists():
        st.error(f"❌ ticker.json not found at: {ticker_file.absolute()}")
        return {}
    
    with open(ticker_file, 'r') as f:
        ticker_data = json.load(f)
    
    # Convert to dict: {ticker: {cik, title}}
    tickers = {}
    for key, value in ticker_data.items():
        ticker = value['ticker']
        tickers[ticker] = {
            'cik': value['cik_str'],
            'title': value.get('title', ticker)
        }
    
    return tickers


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_company_filings(ticker, cik, filing_types=['10-K', '10-Q']):
    """
    Fetch all filings for a company from SEC API
    
    Args:
        ticker: Stock ticker symbol
        cik: Company CIK number
        filing_types: List of filing types to fetch
    
    Returns:
        List of filing dictionaries
    """
    # Run async function in sync context
    return asyncio.run(_fetch_filings_async(ticker, cik, filing_types))


async def _fetch_filings_async(ticker, cik, filing_types):
    """Async implementation of filing fetch"""
    headers = {
        'User-Agent': 'SEC Filing App contact@example.com'
    }
    
    cik_padded = str(cik).zfill(10)
    url = f'https://data.sec.gov/submissions/CIK{cik_padded}.json'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                
                filings = []
                
                # Process recent filings
                recent = data.get('filings', {}).get('recent', {})
                filings.extend(_process_filings(ticker, cik, recent, filing_types))
                
                # Process older filings if needed
                files = data.get('filings', {}).get('files', [])
                for file_info in files:
                    file_url = f"https://data.sec.gov/submissions/{file_info['name']}"
                    
                    async with session.get(file_url, headers=headers) as file_response:
                        if file_response.status == 200:
                            file_data = await file_response.json()
                            filings.extend(_process_filings(ticker, cik, file_data, filing_types))
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                
                return filings
    
    except Exception as e:
        st.warning(f"Error fetching data for {ticker}: {e}")
        return []


def _process_filings(ticker, cik, filing_data, filing_types):
    """Process filing data and extract relevant information"""
    filings = []
    
    if not filing_data:
        return filings
    
    forms = filing_data.get('form', [])
    accession_numbers = filing_data.get('accessionNumber', [])
    filing_dates = filing_data.get('filingDate', [])
    primary_documents = filing_data.get('primaryDocument', [])
    
    for i, form in enumerate(forms):
        if form in filing_types:
            accession_no = accession_numbers[i]
            filing_date = filing_dates[i]
            primary_doc = primary_documents[i]
            
            accession_clean = accession_no.replace('-', '')
            
            # Build URLs
            excel_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/Financial_Report.xlsx'
            filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_doc}'
            
            filings.append({
                'ticker': ticker.upper(),
                'cik': cik,
                'filing_type': form,
                'accession_number': accession_no,
                'filing_date': datetime.strptime(filing_date, '%Y-%m-%d'),
                'excel_url': excel_url,
                'filing_url': filing_url,
                'status': 'found'
            })
    
    return filings


def get_filings_for_ticker(ticker, filing_type='All'):
    """
    Get filings for a specific ticker
    
    Args:
        ticker: Stock ticker symbol
        filing_type: '10-K', '10-Q', or 'All'
    
    Returns:
        DataFrame with filing information
    """
    import pandas as pd
    
    # Load ticker data
    tickers = load_ticker_data()
    
    if ticker not in tickers:
        return pd.DataFrame()
    
    # Determine which filing types to fetch
    if filing_type == 'All':
        types = ['10-K', '10-Q']
    else:
        types = [filing_type]
    
    # Fetch filings
    cik = tickers[ticker]['cik']
    filings = fetch_company_filings(ticker, cik, types)
    
    if not filings:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(filings)
    
    # Sort by date descending
    df = df.sort_values('filing_date', ascending=False)
    
    return df


def get_company_info(ticker):
    """Get company basic info from ticker.json"""
    tickers = load_ticker_data()
    
    if ticker not in tickers:
        return None
    
    return {
        'ticker': ticker,
        'cik': tickers[ticker]['cik'],
        'name': tickers[ticker]['title']
    }