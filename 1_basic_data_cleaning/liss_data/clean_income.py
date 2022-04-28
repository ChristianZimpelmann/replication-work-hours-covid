"""
This file contains all cleaning tools for the
income dataset
"""
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import convert_time_cols
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_income(panel):

    rename_df = pd.read_csv(
        IN_SPECS_LISS / "010-economic-situation-income_renaming.csv",
        sep=";",
    )

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_LISS / "010-economic-situation-income_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    panel = _replace_values_income(panel, replace_dict, rename_df)

    # Set types of variables using renaming file.

    panel = set_types_file(
        panel=panel,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )
    # Logical cleaning of work schooling
    # panel = _clean_logically_income(panel)

    # Check some consistency in the data.
    _check_income(panel, replace_dict)

    return panel


def _replace_values_income(panel, replace_dict, rename_df):
    """Do some cleaning of the database by replacing and renaming some
    observations in the income database, and adding certain columns where
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

    # Replace values using dictionary.
    out = replace_values(out, replace_dict, rename_df)

    # Turn one variable in two.
    out["appliances_has_fixed_phone"] = out["appliances_has_phone"].replace(
        {
            "fixed line and a mobile phone": 1.0,
            "only a fixed line": 1.0,
            "only a mobile phone": 0.0,
            "no fixed line and mobile phone": 0.0,
        }
    )
    out["appliances_has_mobile_phone"] = out["appliances_has_phone"].replace(
        {
            "fixed line and a mobile phone": 1.0,
            "only a fixed line": 0.0,
            "only a mobile phone": 1.0,
            "no fixed line and mobile phone": 0.0,
        }
    )

    return out


def _check_income(panel, config):
    """Check some of the data in the work_schooling database.

    Args:
        panel(pandas.DataFrame): The data frame to be checked.
    """
    general_data_checks(panel, config=config)


def _convert_string_ranges(panel, cols):
    """
    Convert range variables to numeric and float
    """
    renaming_dict = {
        "less than 1,000 euros": 500,
        "less than 2,500 euros": 1250,
        "less than 4,000 euros": 2000,
        "1,000-3,000 euros": 2000,
        "2,500-5,000 euros": 3750,
        "less than 8,000 euros": 4000,
        "3,000-6,000 euros": 4500,
        "4,000-8,000 euros": 6000,
        "5,000-10,000 euros": 7500,
        "6,000-12,000 euros": 9000,
        "8,000-12,000 euros": 10000,
        "8,000-16,000 euros": 12000,
        "10,000-15,000 euros": 12500,
        "12,000-16,000 euros": 14000,
        "15,000-20,000 euros": 17500,
        "16,000-20,000 euros": 18000,
        "16,000-24,000 euros": 20000,
        "12,000-30,000 euros": 21000,
        "20,000-30,000 euros": 25000,
        "24,000-36,000 euros": 30000,
        "30,000-40,000 euros": 35000,
        "36,000-48,000 euros": 42000,
        "30,000-60,000 euros": 45000,
        "40,000-50,000 euros": 45000,
        "48,000-60,000 euros": 54000,
        "60,000 euros or more": 60000,
        "50,000-75,000 euros": 62500,
        "75,000 euros or more": 75000,
    }
    out = panel.copy()

    for col in cols:
        out[col] = out[col].replace(renaming_dict)
        out[col] = out[col].astype("float")

    return out
