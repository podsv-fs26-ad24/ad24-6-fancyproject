from ydata_profiling import ProfileReport
import pandas as pd

conflicts = pd.read_csv("./data/dyadic_mid_4.03.csv")
trade = pd.read_csv("./data/Dyadic_COW_4.0.csv")
alliances = pd.read_csv("./data/alliance_v4.1_by_directed_yearly.csv")
milex =  pd.read_csv(
    "./data/SIPRI-Milex-data-1949-2024_2.csv",
    sep=";",
    encoding="latin1"
)

profile_conflicts = ProfileReport(
    conflicts,
    title="conflicts_eda",
    explorative=True
)
profile_trade = ProfileReport(
    trade,
    title="trade_eda",
    explorative=True
)
profile_alliances = ProfileReport(
    alliances,
    title="alliances_eda",
    explorative=True
)
profile_milex = ProfileReport(
    milex,
    title="milex_eda",
    explorative=True
)



profile_conflicts.to_file("./eda/conflicts_eda.html")
profile_trade.to_file("./eda/trade_eda.html")
profile_alliances.to_file("./eda/alliances_eda.html")
profile_milex.to_file("./eda/milex_eda.html")