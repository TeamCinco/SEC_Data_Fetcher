import pandas as pd
from io import BytesIO
from openpyxl.styles import Font, Alignment, PatternFill, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import FormulaRule


class ExcelExporter:

    def export(self, financials):

        facts = financials["facts"]
        statements = financials["statements"]

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:

            # -------- All Facts Sheet --------

            facts_pivot = facts.pivot_table(
                index="concept",
                columns="date",
                values="value",
                aggfunc="first"
            )

            facts_pivot.to_excel(writer, sheet_name="All Facts")

            ws = writer.book["All Facts"]
            self._beautify_sheet(ws, facts_pivot)


            # -------- Statements --------

            for name, df in statements.items():

                df_clean = df.copy()

                # Optional: indent hierarchy if level column exists
                if "level" in df_clean.columns and "label" in df_clean.columns:
                    df_clean["label"] = df_clean.apply(
                        lambda row: "    " * int(row["level"]) + str(row["label"]),
                        axis=1
                    )

                df_clean.to_excel(writer, sheet_name=name)

                ws = writer.book[name]
                self._beautify_sheet(ws, df_clean)


        output.seek(0)
        return output


    # ---------- Formatting Engine ----------

    def _beautify_sheet(self, ws, df):

        header_font = Font(bold=True, size=12)
        data_font = Font(size=11)

        header_fill = PatternFill(
            start_color="E7EEF7",
            end_color="E7EEF7",
            fill_type="solid"
        )

        zebra_fill = PatternFill(
            start_color="F7F9FC",
            end_color="F7F9FC",
            fill_type="solid"
        )

        currency_format = '#,##0;[Red]-#,##0'
        currency_format_2 = '#,##0.00;[Red]-#,##0.00'

        center_align = Alignment(vertical="center")
        left_align = Alignment(horizontal="left", vertical="center")

        max_row = ws.max_row
        max_col = ws.max_column

        # ----- Header styling -----

        for col in range(1, max_col + 1):

            cell = ws.cell(row=1, column=col)

            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align


        # ----- Data styling -----

        for row in range(2, max_row + 1):

            for col in range(1, max_col + 1):

                cell = ws.cell(row=row, column=col)

                cell.font = data_font

                if col == 1:
                    cell.alignment = left_align
                else:
                    cell.number_format = currency_format
                    cell.alignment = center_align

            # zebra striping
            if row % 2 == 0:
                for col in range(1, max_col + 1):
                    ws.cell(row=row, column=col).fill = zebra_fill


        # ----- Auto column width -----

        for col in range(1, max_col + 1):

            max_length = 0

            col_letter = get_column_letter(col)

            for row in range(1, max_row + 1):

                value = ws.cell(row=row, column=col).value

                if value:
                    max_length = max(max_length, len(str(value)))

            ws.column_dimensions[col_letter].width = min(max_length + 4, 50)


        # ----- Freeze header -----

        ws.freeze_panes = "B2"