"""
XBRL Parser Integration
Handles parsing XBRL filings and generating Excel files
when SEC Excel downloads are not available
"""
import re
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import requests
import tempfile


class UltimateXBRLParser:
    """Maximum accuracy XBRL parser for financial statements"""
    
    STATEMENT_PATTERNS = {
        'Balance Sheet': [
            r'CONSOLIDATED\s+BALANCE\s+SHEETS?',
            r'BALANCE\s+SHEETS?',
            r'STATEMENTS?\s+OF\s+FINANCIAL\s+POSITION',
        ],
        'Income Statement': [
            r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+(?:INCOME|OPERATIONS|EARNINGS)',
            r'STATEMENTS?\s+OF\s+(?:INCOME|OPERATIONS|EARNINGS)',
        ],
        'Cash Flow': [
            r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+CASH\s+FLOWS?',
            r'STATEMENTS?\s+OF\s+CASH\s+FLOWS?',
        ],
        'Stockholders Equity': [
            r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+(?:STOCKHOLDERS|SHAREHOLDERS|SHAREOWNERS).*EQUITY',
            r'STATEMENTS?\s+OF\s+(?:STOCKHOLDERS|SHAREHOLDERS|SHAREOWNERS).*EQUITY',
            r'STATEMENTS?\s+OF\s+CHANGES\s+IN\s+EQUITY',
        ],
        'Comprehensive Income': [
            r'CONSOLIDATED\s+STATEMENTS?\s+OF\s+COMPREHENSIVE\s+(?:INCOME|LOSS)',
            r'STATEMENTS?\s+OF\s+COMPREHENSIVE\s+(?:INCOME|LOSS)',
        ],
    }
    
    def __init__(self, html_file: str, output_file: str = None):
        self.html_file = Path(html_file)
        self.output_file = Path(output_file) if output_file else self.html_file.with_suffix('.xlsx')
        self.soup = None
        self.contexts = {}
        
    def parse_html(self):
        """Load and parse the HTML file"""
        with open(self.html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        self.soup = BeautifulSoup(html_content, 'lxml')
    
    def extract_contexts(self):
        """Extract all XBRL contexts"""
        context_tags = self.soup.find_all('xbrli:context')
        
        for ctx in context_tags:
            ctx_id = ctx.get('id')
            if not ctx_id:
                continue
            
            context_info = {'id': ctx_id}
            
            period = ctx.find('xbrli:period')
            if period:
                instant = period.find('xbrli:instant')
                start_date = period.find('xbrli:startdate')
                end_date = period.find('xbrli:enddate')
                
                if instant:
                    date_str = instant.get_text(strip=True)
                    context_info['instant'] = date_str
                    context_info['period_type'] = 'instant'
                    context_info['label'] = self._format_date_label(date_str)
                    context_info['sort_date'] = self._parse_date(date_str)
                elif start_date and end_date:
                    start_str = start_date.get_text(strip=True)
                    end_str = end_date.get_text(strip=True)
                    context_info['start_date'] = start_str
                    context_info['end_date'] = end_str
                    context_info['period_type'] = 'duration'
                    context_info['label'] = self._format_period_label(start_str, end_str)
                    context_info['sort_date'] = self._parse_date(end_str)
            
            entity = ctx.find('xbrli:entity')
            if entity:
                segment = entity.find('xbrli:segment')
                context_info['has_dimensions'] = segment is not None
            else:
                context_info['has_dimensions'] = False
            
            self.contexts[ctx_id] = context_info
    
    def _format_date_label(self, date_str):
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        except:
            return date_str
    
    def _format_period_label(self, start_str, end_str):
        try:
            end_dt = datetime.strptime(end_str, '%Y-%m-%d')
            start_dt = datetime.strptime(start_str, '%Y-%m-%d')
            days = (end_dt - start_dt).days
            
            if days >= 360:
                return f"Year Ended {end_dt.strftime('%b %d, %Y')}"
            elif days >= 85:
                return f"Quarter Ended {end_dt.strftime('%b %d, %Y')}"
            else:
                return f"{start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"
        except:
            return end_str
    
    def _parse_date(self, date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return datetime.min
    
    def find_statement_table(self, statement_name):
        """Find the HTML table containing a specific financial statement"""
        patterns = self.STATEMENT_PATTERNS.get(statement_name, [])
        all_tables = self.soup.find_all('table')
        
        for table in all_tables:
            xbrl_tags = table.find_all('ix:nonfraction')
            if len(xbrl_tags) < 10:
                continue
            
            text_before = []
            for elem in table.find_all_previous(['p', 'span', 'div', 'b', 'strong', 'td', 'th'], limit=30):
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    text_before.append(text)
                    if len(text_before) >= 10:
                        break
            
            context_text = ' '.join(text_before)
            
            for pattern in patterns:
                if re.search(pattern, context_text, re.IGNORECASE):
                    return table
        
        return None
    
    def extract_xbrl_facts_from_table(self, table_element):
        """Extract all XBRL facts from a table"""
        if not table_element:
            return []
        
        facts = []
        nonfraction_tags = table_element.find_all('ix:nonfraction')
        
        for tag in nonfraction_tags:
            label = self._extract_label_for_tag(tag)
            
            fact = {
                'label': label,
                'name': tag.get('name', ''),
                'contextref': tag.get('contextref', ''),
                'unitref': tag.get('unitref', ''),
                'decimals': tag.get('decimals', '0'),
                'scale': tag.get('scale', '0'),
                'sign': tag.get('sign', ''),
                'value_text': tag.get_text(strip=True),
            }
            
            value = self._parse_numeric_value(fact)
            fact['value'] = value
            facts.append(fact)
        
        return facts
    
    def _extract_label_for_tag(self, tag):
        """Extract clean label for XBRL tag"""
        row = tag.find_parent('tr')
        if not row:
            return self._humanize_concept_name(tag.get('name', 'Unknown'))
        
        cells = row.find_all(['td', 'th'])
        
        tag_cell_idx = None
        for idx, cell in enumerate(cells):
            if tag in cell.find_all('ix:nonfraction'):
                tag_cell_idx = idx
                break
        
        label_parts = []
        for idx, cell in enumerate(cells):
            if tag_cell_idx is not None and idx >= tag_cell_idx:
                break
            
            text = self._get_cell_text_clean(cell)
            
            if text and text not in ['$', '—', '-', '�']:
                label_parts.append(text)
        
        if label_parts:
            label = ' '.join(label_parts)
            label = re.sub(r'\s+', ' ', label).strip()
            return label if label else self._humanize_concept_name(tag.get('name', 'Unknown'))
        
        return self._humanize_concept_name(tag.get('name', 'Unknown'))
    
    def _get_cell_text_clean(self, cell):
        """Get clean text from cell"""
        cell_copy = BeautifulSoup(str(cell), 'lxml')
        
        for xbrl_tag in cell_copy.find_all(['ix:nonfraction', 'ix:nonnumeric']):
            xbrl_tag.decompose()
        
        text = cell_copy.get_text(strip=True)
        text = text.replace('\n', ' ').replace('\t', ' ')
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _humanize_concept_name(self, concept_name):
        """Convert concept name to human-readable label"""
        if ':' in concept_name:
            concept_name = concept_name.split(':')[1]
        
        humanized = re.sub(r'([A-Z])', r' \1', concept_name)
        humanized = humanized.strip()
        humanized = re.sub(r'\s+', ' ', humanized)
        
        return humanized
    
    def _parse_numeric_value(self, fact):
        """Parse numeric value with scale and sign"""
        value_str = fact['value_text'].replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
        
        if value_str in ['—', '-', '�', '']:
            return None
        
        try:
            value = float(value_str)
            
            if fact['scale']:
                try:
                    scale = int(fact['scale'])
                    value = value * (10 ** scale)
                except:
                    pass
            
            if fact['sign'] == '-':
                value = -abs(value)
            
            return value
        except:
            return None
    
    def create_statement_dataframe(self, statement_name, facts):
        """Create DataFrame from facts"""
        if not facts:
            return None
        
        data = defaultdict(dict)
        period_dates = {}
        
        for fact in facts:
            label = fact['label']
            context_id = fact['contextref']
            value = fact['value']
            
            if context_id in self.contexts:
                ctx = self.contexts[context_id]
                if ctx.get('has_dimensions', False):
                    continue
                
                period_label = ctx.get('label', context_id)
                data[label][period_label] = value
                
                if period_label not in period_dates:
                    period_dates[period_label] = ctx.get('sort_date', datetime.min)
        
        if not data:
            return None
        
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index.name = 'Line Item'
        
        if period_dates:
            sorted_cols = sorted(df.columns, key=lambda x: period_dates.get(x, datetime.min), reverse=True)
            df = df[sorted_cols]
        
        return df
    
    def write_dataframe_to_sheet(self, wb, sheet_name, df):
        """Write DataFrame to Excel with formatting"""
        if df is None or df.empty:
            return
        
        ws = wb.create_sheet(title=sheet_name)
        
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        ws.cell(row=1, column=1, value='Line Item').font = Font(bold=True, size=11)
        ws.cell(row=1, column=1).fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        
        for col_idx, col_name in enumerate(df.columns, start=2):
            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        for row_idx, (label, row_data) in enumerate(df.iterrows(), start=2):
            label_cell = ws.cell(row=row_idx, column=1, value=label)
            label_cell.font = Font(size=10)
            
            for col_idx, value in enumerate(row_data, start=2):
                cell = ws.cell(row=row_idx, column=col_idx)
                if pd.notna(value):
                    cell.value = value
                    if isinstance(value, (int, float)):
                        if abs(value) >= 1:
                            cell.number_format = '#,##0'
                        else:
                            cell.number_format = '0.00'
                        cell.alignment = Alignment(horizontal='right')
        
        ws.column_dimensions['A'].width = 55
        for col_idx in range(2, len(df.columns) + 2):
            col_letter = chr(64 + col_idx)
            ws.column_dimensions[col_letter].width = 20
        
        ws.freeze_panes = 'A2'
    
    def convert_to_excel(self):
        """Main conversion method"""
        self.parse_html()
        self.extract_contexts()
        
        wb = Workbook()
        wb.remove(wb.active)
        
        sheets_created = 0
        
        for statement_name in self.STATEMENT_PATTERNS.keys():
            table = self.find_statement_table(statement_name)
            
            if table:
                facts = self.extract_xbrl_facts_from_table(table)
                df = self.create_statement_dataframe(statement_name, facts)
                
                if df is not None and not df.empty:
                    self.write_dataframe_to_sheet(wb, statement_name, df)
                    sheets_created += 1
        
        if sheets_created > 0:
            wb.save(self.output_file)
        
        return self.output_file


def parse_xbrl_to_excel(html_url, output_path):
    """
    Parse XBRL HTML filing and generate Excel file
    
    Args:
        html_url: URL to the HTML filing
        output_path: Where to save the generated Excel file
    
    Returns:
        Path to generated Excel file or None if failed
    """
    try:
        # SEC requires User-Agent header
        headers = {
            'User-Agent': 'SEC Filing App contact@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        
        # Download HTML from URL
        response = requests.get(html_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='wb') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        
        # Parse with XBRL parser
        parser = UltimateXBRLParser(tmp_path, output_path)
        result = parser.convert_to_excel()
        
        # Clean up temp file
        Path(tmp_path).unlink()
        
        return result
    except Exception as e:
        print(f"Error parsing XBRL: {e}")
        return None