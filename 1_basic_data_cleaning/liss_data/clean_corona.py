"""Clean the first questionnaire on the covid-19 epidemic in 2020."""
import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import convert_time_cols
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks
from liss_data.utils_liss_data import clean_background_vars
from liss_data.utils_liss_data import merge_double_columns

# from data_management.utils import check_columns_only_nan


def clean_corona(panel):
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "xyx-corona-questionnaire_renaming.csv",
        sep=";",
    )

    # Update and merge columns.
    panel = _update_and_merge_columns(panel)

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_LISS / "xyx-corona-questionnaire_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    panel = _replace_values_corona(panel, replace_dict, rename_df)

    # Set types of variables using renaming file.
    panel = set_types_file(
        panel=panel,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
        scale_as_category=True,
    )

    # Logical cleaning
    panel = _clean_logically_corona(panel)

    # Check some consistency in the data.
    _check_corona(panel, replace_dict)

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

    # Merge double columns
    out = merge_double_columns(out)

    # Kick out columns that contain only nans!
    out = out.loc[:, ~out.isnull().all(axis=0)]
    return out


def _replace_values_corona(panel, replace_dict, rename_df):
    """Do some cleaning of the database by replacing and renaming some
    observations in the corona database, and adding certain columns where
    needed.

    Args:
        panel(pandas.DataFrame): The data frame to be converted.
        rename_dict(dict): Dictionary containing the information to replace the
            values in the database.
        rename_df(pandas.DataFrame): The renaming dataframe taken from the
            renaming file.

    Returns:
        pandas.DataFrame: the data frame with the changes inplace.
    """
    out = panel.copy()

    # Convert time cols
    out = convert_time_cols(out, ["start_time", "end_time"])

    # Make some general replacements
    non_numerical_cols = [c for c in out if out[c].dtype not in ["float", "int"]]
    replacement_cols = [c for c in non_numerical_cols if not c.startswith("self_used")]
    out[replacement_cols] = out[replacement_cols].replace(
        {
            "": np.nan,
            "Ja": True,
            "Nee": False,
            "ja": True,
            "nee": False,
            "Heel veel vertrouwen": "5 a lot of confidence",
            "Helemaal geen vertrouwen": "1 no confidence at all",
            "Nee, helemaal niet": "1 no, not at all",
            "Ja, heel goed": "5 yes, totally",
        }
    )

    # Replace values using dictionary.
    out = replace_values(out, replace_dict, rename_df)
    # Clean demographic variables
    out = clean_background_vars(out)

    # Clean memory and forward looking variable
    for var in "hist_perf", "forw_look":
        for i in range(1, 4):
            out[f"{var}_e{i}_nocheck"] /= 100
            out[f"{var}_e{i}"] /= 100
            out[f"{var}_e{i}_combined"] = out[f"{var}_e{i}"].where(
                out[f"{var}_e{i}"].notnull(), out[f"{var}_e{i}_nocheck"]
            )
        out[f"{var}_e0_nocheck"] = out[f"{var}_e0_nocheck"] / 100

    return out


def _clean_logically_corona(panel):
    """Clean some of the data logically

    Args:
        panel(pandas.DataFrame): The data frame to be cleaned.

    Returns:
        pandas.DataFrame: The logically cleaned data frame.
    """
    out = panel.copy()

    # Drop observations where the ending time is NA
    out = out[~out["end_time"].isna()]

    return out


def _check_corona(panel, config):
    """Check some of the data in the work_schooling database.

    Args:
        panel(pandas.DataFrame): The data frame to be checked.
    """
    general_data_checks(panel, config=config)
