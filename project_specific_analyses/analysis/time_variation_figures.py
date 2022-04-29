"""Generate time-variation graphs for different groups and variables.


"""
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from table_functions import create_means_output_table
from utilities.colors import get_colors

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.analysis.plot_functions import weighted_means_by
from project_specific_analyses.analysis.time_variation_specs import (
    time_variation_groups,
)
from project_specific_analyses.library.plot_labels import time_labels_no_year

sns.set_style("whitegrid")


def generate_table_for_time_varying_plot(
    data, group, style, path, cols, label_rename_dict
):
    """Generate table showing values that are used in a time varying plot.

    Args:
        data (pd.DataFrame): data
        group (str): split variable (column of data)
        style (str): stype (second split) variable (column of data)
        path (str): path
        cols (list): outcome variables
    """
    if group:
        by = ["month", group, style] if style else ["month", group]
    else:
        by = ["month", style] if style else ["month"]
    out = weighted_means_by(cols=cols, data=data, weight_col="ones", by=by)
    out = out.T
    out.columns.name = None
    if cols[0] in ["unemployed", "out_of_laborf"]:
        rounding = {c: 3 for c in cols}
    else:
        rounding = {c: 1 for c in cols}
    out = create_means_output_table(out, cols, None, rounding=rounding)
    if group or style:
        out = out.stack("month")
        out = out.swaplevel().reindex(
            pd.MultiIndex.from_product(
                [out.index.unique(level=1), out.index.unique(level=0)]
            )
        )
        out.columns.name = None
        out.columns = [str(c) for c in out]
        if label_rename_dict:
            out = out.rename(columns=label_rename_dict)
    # Some renamings
    out = out.rename(
        index={
            **{
                "hours_workplace": "hours worked at the workplace",
                "hours_home": "hours worked from home",
                "hours_total": "total working hours",
                "out_of_laborf": "out of the laborforce",
                "unemployed": "unemployment rate",
            },
            **time_labels_no_year,
        },
        columns=time_labels_no_year,
    )
    if path:
        full_path = ppj("OUT_TABLES", "time-variation", path + ".tex")
        my_table = open(full_path, "w")
        n_index = len(out.index.names)
        n_cols = len(out.columns)
        my_table.write(
            out.to_latex(escape=False, column_format="l" * n_index + "r" * n_cols)
        )
        my_table.close()
        out.to_pickle(ppj("OUT_TABLES", "time-variation", path + ".pickle"))

    return out


def time_varying_plot(
    data,
    group,
    path,
    style=None,
    col="hours_total",
    baseline_col=None,
    label_rename_dict=None,
    ylabel="total working hours",
    ci=95,
    ylim=None,
    german=False,
    legend_title=True,
):
    if german and ylabel == "abs. change in hours":
        ylabel = "Veränderung der Arbeitsstunden"
    # Specify color
    if group:
        no_groups = len(data.loc[data[group].notnull(), group].unique())
        color = get_colors("categorical", no_groups)
    else:
        color = None

    # determine order
    if group:
        if data[group].dtype.name == "category":
            hue_order = data[group].cat.categories
        else:
            hue_order = None
    else:
        hue_order = None

    if style != None:
        if data[style].dtype.name == "category":
            style_order = data[style].cat.categories
        else:
            style_order = None
    else:
        style_order = None

    fig, ax = plt.subplots(figsize=(6, 6))
    sns.lineplot(
        x="month",
        y=col,
        hue=group,
        style=style,
        err_style="bars",
        data=data.reset_index(),
        ax=ax,
        palette=sns.color_palette(color),
        ci=ci,
        hue_order=hue_order,
        style_order=style_order,
        err_kws={"capsize": 5},
    )
    ax.grid(axis="x")
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    plt.xticks(
        [
            pd.to_datetime("2020-02-01"),
            pd.to_datetime("2020-03-22"),
            pd.to_datetime("2020-04-14"),
            pd.to_datetime("2020-05-12"),
            pd.to_datetime("2020-06-10"),
            pd.to_datetime("2020-09-18"),
            pd.to_datetime("2020-12-17"),
        ],
        ["before\nCovid-19", "Mar", "Apr", "May", "Jun", "Sep", "Dec"],
        fontsize="large",
    )
    plt.yticks(fontsize="large")
    plt.xlabel(None)
    plt.ylabel(ylabel, fontsize="large")

    if ylim:
        ax.set_ylim(ylim)

    if group:
        handles, labels_old = ax.get_legend_handles_labels()
        labels_new = []
        if baseline_col:
            n_obs = (
                data.query("month == '2020-02-01'")
                .dropna(subset=[group, baseline_col])
                .shape[0]
            )
            for l in labels_old:
                if label_rename_dict and l in label_rename_dict:
                    l_new = label_rename_dict[l]
                else:
                    l_new = l
                try:
                    baseline_level = (
                        data.query(f'month == "2020-02-01" and {group} == "{l}"')[
                            baseline_col
                        ]
                        .mean()
                        .round(1)
                    )
                    share = (
                        data.query(f'month == "2020-02-01" and {group} == "{l}"')[
                            baseline_col
                        ].count()
                        / n_obs
                    ).round(2)
                    if german:
                        l_new += f"; Anteil: {int(share * 100)}%; Baseline: {baseline_level} Stunden"
                    else:
                        l_new += f"; share: {int(share * 100)}%; baseline: {baseline_level} hours"

                except:
                    pass
                labels_new.append(l_new)
        else:
            n_obs = data.query(f"month == '2020-02-01'").dropna(subset=[group]).shape[0]
            for l in labels_old:
                if label_rename_dict and l in label_rename_dict:
                    l_new = label_rename_dict[l]
                else:
                    l_new = l
                try:

                    share = (
                        data.query(f"month == '2020-02-01' and {group} == '{l}'")[
                            col
                        ].count()
                        / n_obs
                    ).round(2)
                    if german:
                        l_new += f"; Anteil: {int(share * 100)}%"
                    else:
                        l_new += f"; share: {int(share * 100)}%"

                except:
                    pass
                labels_new.append(l_new)

        if legend_title:
            # Remove title of legend
            labels_new = [legend_title] + labels_new
        else:
            handles, labels_new = handles, labels_new

        # Put a legend below current axis
        ax.legend(
            handles=handles,
            labels=labels_new,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.15),
            fancybox=True,
            shadow=False,
            ncol=1,
            fontsize="large",
        )
    fig.tight_layout()
    if path:
        full_path = ppj("OUT_FIGURES", "time-variation", path)
        fig.savefig(full_path + ".pdf")
        fig.savefig(full_path + ".png")
        fig.savefig(full_path + ".svg")
    plt.close()

    # Also generate corresponding table
    generate_table_for_time_varying_plot(
        data, group, style, path, [col], label_rename_dict
    )

    return fig


def unemployment_figures(
    data,
    var,
    var_label,
    var_file_name,
    spec_name,
    group,
    label_rename_dict,
    german,
    legend_title,
    ylim_change=None,
):
    time_varying_plot(
        data,
        group,
        f"unempl/{var_file_name}-over-time-by-{spec_name}",
        col=var,
        ylabel=f"{var_label}",
        ci=95,
        label_rename_dict=label_rename_dict,
        german=german,
        legend_title=legend_title,
        ylim=ylim_change,
    )
    if group:
        # Adjust unemployment such that all lines start at 0
        # ToDo: This breaks categorical dtype of group
        data = data.set_index([group, "personal_id"])
        data[f"{var}_adj"] = (
            data[var] - data.query("month == '2020-02-01'").groupby(group)[var].mean()
        )
        data = data.swaplevel().reset_index(0).reset_index()

        # Change unemployment rate
        time_varying_plot(
            data,
            group,
            f"unempl/change-{var_file_name}-over-time-by-{spec_name}",
            col=f"{var}_adj",
            baseline_col=var,
            ylabel=f"change in {var_label}",
            label_rename_dict=label_rename_dict,
            ci=None,
            german=german,
            legend_title=legend_title,
        )


def generate_basic_split_vars(
    data,
    spec_name,
    group,
    create_unempl_rate,
    label_rename_dict,
    ylim_not_working=None,
    ylim_change_hours=None,
    ylim_change_hours_home=None,
    ylim_rel_change_hours=None,
    german=False,
    legend_title=None,
):
    """
    Generate time varying plots showing:
     - out of labor force
     - change in out of labor force
     - total hours (unconditional and conditional on working)
     - home share (unconditional and conditional on working)
     - absolute change in total hours (unconditional and conditional on working)
     - relative change in total hours (unconditional and conditional on working)

    Args:
        data (pd.DataFrame): data set
        group (str): split variable (column of data)
        create_unempl_rate (boolean): should unemployment rate figures be created

    Return:
        None
    """

    if create_unempl_rate:
        # Unemployment rate
        temp = data.query("out_of_laborf == 0")
        unemployment_figures(
            temp,
            "unemployed",
            "unemployment rate",
            "unempl-rate",
            spec_name=spec_name,
            group=group,
            label_rename_dict=label_rename_dict,
            german=german,
            legend_title=legend_title,
            ylim_change=(0, None),
        )

        # Out of laborforce
        unemployment_figures(
            data,
            "out_of_laborf",
            "out of laborforce",
            "olf",
            spec_name=spec_name,
            group=group,
            label_rename_dict=label_rename_dict,
            german=german,
            legend_title=legend_title,
            ylim_change=(0, None),
        )

        # Not working
        unemployment_figures(
            data,
            "not_working",
            "not working",
            "not_working",
            spec_name=spec_name,
            group=group,
            label_rename_dict=label_rename_dict,
            german=german,
            legend_title=legend_title,
            ylim_change=ylim_not_working,
        )

    # Home share
    time_varying_plot(
        data,
        group,
        f"home-share-over-time-by-{spec_name}",
        col="home_share",
        ylabel="home office share",
        ci=95,
        label_rename_dict=label_rename_dict,
        german=german,
        legend_title=legend_title,
    )

    for uncond_ind in ["-uncond", ""]:

        temp = data.copy()
        if uncond_ind == "-uncond":
            temp = temp.query("max_hours_total >= 10").copy()

            # Calculate terciles on smaller sample
            _q = pd.qcut(temp["net_income_2y_equiv"], q=3, labels=False)
            temp["net_income_2y_equiv_q3"] = _q + 1

            for var in [
                "hours_total",
                "hours_home",
                # "home_share",
                "abs_change_hours",
                "rel_change_hours",
                "abs_change_hours_home",
            ]:
                temp[var] = temp[f"{var}_uncond"]
            temp["hours_baseline"] = temp["hours_uncond_baseline"]

        # Total hours
        time_varying_plot(
            temp,
            group,
            f"working-hours-over-time-by-{spec_name}{uncond_ind}",
            col="hours_total",
            ylabel="hours worked",
            ci=95,
            label_rename_dict=label_rename_dict,  # ylim=(0, 40),
            german=german,
            legend_title=legend_title,
        )

        # Hours Home
        time_varying_plot(
            temp,
            group,
            f"hours-home-over-time-by-{spec_name}{uncond_ind}",
            col="hours_home",
            ylabel="hours worked",
            ci=95,
            label_rename_dict=label_rename_dict,  # ylim=(0, 40),
            german=german,
            legend_title=legend_title,
        )

        # Total hours + hours home
        id_vars = (
            ["personal_id", "month", "ones", group]
            if group
            else ["personal_id", "month", "ones"]
        )
        long_temp = pd.melt(
            temp[["hours_total", "hours_home"] + id_vars].dropna(),
            id_vars=id_vars,
            value_vars=["hours_total", "hours_home"],
            var_name="hours_type",
            value_name="hours",
        )
        time_varying_plot(
            long_temp,
            group,
            f"working-hours-incl-home-over-time-by-{spec_name}{uncond_ind}",
            col="hours",
            ylabel="working hours",
            style="hours_type",
            ci=95,
            label_rename_dict=label_rename_dict,
            german=german,
            legend_title=legend_title,
        )

        # Absolute and relative change
        for c in ["rel", "abs"]:
            temp_10 = temp.copy()
            if c == "rel":
                temp_10 = temp.query("hours_baseline >= 10").copy()
                ylim = ylim_rel_change_hours
            else:
                ylim = ylim_change_hours
            time_varying_plot(
                temp_10,
                group,
                f"{c}-change-hours-over-time-by-{spec_name}{uncond_ind}",
                col=f"{c}_change_hours",
                baseline_col="hours_total",
                ylabel=f"{c}. change in hours",
                ci=95,
                label_rename_dict=label_rename_dict,
                ylim=ylim,
                german=german,
                legend_title=legend_title,
            )

        # Absolute change home hours
        time_varying_plot(
            temp_10,
            group,
            f"abs-change-hours-home-over-time-by-{spec_name}{uncond_ind}",
            col=f"abs_change_hours_home",
            baseline_col="hours_home",
            ylabel=f"abs. change in home hours",
            ci=95,
            label_rename_dict=label_rename_dict,
            ylim=ylim_change_hours_home,
            german=german,
            legend_title=legend_title,
        )


def generate_gender_splits(data, style, group):
    """
    Generate time varying plots showing:
     - out of labor force
     - change in out of labor force
     - total hours (unconditional and conditional on working)
     - home share (unconditional and conditional on working)
     - absolute change in total hours (unconditional and conditional on working)
     - relative change in total hours (unconditional and conditional on working)

    for splits between gender and a second split variable (style)

    Args:
        name (str): name of data set
        data (pd.DataFrame): data set
        style (str): stype (second split) variable (column of data)

    Return:
        None
    """
    time_varying_plot(
        data,
        group=group,
        path=f"gender-splits/working-hours-over-time-by-{spec_name}-{style}",
        style=style,
    )
    time_varying_plot(
        data,
        group=group,
        path=f"gender-splits/home-share-over-time-by-{spec_name}-{style}",
        ylabel="home office share",
        style=style,
        col="home_share",
    )
    for c in ["rel", "abs"]:

        time_varying_plot(
            data,
            group=group,
            style=style,
            path=f"gender-splits/{c}-change-hours-over-time-by-{spec_name}-{style}",
            col=f"{c}_change_hours",
            ylabel=f"{c}. change in hours",
        )


if __name__ == "__main__":
    spec_name = sys.argv[1]

    # Read data
    df = pd.read_parquet(ppj("OUT_DATA", "work-childcare-long.parquet"))
    df = df.reset_index()
    df["month"] = df["month"].replace(
        {
            pd.to_datetime("2020-03-01"): pd.to_datetime("2020-03-22"),
            pd.to_datetime("2020-04-01"): pd.to_datetime("2020-04-14"),
            pd.to_datetime("2020-05-01"): pd.to_datetime("2020-05-12"),
            pd.to_datetime("2020-06-01"): pd.to_datetime("2020-06-10"),
            pd.to_datetime("2020-09-01"): pd.to_datetime("2020-09-18"),
            pd.to_datetime("2020-12-01"): pd.to_datetime("2020-12-17"),
        }
    )
    df = df.query("month != ['2019-11-01', '2020-11-01']").query("18 <= age <= 66")
    df["ones"] = 1

    # Fix reason variable
    df["reason_cat_baseline"] = df["reason_cat_baseline"].cat.remove_categories(
        ["no reduction"]
    )
    df["applied_any_policy_05"] = pd.Categorical(df["applied_any_policy_05"])
    df["ever_affected_by_policy"] = pd.Categorical(df["ever_affected_by_policy"])

    temp = df.copy()
    specs = time_variation_groups[spec_name]
    if "query" in specs:
        temp = temp.query(specs["query"]).copy()

    # Select variables needed for plots
    vars_needed = [
        "personal_id",
        "month",
        "ones",
        "hours_total",
        "hours_home",
        "abs_change_hours",
        "rel_change_hours",
        "abs_change_hours_home",
        "hours_total_uncond",
        "hours_home_uncond",
        "abs_change_hours_uncond",
        "rel_change_hours_uncond",
        "abs_change_hours_home_uncond",
        "hours_baseline",
        "hours_uncond_baseline",
        "home_share",
        "not_working",
        "out_of_laborf",
        "unemployed",
        "not_working_baseline",
        "max_hours_total",
    ]

    generate_basic_split_vars(
        temp,
        spec_name=spec_name,
        group=specs["group"],
        create_unempl_rate=specs["create_unempl_rate"],
        label_rename_dict=specs.get("label_rename_dict"),
        ylim_not_working=specs.get("ylim_not_working"),
        ylim_change_hours=specs.get("ylim_change_hours"),
        ylim_change_hours_home=specs.get("ylim_change_hours_home"),
        ylim_rel_change_hours=specs.get("ylim_rel_change_hours"),
        german=specs.get("german"),
        legend_title=specs.get("legend_title"),
    )
