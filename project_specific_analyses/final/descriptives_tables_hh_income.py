"""Produce descriptive tables.


"""
import pandas as pd

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.analysis.table_functions import write_table
from project_specific_analyses.library.plot_labels import column_to_table
from project_specific_analyses.library.plot_labels import index_to_table
from project_specific_analyses.library.plot_labels import time_labels

time_labels = {k: v[:-5] for k, v in time_labels.items()}

if __name__ == "__main__":
    df_full = pd.read_parquet(ppj("OUT_DATA", "work-childcare-long.parquet"))
    hh_income = pd.read_parquet(ppj("OUT_DATA", "hh_income.parquet"))
    data = (
        df_full.query("20 <= age <= 65 and month >= '2020-02'")
        .dropna(subset=["hours_total_uncond"])
        .copy()
    )

    # ToDo: Redo income split on this sample?

    data["edu_tertiary"] = (data["edu"].dropna() == "tertiary").astype(float)
    data["married"] = (data["civil_status"].dropna() == "Married").astype(float)
    data["hhh_partner"] = data["hhh_partner"].astype(float)

    # Basic characteristics
    tab = (
        data.groupby("net_income_2y_equiv_q")[
            [
                "age",
                "edu_tertiary",
                "female",
                "hhh_partner",
                "married",
                "nr_children_below_12",
                "self_employed_baseline",
                "parttime_baseline_covid",
                "work_perc_home",
                "essential_worker_w2",
                "applied_any_policy_05",
                #            "application_now_yes_05",
                #            "application_togs_yes_05",
            ]
        ]
        .mean()
        .round(2)
    ).T
    tab.columns.name = None
    tab.columns = [f"Q{i + 1}" for i in range(5)]

    tab = tab.rename(index=index_to_table)

    write_table(
        tab,
        ppj("OUT_TABLES", "hh_income", "hh_income_split_characteristics.tex"),
        column_format="l" + "r" * len(tab.columns),
    )

    # mean hh income
    tab = (
        hh_income.query("month > '2020-02' and month != '2020-05' and 20 <= age <= 65")
        .groupby(["month", "net_income_2y_equiv_q"])["net_income_hh_equiv"]
        .mean()
        .reset_index()
        .pivot(index="month", columns="net_income_2y_equiv_q")["net_income_hh_equiv"]
        .T
    )
    tab.insert(
        0,
        "pre-CoViD",
        (
            hh_income.query("month == '2020-02' and 20 <= age <= 65")
            .groupby("net_income_2y_equiv_q")["net_income_hh_equiv_baseline"]
            .mean()
        ),
    )
    tab = tab.round(0).astype(int)
    tab.index.name = None
    tab.index = [f"Q{i + 1}" for i in range(5)]
    tab.columns.name = None
    tab = tab.rename(columns={**time_labels, **column_to_table})
    write_table(
        tab,
        ppj("OUT_TABLES", "hh_income", "hh_income_means.tex"),
        column_format="l" + "r" * len(tab.columns),
    )

    # percentiles relative change hh income
    tab = (
        (
            hh_income.query(
                "month > '2020-02' and month != '2020-05' and "
                "20 <= age <= 65 and net_income_hh_baseline > 0"
            )
            .groupby(["month", "net_income_2y_equiv_q"])[
                "rel_change_net_income_hh_equiv"
            ]
            .describe()
        )[["25%", "75%"]]
        .stack()
        .unstack("month")
        .unstack()
    )
    tab = tab * 100
    tab = tab.round(0).astype(int)
    tab.index.name = None
    tab.index = [f"Q{i + 1}" for i in range(5)]
    tab.columns.names = [None, None]
    tab = tab.rename(columns={**time_labels, **column_to_table})

    write_table(
        tab,
        ppj("OUT_TABLES", "hh_income", "hh_income_rel_change_perc.tex"),
        column_format="l" + "r" * len(tab.columns),
    )
