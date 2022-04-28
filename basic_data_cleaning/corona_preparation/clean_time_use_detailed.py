"""Clean further time use.

The main purpose here is to remove extreme and implausible values
and make sure that the answers are approximately consistent.

It focuses on 11-2019 time use and 4-2020 time use core variables.


"""
import warnings

import numpy as np
import pandas as pd
from config import OUT_DATA_CORONA_PREP

# Dictionary of columns with minimal, maximal hours, extreme outliers
hour_cols_2020 = {
    "hours_workplace": [0, 80, 120],
    "hours_home_office_no_kids": [0, 80, 120],
    "hours_home_office_kids_care": [0, 80, 120],
    "hours_commute": [0, 40, 120],
    "hours_homeschooling": [0, 40, 120],
    "hours_childcare": [0, 120, 140],
    "hours_help_parents": [0, 60, 120],
    "hours_chores": [0, 80, 120],
    "hours_resting": [30, 168, 168],
    "hours_schooling": [0, 80, 120],
    "hours_leisure_alone": [0, 100, 120],
    "hours_leisure_friends": [0, 100, 120],
    "hours_leisure": [0, 100, 120],
    "hours_other_activity": [0, 100, 120],
}
exceptions_2020 = [
    "hours_home_office_kids_care",
    "hours_homeschooling",
    "hours_childcare",
]
hour_cols_2019 = {
    "hours_work": [0, 80, 120],
    "hours_commute": [0, 40, 120],
    "hours_childcare": [0, 120, 140],
    "hours_help_parents": [0, 60, 120],
    "hours_help_family": [0, 60, 120],
    "hours_help_other": [0, 60, 120],
    "hours_chores": [0, 80, 120],
    "hours_resting": [30, 168, 168],
    "hours_schooling": [0, 80, 120],
    "hours_leisure": [0, 100, 120],
    "hours_other_activity": [0, 100, 120],
}
exceptions_2019 = ["hours_childcare"]

# Dictionary lower bound for total number of hours depending on the hours
# columns that were filled out, 1: first column, 2: first and second column
# etc.
cutoffs_low_missing_2020 = {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
    7: 0,
    8: 10,
    9: 60,
    10: 60,
    11: 60,
    12: 60,
    13: 80,
    14: 150,
}
cutoffs_low_missing_2019 = {
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
    6: 0,
    7: 10,
    8: 60,
    9: 60,
    10: 80,
    11: 150,
}


def get_baseline(df, newvar, oldvar, baseline="2020-02-01"):
    """Generate variable that contains before Covid values for all periods.
    Example: want to have variable that contains hours_total from before
             Covid-19 at all points in time.
    Args:
        df (pd.DataFrame)
        newvar (str): name of the variable to be generated
        oldvar (str): name of the variable out of which the new variable
                      shall be generated.
        baseline (str): data of the baseline
    Return:
        original dataframe + newvar
    """
    base = df.index.get_level_values("month") == baseline
    var = df.loc[base, oldvar].reset_index().set_index("personal_id").copy()
    var.rename(columns={oldvar: newvar}, inplace=True)
    var = var[newvar].copy()
    return df.join(var)


def reindex_time_use(time_use, month):
    """Reindex time use to month instead of year index."""
    time_use = time_use.copy()

    # Take in month
    time_use["month"] = month

    # Fix index of time use
    time_use = time_use.reset_index().set_index(["personal_id", "month"])

    # Drop old index
    time_use = time_use.drop("period", axis=1)

    return time_use


def is_systematically_incomplete(row, hour_cols, exceptions):
    """Check whether observation only filled in part of the hours.

    Returns:
        - False, 0 if all columns (except exceptions) are non-missing,
        - False and some number > 0, if some columns are missing, but not in
            not in the order they were asked.
        - True and some number > 0, if the first column that is missing is
            followed by all mising columns.

    Args:
        row of data frame
        hour_cols (list): hour columns that were filled out in
                          the respective year in their correct order.
        exceptions (list): subset of hour_cols that was not filled out be
                           everyone

    Return:
        list:
            boolean: systematically incomplete?,
            float: number of non-missing columns

    """
    row = row.copy()
    colus = [hrs for hrs in hour_cols if hrs not in exceptions]

    # Get all missing columns that are not supposed to be missing
    missing_cols = [c for c in colus if np.isnan(row[c])]

    # Generate output variables
    systematically_incomplete = False
    number_missing = len(missing_cols)

    # Check whether the first missing is followed by all missing
    if len(missing_cols) != 0:
        # Get the first column that is missing
        first_missing = missing_cols[0]

        # Get the columns following the first missing incl. the first missing
        ind = colus.index(first_missing)
        num_total_colus = len(colus)
        following_colus = colus[ind:num_total_colus]

        # If all following the first missing are missing, then they are syst
        # missing
        if following_colus == missing_cols:
            systematically_incomplete = True

    return systematically_incomplete, len(hour_cols) - number_missing


def replace_maximum_with_nan(row):
    """Replace the hrs column with the highest value with missing.

    Args:
        row (pd.Series): row of data with hours columns already selected

    Return:
        row with new values

    """
    row = row.copy()
    argm = row.idxmax()
    row[argm] = np.nan

    return row


def winsorize_outlier(data, hour_dict):
    """Winsorize values according to hour_dict.

    Args:
        data (pd.DataFrame)
        hour_dict (dict): keys are column names values, are lists of at least
                          length 2 containing cutoff values of column

    Return:
        data winsorized according to hour_dict.

    """
    data = data.copy()

    for hrs, cutoffs in hour_dict.items():

        lower = cutoffs[0]
        upper = cutoffs[1]

        assert lower < upper, "lower bound is larger than upper bound"

        lower_bound = data[hrs] < lower
        upper_bound = data[hrs] > upper
        either = lower_bound | upper_bound

        data.loc[lower_bound, hrs] = lower
        data.loc[upper_bound, hrs] = upper

        # Rescale all other columns
        other_hours = [col for col in hour_dict.keys() if col != hrs]
        rescaled = rescaling(data, other_hours, sum_hours=168 - upper)
        data.loc[upper_bound, other_hours + ["rescaled_hrs"]] = rescaled.loc[
            upper_bound, other_hours + ["rescaled_hrs"]
        ]

        # Generate imputation flag
        data[hrs + "_imputed"] = False
        data.loc[either, hrs + "_imputed"] = True
        data[hrs + "_imputed"] = data[hrs + "_imputed"].astype(float)

        month = data.reset_index()["month"].unique()[0].astype(str)[0:10]
        warnings.warn(
            f"{month}: Winsorize {either.sum()} values"
            "at {lower} and {upper} hours in column {hrs}"
        )

    # Calculate the number of imputed values
    impute_cols = [hrs + "_imputed" for hrs in hour_dict.keys()]
    data["number_imputed_values_tu"] = data[impute_cols].sum(axis=1)

    return data


def remove_extreme_outlier(data, col, hour_dict, up=True):
    """Set extrem outlier to missing."""
    data = data.copy()
    hour_cols = [*hour_dict]
    cutoffs = hour_dict[col]

    condition = data[col] > max(cutoffs) if up else data[col] < min(cutoffs)
    drop = condition.sum()

    if drop > 0:
        month = data.reset_index()["month"].unique()[0].astype(str)[0:10]
        warnings.warn(
            f"{month}: Set {drop} obs to missing because of extreme values in {col}."
        )
        for hrs in hour_cols:
            data.loc[condition, hrs] = np.nan

    return data


def rescaling(data, hour_cols, sum_hours=168):
    """Rescale so that sum of hours is always 168."""
    data = data.copy()
    data["tot_hours"] = data[hour_cols].sum(axis=1)
    data.loc[data[hour_cols].isna().all(axis=1), "tot_hours"] = np.nan

    # Rescaling
    condition = data.tot_hours != sum_hours
    data.loc[condition, "rescaled_hrs"] = True

    for hrs in hour_cols:
        data.loc[condition, hrs] = (
            data.loc[condition, hrs] / data.loc[condition, "tot_hours"] * sum_hours
        )

    return data


def clean_hours_vars(data, hour_dict):
    """Cleaning according to single column cutoffs."""
    data = data.copy()
    data["rescaled_hrs"] = False

    # Too high values in variables
    for hrs in [*hour_dict]:
        data = remove_extreme_outlier(data, hrs, hour_dict)

    # Winsorize medium extreme values
    data = winsorize_outlier(data, hour_dict)

    # Rescaling
    data = rescaling(data, [*hour_dict])

    # Drop those that are again over the cutoff, but use winsorize cutoff
    new_hour_dict = {c: hour_dict[c][0:2] for c in hour_dict.keys()}

    for hrs in [*new_hour_dict]:
        data = remove_extreme_outlier(data, hrs, new_hour_dict)

    return data


def generate_additional_variables(data):
    """Sum up some variables and get baseline values of some variables.

    Run after appending 2019 and 2020.

    """
    data = data.copy()

    # Generate aggregated variables
    work_hours = [
        "hours_workplace",
        "hours_work",
        "hours_home_office_no_kids",
        "hours_home_office_kids_care",
    ]
    data["hours_work_total"] = data[work_hours].sum(axis=1, min_count=1)

    childcare = [
        "hours_childcare",
        "hours_homeschooling",
        "hours_home_office_kids_care",
    ]
    data["hours_childcare_total"] = data[childcare].sum(axis=1, min_count=1)

    childcare_strict = ["hours_childcare", "hours_homeschooling"]
    data["hours_childcare_total_strict"] = data[childcare_strict].sum(
        axis=1, min_count=1
    )

    help_vars = ["hours_help_family", "hours_help_parents", "hours_help_other"]
    data["hours_help_total"] = data[help_vars].sum(axis=1, min_count=1)

    leisure_vars = [
        "hours_leisure",
        "hours_leisure_friends",
        "hours_leisure_alone",
        "hours_other_activity",
    ]
    data["hours_leisure_total"] = data[leisure_vars].sum(axis=1, min_count=1)

    # Get baseline values for 2019 variables
    hrs1 = [
        c
        for c in data.columns
        if c.startswith("hours") and not c.startswith("hours_cc")
    ]
    for hr in hrs1:
        data = get_baseline(data, hr + "_baseline", hr, baseline="2019-11-01")

    hrs2 = [c for c in data.columns if c.startswith("hours_cc")]
    for hr in hrs2:
        data = get_baseline(data, hr + "_baseline", hr)

    # Change variables
    for hr in hrs1 + hrs2:
        data["abs_change_" + hr] = data[hr] - data[hr + "_baseline"]
        data["rel_change_" + hr] = np.nan
        data.loc[(data[hr + "_baseline"] != 0), "rel_change_" + hr] = (
            data.loc[(data[hr + "_baseline"] != 0), "abs_change_" + hr]
            / data.loc[(data[hr + "_baseline"] != 0), hr + "_baseline"]
        )

    return data


def wrap_further_time_use_cleaning(time_use):
    """Function wrapping detailed time use cleaning used in some projects."""

    # Select data
    time_use_2019 = (
        time_use[time_use.index.get_level_values("period") == 201911]
        .dropna(how="all", axis=1)
        .copy()
    )
    time_use_20_02 = (
        time_use[time_use.index.get_level_values("period") == 202002]
        .dropna(how="all", axis=1)
        .copy()
    )
    time_use_20_04 = (
        time_use[time_use.index.get_level_values("period") == 202004]
        .dropna(how="all", axis=1)
        .copy()
    )
    time_use_20_11 = (
        time_use[time_use.index.get_level_values("period") == 202011]
        .dropna(how="all", axis=1)
        .copy()
    )

    # Reindex data sets
    time_use_2019 = reindex_time_use(
        time_use_2019, month=pd.Timestamp(year=2019, month=11, day=1)
    )
    time_use_20_02 = reindex_time_use(
        time_use_20_02, month=pd.Timestamp(year=2020, month=2, day=1)
    )
    time_use_20_04 = reindex_time_use(
        time_use_20_04, month=pd.Timestamp(year=2020, month=4, day=1)
    )
    time_use_20_11 = reindex_time_use(
        time_use_20_11, month=pd.Timestamp(year=2020, month=11, day=1)
    )

    # Clean hours vars
    out_2019 = clean_hours_vars(time_use_2019, hour_cols_2019)
    out_20_04 = clean_hours_vars(time_use_20_04, hour_cols_2020)
    out_20_11 = clean_hours_vars(time_use_20_11, hour_cols_2020)

    # Concat all together
    time_use = pd.concat([out_20_11, out_20_04, time_use_20_02, out_2019], axis=0)

    # Finally, generate some aggregate variables
    time_use = generate_additional_variables(time_use)
    time_use.to_pickle(OUT_DATA_CORONA_PREP / "time_use_data_detailed.pickle")

    # save data
    # try:
    #     time_use.to_parquet(path=ppj("OUT_DATA", "time_use_data_detailed.parquet"))
    # except:
    #     wrong_type = []
    #     colus = list(time_use.columns)
    #     colus.remove("hours_workplace")
    #     for col in colus:
    #         try:
    #             time_use[["hours_workplace", col]].to_parquet("test.parquet")
    #         except:
    #             wrong_type.append(col)
    #             print(
    #                 f"!! {col} has dtype incompatible with parquet and is set to categorical"
    #             )
    #     time_use[wrong_type] = time_use[wrong_type].astype(str).astype("category")

    # Dirty hack to get around integer object columns with missings
    # cols = (
    #     "hh_size",
    #     "systematically_incomplete",
    #     "rescaled_hrs",
    #     "hh_children",
    #     "questionnaire_difficult",
    #     "questionnaire_clear",
    #     "questionnaire_thinking",
    #     "questionnaire_interesting",
    #     "questionnaire_enjoy",
    #     "date_fieldwork",
    # )
    # for c in cols:
    #     time_use[c] = time_use[c].astype(float)

    # time_use.to_stata(path=ppj("OUT_DATA", "time_use_data_detailed.dta"))
