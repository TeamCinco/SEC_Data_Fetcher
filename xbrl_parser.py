import requests
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

HEADERS = {
    "User-Agent": "SEC Filing App contact@example.com"
}

XBRL_NS = "{http://www.xbrl.org/2003/instance}"
LINK_NS = "{http://www.xbrl.org/2003/linkbase}"
XLINK_NS = "{http://www.w3.org/1999/xlink}"


class SECXBRLParser:

    def extract_ids_from_url(self, filing_url):
        parts = filing_url.strip("/").split("/")
        return parts[6], parts[7]

    def get_filing_index(self, cik, accession):
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        return r.json()["directory"]["item"]

    def find_file(self, files, suffix):
        for f in files:
            if f["name"].lower().endswith(suffix):
                return f["name"]
        return None

    # ---------------------------------------------------------
    # Parse ALL facts with context dates
    # ---------------------------------------------------------
    def parse_instance(self, cik, accession, files):
        instance_file = None

        for f in files:
            if f["name"].lower().endswith(".xml") and "_htm" in f["name"].lower():
                instance_file = f["name"]
                break

        if not instance_file:
            raise Exception("Instance file not found")

        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{instance_file}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()

        root = ET.fromstring(r.content)
        context_map = {}

        for context in root.findall(f".//{XBRL_NS}context"):
            context_id = context.attrib["id"]
            period = context.find(f"{XBRL_NS}period")
            instant = period.find(f"{XBRL_NS}instant")
            start = period.find(f"{XBRL_NS}startDate")
            end = period.find(f"{XBRL_NS}endDate")

            if instant is not None:
                context_map[context_id] = instant.text
            elif end is not None:
                context_map[context_id] = end.text

        facts = []
        for elem in root.iter():
            context_ref = elem.attrib.get("contextRef")
            if context_ref not in context_map:
                continue

            try:
                value = float(elem.text)
            except:
                continue

            # Extracts base concept name (e.g., 'Assets')
            concept = elem.tag.split("}")[-1]

            facts.append({
                "concept": concept,
                "date": context_map[context_ref],
                "value": value
            })

        return pd.DataFrame(facts)

    # ---------------------------------------------------------
    # Parse presentation, normalize concepts, map to statements
    # ---------------------------------------------------------
    def parse_presentation(self, cik, accession, files):
        pre_file = self.find_file(files, "_pre.xml")

        # Set up a 1-to-many relationship mapping
        statements_concepts = {
            "Balance Sheet": set(),
            "Income Statement": set(),
            "Cash Flow": set()
        }

        if not pre_file:
            return statements_concepts

        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{pre_file}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        for link in root.findall(f".//{LINK_NS}presentationLink"):
            role_uri = link.attrib.get(f"{XLINK_NS}role", "").lower()

            # Ignore disclosures, schedules, and parentheticals
            if any(exclude in role_uri for exclude in ["disclosure", "parenthetical", "details", "policy"]):
                continue

            # Classify the statement
            statement = None
            if "balance" in role_uri or "financialposition" in role_uri:
                statement = "Balance Sheet"
            elif "income" in role_uri or "operations" in role_uri or "earnings" in role_uri:
                statement = "Income Statement"
            elif "cashflow" in role_uri or "cash" in role_uri:
                statement = "Cash Flow"

            if not statement:
                continue

            # Extract concepts associated with this statement
            for loc in link.findall(f".//{LINK_NS}loc"):
                href = loc.attrib.get(f"{XLINK_NS}href")
                if not href:
                    continue

                # Example href: "aapl-20240928_htm.xml#us-gaap_Assets" -> "us-gaap_Assets"
                anchor = href.split("#")[-1]

                # Correct normalization: split by '_' instead of ':'
                # Maxsplit=1 ensures things like 'us-gaap_Property_Plant_Equipment' become 'Property_Plant_Equipment'
                concept = anchor.split("_", 1)[-1] if "_" in anchor else anchor

                statements_concepts[statement].add(concept)

        return statements_concepts

    # ---------------------------------------------------------
    # Distribute facts dynamically to multiple statements
    # ---------------------------------------------------------
    def distribute_statements(self, facts_df, statements_concepts):
        statements = {}

        for stmt_name, concepts in statements_concepts.items():
            if not concepts:
                continue

            # Filter dataframe to only include concepts matching the current statement
            subset = facts_df[facts_df["concept"].isin(concepts)]

            if subset.empty:
                continue

            # Pivot exactly like the All Facts sheet
            pivot = subset.pivot_table(
                index="concept",
                columns="date",
                values="value",
                aggfunc="first"
            )

            # Sort columns descending (newest dates on the left)
            pivot = pivot.sort_index(axis=1, ascending=False)
            statements[stmt_name] = pivot

        return statements

    # ---------------------------------------------------------
    # Export Excel Architecture
    # ---------------------------------------------------------
    def extract_excel_bytes(self, filing_url):
        cik, accession = self.extract_ids_from_url(filing_url)
        files = self.get_filing_index(cik, accession)

        # 1. Get raw facts
        facts_df = self.parse_instance(cik, accession, files)
        
        # 2. Get statement -> concepts map
        statements_concepts = self.parse_presentation(cik, accession, files)
        
        # 3. Build statement dataframes
        statements = self.distribute_statements(facts_df, statements_concepts)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            
            # Write master 'All Facts' sheet
            all_facts = facts_df.pivot_table(
                index="concept",
                columns="date",
                values="value",
                aggfunc="first"
            )
            all_facts = all_facts.sort_index(axis=1, ascending=False)
            all_facts.to_excel(writer, sheet_name="All Facts")

            # Write individual statements dynamically
            for sheet_name in ["Balance Sheet", "Income Statement", "Cash Flow"]:
                if sheet_name in statements:
                    statements[sheet_name].to_excel(writer, sheet_name=sheet_name)

        output.seek(0)
        return output


# ---------------------------------------------------------
# Streamlit function hook
# ---------------------------------------------------------
def parse_xbrl_to_excel(filing_url, output_path=None):
    parser = SECXBRLParser()
    excel_bytes = parser.extract_excel_bytes(filing_url)

    if output_path:
        with open(output_path, "wb") as f:
            f.write(excel_bytes.getvalue())
        return True

    return excel_bytes