import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from config import OUT_DATA_LISS
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_background(data_set_list, file_format):
    """
    Data cleaning for background questionnaire.
    Takes the within person-year mode of the background variables.
    """
    with open(IN_SPECS_LISS / "001-background-variables_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    rename_df = pd.read_csv(
        IN_SPECS_LISS / "001-background-variables_renaming.csv",
        sep=";",
    )

    # Apply groupby separated for each year to use less memory
    years_in_data = sorted({d["year"].iloc[0] for d in data_set_list})
    results_by_year = []
    for year in years_in_data:
        sel_data_sets = [d for d in data_set_list if d["year"].iloc[0] == year]
        data = pd.concat(sel_data_sets, ignore_index=True, sort=True)

        # Replace and rename some values and columns of the data frame.
        data = replace_values_background(data, replace_dict, rename_df)

        # Clean logically net_income and gross_income in background dataset.
        data = clean_logically_background(data)

        # Set types of variables using renaming file.
        data = set_types_file(
            panel=data,
            rename_df=rename_df,
            cat_sep="|",
            int_to_float=True,
            bool_to_float=True,
        )

        data = data.set_index("personal_id").sort_index()

        # Save full datasets
        out_data = (
            data.reset_index().set_index(["personal_id", "date_fieldwork"]).sort_index()
        )
        if file_format in ["pickle", "csv"]:
            getattr(out_data, f"to_{file_format}")(
                OUT_DATA_LISS / ("background_full_" + str(year) + f".{file_format}")
            )
        elif file_format == "dta":
            out_data.to_stata(
                OUT_DATA_LISS / ("background_full_" + str(year) + f".{file_format}")
            )
        # Change the structure of the yearly datasets.
        data = _restructure_background(data)

        results_by_year.append(data)

    data = pd.concat(results_by_year, sort=True).reset_index()

    # Set types of variables using renaming file.
    data = set_types_file(
        panel=data,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
        few_int_to_cat=False,
    )
    # Create a log income variable for the full dataset only.
    data = _create_additional_cols(data)

    # Check some consistency in the data.
    general_data_checks(data)

    return data


def _create_additional_cols(data):
    """Create additional variables using the information from the data frame.

    Args:
        data(pandas.DataFrame): The data frame.

    Returns:
        pandas.DataFrame: the data frame with additional veraiables included.
    """
    out = data.copy()

    # Create log_income
    out["log_income"] = np.log(
        out["net_income"].apply(pd.to_numeric, errors="coerce") + 0.1
    )

    return out


def replace_values_background(data, replace_dict, rename_df):
    """Do some cleaning of the database by replacing and renaming some
    observations in the corona database, and adding certain columns where
    needed.

    Args:
        data(pandas.DataFrame): The data frame to be converted.
        rename_dict(dict): Dictionary containing the information to replace the
            values in the database.
        rename_df(pandas.DataFrame): The renaming dataframe taken from the
            renaming file.

    Returns:
        pandas.DataFrame: the data frame with the changes inplace.
    """
    out = data.copy()

    out["edu_4"] = out["education_cbs"]
    out["edu"] = out["education_cbs"]
    out["female"] = out["gender"].map({"Female": True, "Male": False})
    # Replace some variables:
    out = replace_values(out, replace_dict, rename_df)

    return out


def clean_logically_background(data):
    """Clean some of the data logically

    Args:
        data(pandas.DataFrame): The data frame to be cleaned.

    Returns:
        pandas.DataFrame: The logically cleaned data frame.
    """
    out = data.copy()

    if "net_income_imputed" in out:
        out["net_income"] = out["net_income_imputed"].fillna(out["net_income_incl_cat"])
        out["gross_income"] = out["gross_income_imputed"].fillna(
            out["gross_income_incl_cat"]
        )
    else:
        out["net_income"] = out["net_income_incl_cat"]
        out["gross_income"] = out["gross_income_incl_cat"]

    return out


def _restructure_background(data):
    """Restructure yearly datasets by averiging variables with numerical values
    over the fieldwork dates and, for the rest of the variables, getting the
    first value for each observation.

    Args:
        data(pandas.DataFrame): The data frame to be restructured.

    Returns:
        pandas.DataFrame: The restructured data frame.
    """
    out = data.copy()

    # Split dataset into parts aggregated by mode and mean respectively
    mean_cols = list(
        {c for c in out.columns if "income" in c}
        - {"net_income_cat", "gross_income_cat"}
    )
    discrete_cols = list(
        set(
            [c for c in out.columns if "income" not in c]
            + ["net_income_cat", "gross_income_cat"]
        )
        - {"age_cbs", "hh_head_age", "date_fieldwork"}
    )
    mean_df = out[mean_cols].groupby("personal_id").mean()

    discrete_df = out[discrete_cols].groupby("personal_id").first()

    # Concat the two dataframes again
    # mode is not necessarily unique. this returns a dataframe with a third level
    out = pd.concat([mean_df, discrete_df], axis=1)

    return out
