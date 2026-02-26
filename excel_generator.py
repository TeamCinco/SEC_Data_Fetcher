from xbrl_parser import SECXBRLParser
from excel_exporter import ExcelExporter


def generate_excel_from_filing(filing_url, output_path=None):

    parser = SECXBRLParser()
    exporter = ExcelExporter()

    financials = parser.extract_statements(filing_url)

    excel_bytes = exporter.export(financials)

    if output_path:
        with open(output_path, "wb") as f:
            f.write(excel_bytes.getvalue())
        return True

    return excel_bytes