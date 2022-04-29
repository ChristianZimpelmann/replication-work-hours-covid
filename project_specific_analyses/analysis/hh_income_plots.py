import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from utilities.colors import get_colors

from output.project_paths import project_paths_join as ppj

sns.set_style("whitegrid")


def rel_change_plot(var, legend_titles, drop_may, data, filename):
    fig, ax = plt.subplots(figsize=(6, 6))
    median = (
        data.groupby(["month_nice", var])["rel_change_net_income_hh_equiv"]
        .quantile(0.5)
        .unstack(1)
        .drop(index=["Jan", "Feb"])
    )
    lower = (
        data.groupby(["month_nice", var])["rel_change_net_income_hh_equiv"]
        .quantile(0.25)
        .unstack(1)
        .drop(index=["Jan", "Feb"])
    )
    upper = (
        data.groupby(["month_nice", var])["rel_change_net_income_hh_equiv"]
        .quantile(0.75)
        .unstack(1)
        .drop(index=["Jan", "Feb"])
    )

    if drop_may:
        median.loc["May"] = (
            median.loc["Apr"] + (median.loc["Jun"] - median.loc["Apr"]) / 2
        )
        lower.loc["May"] = lower.loc["Apr"] + (lower.loc["Jun"] - lower.loc["Apr"]) / 2
        upper.loc["May"] = upper.loc["Apr"] + (upper.loc["Jun"] - upper.loc["Apr"]) / 2
        ylim = (-20, 30)
    else:
        ylim = (-20, 50)

    median.plot(ax=ax, color=get_colors("categorical", 3))
    lower.plot(
        ax=ax,
        linestyle="--",
        label="1$^{st} Quartile",
        color=get_colors("categorical", 3),
    )
    upper.plot(
        ax=ax,
        linestyle="--",
        label="3$^{rd} Quartile",
        color=get_colors("categorical", 3),
    )

    plt.xticks(fontsize="large")

    # Shrink current axis's height by 10% on the bottom
    box = ax.get_position()
    ax.set_position(
        [box.x0, box.y0 + box.height * 0.225, box.width, box.height * 0.775]
    )

    handles, labels = ax.get_legend_handles_labels()
    med = mlines.Line2D([], [], color="grey", linestyle="-", label="Median")
    low = mlines.Line2D([], [], color="grey", linestyle="--", label="1$^{st} Quartile")
    upp = mlines.Line2D([], [], color="grey", linestyle="--", label="3$^{rd} Quartile")

    ax.legend(
        handles[0:3] + [med, low, upp],
        labels[0:3] + ["Median", r"1$^{st}$ Quartile", r"3$^{rd}$ Quartile"],
        fontsize="large",
        title=legend_titles,
        title_fontsize="large",
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.5, 0.0),
        bbox_transform=fig.transFigure,
    )

    plt.xticks(rotation=0, fontsize="large")
    plt.yticks(fontsize="large")
    plt.ylim(*ylim)
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.grid(axis="x")
    plt.xlabel("")
    plt.ylabel("Perc. change net equiv. HH income", fontsize="large")
    # plt.tight_layout()

    for end in ["png", "pdf", "svg"]:
        plt.savefig(ppj("OUT_FIGURES", f"income/{filename}.{end}"))

    plt.close()


if __name__ == "__main__":
    hh_income = pd.read_parquet(ppj("OUT_DATA", "hh_income.parquet"))
    hh_income = (
        hh_income.query("age >= 18 & age <= 66")
        .reset_index()
        .set_index(["personal_id", "month"])
    )

    # Create month_nice
    labels = {
        "2020-01-01": "Jan",
        "2020-02-01": "Feb",
        "2020-03-01": "Mar",
        "2020-04-01": "Apr",
        "2020-05-01": "May",
        "2020-06-01": "Jun",
        "2020-07-01": "Jul",
        "2020-08-01": "Aug",
        "2020-09-01": "Sep",
        "2020-10-01": "Oct",
        "2020-11-01": "Nov",
    }

    hh_income = hh_income.reset_index().set_index("personal_id")
    hh_income["month_nice"] = hh_income.month.astype(str).replace(to_replace=labels)
    hh_income["month_nice"] = pd.Categorical(
        hh_income.month_nice, categories=labels.values(), ordered=True
    )

    # Revalue
    hh_income["rel_change_net_income_hh_equiv"] = (
        hh_income["rel_change_net_income_hh_equiv"] * 100
    )

    quints = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}
    hh_income["quintiles"] = hh_income["net_income_2y_equiv_q"].replace(
        to_replace=quints
    )
    hh_income["quintiles"] = pd.Categorical(
        hh_income["quintiles"], categories=quints.values(), ordered=True
    )

    hh_income["terciles"] = hh_income.net_income_2y_equiv_q3.replace(to_replace=quints)
    hh_income["terciles"] = pd.Categorical(
        hh_income["terciles"], categories=["1st", "2nd", "3rd"]
    )

    edu_val = {
        "lower_secondary_and_lower": "lower secondary or less",
        "upper_secondary": "upper secondary",
        "tertiary": "tertiary",
    }
    hh_income["edu"] = pd.Categorical(
        hh_income.edu.replace(to_replace=edu_val),
        categories=edu_val.values(),
        ordered=True,
    )

    # Plots
    varis = {
        "terciles": "HH income tercile (pre-Covid)",
        "edu": "Education",
        "gross_income_groups": "Ind. gross income (pre-Covid)",
        "ever_affect_by_policy_str": "Affected by policy",
    }

    samples = {
        "full": hh_income,
        "working": hh_income.query(
            "max_hours_total >= 10 & work_status_baseline.isin(['employed', 'self-employed'])"
        ),
        "empl": hh_income.query(
            "max_hours_total >= 10 & work_status_baseline.isin(['employed'])"
        ),
        "selfempl": hh_income.query(
            "max_hours_total >= 10 & work_status_baseline.isin(['self-employed'])"
        ),
    }

    for var, title in varis.items():
        for name, sample in samples.items():
            for drop_may, without_may in {False: "", True: "-without-may"}.items():
                filename = f"rel-income-{var}-{name}{without_may}"
                rel_change_plot(var, title, drop_may, sample, filename)
