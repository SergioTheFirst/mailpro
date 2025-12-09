

from __future__ import annotations
import io
import pandas as pd


def extract_excel(file_bytes: bytes, filename: str) -> str:
    name = filename.lower()

    if not name.endswith((".xls", ".xlsx")):
        return ""

    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            engine="openpyxl",
        )
        return df.to_string(index=False, header=True)
    except Exception:
        return ""
