"""Neutralise spreadsheet formulas in untrusted text before writing CSVs.

Review text and usernames come from the public. A cell starting with = + - @ (or a
tab/CR) can run as a formula when the CSV is opened in Excel or Sheets, so prefix
those cells with a single quote.
"""
import pandas as pd

FORMULA_START = r"^([=+\-@\t\r])"


def escape_formulas(df, columns):
    df = df.copy()
    for c in columns:
        if c in df.columns:
            df[c] = df[c].where(df[c].isna(), df[c].astype(str).str.replace(FORMULA_START, r"'\1", regex=True))
    return df
