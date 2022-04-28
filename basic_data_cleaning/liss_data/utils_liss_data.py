"""
This file contains some functions that are shared
across cleaning modules
"""
import logging
import math
import os
import sys
import warnings
from inspect import currentframe
from inspect import getframeinfo
from traceback import format_exception

import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from config import OUT_DATA_LISS


def read_stata(
    file_path,
    convert_categoricals,
    vars_to_keep,
    start_year=None,
    renaming_complete=False,
):
    """Emulate pd.read_stata() that takes care of duplicate entries for
    convert_categoricals=True.

    Args:
        file_path (string): path to file
        convert_categoricals (boolean): Read value labels and convert columns
                                        to Categorical/Factor variables.
        vars_to_keep (list): columns that should be kept
        start_year: all observations before this year are dropped


    Returns:
        DataFrame: loaded file
    """

    data = pd.read_stata(file_path, convert_categoricals=False)
    missing_from_data = [x for x in vars_to_keep if x not in data]
    missing_from_rename = [x for x in data.columns if x not in vars_to_keep]

    # Raise error if expected variable not in data
    if len(missing_from_data) > 0:
        raise KeyError(
            f"Problem with {file_path}: the following variables "
            "are specified in the renaming file, but not in the "
            "dataset:\n\t" + "\n\t".join(missing_from_data)
        )
    # Raise error if expected variable not in renaming file
    if len(missing_from_rename) > 0 and renaming_complete:
        frameinfo = getframeinfo(currentframe())
        module_name = frameinfo.filename
        lineno = frameinfo.lineno - 1
        message = (
            f"Problem with {file_path}: the following "
            "variables are not in the renaming table and as a consequence "
            "dropped:\n\t" + "\n\t".join(missing_from_rename)
        )
        warnings.warn(message)
        send_warnings_to_log(message=message, module_name=module_name, lineno=lineno)

    # Select only subset of variables
    data = data[[c for c in data if c in vars_to_keep]]

    if start_year:
        raise NotImplementedError

    if convert_categoricals:

        # More general version to convert needed than the built-in one.
        value_label_dict = pd.io.stata.StataReader(file_path).value_labels()
        for col in data:
            if col in value_label_dict:
                cat_data = pd.Categorical(data[col], ordered=True)
                categories = []
                for category in cat_data.categories:
                    if category in value_label_dict[col]:
                        categories.append(value_label_dict[col][category])
                    else:
                        categories.append(category)  # Partially labeled
                if len(categories) == len(set(categories)):
                    cat_data.categories = categories
                    data[col] = cat_data
    return data


def load_general_specs(data_set_name):
    """Load general specifications for one data set

    Args:
        data_set_name (string): name of data set

    Returns:
        dictionary: general specifications
    """
    with open(IN_SPECS_LISS / "data_sets_specs.yaml") as fn:
        specs = yaml.safe_load(fn)[data_set_name]

    return specs


def load_rename_df(data_set_name):
    rename_df = pd.read_csv(IN_SPECS_LISS / f"{data_set_name}_renaming.csv", sep=";")
    rename_df = rename_df.dropna(subset=["new_name"])

    # Check validity of rename df
    check_new_name_in_renaming(
        rename_df, data_set_name, suffixes_exception=["_merge", "_202002", "_update"]
    )
    return rename_df


def load_data_set_and_specs(data_set_name, start_year=None):
    """Load data set, specification, and renaming file

    Args:
        data_set_name (string): name of data set

    Returns:
        DataFrame: data set
        dict: specifications for data set
        DataFrame: renaming specifications
        dict: replacing spefications
    """

    # Load specifications
    specs = load_general_specs(data_set_name)

    # Load rename df
    rename_df = load_rename_df(data_set_name)

    # Load further cleaning spec files if they exist
    cleaning_specs = {}
    for cleaning_type in [
        "replacing",
        # "logical_cleaning"
    ]:
        replace_path = IN_SPECS_LISS / f"{data_set_name}_{cleaning_type}.yaml"
        if os.path.isfile(replace_path):
            with open(replace_path) as file:
                cleaning_specs[f"{cleaning_type}"] = yaml.safe_load(file)

    return specs, rename_df, cleaning_specs


def removesuffix(complete_str, suffix):
    # ToDo: when only Python versions after 3.9 are supported, can
    # ToDo: just use the method of the standard library
    if suffix and complete_str.endswith(suffix):
        return complete_str[: -len(suffix)]
    else:
        return complete_str[:]


def check_new_name_in_renaming(rename_df, data_set_name, suffixes_exception=None):
    # ToDo: write unit tests for this function

    rename_df = rename_df.copy()
    if suffixes_exception:
        for suf in suffixes_exception:
            rename_df["new_name"] = rename_df["new_name"].apply(
                lambda x: removesuffix(x, suf)
            )

    # Raise error if too long!
    too_long = rename_df["new_name"].str.match("^.{32,}")
    if too_long.any():

        too_long_variable_names = rename_df.loc[too_long, "new_name"].values
        raise (
            ValueError(
                "column names are too long. Please rename the variable name(s)"
                f" {too_long_variable_names} in the renaming file for {data_set_name}"
            )
        )


def save_panel(panel, file_name, out_format):
    """Save *panel* in one of several data formats as *file_name*.*format*."""
    if out_format.startswith("."):
        out_format = out_format[1:]
    if out_format == "pickle":
        panel.to_pickle(OUT_DATA_LISS / (file_name + ".pickle"))
    elif out_format == "dta":
        try:
            variable_cleaning_for_dta(panel).to_stata(
                OUT_DATA_LISS / (file_name + ".dta")
            )
        except (KeyboardInterrupt, SystemExit):
            raise
        except ValueError:
            variable_cleaning_for_dta(panel).to_stata(
                OUT_DATA_LISS / (file_name + ".dta"), version=117
            )
    elif out_format == "csv":
        panel.to_csv(OUT_DATA_LISS / (file_name + ".csv"), sep=";")

    elif out_format == "parquet":
        for c in [c for c in panel if panel[c].dtype == object]:
            panel[c] = panel[c].astype("string")
        panel.to_parquet(OUT_DATA_LISS / (file_name + ".parquet"))
    else:
        raise ValueError('"format" must be one of pickle, dta, csv, parquet')


def variable_cleaning_for_dta(panel):
    """Clean variables such that they can be exportet to Stata."""
    # Change dtype of object variables
    type_pref = [int, float, str]
    for colname in list(panel.select_dtypes(include=["object"]).columns):
        for t in type_pref:
            try:
                panel[colname] = panel[colname].astype(t)
            except (ValueError, TypeError):
                pass

    for x in panel.dtypes.index:
        if panel.dtypes[x].name == "object":
            panel = panel.drop(columns=[x])

    # retype new boolean and integer types
    for x in panel.dtypes.index:
        if panel.dtypes[x].name in ["boolean", "Int64"]:
            panel[x] = panel[x].astype("float")

    # Replace characters that cannot be read by Stata
    panel = panel.replace(["€"], ["EUR"], regex=True)
    panel = panel.replace(["\u2019"], ["'"], regex=True)
    panel = panel.replace(["nan"], [""], regex=True)
    panel = panel.replace([None], [""], regex=True)

    return panel


def merge_double_columns(df):
    merge_cols = [x for x in df.columns if x[-6:] == "_merge"]
    for col in merge_cols:
        df[col[:-6]] = df.apply(lambda x: _merge_cols(x[col[:-6]], x[col]), axis=1)
    df = df.drop(columns=merge_cols)
    return df


def update_double_columns(df):
    update_cols = [x for x in df.columns if x[-7:] == "_update"]
    for col in update_cols:
        df[col[:-7]] = df.apply(lambda x: _update_cols(x[col[:-7]], x[col]), axis=1)
    df = df.drop(columns=update_cols)
    return df


def _merge_cols(x, y):
    if type(x) == str:
        return x
    elif not math.isnan(x):
        return x
    elif type(y) == str:
        return y
    elif not math.isnan(y):
        return y
    else:
        return np.nan


def _update_cols(x, y):
    if type(y) == str:
        return y
    elif not math.isnan(y):
        return y
    elif type(x) == str:
        return x
    elif not math.isnan(x):
        return x
    else:
        return np.nan


def get_traceback():
    tb = format_exception(*sys.exc_info())
    if isinstance(tb, list):
        tb = "".join(tb)
    return tb


def remove_order_from_categorical(df, cols):
    df = df.copy()
    for c in cols:
        if c in df:
            assert df[c].dtype.name == "category", f"{c} not a category"
            df[c] = pd.Categorical(df[c], df[c].cat.categories, ordered=False)
    return df


def revert_order_of_categorical(df, cols):
    df = df.copy()
    for c in cols:
        if c in df:
            assert df[c].dtype.name == "category"
            df[c] = pd.Categorical(
                df[c], reversed(list(df[c].cat.categories)), ordered=True
            )
    return df


def clean_background_vars(data):
    data["net_income"] = data["net_income_imputed"].fillna(data["net_income_incl_cat"])
    data["gross_income"] = data["gross_income_imputed"].fillna(
        data["gross_income_incl_cat"]
    )

    data = data.drop(
        columns=[
            "age_cbs",
            "hh_head_age",
            "gross_income_incl_cat",
            "gross_income_imputed",
            "net_income_incl_cat",
            "net_income_imputed",
            "net_income_original",
            "gross_income_cat",
            "net_income_cat",
        ]
    )
    data["female"] = data["gender"].map({"Female": True, "Male": False}).astype(float)
    data["edu_4"] = data["education_cbs"].replace(
        {
            "mbo (intermediate vocational education, US: junior college)": "upper_secondary",
            "hbo (higher vocational education, US: college)": "tertiary",
            (
                "vmbo (intermediate secondary education, US: junior high school)"
            ): "lower_secondary",
            "primary school": "primary",
            "wo (university)": "tertiary",
            (
                "havo/vwo (higher secondary education/preparatory university education, "
                "US: senio"
            ): "upper_secondary",
        }
    )
    data["edu"] = data["education_cbs"].replace(
        {
            "mbo (intermediate vocational education, US: junior college)": "upper_secondary",
            "hbo (higher vocational education, US: college)": "tertiary",
            (
                "vmbo (intermediate secondary education, US: junior high school)"
            ): "lower_secondary_and_lower",
            "primary school": "lower_secondary_and_lower",
            "wo (university)": "tertiary",
            (
                "havo/vwo (higher secondary education/preparatory university education, "
                "US: senio"
            ): "upper_secondary",
        }
    )

    return data


# define function to save warnings to a file
def send_warnings_to_log(message, module_name, lineno):
    category = UserWarning
    logging.basicConfig(level=logging.INFO, filename="warnings.log")
    logging.warning(f"{module_name}:{lineno}: {category.__name__}:{message}")
    return
