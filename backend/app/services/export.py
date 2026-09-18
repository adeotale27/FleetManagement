import csv
import io
from typing import Any
from openpyxl import Workbook


class ExportService:
    def csv(self, rows: list[dict[str, Any]]) -> str:
        buf = io.StringIO()
        if rows:
            writer = csv.DictWriter(buf, fieldnames=sorted(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return buf.getvalue()

    def xlsx(self, rows: list[dict[str, Any]]) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "Report"
        if not rows:
            bio = io.BytesIO()
            wb.save(bio)
            return bio.getvalue()
        keys = sorted(rows[0].keys())
        ws.append(keys)
        for row in rows:
            ws.append([str(row.get(k, "")) for k in keys])
        bio = io.BytesIO()
        wb.save(bio)
        return bio.getvalue()
