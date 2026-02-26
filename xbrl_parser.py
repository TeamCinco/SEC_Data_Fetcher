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
IXBRL_NS = "{http://www.xbrl.org/2013/inlineXBRL}" # recently added this line to deal with the change from xbrl to IXBRL in some filings
# ---------------------------------------------------------
# Role URI classification rules
# ---------------------------------------------------------
# Each statement has:
#   - "include": keywords that MUST appear in the role URI
#   - "exclude": keywords that disqualify the role even if include matches
#
# Order matters: more specific checks run first to avoid
# "cash" in cash flow matching a cash disclosure role.
# ---------------------------------------------------------

STATEMENT_RULES = [
    {
        "name": "Balance Sheet",
        "include": [
            "balancesheet", "balance_sheet",
            "financialposition", "financial_position",
            "financialcondition", "financial_condition",
            "consolidatedbalance", "statementoffinancialposition",
        ],
        "exclude": ["parenthetical", "detail", "policy", "note"],
    },
    {
        "name": "Income Statement",
        "include": [
            "incomestatement", "income_statement",
            "statementsofincome", "statementsofoperations",
            "statementofincome", "statementofoperations",
            "statementofearnings", "statementsofearnings",
            "consolidatedoperations", "consolidatedincome",
            "consolidatedearnings",
            "profitandloss", "profit_and_loss",
            "resultsofoperations",
            "revenueexpense", "revenuecostsandexpenses",
        ],
        "exclude": ["parenthetical", "comprehensive", "detail", "policy", "note"],
    },
    {
        "name": "Comprehensive Income",
        "include": [
            "comprehensiveincome", "comprehensive_income",
            "othercomprehensive",
        ],
        "exclude": ["parenthetical", "detail", "policy", "note"],
    },
    {
        "name": "Cash Flow",
        "include": [
            "cashflow", "cash_flow",
            "statementofcashflows", "statementsofcashflows",
            "consolidatedcashflows", "consolidatedstatementsofcash",
        ],
        "exclude": ["parenthetical", "detail", "policy", "note",
                     "supplement", "disclosure"],
    },
    {
        "name": "Stockholders Equity",
        "include": [
            "stockholdersequity", "stockholders_equity",
            "shareholdersequity", "shareholders_equity",
            "changesinequity", "changes_in_equity",
            "statementofequity", "statementsofequity",
        ],
        "exclude": ["parenthetical", "detail", "policy", "note"],
    },
]


def classify_role(role_uri):
    """
    Classify a presentation/calculation role URI into a statement name.
    Returns the statement name or None if unclassified.
    """
    # Normalize: lowercase, strip spaces, collapse for keyword matching
    normalized = role_uri.lower().replace(" ", "").replace("-", "")

    for rule in STATEMENT_RULES:
        # Check excludes first
        if any(ex in normalized for ex in rule["exclude"]):
            # But only skip if an include keyword also matches —
            # otherwise this role wasn't going to match anyway
            has_include = any(inc in normalized for inc in rule["include"])
            if has_include:
                continue  # Excluded: skip this rule
            # No include match, so exclusion is irrelevant — fall through

        # Check includes
        if any(inc in normalized for inc in rule["include"]):
            return rule["name"]

    return None


def extract_concept_from_href(href):
    """
    Extract the concept name from a linkbase loc href.
    
    Examples:
        "aapl-20240928_htm.xml#us-gaap_Assets" -> "Assets"
        "aapl-20240928_htm.xml#aapl_MacRevenue" -> "MacRevenue"
        "aapl-20240928_htm.xml#us-gaap_PaymentsForRepurchaseOfCommonStock" 
            -> "PaymentsForRepurchaseOfCommonStock"
    """
    anchor = href.split("#")[-1]
    # Split on first underscore to strip namespace prefix (us-gaap_, aapl_, etc.)
    # maxsplit=1 preserves underscores within the concept name itself
    return anchor.split("_", 1)[-1] if "_" in anchor else anchor


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
    # Parse ALL facts with context dates (Consolidated Only)
    # ---------------------------------------------------------
# ---------------------------------------------------------
    # Parse ALL facts with context dates (Consolidated Only)
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

        # 1. Parse Contexts (Works for both standard and iXBRL)
        for context in root.findall(f".//{XBRL_NS}context"):
            # Skip dimensional/segment contexts to get consolidated-only facts
            entity = context.find(f"{XBRL_NS}entity")
            if entity is not None and entity.find(f"{XBRL_NS}segment") is not None:
                continue

            context_id = context.attrib["id"]
            period = context.find(f"{XBRL_NS}period")
            instant = period.find(f"{XBRL_NS}instant")
            start = period.find(f"{XBRL_NS}startDate")
            end = period.find(f"{XBRL_NS}endDate")

            if instant is not None:
                context_map[context_id] = instant.text
            elif end is not None:
                context_map[context_id] = end.text

        # 2. Extract Facts
        facts = []
        for elem in root.iter():
            context_ref = elem.attrib.get("contextRef")
            if not context_ref or context_ref not in context_map:
                continue
            
            try:
                # Handle Inline XBRL (iXBRL)
                if elem.tag in [f"{IXBRL_NS}nonFraction", f"{IXBRL_NS}nonNumeric"]:
                    raw_concept = elem.attrib.get("name", "")
                    if not raw_concept:
                        continue
                        
                    # Extract concept name (e.g., "us-gaap:Assets" -> "Assets")
                    concept = raw_concept.split(":")[-1] if ":" in raw_concept else raw_concept
                    
                    # iXBRL uses a 'sign' attribute for negative numbers
                    sign = -1 if elem.attrib.get("sign") == "-" else 1
                    
                    # Extract text, remove commas, handle empty strings
                    text_val = "".join(elem.itertext()).strip().replace(",", "")
                    if not text_val:
                        continue
                        
                    value = float(text_val) * sign
                
                # Handle Standard XBRL
                elif "}" in elem.tag and elem.tag.split("}")[0] + "}" not in [IXBRL_NS, LINK_NS, XLINK_NS]:
                    concept = elem.tag.split("}")[-1]
                    value = float(elem.text)
                else:
                    continue
                    
                facts.append({
                    "concept": concept,
                    "date": context_map[context_ref],
                    "value": value
                })
            except Exception:
                # Silently skip non-numeric strings or unparseable text
                continue

        return pd.DataFrame(facts)

    # ---------------------------------------------------------
    # Parse presentation linkbase -> statement:concepts map
    # ---------------------------------------------------------
    def parse_presentation(self, cik, accession, files):

        pre_file = self.find_file(files, "_pre.xml")

        if not pre_file:
            return {}

        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{pre_file}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()

        root = ET.fromstring(r.content)

        statements = {}

        for link in root.findall(f".//{LINK_NS}presentationLink"):

            role_uri = link.attrib.get(f"{XLINK_NS}role", "")
            statement_name = classify_role(role_uri)

            if not statement_name:
                continue

            label_map = {}
            arcs = []
            children = {}

            # build label map
            for loc in link.findall(f"{LINK_NS}loc"):

                label = loc.attrib.get(f"{XLINK_NS}label")
                href = loc.attrib.get(f"{XLINK_NS}href")

                if label and href:
                    label_map[label] = extract_concept_from_href(href)

            # build tree structure
            for arc in link.findall(f"{LINK_NS}presentationArc"):

                parent_label = arc.attrib.get(f"{XLINK_NS}from")
                child_label = arc.attrib.get(f"{XLINK_NS}to")

                order = float(arc.attrib.get("order", "0"))

                parent = label_map.get(parent_label)
                child = label_map.get(child_label)

                if parent and child:

                    if parent not in children:
                        children[parent] = []

                    children[parent].append({
                        "concept": child,
                        "order": order,
                        "parent": parent
                    })

            # recursive traversal
            ordered = []

            def walk(parent):

                if parent not in children:
                    return

                nodes = sorted(children[parent], key=lambda x: x["order"])

                for node in nodes:

                    ordered.append(node)

                    walk(node["concept"])

            # find root nodes
            all_children = set()
            for v in children.values():
                for node in v:
                    all_children.add(node["concept"])

            roots = [p for p in children.keys() if p not in all_children]

            for root_node in roots:
                walk(root_node)

            statements[statement_name] = ordered

        return statements

    # ---------------------------------------------------------
    # Parse calculation linkbase as secondary classifier
    # ---------------------------------------------------------
    def parse_calculation(self, cik, accession, files):
        """
        The calculation linkbase (_cal.xml) defines mathematical rollup
        relationships (e.g., Assets = CurrentAssets + NoncurrentAssets).
        Each calculationLink has a role URI that maps to a statement.
        
        This serves as a backup classifier — any concept found here
        that wasn't in the presentation linkbase gets added.
        """
        cal_file = self.find_file(files, "_cal.xml")
        statements_concepts = {}

        if not cal_file:
            return statements_concepts

        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{cal_file}"
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        root = ET.fromstring(r.content)

        for link in root.findall(f".//{LINK_NS}calculationLink"):
            role_uri = link.attrib.get(f"{XLINK_NS}role", "")
            statement = classify_role(role_uri)
            if not statement:
                continue

            if statement not in statements_concepts:
                statements_concepts[statement] = set()

            for loc in link.findall(f".//{LINK_NS}loc"):
                href = loc.attrib.get(f"{XLINK_NS}href", "")
                if not href:
                    continue
                concept = extract_concept_from_href(href)
                statements_concepts[statement].add(concept)

        return statements_concepts

    # ---------------------------------------------------------
    # Merge presentation + calculation concept maps
    # ---------------------------------------------------------
    def merge_concept_maps(self, pre_map, cal_map):

        merged = {}

        all_statements = set(pre_map.keys()).union(cal_map.keys())

        for stmt in all_statements:

            pre_arcs = pre_map.get(stmt, [])
            cal_concepts = cal_map.get(stmt, set())

            # extract concepts already in presentation
            pre_concept_names = set()

            for arc in pre_arcs:
                pre_concept_names.add(arc["concept"])

            # add missing concepts from calculation linkbase
            order_counter = len(pre_arcs) + 1

            for concept in cal_concepts:

                if concept not in pre_concept_names:

                    pre_arcs.append({
                        "concept": concept,
                        "parent": None,
                        "order": order_counter
                    })

                    order_counter += 1

            merged[stmt] = pre_arcs

        return merged

    # ---------------------------------------------------------
    # Distribute facts to statements
    # ---------------------------------------------------------
    def distribute_statements(self, facts_df, statements_structure):

        statements = {}

        for stmt_name, arcs in statements_structure.items():

            ordered_concepts = [arc["concept"] for arc in arcs]

            subset = facts_df[facts_df["concept"].isin(ordered_concepts)]

            if subset.empty:
                continue

            pivot = subset.pivot_table(
                index="concept",
                columns="date",
                values="value",
                aggfunc="first"
            )

            existing = [c for c in ordered_concepts if c in pivot.index]

            pivot = pivot.reindex(existing)

            pivot = pivot.sort_index(axis=1, ascending=False)

            statements[stmt_name] = pivot

        return statements
    # ---------------------------------------------------------
    # Export Excel
    # ---------------------------------------------------------
    def extract_excel_bytes(self, filing_url):
        cik, accession = self.extract_ids_from_url(filing_url)
        files = self.get_filing_index(cik, accession)

        # 1. Get raw consolidated facts
        facts_df = self.parse_instance(cik, accession, files)

        # 2. Get statement -> concepts from BOTH linkbases
        pre_map = self.parse_presentation(cik, accession, files)
        cal_map = self.parse_calculation(cik, accession, files)
        statements_concepts = self.merge_concept_maps(pre_map, cal_map)

        # 3. Build statement DataFrames
        statements = self.distribute_statements(facts_df, statements_concepts)

        # 4. Write Excel
        output = BytesIO()

        # Define sheet order (only include sheets that have data)
        sheet_order = [
            "Balance Sheet",
            "Income Statement",
            "Comprehensive Income",
            "Cash Flow",
            "Stockholders Equity",
        ]

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # Master sheet with everything
            all_facts = facts_df.pivot_table(
                index="concept",
                columns="date",
                values="value",
                aggfunc="first"
            )
            all_facts = all_facts.sort_index(axis=1, ascending=False)
            all_facts.to_excel(writer, sheet_name="All Facts")

            # Individual statement sheets
            for sheet_name in sheet_order:
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