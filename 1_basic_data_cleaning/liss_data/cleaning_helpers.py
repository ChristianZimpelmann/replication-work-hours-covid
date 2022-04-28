"""
This file contains three general cleaning functions:
replace_values, set_types_file
"""
import datetime
import math
import warnings
from inspect import currentframe
from inspect import getframeinfo

import numpy as np
import pandas as pd
from liss_data.utils_liss_data import send_warnings_to_log as swtl
from pandas.api.types import infer_dtype


def replace_values(panel, replace_dict, rename_df, raise_if_missing_vars=True):
    """Replace and rename values using the replace dictionary.

    Args:
        panel (pandas.DataFrame): The dataframe which values need to be
            replaced or renamed.
        replace_dict (dictionary): The replacing dictionary.
        rename_df (pandas.DataFrame): The renaming dataframe taken from the
            renaming file.
        raise_if_missing_vars (bool): Raise error if specified variables are missing

    Returns:
        pandas.DataFrame: The dataframe with the replaced or renamed values.

    """

    out = panel.copy()
    # Convert some columns to lower case
    if "mixed_case" in replace_dict and replace_dict["mixed_case"]:

        # Raise error if not all specified variables are in the DataFrame
        mixed_case = [c for c in replace_dict["mixed_case"] if c in out]
        mixed_case_mi = [c for c in replace_dict["mixed_case"] if c not in out]
        if raise_if_missing_vars and len(mixed_case_mi) > 0:
            raise ValueError(f"{mixed_case_mi} are missing in the DataFrame")

        out[mixed_case] = out[mixed_case].apply(lambda x: x.str.lower())

    # Convert numeric columns
    if "numeric" in replace_dict and replace_dict["numeric"]:

        # Raise error if not all specified variables are in the DataFrame
        numeric = [c for c in replace_dict["numeric"] if c in out]
        numeric_mi = [c for c in replace_dict["numeric"] if c not in out]
        if raise_if_missing_vars and len(numeric_mi) > 0:
            raise ValueError(f"{numeric_mi} are missing in the DataFrame")

        out[numeric] = out[numeric].apply(lambda x: pd.to_numeric(x, errors="coerce"))

    # Rename variables according to their types.
    if "type renaming" in replace_dict:

        rename_df["type"] = rename_df["type"].replace(
            {
                "int": "Int64",
                "float": "float64",
                "bool": "boolean",
                "Categorical": "category",
                "Int": "Int64",
            }
        )

        for group in replace_dict["type renaming"] and replace_dict["type renaming"]:
            filter = rename_df["type"] == group
            cols = rename_df.copy()[filter]["new_name"].values

            # Raise error if not all specified variables are in the DataFrame
            cols_restr = [c for c in cols if c in out]
            cols_mi = [c for c in cols if c not in out]
            if raise_if_missing_vars and len(cols_mi) > 0:
                raise ValueError(f"{cols_mi} are missing in the DataFrame")

            for col in cols_restr:
                try:
                    out[col] = out[col].replace(replace_dict["type renaming"][group])
                except Exception:
                    frameinfo = getframeinfo(currentframe())
                    module_name = frameinfo.filename
                    lineno = frameinfo.lineno - 1
                    message = f"issue with {col}"
                    warnings.warn(message)
                    swtl(message=message, module_name=module_name, lineno=lineno)
                    continue

    # Rename variables according to the renaming dictionary
    if "replacing" in replace_dict and replace_dict["replacing"]:
        for _i in replace_dict["replacing"]:
            if _i != "full_df":
                if _i in out:
                    try:
                        out[_i].replace(replace_dict["replacing"][_i], inplace=True)
                    except TypeError:
                        frameinfo = getframeinfo(currentframe())
                        module_name = frameinfo.filename
                        lineno = frameinfo.lineno - 1
                        message = f"type issue with {_i}"
                        warnings.warn(message)
                        swtl(message=message, module_name=module_name, lineno=lineno)
                else:
                    if raise_if_missing_vars:
                        raise ValueError(f"{_i} is missing in the DataFrame")

            else:
                try:
                    out.replace(replace_dict["replacing"][_i], inplace=True)
                except TypeError:
                    frameinfo = getframeinfo(currentframe())
                    module_name = frameinfo.filename
                    lineno = frameinfo.lineno - 1
                    message = f"type issue with {_i}"
                    warnings.warn(message)
                    swtl(message=message, module_name=module_name, lineno=lineno)

    # Rename variables in multiple columns.
    if "multicolumn" in replace_dict and replace_dict["multicolumn"]:
        for _j in replace_dict["multicolumn"]:

            # Raise error if not all specified variables are in the DataFrame
            cols = replace_dict["multicolumn"][_j]["columns"]
            cols_restr = [c for c in cols if c in out]
            cols_mi = [c for c in cols if c not in out]
            if raise_if_missing_vars and len(cols_mi) > 0:
                raise ValueError(f"{cols_mi} are missing in the DataFrame")

            try:
                out.loc[:, cols_restr] = out.loc[:, cols_restr].replace(
                    replace_dict["multicolumn"][_j]["dictionary"]
                )
            except Exception:
                frameinfo = getframeinfo(currentframe())
                module_name = frameinfo.filename
                lineno = frameinfo.lineno - 1
                message = f"error in {replace_dict['multicolumn'][_j]}"
                warnings.warn(message)
                swtl(message=message, module_name=module_name, lineno=lineno)
    out = _fix_nas(out)

    return out


def set_types_file(
    panel,
    rename_df,
    cat_sep=", ",
    int_to_float=True,
    bool_to_float=True,
    num_str_categorical=18,
    scale_as_category=True,
    few_int_to_cat=True,
):
    """Assign types to the columns in `panel` using the renaming file.

    Args:
        panel (pandas.DataFrame): The dataframe which types need to be
            assigned.
        rename_df (pandas.DataFrame): The renaming dataframe taken from the
            renaming file.
        cat_sep (string): The separator of the categories in the file.
        int_to_float (boolean): True if values specified as int should be coded
            as float.
        bool_to_float (boolean): True if values specified as boolean should be
            coded as float.
        num_str_categorical (int): Number of unique values for inferance as
            category
        few_int_to_cat (boolean): True if variable with only a few int values
            should be converted to categorical.

    Returns:
        pandas.DataFrame: The dataframe with the new types assigned.

    """
    out = panel.copy()

    if "type" in rename_df.columns:
        out = _set_types_file_with_file(
            panel=out,
            rename_df=rename_df,
            cat_sep=cat_sep,
            int_to_float=int_to_float,
            bool_to_float=bool_to_float,
            num_str_categorical=num_str_categorical,
            scale_as_category=scale_as_category,
        )
    else:
        for var in out.columns.values:
            out.loc[:, var] = _set_inferred_types(
                out[var],
                int_to_float=int_to_float,
                bool_to_float=bool_to_float,
                num_str_categorical=num_str_categorical,
                few_int_to_cat=few_int_to_cat,
            )
    for i in ["personal_id", "year"]:
        if i in out:
            out[i] = out[i].astype("int")

    return out


def _set_inferred_types(
    col,
    num_str_categorical=18,
    int_to_float=False,
    bool_to_float=False,
    few_int_to_cat=True,
):
    out_col = col.copy()
    inf_type = infer_dtype(out_col, skipna=True)
    expected_type = None
    if inf_type in ("string", "mixed-integer", "mixed"):
        try:
            out_col = pd.to_numeric(out_col)
            inf_type = infer_dtype(out_col)
        except ValueError:
            if len(col.unique()) <= num_str_categorical:
                expected_type = "category"
            else:
                expected_type = "object"

    if inf_type in ("floating", "mixed-integer-float", "integer"):

        # Check if all values are integer
        if all(
            isinstance(x, (int, np.integer)) or x.is_integer()
            for x in out_col.dropna().unique()
        ):

            # Dummy variable (only 0 and 1)
            if sorted(out_col.dropna().unique()) == [0, 1]:
                expected_type = "float64" if bool_to_float else "boolean"

            # limited number of integer values (potentially convert to cat)
            elif few_int_to_cat and (
                all(x in range(11) for x in out_col.dropna().unique())
                or all(x in range(1990, 2030) for x in out_col.dropna().unique())
            ):
                expected_type = "category"
                category_ordered = True
                category_labels = sorted(out_col.dropna().unique())

            # all other cases
            else:
                expected_type = "float64" if int_to_float else "Int64"
        else:
            expected_type = "float64"
    elif inf_type == "boolean":
        expected_type = "float64" if bool_to_float else "boolean"
    elif inf_type == "categorical":
        expected_type = "category"

    elif pd.isnull(expected_type) or inf_type in ("mixed"):
        frameinfo = getframeinfo(currentframe())
        module_name = frameinfo.filename
        lineno = frameinfo.lineno - 1
        message = (
            f"{out_col.name} contains bad combination of values! Either"
            " further cleaning is required or an error occured"
        )
        swtl(message=message, module_name=module_name, lineno=lineno)
        warnings.warn(
            message,
            UserWarning,
        )
        out_col = out_col.astype("object")
    try:
        if expected_type == "categorical" and category_labels:
            out_col = pd.Categorical(out_col, category_labels, category_ordered)
        else:
            out_col = out_col.astype(expected_type)

    except Exception:
        frameinfo = getframeinfo(currentframe())
        module_name = frameinfo.filename
        lineno = frameinfo.lineno - 1
        message = f"{out_col.name} cannot be converted to inferred type."
        swtl(message=message, module_name=module_name, lineno=lineno)
        warnings.warn(
            message,
            UserWarning,
        )
    return out_col


def _fix_nas(df):
    # Make sure columns contain only one type of missing
    np_na = df.isin([np.nan]).any(axis=0)
    pd_na = df.isin([pd.NA]).any(axis=0)
    missing_both = np_na & pd_na
    if missing_both.any():
        df.loc[:, missing_both] = df.loc[:, missing_both].apply(
            lambda x: np.array([_fix_nans(y) for y in x]), axis=0
        )
    return df


def _fix_nans(x):
    if pd.isna(x):
        return np.nan
    else:
        return x


def _set_types_file_with_file(
    panel,
    rename_df,
    cat_sep=", ",
    int_to_float=True,
    bool_to_float=True,
    num_str_categorical=18,
    scale_as_category=True,
):
    """Assign types to the columns in `panel` using the renaming file.

    Args:
        panel (pandas.DataFrame): The dataframe which types need to be
            assigned.
        rename_df (pandas.DataFrame): The renaming dataframe taken from the
            renaming file.
        cat_sep(string): The separator of the categories in the file.
        int_to_float(boolean): True if values specified as int should be coded
            as float.
        bool_to_float(boolean): True if values specified as boolean should be
            coded as float.
        num_str_categorical(int): Number of unique values for inferance as
            category.
        scale_as_category(boolean): True if values specified as scales should
            be catagories.

    Returns:
        pandas.DataFrame: The dataframe with the new types assigned.

    """
    out = panel.copy()

    rename_df = rename_df.set_index("new_name")
    rename_df["type"] = rename_df["type"].replace(
        {
            "int": "Int64",
            "float": "float64",
            "bool": "boolean",
            "Categorical": "category",
            "Int": "Int64",
        }
    )

    if scale_as_category:
        rename_df["type"] = rename_df["type"].replace({"scale": "category"})
    if int_to_float:
        rename_df["type"] = rename_df["type"].replace({"Int64": "float64"})
    if bool_to_float:
        rename_df["type"] = rename_df["type"].replace({"boolean": "float64"})

    errors = {}
    error_cats = {}
    for var in out:
        if var in rename_df.index and not pd.isna(rename_df.loc[var, "type"]):
            expected_type = rename_df.loc[var, "type"]
            # ToDo: Get rid of this? If not, document better
            if expected_type == "scale":
                cats_scale = rename_df.loc[var, "categories_english"].split(cat_sep)
                replace_dict = dict(zip(cats_scale, np.arange(0, len(cats_scale))))
                try:
                    out[var] = out[var].replace(replace_dict)
                except TypeError:
                    try:
                        cats_scale = [int(s) for s in cats_scale]
                        replace_dict = dict(
                            zip(cats_scale, np.arange(0, len(cats_scale)))
                        )
                        out[var].replace(replace_dict, inplace=True)
                    except Exception:
                        frameinfo = getframeinfo(currentframe())
                        module_name = frameinfo.filename
                        lineno = frameinfo.lineno - 1
                        message = f"Problem converting to scale var: {var}"
                        warnings.warn(message)
                        swtl(message=message, module_name=module_name, lineno=lineno)
                if int_to_float:
                    expected_type = "float64"
                else:
                    expected_type = "Int64"

            try:
                out[var] = out[var].astype(expected_type)
            except TypeError:
                frameinfo = getframeinfo(currentframe())
                module_name = frameinfo.filename
                lineno = frameinfo.lineno - 1
                message = f"could not convert {var} to {expected_type}"
                warnings.warn(message)
                swtl(message=message, module_name=module_name, lineno=lineno)
            except Exception:
                frameinfo = getframeinfo(currentframe())
                module_name = frameinfo.filename
                lineno = frameinfo.lineno - 1
                message = (
                    f"unexpected error converting the type of {var} to {expected_type}"
                )
                warnings.warn(message)
                swtl(message=message, module_name=module_name, lineno=lineno)

            if (
                expected_type == "category"
                and rename_df.loc[var, "categories_english"]
                == rename_df.loc[var, "categories_english"]
            ):
                try:
                    cats = [
                        int(s)
                        for s in rename_df.loc[var, "categories_english"].split(cat_sep)
                    ]
                except Exception:
                    cats = rename_df.loc[var, "categories_english"].split(cat_sep)

                missing_in_renaming = [
                    c for c in out[var].unique() if c not in cats and not pd.isna(c)
                ]
                if len(missing_in_renaming) > 0:
                    errors[var] = missing_in_renaming
                    error_cats[var] = cats

                if rename_df.loc[var, "ordered"] == rename_df.loc[var, "ordered"]:
                    ordered = rename_df.loc[var, "ordered"]
                else:
                    ordered = False
                try:
                    out[var].cat.set_categories(
                        cats,
                        ordered=ordered,
                        inplace=True,
                    )
                except Exception:
                    frameinfo = getframeinfo(currentframe())
                    module_name = frameinfo.filename
                    lineno = frameinfo.lineno - 1
                    message = (
                        f"for {out[var]} there is an error in the "
                        "categories specified in the file"
                    )
                    swtl(message=message, module_name=module_name, lineno=lineno)

                    warnings.warn(message, UserWarning)

        # If no type specified, infer it
        else:
            out.loc[:, var] = _set_inferred_types(
                out[var],
                int_to_float=int_to_float,
                bool_to_float=bool_to_float,
                num_str_categorical=num_str_categorical,
            )
    if errors:
        error_message = "\n".join(
            [
                (
                    f"{errors[var]} missing in row {var} of renaming file"
                    f" which only contains {error_cats[var]}"
                )
                for var in errors
            ]
        )
        raise ValueError(error_message)

    return out


def convert_time_cols(panel, cols):
    """Convert the observations in the selected time columns of a panel to a
    HH:MM:SS format. If they are in seconds from the beginning of the day.

    Args:
        panel(pandas.DataFrame): The data frame to be converted.
        cols(list): The time columns to be converted.

    Returns:
        pandas.DataFrame: the data frame with the time in the format specified.
    """
    out = panel.copy()
    for col in cols:
        out[col] = out[col].apply(
            lambda x: str(datetime.timedelta(seconds=math.floor(x)))
            if type(x) == float and x == x
            else x
        )
    return out


# def convert_dtypes(data, description, logging="print"):
#     """Convert and check dtypes to match between data and description.
#     For categorical dtypes this only checks that categories match and ordered variables
#     are ordered.
#     Args:
#         data (pd.DataFrame): DataFrame with the survey data.
#         data_name (str): name of the column containing the variable names in
#             the raw dataset.
#         description (pd.DataFrame): DataFrame describing the finished DataFrame.
#         logging (str, optional): Path to a text file, "print" or None
#     Returns:
#         data (pd.DataFrame): DataFrame satisfying the
#     """
#     dict_data = description.set_index("new_name")[
#         ["type", "categories_english", "ordered"]
#     ]
#     overlap = set(data.columns).intersection(dict_data.index)
#     dict_data = dict_data.loc[overlap]
#     col_to_dtype = dict_data.T.to_dict()
#     for col, col_dict in col_to_dtype.items():
#         should_type = col_dict["type"]
#         if should_type == "boolean":
#             if data[col].dtype.name in ["category", "object"]:
#                 data[col] = data[col].replace({"Yes": True, "No": False})
#                 try:
#                     data[col] = data[col].astype("float")
#                 except TypeError:
#                     warnings.warn("corrupted categories! cant be converted to boolean.")
#             else:
#                 try:
#                     data[col] = data[col].astype(should_type)
#                 except TypeError:
#                     warnings.warn(col, data[col].dtype, data[col].unique())

#         elif should_type == "Categorical":
#             is_type = data[col].dtype
#             try:
#                 if is_type != "category":
#                     msg = f"{col} is not a Categorical variable but {is_type}"  # noqa
#                     _custom_logging(msg=msg, logging=logging)
#                 else:
#                     should_cats = col_dict["categories_english"].split(", ")
#                     if set(should_cats) != set(is_type.categories):
#                         msg = (
#                             f"{col} does not have the categories it should have. \n\t"
#                             + f"It has: {is_type.categories.tolist()}\n\t"
#                             + f"It shoud have: {should_cats}"
#                         )
#                     should_be_ordered = col_dict["ordered"]
#                     if should_be_ordered:
#                         if not is_type.ordered:
#                             msg = f"{col} is not ordered though it should be."
#                             _custom_logging(msg=msg, logging=logging)
#                         else:
#                             if is_type.categories.tolist() != list(should_cats):
#                                 msg = (
#                                     f"{col}'s categories are not in the right order."
#                                     + f"They are: \n\t{is_type.categories.tolist()}"
#                                     + f"\n\nThey should be: \n\t{should_cats}."
#                                 )
#             except TypeError:
#                 msg = f"{col} raises the type error. its type is {is_type}"
#                 _custom_logging(msg=msg, logging=logging)
#         elif should_type == "str":
#             data[col].replace({"": np.nan}, inplace=True)
#         else:  # Int or float
#             try:
#                 data[col] = data[col].astype(should_type)
#             except Exception:
#                 warnings.warn(
#                     f"{col} should be {should_type}"
#                     + " but can't be converted from {data[col].dtype}"
#                 )
#     return data


# def check_description(data, data_name, description, logging="print"):
#     """Perform various checks on the description table.
#     Args:
#         data (pd.DataFrame): DataFrame with the survey data.
#         data_name (str): column name of the raw variable names
#         description (pd.DataFrame): DataFrame describing the finished DataFrame.
#         logging (str, optional): Path to a text file, "print" or None
#     """
#     _check_new_names(new_names=description["new_name"], logging=logging)
#     _check_types(types=description["type"], logging=logging)
#     _check_var_overlap_btw_description_and_data(
#         data_vars=data.columns, covered=description[data_name].unique(), logging=logging
#     )
#     labels = description.set_index("new_name")["label_english"]
#     if labels.isnull().any():
#         msg = "The following variables don't have a label:\n\t" + "\n\t".join(
#             labels[labels.isnull()].index
#         )
#         _custom_logging(msg=msg, logging=logging)

#     # warn if topic missing


# def _check_new_names(new_names, logging):
#     if new_names.duplicated().any():
#         msg = f"{new_names[new_names.duplicated()]} are duplicates in the new_name column."
#         _custom_logging(msg=msg, logging=logging)
#     if new_names.isnull().any():
#         msg = "The new name column should not contain NaNs"
#         _custom_logging(msg=msg, logging=logging)

#     lengths = new_names.str.len()
#     too_long = new_names[lengths > 31]
#     if len(too_long) > 0:
#         msg = "The following new names are too long for STATA:\n\t" + "\n\t".join(
#             too_long
#         )
#         _custom_logging(msg=msg, logging=logging)


# def _check_types(types, logging):
#     if types.isnull().any():
#         msg = "You should declare a type for every variable."
#         _custom_logging(msg=msg, logging=logging)

#     known_types = ["boolean", "Int64", "float", "Categorical", "str"]
#     if not types.isin(known_types).all():
#         unknown_types = types[~types.isin(known_types)].tolist()
#         msg = "There are unknokn types: \n" + "\n\t".join(unknown_types)
#         _custom_logging(msg=msg, logging=logging)


# def _check_var_overlap_btw_description_and_data(data_vars, covered, logging):
#     missing_in_description = [x for x in data_vars if x not in covered]
#     if missing_in_description:
#         msg = (
#             "The following variables from the raw dataset are not "
#             + "covered by the description table: \n\t"
#             + "\n\t".join(sorted(missing_in_description))
#         )
#         _custom_logging(msg=msg, logging=logging)
#     missing_in_data = [str(x) for x in covered if x not in data_vars]
#     if missing_in_data:
#         msg = (
#             "The following variables from the description table are not "
#             + "in the raw dataset: \n\t"
#             + "\n\t".join(sorted(missing_in_data))
#         )
#         _custom_logging(msg=msg, logging=logging)


# def _check_categorical_cols(description, data_name, logging):
#     cat_df = description[description["type"] == "Categorical"]
#     no_categories = cat_df["categories_english"].isnull()
#     if no_categories.any():
#         msg = "English category labels are missing for: \n\t" + "\n\t".join(
#             cat_df[no_categories]["new_name"]
#         )
#         _custom_logging(msg=msg, logging=logging)
#     ordered_bool = cat_df["ordered"].isin([True, False])
#     if not ordered_bool.all():
#         msg = "The ordered column must be boolean but is not for: \n\t" + "\n\t".join(
#             cat_df[~ordered_bool]["new_name"]
#         )
#         _custom_logging(msg=msg, logging=logging)


# def _custom_logging(msg, logging):
#     """Print or write msg to a file."""
#     padded = "\n\n" + msg + "\n\n"
#     if logging == "print":
#         warnings.warn(padded)
#     elif logging is not None:
#         with open(logging, "a") as f:
#             f.write(padded)


# def convert_dtypes(df, num_str_categorigal=18):
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
#     for col in out:
#         if out[col].dtype.name == "object":
#             contains_float = _check_for_float(out[col].unique())
#             contains_string_float = _check_for_str_number(out[col].unique())

#             # Convert string only cols to cat if they have few labels
#             if (
#                   (contains_string_float is False) and
#                   (len(out[col].unique()) <= num_str_categorigal)):
#                 out[col] = out[col].astype("category")

#             # Convert cols to cat that contain only floats/str in range(11)
#             elif contains_string_float in ["categorical", "years"]:
#                 out[col] = out[col].astype("float").astype("category")

#             # Convert float only strings to numerical
#             elif contains_float == "all":
#                 out[col] = out[col].astype("float")

#             # Print the rest and maybe inlcude warning for weird cols
#             elif contains_float == "some" or contains_string_float == "some":
#                 warnings.warn(
#                     f"{col} contains bad combination of values! Either"
#                     "further cleaning is required or an error occured",
#                     UserWarning,
#                 )

#     return out


# def _check_for_str_number(values):
#     """
#     Check for str floats in list of values
#     """
#     out = []
#     values = [x for x in values if str(x) != "nan"]

#     for x in values:
#         try:
#             out.append(float(x))
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
