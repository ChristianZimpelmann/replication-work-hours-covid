"""
Makes a dataframe collecting various individual characteristics
"""
from shutil import copyfile

import pandas as pd
import pytask
from config import CORONA_INSTALL
from config import CORONA_PREP_LISS
from config import OUT_DATA_CORONA_INSTALL
from config import OUT_DATA_CORONA_PREP
from corona_preparation.utils_corona_prep import load_data_set
from corona_preparation.utils_corona_prep import save_and_check_data_set


def find_partner(background):
    partners = background.copy().query(
        "hh_position in ['Household head', 'Unwedded partner', 'Wedded partner'] & hhh_partner"
    )[["hh_id", "gender", "age"]]

    # Take care of households with more than 2 "partners"
    # ToDo: do this more sophisticated (based on hh_position, gender, age)

    partners = partners.drop(
        [815506, 802443, 893500, 841311, 800049, 870505, 886366, 897295],
        errors="ignore",
    )
    if partners.groupby("hh_id")["age"].count().max() > 2:
        duplicates = (
            partners.groupby("hh_id")["age"]
            .count()
            .loc[partners.groupby("hh_id")["age"].count() > 2]
            .index
        )
        error_mess = (
            f"There are households with more than 2 partners: {duplicates}. "
            + "Please drop some observations"
        )
        raise ValueError(error_mess)

    # Merge id of other member in household
    df_incl_partner_id = pd.merge(
        left=partners.reset_index(),
        right=partners.reset_index()[["hh_id", "personal_id"]],
        how="left",
        left_on=["hh_id"],
        right_on=["hh_id"],
        suffixes=["", "_partner"],
    )[["personal_id", "personal_id_partner"]]

    # Throw out observation in which own personal_id was merged
    df_incl_partner_id = df_incl_partner_id.query("personal_id != personal_id_partner")

    res = partners.join(df_incl_partner_id.set_index("personal_id")).sort_index()

    res = res.join(
        partners.drop("hh_id", axis=1), on="personal_id_partner", rsuffix="_partner"
    )

    return res


def create_partner_links_male_female(partner_links):
    """Create partner links that give male and female partner for each hh_id

    Args:
        partner_links (DataFrame): partner links from each subject to their partner

    Returns:
        DataFrame: partner links male--female
    """
    res = partner_links.query(
        "(gender == 'male' & gender_partner == 'female')"
        + " | gender == 'female' & gender_partner == 'male'"
    ).copy()
    res = res.reset_index()

    sel_male = res["gender"] == "male"
    sel_female = res["gender"] == "female"

    for col in ["personal_id", "gender", "age"]:
        res.loc[sel_male, col + "_man"] = res.loc[sel_male, col]
        res.loc[sel_male, col + "_woman"] = res.loc[sel_male, col + "_partner"]
        res.loc[sel_female, col + "_woman"] = res.loc[sel_female, col]
        res.loc[sel_female, col + "_man"] = res.loc[sel_female, col + "_partner"]
    res = res[["hh_id", "personal_id_man", "age_man", "personal_id_woman", "age_woman"]]
    res = res.set_index("hh_id").drop_duplicates().sort_values("hh_id")

    return res


PRODUCES = [
    OUT_DATA_CORONA_PREP / "partner_links.pickle",
    OUT_DATA_CORONA_PREP / "partner_links_male_female.pickle",
    OUT_DATA_CORONA_PREP / "partner_links.dta",
    OUT_DATA_CORONA_PREP / "partner_links_male_female.dta",
    OUT_DATA_CORONA_PREP / "partner_links.csv",
    OUT_DATA_CORONA_PREP / "partner_links_male_female.csv",
]

DEPENDS_ON = [
    OUT_DATA_CORONA_PREP / "background_data_merged.pickle",
    "utils_corona_prep.py",
]


@pytask.mark.skipif(not CORONA_PREP_LISS, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_create_hh_level_data_set(depends_on, produces):
    # Load data
    background = load_data_set("background_data_merged")

    # Build partner_links
    partner_links = find_partner(background)

    # Also build data set with personal_ids of man and woman in partnership
    partner_links_male_female = create_partner_links_male_female(partner_links)

    # Save data sets
    save_and_check_data_set(partner_links, "partner_links")
    save_and_check_data_set(partner_links_male_female, "partner_links_male_female")


PARAMETRIZATION = [(d_, OUT_DATA_CORONA_INSTALL / d_.name) for d_ in PRODUCES]


@pytask.mark.skipif(not CORONA_INSTALL, reason="skip corona tasks")
@pytask.mark.parametrize("depends_on, produces", PARAMETRIZATION)
def task_install_hh_level_data_set(depends_on, produces):
    copyfile(depends_on, produces)
