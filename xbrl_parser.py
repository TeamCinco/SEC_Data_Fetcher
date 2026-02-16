"""
RELATIONAL iXBRL PARSER — FILTERED FINANCIAL STATEMENTS
- Proper XML parsing
- Safe Excel sheet names
- Full context + dimension support
- ONLY exports:
    • Income Statement
    • Balance Sheet
    • Cash Flow
    • Stockholders Equity
"""

import re
import requests
import tempfile
from pathlib import Path
from collections import defaultdict
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


class RelationalXBRLParser:

    INVALID_SHEET_CHARS = r'[:\\/?*\[\]]'

    TARGET_SHEETS = {
        "income": "Income Statement",
        "revenue": "Income Statement",
        "expense": "Income Statement",
        "profit": "Income Statement",

        "asset": "Balance Sheet",
        "liabilit": "Balance Sheet",
        "equity": "Stockholders Equity",

        "cash": "Cash Flow",
        "operating activities": "Cash Flow",
        "investing activities": "Cash Flow",
        "financing activities": "Cash Flow",
    }

    def __init__(self, html_file: str, output_file: str = None):
        self.html_file = Path(html_file)
        self.output_file = Path(output_file) if output_file else self.html_file.with_suffix(".xlsx")

        self.soup = None
        self.contexts = {}
        self.units = {}
        self.facts = []

    # ---------------------------------------------------------
    # LOAD (XML MODE)
    # ---------------------------------------------------------

    def parse_html(self):
        with open(self.html_file, "r", encoding="utf-8", errors="ignore") as f:
            self.soup = BeautifulSoup(f.read(), "lxml-xml")

    # ---------------------------------------------------------
    # CONTEXTS
    # ---------------------------------------------------------

    def extract_contexts(self):

        for ctx in self.soup.find_all("context"):
            ctx_id = ctx.get("id")
            if not ctx_id:
                continue

            context_data = {
                "period_type": None,
                "start": None,
                "end": None,
                "instant": None,
                "dimensions": []
            }

            period = ctx.find("period")
            if period:
                if period.find("instant"):
                    context_data["period_type"] = "instant"
                    context_data["instant"] = period.find("instant").text.strip()

                elif period.find("startDate") and period.find("endDate"):
                    context_data["period_type"] = "duration"
                    context_data["start"] = period.find("startDate").text.strip()
                    context_data["end"] = period.find("endDate").text.strip()

            segment = ctx.find("segment")
            if segment:
                for explicit in segment.find_all("explicitMember"):
                    dimension = explicit.get("dimension")
                    member = explicit.text.strip()
                    context_data["dimensions"].append((dimension, member))

                for typed in segment.find_all("typedMember"):
                    dimension = typed.get("dimension")
                    member = typed.get_text(strip=True)
                    context_data["dimensions"].append((dimension, member))

            self.contexts[ctx_id] = context_data

    # ---------------------------------------------------------
    # UNITS
    # ---------------------------------------------------------

    def extract_units(self):
        for unit in self.soup.find_all("unit"):
            unit_id = unit.get("id")
            measure = unit.get_text(strip=True)
            self.units[unit_id] = measure

    # ---------------------------------------------------------
    # FACTS
    # ---------------------------------------------------------

    def extract_all_facts(self):

        for tag in self.soup.find_all("nonFraction"):
            self.facts.append(self._parse_numeric(tag))

        for tag in self.soup.find_all("nonNumeric"):
            self.facts.append(self._parse_text(tag))

    def _parse_numeric(self, tag):

        text = tag.get_text(strip=True)

        if tag.get("format") == "ixt:fixed-zero":
            value = 0.0
        else:
            text = text.replace(",", "").replace("$", "").strip()
            if text in ["—", "-", "", None]:
                return None
            try:
                value = float(text)
            except:
                return None

            scale = int(tag.get("scale", "0"))
            value *= 10 ** scale

            if tag.get("sign") == "-":
                value = -abs(value)

        return {
            "type": "numeric",
            "name": tag.get("name"),
            "context": tag.get("contextRef"),
            "value": value
        }

    def _parse_text(self, tag):

        return {
            "type": "text",
            "name": tag.get("name"),
            "context": tag.get("contextRef"),
            "value": tag.get_text(strip=True)
        }

    # ---------------------------------------------------------
    # CLASSIFY STATEMENT
    # ---------------------------------------------------------

    def _classify_statement(self, label):

        label_lower = label.lower()

        for key, statement in self.TARGET_SHEETS.items():
            if key in label_lower:
                return statement

        return None

    # ---------------------------------------------------------
    # BUILD DATAFRAMES
    # ---------------------------------------------------------

    def build_statement_dataframes(self):

        statements = {
            "Income Statement": defaultdict(dict),
            "Balance Sheet": defaultdict(dict),
            "Cash Flow": defaultdict(dict),
            "Stockholders Equity": defaultdict(dict)
        }

        for fact in self.facts:

            if not fact or fact["type"] != "numeric":
                continue

            context = self.contexts.get(fact["context"])
            if not context:
                continue

            label = self._humanize(fact["name"])
            statement_type = self._classify_statement(label)

            if not statement_type:
                continue

            period = context["instant"] if context["period_type"] == "instant" else context["end"]

            statements[statement_type][label][period] = fact["value"]

        dfs = {}
        for name, data in statements.items():
            df = pd.DataFrame.from_dict(data, orient="index")
            if not df.empty:
                dfs[name] = df

        return dfs

    def _humanize(self, concept):

        if not concept:
            return "Unknown"

        if ":" in concept:
            concept = concept.split(":")[1]

        concept = re.sub(r"([A-Z])", r" \1", concept).strip()
        concept = re.sub(r"\s+", " ", concept)

        return concept

    # ---------------------------------------------------------
    # SAFE SHEET NAME
    # ---------------------------------------------------------

    def _safe_sheet_name(self, name, existing):

        name = re.sub(self.INVALID_SHEET_CHARS, "-", name)
        name = name[:31]

        original = name
        counter = 1

        while name in existing:
            name = f"{original[:28]}_{counter}"
            counter += 1

        return name

    # ---------------------------------------------------------
    # EXCEL
    # ---------------------------------------------------------

    def write_to_excel(self):

        statement_dfs = self.build_statement_dataframes()

        wb = Workbook()
        wb.remove(wb.active)

        used_names = set()

        for statement_name, df in statement_dfs.items():

            sheet_name = self._safe_sheet_name(statement_name, used_names)
            used_names.add(sheet_name)

            ws = wb.create_sheet(title=sheet_name)

            ws.cell(row=1, column=1, value="Line Item").font = Font(bold=True)

            for col_idx, col_name in enumerate(df.columns, start=2):
                ws.cell(row=1, column=col_idx, value=col_name).font = Font(bold=True)

            for row_idx, (label, row) in enumerate(df.iterrows(), start=2):
                ws.cell(row=row_idx, column=1, value=label)

                for col_idx, value in enumerate(row, start=2):
                    ws.cell(row=row_idx, column=col_idx, value=value).alignment = Alignment(horizontal="right")

            ws.column_dimensions["A"].width = 50
            for col in range(2, len(df.columns) + 2):
                ws.column_dimensions[get_column_letter(col)].width = 20

        wb.save(self.output_file)

    # ---------------------------------------------------------

    def convert(self):

        self.parse_html()
        self.extract_contexts()
        self.extract_units()
        self.extract_all_facts()
        self.write_to_excel()

        return self.output_file


# ---------------------------------------------------------
# PUBLIC FUNCTION (STREAMLIT SAFE)
# ---------------------------------------------------------

def parse_xbrl_to_excel(html_url, output_path):

    headers = {
        "User-Agent": "Research App contact@example.com"
    }

    response = requests.get(html_url, headers=headers, timeout=30)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    parser = RelationalXBRLParser(tmp_path, output_path)
    result = parser.convert()

    Path(tmp_path).unlink()

    return result
