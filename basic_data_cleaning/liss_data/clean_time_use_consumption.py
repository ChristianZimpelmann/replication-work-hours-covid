"""
"""
import math

import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import convert_time_cols
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks
from liss_data.utils_liss_data import merge_double_columns
from liss_data.utils_liss_data import update_double_columns


def clean_time_use_consumption(panel):
    # Update and merge columns.
    panel = _update_and_merge_columns(panel)

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_LISS / "034-time-use-and-consumption_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    rename_df = pd.read_csv(
        IN_SPECS_LISS / "034-time-use-and-consumption_renaming.csv",
        sep=";",
    )
    panel = _replace_values_time_use(panel, replace_dict, rename_df)

    # Set types of variables using renaming file.

    panel = set_types_file(panel=panel, rename_df=rename_df, int_to_float=True)

    # Logical cleaning of time use
    panel = _clean_logically_time_use(panel)

    # Check some consistency in the data.
    _check_time_use(panel, replace_dict)

    return panel


def _update_and_merge_columns(panel):
    """Merge and update different columns in the data that contain information
    that can be grouped into a single column without loss of information.

    Args:
        panel(pandas.DataFrame): The data frame to be converted.

    Returns:
        pandas.DataFrame: the data frame with the changes inplace.

    """
    out = panel.copy()
    out = update_double_columns(out)
    out = merge_double_columns(out)
    out = _merge_minutes(out)

    # Some column specific fixes - transforming in two variables
    out["partner"] = (
        out["cohabiting_partner"].isin(["yes", "ja"])
        | out["cohabiting_partner"].isin(
            [
                "no, I do not live together with my partner",
                "nee, ik heb geen vaste partner",
            ]
        )
    ).astype(int)

    return out


def _replace_values_time_use(panel, replace_dict, rename_df):
    """Do some cleaning of the database by replacing and renaming some
    observations in the time_use_consumption database, and adding certain
    columns where needed.

    Args:
        panel(pandas.DataFrame): The data frame to be converted.
        rename_dict(dict): Dictionary containing the information to replace the
            values in the database.

    Returns:
        pandas.DataFrame: the data frame with the changes inplace.
    """
    out = panel.copy()

    # Convert time cols
    out = convert_time_cols(out, ["start_time", "end_time"])

    # Clean all columns with days
    # ToDo: Specify this in replace yaml
    for col in [x for x in out.columns if x.startswith("days_")]:
        out[col] = out[col].replace({"niet van toepassing": np.nan}).astype(float)

    # Rename variables according to the renaming dictionary
    out = replace_values(out, replace_dict, rename_df)

    return out


def _check_time_use(panel, replace_dict):
    """Check some of the data in the time_use_consumption database.

    Args:
        panel(pandas.DataFrame): The data frame to be checked.
    """

    out = panel.copy()
    general_data_checks(out, replace_dict)


def _clean_logically_time_use(panel):
    """Clean some of the data logically.

    Args:
        panel(pandas.DataFrame): The data frame to be cleaned.

    Returns:
        pandas.DataFrame: The logically cleaned data frame.
    """
    out = panel.copy()

    # Missing consumption and childcare set to 0 if no children (and no answer)
    out = _no_children_no_childcare(
        out,
        [
            "hours_childcare",
            "expendit_child_eatoutside",
            "expendit_child_tobacco",
            "expendit_child_clothing",
            "expendit_child_personalcare",
            "expendit_child_medicalcare",
            "expendit_child_leisure",
            "expendit_child_schooling",
            "expendit_child_donations",
            "expendit_child_other",
            "expendit_child_total_sum",
            "expendit_child",
        ],
    )

    # Question not asked to non cohabitating partners
    out.loc[out.cohabiting_partner == 0, "hours_with_partner"] = 0

    # Drop observations where the ending time is NA
    out = out[~out["end_time"].isna()]

    # Drop observations where reported weekly hours is larger than 168.
    out = _cap_weekly_hours(out)

    # Drop observations that report less than 168 hours
    # (for the updated version of the questionnaire)
    out = out.set_index(["personal_id", "year"])
    out = out.drop((847164, 201911))
    out = out.reset_index()

    # Calculating the sum of expenditures since in some observations it does not
    # coincide with the one reported by the database
    out = _calculate_expendit_sum(out)

    return out


def _cap_weekly_hours(panel):
    """Cap values of weekly hours: The maximum is 168. 24 hours times 7 days.

    Args:
        panel (pandas.DataFrame): The data frame to be converted.

    Returns:
        pandas.DataFrame: the data frame without the observations that have
            more than `168` in any hour variable.
    """
    out = panel.copy()
    cols = [x for x in out.columns if x.startswith("hours_")]
    drop_list = []
    for col in cols:
        if not out.loc[out[col] > 168.0].empty:
            drop_values = out.loc[out[col] > 168.0].index.values
            drop_list.extend(drop_values)
    out.drop(drop_list, inplace=True)
    return out


def _no_children_no_childcare(panel, cols):
    """
    Set missing to 0 if no children and none of the respondants without children
    answered
    """
    out = panel.copy()

    for col in cols:
        if len(list(out[col][(panel.hh_children == 0)].unique())) == 1:
            out.loc[out.hh_children == 0, col] = 0
    return out


def _merge_minutes(panel):
    """
    Combine minutes and hours in the column with hours.
    """
    out = panel.copy()
    min_cols = [x for x in panel.columns if x.startswith("mins_")]
    for col in min_cols:
        out[f"hours_{col[5:]}"] = (
            out[f"hours_{col[5:]}"]
            + out[col].map(lambda x: 0 if math.isnan(x) is True else x) / 60
        )
    out = out.drop(columns=min_cols)
    return out


def _calculate_expendit_sum(panel):
    """Calculates expendit sum with expenditure columns

    Args:
        panel (pandas.DataFrame): The data frame to be converted.

    Returns:
        pandas.DataFrame: the data frame with a the new column
            calculated_expendit_sum.
    """
    out = panel.copy()

    cols = [
        "expendit_mortgage",
        "expendit_rent",
        "expendit_utilities",
        "expendit_transport",
        "expendit_insurance",
        "expendit_daycare",
        "expendit_financialsupport",
        "expendit_loans",
        "expendit_trips",
        "expendit_maintenance",
        "expendit_nutrition",
        "expendit_other",
        "expendit_eatoutside",
        "expendit_clothing",
        "expendit_gifts",
        "expendit_school",
        "expendit_medical",
        "expendit_software",
    ]

    out["calculated_expendit_sum"] = (out.loc[:, cols].sum(axis=1, skipna=True)).astype(
        "Int64"
    )

    return out
