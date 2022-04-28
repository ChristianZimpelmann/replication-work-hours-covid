import numpy as np
import pandas as pd
from config import IN_SPECS_LISS
from liss_data.cleaning_helpers import set_types_file
from pandas.api.types import CategoricalDtype


def clean_religion_ethnicity(panel):
    """
    Data cleaning for religion questionnaire.

    """
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "003-religion-and-ethnicity_renaming.csv", sep=";"
    )
    panel = _general_replacements(panel)
    panel = _yes_no_maybe(panel)
    panel = _clean_categoricals(panel)
    panel = _to_ordered_categoricals(panel)
    panel = set_types_file(panel=panel, rename_df=rename_df, num_str_categorigal=25)

    return panel


def _general_replacements(panel):
    """
    Make general replacements. Remove whitespace.

    Comments:
        99 and 999 are used as np.nan across the documentation.
        Has no numeric conflicts prior to merging to background.

    """
    # To remove whitespace
    panel = panel.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # To make general replacements
    panel = panel.copy().replace(
        {
            99: np.nan,
            999: np.nan,
            "I dont know": np.nan,
            "I don't know": np.nan,
            "certainly not": 1,
            "certainly yes": 5,
            "certainly no": 1,
            "not applicable": np.nan,
        }
    )

    return panel


def _yes_no_maybe(panel):
    """
    Handle yes/no/maybe columns.

    """
    yes_no_maybe = [
        "believe_after_death",
        "believe_heaven",
        "believe_purgatory",
        "believe_hell",
        "believe_devil",
        "believe_adam_eve",
        "acknowledge_bible",
        "acknowledge_koran",
        "acknowledge_torah",
        "believe_praying",
        "religion_invention",
        "same_religion",
        "value_wife",
        "value_husband",
        "enter_virgin_women",
        "enter_virgin_men",
        "abortion_good",
        "believe_reincarnation",
        "believe_karma",
        "meditate",
    ]

    for column in yes_no_maybe:
        panel[column] = panel[column].copy().replace({4: np.nan})
        cat_type = CategoricalDtype(categories=["no", "maybe", "yes"], ordered=True)

        panel[column] = panel[column].astype(cat_type)

    yes_no = [
        "member_religion_parent",
        "member_religion",
        "member_religion_past",
        "nationality_dutch",
        "nationality_non_dutch",
        "nationality_turkish",
        "nationality_moroccan",
        "nationality_antillean",
        "nationality_surinamese",
        "nationality_indonesian",
        "nationality_other_non_western",
        "nationality_other_western",
        "birth_country_netherland",
        "birth_country_father_netherland",
        "brith_country_mother_netherland",
        "population_dutch",
        "population_turks",
        "population_kurds",
        "population_armenians",
        "population_moroccans",
        "population_berbers",
        "population_hindustanis",
        "population_creoles",
        "population_javanese",
        "population_chinese",
        "population_surinamese",
        "population_antilleans",
        "population_curacaoans",
        "population_arubans",
        "population_other",
        "nativ_language_dutch",
        "nativ_language_arab",
        "nativ_language_berber",
        "nativ_language_german",
        "nativ_language_frisian",
        "nativ_language_indonesian",
        "nativ_language_turkish",
        "nativ_language_flemish",
        "nativ_language_other",
    ]

    for column in yes_no:
        panel[column] = panel[column].replace(
            {
                "no": 0,
                "yes": 1,
                2: np.nan,
                3: np.nan,
                4: np.nan,
                5: np.nan,
                6: np.nan,
                7: np.nan,
                8: np.nan,
                9: np.nan,
            }
        )

    return panel


def _clean_categoricals(panel):
    """
    Some replacements then convert to category.

    """
    panel["nationality"] = panel["nationality"].astype("category")

    birth_country_columns = [
        "birth_country_cat",
        "birth_country_father_cat",
        "birth_country_mother_cat",
    ]

    # This variable is very weird. Different between waves.
    panel["birth_country_mother_cat"] = panel["birth_country_mother_cat"].replace(
        {"no": 2, "yes": 1}
    )

    for column in birth_country_columns:
        if column == "birth_country_mother_cat":
            panel[column] = panel[column].replace(
                {
                    1: "Turkey",
                    2: "Morocco",
                    3: "Dutch Antilles",
                    4: "Surinam",
                    5: "Indonesia",
                    6: "other non-western country",
                    7: "other western country",
                }
            )
        else:
            panel[column] = (
                panel[column].replace({7: "other western country"}).astype("category")
            )

    panel["home_language_dutch"] = (
        panel["home_language_dutch"].replace({2: "other language"}).astype("category")
    )

    panel["home_language_cat"] = (
        panel["home_language_cat"].replace({8: "other language"}).astype("category")
    )

    return panel


def _to_ordered_categoricals(panel):
    """
    Convert object column to ordered categorical. Some cleaning first.

    """
    # Clean columns first: general replacements
    panel["believe_god"] = panel["believe_god"].replace(
        {6: "I believe without any doubt that God exists"}
    )

    panel["speak_dialect"] = panel["speak_dialect"].replace({0: "no", 4: "no"})

    panel = panel.copy().replace(
        {
            "speak_dutch_partner": {4: np.nan},  # 4 = NA
            "speak_dutch_children": {4: np.nan},
            "speak_dutch_friends": {4: np.nan},
            "speak_dutch_colleagues": {4: np.nan},
        }
    )

    for column in ["trouble_dutch_speak", "trouble_dutch_read"]:
        panel[column] = panel[column].replace({3: "no, never"})

    ordered_cat_dict = {
        "religion": {
            "variables": [
                "attendance_religious_parent",
                "attendance_religious",
                "pray",
            ],
            "categories": [  # attendace_religion_parent/pray
                "never",
                "less often",
                "only on special religious holidays",
                "at least once a month",
                "once a week",
                "more than once a week",
                "every day",
            ],
        },
        "god": {
            "variables": ["believe_god"],
            "categories": [  # believe_god
                "I do not believe in God",
                "I do not know if God exists, and I do not believe that we "
                "have any way of knowing",
                "I do not believe in a God that is personally concerned with "
                "each of us, but I do believe in a higher power",
                "at some moments I do believe in God, at other moments I dont",
                "I believe in God, although I have my doubts",
                "I believe without any doubt that God exists",
            ],
        },
        "speak": {
            "variables": ["speak_dialect"],
            "categories": [  # speak_dialect
                "no",
                "yes, once in while",
                "yes, regularly",
                "yes, daily",
            ],
        },
        "dutch": {
            "variables": [
                "speak_dutch_partner",
                "speak_dutch_children",
                "speak_dutch_friends",
                "speak_dutch_colleagues",
            ],
            "categories": [  # speak_dutch_x
                "no, never",
                "yes, sometimes",
                "yes, often/always",
            ],
        },
        "trouble": {
            "variables": ["trouble_dutch_speak", "trouble_dutch_read"],
            "categories": [  # trouble_dutch_x
                "no, never",
                "yes, sometimes",
                "yes, often have trouble/do not speak Dutch",
            ],
        },
    }

    for key in ordered_cat_dict.keys():
        cat_type = CategoricalDtype(
            categories=ordered_cat_dict[key]["categories"], ordered=True
        )
        for column in ordered_cat_dict[key]["variables"]:
            panel[column] = panel[column].astype(cat_type)

    return panel
