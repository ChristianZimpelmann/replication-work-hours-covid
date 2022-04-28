"""
Put data description together for corona data set
"""
from shutil import copyfile

import pandas as pd
import pytask
from config import CORONA_INSTALL
from config import CORONA_PREP_LISS
from config import IN_SPECS_CORONA
from config import IN_SPECS_LISS
from config import OUT_DATA_CORONA_INSTALL
from config import OUT_TABLES_CORONA


PRODUCES = OUT_TABLES_CORONA / "covid_variable_description.csv"

DEPENDS_ON = {
    "xyx-corona-questionnaire_renaming": IN_SPECS_LISS
    / "xyx-corona-questionnaire_renaming.csv",
    "corona_routing_original_vars": IN_SPECS_CORONA
    / "corona_routing_original_vars.csv",
}


@pytask.mark.skipif(not CORONA_PREP_LISS, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_merge_description_corona(depends_on, produces):
    renaming = pd.read_csv(depends_on["xyx-corona-questionnaire_renaming"], sep=";")
    routing = pd.read_csv(depends_on["corona_routing_original_vars"], sep=";")

    # merge one column for each wave that specifies the renaming
    wave_columns = [c for c in renaming if c.endswith(".dta")]

    # ToDo: Adjust once column name refers to wave and not file name
    for i, wave in enumerate(wave_columns[::-1]):
        w = routing.loc[routing["wave"] == i + 1]
        w = w.rename(columns={"routing": f"routing_wave_{i+1}"})
        renaming = renaming.merge(
            w[["original_name", f"routing_wave_{i+1}"]],
            how="left",
            left_on=wave,
            right_on="original_name",
        )
        renaming.drop("original_name", axis=1, inplace=True)
    renaming.to_csv(
        produces,
        sep=";",
        index=False,
    )


DEPENDS_ON = PRODUCES
PRODUCES = OUT_DATA_CORONA_INSTALL / "variable_descriptions" / DEPENDS_ON.name


@pytask.mark.skipif(not CORONA_INSTALL, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_install_corona_variable_description(depends_on, produces):
    copyfile(depends_on, produces)
