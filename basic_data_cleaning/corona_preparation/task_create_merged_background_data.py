from functools import reduce
from shutil import copyfile

import pandas as pd
import pytask
import yaml
from config import CORONA_INSTALL
from config import CORONA_PREP_LISS
from config import IN_SPECS_CORONA
from config import OUT_DATA_CORONA_INSTALL
from config import OUT_DATA_CORONA_PREP
from config import OUT_DATA_LISS
from corona_preparation.task_load_data_sets import (
    select_last_obs_from_last_two_pre_covid_waves,
)
from corona_preparation.utils_corona_prep import create_new_background_variables
from corona_preparation.utils_corona_prep import load_data_set
from corona_preparation.utils_corona_prep import save_and_check_data_set
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file


def create_background_data_wide():
    var_description = pd.read_csv(
        IN_SPECS_CORONA / "background_data_variable_description.csv", sep=";"
    ).replace({"bool": "boolean"})

    # Load in data sets
    data_sets = {
        ds_name: load_data_set(ds_name)
        for ds_name in var_description["liss-data-set"].value_counts().index
        if ds_name != "background_selected"
    }
    # Get Background Data
    background_files = ["background_full_2020.pickle", "background_full_2019.pickle"]
    background_df = pd.concat(
        [pd.read_pickle(OUT_DATA_LISS / file) for file in background_files]
    )
    background_df = background_df.reset_index()

    data_sets["background_selected"] = select_last_obs_from_last_two_pre_covid_waves(
        background_df, tolerance=103
    )

    # Select variables
    for ds_name in data_sets:
        variables_used = var_description.loc[
            var_description["liss-data-set"] == ds_name, "import_name"
        ].values
        data_sets[ds_name] = data_sets[ds_name][
            [x for x in variables_used if x in data_sets[ds_name].columns]
        ]

    # Merge all studies
    data_merged = reduce(
        lambda x, y: pd.merge(x, y, on="personal_id", how="outer"), data_sets.values()
    )

    # Replacing and renaming of some values and columns of the data frame.
    with open(IN_SPECS_CORONA / "background_data_merged_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)
    data_merged = replace_values(data_merged, replace_dict, var_description)

    # Set types
    data_merged = set_types_file(
        panel=data_merged,
        rename_df=var_description,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )

    # Rename variables
    data_merged = data_merged.rename(
        {
            var_description.loc[i, "import_name"]: var_description.loc[i, "new_name"]
            for i in var_description.index
            if not pd.isna(var_description.loc[i, "import_name"])
        },
        axis=1,
    )
    data_merged = create_new_background_variables(data_merged)

    # Remove nan cols. HOTFIX! They should not even arise!
    data_merged = data_merged.loc[:, ~data_merged.columns.isna()]

    # Save full data set
    save_and_check_data_set(data_merged, "background_data_merged")


def clean_and_save_monthly_background(months):
    for month in months:
        year = str(month)[:4]
        path = OUT_DATA_LISS / f"background_full_{year}.pickle"
        df = pd.read_pickle(path)
        out = df.query(f"date_fieldwork=={int(month)}")
        out.to_pickle(OUT_DATA_CORONA_PREP / f"background_{month}")


data_sets = yaml.safe_load(open(IN_SPECS_CORONA / "data_sets_corona_prep.yaml", "rb"))

DEPENDS_ON = (
    [OUT_DATA_CORONA_PREP / f"{ds_name}_selected.pickle" for ds_name in data_sets]
    + [
        IN_SPECS_CORONA / "background_data_variable_description.csv",
        IN_SPECS_CORONA / "background_data_long_variable_description.csv",
        "utils_corona_prep.py",
    ]
    + [IN_SPECS_CORONA / "data_sets_corona_prep.yaml"]
)
PRODUCES = [
    OUT_DATA_CORONA_PREP / "background_data_merged.pickle",
    #  OUT_DATA_CORONA_PREP/ "background_data_merged_long.pickle",
    OUT_DATA_CORONA_PREP / "background_data_merged.dta",
    OUT_DATA_CORONA_PREP / "background_data_merged.csv",
]
for month in [202003, 202004]:
    year = str(month)[:4]
    DEPENDS_ON.append(OUT_DATA_LISS / f"background_full_{year}.pickle")
    PRODUCES.append(OUT_DATA_CORONA_PREP / f"background_{month}")


@pytask.mark.skipif(not CORONA_PREP_LISS, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_create_background_wide(depends_on, produces):
    create_background_data_wide()
    clean_and_save_monthly_background([202003, 202004])
    # create_background_data_long()


PARAMETRIZATION = [(d_, OUT_DATA_CORONA_INSTALL / d_.name) for d_ in PRODUCES]


@pytask.mark.skipif(not CORONA_INSTALL, reason="skip corona tasks")
@pytask.mark.parametrize("depends_on, produces", PARAMETRIZATION)
def task_install_merged_background_data(depends_on, produces):
    copyfile(depends_on, produces)
