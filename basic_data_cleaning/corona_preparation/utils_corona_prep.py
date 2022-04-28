"""
This file contains some crucial utilities
"""
import numpy as np
import pandas as pd
from config import IN_SPECS_CORONA
from config import OUT_DATA_CORONA_PREP
from config import OUT_DATA_LISS
from liss_data.utils_liss_data import variable_cleaning_for_dta
from pandas.api.types import is_categorical


def load_data_set_liss(data_set_name):
    """
    Load the data set with name data_set_name.
    """

    return pd.read_pickle(OUT_DATA_LISS / f"{data_set_name}.pickle")


def load_data_set(data_set_name):
    """
    Load the data set with name data_set_name.
    """

    return pd.read_pickle(OUT_DATA_CORONA_PREP / f"{data_set_name}.pickle")


def save_and_check_data_set(data, data_set_name, stata=True):
    """
    Save the data set with name data_set_name.
    """

    # Check for columns with all nan or nan columns
    assert (
        not data.isnull().all(axis=0).any()
    ), f"Only contain NaN values in columns {data.columns[data.isnull().all(axis=0)]}."

    assert (
        not data.columns.isnull().any()
    ), f"There are NaN columns in the data set. {data.columns[data.columns.isnull()]}"
    data = _check_for_two_types_of_missing(data)

    # Save data
    data.to_pickle(OUT_DATA_CORONA_PREP / f"{data_set_name}.pickle")
    data.to_csv(OUT_DATA_CORONA_PREP / f"{data_set_name}.csv", sep=";")
    if stata:
        data = variable_cleaning_for_dta(data.copy(deep=True))
        data.to_stata(OUT_DATA_CORONA_PREP / f"{data_set_name}.dta")
        # data.to_parquet(ppj("OUT_DATA_CORONA_PREP", f"{data_set_name}.parquet"))


def create_mhi5(data, suffix):
    """Return MHI-5 score based on colums

        - nervous
        - depressed
        - calm
        - gloomy
        - happy

    and append *suffix* to each of those.

    Assumes that all of them are ordered Categoricals with higher values
    indicating better mental health. The latter feature is not checked!

    """

    assert data[f"nervous{suffix}"].cat.ordered
    assert data[f"depressed{suffix}"].cat.ordered
    assert data[f"calm{suffix}"].cat.ordered
    assert data[f"gloomy{suffix}"].cat.ordered
    assert data[f"happy{suffix}"].cat.ordered

    return 4 * (
        data[f"nervous{suffix}"].cat.codes.replace({-1: np.nan})
        + data[f"depressed{suffix}"].cat.codes.replace({-1: np.nan})
        + data[f"calm{suffix}"].cat.codes.replace({-1: np.nan})
        + data[f"gloomy{suffix}"].cat.codes.replace({-1: np.nan})
        + data[f"happy{suffix}"].cat.codes.replace({-1: np.nan})
    )


def create_new_background_variables(df):
    df = df.copy()

    df["mhi5_back"] = create_mhi5(data=df, suffix="_back")

    # female
    # df["female"] = df["gender"].map({"female": True, "male": False}).astype(float)

    # age
    df["age"] = 2020 - df["birth_year"]

    # wealth
    df["housing_part_of_wealth"] = (
        df["home_price"]
        - df["home_remaining_mortgage"]
        + df["sec_home_price"]
        - df["sec_home_remaining_mort"]
    )
    # ToDo: housing: fillna(0) ?
    df["wealth"] = df["wealth_excl_housing"] + df["housing_part_of_wealth"]

    # Remove observations that report mortgage that is twice as large as house price
    df.loc[
        df["home_remaining_mortgage"] > df["home_price"] * 2,
        ["wealth", "home_price", "home_remaining_mortgage"],
    ] = np.nan
    df.loc[
        df["sec_home_remaining_mort"] > df["sec_home_price"] * 2,
        ["wealth", "sec_home_price", "sec_home_remaining_mort"],
    ] = np.nan
    df.loc[df["mortgage"] > df["real_estate"] * 2, ["wealth", "mortgage"]] = np.nan

    # Find out age of youngest child
    temp = (
        df.query("(hh_position == 'Child living at home')")
        .copy()[["age", "hh_id"]]
        .groupby("hh_id")
        .min()
    )
    temp = temp.rename(columns={"age": "age_youngest_child"})
    df = pd.merge(df, temp, left_on="hh_id", right_index=True, how="left")

    # Generate hh_wide variables
    hh_wide_vars = [
        "wealth",
        "total_financial_assets",
        "risky_financial_assets",
        "home_price",
        "home_remaining_mortgage",
    ]
    for var in hh_wide_vars:
        df = (
            df.reset_index()
            .set_index("hh_id")
            .join(df.groupby("hh_id")[var].sum(min_count=1), rsuffix="_hh")
            .reset_index()
            .set_index("personal_id")
        )
        df = df.drop([var], axis=1)

    # Equivalise some vars
    for var in hh_wide_vars + ["net_income"]:
        df[var + "_hh_eqv"] = df[var + "_hh"] / np.sqrt(df["hh_members"])

    # Categorization
    df["age_group"] = pd.cut(
        df["age"], [-1, 40, 65, np.inf], labels=["<40", "40 to 65", ">65"]
    ).astype("category")

    df["income_group"] = pd.cut(
        df["net_income"],
        [-1, 1200, 2000, np.inf],
        labels=["< 1200", "1200 to 2000", "> 2000"],
    ).astype("category")

    df["income_hh_group"] = pd.cut(
        df["net_income_hh_eqv"],
        [-1, 1500, 2500, np.inf],
        labels=["< 1500", "1500 to 2500", "> 2500"],
    ).astype("category")

    df["health_group"] = df["health_general"].replace(
        {"poor": "moderate", "excellent": "very good"}
    )
    df["health_group"] = pd.Categorical(
        df["health_group"], ["moderate", "good", "very good"], ordered=True
    )

    df["age_bins"] = pd.cut(
        df["age"],
        [10, 25, 35, 45, 55, 65, 75, 120],
        ["<25", "25 to 35", "35 to 45", "45 to 55", "55 to 65", "65 to 75", ">75"],
    )

    return df


def create_weighting(raw_df):
    """Create weights based on demographics (age, gender, civil_status)

    Args:
        raw_df (DataFrame): Original data

    Returns:
        DataFrame: Original data including the new weights
    """
    # Define weighting variables
    weighting_vars = ["age", "gender", "civil_status"]

    # Load distribution of demographics in population
    age_bins, population_dist = load_population_dist(weighting_vars)

    # Prepare LISS data set
    df = raw_df[weighting_vars]

    # For pre-covid period, take first observation of next periods
    df = df.groupby("personal_id").bfill()

    df = df.dropna().query("age >= 18").copy()
    df.loc[df["age"] > 99, "age"] = 99
    df["age"] = pd.cut(df["age"], age_bins)
    df["civil_status"] = df["civil_status"].replace({"Separated": "Married"})

    # Calculate distribution in sample and weights for each period
    weights_by_period = {}
    for period in df.index.unique("period"):
        sample = df.xs(period, level="period")
        sample_dist = sample.groupby(weighting_vars).size() / len(sample)

        # Check that all observed combinations of demographics are
        # in the population data set
        for i in range(len(sample_dist.index.names)):
            for value in sample_dist.index.unique(level=i):
                assert value in population_dist.index.unique(level=i), f"{value}"
        weights = (population_dist / sample_dist.loc[sample_dist != 0]).dropna()
        weights.name = "age_sex_marital_weighting"
        weights_by_period[period] = weights

    # Aggregate weights and merge to LISS data
    weights = pd.concat(weights_by_period)
    out = df.join(weights, on=["period"] + weighting_vars)
    out = out["age_sex_marital_weighting"]

    return raw_df.join(out)


def load_population_dist(weighting_vars):
    """Load distribution of demographics in the population

    Args:
        weighting_vars (list): variables used for the weighting

    Returns:
        Series: population distribution
    """
    # Load distribution of demographics in population
    population_dist = pd.read_csv(
        IN_SPECS_CORONA / "weights_real_nl.csv", sep=";"
    ).set_index("Unnamed: 0")
    population_dist.columns = population_dist.columns.str.split("_", expand=True)
    population_dist = population_dist.stack(level=0).stack()
    population_dist.index.names = weighting_vars

    # Adjust variables to LISS notation
    age_bins = [17, 30, 40, 50, 60, 70, 80, 90, 1000]
    population_dist = population_dist.reset_index()
    population_dist["civil_status"] = population_dist["civil_status"].replace(
        {
            "unmarried": "Never been married",
            "married": "Married",
            "widowed": "Widow or widower",
            "divorced": "Divorced",
        }
    )
    population_dist["gender"] = population_dist["gender"].replace(
        {"men": "Male", "women": "Female"}
    )
    population_dist["age"] = pd.cut(population_dist["age"], age_bins)
    population_dist = population_dist.set_index(weighting_vars).iloc[:, 0]

    # Take sum over all ages in any age group
    population_dist = population_dist.groupby(weighting_vars).sum()
    return age_bins, population_dist


def _fix_nans(x):
    if pd.isna(x):
        return np.nan
    else:
        return x


def _check_for_two_types_of_missing(df):
    # Make sure columns contain only one type of missing
    for col in df.columns:
        pd_na = any(x is pd.NA for x in list(df[col].unique()))
        np_na = any(x is pd.NA for x in list(df[col].unique()))
        if pd_na & np_na:
            print(
                f"{col} contains two types of nans. Will be fixed. Should be checked!"
            )
            df[col] = df[col].map(lambda x: _fix_nans(x))
    return df


def cat_to_float(sr):
    if is_categorical(sr):
        res = sr.cat.codes.replace({-1: np.nan}).astype(float)
    else:
        res = sr
    return res


def create_and_export_combined_data_description(df_corona, df_other):
    # ToDO: not used at the moment anymore, but could be interesting in the future
    df_other = df_other.dropna(subset=["new_name"]).copy()
    df_common = pd.concat([df_corona.copy(), df_other], axis=0)
    df_common.to_csv(
        OUT_DATA_CORONA_PREP / "covid19_data_description_all_vars.csv", sep=";"
    )
