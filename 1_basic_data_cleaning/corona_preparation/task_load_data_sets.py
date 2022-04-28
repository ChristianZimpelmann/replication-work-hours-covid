"""
Plug dataset together
"""
from shutil import copyfile

import pytask
import yaml
from config import CORONA_INSTALL
from config import CORONA_PREP_LISS
from config import IN_SPECS_CORONA
from config import OUT_DATA_CORONA_INSTALL
from config import OUT_DATA_CORONA_PREP
from config import OUT_DATA_LISS
from corona_preparation.utils_corona_prep import load_data_set_liss
from corona_preparation.utils_corona_prep import save_and_check_data_set


def select_last_obs_from_last_two_pre_covid_waves(df, tolerance=101):
    # Select the last observation within the last two waves
    # Drop columns that haven't been asked within the last two years
    df_ = df[~df["date_fieldwork"].isna()].dropna(axis=1, how="all").copy()

    filter_year = df_["date_fieldwork"].map(lambda x: x < 202003)
    df_ = df_[filter_year]

    if len(df_["date_fieldwork"].unique()) > 1:
        last_date = sorted(df_["date_fieldwork"].unique())[-1]
        filter_last_df = df_["date_fieldwork"].map(lambda x: x > last_date - tolerance)
        df_ = df_[filter_last_df]
        df_["date_fieldwork"] = df_["date_fieldwork"].astype("float")
        idxmax = df_.groupby(["personal_id"])["date_fieldwork"].idxmax()
        df_ = df_.loc[idxmax]
        df_ = df_.reset_index().set_index("personal_id").drop(columns=["year"])

    return df_


def _stretch_year(x):
    out = str(x)
    if len(out) == 6:
        return float(out)
    elif len(out) == 4:
        return float(f"{out}00")


data_sets = yaml.safe_load(open(IN_SPECS_CORONA / "data_sets_corona_prep.yaml", "rb"))

PRODUCES = (
    [
        OUT_DATA_CORONA_PREP / f"{ds_name}_selected.pickle"
        for ds_name in data_sets
        if data_sets[ds_name]["selected"]
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}_selected.csv"
        for ds_name in data_sets
        if data_sets[ds_name]["selected"]
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}_selected.dta"
        for ds_name in data_sets
        if data_sets[ds_name]["stata"] and data_sets[ds_name]["selected"]
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}.pickle"
        for ds_name in data_sets
        if type(data_sets[ds_name]["subset"]) is list
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}.csv"
        for ds_name in data_sets
        if type(data_sets[ds_name]["subset"]) is list
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}.dta"
        for ds_name in data_sets
        if data_sets[ds_name]["stata"] and type(data_sets[ds_name]["subset"]) is list
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}_full.pickle"
        for ds_name in data_sets
        if data_sets[ds_name]["subset"] == "full"
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}_full.csv"
        for ds_name in data_sets
        if data_sets[ds_name]["subset"] == "full"
    ]
    + [
        OUT_DATA_CORONA_PREP / f"{ds_name}_full.dta"
        for ds_name in data_sets
        if data_sets[ds_name]["subset"] == "full" and data_sets[ds_name]["stata"]
    ]
)

DEPENDS_ON = [OUT_DATA_LISS / f"{ds_name}.pickle" for ds_name in data_sets] + [
    "utils_corona_prep.py",
    IN_SPECS_CORONA / "data_sets_corona_prep.yaml",
]


@pytask.mark.skipif(not CORONA_PREP_LISS, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_load_data_sets(depends_on, produces):
    # Load in data sets
    data_sets = yaml.safe_load(
        open(IN_SPECS_CORONA / "data_sets_corona_prep.yaml", "rb")
    )
    # Select correct year(s) for each variable
    for ds_name, specs in data_sets.items():
        # Load data set
        df_full = load_data_set_liss(ds_name)

        if "date_fieldwork" not in df_full.columns:
            df_full["date_fieldwork"] = df_full.index.get_level_values(1).map(
                lambda x: _stretch_year(x)
            )

        df_selected = df_full.copy()

        if specs["selected"]:
            df_selected = select_last_obs_from_last_two_pre_covid_waves(df_selected)
            df_selected = df_selected.dropna(axis="columns", how="all")

            # Save files
            save_and_check_data_set(
                df_selected, f"{ds_name}_selected", stata=specs["stata"]
            )

        if type(specs["subset"]) is list:
            years = specs["subset"]
            temp = df_full.query(f"year in {years}")
            temp = temp.dropna(axis="columns", how="all")

            save_and_check_data_set(temp, f"{ds_name}", stata=specs["stata"])

        if specs["subset"] == "full":
            # manually drop columns that are all missing
            if ds_name == "corona":
                df_full = df_full.drop(
                    ["impact_college_sec_child4", "impact_college_sec_child5"], axis=1
                )
            save_and_check_data_set(df_full, f"{ds_name}_full", stata=specs["stata"])


PARAMETRIZATION = [
    (d_, OUT_DATA_CORONA_INSTALL / "unmerged_files" / d_.name)
    for d_ in PRODUCES
    if d_
    not in [
        OUT_DATA_CORONA_PREP / "corona_full.pickle",
        OUT_DATA_CORONA_PREP / "time_use_consumption_full.pickle",
    ]
]


@pytask.mark.skipif(not CORONA_INSTALL, reason="skip corona tasks")
@pytask.mark.parametrize("depends_on, produces", PARAMETRIZATION)
def task_install_loaded_datasets(depends_on, produces):
    copyfile(depends_on, produces)
