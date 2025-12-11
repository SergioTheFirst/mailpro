from __future__ import annotations

import io


def _load_pandas():
    try:
        import pandas as pd  # type: ignore

        return pd
    except Exception:
        return None


def extract_excel(file_bytes: bytes, filename: str) -> str:
    name = (filename or "").lower()

    if not name.endswith((".xls", ".xlsx")):
        return ""

    pandas = _load_pandas()
    if pandas is None:
        return ""

    try:
        df = pandas.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        return df.to_string(index=False, header=True)
    except Exception:
        return ""


extract_excel_text = extract_excel
