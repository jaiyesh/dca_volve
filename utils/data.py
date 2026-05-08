from pathlib import Path
import pandas as pd
import streamlit as st

# Absolute path — required for HuggingFace Spaces Docker environment
_CSV_PATH = Path(__file__).parent.parent / "Final PF-12 and Injection.csv"

# Key columns used by the app
DISPLAY_COLUMNS = [
    "DATEPRD", "BORE_OIL_VOL", "BORE_GAS_VOL",
    "BORE_WAT_VOL", "AVG_WHP_P", "AVG_CHOKE_SIZE_P", "ON_STREAM_HRS",
]


@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load and clean the Volve production CSV.
    - Parses DATEPRD with explicit format='%d-%b-%y' (e.g. 01-Sep-07)
    - Filters to ON_STREAM_HRS > 0 (removes 404 shut-in rows)
    - Adds WATER_CUT derived column
    - Sorts by DATEPRD ascending
    Returns a DataFrame with 2901 producing-day rows.
    """
    df = pd.read_csv(_CSV_PATH)
    df["DATEPRD"] = pd.to_datetime(df["DATEPRD"], format="%d-%b-%y")

    # Sanity check date range (Volve dataset is Sept 2007 – Sept 2016)
    assert df["DATEPRD"].min().year == 2007, "Date parse error: min year != 2007"
    assert df["DATEPRD"].max().year == 2016, "Date parse error: max year != 2016"

    df = df.sort_values("DATEPRD").reset_index(drop=True)
    # Remove shut-in days — ON_STREAM_HRS == 0 rows corrupt DCA fitting
    df = df[df["ON_STREAM_HRS"] > 0].copy()

    # Derived column: water cut (fraction), bounded [0, 1]
    total_liquid = df["BORE_OIL_VOL"] + df["BORE_WAT_VOL"]
    df["WATER_CUT"] = df["BORE_WAT_VOL"] / total_liquid.replace(0, float("nan"))
    df["WATER_CUT"] = df["WATER_CUT"].clip(0.0, 1.0)

    return df.reset_index(drop=True)


def filter_by_date(df: pd.DataFrame, start, end) -> pd.DataFrame:
    """
    Return rows where DATEPRD is within [start, end] inclusive.
    start and end may be datetime.date or pd.Timestamp objects.
    Does NOT mutate the input DataFrame (no inplace=True).
    """
    mask = (df["DATEPRD"] >= pd.Timestamp(start)) & (df["DATEPRD"] <= pd.Timestamp(end))
    return df.loc[mask].copy()


def get_sidebar_kpis(df: pd.DataFrame) -> dict:
    """
    Return dataset-level KPIs for the persistent sidebar display.
    All pages call this to populate sidebar info cards.
    Returns dict with: well_name, date_start, date_end, total_oil_mmsm3, peak_rate, peak_date, on_stream_days
    """
    total_oil = df["BORE_OIL_VOL"].sum()  # Sm³
    peak_idx = df["BORE_OIL_VOL"].idxmax()
    return {
        "well_name": "15/9-F-12",
        "date_start": df["DATEPRD"].min().strftime("%b %Y"),
        "date_end": df["DATEPRD"].max().strftime("%b %Y"),
        "total_oil_mmsm3": round(total_oil / 1_000_000, 3),
        "peak_rate": int(df.loc[peak_idx, "BORE_OIL_VOL"]),
        "peak_date": df.loc[peak_idx, "DATEPRD"].strftime("%d %b %Y"),
        "on_stream_days": len(df),
    }
