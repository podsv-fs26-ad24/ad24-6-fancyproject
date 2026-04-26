import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide",
                   page_title="Conflict Overview")

st.sidebar.success("")

### Data Import
conflicts = pd.read_parquet("./data/clean/conflicts.parquet")
trade = pd.read_parquet("./data/clean/trade.parquet")
alliances = pd.read_parquet("./data/clean/alliances.parquet")

conflict_outcomes = {0:"Ongoing MID", 1:"Victory for State A", 2:"Victory for state B", 3:"Yield by State A", 4:"Yield by State B", 5:"Stalemate",
                     6:"Compromise", 7:"Released (for seizures)", 8:"Unclear", 9:"Missing"}

conflict_roles = {1:"Primary Initiator",2:"Joiner on initiator side", 3:"Primary target", 4:"Joiner on target side"}

### Data Processing

@st.cache_data
def get_conflicts_counts(data):
    
    # 1. Extract unique Conflict_ID and Statecode pairs to avoid double-counting years
    state_a = data[["Conflict_ID", "Statecode_A"]].rename(columns={"Statecode_A": "Statecode"})
    state_b = data[["Conflict_ID", 'Statecode_B']].rename(columns={"Statecode_B": "Statecode"})
    
    # Combine lists and drop duplicates so each country is counted once per conflict
    unique_conflicts = pd.concat([state_a, state_b]).drop_duplicates()
    
    # 2. Count total unique conflicts per country
    counts = unique_conflicts["Statecode"].value_counts().reset_index()
    counts.columns = ["Statecode", "Total_Conflicts"]
    
    # Group again because historical entities (e.g. East/West Germany -> DEU) merge into single modern codes
    final_counts = counts.groupby("Statecode")["Total_Conflicts"].sum().reset_index()
    
    return final_counts


df_conflict_counts = get_conflicts_counts(conflicts)
df_conflict_counts["Log_Conflicts"] = np.log1p(df_conflict_counts["Total_Conflicts"])


### Generate Figure Objects



# 4. Generate the Choropleth map using Plotly Express
fig = px.choropleth(
    df_conflict_counts,
    locations="Statecode",
    color="Log_Conflicts",
    hover_name="Statecode",
    color_continuous_scale="YlGnBu", # You can also try "Reds", "Viridis", or "Turbo"
    labels={"Total_Conflicts": "Conflict Count"},
    hover_data={"Log_Conflicts": False, "Total_Conflicts": True},
)

#manually define colorbar ticks
legend_ticks = [1, 5, 10, 50, 100, 300]
# Calculate where those ticks should physically sit on the log scale
log_ticks = np.log1p(legend_ticks)

# 4. Update the layout to override the colorbar and make it full screen
fig.update_layout(
    coloraxis_colorbar=dict(
        title="Conflict Count",
        tickvals=log_ticks,       # Position ticks at the log scale values
        ticktext=legend_ticks     # But display the real numbers as text!
    ),
    geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'),
    margin={"r":0,"t":0,"l":0,"b":0},
    height=750
)



### Dashboard layout

# Global Map with conflict count for each country
st.title("Geopolitical Conflict & Trade Explorer")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Recorded Conflicts", f"{len(conflicts["Conflict_ID"].unique())}")
with col2:
    year_min, year_max = conflicts["Start_Year"].min(), conflicts["End_Year"].max()
    st.metric("Year Range", f"{year_min} - {year_max}")
with col3:
    st.metric("Number of Countries involved in conflicts", f"{len(conflicts["Statecode_A"].unique())}")

with st.container():
    st.title("Global Conflict Involvement Map")
    st.markdown("This map shows the total number of unique conflicts each country has been involved in.")
    # Render Plotly map to Streamlit
    st.plotly_chart(fig, use_container_width=True)


with st.container():
    # Table to filter and search specific conflicts
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



with st.container():
    selected_conflict = st.selectbox(
    label="Which Conflict would you like to analyze in detail",
    options=conflicts["Conflict_ID"].unique()
    )
    with st.container(border=True):
        col4, col5 = st.columns(2)
        with col4:
            st.text(f"Duration: {conflicts["Start_Year"][selected_conflict]} - {conflicts["End_Year"][selected_conflict]}")
            st.text(f"Fatality Level: {conflicts["Fatality_Level"][selected_conflict]}")
            st.text(f"Conflict Outcome: {conflict_outcomes[conflicts["Outcome"][selected_conflict]]}")
        with col5:
            st.text(f"Conflict Outcome: {conflict_outcomes[conflicts["Outcome"][selected_conflict]]}")

    col6, col7 = st.columns(2)
    with col6:
        with st.container(border=True):
            st.markdown("**Side A**")
            st.text(f"State: {conflicts["Statecode_A"][selected_conflict]}")
            st.text(f"Role: {conflict_roles[conflicts["Role_A"][selected_conflict]]}")
            st.text(f"Conflict Severity: {conflicts["Severity_A"][selected_conflict]}")
    
    with col7:
        with st.container(border=True):
            st.markdown("**Side B**")
            st.text(f"State: {conflicts["Statecode_B"][selected_conflict]}")
            st.text(f"Role: {conflict_roles[conflicts["Role_B"][selected_conflict]]}")
            st.text(f"Conflict Severity: {conflicts["Severity_B"][selected_conflict]}")

