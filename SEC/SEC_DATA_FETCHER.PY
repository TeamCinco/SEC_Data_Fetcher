import requests
import pandas as pd
from time import sleep
import signal
import sys
import atexit

# SEC requires a User-Agent header
headers = {
    'User-Agent': 'Humberto Renderos humberto.jobs24@gmail.com'
}

# Global list to store results for graceful shutdown
results = []
output_path = '/Users/jazzhashzzz/Documents/Market_Analysis_files/output/sec/sec_filing_urls.csv'

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

def get_all_filings_fast(cik, filing_type='10-K'):
    """Get ALL filings - just build the URLs, don't check if they exist"""
    cik_padded = str(cik).zfill(10)
    
    try:
        # Get company filings
        url = f'https://data.sec.gov/submissions/CIK{cik_padded}.json'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
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
                    'filing_type': filing_type,
                    'accession_number': accession_no,
                    'filing_date': filing_date,
                    'excel_url': excel_url,
                    'filing_url': filing_url,
                    'status': 'found'
                })
        
        # Older filings
        if 'files' in data['filings']:
            for file_info in data['filings']['files']:
                file_url = f"https://data.sec.gov/submissions/{file_info['name']}"
                try:
                    file_response = requests.get(file_url, headers=headers)
                    file_response.raise_for_status()
                    old_data = file_response.json()
                    
                    for i, form in enumerate(old_data['form']):
                        if form == filing_type:
                            accession_no = old_data['accessionNumber'][i]
                            filing_date = old_data['filingDate'][i]
                            primary_document = old_data['primaryDocument'][i]
                            
                            accession_clean = accession_no.replace('-', '')
                            excel_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/Financial_Report.xlsx'
                            filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{primary_document}'
                            
                            found_filings.append({
                                'filing_type': filing_type,
                                'accession_number': accession_no,
                                'filing_date': filing_date,
                                'excel_url': excel_url,
                                'filing_url': filing_url,
                                'status': 'found'
                            })
                    
                except Exception as e:
                    print(f"    Error fetching old filings: {e}")
        
        print(f'    Found {len(found_filings)} {filing_type} filings')
        return found_filings if found_filings else [{'filing_type': filing_type, 'status': 'no_filings_found'}]
    
    except Exception as e:
        return [{'filing_type': filing_type, 'status': f'error: {str(e)}'}]

# Read ticker file
ticker_file_path = '/Users/jazzhashzzz/Documents/Market_Analysis_files/ticker.txt'

tickers = {}
with open(ticker_file_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line:
            ticker, cik = line.split('\t')
            tickers[ticker] = int(cik)

# Filing types to fetch
filing_types = ['10-K', '10-Q']

# Get filings for each ticker
try:
    for ticker, cik in tickers.items():
        print(f'Processing {ticker.upper()}... (CIK: {cik})', end=' ')
        
        for filing_type in filing_types:
            filing_list = get_all_filings_fast(cik, filing_type)
            
            for filing_info in filing_list:
                results.append({
                    'ticker': ticker.upper(),
                    'cik': cik,
                    **filing_info
                })
        
        sleep(0.15)  # Just rate limit the API calls

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user! Saving progress...")
    save_results()
    sys.exit(0)

# Save final results
save_results()

# Display summary
df = pd.DataFrame(results)
successful = df[df['status'] == 'found'].copy()

print("\n" + "="*80)
print(f"TOTAL RESULTS: {len(successful)} filings found")
print("="*80)

summary = successful.groupby(['ticker', 'filing_type']).size().reset_index(name='count')
print("\nBreakdown by ticker and filing type:")
print(summary.to_string(index=False))

print(f"\nSaved to: {output_path}")