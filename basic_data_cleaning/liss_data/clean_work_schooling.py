"""
This file contains all cleaning tools for the
work and schooling dataset
"""
import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import convert_time_cols
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_work_schooling(panel):

    rename_df = pd.read_csv(
        IN_SPECS_LISS / "006-work-and-schooling_renaming.csv",
        sep=";",
    )

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_LISS / "006-work-and-schooling_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)
    panel = _replace_values_work_schooling(panel, replace_dict, rename_df)

    # Set types of variables using renaming file.
    panel = set_types_file(
        panel=panel, rename_df=rename_df, cat_sep="|", int_to_float=True
    )

    # Logical cleaning of work schooling
    panel = _clean_logically_work_schooling(panel)

    # Check some consistency in the data.
    _check_work_schooling(panel)

    return panel


def _replace_values_work_schooling(panel, replace_dict, rename_df):
    out = panel.copy()

    # Replace values using dictionary.
    out = replace_values(out, replace_dict, rename_df)

    # Convert time cols
    out = convert_time_cols(out, ["start_time", "end_time"])

    # Specific changes
    out = _convert_binary(out)

    return out


def _clean_logically_work_schooling(panel):
    """Clean some of the data logically

    Args:
        panel(pandas.DataFrame): The data frame to be cleaned.

    Returns:
        pandas.DataFrame: The logically cleaned data frame.
    """
    out = panel

    # Drop observations where the ending time is NA
    # out = out[~out["end_time"].isna()]

    return out


def _check_work_schooling(panel):
    """Check some of the data in the work_schooling database.

    Args:
        panel(pandas.DataFrame): The data frame to be checked.
    """
    out = panel.copy()
    general_data_checks(out)


def _automatic_replacement(panel, num_str_categorical=25):
    """
    This function automatically replaces strings in columns with
    large number of distinct float values!
    Most of these should be done in the renaming step already!
    """

    out = panel
    for col in out.columns:
        if out[col].dtype.name == "object":
            # Create some information that we would want to know
            float_vals = [x for x in out[col].unique() if type(x) == float]
            if len(float_vals) > num_str_categorical:
                out[col] = out[col].replace(
                    {x: np.nan for x in out[col].unique() if type(x) == str}
                )
    return out


def _convert_binary(df):
    """
    Convert yes/no to numerical categories!
    """
    out = df
    for col in out.columns:
        is_binary = _check_binary(out[col])
        if is_binary:
            out[col] = out[col].map({"no": 0.0, "yes": 1.0}).astype("float")
    return out


def _convert_string_ranges(panel, cols):
    """
    Convert range variables to numeric
    """
    renaming_dict = {
        "less than 1000 euros": 500,
        "less than 2,500 euros": 1250,
        "between 1000 and 2000 euros": 1500,
        "between 2000 and 3000 euros": 2500,
        "more than 3000 euros": 3000,
        "between 2,500 and 5,000 euros": 3750,
        "between 5,000 and 10,000 euros": 7500,
        "between 10,000 and 15,000 euros": 12500,
        "between 15,000 and 20,000 euros": 17500,
        "between 20,000 and 30,000 euros": 25000,
        "between 30,000 and 40,000 euros": 35000,
        "between 40,000 and 50,000 euros": 45000,
        "between 50,000 and 75,000 euros": 62500,
        "between 75,000 and 100,000 euros": 87500,
        "between 100,000 and 125,000": 112500,
        "between 100,000 and 125,000 euros": 112500,
    }
    out = panel

    for col in cols:
        out[col] = out[col].replace(renaming_dict)

    return out


def _replace_float_nan(panel, cols):
    out = panel
    for x in cols:
        out[x] = out[x].replace(
            {x: np.nan for x in out[x].unique() if type(x) == float}
        )
    return out


def _check_binary(col):
    values = list(col.value_counts().index)
    if (
        (("yes" in values and "no" in values) and len(values) == 2)
        or (
            (("yes" in values or "no" in values) and (0.0 in values or 1.0 in values))
            and len(values) <= 4
        )
        or (("yes" in values or "no" in values) and len(values) == 1)
    ):
        return True
    else:
        return False
