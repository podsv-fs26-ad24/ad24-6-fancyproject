import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# --- Page Configuration ---
# Sets the browser tab title and uses the full browser width for the layout
st.set_page_config(layout="wide",
                   page_title="Conflict Overview")


# --- Data Import ---
# Load pre-cleaned parquet files for each domain
conflicts = pd.read_parquet("./data/clean/conflicts.parquet")
trade = pd.read_parquet("./data/clean/trade.parquet")
alliances = pd.read_parquet("./data/clean/alliances.parquet")
milex = pd.read_parquet("./data/clean/milex.parquet")


# --- Global Variables ---
# Shared font size used across all chart annotations for visual consistency
vis_annot_size = 18


# =============================================================================
# Data Processing
# =============================================================================

@st.cache_data
def get_conflicts_counts(data: pd.DataFrame):
    """Return df with conflict counts for each country"""
    # Extract unique Conflict_ID and Statecode pairs to avoid double-counting years
    state_a = data[["Conflict_ID", "Statecode_A"]].rename(columns={"Statecode_A": "Statecode"})
    state_b = data[["Conflict_ID", 'Statecode_B']].rename(columns={"Statecode_B": "Statecode"})
    
    # Combine both sides and drop duplicates so each country is counted once per conflict
    unique_conflicts = pd.concat([state_a, state_b]).drop_duplicates()
    
    # Count total unique conflicts per country
    counts = unique_conflicts["Statecode"].value_counts().reset_index()
    counts.columns = ["Statecode", "Total_Conflicts"]
    
    # Aggregate by Statecode to merge historical entities
    # (e.g. East/West Germany both map to DEU and their counts are summed)
    final_counts = counts.groupby("Statecode")["Total_Conflicts"].sum().reset_index()
    
    return final_counts


def get_country_alliances(country_code: str, year: int, data: pd.DataFrame) -> pd.DataFrame:
    """Return all alliance partners a country had in a given year, with alliance types."""

    # Match rows where the country appears on either side and the alliance was active in that year
    mask = (
        ((data["Statecode_A"] == country_code) | (data["Statecode_B"] == country_code)) &
        (data["Start_Year"] <= year) &
        (data["End_Year"]   >= year)
    )
    active = data[mask].copy()

    # If no alliances found for this country/year, return an empty DataFrame
    if active.empty:
        return pd.DataFrame()

    # Derive the partner country (the side that is not the selected country)
    active["Partner_Code"] = active.apply(
        lambda r: r["Statecode_B"] if r["Statecode_A"] == country_code else r["Statecode_A"],
        axis=1
    )
    active["Partner_Name"] = active.apply(
        lambda r: r["State_B"] if r["Statecode_A"] == country_code else r["State_A"],
        axis=1
    )

    # Map one-hot encoded alliance type columns to human-readable labels
    type_flags = {
        "Defense":      "Defense Pact",
        "Neutrality":   "Neutrality Pact",
        "Nonaggression":"Non-Aggression Pact",
        "Entente":      "Entente",
    }
    def alliance_types(row):
        # Collect all active alliance types for this row and join them into one string
        return ", ".join(label for col, label in type_flags.items() if row.get(col, 0) == 1)

    active["Alliance Type"] = active.apply(alliance_types, axis=1)
    # Replace empty strings (no matched type) with a readable fallback
    active["Alliance Type"] = active["Alliance Type"].replace("", "Unspecified")

    # Return a clean, renamed subset of columns
    return active[["Partner_Code", "Partner_Name", "Alliance Type", "Start_Year", "End_Year"]] \
               .drop_duplicates() \
               .reset_index(drop=True) \
               .rename(columns={
                   "Partner_Code": "Country Code",
                   "Partner_Name": "Partner Country",
                   "Start_Year":   "Since",
                   "End_Year":     "Until",
               })


def get_global_conflict_count(data: pd.DataFrame):
    """Return df with unique conflict count per year."""
    # Drop duplicate Conflict_ID/Year pairs so each conflict is counted once per year
    unique_conflicts = data.drop_duplicates(subset=["Conflict_ID", "Year"])
    # Count rows per year and name the count column ccount
    yearly_conflicts = unique_conflicts.groupby("Year").size().reset_index(name="ccount")
    return yearly_conflicts


# --- Precompute Global Conflict Counts ---
# Used by the choropleth map; computed once at startup
df_conflict_counts = get_conflicts_counts(conflicts)
# Apply log1p transform to compress the wide range of conflict counts for better color mapping
df_conflict_counts["Log_Conflicts"] = np.log1p(df_conflict_counts["Total_Conflicts"])


# =============================================================================
# Dashboard Layout
# =============================================================================

st.title("Geopolitical Conflict & Trade Explorer")
st.subheader("Military Interstate Disputes")

# --- Summary Metrics ---
# Top-level KPIs displayed as metric cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Recorded Conflicts", f"{len(conflicts["Conflict_ID"].unique())}")
with col2:
    year_min, year_max = conflicts["Start_Year"].min(), conflicts["End_Year"].max()
    st.metric("Year Range", f"{year_min} - {year_max}")
with col3:
    st.metric("Number of Countries Involved in Conflicts", f"{len(conflicts["Statecode_A"].unique())}")


# --- Global Conflict Involvement Choropleth Map ---
with st.container(border=True):
    st.markdown("#### Global Conflict Involvement Map")
    st.markdown("This map shows the total number of unique conflicts each country has been involved in.")

    # Build choropleth using the log-transformed conflict count for color scaling
    fig = px.choropleth(
        df_conflict_counts,
        locations="Statecode",
        color="Log_Conflicts",
        hover_name="Statecode",
        color_continuous_scale="YlGnBu", 
        labels={"Total_Conflicts": "Conflict Count"},
        # Show raw count on hover, hide the log value
        hover_data={"Log_Conflicts": False, "Total_Conflicts": True},
    )

    # Define readable colorbar ticks using the original (non-log) scale
    legend_ticks = [1, 10, 100, 300]
    # Map those values back to log1p positions so ticks align correctly on the color axis
    log_ticks = np.log1p(legend_ticks)

    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Conflict Count",
            title_font=dict(color="black", size=vis_annot_size),
            tickvals=log_ticks,       # Physical position on the log scale
            ticktext=legend_ticks,    # Labels showing the actual conflict counts
            tickfont=dict(color="black")
        ),
        geo=dict(showframe=False, showcoastlines=True, projection_type='equirectangular'),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=750
    )
    st.plotly_chart(fig, use_container_width=True)


    # --- Global Conflicts Per Year Line Chart ---
    st.markdown("#### Global Ongoing Conflicts Over Time")
    global_yearly_conflicts = get_global_conflict_count(conflicts)

    fig_glob_conflicts = px.line(
        global_yearly_conflicts,
        x="Year",
        y="ccount",
        labels={"Year":"Year", "ccount": "Number of Conflicts"},
        color_discrete_sequence=["#225ea8"]  # Static navy blue line
    )
    
    fig_glob_conflicts.update_layout(
        height=550,
        font=dict(size=vis_annot_size),
        xaxis=dict(
            title_font=dict(color="black", size=vis_annot_size),   
            tickfont=dict(color="black", size=vis_annot_size)
        ),
        yaxis=dict(
            title_font=dict(color="black", size=vis_annot_size),   
            tickfont=dict(color="black", size=vis_annot_size)
        ),
        legend_font=dict(color="black"),        
        legend_title_font=dict(color="black")
    )

    st.plotly_chart(fig_glob_conflicts, use_container_width=True)


# =============================================================================
# Conflict Browser
# =============================================================================

with st.container(border=True):
    st.markdown("### Conflict Browser")
    st.markdown("Use the Filters to search for specific conflicts in the conflict dataset.")

    # --- Filter Widgets ---
    selected_countries = st.multiselect(
        "Filter involved Countries",
        options=conflicts["Statecode_A"].unique(),
        default="USA"
    )

    min_year, max_year = st.slider(
        "Year",
        min_value=int(conflicts["Year"].min()),
        max_value=int(conflicts["Year"].max()),
        value=(int(conflicts["Year"].min()), int(conflicts["Year"].max()))
    )

    selected_hostilities = st.multiselect(
        "Filter Hostility",
        options=conflicts["Hostility"].unique(),
        default="Use of Force"
    )

    # Apply all three filters simultaneously
    filtered_df = conflicts[
        conflicts["Statecode_A"].isin(selected_countries) &
        conflicts["Year"].between(min_year, max_year) &
        conflicts["Hostility"].isin(selected_hostilities)
    ]
    
    # Display the filtered result as an interactive table with human-readable column names
    st.dataframe(filtered_df,
                 use_container_width=True,
                 hide_index=True,
                 column_config={
                    "Conflict_ID": st.column_config.NumberColumn(
                    label="Conflict ID"
                ),
                "Start_Year": st.column_config.NumberColumn(
                    label="Start Year"
                ),
                "End_Year": st.column_config.NumberColumn(
                    label="End Year"
                ),
                    "Statecode_A": st.column_config.TextColumn(
                    label="State A",
                    help="The 3-letter iso3 country code for the on Side A."
                ),
                    "Statecode_B": st.column_config.TextColumn(
                    label="State B",
                    help="The 3-letter iso3 country code for the on Side B."
                ),
                    "Fatality_Level": st.column_config.NumberColumn(
                    label="Fatality Level",
                    help="""Severity of the conflict measured by estimated casualties. Scale:  
                    0: None  
                    1: 1-25  
                    2: 26-100  
                    3: 101-250  
                    4: 251-500  
                    5: 501-999  
                    6: 1000+"""
                ),
                "Role_A": st.column_config.TextColumn(
                    label="Role A"
                ),
                "Role_B": st.column_config.TextColumn(
                    label="Role A"
                ),
                "Severity": st.column_config.TextColumn(
                    label="Severity",
                    help="""Highest severity score committed by any state  
                    ranges from 0 - 100"""
                ),
                "Severity_A": st.column_config.TextColumn(
                    label="Severity A",
                    help="Highest severity score committed by state A"
                ),
                "Severity_B": st.column_config.TextColumn(
                    label="Severity B",
                    help="Highest severity score committed by state B"
                )
            })


# =============================================================================
# Conflict Analyzer
# =============================================================================

with st.container(border=True):
    st.markdown("### Conflict Analyzer")
    st.markdown("Choose a conflict you want to analyze in depth by entering a Conflict_ID from the conflict browser above.")

    selected_conflict = st.selectbox(
        label="Which Conflict would you like to analyze in detail?",
        options=conflicts["Conflict_ID"].unique()
    )

    # Isolate all rows belonging to the selected conflict
    conflict_data = conflicts[conflicts["Conflict_ID"] == selected_conflict]
    
    # Calculate the maximum fatality level across ALL years of the conflict
    max_fatality = conflict_data["Fatality_Level"].max()
    
    # Use the last recorded year's row for end-of-conflict summary stats
    row = conflict_data.sort_values(by="Year").iloc[-1]


    # Build a minimal DataFrame with just the two involved countries for the choropleth
    df_selected_map = pd.DataFrame({
        "Statecode": [row['Statecode_A'], row['Statecode_B']],
        "Side": ["State A", "State B"]
    })

    # --- Conflict Location Map ---
    # Highlights only the two involved countries; all others rendered in lightgray
    fig_conflict_map = px.choropleth(
        df_selected_map,
        locations="Statecode",
        color="Side",
        color_discrete_map={"State A": "#225ea8", "State B": "#7fcdbb"}, 
        hover_name="Statecode"
    )

    fig_conflict_map.update_layout(
        geo=dict(
            showframe=False, 
            showcoastlines=True, 
            projection_type='equirectangular',
            showland=True,
            landcolor="lightgray"  # Non-involved countries rendered in gray for contrast
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=400,
        font=dict(size=vis_annot_size),
        legend_title_text="Involved Parties",
        legend_font=dict(color="black", size=vis_annot_size),        
        legend_title_font=dict(color="black", size=vis_annot_size)
    )

    st.plotly_chart(fig_conflict_map, use_container_width=True)


    # --- Conflict Summary Stats ---
    with st.container(border=True):
        st.subheader(f"Stats for Conflict {row['Conflict_ID']}")
        col4, col5 = st.columns(2)
        with col4:
            st.write(f"**Duration:** {row["Start_Year"]} - {row["End_Year"]}")
            st.write(f"**Fatality Level (Max):** {max_fatality}")
            
        with col5:
            st.write(f"**Conflict Outcome:** {row["Outcome"]}")
            st.write(f"**Highest Severity:** {row["Severity"]}")

    # --- Per-Country Detail Cards with Alliance Tables ---
    col6, col7 = st.columns(2)

    with col6:
        with st.container(border=True):
            st.subheader("State A")
            st.write(f"**State:** {row['Statecode_A']}")
            st.write(f"**Role:** {row['Role_A']}")
            st.write(f"**Conflict Severity:** {row['Severity_A']}")

            st.markdown("**Alliances during conflict:**")
            # Fetch active alliances for State A at the conflict start year
            alliances_a = get_country_alliances(
                row["Statecode_A"], row["Start_Year"], alliances
            )
            if alliances_a.empty:
                st.info("No alliance data found for this country / year.")
            else:
                st.dataframe(alliances_a, use_container_width=True, hide_index=True)

    with col7:
        with st.container(border=True):
            st.subheader("State B")
            st.write(f"**State:** {row['Statecode_B']}")
            st.write(f"**Role:** {row['Role_B']}")
            st.write(f"**Conflict Severity:** {row['Severity_B']}")

            st.markdown("**Alliances during conflict:**")
            # Fetch active alliances for State B at the conflict start year
            alliances_b = get_country_alliances(
                row["Statecode_B"], row["Start_Year"], alliances
            )
            if alliances_b.empty:
                st.info("No alliance data found for this country / year.")
            else:
                st.dataframe(alliances_b, use_container_width=True, hide_index=True)
    

    # --- Conflict Activity Bar Chart (±5 years around the conflict) ---
    with st.container(border=True):
        st.markdown(f"#### Conflict Involvements Around Conflict {row["Conflict_ID"]}")

        involved_countries = [row["Statecode_A"], row["Statecode_B"]]
        # Build a ±5 year window around the conflict duration
        year_window = range(row["Start_Year"] - 5, row["End_Year"] + 5 + 1)

        # Filter to conflicts where either involved country appears on either side
        conflicts_window = conflicts[
            (conflicts["Statecode_A"].isin(involved_countries) |
             conflicts["Statecode_B"].isin(involved_countries)) &
            (conflicts["Start_Year"].isin(year_window))
        ].copy()

        # Tag each conflict row with which of the two countries it belongs to
        # (a conflict may involve both, so we create one row per country)
        rows = []
        for country in involved_countries:
            mask = (
                (conflicts_window["Statecode_A"] == country) |
                (conflicts_window["Statecode_B"] == country)
            )
            per_country = conflicts_window[mask].copy()
            per_country["Country"] = country
            rows.append(per_country)

        conflicts_tagged = pd.concat(rows)

        # Count unique conflicts per country per start year for the grouped bar chart
        conflicts_per_year = (
            conflicts_tagged
            .drop_duplicates(subset=["Conflict_ID", "Country"])
            .groupby(["Start_Year", "Country"])
            .size()
            .reset_index(name="Conflict_Count")
        )

        # Grouped bar chart: one bar group per year, one bar per country
        fig_activity = px.bar(
            conflicts_per_year,
            x="Start_Year",
            y="Conflict_Count",
            color="Country",
            barmode="group",
            labels={"Start_Year": "Year", "Conflict_Count": "Number of Conflicts", "Country": "Country"},
            color_discrete_sequence=["#225ea8", "#7fcdbb"] 
        )

        # Annotate the conflict period: dashed red line for single-year, red band for multi-year
        if row["Start_Year"] == row["End_Year"]:
            fig_activity.add_vline(
                x=row["Start_Year"],
                line_color="red",
                line_width=2,
                line_dash="dash",
                annotation_text=f"Conflict Period",
                annotation_position="top",
                annotation=dict(font_size=14, font_color="red")
            )
        else:
            fig_activity.add_vrect(
                x0=row["Start_Year"],
                x1=row["End_Year"],
                fillcolor="red",
                opacity=0.15,
                layer="below",
                line_width=0,
                annotation_text=f"Conflict Period",
                annotation_position="top left",
                annotation=dict(font_size=14, font_color="red")
            )

        fig_activity.update_layout(
            height=350,
            font=dict(size=vis_annot_size),
            xaxis=dict(
                tickmode="linear",  # Force a tick for every year on the x-axis
                dtick=1,
                title_font=dict(color="black", size=vis_annot_size),   
                tickfont=dict(color="black", size=vis_annot_size)
            ),
            yaxis=dict(
                title_font=dict(color="black", size=vis_annot_size),   
                tickfont=dict(color="black", size=vis_annot_size)
            ),
            legend_font=dict(color="black", size=vis_annot_size),        
            legend_title_font=dict(color="black", size=vis_annot_size)
        )

        st.plotly_chart(fig_activity, use_container_width=True)
    

    # --- Military Expenditure Line Chart (±5 years around the conflict) ---
    # Note: MILEX data is only available from 1988–2024
    with st.container(border=True):
        st.markdown(
            f"#### Military Expenditure Around Conflict {row['Conflict_ID']} "
            f'<span title=" Data available from 1988 - 2024" '
            f'style="cursor:help; font-size:1rem;">ℹ️</span>',
            unsafe_allow_html=True
        )

        # Filter MILEX data to the two involved countries within the time window
        milex_window = milex[
            milex["Statecode"].isin([row["Statecode_A"], row["Statecode_B"]]) &
            milex["Year"].between(row["Start_Year"] - 5, row["End_Year"] + 5)
        ].copy()

        if milex_window.empty:
            st.info("No military expenditure data available for these countries in this period.")
        else:
            # Color each country's line consistently with the rest of the dashboard
            fig_milex = px.line(
                milex_window,
                x="Year",
                y="Expenditure",
                color="Statecode",
                markers=True,
                labels={"Expenditure": "Military Expenditure [Mio. USD]", "Year": "Year"},
                color_discrete_map={
                    row["Statecode_A"]: "#225ea8",
                    row["Statecode_B"]: "#7fcdbb",
                }
            )

            # Annotate the conflict period (same logic as the bar chart above)
            if row["Start_Year"] == row["End_Year"]:
                fig_milex.add_vline(
                    x=row["Start_Year"],
                    line_color="red",
                    line_width=2,
                    line_dash="dash",
                    annotation_text=f"Conflict",
                    annotation_position="top",
                    annotation=dict(font_size=14, font_color="red")
                )
            else:
                fig_milex.add_vrect(
                    x0=row["Start_Year"],
                    x1=row["End_Year"],
                    fillcolor="red",
                    opacity=0.15,
                    layer="below",
                    line_width=0,
                    annotation_text=f"Conflict Period",
                    annotation_position="top left",
                    annotation=dict(font_size=14, font_color="red")
                )

            fig_milex.update_layout(
                height=350,
                font=dict(size=vis_annot_size),
                xaxis=dict(
                    tickmode="linear",  # Force a tick for every year
                    dtick=1,
                    title_font=dict(color="black", size=vis_annot_size),   
                    tickfont=dict(color="black", size=vis_annot_size)
                ),
                yaxis=dict(
                    title_font=dict(color="black", size=vis_annot_size),   
                    tickfont=dict(color="black", size=vis_annot_size)
                ),
                legend_font=dict(color="black"),        
                legend_title_font=dict(color="black")
            )

            st.plotly_chart(fig_milex, use_container_width=True)


    # =========================================================================
    # Trade Section
    # =========================================================================

    with st.container(border=True):
        st.markdown("### Trade")
        st.markdown(
            "By default the countries involved in the selected conflict are selected in the filter and the year"
            " is set to the start of the selected conflict. The filters can be adjusted to expand the scope of your analysis "
            "beyond a single conflict."
        )

        # Pre-populate filters with the conflict's countries and start year
        selected_countries_trade = st.multiselect(
            "Filter Countries",
            options=trade["Statecode_A"].unique(),
            default=[row["Statecode_A"], row["Statecode_B"]]
        )

        selected_year = st.number_input(
            "Enter Year",
            min_value=trade["Year"].min(),
            max_value=trade["Year"].max(),
            value=row["Start_Year"]
        )

        # --- Trade Flow Line Chart (±5 years around selected year) ---
        # Filter trade data to the selected countries and a ±5 year window
        trade_line = trade[
            (trade["Statecode_A"].isin(selected_countries_trade)) &
            (trade["Statecode_B"].isin(selected_countries_trade)) &
            (trade["Year"].between(selected_year - 5, selected_year + 5))
        ].copy()

        trade_line = trade_line.sort_values("Year")

        if not trade_line.empty:
            fig_line = go.Figure()

            # Add one trace per directional flow for each unique country pair
            for _, pair_row in trade_line[["Statecode_A", "Statecode_B"]].drop_duplicates().iterrows():
                state_a = pair_row["Statecode_A"]
                state_b = pair_row["Statecode_B"]

                pair_data = trade_line[
                    (trade_line["Statecode_A"] == state_a) &
                    (trade_line["Statecode_B"] == state_b)
                ].sort_values("Year")

                # Flow 1: Imports to A from B (B → A)
                fig_line.add_trace(go.Scatter(
                    x=pair_data["Year"],
                    y=pair_data["Flow_1"],
                    mode="lines+markers",
                    name=f"{state_b} → {state_a}"
                ))

                # Flow 2: Imports to B from A (A → B)
                fig_line.add_trace(go.Scatter(
                    x=pair_data["Year"],
                    y=pair_data["Flow_2"],
                    mode="lines+markers",
                    name=f"{state_a} → {state_b}"
                ))

        fig_line.update_layout(
            height=450,
            font=dict(size=vis_annot_size),
            yaxis_title="Trade flow [Mio USD]",
            legend_title="Trade Direction",
            xaxis=dict(
                tickmode="linear",  # Force a tick for every year
                dtick=1,
                title_font=dict(color="black", size=vis_annot_size),   
                tickfont=dict(color="black", size=vis_annot_size)
            ),
            yaxis=dict(
                title_font=dict(color="black", size=vis_annot_size),   
                tickfont=dict(color="black", size=vis_annot_size)
            ),
            legend_font=dict(color="black", size=vis_annot_size),        
            legend_title_font=dict(color="black", size=vis_annot_size)
        )

        # Annotate the conflict period on the trade chart (dashed line or shaded region)
        if row["Start_Year"] == row["End_Year"]:
            fig_line.add_vline(
                x=row["Start_Year"],
                line_color="red",
                line_width=2,
                line_dash="dash",
                annotation_text="Conflict",
                annotation_position="top",
                annotation=dict(font_size=14, font_color="red")
            )
        else:
            fig_line.add_vrect(
                x0=row["Start_Year"],
                x1=row["End_Year"],
                fillcolor="red",
                opacity=0.15,
                layer="below",
                line_width=0,
                annotation_text="Conflict Period",
                annotation_position="top left",
                annotation=dict(font_size=14, font_color="red")
            )
        st.markdown(f"#### Trade Around Conflict {row["Conflict_ID"]}")
        st.plotly_chart(fig_line, use_container_width=True)


        # --- Multilateral Trade Sankey Diagram ---
        # Only render when at least two countries are selected
        if len(selected_countries_trade) >= 2:
            
            # Filter to trades exclusively between the selected countries in the chosen year
            filtered_trade = trade[
                (trade["Statecode_A"].isin(selected_countries_trade)) & 
                (trade["Statecode_B"].isin(selected_countries_trade)) & 
                (trade["Year"] == selected_year)
            ].copy()

            if not filtered_trade.empty:
                countries = list(selected_countries_trade)
                num_countries = len(countries)
                
                # Sankey nodes: left side = origins, right side = destinations
                # Labels are duplicated so each country appears as both origin and destination
                labels = [f"{c}" for c in countries] + [f"{c}" for c in countries]
                
                # Build lookup dicts: origin nodes are 0..N-1, destination nodes are N..2N-1
                origin_idx = {country: i for i, country in enumerate(countries)}
                dest_idx = {country: i + num_countries for i, country in enumerate(countries)}
                
                # Assign a distinct color to each country node, cycling the palette if needed
                base_colors = px.colors.qualitative.Set3
                node_colors = [base_colors[i % len(base_colors)] for i in range(num_countries)]
                node_colors = node_colors + node_colors  # Mirror colors for destination nodes

                # Build Sankey link arrays
                sources = []
                targets = []
                values = []
                link_labels = []

                for _, row in filtered_trade.iterrows():
                    state_a = row['Statecode_A']
                    state_b = row['Statecode_B']
                    
                    # Clamp negative values to 0 (data quality guard)
                    flow_1 = max(row['Flow_1'], 0)  # Imports to A from B (B → A)
                    flow_2 = max(row['Flow_2'], 0)  # Imports to B from A (A → B)

                    # Add link for Flow 1 (B → A) if non-zero
                    if flow_1 > 0:
                        sources.append(origin_idx[state_b])
                        targets.append(dest_idx[state_a])
                        values.append(flow_1)
                        link_labels.append(f"{state_b} to {state_a}")

                    # Add link for Flow 2 (A → B) if non-zero
                    if flow_2 > 0:
                        sources.append(origin_idx[state_a])
                        targets.append(dest_idx[state_b])
                        values.append(flow_2)
                        link_labels.append(f"{state_a} to {state_b}")

                # Build the Sankey figure
                fig = go.Figure(data=[go.Sankey(
                    valuesuffix=" Mio USD",
                    textfont=dict(color="black"),  # Node/flow labels in black for readability
                    node=dict(
                        pad=20,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=labels,
                        color=node_colors
                    ),
                    link=dict(
                        source=sources,
                        target=targets,
                        value=values,
                        label=link_labels
                    )
                )])

                fig.update_layout(
                    font_size=vis_annot_size,
                    height=600 
                )
                st.markdown(f"#### Multilateral Trade Network ({selected_year})")
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.warning("No trade data available between these selected countries for this year.")
        else:
            st.info("Please select at least two countries to generate the trade map.")


# =============================================================================
# Footer
# =============================================================================

footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed by Patrik Pnishi, Aron Monn, Jan Müller <a style='display: block; text-align: center;' </a></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)


# parts of this code were written with the help of or written by OpenAI ChatGPT 5.5 and Anthropic Claude Sonnet 4.6