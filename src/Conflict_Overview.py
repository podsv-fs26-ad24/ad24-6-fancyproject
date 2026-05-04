import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.set_page_config(layout="wide",
                   page_title="Conflict Overview")


### Data Import
conflicts = pd.read_parquet("./data/clean/conflicts.parquet")
trade = pd.read_parquet("./data/clean/trade.parquet")
alliances = pd.read_parquet("./data/clean/alliances.parquet")



# Data Processing
#########################################################

@st.cache_data
def get_conflicts_counts(data: pd.DataFrame):
    """Return df with conflict counts for each country"""
    # Extract unique Conflict_ID and Statecode pairs to avoid double-counting years
    state_a = data[["Conflict_ID", "Statecode_A"]].rename(columns={"Statecode_A": "Statecode"})
    state_b = data[["Conflict_ID", 'Statecode_B']].rename(columns={"Statecode_B": "Statecode"})
    
    # Combine lists and drop duplicates so each country is counted once per conflict
    unique_conflicts = pd.concat([state_a, state_b]).drop_duplicates()
    
    # Count total unique conflicts per country
    counts = unique_conflicts["Statecode"].value_counts().reset_index()
    counts.columns = ["Statecode", "Total_Conflicts"]
    
    # Groupby State because historical entities (e.g. East/West Germany -> DEU) merge into single Entity
    final_counts = counts.groupby("Statecode")["Total_Conflicts"].sum().reset_index()
    
    return final_counts


def get_country_alliances(country_code: str, year: int, data: pd.DataFrame) -> pd.DataFrame:
    """Return all alliance partners a country had in a given year, with alliance types."""

    # Match rows where the country appears on either side
    mask = (
        ((data["Statecode_A"] == country_code) | (data["Statecode_B"] == country_code)) &
        (data["Start_Year"] <= year) &
        (data["End_Year"]   >= year)
    )
    active = data[mask].copy()

    # if no alliances -> return empty df
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

    # Build a readable alliance type string from the binary flag columns
    type_flags = {
        "Defense":      "Defense Pact",
        "Neutrality":   "Neutrality Pact",
        "Nonaggression":"Non-Aggression Pact",
        "Entente":      "Entente",
    }
    def alliance_types(row):
        return ", ".join(label for col, label in type_flags.items() if row.get(col, 0) == 1)
    # Apply function to get Alliance Type Column from One-Hot encoded Alliance columns
    active["Alliance Type"] = active.apply(alliance_types, axis=1)
    active["Alliance Type"] = active["Alliance Type"].replace("", "Unspecified")

    return active[["Partner_Code", "Partner_Name", "Alliance Type", "Start_Year", "End_Year"]] \
               .drop_duplicates() \
               .reset_index(drop=True) \
               .rename(columns={
                   "Partner_Code": "Country Code",
                   "Partner_Name": "Partner Country",
                   "Start_Year":   "Since",
                   "End_Year":     "Until",
               })


# use helper function to create new df with conflict counts
df_conflict_counts = get_conflicts_counts(conflicts)
df_conflict_counts["Log_Conflicts"] = np.log1p(df_conflict_counts["Total_Conflicts"])



# Dashboard layout
############################################################################

st.title("Geopolitical Conflict & Trade Explorer")

# Show stats for conflict dataset
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Recorded Conflicts", f"{len(conflicts["Conflict_ID"].unique())}")
with col2:
    year_min, year_max = conflicts["Start_Year"].min(), conflicts["End_Year"].max()
    st.metric("Year Range", f"{year_min} - {year_max}")
with col3:
    st.metric("Number of Countries involved in conflicts", f"{len(conflicts["Statecode_A"].unique())}")

# Global Map with conflict count for each country
with st.container():
    st.title("Global Conflict Involvement Map")
    st.markdown("This map shows the total number of unique conflicts each country has been involved in.")
    # Generate the Choropleth map using Plotly Express
    fig = px.choropleth(
        df_conflict_counts,
        locations="Statecode",
        color="Log_Conflicts",
        hover_name="Statecode",
        color_continuous_scale="YlGnBu", 
        labels={"Total_Conflicts": "Conflict Count"},
        hover_data={"Log_Conflicts": False, "Total_Conflicts": True},
    )

    #manually define colorbar ticks
    legend_ticks = [5, 25, 50, 100, 200, 300]
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
    # Render Plotly map to Streamlit
    st.plotly_chart(fig, use_container_width=True)


with st.container(border=True):
    st.markdown("### Conflict Browser")

    # Table to filter and search specific conflicts
    selected_countries = st.multiselect(
        "Filter involved Countries",
        options=conflicts["Statecode_A"].unique(),
        default="CHE"
    )

    min_year, max_year = st.slider(
        "Year",
        min_value=int(conflicts["Year"].min()),
        max_value=int(conflicts["Year"].max()),
        value=(int(conflicts["Year"].min()), int(conflicts["Year"].max()))
    )

    min_sev, max_sev = st.slider(
        "Severity",
        min_value=int(conflicts["Severity"].min()),
        max_value=int(conflicts["Severity"].max()),
        value=(int(conflicts["Severity"].min()), int(conflicts["Severity"].max()))
    )

    filtered_df = conflicts[
        conflicts["Statecode_A"].isin(selected_countries) &
        conflicts["Year"].between(min_year, max_year) &
        conflicts["Severity"].between(min_sev, max_sev)
    ]
    
    # Display Dataframe
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


# Conflict Analyzer
############################################

with st.container(border=True):
    st.markdown("### Conflict Analyzer")
    selected_conflict = st.selectbox(
        label="Which Conflict would you like to analyze in detail?",
        options=conflicts["Conflict_ID"].unique()
    )

    # Isolate all rows for the selected conflict
    conflict_data = conflicts[conflicts["Conflict_ID"] == selected_conflict]
    
    # Calculate the maximum fatality level across ALL years of the conflict
    max_fatality = conflict_data["Fatality_Level"].max()
    
    # Sort by Year and grab the very last row for the end-of-conflict stats
    row = conflict_data.sort_values(by="Year").iloc[-1]


    # Create a small DataFrame for the two involved countries
    df_selected_map = pd.DataFrame({
        "Statecode": [row['Statecode_A'], row['Statecode_B']],
        "Side": ["Side A", "Side B"]
    })

    # Generate a Choropleth map highlighting just these two countries
    fig_conflict_map = px.choropleth(
        df_selected_map,
        locations="Statecode",
        color="Side",
        color_discrete_map={"Side A": "#225ea8", "Side B": "#7fcdbb"}, # Red and Blue
        hover_name="Statecode"
    )

    fig_conflict_map.update_layout(
        geo=dict(
            showframe=False, 
            showcoastlines=True, 
            projection_type='equirectangular',
            showland=True,
            landcolor="lightgray" # Paints non-involved countries gray for contrast
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        height=400,
        legend_title_text="Involved Parties"
    )

    # Display the map
    st.plotly_chart(fig_conflict_map, use_container_width=True)


    with st.container(border=True):
        st.subheader("Stats")
        col4, col5 = st.columns(2)
        with col4:
            st.write(f"**Duration:** {row["Start_Year"]} - {row["End_Year"]}")
            # 4. Use the max_fatality variable we calculated above
            st.write(f"**Fatality Level (Max):** {max_fatality}")
            
        with col5:
            st.write(f"**Conflict Outcome:** {row["Outcome"]}")
            st.write(f"**Highest Severity:** {row["Severity"]}")

    col6, col7 = st.columns(2)

    with col6:
        with st.container(border=True):
            st.subheader("Side A")
            st.write(f"**State:** {row['Statecode_A']}")
            st.write(f"**Role:** {row['Role_A']}")
            st.write(f"**Conflict Severity:** {row['Severity_A']}")

            st.markdown("**Alliances during conflict:**")
            alliances_a = get_country_alliances(
                row["Statecode_A"], row["Start_Year"], alliances
            )
            if alliances_a.empty:
                st.info("No alliance data found for this country / year.")
            else:
                st.dataframe(
                    alliances_a,
                    use_container_width=True,
                    hide_index=True,
                )

    with col7:
        with st.container(border=True):
            st.subheader("Side B")
            st.write(f"**State:** {row['Statecode_B']}")
            st.write(f"**Role:** {row['Role_B']}")
            st.write(f"**Conflict Severity:** {row['Severity_B']}")

            st.markdown("**Alliances during conflict:**")
            alliances_b = get_country_alliances(
                row["Statecode_B"], row["Start_Year"], alliances
            )
            if alliances_b.empty:
                st.info("No alliance data found for this country / year.")
            else:
                st.dataframe(
                    alliances_b,
                    use_container_width=True,
                    hide_index=True,
                )
    
        # Conflicts per year chart — ± 5 years around the conflict start
    with st.container(border=True):
        st.markdown(f"#### Conflict Involvements Around Conflict {row["Conflict_ID"]}")

        involved_countries = [row["Statecode_A"], row["Statecode_B"]]
        year_window = range(row["Start_Year"] - 5, row["End_Year"] + 5 + 1)

        # Keep rows where either side matches one of the two countries
        conflicts_window = conflicts[
            (conflicts["Statecode_A"].isin(involved_countries) |
             conflicts["Statecode_B"].isin(involved_countries)) &
            (conflicts["Start_Year"].isin(year_window))
        ].copy()

        # Tag each row with which of the two countries it belongs to
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

        # Count unique conflicts per country per start year
        conflicts_per_year = (
            conflicts_tagged
            .drop_duplicates(subset=["Conflict_ID", "Country"])
            .groupby(["Start_Year", "Country"])
            .size()
            .reset_index(name="Conflict_Count")
        )

        fig_activity = px.bar(
            conflicts_per_year,
            x="Start_Year",
            y="Conflict_Count",
            color="Country",
            barmode="group",
            labels={"Start_Year": "Year", "Conflict_Count": "Number of Conflicts", "Country": "Country"},
            color_discrete_sequence=["#225ea8", "#7fcdbb"]  # matches your Side A / Side B map colors
        )

        # Highlight the conflict duration with a red line if duration <=1 year
        if row["Start_Year"] == row["End_Year"]:
            fig_activity.add_vline(
                x=row["Start_Year"],
                line_color="red",
                line_width=2,
                line_dash="dash",
                annotation_text=f"Conflict {row["Conflict_ID"]}",
                annotation_position="top",
                annotation=dict(font_size=12, font_color="red")
            )
            # Highlight the conflict duration with a red block if duration >1 year
        else:
            fig_activity.add_vrect(
                x0=row["Start_Year"],
                x1=row["End_Year"],
                fillcolor="red",
                opacity=0.15,
                layer="below",
                line_width=0,
                annotation_text=f"Conflict {row["Conflict_ID"]}",
                annotation_position="top left",
                annotation=dict(font_size=12, font_color="red")
            )

        fig_activity.update_layout(
            height=350,
            font=dict(size=13),
            xaxis=dict(tickmode="linear", dtick=1)
        )

        st.plotly_chart(fig_activity, use_container_width=True)




##########################################

    ### Trade
    with st.container(border=True):
        st.markdown("### Trade")

        # by default select countries from conflict with option to add more countries
        selected_countries_trade = st.multiselect(
        "Filter Countries",
        options=trade["Statecode_A"].unique(),
        default= [row["Statecode_A"], row["Statecode_B"]]
    )
        #use start of conlfict as default selected year selected_year
        selected_year = st.number_input(
            "Enter Year",
            min_value=trade["Year"].min(),
            max_value=trade["Year"].max(),
            value=row["Start_Year"]
        )

        #Linechart
        ##################
        # Filter: selected countries and +- 5 years
        trade_line = trade[
            (trade["Statecode_A"].isin(selected_countries_trade)) &
            (trade["Statecode_B"].isin(selected_countries_trade)) &
            (trade["Year"].between(selected_year - 5, selected_year + 5))
        ].copy()


        # Sort by year
        trade_line = trade_line.sort_values("Year")

        if not trade_line.empty:
            fig_line = go.Figure()

            # Iterate over every unique country pair in the filtered data
            for _, pair_row in trade_line[["Statecode_A", "Statecode_B"]].drop_duplicates().iterrows():
                state_a = pair_row["Statecode_A"]
                state_b = pair_row["Statecode_B"]

                pair_data = trade_line[
                    (trade_line["Statecode_A"] == state_a) &
                    (trade_line["Statecode_B"] == state_b)
                ].sort_values("Year")

                # Flow 1: B → A
                fig_line.add_trace(go.Scatter(
                    x=pair_data["Year"],
                    y=pair_data["Flow_1"],
                    mode="lines+markers",
                    name=f"{state_b} → {state_a}"
                ))

                # Flow 2: A → B
                fig_line.add_trace(go.Scatter(
                    x=pair_data["Year"],
                    y=pair_data["Flow_2"],
                    mode="lines+markers",
                    name=f"{state_a} → {state_b}"
                ))

            fig_line.update_layout(
                yaxis_title="Trade flow [Mio USD]",
                legend_title="Trade Direction",
            )

        fig_line.update_layout(
            height=450,
            font=dict(size=14)
        )

        # Highlight conflict duration: vline if < 1 year, red band if > 1
        if row["Start_Year"] == row["End_Year"]:
            fig_line.add_vline(
                x=row["Start_Year"],
                line_color="red",
                line_width=2,
                line_dash="dash",
                annotation_text="Conflict",
                annotation_position="top",
                annotation=dict(font_size=12, font_color="red")
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
                annotation=dict(font_size=12, font_color="red")
            )

        st.plotly_chart(fig_line, use_container_width=True)


        #Sankey Chart
        #####################
        # Only render the chart if at least two countries are selected
        if len(selected_countries_trade) >= 2:
            
            # 2. Filter the dataset for ALL selected countries (both sides of the trade)
            filtered_trade = trade[
                (trade["Statecode_A"].isin(selected_countries_trade)) & 
                (trade["Statecode_B"].isin(selected_countries_trade)) & 
                (trade["Year"] == selected_year) # Make sure you filter by a specific year!
            ].copy()

            if not filtered_trade.empty:
                # 3. Dynamically build Nodes (Origins on the left, Destinations on the right)
                countries = list(selected_countries_trade)
                num_countries = len(countries)
                
                # Create labels: e.g., ["USA (Origin)", "CAN (Origin)", ..., "USA (Dest)", "CAN (Dest)"]
                labels = [f"{c} (Origin)" for c in countries] + [f"{c} (Destination)" for c in countries]
                
                # Create a dictionary to easily look up the index for any country
                # Origins are indices 0 to N-1. Destinations are indices N to 2N-1.
                origin_idx = {country: i for i, country in enumerate(countries)}
                dest_idx = {country: i + num_countries for i, country in enumerate(countries)}
                
                # Generate a color palette for the nodes so they are easy to distinguish
                base_colors = px.colors.qualitative.Set3
                # Assign colors, looping the palette if there are more countries than colors
                node_colors = [base_colors[i % len(base_colors)] for i in range(num_countries)]
                node_colors = node_colors + node_colors # Match Origin colors to Destination colors

                # 4. Dynamically build Links
                sources = []
                targets = []
                values = []
                link_labels = []

                # Iterate through the filtered data to map the flows
                for _, row in filtered_trade.iterrows():
                    state_a = row['Statecode_A']
                    state_b = row['Statecode_B']
                    
                    # Clean missing data
                    flow_1 = max(row['Flow_1'], 0) # Imports to A from B (B -> A)
                    flow_2 = max(row['Flow_2'], 0) # Imports to B from A (A -> B)

                    # Map Flow 1 (B -> A)
                    if flow_1 > 0:
                        sources.append(origin_idx[state_b])
                        targets.append(dest_idx[state_a])
                        values.append(flow_1)
                        link_labels.append(f"{state_b} to {state_a}")

                    # Map Flow 2 (A -> B)
                    if flow_2 > 0:
                        sources.append(origin_idx[state_a])
                        targets.append(dest_idx[state_b])
                        values.append(flow_2)
                        link_labels.append(f"{state_a} to {state_b}")

                # 5. Build the Figure
                fig = go.Figure(data=[go.Sankey(
                    valuesuffix = " Mio USD",
                    node = dict(
                        pad = 20,
                        thickness = 20,
                        line = dict(color = "black", width = 0.5),
                        label = labels,
                        color = node_colors
                    ),
                    link = dict(
                        source = sources,
                        target = targets,
                        value = values,
                        label = link_labels
                    )
                )])

                fig.update_layout(
                    font_size=15,
                    height=600 # Slightly taller to accommodate more nodes
                )
                st.markdown(f"#### Multilateral Trade Network ({selected_year})")
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.warning("No trade data available between these selected countries for this year.")
        else:
            st.info("Please select at least two countries to generate the trade map.")


















### Footer

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
st.markdown(footer,unsafe_allow_html=True)