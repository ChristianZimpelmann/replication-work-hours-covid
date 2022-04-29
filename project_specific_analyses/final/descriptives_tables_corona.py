"""Produce descriptive tables.


"""
import numpy as np
import pandas as pd

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.analysis.plot_functions import weighted_means_by
from project_specific_analyses.analysis.table_functions import create_means_output_table
from project_specific_analyses.analysis.table_functions import write_table
from project_specific_analyses.library.plot_labels import column_to_table
from project_specific_analyses.library.plot_labels import index_to_table
from project_specific_analyses.library.plot_labels import labels
from project_specific_analyses.library.plot_labels import regressor_order
from project_specific_analyses.library.plot_labels import time_labels
from project_specific_analyses.library.plot_labels import time_labels_no_year
from project_specific_analyses.library.plot_labels import time_labels_short_no_year


def descriptives_table(
    data,
    categorical_vars,
    numerical_vars,
    dummy_vars,
    order=None,
    by=None,
    median_vars=[],
):
    """Create descriptive table."""
    variables_needed = categorical_vars + numerical_vars + dummy_vars
    if by:
        variables_needed += by
    tab = data[variables_needed].groupby("personal_id").first()
    for v in categorical_vars:
        dummies = pd.get_dummies(tab[v])
        dummies.rename(
            columns={c: f"{v}_{str(c)}" for c in dummies.columns}, inplace=True
        )
        tab = tab.join(dummies)
        dummy_vars += list(dummies.columns)
    variables_used = dummy_vars + numerical_vars

    # scaling money variables
    scale_to_thousands = ["gross_income", "wealth_hh_eqv", "net_income_2y_equiv"]
    for v in scale_to_thousands:
        if v in tab:
            tab[v] *= 1 / 1000

    if by:
        descriptive_stats = tab.groupby(by)[variables_used].mean()

        # formatting
        for v in median_vars:
            descriptive_stats[v] = tab.groupby("gender")[v].median()
        descriptive_stats = descriptive_stats.T.round(2)
        descriptive_stats.loc["count"] = tab.groupby("gender")["age"].count().values

        descriptive_stats.loc["count"] = descriptive_stats.loc["count"].apply(
            lambda x: f"{x:.0f}"
        )

    else:
        descriptive_stats = (
            tab[variables_used]
            .describe(percentiles=[0.25, 0.5, 0.75])
            .loc[["count", "mean", "std", "25%", "50%", "75%"]]
        )
        # formatting
        descriptive_stats = descriptive_stats.T.round(2)
        for v in dummy_vars:
            descriptive_stats.loc[v, ["std", "25%", "50%", "75%"]] = ""
        descriptive_stats["count"] = descriptive_stats["count"].apply(
            lambda x: f"{x:.0f}"
        )

    if order:
        descriptive_stats = descriptive_stats.reindex(order)

    descriptive_stats = descriptive_stats.rename(
        index=index_to_table, columns=column_to_table
    )

    return descriptive_stats


def descriptives_over_time(df_full):

    df_full["married"] = (df_full["civil_status"].dropna() == "Married").astype(float)
    df_full["hhh_partner"] = df_full["hhh_partner"].astype(float)

    columns = [
        "age",
        "female",
        "edu_lower_secondary_and_lower",
        "edu_upper_secondary",
        "edu_tertiary",
        "net_income_2y_equiv",
        "gross_income_groups_below 2500",
        "gross_income_groups_bet. 2500 and 3500",
        "gross_income_groups_above 3500",
        "work_status_spec_baseline_full time",
        # "work_status_spec_baseline_not working",
        "work_status_spec_baseline_part time",
        "work_status_spec_baseline_self-employed",
        "hhh_partner",
        "married",
        "nr_children_below_12",
        "work_perc_home",
        "essential_worker_w2",
        # "essential_worker",
        "ever_affect_by_policy_str_Affected by policy",
        "ever_affect_by_policy_str_Never affected by policy",
        "ever_affect_by_policy_str_Don't know",
    ]
    data = df_full.query(
        "18 <= age <= 66 and month != ['2019-11-01', '2020-11-01']"
    ).dropna(subset=["hours_total_uncond"])

    # Add dummies for categorical variables
    categorical_vars = [
        "edu",
        "work_status_spec_baseline",
        "gross_income_groups",
        "ever_affect_by_policy_str",
    ]
    for v in categorical_vars:
        dummies = pd.get_dummies(data[v].dropna())
        dummies.rename(
            columns={c: f"{v}_{str(c)}" for c in dummies.columns}, inplace=True
        )
        data = data.join(dummies)

    out = weighted_means_by(
        cols=columns,
        data=data.reset_index(),
        weight_col="ones",
        dropna=False,
        by=["month"],
    )
    out = out.T
    out.columns.name = None
    rounding = {c: 3 for c in columns}
    out = create_means_output_table(out, columns, None, rounding=rounding)

    out = out.rename(
        index=index_to_table,
        columns=time_labels,
    )

    write_table(
        out,
        ppj("OUT_TABLES", "descriptives", "descriptives_by_month_full_sample.tex"),
        column_format="l" + "r" * len(out.columns),
    )
    data = data.query("hours_uncond_baseline >= 10")
    out = weighted_means_by(
        cols=columns,
        data=data.reset_index(),
        weight_col="ones",
        dropna=False,
        by=["month"],
    )
    out = out.T
    out.columns.name = None
    rounding = {c: 3 for c in columns}
    out = create_means_output_table(out, columns, None, rounding=rounding)

    out = out.rename(index=index_to_table, columns=time_labels)

    write_table(
        out,
        ppj("OUT_TABLES", "descriptives", "descriptives_by_month_working_sample.tex"),
        column_format="l" + "r" * len(out.columns),
    )


def work_status_hours_over_time(weight_col, rows, file_name):
    """Create table that shows work status and hours worked over time.

    Args:
        weight_col (string): column name of weighting variable
        rows (list of tuples): rows in the table and associated data
        file_name (string): filename

    """
    out_list = []

    # Iterate over rows
    for col, temp in rows:
        if isinstance(temp, pd.DataFrame):
            out = weighted_means_by(
                cols=[col], data=temp, weight_col=weight_col, by=["month"]
            )
            out = out.T
            out.columns.name = None
            if col in ["unemployed", "out_of_laborf"]:
                rounding = {c: 1 for c in [col]}
            elif col in ["home_share"]:
                rounding = {c: 2 for c in [col]}
            else:
                rounding = {c: 1 for c in [col]}
            out = create_means_output_table(out, [col], None, rounding=rounding)
            # Some renamings
            out = out.rename(
                index=index_to_table,
                columns=time_labels_short_no_year,
            )
            out = out.rename(
                index={
                    "out of laborforce": "out of laborforce (perc.)",
                    "unemployed": "unemployed (perc.)",
                }
            )
            out_list.append(out)
    res = pd.concat(out_list)

    # Iterate over rows for rows that are specified directly
    for col, temp in rows:
        if not isinstance(temp, pd.DataFrame):
            res.loc[col] = [format(i, ".1f") for i in temp]

    # Output table to latex
    if file_name:
        full_path = ppj("OUT_TABLES", "descriptives", file_name + ".tex")
        with open(full_path, "w") as my_table:
            n_index = len(res.index.names)
            n_cols = len(res.columns)
            my_table.write(
                res.to_latex(
                    escape=False,
                    column_format="l" * n_index + "p{1cm}" + "p{0.7cm}" * (n_cols - 1),
                )
            )
    return res


def joint_socio_job_charc(data):
    """Generate table showing joint distribution of socio economic and job characteristics"""

    # Education
    res1 = data.groupby("edu")[["essential_worker_w2", "work_perc_home"]].mean()
    res1.index = res1.index.astype(str)
    res1 = res1.rename(
        index={i: "education: " + i.replace("_", " ") for i in res1.index}
    )

    # Gross income
    res2 = data.groupby("gross_income_groups")[
        ["essential_worker_w2", "work_perc_home"]
    ].mean()
    res2.index = res2.index.astype(str)
    res2 = res2.rename(
        index={i: "gross income: " + i.replace("_", " ") for i in res2.index}
    )
    res = pd.concat([res1, res2]).round(2)

    res = res.rename(
        columns={
            "essential_worker_w2": "essential worker",
            "work_perc_home": "frac. work doable from home",
        }
    )

    path_out = ppj("OUT_TABLES", "descriptives", "job_charac_by_edu_income.tex")
    my_table = open(path_out, "w")
    my_table.write(res.to_latex(escape=True, column_format="l" + "r" * 2))
    my_table.close()


if __name__ == "__main__":
    df_full = pd.read_parquet(ppj("OUT_DATA", "work-childcare-long.parquet"))
    data = (
        df_full.query(
            "18 <= age <= 66 and hours_uncond_baseline >= 10 and month != ['2019-11-01', '2020-11-01']"
        )
        .dropna(subset=["hours_total_uncond"])
        .copy()
    )

    data["self-employed_baseline"] = (
        data["work_status_baseline"].dropna() == "self-employed"
    ).astype(float)
    data["employed_baseline"] = (
        data["work_status_baseline"].dropna() == "employed"
    ).astype(float)
    # data["work_perc_home"] /= 100

    categorical_vars = ["edu", "work_status_spec_baseline", "ever_affect_by_policy_str"]
    numerical_vars = ["age", "gross_income", "work_perc_home", "net_income_2y_equiv"]
    dummy_vars = [
        "female",
        "essential_worker_w2",
        # "ever_affect_by_policy_str",
    ]

    order = [
        "female",
        "age",
        "edu_lower_secondary_and_lower",
        "edu_upper_secondary",
        "edu_tertiary",
        "net_income_2y_equiv",
        "work_status_spec_baseline_full time",
        "work_status_spec_baseline_part time",
        "work_status_spec_baseline_self-employed",
        # "work_status_spec_baseline_not working",
        "gross_income",
        "essential_worker_w2",
        "work_perc_home",
        # "applied_any_policy_any",
        "ever_affect_by_policy_str_Affected by policy",
        "ever_affect_by_policy_str_Never affected by policy",
        "ever_affect_by_policy_str_Don't know",
    ]

    tab = descriptives_table(data, categorical_vars, numerical_vars, dummy_vars, order)
    write_table(
        tab,
        ppj("OUT_TABLES", "descriptives", "descriptives_work_hours.tex"),
        column_format="l" + "r" * 6,
        full_width=True,
    )

    descriptives_over_time(df_full)

    data = df_full.query(
        "18 <= age <= 66 and month != ['2019-11-01', '2020-11-01']"
    ).reset_index()
    # work status hours over time
    # Specify rows in table
    for c in ["out_of_laborf", "unemployed"]:
        data[c] *= 100
    work_status_hours_over_time(
        weight_col="ones",
        rows=[
            ("hours_total_uncond", data.query("hours_uncond_baseline >= 10")),
            ("hours_home_uncond", data.query("hours_uncond_baseline >= 10")),
            ("home_share", data.query("hours_uncond_baseline >= 10")),
        ],
        file_name="descriptives_hours",
    )
    work_status_hours_over_time(
        weight_col="ones",
        rows=[
            ("out_of_laborf", data),
            ("unemployed", data.query("out_of_laborf == 0")),
        ],
        file_name="descriptives_hours_unemployment",
    )
    work_status_hours_over_time(
        weight_col="ones",
        rows=[
            ("out_of_laborf", data.query("25 <= age <= 44")),
            ("unemployed", data.query("25 <= age <= 44 and out_of_laborf == 0")),
            (
                "out of laborf CBS",
                100 - np.array([88.4, 88.4, 87.9, 88.0, 88.1, 88.6, 88.8]),
            ),
            ("unemployed CBS", np.array([3, 3, 3.1, 3, 3.5, 3.5, 3.2])),
        ],
        file_name="descriptives_hours_unemployment_comparison",
    )
    work_status_hours_over_time(
        weight_col="ones",
        rows=[
            ("hours_total_uncond", data.query("max_hours_total >= 10")),
            ("hours_home_uncond", data.query("max_hours_total >= 10")),
            ("home_share", data.query("hours_uncond_baseline >= 10")),
        ],
        file_name="descriptives_hours_max_hours",
    )

    # joint dist of job charac and socio-economic
    joint_socio_job_charc(data)
