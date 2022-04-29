"""Prepare data for work-childcare anlysis.

Output:
    - "../../data/work-childcare-long.parquet"
    - "../../data/work-childcare-wide.parquet"

Contains all additionally necessary variables, and partners' variables.
If you want to add additional variables, please do so in variables_to_keep.py
"""
import sys
import warnings

import numpy as np
import pandas as pd

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.data_management.data_management_utils import (
    set_types_file,
)
from project_specific_analyses.data_management.recode_reasons import (
    recode_reasons_for_other_responses,
)
from project_specific_analyses.data_management.variables_to_keep import (
    background_variables,
)
from project_specific_analyses.data_management.variables_to_keep import covid_vars
from project_specific_analyses.data_management.variables_to_keep import other
from project_specific_analyses.data_management.variables_to_keep import (
    time_invariant_vars,
)
from project_specific_analyses.data_management.variables_to_keep import (
    timevarying_variables,
)
from project_specific_analyses.library.panel_functions import get_baseline


def generate_baseline_variables(covid):
    """Generate variables that calculate the difference to baseline."""
    covid = covid.copy()
    covid = covid.sort_index()
    covid = get_baseline(covid, "out_of_laborf_baseline", "out_of_laborf")
    covid = get_baseline(covid, "not_working_baseline", "not_working")
    covid["change_out_of_laborf"] = (
        covid["out_of_laborf"] - covid["out_of_laborf_baseline"]
    )
    covid["change_not_working"] = covid["not_working"] - covid["not_working_baseline"]

    # Calc differences to baseline
    for uncond in ["", "_uncond"]:

        # Hours home
        covid = get_baseline(
            covid, f"hours_home{uncond}_baseline", f"hours_home{uncond}"
        )
        covid[f"abs_change_hours_home{uncond}"] = (
            covid[f"hours_home{uncond}"] - covid[f"hours_home{uncond}_baseline"]
        )
        covid[f"rel_change_hours_home{uncond}"] = (
            covid[f"abs_change_hours_home{uncond}"]
            / covid[f"hours_home{uncond}_baseline"]
        )
        # Hours total
        for hours in ["hours", "hours_tu"]:

            covid = get_baseline(
                covid,
                f"{hours}{uncond}_baseline",
                f"{hours}_total{uncond}",
                baseline="2020-02-01" if hours == "hours" else "2019-11-01",
            )

            covid[f"abs_change_{hours}{uncond}"] = (
                covid[f"hours_total{uncond}"] - covid[f"{hours}{uncond}_baseline"]
            )
            covid[f"rel_change_{hours}{uncond}"] = (
                covid[f"abs_change_{hours}{uncond}"]
                / covid[f"{hours}{uncond}_baseline"]
            )
            covid.loc[
                covid[f"{hours}{uncond}_baseline"] == 0, f"rel_change_{hours}{uncond}"
            ] = np.nan

            # Winsorized values"
            for rel in [f"abs_change_{hours}{uncond}", f"rel_change_{hours}{uncond}"]:
                q02 = covid[rel].quantile(0.02)
                q98 = covid[rel].quantile(0.98)
                covid[rel + "_winsorize"] = covid[rel].copy()
                covid.loc[covid[rel] < q02, rel + "_winsorize"] = q02
                covid.loc[covid[rel] > q98, rel + "_winsorize"] = q98

    # Home share
    covid = get_baseline(covid, "home_share_baseline", "home_share")

    return covid


def generate_new_variables(covid):
    covid["March_April"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-03-01", "2020-04-01"]], "March_April"] = 1
    covid["May_June"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-05-01", "2020-06-01"]], "May_June"] = 1
    covid["March"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-03-01"]], "March"] = 1
    covid["April"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-04-01"]], "April"] = 1
    covid["May"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-05-01"]], "May"] = 1
    covid["June"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-06-01"]], "June"] = 1
    covid["September"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-09-01"]], "September"] = 1
    covid["December"] = 0
    covid.loc[pd.IndexSlice[:, ["2020-12-01"]], "December"] = 1
    # Full time / part time dummies
    covid["work_status_spec"] = covid["work_status"].replace(
        {
            "social assistance": "not working",
            "retired": "not working",
            "employed": "full time",
            "homemaker": "not working",
            "self-employed": "self-employed",
            "unemployed": "not working",
            "student or trainee": "not working",
            "other": "not working",
        }
    )
    covid.loc[
        (covid["work_status_spec"] == "full time") & (covid["hours_total"] <= 30),
        "work_status_spec",
    ] = "part time"
    covid["work_status_spec"] = pd.Categorical(covid["work_status_spec"])
    covid = get_baseline(covid, "work_status_spec_baseline", "work_status_spec")
    covid["work_status_spec_short"] = covid["work_status_spec"].cat.remove_categories(
        ["not working"]
    )
    covid = get_baseline(
        covid, "work_status_spec_short_baseline", "work_status_spec_short"
    )

    covid["fulltime_baseline_covid"] = (covid["hours_baseline"].dropna() > 30) * 1
    covid["parttime_baseline_covid"] = 1 - covid["fulltime_baseline_covid"].dropna()
    covid["fulltime_baseline_w_s_2019"] = (
        covid["work_contract_hours_2019"].dropna() > 30
    ) * 1
    covid.loc[
        covid.work_contract_hours_2019 == 0, "fulltime_baseline_w_s_2019"
    ] = np.nan
    covid["parttime_baseline_w_s_2019"] = 1 - covid["fulltime_baseline_w_s_2019"]

    covid["fulltime_baseline_w_s_2020"] = (
        covid["work_contract_hours_2020"].dropna() > 30
    ) * 1
    covid.loc[
        covid.work_contract_hours_2020 == 0, "fulltime_baseline_w_s_2020"
    ] = np.nan
    covid["parttime_baseline_w_s_2020"] = 1 - covid["fulltime_baseline_w_s_2020"]

    # Create Part-time
    covid = get_baseline(
        covid, "change_empl_baseline", "change_empl", baseline="2020-05-01"
    )
    covid["parttime_baseline"] = covid["parttime_baseline_w_s_2020"]
    changed_empl = covid.change_empl_baseline.isin(
        [
            "Ik heb een arbeidscontract met meer uren",
            "Anders, namelijk...",
            "Ik heb een arbeidscontract met minder uren",
        ]
    )
    covid.loc[changed_empl, "parttime_baseline"] = covid.loc[
        changed_empl, "parttime_baseline_w_s_2019"
    ]

    covid.loc[covid.parttime_baseline.isnull(), "parttime_baseline"] = covid.loc[
        covid.parttime_baseline.isnull(), "parttime_baseline_covid"
    ]
    covid.loc[covid.not_working_baseline == 1, "parttime_baseline"] = np.nan
    covid["fulltime_baseline"] = 1 - covid["parttime_baseline"].dropna()

    # Part time time use
    self_employed = covid.work_status_baseline == "self-employed"
    covid["part_time_tu"] = covid["parttime_baseline"]
    w19 = covid.index.get_level_values("month") == "2019-11-01"
    covid.loc[(w19 & ~self_employed), "part_time_tu"] = covid.loc[
        (w19 & ~self_employed), "parttime_baseline_w_s_2019"
    ]
    covid.loc[(w19 & self_employed), "part_time_tu"] = (
        covid.loc[(w19 & self_employed), "hours_work"] <= 30
    ) * 1

    covid.loc[(covid.part_time_tu.isnull() & w19), "part_time_tu"] = (
        covid.loc[(covid.part_time_tu.isnull() & w19), "hours_work"] <= 30
    ) * 1

    # Labor force status
    covid["labor_force"] = np.nan
    condition = (covid.parttime_baseline == 1) & (covid.max_hours_total > 0)
    covid.loc[condition, "labor_force"] = "part-time"
    covid.loc[(covid.out_of_laborf_baseline == 1), "labor_force"] = "out of labor force"

    condition = (covid.fulltime_baseline == 1) & (covid.max_hours_total > 0)
    covid.loc[condition, "labor_force"] = "full-time"
    covid.loc[covid.unemployed_baseline == 1, "labor_force"] = "unemployed"
    covid["labor_force"] = pd.Categorical(
        covid["labor_force"],
        categories=["out of labor force", "unemployed", "part-time", "full-time"],
        ordered=True,
    )
    # Coarse labor force status
    covid["labor_force_coarse"] = covid["labor_force"].astype(str)
    covid.loc[
        covid.labor_force.isin(["unemployed", "out of labor force"]),
        "labor_force_coarse",
    ] = "not working"
    covid["labor_force_coarse"] = pd.Categorical(
        covid.labor_force_coarse,
        categories=["not working", "part-time", "full-time"],
        ordered=True,
    )
    # Present in march and april
    covid["ones"] = 1
    c = (
        covid.query("month.isin(['2020-04-01', '2020-03-01'])")
        .groupby("personal_id")["ones"]
        .sum()
    )
    c = c > 1
    c.name = "pres_in_march_april"
    covid = covid.join(c)

    # Take average march april in hours
    mean = (
        covid.query("month.isin(['2020-04-01', '2020-03-01'])")
        .groupby("personal_id")["hours_total_uncond"]
        .mean()
    )
    mean.name = "hours_total_uncond_mean_march_april"
    covid = covid.join(mean)
    covid["hours_total_mean_ma"] = covid["hours_total_uncond"]
    covid.loc[
        covid.index.get_level_values("month").isin(["2020-04-01", "2020-03-01"]),
        "hours_total_mean_ma",
    ] = covid.loc[
        covid.index.get_level_values("month").isin(["2020-04-01", "2020-03-01"]),
        "hours_total_uncond_mean_march_april",
    ]
    condition = (
        covid.index.get_level_values("month").isin(["2020-03-01"])
        & covid.pres_in_march_april
    )
    covid.loc[condition, "hours_total_mean_ma"] = np.nan

    # average hours reduction
    for abs_rel in ["abs", "rel"]:
        temp = covid.query("month > '2020-02-01'")[[f"{abs_rel}_change_hours_uncond"]]
        temp = temp.unstack("month").sort_index(axis=1).droplevel(0, axis=1)
        temp.columns = [f"{abs_rel}_change_hours_uncond_{str(c)[5:7]}" for c in temp]
        temp[f"{abs_rel}_change_hours_uncond_avg_0305"] = temp[
            [
                f"{abs_rel}_change_hours_uncond_03",
                f"{abs_rel}_change_hours_uncond_04",
                f"{abs_rel}_change_hours_uncond_05",
            ]
        ].mean(axis=1)
        temp[f"{abs_rel}_change_hours_uncond_avg_0304"] = temp[
            [
                f"{abs_rel}_change_hours_uncond_03",
                f"{abs_rel}_change_hours_uncond_04",
            ]
        ].mean(axis=1)
        covid = covid.reset_index().set_index("personal_id")
        covid = covid.join(temp)
        covid = covid.reset_index().set_index(["personal_id", "month"])

    # expectations and concerns
    covid["concern_4w_job"] = covid["concern_4w_unemp"].fillna(
        covid["concern_4w_company"]
    )
    covid["p_2m_lost"] = covid["p_2m_employee_lost"].fillna(
        covid["p_3m_selfempl_shutdown"]
    )
    for c in [
        "p_2m_employee_keep",
        "p_2m_employee_keep_gov",
        "p_2m_employee_lost",
        "p_2m_employee_other",
        "p_2m_employee_unemployed",
        "p_2m_employee_new_job",
        "p_2m_lost",
        "p_3m_selfempl_shutdown",
        "concern_4w_job",
    ]:
        covid = get_baseline(covid, c + "_baseline", c, baseline="2020-03-01")

    # Create variables that fill subject that became unemployed until may with 0 or 1
    covid = covid.reset_index()
    for value in [0, 1]:
        covid[f"applied_any_policy_05_fill{value}"] = covid["applied_any_policy_05"]
        covid.loc[
            (covid["month"] == "2020-05-01")
            & (covid["not_working"] == 1)
            & (covid["not_working_baseline"] == 0),
            f"applied_any_policy_05_fill{value}",
        ] = value
        covid[f"applied_any_policy_05_fill{value}"] = (
            covid.groupby("personal_id")[f"applied_any_policy_05_fill{value}"]
            .bfill()
            .ffill()
        )
    covid = covid.set_index(["personal_id", "month"])

    # Make groups variables
    var = "net_income"
    covid[var + "_groups"] = pd.cut(
        covid[var],
        [-1, 1700, 2300, 10000000],
        labels=["below 1700", "bet. 1700 and 2300", "above 2300"],
    )
    var = "gross_income"
    covid[var + "_groups"] = pd.cut(
        covid[var],
        [-1, 2500, 3500, 10000000],
        labels=["below 2500", "bet. 2500 and 3500", "above 3500"],
    )
    covid["net_income_hh_eqv_groups"] = pd.qcut(
        covid["net_income_hh_eqv"],
        3,
        labels=["lower tercile", "middle tercile", "upper tercile"],
    )
    covid["female"] = (covid["gender"].dropna() == "female").astype(int)
    covid["age_groups"] = pd.cut(
        covid["age"], [0, 35, 55, 70], labels=["below 35", "36-55", "above 55"]
    )
    # Generate age bins
    covid["age_bins"] = pd.cut(covid.age, bins=range(0, 100, 10))
    covid["age_bins"].cat.categories = [
        str(c) for c in covid["age_bins"].cat.categories
    ]

    # Fix hhh_partner
    covid.loc[covid.hhh_partner == 1, "hhh_partner"] = True
    covid.loc[covid.hhh_partner == 0, "hhh_partner"] = False
    covid["hhh_partner"] = covid["hhh_partner"].astype("boolean")

    # Create high_edu variable
    covid["high_edu"] = (covid["edu"] == "tertiary").astype(float)
    covid["abs_change_hours_uncond_avg_0304_groups"] = pd.cut(
        covid["abs_change_hours_uncond_avg_0304"],
        [-100, -20, -0.1, 100],
        labels=[
            "decreased at least 20h",
            "decreased less than 20h",
            "did not decrease",
        ],
    )
    # ToDo: Create these groups for rel changes.
    return covid


def merge_background_data(background, covid, background_2019, background_full):
    """Merge in relevant background varaiables.

    Args:
        background (pd.DataFrame): df with background info as wide format.
        covid (pd.DataFrame): covid data set in long format
        covid_variables (list): list of columns names to keep from
                                the covid data set.

    Return:
        Merged background and covid data set with respective columns.

    """

    # Merge quasi-timeconstant background variables
    covid = covid.reset_index()
    covid = pd.merge(
        covid,
        background[background_variables],
        on="personal_id",
        how="left",
        suffixes=["_tu", ""],
    )
    covid.set_index(["personal_id", "month"], inplace=True)

    # clean background
    covid = clean_background_data(covid, work_schooling)

    # Merge background data that is potentially time varying
    # Split up data into 2019 and 2020
    covid_2019 = covid.query("month == '2019-11-01'").copy()
    covid_2020 = covid.query("month != '2019-11-01'").copy()

    # Check for duplicated columns
    colu_covid = set(covid_2019.columns)
    colu_2019 = set(background_2019.columns)
    joint = colu_covid.intersection(colu_2019)
    if len(joint) == 0:
        warnings.warn(
            f"{joint} are both in covid or time use and in background data and will be renamed in merge."
        )

    # Fix that gender is ordered in background data
    # ToDo: remove when fixed
    background_2019["gender"] = background_2019["gender"].cat.as_unordered()

    # Merge in data and put back together again
    covid_2019 = pd.merge(
        covid_2019,
        background_2019,
        right_index=True,
        left_index=True,
        how="left",
        suffixes=("", "_2019"),
    )
    covid_2020 = pd.merge(
        covid_2020,
        background[timevarying_variables + other],
        right_index=True,
        left_index=True,
        how="left",
        suffixes=("", "_2020"),
    )
    covid = pd.concat([covid_2019, covid_2020], axis=0)

    # Also merge net_income_hh from last two years of background data
    background_full["net_income_2y_equiv"] = background_full["net_income_hh"] / np.sqrt(
        background_full["hh_members"]
    )
    net_income_2y_equiv = (
        background_full.loc[pd.IndexSlice[:, [2018, 2019]], :]
        .groupby("hh_id")["net_income_2y_equiv"]
        .mean()
    )
    covid = pd.merge(
        left=covid,
        right=net_income_2y_equiv,
        left_on="hh_id",
        right_index=True,
        how="left",
    )
    _q = pd.qcut(covid["net_income_2y_equiv"], q=5, labels=False)
    covid["net_income_2y_equiv_q"] = _q + 1
    _q = pd.qcut(covid["net_income_2y_equiv"], q=3, labels=False)
    covid["net_income_2y_equiv_q3"] = _q + 1
    for var in ["net_income_2y_equiv_q", "net_income_2y_equiv_q3"]:
        covid[var] = pd.Categorical(covid[var])
    return covid


def merge_variables_from_work_schooling(data, ws_vars):
    """Merge variables from 2020 from work schooling

    Args:
        data (DataFrame): data without work schooling 2020 variables
        ws_vars (list): variables to be merged

    Returns:
        DataFrame: new data
    """

    # Load work schooling data and replace some values
    work_schooling = pd.read_pickle(
        ppj("IN_DATA", "unmerged_files", "work_schooling_full.pickle")
    )
    RENAME_PROFESSION = {
        "higher academic or independent profession (e.g. architect, physician, scholar, academic instructor, engineer)": "higher_academic",
        "higher supervisory profession (e.g. manager, director, owner of large company, supervisory civil servant)": "higher_supervisory",
        "intermediate academic or independent profession (e.g. teacher, artist, nurse, social worker, policy assistant)": "intermediate_academic",
        "intermediate supervisory or commercial profession (e.g. head representative, department manager, shopkeeper)": "intermediate_supervisory",
        "other mental work (e.g. administrative assistant, accountant, sales assistant, family carer)": "other_mental",
        "skilled and supervisory manual work (e.g. car mechanic, foreman, electrician)": "skilled_manual",
        "semi-skilled manual work (e.g. driver, factory worker)": "semiskilled_manual_work",
        "unskilled and trained manual work (e.g. cleaner, packer)": "unskilled_manual_work",
        "agrarian profession (e.g. farm worker, independent agriculturalist)": "agricultural_work",
    }
    RENAME_SECTOR = {
        "agriculture, forestry, fishery, hunting": "agri_business",
        "business services (including real estate, rental)": "business_services",
        "environmental services, culture, recreation and other services": "env_culture_recr",
        "government services, public administration and mandatory social insurances": "public_services",
        "healthcare and welfare": "health_welfare",
        "industrial production": "industry",
        "retail trade (including repairs of consumer goods)": "retail",
        "transport, storage and communication": "logistics",
        "utilities production, distribution and/or trade (electricity, natural gas, steam": "utilities",
        "utilities production, distribution and/or trade (electricity, natural gas, steam, water)": "utilities",
        "mining": "other",
    }
    work_schooling["profession"] = work_schooling["profession"].replace(
        RENAME_PROFESSION
    )
    work_schooling["sector"] = work_schooling["sector"].replace(RENAME_SECTOR)
    data = data.rename(columns={c: c + "_pre" for c in ws_vars})
    data = data.join(work_schooling.xs(2020, level="year")[ws_vars])
    for c in ws_vars:
        data[c] = (
            data[c]
            .astype(object)
            .fillna(data[c + "_pre"].astype(object))
            .astype("category")
        )
    data = data.drop([c + "_pre" for c in ws_vars], axis=1)
    return data


def clean_background_data(background, work_schooling):
    """Cleaning background variables."""
    back = background.copy()

    # merge sector and profession from work schooling 2020
    back = merge_variables_from_work_schooling(back, ws_vars=["sector", "profession"])

    # Some replacements for sector and profession variable
    back["sector"] = back["sector"].replace(
        {
            "utilities production, distribution and/or trade (electricity, natural gas, steam, water)": "transport, communication, & utilities",
            "logistics": "transport, communication, & utilities",
            "agri_business": "other",
            "health_welfare": "healthcare & welfare",
            "public_services": "public services",
            "env_culture_recr": "env., culture, recr.",
            "horeca": "catering",
            "business_services": "financial & business services",
            "financial": "financial & business services",
        }
    )
    back["sector"] = pd.Categorical(back["sector"])
    back["profession"] = back["profession"].replace(
        {
            "higher_supervisory": "higher supervisory/academic",
            "higher_academic": "higher supervisory/academic",
            "intermediate_supervisory": "intermediate supervisory/academic",
            "intermediate_academic": "intermediate supervisory/academic",
            "other_mental": "other office",
            "semiskilled_manual_work": "manual",
            "unskilled_manual_work": "manual",
            "skilled_manual": "manual",
            "agricultural_work": "manual",
        }
    )
    back["profession"] = pd.Categorical(
        back["profession"],
        [
            "manual",
            "other office",
            "intermediate supervisory/academic",
            "higher supervisory/academic",
        ],
        ordered=True,
    )

    # Merge work actual and contract hours for years 2019 and 2020
    contract_hours = work_schooling.reset_index().pivot(
        index="personal_id", columns="year", values="work_contract_hours"
    )
    contract_hours.columns = [
        "work_contract_hours_" + str(int(c)) for c in contract_hours
    ]
    actual_hours = work_schooling.reset_index().pivot(
        index="personal_id", columns="year", values="work_actual_hours"
    )
    actual_hours.columns = ["work_actual_hours_" + str(int(c)) for c in actual_hours]

    # back = back.drop(["work_actual_hours", "work_contract_hours"], axis=1)
    back = back.join(actual_hours).join(contract_hours)

    return back


def clean_covid_data(covid):
    """Clean covid data."""
    covid = covid.copy()

    # Fix hh_position
    covid.loc[covid.hh_position.isnull(), "hh_position"] = covid.loc[
        covid.hh_position.isnull(), "hh_position_2020"
    ]

    # Fix hh_children
    covid.loc[covid.hh_children.isnull(), "hh_children"] = covid.loc[
        covid.hh_children.isnull(), "hh_children_2020"
    ]

    # Manually recode reason variable (based on other-answer)
    covid = recode_reasons_for_other_responses(covid)

    # ---------------------
    # Work Status
    # ---------------------

    # Fill work status for periods where work status isn't asked. Generate some associate vars
    covid = fill_work_status(covid)
    for var in ["work_status", "unemployed", "self_employed"]:
        covid = get_baseline(covid, f"{var}_baseline", var)

    # Fix work status
    covid["work_status_baseline"] = covid["work_status_baseline"].astype(object)
    covid.loc[
        covid.index.get_level_values("month") == "2019-11-01", "work_status_baseline"
    ] = covid.loc[
        covid.index.get_level_values("month") == "2019-11-01", "work_status_2019"
    ]
    covid["work_status"] = covid["work_status"].astype(object)
    covid.loc[
        covid.index.get_level_values("month") == "2019-11-01", "work_status"
    ] = covid.loc[
        covid.index.get_level_values("month") == "2019-11-01", "work_status_2019"
    ]
    covid["work_status"] = pd.Categorical(covid["work_status"])

    # Make time-invariant variable if person unemployed any time after May
    covid = covid.reset_index().set_index("personal_id")
    covid["unemployed_after_may"] = (
        covid.query("month >= '2020-05-01'").groupby("personal_id")["unemployed"].max()
    )
    covid["out_of_laborf_after_may"] = (
        covid.query("month >= '2020-05-01'")
        .groupby("personal_id")["out_of_laborf"]
        .max()
    )
    covid["not_working_after_may"] = (
        covid.query("month >= '2020-05-01'").groupby("personal_id")["not_working"].max()
    )
    covid = covid.reset_index().set_index(["personal_id", "month"])

    # Generate indicator if present in all waves
    max_waves = covid.groupby("personal_id")["age"].count().max()
    covid["present_in_all_waves"] = (
        (covid.groupby("personal_id")["age"].count() == max_waves)
        .reindex(covid.index, level="personal_id")
        .astype(float)
    )

    # Generate new variabels (out of the covid-data)
    # essential worker
    covid["essential_compliance"] = np.nan
    covid.loc[
        covid.comply_curfew_self == "Critical Profession", "essential_compliance"
    ] = "essential"
    covid.loc[
        covid.comply_curfew_self != "Critical Profession", "essential_compliance"
    ] = "other"
    covid.loc[covid["comply_curfew_self"].isna(), "essential_compliance"] = np.nan

    covid["essential_compliance"] = pd.Categorical(covid.essential_compliance)

    covid["essential_worker_compliance"] = (
        covid["essential_compliance"].dropna() == "essential"
    ).astype(float)
    covid.loc[covid["not_working"] == 1, "essential_worker_compliance"] = np.nan

    # Generate two essential worker variables "_2" uses wave 2 definition whenever possible
    covid["essential_worker_w2"] = covid["essential_worker"].fillna(
        covid["essential_worker_compliance"]
    )

    # work_perc_home
    covid["work_perc_home_raw"] = covid["work_perc_home"]
    covid = covid.reset_index().set_index("personal_id")
    covid["work_perc_home"] = covid["work_perc_home"].groupby("personal_id").mean()
    covid = covid.reset_index().set_index(["personal_id", "month"])

    # Generate total hours variable for time use measure
    covid["hours_tu_total"] = covid["hours_work_total"]
    covid["hours_tu_total_uncond"] = covid["hours_tu_total"]

    # Create unconditional hours variable
    for var in [
        "hours_home",
        "hours_workplace",
        "hours_total",
        "hours_workplace_september",
        "hours_workplace_october",
        "hours_workplace_november",
        "hours_home_september",
        "hours_home_october",
        "hours_home_november",
        "hours_total_september",
        "hours_total_october",
        "hours_total_november",
        "hours_workplace_pre_corona",
        "hours_workplace_expected_post",
        "hours_workplace_preferred_post",
        "hours_home_pre_corona",
        "hours_home_expected_post",
        "hours_home_preferred_post",
        "hours_total_pre_corona",
        "hours_total_expected_post",
        "hours_total_preferred_post",
    ]:
        covid[f"{var}_uncond"] = covid[var]
        covid.loc[covid["not_working"] == 1, f"{var}_uncond"] = covid.loc[
            covid["not_working"] == 1, f"{var}_uncond"
        ].fillna(0)

        # Make sure that hours variables are only filled out if in labor force
        covid.loc[covid["not_working"] == 1, var] = np.nan

        # Make sure that hours variables that are only asked in
        # december are missing in all other waves
        indices_no_dec = [
            i
            for i in covid.index.unique(level="month")
            if i != pd.to_datetime(f"2020-12-01")
        ]
        if var not in [
            "hours_home",
            "hours_workplace",
            "hours_total",
        ]:
            covid.loc[
                pd.IndexSlice[
                    :,
                    indices_no_dec,
                ],
                f"{var}_uncond",
            ] = np.nan
            covid = make_vars_time_invariant(covid, [var])
            covid = make_vars_time_invariant(covid, [f"{var}_uncond"])

    # Generate max hours worked
    covid["max_hours_total"] = (
        covid.groupby("personal_id")["hours_total"].max()
    ).reindex(covid.index, level="personal_id")

    # Home share
    covid["home_share"] = covid["hours_home"] / covid["hours_total"]

    # Create catogorical variable
    covid["work_h_cat"] = pd.cut(
        covid.hours_total,
        bins=[1, 20, 30, covid.hours_total.max()],
        labels=["1-20", "20-30", "30+"],
        include_lowest=True,
    )

    # Home office variables
    covid["work_perc_home_cat"] = pd.cut(
        covid.work_perc_home,
        bins=[0, 10, 90, 100],
        labels=["up to 10%", "10-90%", "more than 90%"],
        include_lowest=True,
    )
    covid["work_perc_home_cat_20"] = pd.cut(
        covid.work_perc_home,
        bins=[0, 20, 80, 100],
        labels=["up to 20%", "20-80%", "more than 80%"],
        include_lowest=True,
    )
    covid["work_perc_home"] = covid["work_perc_home"] / 100

    # Categorize reasons for reduction
    cat = {
        "less_business": [
            "empl_less_work_lessbusiness",
            "empl_not_work_lessbusiness",
            "selfempl_less_business",
        ],
        "closure": [
            "empl_not_work_infection_gov",
            "empl_not_work_infection_empl",
            "empl_less_work_infection_empl",
            "empl_less_work_infection_gov",
            "selfempl_less_infection_gov",
            "selfempl_less_infection_self",
            "selfempl_less_closure",
        ],
        "care": ["empl_not_work_care", "selfempl_less_care", "empl_less_work_care"],
        "lost_job": [
            "empl_not_work_fired",
            "empl_less_work_fired",
            "empl_not_work_out_of_laborf",
        ],
        "vacation": [
            "empl_not_work_vacation",
            "selfempl_less_vacation",
            "empl_less_work_vacation",
        ],
        "vacation_sick": [
            "empl_not_work_sick",
            "empl_less_work_sick",
            "selfempl_less_sick",
            "empl_not_work_vacation",
            "selfempl_less_vacation",
            "empl_less_work_vacation",
        ],
        "unrel_corona": [
            "empl_not_work_sick",
            "empl_less_work_sick",
            "selfempl_less_sick",
            "empl_not_work_vacation",
            "selfempl_less_vacation",
            "empl_less_work_vacation",
            "empl_less_work_unrel_corona",
            "selfempl_less_unrel_corona",
        ],
        "other": ["empl_not_work_other", "empl_less_work_other", "selfempl_less_other"],
        "fear_infection": [
            "empl_not_work_fear_infection",
            "empl_less_work_fear_infection",
        ],
        "other_broad": [
            "empl_not_work_care",
            "selfempl_less_care",
            "empl_less_work_care",
            "empl_not_work_sick",
            "empl_less_work_sick",
            "selfempl_less_sick",
            "empl_not_work_vacation",
            "selfempl_less_vacation",
            "empl_less_work_vacation",
            "empl_less_work_unrel_corona",
            "selfempl_less_unrel_corona",
            "empl_not_work_fear_infection",
            "empl_less_work_fear_infection",
            "empl_not_work_other",
            "empl_less_work_other",
            "selfempl_less_other",
        ],
    }

    for key, value in cat.items():
        col_name = f"reason_{key}"
        covid[col_name] = np.nan
        condition = covid.index.get_level_values("month").isin(
            ["2020-03-01", "2020-04-01"]
        ) & (covid.hours_total_uncond >= 0)
        covid.loc[condition, col_name] = 0
        for val in value:
            covid.loc[covid[val] == 1, col_name] = 1

        # Make baseline variable by taking the maximum
        covid = covid.reset_index().set_index("personal_id")
        covid[f"{col_name}_baseline"] = covid.groupby("personal_id")[col_name].max()
        covid = covid.reset_index().set_index(["personal_id", "month"])

        # Get march april seperately
        covid = get_baseline(
            covid, f"{col_name}_march", col_name, baseline="2020-03-01"
        )
        covid = get_baseline(
            covid, f"{col_name}_april", col_name, baseline="2020-04-01"
        )

    # Time varying care variable
    covid["less_care"] = 0
    covid.loc[
        covid.index.get_level_values("month").isin(["2020-03", "2020-04"]), "less_care"
    ] = covid.loc[
        covid.index.get_level_values("month").isin(["2020-03", "2020-04"]),
        "reason_care",
    ]

    # Time varying care variable mai/juni
    covid["less_care_with_may"] = covid["less_care"]
    covid.loc[
        covid.index.get_level_values("month") == "2020-05", "less_care_with_may"
    ] = (
        covid.loc[
            covid.index.get_level_values("month") == "2020-05", "day_off_childcare"
        ]
        > 0
    ) * 1

    # Ordered categories
    covid["reason_cat_baseline"] = covid["reason_closure_baseline"].replace(
        {0: "no reduction", 1: "closure"}
    )
    covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_cat_baseline"
    ] = covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_less_business_baseline"
    ].replace(
        {0: "no reduction", 1: "less business"}
    )
    covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_cat_baseline"
    ] = covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_care_baseline"
    ].replace(
        {0: "no reduction", 1: "care"}
    )
    covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_cat_baseline"
    ] = covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_other_broad_baseline"
    ].replace(
        {0: "no reduction", 1: "other"}
    )
    covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_cat_baseline"
    ] = covid.loc[
        covid["reason_cat_baseline"] == "no reduction", "reason_lost_job_baseline"
    ].replace(
        {0: "no reduction", 1: "other"}
    )
    covid["reason_cat_baseline"] = pd.Categorical(
        covid["reason_cat_baseline"],
        categories=["closure", "less business", "care", "other", "no reduction"],
        # ordered=True,
    )

    # -------------------
    # Childcare variables
    # -------------------
    # Make sure that it is only there if they are the parents
    cc_vars = [c for c in covid.columns if c.startswith("cc_")]

    # Type conversion
    for cc in cc_vars:
        try:
            covid[cc] = covid[cc].astype("boolean")
        except TypeError:
            pass
    for col in cc_vars:
        covid.loc[
            ~covid.hh_position.isin(
                ["Household head", "Unwedded partner", "Wedded partner"]
            ),
            col,
        ] = np.nan

    # Create non-parents cc variables
    covid["cc_parents"] = (
        covid[["cc_self_home", "cc_partner_home", "cc_ex_partner"]].sum(axis=1) > 0
    ).astype(float)
    covid["cc_no_parents_state"] = (
        covid[
            [
                "cc_older_siblings",
                "cc_grand_parents",
                "cc_other_relatives",
                "cc_share_neighbors",
                "cc_home_alone",
                "cc_other",
            ]
        ].sum(axis=1)
        > 0
    ).astype(float)

    # Partner variables
    cohab = (
        covid.reset_index()
        .set_index("personal_id")
        .query("month == '2020-04-01'")[["cohabiting_partner", "hhh_partner"]]
        .copy()
    )
    cohab["month"] = pd.Timestamp(year=2020, month=2, day=1)
    cohab = cohab.reset_index().set_index(["personal_id", "month"])
    cohab = cohab.rename(columns={"cohabiting_partner": "help"})
    covid = covid.join(cohab["help"])
    covid.loc[covid.cohabiting_partner.isnull(), "cohabiting_partner"] = covid.loc[
        covid.cohabiting_partner.isnull(), "help"
    ]
    covid.loc[covid.cohabiting_partner.isnull(), "cohabiting_partner"] = covid.loc[
        covid.cohabiting_partner.isnull(), "hhh_partner"
    ].astype(float)

    # Create single parent indicator
    covid["single_parent"] = 1 - covid["cohabiting_partner"]
    condition = (covid.cohabiting_partner == 0) & (
        ((covid.hours_cc_partner > 0) & (covid.hours_cc_expartner == 0))
        | ((covid.hours_cc_young_partner > 0) & (covid.hours_cc_young_expartner == 0))
    )
    covid.loc[condition, "single_parent"] = 0
    covid.drop("help", axis=1, inplace=True)

    # Answered cc questionnaire
    cc = (covid.groupby("personal_id")["hours_cc_self"].sum(min_count=2).notnull()) * 1
    cc.name = "cc_questionnaire"
    covid = covid.join(cc)

    # Do I take care?
    covid["cc_only_me"] = (
        (covid.cc_self_home) & ~(covid.cc_partner_home) & ~(covid.cc_ex_partner)
    )

    # Generate care taker variables
    covid["care_taker"] = np.nan
    condition = (
        (covid.female == 1)
        & (covid.cc_self_home)
        & ~(covid.cc_partner_home)
        & ~(covid.cc_ex_partner)
    )
    covid.loc[condition, "care_taker"] = "mother"

    condition = (
        (covid.female == 0)
        & ~(covid.cc_self_home)
        & (covid.cc_partner_home | covid.cc_ex_partner)
    )
    covid.loc[condition, "care_taker"] = "mother"

    condition = (
        (covid.female == 0)
        & (covid.cc_self_home)
        & ~(covid.cc_partner_home)
        & ~(covid.cc_ex_partner)
    )
    covid.loc[condition, "care_taker"] = "father"

    condition = (
        (covid.female == 1)
        & ~(covid.cc_self_home)
        & (covid.cc_partner_home | covid.cc_ex_partner)
    )
    covid.loc[condition, "care_taker"] = "father"

    condition = ~(covid.cc_self_home) & ~(covid.cc_partner_home)
    covid.loc[condition, "care_taker"] = "neither"
    condition = (covid.cc_self_home) & (covid.cc_partner_home)
    covid.loc[condition, "care_taker"] = "both"
    covid["care_taker"] = pd.Categorical(
        covid["care_taker"],
        categories=["both", "mother", "father", "neither"],
        ordered=True,
    )

    # Cc mother or father ?
    covid["cc_mother"] = np.nan
    covid.loc[covid.care_taker.isin(["mother", "both"]), "cc_mother"] = 1
    covid.loc[covid.care_taker.isin(["father", "neither"]), "cc_mother"] = 0

    covid["cc_father"] = np.nan
    covid.loc[covid.care_taker.isin(["father", "both"]), "cc_father"] = 1
    covid.loc[covid.care_taker.isin(["mother", "neither"]), "cc_father"] = 0

    # For christians code
    covid["cc_only_mother"] = covid["care_taker"] == "mother"
    covid["cc_only_father"] = covid["care_taker"] == "father"
    covid["cc_both_parents"] = covid["care_taker"] == "both"
    covid["cc_no_parents"] = covid["care_taker"] == "neither"

    # -------------------
    # policy variables
    # -------------------
    # create applied_any_policy_cat
    policy_cols_employer = [
        "employer_application_now",
        "employer_application_togs",
        "employer_application_deferral",
    ]
    policy_cols_self_employed = [
        "self_application_now",
        "self_application_togs",
        "self_application_deferral",
        "self_application_tozo",
        "self_grekening",
        "self_used_apa",
        "self_used_guarantee",
        "self_used_go",
        "self_used_qredits",
        "self_used_loan_fund",
    ]
    policy_cols = policy_cols_employer + policy_cols_self_employed

    renaming_df = {
        "no, I don't think it's necessary": "No",
        "yes, the application has been granted": "Yes",
        "I don't know": "I don't know",
        "no, but I think my employer is gonna do this": "I don't know",
        "yes, but I don't yet know if the application has been granted": "Yes",
        "no, I don't think it's possible": "No",
        "yes, but the application was rejected": "No",
        "not applicable/I don't have a g-account": "No",
        "no, for another reason.": "No",
        "no, I don't think my company qualifies.": "No",
        "I didn't know there was this arrangement.": "No",
        "no, but I'm gonna do this.": "I don't know",
        "yes": "Yes",
        "no, this is too much paperwork.": "No",
        "no, I have no employees/no payroll costs.": "No",
        "no, I don't intend to.": "No",
        "not applicable.": "No",
    }
    for var in policy_cols:

        covid[f"{var}_cat"] = covid[var].replace(renaming_df)
        covid[var + "_yes"] = (covid[f"{var}_cat"].dropna() == "Yes").astype(float)

    covid["applied_any_policy"] = (
        (
            covid[
                [
                    p + "_yes"
                    for p in policy_cols
                    if p
                    not in [
                        "employer_application_togs",
                        "employer_application_deferral",
                    ]
                ]
            ].dropna(how="all")
            == 1
        )
        .any(axis=1)
        .astype(float)
    )
    for sup in ["now", "togs", "deferral"]:
        covid[f"application_{sup}_yes"] = covid[
            f"employer_application_{sup}_yes"
        ].fillna(covid[f"self_application_{sup}_yes"])
        covid[f"application_{sup}_cat"] = covid[
            f"employer_application_{sup}_cat"
        ].fillna(covid[f"self_application_{sup}_cat"])

    covid["applied_any_policy_cat"] = covid["applied_any_policy"].replace(
        {1: "yes", 0: "no"}
    )
    covid.loc[
        (covid["applied_any_policy"] == 0)
        & (covid[[c + "_cat" for c in policy_cols]] == "I don't know").any(axis=1),
        "applied_any_policy_cat",
    ] = "I don't know"
    covid["applied_any_policy_cat"] = pd.Categorical(
        covid["applied_any_policy_cat"],
        categories=["no", "I don't know", "yes"],
        ordered=True,
    )
    renaming_covid_narrow = {
        "no, I don't think it's necessary": "No",
        "yes, the application has been granted": "Yes",
        "I don't know": "I don't know",
        "no, but I think my employer is gonna do this": "I don't know",
        "yes, but I don't yet know if the application has been granted": "I don't know",
        "no, I don't think it's possible": "No",
        "yes, but the application was rejected": "No",
        "not applicable/I don't have a g-account": "No",
        "no, for another reason.": "No",
        "no, I don't think my company qualifies.": "No",
        "I didn't know there was this arrangement.": "No",
        "no, but I'm gonna do this.": "I don't know",
        "yes": "Yes",
        "no, this is too much paperwork.": "No",
        "no, I have no employees/no payroll costs.": "No",
        "no, I don't intend to.": "No",
        "not applicable.": "No",
    }
    for var in policy_cols:

        covid[f"{var}_cat_narrow"] = covid[var].replace(renaming_covid_narrow)
        covid[var + "_yes_narrow"] = (
            covid[f"{var}_cat_narrow"].dropna() == "Yes"
        ).astype(float)

    covid["applied_any_policy_narrow"] = (
        (covid[[p + "_yes_narrow" for p in policy_cols]].dropna(how="all") == 1)
        .any(axis=1)
        .astype(float)
    )

    # create time-invariant variables
    for var in [
        "self_application_now_yes",
        "self_application_togs_yes",
        "self_application_deferral_yes",
        "employer_application_now_yes",
        "employer_application_togs_yes",
        "employer_application_deferral_yes",
        "applied_any_policy",
        "applied_any_policy_cat",
        "applied_any_policy_narrow",
    ]:
        temp = covid[var].unstack()
        covid = covid.reset_index().set_index(["personal_id"])
        obs_months = ["05", "09"]
        for month in obs_months:
            covid[f"{var}_{month}"] = temp[pd.to_datetime(f"2020-{month}-01")]
        covid = covid.reset_index().set_index(["personal_id", "month"])

        if not "cat" in var:
            covid[f"{var}_any"] = (
                covid[[f"{var}_{m}" for m in obs_months]].dropna(how="all").sum(axis=1)
                > 0
            ).astype(float)

    # Create vars indicating application for employees and self-employed
    for pol in ["now", "togs", "deferral"]:
        for month in obs_months:
            covid[f"application_{pol}_yes_{month}"] = covid[
                f"employer_application_{pol}_yes_{month}"
            ].fillna(covid[f"self_application_{pol}_yes_{month}"])

    # Create combination of September/May policy variables
    covid["policy_cat"] = np.nan
    covid.loc[
        covid.applied_any_policy_05 == 1, "policy_cat"
    ] = "Affected by policy, March-May"
    covid.loc[
        covid.applied_any_policy_09 == 1, "policy_cat"
    ] = "Affected by policy, June-Sept"
    covid.loc[
        (covid.applied_any_policy_09 == 1) & (covid.applied_any_policy_05 == 1),
        "policy_cat",
    ] = "Affected by policy, March-Sept"
    covid.loc[
        (covid.applied_any_policy_05 == 0) & (covid.applied_any_policy_09 == 0),
        "policy_cat",
    ] = "Never affect by policy"
    covid["policy_cat"] = pd.Categorical(
        covid.policy_cat,
        categories=[
            "Affected by policy, March-Sept",
            "Affected by policy, March-May",
            "Affected by policy, June-Sept",
            "Never affect by policy",
        ],
        ordered=True,
    )
    covid["ever_affected_by_policy"] = "Never affected by policy"
    covid.loc[
        (covid.applied_any_policy_05.isnull() | covid.applied_any_policy_09.isnull()),
        "ever_affected_by_policy",
    ] = np.nan
    covid.loc[
        ((covid.applied_any_policy_05 == 1) | (covid.applied_any_policy_09 == 1)),
        "ever_affected_by_policy",
    ] = "Affected by policy"

    covid["ever_affect_by_policy_help"] = covid.ever_affected_by_policy.replace(
        to_replace={"Affected by policy": 1, "Never affected by policy": 0}
    ).astype(float)
    covid.loc[
        covid.employer_application_now_cat == "I don't know",
        "ever_affect_by_policy_help",
    ] = 0.5

    m = covid.ever_affect_by_policy_help.groupby("personal_id").max()
    m.name = "ever_affect_by_policy_str"
    covid = covid.join(m)
    covid["ever_affect_by_policy_str"] = covid["ever_affect_by_policy_str"].replace(
        to_replace={
            1: "Affected by policy",
            0: "Never affected by policy",
            0.5: "Don't know",
        }
    )
    covid["ever_affect_by_policy_str"] = pd.Categorical(
        covid["ever_affect_by_policy_str"],
        categories=["Affected by policy", "Never affected by policy", "Don't know"],
        ordered=True,
    )

    # remove helper variable
    covid = covid.drop(["ever_affect_by_policy_help"], axis=1)

    return covid


def fill_work_status(covid):
    covid["work_status"] = covid.groupby("personal_id")["work_status"].ffill()

    # Out of laborf -> set to retired
    covid.loc[covid["empl_not_work_out_of_laborf"] == 1, "work_status"] = "retired"

    # No work anymore/ fired -> set to unemployed
    covid.loc[covid["empl_not_work_fired"] == 1, "work_status"] = "unemployed"

    covid["out_of_laborf"] = (
        ~covid["work_status"]
        .replace({"nan": np.nan})
        .dropna()
        .isin(["employed", "self-employed", "unemployed"])
    ).astype(float)

    covid["not_working"] = (
        ~covid["work_status"]
        .replace({"nan": np.nan})
        .dropna()
        .isin(["employed", "self-employed"])
    ).astype(float)

    covid["unemployed"] = (
        covid["work_status"].dropna().isin(["unemployed"]).astype(float)
    )

    covid["self_employed"] = (
        covid["work_status"].dropna().isin(["self-employed"]).astype(float)
    )
    return covid


def make_vars_time_invariant(df, cols):
    df = df.reset_index().set_index("personal_id")

    for col in cols:
        time_invariant = df[col].copy()
        time_invariant = time_invariant.dropna()

        # Check for duplicates
        double = time_invariant.index.duplicated()
        if double.any():
            warnings.warn(f"Duplicates in {col}, only one will be kept.")
            # {time_invariant.loc[time_invariant.index.duplicated()]}s

            time_invariant = time_invariant[~double]

        # Join column in
        df = df.drop(columns=col).join(time_invariant)

    df = df.reset_index().set_index(["personal_id", "month"])

    return df


def create_hh_income_data(hh_income, covid):

    hh_income = hh_income.reset_index().set_index(["personal_id", "month"]).copy()
    hh_income = hh_income.dropna(axis=0, how="all")

    wins_at = 20000
    hh_income.loc[hh_income["net_income_hh"] > wins_at, "net_income_hh"] = wins_at
    hh_income.loc[hh_income["net_income_hh"] < 0, "net_income_hh"] = 0
    hh_income = (
        hh_income[["net_income_hh"]]
        .join(
            covid[
                [
                    "net_income_2y_equiv_q",
                    "net_income_2y_equiv_q3",
                    "hh_members",
                    "age",
                    "abs_change_hours_uncond_03",
                    "abs_change_hours_uncond_04",
                    "abs_change_hours_uncond_05",
                    "abs_change_hours_uncond_06",
                    "abs_change_hours_uncond_09",
                    "abs_change_hours_uncond_12",
                    "abs_change_hours_uncond_avg_0305",
                    "abs_change_hours_uncond_avg_0304",
                    "abs_change_hours_uncond_avg_0304_groups",
                    "rel_change_hours_uncond_03",
                    "rel_change_hours_uncond_04",
                    "rel_change_hours_uncond_05",
                    "rel_change_hours_uncond_06",
                    "rel_change_hours_uncond_09",
                    "rel_change_hours_uncond_12",
                    "rel_change_hours_uncond_avg_0305",
                    "rel_change_hours_uncond_avg_0304",
                    # "rel_change_hours_uncond_avg_0304_groups",
                    "max_hours_total",
                    "work_status_baseline",
                    "applied_any_policy_05",
                    "gender",
                    "reason_lost_job_baseline",
                    "hh_id",
                    "hh_position",
                    "reason_cat_baseline",
                    "hhh_partner",
                    "civil_status",
                    "policy_cat",
                    "ever_affected_by_policy",
                    "edu",
                    "gross_income_groups",
                    "ever_affect_by_policy_str",
                ]
            ]
            .groupby("personal_id")
            .first()
        )
        .sort_index()
    )
    hh_income["net_income_hh_equiv"] = hh_income["net_income_hh"] / np.sqrt(
        hh_income["hh_members"]
    )
    for var in ["net_income_2y_equiv_q", "net_income_2y_equiv_q3"]:
        hh_income[var] = pd.Categorical(hh_income[var])
    for var in ["net_income_hh", "net_income_hh_equiv"]:
        temp = (
            hh_income.query("month == ['2020-01-01', '2020-02-01']")[var]
            .groupby("personal_id")
            .mean()
        )
        hh_income = hh_income.reset_index().set_index(["personal_id"])
        hh_income[f"{var}_baseline"] = temp
        hh_income[f"change_{var}"] = hh_income[var] - hh_income[f"{var}_baseline"]
        hh_income.loc[hh_income[f"{var}_baseline"] > 0, f"rel_change_{var}"] = (
            hh_income.loc[hh_income[f"{var}_baseline"] > 0, f"change_{var}"]
            / hh_income.loc[hh_income[f"{var}_baseline"] > 0, f"{var}_baseline"]
        )

    hh_income.to_parquet(ppj("OUT_DATA", "hh_income.parquet"))
    # ToDo: merge some variables back to covid? Merge more covid variable to background


if __name__ == "__main__":

    # Load data
    months_in_covid_data = sys.argv[1].split(",")
    time_use = pd.read_parquet(ppj("IN_DATA", "time_use_data_detailed.pickle"))
    work_schooling = pd.read_pickle(
        ppj("IN_DATA", "unmerged_files", "work_schooling_full.pickle")
    )
    hh_income = pd.read_pickle(ppj("IN_DATA", "hh_income_data_set.pickle"))

    background = pd.read_pickle(ppj("IN_DATA", "background_data_merged.pickle"))
    background_2019 = pd.read_parquet(ppj("OUT_DATA", "background_2019.parquet"))
    background_full = pd.read_pickle(
        ppj("IN_DATA", "unmerged_files", "background_full.pickle")
    )
    partner = pd.read_pickle(ppj("IN_DATA", "partner_links.pickle"))
    covid_renaming = pd.read_csv(
        ppj(
            "PROJECT_ROOT",
            "basic_data_cleaning",
            "liss_data_specs",
            "xyx-corona-questionnaire_renaming.csv",
        ),
        sep=";",
    )

    single_files = [
        pd.read_pickle(ppj("IN_DATA", f"covid_data_{m}.pickle"))
        for m in months_in_covid_data
    ]
    covid = (
        pd.concat(single_files)
        .reset_index()
        .set_index(["personal_id", "month"])
        .sort_index()
    ).copy()
    covid = set_types_file(
        panel=covid,
        rename_df=covid_renaming,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
    )

    # Select variables to keep
    covid = covid[covid_vars].copy()

    # Merge time use
    covid = pd.merge(
        covid,
        time_use,
        left_index=True,
        right_index=True,
        how="outer",
        suffixes=("", "_tu"),
    )

    # Merge background data
    covid = merge_background_data(background, covid, background_2019, background_full)

    # ----------------
    # Clean covid data
    # ----------------

    # Remove answers of one participant that didn't finish childcare questions in wave 1
    # and was asked these questions again in wave 2
    cc_vars = [c for c in covid.columns if c.startswith("cc_")]
    cc_vars.remove("cc_other_str")
    cc_vars.remove("cc_emergency_comment")
    covid.loc[(817065, "2020-03-01"), cc_vars + ["nr_children_below_12"]] = np.nan

    # Make quasi time -invarying variables from covid time invarying
    covid = make_vars_time_invariant(covid, time_invariant_vars)

    # Clean covid data
    covid = clean_covid_data(covid)

    # Generate new variables
    covid = generate_baseline_variables(covid)
    covid = generate_new_variables(covid)

    # Create hh income data
    create_hh_income_data(hh_income, covid)

    # Export long format
    try:
        covid.to_parquet(ppj("OUT_DATA", "work-childcare-ind.parquet"))
    except:
        colus = list(covid.columns)
        colus.remove("hours_workplace")
        for col in colus:
            try:
                covid[["hours_workplace", col]].to_parquet("test.parquet")
            except:
                if covid[col].dtype.name == "category":
                    covid[col].cat.categories = [
                        str(c) for c in covid[col].cat.categories
                    ]
                else:
                    print(
                        f"!! {col} has dtype {covid[col].dtype} incompatible with parquet and is set to categorical"
                    )
                    covid[col] = covid[col].astype(str).astype("category")

        covid.to_parquet(path=ppj("OUT_DATA", "work-childcare-ind.parquet"))
