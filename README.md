# SEC Filing Downloader

A Streamlit web app for downloading SEC 10-K and 10-Q filings with direct Excel access.

## Quick Start

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your `sec_filing_urls.csv` is in the same directory

3. Run the app:
```bash
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud (FREE)

1. Push this code to GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

2. Go to https://share.streamlit.io

3. Click "New app"

4. Select your repository, branch (main), and main file path (streamlit_app.py)

5. Click "Deploy"

Done! Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

## File Structure

```
.
├── streamlit_app.py          # Main Streamlit app
├── requirements.txt           # Python dependencies
├── sec_filing_urls.csv        # Your SEC filing database (generated from your script)
└── README.md                  # This file
```

## Features

- Search by ticker symbol
- Filter by filing type (10-K, 10-Q, or All)
- Direct download links for:
  - Excel files (Financial_Report.xlsx)
  - HTML filing viewer
  - Raw TXT format
- Database statistics in sidebar
- Clean, responsive UI

## Data Source

All data comes from SEC EDGAR database via their public API.
