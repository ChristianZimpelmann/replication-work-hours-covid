"""Prepare data for work-childcare anlysis.

Output:
    - "../../data/work-childcare-long.parquet"
    - "../../data/work-childcare-wide.parquet"

Contains all additionally necessary variables, and partners' variables.
If you want to add additional variables, please do so in variables_to_keep.py
"""
import warnings

import numpy as np
import pandas as pd

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.data_management.variables_to_keep import (
    background_variables,
)
from project_specific_analyses.data_management.variables_to_keep import (
    time_invariant_vars,
)
from project_specific_analyses.data_management.variables_to_keep import (
    timevarying_variables,
)
from project_specific_analyses.library.panel_functions import get_baseline


def generate_hh_level_data(
    df, partner, timevarying_background, timeconstant, time="month"
):
    """Generates data set with partner info.

    Merge in all variables in df as variables with extention "_partner".
    These variables contain the answer of the partner.

    Args:
        df (pd.DataFrame): contains the original data set with index: personal_id and `time`.
        partner (pd.Series): contains series with index: personal_id and column personal_id_partner.
        time (str): name of time index.

    Return:
        pd.DataFrame: df + columns with partner info named as columnname_partner.

    """
    # Get partners personal id in the data set
    partner_id = partner[["personal_id_partner"]].copy()
    df_reindex = df.reset_index()
    df_w_partner_id = pd.merge(df_reindex, partner_id, on="personal_id", how="left")

    # Generate data set to merge in.
    df_partner = df_w_partner_id.copy()

    # Rename variables to have _partner in variable name
    ren = {}
    for col in df_partner.columns:
        if not col in [time]:
            ren.update({col: col + "_partner"})
    df_partner.rename(columns=ren, inplace=True)
    df_partner.rename(
        columns={"personal_id_partner_partner": "personal_id"}, inplace=True
    )
    df_partner = df_partner.dropna(subset=["personal_id"])

    # Create lists with timevarying background/ time constant variables
    baselinevars = [var for var in df.columns if var.endswith("baseline")] + [
        "labor_force",
        "labor_force_coarse",
        "essential_worker_w2",
    ]
    baselinevars.remove("work_status_baseline")
    time_back = [
        c + "_partner" for c in timevarying_background + ["work_status_baseline"]
    ]
    time_constant = [c + "_partner" for c in timeconstant + baselinevars]

    # Merge in all columns that are truly time dependent
    df_hh = pd.merge(
        df_w_partner_id,
        df_partner.drop(time_constant, axis=1),
        on=["personal_id", "personal_id_partner", time],
        how="outer",
    )

    # Merge in time constant variables
    df_constant = df_partner[time_constant + ["personal_id_partner"]].copy()
    df_constant = df_constant[~df_constant.personal_id_partner.duplicated()]
    df_hh = pd.merge(
        df_hh,
        df_constant,
        how="left",
        on=["personal_id_partner"],
        validate="many_to_one",
    )

    df_hh.set_index(["personal_id", time], inplace=True)
    df_hh.sort_index(inplace=True)

    ind = list(df_hh.index)
    assert len(ind) == len(list(set(ind))), "Multiindex is not unique"

    # Not sure what we needed this for
    # Fill wholes in those columns that are partially time variant
    condition = df_hh.index.get_level_values(time) != "2019-11-01"

    df_hh.loc[condition, time_back] = make_vars_time_invariant(
        df_hh.loc[condition, time_back], time_back
    )

    # Since outer merge need to reconsider baseline variables because
    # their empty
    baselinevars = (
        [var for var in df_hh.columns if var.endswith("baseline")]
        + timeconstant
        + timevarying_background
        + [
            "single_parent",
            "max_hours_total",
            "essential_worker_w2",
            "labor_force",
            "labor_force_coarse",
        ]
    )
    base = df_hh.index.get_level_values(time) == "2020-02-01"
    var = (
        df_hh.loc[base, baselinevars]
        .reset_index()
        .drop("month", axis=1)
        .set_index("personal_id")
        .copy()
    )
    condition = df_hh[baselinevars].isnull().all(axis=1) & (
        df_hh.index.get_level_values(time) != "2019-11-01"
    )
    df_empty = df_hh[condition].copy()
    df_empty = df_empty.drop(baselinevars, axis=1).join(var)
    df_nonempty = df_hh[~condition].copy()

    df_hh = pd.concat([df_empty, df_nonempty], axis=0).sort_index()

    # Fix workstatus baseline partner
    condition = df_hh.index.get_level_values("month") != "2019-11-01"
    df_hh.loc[condition, "work_status_baseline_partner"] = make_vars_time_invariant(
        df_hh.loc[condition, "work_status_baseline_partner"],
        ["work_status_baseline_partner"],
    )

    return df_hh


def generate_vars_for_couples(hh_data):
    """Generate variables that rely on partner data."""
    df_hh = hh_data.copy()

    # Calculate household weights
    n_hh_members_in_sample = df_hh.groupby("hh_id").count().max(axis=1)
    hh_weight = 1 / n_hh_members_in_sample
    hh_weight.name = "hh_weight"
    df_hh = df_hh.join(hh_weight, on="hh_id")

    # Generate children variables.
    df_hh = children_variables(df_hh)

    # Calculate household level essential variables
    df_hh["essential_father"] = np.nan
    df_hh.loc[df_hh.child_below_12 == 1, "essential_father"] = df_hh.loc[
        df_hh.child_below_12 == 1, "essential_worker_w2"
    ]
    df_hh.loc[df_hh.child_below_12 == 1, "essential_mother"] = df_hh.loc[
        df_hh.child_below_12 == 1, "essential_worker_w2_partner"
    ]

    condition = (df_hh.child_below_12 == 1) & (df_hh.female == 1)
    df_hh.loc[condition, "essential_mother"] = df_hh.loc[
        condition, "essential_worker_w2"
    ]
    df_hh.loc[condition, "essential_father"] = df_hh.loc[
        condition, "essential_worker_w2_partner"
    ]

    df_hh["essential_hh_type"] = np.nan
    df_hh.loc[
        (df_hh["essential_mother"] == 1) & (df_hh["essential_father"] == 1),
        "essential_hh_type",
    ] = "both essential"
    df_hh.loc[
        (df_hh["essential_mother"] == 1) & (df_hh["essential_father"] == 0),
        "essential_hh_type",
    ] = "only mother essential"
    df_hh.loc[
        (df_hh["essential_mother"] == 0) & (df_hh["essential_father"] == 1),
        "essential_hh_type",
    ] = "only father essential"
    df_hh.loc[
        (df_hh["essential_mother"] == 0) & (df_hh["essential_father"] == 0),
        "essential_hh_type",
    ] = "neither essential"
    df_hh["essential_hh_type"] = pd.Categorical(df_hh["essential_hh_type"])

    df_hh["hh_type_single_essential"] = np.nan
    df_hh.loc[
        (
            df_hh.hhh_partner
            & (
                (df_hh.essential_worker_w2 == 0)
                | (df_hh.essential_worker_w2_partner == 0)
            )
        ),
        "hh_type_single_essential",
    ] = "couple non-essential"
    df_hh.loc[
        (~df_hh["hhh_partner"].astype("boolean")) & (df_hh["essential_worker_w2"] == 1),
        "hh_type_single_essential",
    ] = "single essential"
    df_hh.loc[
        (
            (~df_hh["hhh_partner"].astype("boolean"))
            & ~(df_hh["essential_worker_w2"] == 1)
        ),
        "hh_type_single_essential",
    ] = "single non-essential"
    df_hh.loc[
        (
            df_hh["hhh_partner"].astype("boolean")
            & (df_hh["essential_worker"])
            & (df_hh["essential_worker_partner"])
        ),
        "hh_type_single_essential",
    ] = "couple essential"
    df_hh["hh_type_single_essential"] = pd.Categorical(
        df_hh["hh_type_single_essential"]
    )

    # Essential worker in on the household level
    df_hh["essential_worker_mother"] = df_hh["essential_worker"]
    df_hh.loc[df_hh.gender == "male", "essential_worker_mother"] = df_hh.loc[
        df_hh.gender == "male", "essential_worker_partner"
    ]

    df_hh["essential_worker_father"] = df_hh["essential_worker"]
    df_hh.loc[df_hh.gender == "female", "essential_worker_father"] = df_hh.loc[
        df_hh.gender == "female", "essential_worker_partner"
    ]

    # Calc income share
    df_hh["income_share"] = df_hh["gross_income"] / (
        df_hh["gross_income"] + df_hh["gross_income_partner"]
    )

    df_hh["income_share_groups"] = pd.cut(
        df_hh["income_share"],
        [0, 0.3, 0.6, 1],
        labels=["< 0.3", "0.3 - 0.45", "> 0.45"],
        include_lowest=True,
    )

    # Home office one year earlier
    df_hh["work_home_one_year_before"] = (df_hh["work_home"] != "no").astype(float)
    df_hh["work_home_one_year_before_partner"] = (
        df_hh["work_home_partner"] != "no"
    ).astype(float)

    # Breadwinner
    # Classify according to income share
    df_hh["female_income_share"] = np.nan
    df_hh.loc[(df_hh.gender == "female"), "female_income_share"] = df_hh.loc[
        (df_hh.gender == "female"), "income_share"
    ]
    df_hh.loc[(df_hh.gender == "male"), "female_income_share"] = (
        1 - df_hh.loc[(df_hh.gender == "male"), "income_share"]
    )
    df_hh.loc[(df_hh.gender == df_hh.gender_partner), "female_income_share"] = np.nan
    df_hh.loc[
        ~df_hh.hh_position.isin(
            ["Household head", "Wedded partner", "Unwedded partner"]
        ),
        "female_income_share",
    ] = np.nan

    df_hh["male_breadwinner"] = df_hh.female_income_share < 0.4
    df_hh.loc[df_hh.female_income_share.isnull(), "male_breadwinner"] = np.nan

    # Education on the household level
    df_hh["high_edu_mother"] = df_hh["high_edu"]
    df_hh.loc[df_hh.gender == "male", "high_edu_mother"] = df_hh.loc[
        df_hh.gender == "male", "high_edu_partner"
    ]
    df_hh["high_edu_father"] = df_hh["high_edu"]
    df_hh.loc[df_hh.gender == "female", "high_edu_father"] = df_hh.loc[
        df_hh.gender == "female", "high_edu_father"
    ]

    df_hh["work_perc_home_cat_mother"] = df_hh["work_perc_home_cat"]
    df_hh.loc[df_hh.gender == "male", "work_perc_home_cat_mother"] = df_hh.loc[
        df_hh.gender == "male", "work_perc_home_cat_partner"
    ]

    df_hh["work_perc_home_cat_father"] = df_hh["work_perc_home_cat"]
    df_hh.loc[df_hh.gender == "female", "work_perc_home_cat_father"] = df_hh.loc[
        df_hh.gender == "female", "work_perc_home_cat_partner"
    ]

    # Calculate hours baseline father/mother
    df_hh["hours_baseline_father"] = np.nan
    df_hh.loc[df_hh.child_below_12 == 1, "hours_baseline_father"] = df_hh.loc[
        df_hh.child_below_12 == 1, "hours_baseline"
    ]
    df_hh.loc[df_hh.child_below_12 == 1, "hours_baseline_mother"] = df_hh.loc[
        df_hh.child_below_12 == 1, "hours_baseline_partner"
    ]

    # Hours on the household level
    condition = (df_hh.child_below_12 == 1) & (df_hh.female == 1)
    df_hh.loc[condition, "hours_baseline_mother"] = df_hh.loc[
        condition, "hours_baseline"
    ]
    df_hh.loc[condition, "hours_baseline_father"] = df_hh.loc[
        condition, "hours_baseline_partner"
    ]
    # Present in march april
    df_hh.drop("pres_in_march_april", axis=1, inplace=True)
    c = (
        df_hh.query(
            "month.isin(['2020-04-01']) & hours_total_uncond.notnull() & hours_total_uncond_partner.notnull()"
        )
        .groupby("personal_id")["ones"]
        .sum()
    )
    c = c == 1
    c.name = "both_pres_in_april"
    df_hh = df_hh.join(c)
    df_hh.loc[df_hh.both_pres_in_april.isnull(), "both_pres_in_april"] = False
    df_hh["both_pres_in_april"] = df_hh.both_pres_in_april.astype(bool)

    c = (
        df_hh.query(
            "month.isin(['2020-03-01']) & hours_total_uncond.notnull() & hours_total_uncond_partner.notnull()"
        )
        .groupby("personal_id")["ones"]
        .sum()
    )
    c = c == 1
    c.name = "both_pres_in_march"
    df_hh = df_hh.join(c)
    df_hh.loc[df_hh.both_pres_in_march.isnull(), "both_pres_in_march"] = False
    df_hh["both_pres_in_march"] = df_hh.both_pres_in_march.astype(bool)

    c = (
        df_hh.query("month.isin(['2020-04-01']) & hours_total_uncond.notnull()")
        .groupby("personal_id")["ones"]
        .sum()
    )
    c = c == 1
    c.name = "pres_in_april"
    df_hh = df_hh.join(c)
    df_hh.loc[df_hh.pres_in_april.isnull(), "pres_in_april"] = False
    df_hh["pres_in_april"] = df_hh.pres_in_april.astype(bool)

    c = (
        df_hh.query("month.isin(['2020-03-01']) & hours_total_uncond.notnull()")
        .groupby("personal_id")["ones"]
        .sum()
    )
    c = c == 1
    c.name = "pres_in_march"
    df_hh = df_hh.join(c)
    df_hh.loc[df_hh.pres_in_march.isnull(), "pres_in_march"] = False
    df_hh["pres_in_march"] = df_hh.pres_in_march.astype(bool)

    df_hh["pres_in_march_april"] = (df_hh.pres_in_march & df_hh.pres_in_april).astype(
        bool
    )
    df_hh["both_pres_in_march_april"] = (
        df_hh.both_pres_in_march & df_hh.both_pres_in_april
    ).astype(bool)

    # Father/Mother hours variables
    hrs = [
        "hours_home_office_kids_care",
        "hours_home_office_no_kids",
        "hours_workplace_tu",
        "hours_childcare",
        "hours_commute",
        "hours_childcare_total",
        "hours_childcare_total_strict",
        "hours_homeschooling",
        "hours_chores",
        "hours_leisure_total",
        "hours_childcare_total",
        "hours_work_total",
        "hours_total_uncond",
        "essential_worker_w2",
        "work_perc_home",
        "age_groups",
        "self_employed_baseline",
        "parttime_baseline_covid",
        "parttime_baseline",
        "fulltime_baseline",
        "out_of_laborf_baseline",
        "labor_force",
        "labor_force_coarse",
        "work_status_baseline",
        "part_time_tu",
        "not_working_baseline",
        "sector",
        "profession",
        "reason_care_april",
        "reason_care_march",
        "less_care",
        "reason_care_baseline",
    ]
    dici = {"female": "father", "male": "mother"}

    for colu in hrs:
        for key, value in dici.items():
            colu_new = f"{colu}_{value}"
            df_hh[colu_new] = df_hh[colu]

            df_hh.loc[(df_hh.gender == key), colu_new] = df_hh.loc[
                (df_hh.gender == key), colu + "_partner"
            ]

    # Work gap using mean
    for parent in ["mother", "father"]:
        mean = (
            df_hh.query("month.isin(['2020-04-01', '2020-03-01'])")
            .groupby("personal_id")[f"hours_total_uncond_{parent}"]
            .mean()
        )
        mean.name = f"hours_total_uncond_mean_march_april_{parent}"
        df_hh = df_hh.join(mean)
        df_hh[f"hours_total_mean_ma_{parent}"] = df_hh[f"hours_total_uncond_{parent}"]
        df_hh.loc[
            df_hh.index.get_level_values("month").isin(["2020-04-01", "2020-03-01"]),
            f"hours_total_mean_ma_{parent}",
        ] = df_hh.loc[
            df_hh.index.get_level_values("month").isin(["2020-04-01", "2020-03-01"]),
            f"hours_total_uncond_mean_march_april_{parent}",
        ]
        condition = df_hh.both_pres_in_march_april & (
            df_hh.index.get_level_values("month") == "2020-03-01"
        )
        df_hh.loc[condition, f"hours_total_mean_ma_{parent}"] = np.nan
        condition = (
            df_hh.both_pres_in_april
            & ~df_hh.both_pres_in_march_april
            & (df_hh.index.get_level_values("month") == "2020-03-01")
        )
        df_hh.loc[condition, f"hours_total_mean_ma_{parent}"] = np.nan
        condition = (
            df_hh.both_pres_in_march
            & ~df_hh.both_pres_in_march_april
            & (df_hh.index.get_level_values("month") == "2020-04-01")
        )
        df_hh.loc[condition, f"hours_total_mean_ma_{parent}"] = np.nan

    condition = (df_hh.pres_in_march & ~df_hh.pres_in_april) & (
        df_hh.index.get_level_values("month") == "2020-04-01"
    )
    df_hh.loc[condition, f"hours_total_mean_ma_mother"] = np.nan
    df_hh.loc[condition, f"hours_total_mean_ma_father"] = np.nan

    condition = (~df_hh.pres_in_march & df_hh.pres_in_april) & (
        df_hh.index.get_level_values("month") == "2020-03-01"
    )
    df_hh.loc[condition, f"hours_total_mean_ma_mother"] = np.nan
    df_hh.loc[condition, f"hours_total_mean_ma_father"] = np.nan

    df_hh["work_gap_mean_ma"] = (
        df_hh.hours_total_mean_ma_father - df_hh.hours_total_mean_ma_mother
    )

    # Work gap
    df_hh["work_gap"] = (
        df_hh.hours_total_uncond_father - df_hh.hours_total_uncond_mother
    )

    condition = ~df_hh.both_pres_in_march & ~df_hh.both_pres_in_april
    assert condition.sum() != df_hh.shape[0], "Condition always True"
    df_hh.loc[condition, "work_gap"] = df_hh.loc[condition, "work_gap_mean_ma"]

    # Work gap april imputed with march/mean values if available
    df_hh["work_gap_imputed_april"] = df_hh["work_gap"]
    condition = (
        df_hh.index.get_level_values("month") == "2020-04"
    ) & df_hh.work_gap.isnull()
    df_hh.loc[condition, "work_gap_imputed_april"] = (
        df_hh.loc[condition, "hours_total_uncond_mean_march_april_father"]
        - df_hh.loc[condition, "hours_total_uncond_mean_march_april_mother"]
    )

    # Generate max hours total again
    df_hh["max_hours_total_partner"] = (
        df_hh.groupby("personal_id")["hours_total_partner"].max()
    ).reindex(df_hh.index, level="personal_id")
    df_hh["max_hours_total"] = (
        df_hh.groupby("personal_id")["hours_total"].max()
    ).reindex(df_hh.index, level="personal_id")

    df_hh["breadwinner_hrs"] = np.nan
    condition = df_hh.hours_total_uncond_father - 5 > df_hh.hours_total_uncond_mother
    df_hh.loc[condition, "breadwinner_hrs"] = "father"
    condition = df_hh.hours_total_uncond_father < df_hh.hours_total_uncond_mother - 5
    df_hh.loc[condition, "breadwinner_hrs"] = "mother"
    condition = (
        df_hh.hours_total_uncond_father >= df_hh.hours_total_uncond_mother - 5
    ) & (df_hh.hours_total_uncond_father - 5 <= df_hh.hours_total_uncond_mother)
    df_hh.loc[condition, "breadwinner_hrs"] = "equal"

    df_hh = get_baseline(df_hh, "breadwinner_hrs_baseline", "breadwinner_hrs")

    # Reason care on hh level
    df_hh["less_care_comb"] = np.nan
    df_hh.loc[
        ((df_hh.less_care == 1) & (df_hh.less_care_partner == 1)), "less_care_comb"
    ] = "both"
    df_hh.loc[
        ((df_hh.less_care_mother == 0) & (df_hh.less_care_father == 1)),
        "less_care_comb",
    ] = "father"
    df_hh.loc[
        ((df_hh.less_care_mother == 1) & (df_hh.less_care_father == 0)),
        "less_care_comb",
    ] = "mother"
    df_hh.loc[
        ((df_hh.less_care == 0) & (df_hh.less_care_partner == 0)), "less_care_comb"
    ] = "neither"
    df_hh["less_care_comb"] = pd.Categorical(df_hh["less_care_comb"])

    # Create imputed variable
    df_hh["less_care_comb_imputed_april"] = df_hh["less_care_comb"]
    condition = (
        df_hh.index.get_level_values("month") == "2020-04"
    ) & df_hh.work_gap.isnull()
    mother = (df_hh.reason_care_baseline_mother == 1) & (
        df_hh.reason_care_baseline_father == 0
    )
    df_hh.loc[(condition & mother), "less_care_comb_imputed_april"] = "mother"

    father = (df_hh.reason_care_baseline_mother == 0) & (
        df_hh.reason_care_baseline_father == 1
    )
    df_hh.loc[(condition & father), "less_care_comb_imputed_april"] = "father"

    both = (df_hh.reason_care_baseline_mother == 1) & (
        df_hh.reason_care_baseline_father == 1
    )
    df_hh.loc[(condition & both), "less_care_comb_imputed_april"] = "both"

    neither = (df_hh.reason_care_baseline_mother == 0) & (
        df_hh.reason_care_baseline_father == 0
    )
    df_hh.loc[(condition & neither), "less_care_comb_imputed_april"] = "neither"

    df_hh = cc_variables_on_hh_level(df_hh)

    return df_hh


def cc_variables_on_hh_level(df):
    """Generate variables from time use cc."""
    df = df.copy()

    # Mother/father
    df["hours_cc_young_female"] = df["hours_cc_young_self"]
    df.loc[df.gender == "male", "hours_cc_young_female"] = df.loc[
        df.gender == "male", "hours_cc_young_partner"
    ]

    df["hours_cc_young_male"] = df["hours_cc_young_self"]
    df.loc[df.gender == "female", "hours_cc_young_male"] = df.loc[
        df.gender == "female", "hours_cc_young_partner"
    ]

    df["hours_cc_female"] = df["hours_cc_self"]
    df.loc[df.gender == "male", "hours_cc_female"] = df.loc[
        df.gender == "male", "hours_cc_partner"
    ]

    df["hours_cc_male"] = df["hours_cc_self"]
    df.loc[df.gender == "female", "hours_cc_male"] = df.loc[
        df.gender == "female", "hours_cc_partner"
    ]

    # Deal with single parents
    condition = (df.single_parent == 1) & (df.gender == "male")
    df.loc[condition, "hours_cc_young_female"] = df.loc[
        condition, "hours_cc_young_expartner"
    ]

    condition = (df.single_parent == 1) & (df.gender == "female")
    df.loc[condition, "hours_cc_young_male"] = df.loc[
        condition, "hours_cc_young_expartner"
    ]

    condition = (df.single_parent == 1) & (df.gender == "female")
    df.loc[condition, "hours_cc_male"] = df.loc[condition, "hours_cc_expartner"]

    condition = (df.single_parent == 1) & (df.gender == "male")
    df.loc[condition, "hours_cc_female"] = df.loc[condition, "hours_cc_expartner"]

    # Generate variable that contains info that is not captured in mother or father
    # I.e. for single parents a partner variable/ missing for
    # for non-single parents an expartner variable
    condition = df.single_parent == 1
    df["hours_cc_expartner_alt"] = df["hours_cc_expartner"]
    df.loc[condition, "hours_cc_expartner_alt"] = np.nan
    df["hours_cc_young_expartner_alt"] = df["hours_cc_young_expartner"]
    df.loc[condition, "hours_cc_young_expartner_alt"] = np.nan

    condition = df.single_parent == 0
    df["hours_cc_partner_alt"] = df["hours_cc_partner"]
    df.loc[condition, "hours_cc_partner_alt"] = np.nan
    df["hours_cc_young_partner_alt"] = df["hours_cc_young_partner"]
    df.loc[condition, "hours_cc_young_partner_alt"] = np.nan

    # Take the youngest child
    condition = df.hours_cc_young_self.notnull()
    df["hours_cc_youngest_female"] = df["hours_cc_self"]
    df.loc[condition, "hours_cc_youngest_female"] = df.loc[
        condition, "hours_cc_young_self"
    ]
    df.loc[df.gender == "male", "hours_cc_youngest_female"] = df.loc[
        df.gender == "male", "hours_cc_partner"
    ]
    df.loc[(condition & (df.gender == "male")), "hours_cc_youngest_female"] = df.loc[
        (condition & (df.gender == "male")), "hours_cc_young_self"
    ]

    df["hours_cc_youngest_male"] = df["hours_cc_self"]
    df.loc[condition, "hours_cc_youngest_male"] = df.loc[
        condition, "hours_cc_young_self"
    ]
    df.loc[df.gender == "female", "hours_cc_youngest_male"] = df.loc[
        df.gender == "female", "hours_cc_partner"
    ]
    df.loc[(condition & (df.gender == "female")), "hours_cc_youngest_male"] = df.loc[
        (condition & (df.gender == "female")), "hours_cc_young_self"
    ]

    # Calculate Gender Gap
    df["cc_gap_young"] = df.hours_cc_youngest_female - df.hours_cc_youngest_male
    df["cc_gap_school"] = df.hours_cc_female - df.hours_cc_male

    return df


def children_variables(df):
    """Create children indicator.

    Challenge: Background data is not fully accurate, and routing was messed
    up in time use survey, so that unwedded partners were not asked
    children_school, children_not_school.

    For these people, the answers are imputed in case these are availabel.

    This means this function needs to be executed after the hh data set is
    calculated.

    Further, for 2019 the same variables need to be generated from background
    data.

    """
    df = df.copy()

    condition19 = df.index.get_level_values("month") == "2019-11-01"
    condition20 = df.index.get_level_values("month") != "2019-11-01"
    conditionhh = df.hh_position.isin(
        ["Household head", "Wedded partner", "Unwedded partner"]
    )

    # Children below 12
    # Child indicator
    condition1 = (covid.nr_children_below_12 > 0) & (conditionhh)

    condition2 = ((df.nr_children_below_12 > 0) & ~conditionhh) | (
        df.nr_children_below_12 == 0
    )

    df["child_below_12"] = np.nan
    df.loc[condition1, "child_below_12"] = 1
    df.loc[condition2, "child_below_12"] = 0
    df.loc[condition19, "child_below_12"] = 0
    df.loc[
        condition19 & conditionhh & (df.age_youngest_child <= 12), "child_below_12"
    ] = 1
    df.loc[
        condition20 & df.child_below_12.isnull() & (df.age_youngest_child <= 12),
        "child_below_12",
    ] = 1
    df.loc[condition20 & df.child_below_12.isnull(), "child_below_12"] = 0
    df.loc[(df.index.get_level_values("personal_id") == 816702), "child_below_12"] = 0

    # Children school age (between 4 and 18)
    df.loc[condition19, "children_school"] = 0
    df.loc[df.children_school.isnull(), "children_school"] = df.loc[
        df.children_school.isnull(), "children_school_partner"
    ]
    df.loc[
        (
            conditionhh
            & (df.age_youngest_child <= 18)
            & (df.age_youngest_child >= 4)
            & (df.children_school.isnull() | condition19)
        ),
        "children_school",
    ] = 1

    # Younger than school age (between 0 and 4)
    df.loc[condition19, "children_not_school"] = 0
    df.loc[df.children_not_school.isnull(), "children_not_school"] = df.loc[
        df.children_not_school.isnull(), "children_not_school_partner"
    ]
    df.loc[
        (
            conditionhh
            & (df.age_youngest_child < 4)
            & (df.children_not_school.isnull() | condition19)
        ),
        "children_not_school",
    ] = 1

    # School age or younger
    df["child_school_or_younger"] = np.nan
    df.loc[
        ((df.children_school == 1) | (df.children_not_school == 1)),
        "child_school_or_younger",
    ] = 1
    df.loc[
        ((df.children_school == 0) & (df.children_not_school == 0)),
        "child_school_or_younger",
    ] = 0
    df.loc[
        (condition20 & df.child_school_or_younger.isnull()), "child_school_or_younger"
    ] = 0

    # interaction variables
    df["gender_child"] = (
        df["gender"].dropna().astype(str)
        + "_"
        + df["child_school_or_younger"]
        .replace({1: "child", 0: "no_child"})
        .dropna()
        .astype(str)
    )
    df["gender_child"] = pd.Categorical(df["gender_child"])

    # Children below 16
    df["child_below_16"] = 0
    df.loc[((df.age_youngest_child <= 16) & conditionhh), "child_below_16"] = 1

    # Some childcare vars
    df["cc_only_me_full"] = df.cc_only_me
    df.loc[df.child_below_12 == 0, "cc_only_me_full"] = False

    return df


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


if __name__ == "__main__":
    # Load data

    partner_links = pd.read_pickle(ppj("IN_DATA", "partner_links.pickle"))
    covid = pd.read_parquet(ppj("OUT_DATA", "work-childcare-ind.parquet"))

    # Merge in partner info
    covid_hh = generate_hh_level_data(
        covid,
        partner_links,
        timevarying_background=timevarying_variables,
        timeconstant=time_invariant_vars + background_variables,
    )
    # Create variables that rely on partner info
    out = generate_vars_for_couples(covid_hh)

    # Make sure it is sorted
    out = out.sort_index()

    # Export long format
    try:
        out.to_parquet(ppj("OUT_DATA", "work-childcare-long.parquet"))
    except:
        colus = list(out.columns)
        colus.remove("hours_workplace")
        for col in colus:
            try:
                out[["hours_workplace", col]].to_parquet("test.parquet")
            except:
                if out[col].dtype.name == "category":
                    out[col].cat.categories = [str(c) for c in out[col].cat.categories]
                else:
                    print(
                        f"!! {col} has dtype {out[col].dtype} incompatible with parquet and is set to categorical"
                    )
                    out[col] = out[col].astype(str).astype("category")

        out.to_parquet(path=ppj("OUT_DATA", "work-childcare-long.parquet"))

    # Make wide format
    wide = out.unstack(1)
    newcolu = [c[0] + "_" + str(c[1])[:7] for c in wide.columns]
    wide.columns = newcolu
    wide.dropna(axis=1, inplace=True, how="all")

    # Export wide format
    wide.to_parquet(path=ppj("OUT_DATA", "work-childcare-wide.parquet"))
