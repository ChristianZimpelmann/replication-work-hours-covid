"""
Contains time use cleaning
"""
from shutil import copyfile

import pytask
from config import CORONA_INSTALL
from config import CORONA_PREP_LISS
from config import OUT_DATA_CORONA_INSTALL
from config import OUT_DATA_CORONA_PREP
from corona_preparation.clean_time_use_detailed import wrap_further_time_use_cleaning
from corona_preparation.utils_corona_prep import load_data_set
from corona_preparation.utils_corona_prep import save_and_check_data_set


PRODUCES = (
    [
        OUT_DATA_CORONA_PREP / "time_use_back.pickle",
        OUT_DATA_CORONA_PREP / "time_use_202011.pickle",
        OUT_DATA_CORONA_PREP / "time_use_202004.pickle",
        OUT_DATA_CORONA_PREP / "time_use_202002.pickle",
        OUT_DATA_CORONA_PREP / "time_use_data_detailed.pickle",
    ]
    + [
        OUT_DATA_CORONA_PREP / "time_use_back.csv",
        OUT_DATA_CORONA_PREP / "time_use_202011.csv",
        OUT_DATA_CORONA_PREP / "time_use_202004.csv",
        OUT_DATA_CORONA_PREP / "time_use_202002.csv",
    ]
    + [
        OUT_DATA_CORONA_PREP / "time_use_back.dta",
        OUT_DATA_CORONA_PREP / "time_use_202011.dta",
        OUT_DATA_CORONA_PREP / "time_use_202004.dta",
        OUT_DATA_CORONA_PREP / "time_use_202002.dta",
    ]
)

DEPENDS_ON = [
    OUT_DATA_CORONA_PREP / "time_use_consumption_full.pickle",
    "utils_corona_prep.py",
    "clean_time_use_detailed.py",
]


@pytask.mark.skipif(not CORONA_PREP_LISS, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_time_use_data(depends_on, produces):
    # Load corona vars
    time_use = load_data_set("time_use_consumption_full")

    # Create additional period 202002 (pre-period)
    time_use.index.names = ["personal_id", "period"]
    for period in [202002]:
        temp = (
            time_use[[c for c in time_use if c.endswith(str(period))]]
            .groupby(["personal_id"])
            .last()
        )
        temp = temp.reset_index()
        temp["period"] = period
        temp = temp.set_index(["personal_id", "period"])
        temp.columns = [c.replace(f"_{period}", "") for c in temp]
        time_use = time_use.append(temp).sort_index()

    save_and_check_data_set(
        time_use.query("period==202002").dropna(axis=1, how="all"), "time_use_202002"
    )
    save_and_check_data_set(
        time_use.query("period==202004").dropna(axis=1, how="all"), "time_use_202004"
    )
    save_and_check_data_set(
        time_use.query("period==202011").dropna(axis=1, how="all"), "time_use_202011"
    )
    save_and_check_data_set(
        time_use.query("period not in [202004, 202002, 202011]").dropna(
            axis=1, how="all"
        ),
        "time_use_back",
    )
    wrap_further_time_use_cleaning(time_use)


PARAMETRIZATION = [(d_, OUT_DATA_CORONA_INSTALL / d_.name) for d_ in PRODUCES]


@pytask.mark.skipif(not CORONA_INSTALL, reason="skip corona tasks")
@pytask.mark.parametrize("depends_on, produces", PARAMETRIZATION)
def task_install_time_use_data(depends_on, produces):
    copyfile(depends_on, produces)
