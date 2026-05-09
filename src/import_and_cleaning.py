import pandas as pd

# ── Load raw data ──────────────────────────────────────────────────────────────
conflicts = pd.read_csv("../data/dyadic_mid_4.03.csv")
trade = pd.read_csv("../data/Dyadic_COW_4.0.csv")
alliances = pd.read_csv("../data/alliance_v4.1_by_directed_yearly.csv")
cow_iso = pd.read_csv("../data/countries.csv")  # COW code → ISO3 lookup
milex = pd.read_csv(
    "../data/SIPRI-Milex-data-1949-2024_2.csv",
    sep=";",
    encoding="latin1"
)

# SIPRI uses full country names; map to ISO3 for joining with COW-based datasets
country_to_iso3 = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Angola": "AGO",
    "Argentina": "ARG", "Armenia": "ARM", "Australia": "AUS", "Austria": "AUT",
    "Azerbaijan": "AZE", "Bahrain": "BHR", "Bangladesh": "BGD", "Belarus": "BLR",
    "Belgium": "BEL", "Belize": "BLZ", "Benin": "BEN", "Bolivia": "BOL",
    "Bosnia and Herzegovina": "BIH", "Botswana": "BWA", "Brazil": "BRA",
    "Brunei": "BRN", "Bulgaria": "BGR", "Burkina Faso": "BFA", "Burundi": "BDI",
    "Cambodia": "KHM", "Cameroon": "CMR", "Canada": "CAN", "Cape Verde": "CPV",
    "Central African Republic": "CAF", "Chad": "TCD", "Chile": "CHL",
    "China": "CHN", "Colombia": "COL", "Congo, DR": "COD", "Congo, Republic": "COG",
    "Costa Rica": "CRI", "Cote d'Ivoire": "CIV", "Croatia": "HRV", "Cuba": "CUB",
    "Cyprus": "CYP", "Czechia": "CZE", "Czechoslovakia": "CSK", "Denmark": "DNK",
    "Djibouti": "DJI", "Dominican Republic": "DOM", "Ecuador": "ECU",
    "Egypt": "EGY", "El Salvador": "SLV", "Equatorial Guinea": "GNQ",
    "Eritrea": "ERI", "Estonia": "EST", "Eswatini": "SWZ", "Ethiopia": "ETH",
    "European Union": "EUU", "Fiji": "FJI", "Finland": "FIN", "France": "FRA",
    "Gabon": "GAB", "Gambia, The": "GMB", "Georgia": "GEO",
    "German Democratic Republic": "DDR", "Germany": "DEU", "Ghana": "GHA",
    "Greece": "GRC", "Guatemala": "GTM", "Guinea": "GIN", "Guinea-Bissau": "GNB",
    "Guyana": "GUY", "Haiti": "HTI", "Honduras": "HND", "Hungary": "HUN",
    "Iceland": "ISL", "India": "IND", "Indonesia": "IDN", "Iran": "IRN",
    "Iraq": "IRQ", "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA",
    "Jamaica": "JAM", "Japan": "JPN", "Jordan": "JOR", "Kazakhstan": "KAZ",
    "Kenya": "KEN", "Korea, North": "PRK", "Korea, South": "KOR", "Kosovo": "XKX",
    "Kuwait": "KWT", "Kyrgyz Republic": "KGZ", "Laos": "LAO", "Latvia": "LVA",
    "Lebanon": "LBN", "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY",
    "Lithuania": "LTU", "Luxembourg": "LUX", "Madagascar": "MDG", "Malawi": "MWI",
    "Malaysia": "MYS", "Mali": "MLI", "Malta": "MLT", "Mauritania": "MRT",
    "Mauritius": "MUS", "Mexico": "MEX", "Moldova": "MDA", "Mongolia": "MNG",
    "Montenegro": "MNE", "Morocco": "MAR", "Mozambique": "MOZ", "Myanmar": "MMR",
    "Namibia": "NAM", "Nepal": "NPL", "Netherlands": "NLD", "New Zealand": "NZL",
    "Nicaragua": "NIC", "Niger": "NER", "Nigeria": "NGA", "North Macedonia": "MKD",
    "Norway": "NOR", "Oman": "OMN", "Pakistan": "PAK", "Panama": "PAN",
    "Papua New Guinea": "PNG", "Paraguay": "PRY", "Peru": "PER",
    "Philippines": "PHL", "Poland": "POL", "Portugal": "PRT", "Qatar": "QAT",
    "Romania": "ROU", "Russia": "RUS", "Rwanda": "RWA", "Saudi Arabia": "SAU",
    "Senegal": "SEN", "Serbia": "SRB", "Seychelles": "SYC", "Sierra Leone": "SLE",
    "Singapore": "SGP", "Slovakia": "SVK", "Slovenia": "SVN", "Somalia": "SOM",
    "South Africa": "ZAF", "South Sudan": "SSD", "Spain": "ESP",
    "Sri Lanka": "LKA", "Sudan": "SDN", "Sweden": "SWE", "Switzerland": "CHE",
    "Syria": "SYR", "Taiwan": "TWN", "Tajikistan": "TJK", "Tanzania": "TZA",
    "Thailand": "THA", "Timor Leste": "TLS", "Togo": "TGO",
    "Trinidad and Tobago": "TTO", "Tunisia": "TUN", "Turkmenistan": "TKM",
    "Türkiye": "TUR", "Uganda": "UGA", "Ukraine": "UKR",
    "United Arab Emirates": "ARE", "United Kingdom": "GBR",
    "United States of America": "USA", "Uruguay": "URY", "Uzbekistan": "UZB",
    "Venezuela": "VEN", "Viet Nam": "VNM", "Yemen": "YEM",
    "Yemen, North": "YEM",  # historical state, maps to modern YEM
    "Yugoslavia": "YUG", "Zambia": "ZMB", "Zimbabwe": "ZWE",
}

# ── Column selections and renames (per MID 4.03 / COW codebooks) ───────────────
conflicts_cols = [
    "disno", "statea", "stateb", "year", "strtyr", "endyear",
    "outcome", "fatlev", "hihost", "rolea", "roleb",
    "severity", "severitya", "severityb"
]
conflicts_col_mapper = {
    "disno": "Conflict_ID", "statea": "Statecode_A", "stateb": "Statecode_B",
    "year": "Year", "strtyr": "Start_Year", "endyear": "End_Year",
    "outcome": "Outcome", "fatlev": "Fatality_Level", "hihost": "Hostility",
    "rolea": "Role_A", "roleb": "Role_B",
    "severity": "Severity", "severitya": "Severity_A", "severityb": "Severity_B"
}

trade_cols = ["ccode1", "ccode2", "year", "importer1", "importer2", "flow1", "flow2"]
trade_col_mapper = {
    "ccode1": "Statecode_A", "ccode2": "Statecode_B", "year": "Year",
    "importer1": "State_A", "importer2": "State_B",
    "flow1": "Flow_1", "flow2": "Flow_2"
}

alliances_cols = [
    "ccode1", "state_name1", "ccode2", "state_name2",
    "dyad_st_year", "dyad_end_year",
    "defense", "neutrality", "nonaggression", "entente", "year"
]
alliances_col_mapper = {
    "ccode1": "Statecode_A", "state_name1": "State_A",
    "ccode2": "Statecode_B", "state_name2": "State_B",
    "dyad_st_year": "Start_Year", "dyad_end_year": "End_Year",
    "defense": "Defense", "neutrality": "Neutrality",
    "nonaggression": "Nonaggression", "entente": "Entente", "year": "Year"
}

# Codebook label mappings (MID 4.03 documentation)
conflict_outcomes = {
    0: "Ongoing MID", 1: "Victory for State A", 2: "Victory for state B",
    3: "Yield by State A", 4: "Yield by State B", 5: "Stalemate",
    6: "Compromise", 7: "Released (for seizures)", 8: "Unclear", 9: "Missing"
}
conflict_roles = {
    1: "Primary Initiator", 2: "Joiner on initiator side",
    3: "Primary target", 4: "Joiner on target side"
}
conflict_hostility = {
    1: "None", 2: "Threat to use force", 3: "Display of Force",
    4: "Use of Force", 5: "Interstate war"
}

# ── Select and rename columns ──────────────────────────────────────────────────
conflicts = conflicts[conflicts_cols].rename(columns=conflicts_col_mapper)
trade = trade[trade_cols].rename(columns=trade_col_mapper)
alliances = alliances[alliances_cols].rename(columns=alliances_col_mapper)

# ── COW code → ISO3 conversion ─────────────────────────────────────────────────
# COW assigns multiple rows per country code for historical states; keep one
cow_iso = cow_iso.drop_duplicates(subset=["CCode"])
ccode_to_iso = cow_iso.set_index("CCode")["iso3"]

for df in [conflicts, trade, alliances]:
    df["Statecode_A"] = df["Statecode_A"].map(ccode_to_iso)
    df["Statecode_B"] = df["Statecode_B"].map(ccode_to_iso)

# Drop dyads involving dissolved or unrecognised states (no ISO3 mapping)
conflicts = conflicts.dropna()
trade = trade.dropna()
alliances = alliances.dropna()

# ── Clean trade flows ──────────────────────────────────────────────────────────
# -9 encodes missing values in COW trade data; replace with NaN
trade["Flow_1"] = trade["Flow_1"].replace(-9.0, None)
trade["Flow_2"] = trade["Flow_2"].replace(-9.0, None)

# ── Decode conflict categorical variables ──────────────────────────────────────
conflicts["Outcome"] = conflicts["Outcome"].map(conflict_outcomes)
conflicts["Role_A"] = conflicts["Role_A"].map(conflict_roles)
conflicts["Role_B"] = conflicts["Role_B"].map(conflict_roles)
conflicts["Hostility"] = conflicts["Hostility"].map(conflict_hostility)

# ── Reshape SIPRI milex from wide (countries × years) to long ─────────────────
milex = milex.melt(id_vars="Country", var_name="Year", value_name="Expenditure")

milex["Year"] = milex["Year"].astype(int)
milex["Expenditure"] = pd.to_numeric(milex["Expenditure"], errors="coerce")
milex = milex.sort_values(["Country", "Year"]).reset_index(drop=True)

milex["Statecode"] = milex["Country"].map(country_to_iso3)

# ── Write cleaned datasets to parquet ─────────────────────────────────────────
conflicts.to_parquet("../data/clean/conflicts.parquet")
alliances.to_parquet("../data/clean/alliances.parquet")
trade.to_parquet("../data/clean/trade.parquet")
milex.to_parquet("../data/clean/milex.parquet")


# parts of this code were written with the help of or written by OpenAI ChatGPT 5.5 and Anthropic Claude Sonnet 4.6