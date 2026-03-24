from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from extractor import extract_text, fixtures_to_rows, infer_year, parse_pdf


st.set_page_config(page_title="Garrycastle Fixtures Extractor", layout="wide")
st.title("Garrycastle Fixtures Extractor")
st.caption("Upload a fixtures PDF, extract only the club's games, and download script-friendly CSV/JSON output.")


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    preferred_order = [
        "date_iso",
        "weekday",
        "throw_in",
        "team",
        "opponent",
        "is_home",
        "home_team",
        "away_team",
        "competition",
        "age_group",
        "sport",
        "division",
        "venue",
        "referee",
        "source_pdf",
        "original_line",
    ]
    existing = [col for col in preferred_order if col in df.columns]
    remaining = [col for col in df.columns if col not in existing]
    return df[existing + remaining]



def weekend_slice(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "date_iso" not in df.columns:
        return df

    dates = pd.to_datetime(df["date_iso"], errors="coerce")
    today = pd.Timestamp.now().normalize()

    days_until_saturday = (5 - today.weekday()) % 7
    saturday = today + pd.Timedelta(days=days_until_saturday)
    sunday = saturday + pd.Timedelta(days=1)

    mask = dates.isin([saturday, sunday])
    return df.loc[mask].copy()


uploaded_file = st.file_uploader("Upload fixtures PDF", type=["pdf"])
team_name = st.text_input("Club name", value="Garrycastle")
year_value = st.number_input(
    "Fixture year",
    min_value=2020,
    max_value=2100,
    value=datetime.now().year,
    step=1,
    help="Used when the PDF does not clearly include the year.",
)
use_inferred_year = st.checkbox("Try to infer the year from the PDF first", value=True)
show_weekend_only = st.checkbox("Show this weekend's games only", value=False)

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_path = Path(tmp.name)

    try:
        text = extract_text(pdf_path)
        year = infer_year(text, fallback=int(year_value)) if use_inferred_year else int(year_value)
        fixtures = parse_pdf(pdf_path=pdf_path, team_name=team_name, year=year)
        rows = fixtures_to_rows(fixtures)
        df = to_dataframe(rows)

        st.success(f"Found {len(df)} fixture(s) for {team_name} using year {year}.")

        if df.empty:
            st.warning("No matching fixtures were found in this PDF.")
        else:
            display_df = weekend_slice(df) if show_weekend_only else df

            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Total fixtures", len(df))
            metric_col2.metric("Home games", int(df["is_home"].sum()))
            metric_col3.metric("Away games", int((~df["is_home"]).sum()))

            st.subheader("Fixtures")
            st.dataframe(display_df, use_container_width=True)

            csv_data = df.to_csv(index=False).encode("utf-8")
            json_data = json.dumps(
                {
                    "team": team_name,
                    "fixture_count": len(rows),
                    "fixtures": rows,
                },
                indent=2,
                ensure_ascii=False,
            )

            download_name = f"{team_name.lower().replace(' ', '_')}_fixtures"

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name=f"{download_name}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with col2:
                st.download_button(
                    "Download JSON",
                    data=json_data,
                    file_name=f"{download_name}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            with st.expander("Why this output format is useful for later weekend queries"):
                st.markdown(
                    "- `date_iso` is stored as `YYYY-MM-DD` for easy filtering in Python.\n"
                    "- `throw_in` is kept in `HH:MM` 24-hour format.\n"
                    "- `is_home`, `home_team`, and `away_team` make home/away checks simple.\n"
                    "- `original_line` is kept for debugging awkward PDF rows."
                )
    finally:
        try:
            pdf_path.unlink(missing_ok=True)
        except Exception:
            pass
else:
    st.info("Upload a PDF to begin.")
