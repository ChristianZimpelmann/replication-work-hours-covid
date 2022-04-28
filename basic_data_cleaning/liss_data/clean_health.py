import functools

import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import convert_time_cols
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_health(panel):

    rename_df = pd.read_csv(
        IN_SPECS_LISS / "002-health_renaming.csv",
        sep=";",
    )

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_LISS / "002-health-replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    panel = _replace_values_health(panel, replace_dict, rename_df)

    # Set types of variables using renaming file.

    panel = set_types_file(
        panel=panel,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )

    panel = _additional_variables(panel)

    general_data_checks(panel, replace_dict)

    return panel


def _replace_values_health(panel, replace_dict, rename_df):
    """Do some cleaning of the database by replacing and renaming some
    observations in the health database, and adding certain columns where
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
    out = out.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Convert time cols
    out = convert_time_cols(out, ["questionnaire_start_time", "questionnaire_end_time"])

    # Replace values using dictionary.
    out = replace_values(out, replace_dict, rename_df)

    return out


def _convert_string_ranges(data, columns):
    """
    Convert string ranges to numeric.
    """
    string_range = {
        "I have no voluntary own risk": np.nan,
        "0 euro": 0,
        "100 euros": 100,
        "200 euros": 200,
        "300 euros": 300,
        "400 euros": 400,
        "500 euros": 500,
        "don't know": np.nan,
    }
    range_data = data.copy()
    for column in columns:
        range_data[column] = range_data[column].replace(string_range)

    return range_data


#
#
# def _convert_dtypes(df, num_str_categorigal=45):
#     """
#     This function assigns new dtypes accroding to the follwing logic:
#     - If the col contains no float and no str-float and has less than 20 values
#       it is coverted to category otherwise left at object!
#     - If the col contains only float or str float in either range(11) or range(1990,2025)
#       it is converted to categorical numeric
#     - If the col only contains floats it is converted to numeric!
#     In other cases a warning is raised! Since we do not want these cases to happen!
#     """
#     out = df.copy()
#     for col in out.columns:
#         if out[col].dtype.name == "object":
#             contains_float = _check_for_float(out[col].unique())
#             contains_string_float = _check_for_str_number(out[col].unique())
#
#             # Convert string only cols to cat if they have few labels
#             if (
#                 contains_string_float is False
#                 and len(out[col].unique()) <= num_str_categorigal
#             ):
#                 out[col] = out[col].astype("category")
#
#             # Convert cols to cat that contain only floats/str in range(11)
#             elif contains_string_float in ["categorical", "years"]:
#                 out[col] = out[col].astype("float").astype("category")
#
#             # Convert float only strings to numerical
#             elif contains_float == "all":
#                 out[col] = out[col].astype("float")
#
#             # Print the rest and maybe inlcude warning for weird cols
#             elif contains_float == "some" or contains_string_float == "some":
#
#                 # Todo: Remove this if statement as soon as is taken care of
#                 # these two variables somewhere
#                 # if col not in [
#                 #     "questionnaire_start_time",
#                 #     "questionnaire_end_time",
#                 # ]:
#                     warnings.warn(
#                         f"{col} contains bad combination of values! Either "
#                         "further cleaning is required or an error occured",
#                         UserWarning,
#                     )
#
#     return out


# def _check_for_str_number(values):
#     """
#     Check for str floats in list of values
#     """
#     out = []
#     values = [x for x in values if str(x) != "nan"]
#
#     for x in values:
#         try:
#             out.append(float(x))
#         except (KeyboardInterrupt, SystemExit):
#             raise
#         except ValueError:
#             continue
#     if len(out) == len(values) and all(x in range(11) for x in out):
#         return "categorical"
#     elif len(out) == len(values) and all(x in range(1990, 2025) for x in out):
#         return "years"
#     elif len(out) > 0:
#         return "some floats/str numbers"
#     else:
#         return False

#
# def _check_for_float(values):
#     """
#     Check for presence of floats in list
#     """
#     values = [x for x in values if str(x) != "nan"]
#     if all(type(x) == float for x in values):
#         return "all"
#     elif any(type(x) == float and x != np.nan for x in values):
#         return "some"
#     else:
#         return False


def _additional_variables(panel):
    cols = ["feel_anxious", "feel_down", "feel_calm", "feel_depressed", "feel_happy"]

    panel["mhi5"] = _create_mhi5(data=panel, cols=cols)
    return panel


def _create_mhi5(data, cols):
    """Create mhi 5. TOBE PLACED in utils!"""

    for col in cols:
        assert data[col].cat.ordered

    out = functools.reduce(
        lambda x, y: x + y, [data[col].cat.codes.replace({-1: np.nan}) for col in cols]
    )

    return 4 * out
