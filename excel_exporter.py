import pandas as pd
from io import BytesIO


class ExcelExporter:

    def export(self, financials):

        facts = financials["facts"]
        statements = financials["statements"]

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            # Raw facts sheet
            facts.pivot_table(
                index="concept",
                columns="date",
                values="value",
                aggfunc="first"
            ).to_excel(writer, sheet_name="All Facts")

            # Statements
            for name, df in statements.items():

                df.to_excel(writer, sheet_name=name)

        output.seek(0)

        return output