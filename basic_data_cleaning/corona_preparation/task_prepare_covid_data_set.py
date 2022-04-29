"""Makes a dataframe collecting various individual characteristics"""
from shutil import copyfile

import pandas as pd
import pytask
import yaml
from config import CORONA_INSTALL
from config import CORONA_PREP_LISS
from config import IN_SPECS_CORONA
from config import IN_SPECS_LISS
from config import OUT_DATA_CORONA_INSTALL
from config import OUT_DATA_CORONA_PREP
from corona_prep_specs.cleaning_config import BACKGROUND_VARS_IN_CORONA
from corona_prep_specs.cleaning_config import INFORMATION_TREATMENT_VARS_WAVE_2
from corona_preparation.clean_hh_income_var import create_cleaned_hh_income
from corona_preparation.utils_corona_prep import create_mhi5
from corona_preparation.utils_corona_prep import create_weighting
from corona_preparation.utils_corona_prep import load_data_set
from corona_preparation.utils_corona_prep import save_and_check_data_set
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file


def create_hh_income_df(data):
    temp = data.copy()
    cols = [x for x in temp.columns if x.startswith("hh_income_2020")]
    res = temp[cols].dropna(axis=0, how="all")
    res = res.groupby("personal_id").first()
    res = pd.wide_to_long(
        res.reset_index(), stubnames="hh_income", i="personal_id", j="period", sep="_"
    )
    res = res.rename({"hh_income": "net_income_hh"}, axis=1)
    res = res.reset_index()
    res["month"] = pd.to_datetime(res["period"], format="%Y%m")
    res = res.drop("period", axis=1)
    res = res.set_index(["personal_id"])

    # Add additional columns for May for which hh income is elicited twice
    # ToDO: If more months are asked twice, this should be generalized
    # (probably by transposing temp)
    res.loc[
        res["month"] == pd.to_datetime("2020-05-01"), "net_income_hh_202005_elic_06"
    ] = (
        data.loc[pd.IndexSlice[:, 202006], :]
        .reset_index()
        .set_index("personal_id")["hh_income_202005"]
    )
    res.loc[
        res["month"] == pd.to_datetime("2020-05-01"), "net_income_hh_202005_elic_09"
    ] = (
        data.loc[pd.IndexSlice[:, 202009], :]
        .reset_index()
        .set_index("personal_id")["hh_income_202005"]
    )

    res = res.reset_index().set_index(["personal_id", "month"]).sort_index()

    # create cleaned version of hh income variable
    res = create_cleaned_hh_income(res)

    save_and_check_data_set(res, "hh_income_data_set")


months_in_covid_data = [
    "2020_02",
    "2020_03",
    "2020_04",
    "2020_05",
    "2020_06",
    "2020_09",
    "2020_12",
]

PRODUCES = (
    [
        OUT_DATA_CORONA_PREP / f"covid_data_{month}.pickle"
        for month in months_in_covid_data
    ]
    + [
        OUT_DATA_CORONA_PREP / f"covid_data_{month}.dta"
        for month in months_in_covid_data
    ]
    + [
        OUT_DATA_CORONA_PREP / f"covid_data_{month}.csv"
        for month in months_in_covid_data
    ]
    + [
        OUT_DATA_CORONA_PREP / "hh_income_data_set.pickle",
        OUT_DATA_CORONA_PREP / "hh_income_data_set.dta",
        OUT_DATA_CORONA_PREP / "hh_income_data_set.csv",
        OUT_DATA_CORONA_PREP / "bg_vars_covid.pickle",
        OUT_DATA_CORONA_PREP / "bg_vars_covid.dta",
        OUT_DATA_CORONA_PREP / "bg_vars_covid.csv",
    ]
)


DEPENDS_ON = [
    OUT_DATA_CORONA_PREP / "background_data_merged.pickle",
    OUT_DATA_CORONA_PREP / "corona_selected.pickle",
    IN_SPECS_CORONA / "background_data_variable_description.csv",
    # ctx.path_to(ctx, "IN_SPECS_CORONA", "covid19_data_description.csv"),
    "utils_corona_prep.py",
]
# Load corona vars


@pytask.mark.skipif(not CORONA_PREP_LISS, reason="skip corona tasks")
@pytask.mark.depends_on(DEPENDS_ON)
@pytask.mark.produces(PRODUCES)
def task_prepare_covid_data_set(depends_on, produces):
    # Load corona vars
    corona = load_data_set("corona_full")
    rename_df = pd.read_csv(
        IN_SPECS_LISS / "xyx-corona-questionnaire_renaming.csv", sep=";"
    )

    # Put hh_income variable in separate file
    create_hh_income_df(corona)
    corona = corona.drop([c for c in corona if c.startswith("hh_income_")], axis=1)

    # Create additional period 202002 (pre-period)
    corona.index.names = ["personal_id", "period"]
    for period in [202002]:
        temp = (
            corona[[c for c in corona if c.endswith(str(period))]]
            .groupby(["personal_id"])
            .last()
        )
        temp = temp.reset_index()
        temp["period"] = period
        temp = temp.set_index(["personal_id", "period"])
        temp.columns = [c.replace(f"_{period}", "") for c in temp]
        corona = pd.concat([corona, temp])
        corona = corona.drop([c for c in corona if c.endswith(str(period))], axis=1)
    corona = corona.sort_index()

    # Create weighting
    corona = create_weighting(corona)

    # Make new index
    corona = corona.reset_index().drop(["wave"], axis=1)
    corona["month"] = pd.to_datetime(corona["period"], format="%Y%m")
    corona = corona.drop("period", axis=1)
    corona = corona.set_index(["personal_id", "month"])

    corona = set_types_file(
        panel=corona,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )

    # Save background variables
    save_corona_bg_vars(corona)

    # Throw out background variables and information treatment variables
    corona = corona.drop(
        BACKGROUND_VARS_IN_CORONA + INFORMATION_TREATMENT_VARS_WAVE_2, axis=1
    )

    # MHI-5 score
    for suffix in ["_month", "_7d"]:
        corona[f"mhi5{suffix}"] = create_mhi5(data=corona, suffix=suffix)

    for postfix in [
        "",
        "_september",
        "_october",
        "_november",
        "_pre_corona",
        "_expected_post",
        "_preferred_post",
    ]:

        # Total hours
        corona[f"hours_total{postfix}"] = (
            corona[f"hours_home{postfix}"] + corona[f"hours_workplace{postfix}"]
        )

        # Winsorize number of hours at 80 (total)
        sel = corona[f"hours_total{postfix}"] > 80

        for c in [
            f"hours_home{postfix}",
            f"hours_workplace{postfix}",
            f"hours_total{postfix}",
        ]:
            corona.loc[sel, c] = (
                corona.loc[sel, c] * 80 / corona.loc[sel, f"hours_total{postfix}"]
            )

    # some checks
    assert (
        not corona.isnull().all(axis=0).any()
    ), f"Only contain NaN values in columns {corona.columns[corona.isnull().all(axis=0)]}."

    assert (
        not corona.columns.isnull().any()
    ), f"There are NaN columns in the data set. {corona.columns[corona.columns.isnull()]}"

    # Save data sets by month
    for month in corona.index.unique(level="month"):
        temp = corona.loc[pd.IndexSlice[:, month], :].copy()

        # Drop variables that haven't been asked in this wave
        temp = temp.dropna(axis="columns", how="all")
        save_and_check_data_set(temp, "covid_data_" + str(month)[:7].replace("-", "_"))


def save_corona_bg_vars(corona):
    out = corona[BACKGROUND_VARS_IN_CORONA].query("month != '2020-02'").copy()

    # Replacing and renaming of some values and columns of the data frame.
    var_description = pd.read_csv(
        IN_SPECS_CORONA / "background_data_variable_description.csv", sep=";"
    ).replace({"bool": "boolean"})

    with open(IN_SPECS_CORONA / "background_data_merged_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    out = replace_values(
        out, replace_dict, var_description, raise_if_missing_vars=False
    )

    out = set_types_file(
        panel=out,
        rename_df=var_description,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )
    save_and_check_data_set(out, "bg_vars_covid")


PARAMETRIZATION = [(d_, OUT_DATA_CORONA_INSTALL / d_.name) for d_ in PRODUCES]


@pytask.mark.skipif(not CORONA_INSTALL, reason="skip corona tasks")
@pytask.mark.parametrize("depends_on, produces", PARAMETRIZATION)
def task_install_prepared_covid_datasets(depends_on, produces):
    copyfile(depends_on, produces)
