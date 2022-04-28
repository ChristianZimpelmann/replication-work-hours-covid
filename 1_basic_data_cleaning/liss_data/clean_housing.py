import numpy as np
import pandas as pd
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import set_types_file


def clean_housing(panel):
    """
    Data cleaning for housing questionnaire.

    """

    # Replace and rename some values and columns of the data frame.
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "011-economic-situation-housing_renaming.csv",
        sep=";",
    )

    # Some general renaming
    panel = panel.replace(
        {
            "ja": 1,
            "nee": 0,
            "yes": 1,
            "no": 0,
            "I prefer not to say": np.nan,
            "I don't know": np.nan,
            "I don\x92t know": np.nan,
            "entirely satisfied": 10,
            "not at all satisfied": 0,
            "Other": "other",
            "Usufruct": "usufruct",
            "Property right": "property right",
            "Anti-squatting": "anti-squatting",
            "yes, I receive rent benefit": "yes",
            "no, I don't receive rent benefit": "no",
            "no, I don\x92t receive rent benefit": "no",
            "9999999999": np.nan,
            "yes, premiums were paid/debts were redeemed on this or these"
            " mortgage(s) or loan": "yes",
            "no, there were no premiums paid/debts redeemed on this or"
            " these mortgage(s) or l": "no",
            "with buyer\x92s costs (Dutch: kosten koper)": "with buyer's costs"
            " (Dutch: kosten koper)",
            "without buyer\x92s costs": "without buyer's costs",
            "niet van toepassing": np.nan,
            "not applicable": np.nan,
            "certainly not": 1,
            "1 = certainly not": 1,
            "certainly yes": 5,
            "5 = certainly yes": 5,
        }
    )

    dont_say = [9_999_999_998, 99_999_999_998]
    dont_know = [9_999_999_999, 99_999_999_999]

    for col in [
        "home_price_sold_now",
        "home_remaining_mortgage",
        "home_appraisal_by_munic",
        "sec_home_remaining_mort",
        "sec_home_price_sold_now",
    ]:
        # panel[col + "_raw"] = panel[col]

        # Fill don't say and don't know with nan
        panel[col] = panel[col].apply(
            lambda x: x if x not in dont_say + dont_know else np.nan
        )

    for col in [
        "home_price_sold_now",
        "home_remaining_mortgage",
        "home_appraisal_by_munic",
    ]:
        # Fill with 0 if no home owner
        panel[col].fillna(
            panel["home_ownership_status"].apply(
                lambda x: 0 if (x != "(co-)owner") else np.nan
            ),
            inplace=True,
        )

    for col in ["sec_home_remaining_mort", "sec_home_price_sold_now"]:
        # Fill with 0 if no home owner of second home
        panel[col].fillna(
            panel["has_sec_home"].apply(lambda x: 0 if (x == "no") else np.nan),
            inplace=True,
        )
        panel[col].fillna(
            panel["sec_home_ownership_status"].apply(
                lambda x: 0 if (x != "owner") else np.nan
            ),
            inplace=True,
        )

    # Fill with 0 if no mortgage
    panel["home_remaining_mortgage"].fillna(
        panel["home_has_mortgage"].apply(lambda x: 0 if (x == "no") else np.nan),
        inplace=True,
    )
    panel["sec_home_remaining_mort"].fillna(
        panel["sec_home_has_mortgage"].apply(lambda x: 0 if (x == "no") else np.nan),
        inplace=True,
    )

    # Create estimate of current home price
    panel["home_price"] = panel["home_appraisal_by_munic"].fillna(
        panel["home_price_sold_now"]
    )
    panel = panel.rename(columns={"sec_home_price_sold_now": "sec_home_price"})

    float_columns = [
        "satisfied_home_vicinity",
        "satisfied_home",
        "home_year_bought",
        "home_appraisal_by_munic_year",
        "questionnaire_difficult",
        "questionnaire_clear",
        "questionnaire_thinking",
        "questionnaire_interesting",
        "questionnaire_enjoy",
    ]

    panel[float_columns] = panel[float_columns].replace(
        {"10 very satisfied": 10.0, "0 not at all satisfied": 0.0}
    )

    # Set types of variables using renaming file.
    panel = set_types_file(
        panel=panel,
        rename_df=rename_df,
        int_to_float=True,
        bool_to_float=True,
    )
    return panel
