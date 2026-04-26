library("countrycode")
library("tidyverse")

states <- read_csv("./data/COW-country-codes.csv")

states$iso3 <- countrycode(
  states$CCode,
  origin = "cown",
  destination = "iso3c",
  custom_match = c(
    "260" = "DEU",  # German Federal Republic
    "265" = "DEU",  # German Democratic Republic
    "678" = "YEM", #Yemen Arab Republic
    "780" = "YEM", #Yemen People's Republic
    "817" = "VNM" # Republic of Vietnam
  )
)

write_csv(states, "./data/countries.csv")