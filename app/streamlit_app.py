"""Application Radar (Streamlit).

Lancer : uv run streamlit run app/streamlit_app.py
"""

import pandas as pd
import streamlit as st

from radar.config import FILES

st.set_page_config(page_title="Radar", page_icon="📡", layout="wide")
st.title("📡 Radar")
st.caption("Les entreprises qui ont besoin de ton profil, même sans offre publiée.")

path = FILES["entreprises"]
if not path.exists():
    st.info(
        f"Aucune donnée trouvée ({path.relative_to(path.parents[2])}). "
        "Lance le générateur de données factices (T5) ou l'extraction SIRENE (T20)."
    )
    st.stop()

df = pd.read_parquet(path)
st.metric("Entreprises chargées", f"{len(df):,}".replace(",", " "))
if {"lat", "lon"}.issubset(df.columns):
    st.map(df.dropna(subset=["lat", "lon"]).head(5000), latitude="lat", longitude="lon")
st.dataframe(df.head(100))
