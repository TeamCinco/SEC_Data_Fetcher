# 📊 SEC Real-Time Filing-to-Excel Converter

### "Because waiting for the SEC to generate an Excel file shouldn't be part of your workflow."

## 📌 What is this?

When a company (like PayPal or Apple) submits a new financial filing (10-K or 10-Q), the SEC website provides the **PDF** and **HTML** versions immediately. However, it often takes **hours or even days** for the official "Interactive Data" Excel file to appear on the EDGAR system.

**This tool bridges that gap.** It takes the raw HTML filing and instantly converts it into a structured Excel workbook that looks exactly like the one the SEC eventually provides.

---

## 🚀 Why use this?

* **Zero Wait Time:** Get your data the second the filing hits the wire.
* **Dynamic Extraction:** No hardcoded lists. Whether it's a tech company or a bank, the tool finds the specific tables (Balance Sheet, Income Statement, etc.) automatically.
* **iXBRL Powered:** It doesn't just "read" text; it pulls the hidden digital tags (XBRL) embedded by the company’s accountants. This means the numbers are 100% accurate.
* **No "Messy" Sheets:** Unlike a standard PDF-to-Excel converter that creates a mess of merged cells, this creates clean, analysis-ready rows and columns.

---

## 🛠️ How it works (The Simple Version)

1. **The Input:** You give it a link or a downloaded `.html` filing from the SEC EDGAR website.
2. **The Search:** The tool scans the document for "Smart Tags" (iXBRL) that identify specific financial metrics (e.g., *Net Income*, *Total Assets*).
3. **The Build:** It groups these tags into their respective categories:
* **Balance Sheet**
* **Income Statement**
* **Cash Flows**
* **Stockholders' Equity**


4. **The Output:** It saves everything into a multi-sheet `.xlsx` file formatted for financial modeling.

---

## 📂 Project Structure

* `ixbrl_to_excel.py`: The "Smart" engine that reads digital tags.
* `dynamic_xbrl_extractor.py`: The "Flexible" engine that handles different company naming conventions automatically.
* `examples/`: Contains the converted PayPal 2025 filings as a proof of concept.

---

## 🏁 Quick Start

1. Download your desired `.html` filing from the SEC.
2. Run the script.
3. Open your brand-new Excel file.

