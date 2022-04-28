import numpy as np
import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_assets(panel):
    """
    Data cleaning for assets questionnaire.

    Calculate the reported values of banking, insurance, risky_financial_assets,
    real_estate, cars_etc, etc.
    Calculations based on dummy (_d), value (_v), and category (_c)
    Combine them for total wealth and financial wealth.

    """
    # Replace and rename some values and columns of the data frame.
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "009-economic-situation-assets_renaming.csv",
        sep=";",
    )
    with open(IN_SPECS_LISS / "009-economic-situation-assets_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    panel = replace_values(panel, replace_dict, rename_df)

    # Clean logically assets dataset.
    panel = _clean_logically_assets(panel)

    # Create additional variables.
    panel = _create_additional_cols_assets(panel)

    # Set types of variables using renaming file.
    panel = set_types_file(
        panel=panel,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )

    # Check some consistency in the data.
    _check_assets(panel)

    return panel


def _clean_logically_assets(panel):
    """Clean some of the data logically

    Args:
        panel(pandas.DataFrame): The data frame to be cleaned.

    Returns:
        pandas.DataFrame: The logically cleaned data frame.
    """
    out = panel.copy()

    # Take the same midpoints for all variables
    # Draw them from dictionary:
    bin_values = {
        "less than EUR 50": 25,
        "less than EUR 500": 250,
        "EUR 50 to EUR 250": 150,
        "EUR 250 to EUR 500": 375,
        "EUR 500 to EUR 750": 625,
        "EUR 500 to EUR 1,500": 1000,
        "EUR 750 to EUR 1,000": 875,
        "EUR 1,000 to EUR 2,500": 1750,
        "EUR 1,500 to EUR 2,500": 2000,
        "EUR 2,500 to EUR 5,000": 3750,
        "EUR 5,000 to EUR 7,500": 6250,
        "EUR 7,500 to EUR 10,000": 8750,
        "EUR 10,000 to EUR 11,500": 10750,
        "EUR 10,000 to EUR 12,000": 11000,
        "EUR 11,500 to EUR 14,000": 12750,
        "EUR 12,000 to EUR 15,000": 13500,
        "EUR 14,000 to EUR 17,000": 15500,
        "EUR 15,000 to EUR 20,000": 17500,
        "EUR 17,000 to EUR 20,000": 18500,
        "EUR 20,000 to EUR 25,000": 22500,
        "EUR 25,000 or more": 25000,
        "EUR 25,000 to EUR 50,000": 37500,
        "EUR 25,500 to EUR 50,000": 37750,
        "EUR 50,000 to EUR 75,000": 62500,
        "EUR 75,000 to EUR 100,000": 87500,
        "EUR 100,000 or more": 100_000,
        "less than EUR 50,000": 25000,
        "EUR  50,000 to EUR 100,000": 75000,
        "EUR 100,000 to EUR 150,000": 125_000,
        "EUR 150,000 to EUR 200,000": 175_000,
        "EUR 200,000 to EUR 250,000": 225_000,
        "EUR 250,000 to EUR 400,000": 325_000,
        "EUR 400,000 to EUR 500,000": 450_000,
        "EUR 500,000 to EUR 1,000,000": 750_000,
        "EUR 1,000,000 to EUR 2,500,000": 1_750_000,
        "EUR 2,500,000 or more": 2_500_000,
        "positive, but less than EUR 50,000": 25000,
    }

    # Some arangements such that the following loop can be used for every variable
    out["debt_d"] = out["debt_no_d"].map({1: 0, 0: 1})

    asset_list = [
        "banking",
        "insurance",
        "risky_financial_assets",
        "real_estate",
        "durables",
        "mortgage",
        "loan_out",
        "other_inv",
        "study_grant",
        "priv_comp",
        "pship",
        "self_empl_comp",
        "debt",
    ]

    for asset in asset_list:
        out[f"{asset}_c"] = out[f"{asset}_c"].replace("I don’t know", np.nan)

        out[asset] = out[f"{asset}_v"]

        # Fill up missing value with categorical values; retain missing if
        # value not found in dict.
        out[asset].fillna(
            panel[f"{asset}_c"].apply(
                lambda x: bin_values.get(x) if x in bin_values else np.nan
            ),
            inplace=True,
        )

        # Fill up with zero values when subject said no
        out[asset].fillna(
            out[f"{asset}_d"].apply(lambda x: 0 if (x == 0) else np.nan), inplace=True
        )

    # Convert everything to numeric if possible
    out = out.apply(pd.to_numeric, errors="ignore")

    # Fill mortgage with 0 if no house
    out["mortgage"].fillna(
        out["real_estate_d"].apply(lambda x: 0 if (x == 0) else np.nan), inplace=True
    )

    # Fill study grant with 0 if not asked for study grant
    out.loc[out["study_grant_c"].isna(), "study_grant"] = 0

    out.loc[out["priv_comp"] > 0, "priv_comp"] = (
        out.loc[out["priv_comp"] > 0, "priv_comp"]
        * out.loc[out["priv_comp"] > 0, "priv_comp_stake"]
        / 100
    )

    # Add substract mortgage and/or study_grant to debts if they are not missing
    out["debt"] = out["debt"] + out["study_grant"] + out["mortgage"]
    out = out.rename(columns={"debt": "debt_excl_housing"})

    return out


def _create_additional_cols_assets(panel):
    """Create additional variables using the information from the data frame.

    Args:
        panel(pandas.DataFrame): The data frame.

    Returns:
        pandas.DataFrame: the data frame with additional veraiables included.
    """
    out = panel.copy()

    out["total_financial_assets"] = (
        out["banking"] + out["risky_financial_assets"] + out["insurance"]
    )
    out["non_fin_assets_excl_housing"] = (
        out["durables"]
        + out["real_estate"]
        + out["priv_comp"]
        + out["pship"]
        + out["self_empl_comp"]
        + out["loan_out"]
        + out["other_inv"]
    )
    out["wealth_excl_housing"] = (
        out["total_financial_assets"]
        + out["non_fin_assets_excl_housing"]
        - out["debt_excl_housing"]
    )

    # Create some variables that are often used
    out["has_rfa"] = (out["risky_financial_assets"].dropna() > 0).astype(float)

    out["has_rfa_wide_def"] = out["risky_financial_assets_d"]
    out["frac_rfa"] = out["risky_financial_assets"] / out[
        "total_financial_assets"
    ].where(out["total_financial_assets"] > 0)

    return out


def _check_assets(panel):
    """Check some of the data in the assets database.

    Args:
        panel(pandas.DataFrame): The data frame to be checked.
    """
    out = panel.copy()
    general_data_checks(out)
