"""Makes a dataframe collecting various individual characteristics"""
import numpy as np
import pandas as pd


def create_cleaned_hh_income(data):
    data["net_income_hh_raw"] = data["net_income_hh"]
    data.loc[
        [818981, 808789, 825565, 843115, 836520, 889373, 878469, 815637],
        "net_income_hh",
    ] = np.nan
    data.loc[
        pd.IndexSlice[[805749, 822924, 890798, 893679], ["2020-04-01", "2020-05-01"]],
        "net_income_hh",
    ] /= 10
    data.loc[pd.IndexSlice[[827557], ["2020-01-01"]], "net_income_hh"] /= 1000
    data.loc[
        pd.IndexSlice[[827557, 871542], ["2020-06-01", "2020-07-01", "2020-08-01"]],
        "net_income_hh",
    ] /= 10
    data.loc[
        pd.IndexSlice[[829412], ["2020-01-01", "2020-02-01", "2020-03-01"]],
        "net_income_hh",
    ] /= 10
    data.loc[
        pd.IndexSlice[[829888], ["2020-01-01", "2020-02-01", "2020-03-01"]],
        "net_income_hh",
    ] /= 100
    data.loc[pd.IndexSlice[[834820], ["2020-05-01"]], "net_income_hh"] /= 100
    data.loc[pd.IndexSlice[[839682], ["2020-03-01"]], "net_income_hh"] /= 100
    data.loc[pd.IndexSlice[[847283], ["2020-01-01"]], "net_income_hh"] /= 100
    data.loc[pd.IndexSlice[[847283, 845327], ["2020-02-01"]], "net_income_hh"] /= 10
    data.loc[pd.IndexSlice[[861538], ["2020-02-01"]], "net_income_hh"] /= 1000
    data.loc[
        pd.IndexSlice[[861538, 859658, 886560], ["2020-03-01"]], "net_income_hh"
    ] /= 10
    data.loc[pd.IndexSlice[[871536], ["2020-04-01"]], "net_income_hh"] /= 1000
    data.loc[pd.IndexSlice[[873541], ["2020-04-01"]], "net_income_hh"] = np.nan
    data.loc[pd.IndexSlice[[847018], ["2020-04-01"]], "net_income_hh"] = np.nan
    data.loc[
        pd.IndexSlice[[847018, 822732], ["2020-05-01"]], "net_income_hh"
    ] = data.loc[
        pd.IndexSlice[[847018, 822732], ["2020-05-01"]], "net_income_hh_202005_elic_09"
    ]

    data.loc[pd.IndexSlice[[878442], ["2020-06-01"]], "net_income_hh"] /= 1000
    data.loc[pd.IndexSlice[[881396, 838024], ["2020-03-01"]], "net_income_hh"] /= 10
    data.loc[pd.IndexSlice[[898706], ["2020-04-01"]], "net_income_hh"] /= 1000

    data.loc[pd.IndexSlice[[811041], ["2020-05-01"]], "net_income_hh"] /= 10
    data.loc[
        pd.IndexSlice[[817797], ["2020-04-01", "2020-05-01"]], "net_income_hh"
    ] /= 1000
    data.loc[
        pd.IndexSlice[[821951, 823675], ["2020-04-01", "2020-05-01"]], "net_income_hh"
    ] /= 10
    data.loc[pd.IndexSlice[[822798, 831478], ["2020-01-01"]], "net_income_hh"] /= 10
    data.loc[
        pd.IndexSlice[[822863], ["2020-03-01", "2020-04-01", "2020-05-01"]],
        "net_income_hh",
    ] /= 10

    data.loc[pd.IndexSlice[[831478], ["2020-04-01"]], "net_income_hh"] /= 100
    data.loc[
        pd.IndexSlice[[858104], ["2020-02-01", "2020-03-01"]], "net_income_hh"
    ] /= 10
    data.loc[
        pd.IndexSlice[
            [881359],
            ["2020-01-01", "2020-02-01", "2020-03-01", "2020-04-01", "2020-05-01"],
        ],
        "net_income_hh",
    ] /= 10
    data.loc[pd.IndexSlice[[888732], ["2020-08-01"]], "net_income_hh"] /= 10
    data.loc[pd.IndexSlice[[822798], ["2020-01-01"]], "net_income_hh"] /= 10
    data.loc[pd.IndexSlice[[822798], ["2020-01-01"]], "net_income_hh"] /= 10
    data.loc[pd.IndexSlice[[822798], ["2020-01-01"]], "net_income_hh"] /= 10
    return data
