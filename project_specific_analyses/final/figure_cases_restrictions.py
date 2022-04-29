"""Produce descriptive tables.


"""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from utilities.colors import get_colors

from output.project_paths import project_paths_join as ppj

if __name__ == "__main__":

    colors = get_colors("blue-orange", 2)

    wid = pd.read_csv(ppj("RAW_DATA", "owid-covid-data.csv"))
    wid["date"] = pd.to_datetime(wid["date"])
    wid = wid.query("location == 'Netherlands'")
    wid = wid.query("'2020-03-15' < date < '2020-12-30'").set_index("date")

    data = pd.read_csv(ppj("RAW_DATA", "OxCGRT_latest.csv"))
    data = data.query("CountryName == 'Netherlands'")
    data["date"] = pd.to_datetime(data["Date"], format="%Y%m%d")
    data = data.query("'2020-03-15' < date < '2020-12-30'").set_index("date")

    fig, ax = plt.subplots(1, 1, figsize=(7, 5))
    ax = sns.lineplot(
        y="new_cases_smoothed_per_million",
        x="date",
        data=wid.reset_index(),
        legend=False,
        label="daily new cases (left axis, log scale)",
        color=colors[0],
    )
    ax.set_yscale("log")

    ax.set_yticks([10, 100, 1000])
    ax.set_yticklabels(["10", "100", "1000"])
    ax.set_ylabel("Daily new cases per million people")
    ax.set_xlabel("Month in 2020")

    ax2 = ax.twinx()
    ax2 = sns.lineplot(
        y="StringencyIndexForDisplay",
        x="date",
        data=data.reset_index(),
        legend=False,
        label="stringency index (right axis)",
        color=colors[1],
    )
    ax2.set_ylim(0, 100)

    ax2.set_xticks(
        [
            pd.to_datetime("2020-03-22"),
            pd.to_datetime("2020-04-14"),
            pd.to_datetime("2020-05-12"),
            pd.to_datetime("2020-06-10"),
            pd.to_datetime("2020-09-18"),
            pd.to_datetime("2020-12-17"),
        ],
        minor=False,
    )
    ax2.set_xticklabels(
        labels=["Mar", "Apr", "May", "Jun", "Sept", "Dec"],
    )
    ax2.set_xlabel("Month in 2020")
    ax2.set_ylabel("Stringency Index")

    plt.subplots_adjust(bottom=0.22)
    # plt.tight_layout()

    ax.figure.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 0.12),
        fancybox=True,
        shadow=False,
        ncol=2,
    )
    ax.grid(axis="x")
    # ax2.grid(axis="x")
    for format in "pdf", "png", "svg":
        plt.savefig(
            ppj(
                "OUT_FIGURES",
                "background",
                f"covid_cases_and_stringency_over_time.{format}",
            ),
            transparent=False,
        )
