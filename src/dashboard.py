import pandas as pd
import streamlit as st

conflicts = pd.read_parquet("./data/clean/conflicts.parquet")
trade = pd.read_parquet("./data/clean/trade.parquet")
alliances = pd.read_parquet("./data/clean/alliances.parquet")


st.title("Geopolitical Conflict & Trade Explorer")

st.write("Hello! This is my dashboard.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Number of Conflicts", f"{len(conflicts["Conflict_ID"].unique()):,}")
with col2:
    year_min, year_max = conflicts["Start_Year"].min(), conflicts["End_Year"].max()
    st.metric("Year Range", f"{year_min} - {year_max}")
with col3:
    st.metric("Number of Countries involved in conflicts", f"{len(conflicts["Statecode_A"].unique()):,}")

st.dataframe(conflicts)


selected_countries = st.multiselect(
    "Filter involved Countries",
    options=conflicts["Statecode_A"].unique(),
    default="USA"
)

min_year, max_year = st.slider(
    "Value range",
    min_value=int(conflicts["Year"].min()),
    max_value=int(conflicts["Year"].max()),
    value=(int(conflicts["Year"].min()), int(conflicts["Year"].max()))
)

filtered_df = conflicts[
    conflicts["Statecode_A"].isin(selected_countries) &
    conflicts["Year"].between(min_year, max_year)
]

st.dataframe(filtered_df, use_container_width=True)