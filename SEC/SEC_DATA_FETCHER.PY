import asyncio
import aiohttp
import pandas as pd
from time import sleep
import signal
import sys
import atexit

# SEC requires a User-Agent header
headers = {
    'User-Agent': 'Humberto Renderos humberto.jobs24@example.com'
}

# Global list to store results for graceful shutdown
results = []
output_path = '/Users/jazzhashzzz/Desktop/SEC_Data_Fetcher/output/sec_filing_urls.csv'

def save_results():
    """Save current results to CSV"""
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        print(f"\n✓ Saved {len(results)} results to: {output_path}")
        return True
    else:
        print("\nNo results to save yet.")
        return False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n⚠️  Interrupted! Saving progress...")
    save_results()
    print("Exiting...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTSTP, signal_handler)
atexit.register(save_results)

async def fetch_json(session, url):
    """Async fetch JSON from URL"""
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def get_all_filings_async(session, ticker, cik, filing_type='10-K'):
    """Get ALL filings for a ticker asynchronously"""
    cik_padded = str(cik).zfill(10)
    
    try:
        # Get company filings
        url = f'https://data.sec.gov/submissions/CIK{cik_padded}.json'
        data = await fetch_json(session, url)
        
        if not data:
            return []
        
        found_filings = []
        
        # Recent filings
        filings = data['filings']['recent']
        for i, form in enumerate(filings['form']):
            if form == filing_type:
                accession_no = filings['accessionNumber'][i]
                filing_date = filings['filingDate'][i]
                primary_document = filings['primaryDocument'][i]
                
                accession_clean = accession_no.replace('-', '')
                excel_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/Financial_Report.xlsx'
                filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_document}'
                
                found_filings.append({
                    'ticker': ticker.upper(),
                    'cik': cik,
                    'filing_type': filing_type,
                    'accession_number': accession_no,
                    'filing_date': filing_date,
                    'excel_url': excel_url,
                    'filing_url': filing_url,
                    'status': 'found'
                })
        
        # Older filings
        if 'files' in data['filings']:
            old_file_tasks = []
            for file_info in data['filings']['files']:
                file_url = f"https://data.sec.gov/submissions/{file_info['name']}"
                old_file_tasks.append(fetch_json(session, file_url))
            
            old_files_data = await asyncio.gather(*old_file_tasks, return_exceptions=True)
            
            for old_data in old_files_data:
                if old_data and not isinstance(old_data, Exception):
                    for i, form in enumerate(old_data['form']):
                        if form == filing_type:
                            accession_no = old_data['accessionNumber'][i]
                            filing_date = old_data['filingDate'][i]
                            primary_document = old_data['primaryDocument'][i]
                            
                            accession_clean = accession_no.replace('-', '')
                            excel_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/Financial_Report.xlsx'
                            filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_document}'
                            
                            found_filings.append({
                                'ticker': ticker.upper(),
                                'cik': cik,
                                'filing_type': filing_type,
                                'accession_number': accession_no,
                                'filing_date': filing_date,
                                'excel_url': excel_url,
                                'filing_url': filing_url,
                                'status': 'found'
                            })
        
        print(f'✓ {ticker.upper()}: Found {len(found_filings)} {filing_type} filings')
        return found_filings
    
    except Exception as e:
        print(f'✗ {ticker.upper()}: Error - {e}')
        return []

async def process_all_tickers(tickers, filing_types):
    """Process all tickers concurrently"""
    # SEC rate limit: ~10 requests per second
    connector = aiohttp.TCPConnector(limit=3)  # Max 3 concurrent connections
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        
        for ticker, cik in tickers.items():
            for filing_type in filing_types:
                tasks.append(get_all_filings_async(session, ticker, cik, filing_type))
        
        # Process in small batches to respect rate limits
        batch_size = 5
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if result and not isinstance(result, Exception):
                    results.extend(result)
            
            # Longer delay between batches (SEC allows ~10 req/sec)
            if i + batch_size < len(tasks):
                print(f"  Progress: {i+batch_size}/{len(tasks)} tasks completed...")
                await asyncio.sleep(1.0)  # 1 second between batches

async def main():
    # Read ticker file
    ticker_file_path = '/Users/jazzhashzzz/Documents/Market_Analysis_files/ticker.txt'
    
    tickers = {}
    with open(ticker_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                ticker, cik = line.split('\t')
                tickers[ticker] = int(cik)
    
    print(f"Processing {len(tickers)} tickers...")
    
    # Filing types to fetch
    filing_types = ['10-K', '10-Q']
    
    # Process all tickers
    await process_all_tickers(tickers, filing_types)
    
    # Save results
    save_results()
    
    # Display summary
    if results:
        df = pd.DataFrame(results)
        successful = df[df['status'] == 'found'].copy()
        
        print("\n" + "="*80)
        print(f"TOTAL RESULTS: {len(successful)} filings found")
        print("="*80)
        
        summary = successful.groupby(['ticker', 'filing_type']).size().reset_index(name='count')
        print("\nBreakdown by ticker and filing type:")
        print(summary.to_string(index=False))
        
        print(f"\nSaved to: {output_path}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user! Saving progress...")
        save_results()
        sys.exit(0)