from __future__ import annotations

import tempfile
import pandas as pd
import streamlit as st

from extractor import extract_text, fixtures_to_rows, infer_year

st.set_page_config(page_title="GAA Fixtures Extractor", layout="wide")

st.title("GAA Fixtures Extractor")
st.write("Upload a fixtures PDF to extract your club's games.")

uploaded_file = st.file_uploader("Upload fixtures PDF", type=["pdf"])
team_name = st.text_input("Club name", value="Garrycastle")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_path = tmp.name

    text = extract_text(pdf_path)
    year = infer_year(text)
    fixtures = fixtures_to_rows(text, team_name=team_name, year=year)

    if not fixtures:
        st.warning(f"No fixtures found for {team_name}.")
    else:
        df = pd.DataFrame(fixtures)
        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(index=False).encode("utf-8")
        json_data = df.to_json(orient="records", indent=2)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "Download CSV",
                data=csv_data,
                file_name=f"{team_name.lower()}_fixtures.csv",
                mime="text/csv",
            )

        with col2:
            st.download_button(
                "Download JSON",
                data=json_data,
                file_name=f"{team_name.lower()}_fixtures.json",
                mime="application/json",
            )
