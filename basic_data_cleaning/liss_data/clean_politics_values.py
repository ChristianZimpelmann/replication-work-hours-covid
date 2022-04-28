import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import convert_time_cols
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks


def clean_politics_values(panel):
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "008-politics-and-values_renaming.csv",
        sep=";",
    )

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_LISS / "008-politics-and-values_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    panel = _replace_values_political_values(panel, replace_dict, rename_df)

    # Set types of variables using renaming file.
    panel = set_types_file(
        panel=panel,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
        scale_as_category=False,
    )

    general_data_checks(panel, replace_dict)

    return panel


def _replace_values_political_values(panel, replace_dict, rename_df):
    """Do some cleaning of the database by replacing and renaming some
    observations in the health database, and adding certain columns where
    needed.

    Args:
        panel(pandas.DataFrame): The data frame to be converted.
        replace_dict(dict): Dictionary containing the information to replace the
            values in the database.
        rename_df(pandas.DataFrame): The renaming dataframe taken from the
            renaming file.

    Returns:
        pandas.DataFrame: the data frame with the changes inplace.
    """
    out = panel.copy()

    # Convert time cols
    out = convert_time_cols(
        out,
        [
            "start_time",
            "end_time",
            "start_time_1",
            "end_time_1",
            "start_time_2",
            "end_time_2",
            "start_time_3",
            "end_time_3",
            "end_time_a",
            "end_time_b",
            "end_time_c",
            "end_time_d",
            "end_time_e",
            "end_time_f",
            "end_time_g",
            "end_time_h",
            "end_time_i",
            "end_time_j",
            "end_time_norm",
        ],
    )

    # Replace values using dictionary.
    out = replace_values(out, replace_dict, rename_df)

    return out


'''
def _clean_politics_values(panel):
    """
    Data cleaning for politics questionnaire.

    Fix missing date_fieldwork for wave 8.

    """
    panel = _general_replacements(panel)
    panel = _to_categoricals(panel)
    panel = convert_dtypes(panel, num_str_categorigal=20)

    return panel


def _general_replacements(panel):
    """
    Make general replacements. Remove whitespace.

    Comments:
        For each value, I made sure there was no overlap across surveys.
        That way, **certainly yes** equates to 5 no matter what, irrespective
        of question or simply because no question used it.

    """
    panel.loc[panel["wave"] == 8, "year"] = 2015
    panel.loc[panel["wave"] == 4, "year"] = 2010

    panel = panel.replace(
        {
            "no": 0,
            "yes": 1,
            "I dont know": np.nan,
            "not eligible to vote": np.nan,
            "I don't know": np.nan,
            "I am not eligible to vote": np.nan,
            999: np.nan,
            998: np.nan,
            "very sympathetic": 10,
            "very unsympathetic": 0,
            "right": 10,
            "left": 0,
            "euthanasia should be permitted": 5,
            "euthanasia schould be forbidden": 1,  # it is mispelled on purpose
            "differences in income should decrease": 5,
            "differences in income should increase": 1,
            "immigrants should adapt entirely to Dutch culture": 5,
            "immigrants can retain their own culture": 1,
            "European unification has already gone too far": 5,
            "European unification should go further": 1,
            "never thought about it": np.nan,
            "definitely yes": 5,
            "definitely no": 1,
            "certainly yes": 5,
            "certainly not": 1,
            "no confidence at all": 0,
            "full confidence": 10,
            "that is true": 1,
            "that is not true": 0,
        }
    )

    # Convert satisfaction and confidence variables to floats
    panel["gov_satisfaction"] = (
        panel["gov_satisfaction"]
        .replace(
            {
                "very dissatisfied": 1,
                "dissatisfied": 2,
                "neither satisfied nor dissatisfied": 3,
                "satisfied": 4,
                "very satisfied": 5,
            }
        )
        .astype(float)
    )

    for c in [
        c for c in panel.columns if "satisfied" in c and c != "satisfied_gov_general"
    ]:
        panel[c] = (
            panel[c]
            .replace(
                {"I dont know": np.nan, "very dissatisfied": 0, "very satisfied": 10}
            )
            .astype(float)
        )

    for c in [c for c in panel.columns if "view" in c]:
        cat_type = CategoricalDtype(
            categories=[
                "fully disagree",
                "disagree",
                "neither agree nor disagree",
                "agree",
                "fully agree",
            ],
            ordered=True,
        )
        panel[c] = panel[c].astype(cat_type)

    for c in [c for c in panel.columns if "political_priority" in c]:
        panel[c] = panel[c].astype("category")

    panel["random_trad_or_chance_voting_q"] = (
        panel["random_trad_or_chance_voting_q"]
        .replace(
            {
                "The chance questions cv18j245 \x96 cv18j262":
                 "The chance questions cv18j245 – cv18j262",
                "The chance questions cv17i245 \x96 cv17i262":
                "The chance questions cv17i245 – cv17i262",
                -9: np.nan,
            }
        )
        .astype("category")
    )

    return panel


def _to_categoricals(panel):
    """
    Convert to category.

    """
    vote_columns = ["voted_for_parl", "voted_for_prov", "would_vote_for_now_parl"]

    for column in vote_columns:
        panel[column] = panel[column].astype("category")

    return panel
'''
