import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_personality(data):
    """
    Data cleaning for personality questionnaire.
    """

    # Replace and rename some values and columns of the data frame.
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "007-personality_renaming.csv",
        sep=";",
    )
    with open(IN_SPECS_LISS / "007-personality_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    data = replace_values(panel=data, replace_dict=replace_dict, rename_df=rename_df)

    # Set types of variables using renaming file.
    data = set_types_file(
        panel=data,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )

    # Create additional variables.
    data = _create_additional_cols(data)

    # Check some consistency in the data.
    _check_personality(data)

    return data


def _create_additional_cols(data):
    """Create additional variables using the information from the data frame.

    Args:
        data(pandas.DataFrame): The data frame.

    Returns:
        pandas.DataFrame: the data frame with additional veraiables included.
    """
    out = data.copy()

    # Calculate the five factors
    bigV_factors = {
        "e": "extraversion",
        "a": "agreeableness",
        "c": "conscientiousness",
        "n": "neuroticism",
        "o": "openness",
    }

    bigV_columns = [c for c in out.columns if "bigV" in c]

    for fac in bigV_factors:
        fac_columns = [c for c in bigV_columns if "_" + fac + "_" in c]
        out[bigV_factors[fac]] = out[fac_columns].mean(axis=1)

    # calc social desirabililty
    social_des_pos_cols = [
        "mc_sds_helpothers",
        "mc_sds_dislike",
        "mc_sds_admittingignorance",
        "mc_sds_courteous",
        "mc_sds_responsible",
    ]
    social_des_neg_cols = [
        "mc_sds_rebllious",
        "mc_sds_playingsick",
        "mc_sds_insistence",
        "mc_sds_jealous",
        "mc_sds_irritated",
    ]
    pos = out[social_des_pos_cols].sum(axis=1)
    neg = out[social_des_neg_cols].sum(axis=1)
    out["social_desirability"] = pos - neg

    # Calculate optimism and pessimism using lot-r
    out["optimism"] = out[
        ["lot_r_expectbest", "lot_r_optimistic_future", "lot_r_optimistic_events"]
    ].mean(axis=1)
    out["pessimism"] = out[
        [
            "lot_r_hardlyoptimistic",
            "lot_r_pessimistic_future",
            "lot_r_pessimistic_events",
        ]
    ].mean(axis=1)

    return out


def _check_personality(data):
    """Check some of the data in the personality database.

    Args:
        data(pandas.DataFrame): The data frame to be checked.
    """
    out = data.copy()
    general_data_checks(out)
