"""Contains function for plots.




"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import utilities.colors as cl


def _weight_cols(data, cols, weight_col, other_cols, by=[]):
    """Prepare data for weighted mean calculation.

    Multiply *cols* with *weight_col*, dropping missing values of *cols*,
    *weight_col*, and *other_cols*.

    Args:

        data: DataFrame with data to be weighted.
        cols: Columns that are to be weighted
        weight_col: The column containing the weights
        other_cols: Other columns to be retained, will be considered when
                   dropping missing values
        by: List of variables for which the mean weight should be normalized

    Returns:

        out: DataFrame with cols and other_cols, where cols are weighted
             versions of their counterparts in *data*.

    """
    other_cols = [] if other_cols is None else other_cols

    if by == []:
        d = data.dropna(subset=cols + [weight_col] + other_cols)
        norm = d[weight_col].sum()

        out = d[cols].multiply(d[weight_col], axis="index") / norm * len(d)

    else:
        d = data.dropna(subset=cols + [weight_col] + other_cols + by)
        out = d[cols].multiply(d[weight_col], axis="index")
        out[by + [weight_col]] = d[by + [weight_col]]

        # Iterate over unique values of by variables and normalize in each group
        chunks_by_by = []
        for row in out.reset_index()[by].drop_duplicates().dropna().iterrows():
            temp = out.copy()

            # Select a chunk
            for by_var in by:
                temp = temp.loc[temp[by_var] == row[1][by_var]]

            # Normalize
            norm = temp[weight_col].sum() / len(temp[weight_col])
            temp[cols] = temp[cols] / norm
            chunks_by_by.append(temp)

        out = pd.concat(chunks_by_by)

    out[other_cols] = d[other_cols]
    return out[cols + other_cols + by].sort_index()


def weighted_means_by(cols, data, weight_col, dropna=True, by=None):
    """Calculates weighted hour means by by.

    Args:
        cols (list): list of columns to calculate mean of.
        data (pd.DataFrame):
            should contain the columns "workplace_h_before", "home_h_before",
            "workplace_h_after", "home_h_after"
        weight_col (str): column which contains the weights
        dropna (boolean): if missings in cols should be dropped for all observations
        by (list): list of columns for grouping

    Return:
        pd.DataFrame:
            means
        and the by columns with its respective values

    """
    if by is None:
        d = _weight_cols(
            data=data, cols=cols, weight_col=weight_col, other_cols=[], by=[]
        )
        means = d.mean()
        # means.name = cols[0]
        sd = d.std() / np.sqrt(d.count())
        # sd.name = "se_" + cols[0]
        means["N"] = d.shape[0]
        colnames = ["se_" + c for c in cols]
        sd.index = colnames
        out = pd.concat([means, sd], axis=0)

    else:
        if not dropna:
            if weight_col == "ones":
                d = data[cols + by]
            else:
                ValueError("weighting requires dropna=True")
        else:
            d = _weight_cols(
                data=data, cols=cols, weight_col=weight_col, other_cols=[], by=by
            )
        means = d.groupby(by).mean()
        sd = d.groupby(by).std() / np.sqrt(d.groupby(by).count() - 1)
        means["N"] = d.groupby(by).count().iloc[:, 0]

        colnames = ["se_" + c for c in cols]
        sd.columns = colnames

        out = pd.concat([means, sd], axis=1)

    return out


def weighted_hour_means_by(
    data, weight_col, by, name_before="before", name_after="after"
):
    """Calculates weighted hour means by by.

    Args:
        data (pd.DataFrame):
            should contain the columns "workplace_h_before", "home_h_before",
            "workplace_h_after", "home_h_after"
        weight_col (str): column which contains the weights
        by (list): list of columns for grouping
        name_before (str): name to use for before corona
        name_after (str): name to use for after corona

    Return:
        pd.DataFrame: output data set contains columns:

            time (str): name_before, name_after
            workplace (float): hours worked at the workplace
            home (float): hours worked at home

        and the by columns with its respective values

    """
    # Calculate weighted means by by
    before = weighted_means_by(
        ["workplace_h_before", "home_h_before", "work_h_before", "home_share_before"],
        data,
        weight_col,
        by,
    ).reset_index()
    after = weighted_means_by(
        ["workplace_h_after", "home_h_after", "work_h_before", "home_share_before"],
        data,
        weight_col,
        by,
    ).reset_index()

    # Generate output data set
    before["time"] = name_before
    before.rename(
        columns={
            "workplace_h_before": "workplace",
            "home_h_before": "home",
            "se_workplace_h_before": "se_workplace",
            "se_home_h_before": "se_home",
            "work_h_before": "total",
            "home_share_before": "home share",
            "se_work_h_before": "se_total",
            "se_home_share_before": "se_home share",
        },
        inplace=True,
    )

    after["time"] = name_after
    after.rename(
        columns={
            "workplace_h_after": "workplace",
            "home_h_after": "home",
            "se_workplace_h_after": "se_workplace",
            "se_home_h_after": "se_home",
        },
        inplace=True,
    )

    out = before.append(after, ignore_index=True)

    out["total"] = out["workplace"] + out["home"]
    out["home share"] = (
        np.round((out["home"] / (out["home"] + out["workplace"])) * 100, 2)
    ).astype(str) + "%"

    return out[
        ["time"]
        + by
        + ["workplace", "home", "se_workplace", "se_home", "total", "home share", "N"]
    ]


def rel_change(plot_df, group, name_after):
    rel = plot_df.copy()
    rel.sort_values(group + ["time"], inplace=True)
    cols = ["workplace", "home", "total"]
    rel[cols] = np.round(rel[cols].shift(-1) - rel[cols], 2)
    rel["total (%)"] = (
        np.round(rel["total"] / plot_df["total"] * 100, 2).astype(str) + "%"
    )
    rel = rel[rel.time != name_after]
    rel.index = rel[group].copy()
    rel.drop(["time", "home_share"] + group, inplace=True, axis=1)

    return rel


def stacked_bar_plot_home_office(
    plot_df,
    group1,
    group2,
    ax,
    path,
    ylabel="weekly working hours",
    loc="best",
    colors=cl.get_colors("blue", 2),
    fontsize="large",
    width=0.8,
    var1="workplace",
    var2="home",
):
    plot_sorted = plot_df.sort_values([group1, group2])
    menMeans = plot_sorted[var1].values
    womenMeans = plot_sorted[var2].values

    group1_levels = list(plot_df[group1].unique())
    group2_levels = list(plot_df[group2].unique())

    # Create position of bar plot
    no_group1_levels = len(group1_levels)
    no_group2_levels = len(group2_levels)

    ind = []
    x_lab = []
    count = 0

    for _i in np.arange(no_group1_levels):
        ind = ind + list(np.arange(start=count, stop=count + no_group2_levels))
        count = count + no_group2_levels + 1
        x_lab = x_lab + group2_levels

    # Create bars
    p1 = ax.bar(ind, menMeans, width, color=colors[0])
    p2 = ax.bar(ind, womenMeans, width, bottom=menMeans, color=colors[1])

    # General layout
    ax.grid(axis="x")
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    # Y-axis
    plt.ylabel(ylabel, fontsize=fontsize)
    plt.yticks(fontsize=fontsize)

    # X-axis
    additional_xticks = []
    additional_xlabels = [f"\n\n{i}" for i in group1_levels]

    for i in np.arange(no_group1_levels):
        to_append = (no_group2_levels + 1) / 2 + i * (no_group2_levels + 1) - 1
        additional_xticks.append(to_append)

    ind_lab = ind + additional_xticks
    x_lab = x_lab + additional_xlabels

    plt.xticks(ind_lab, x_lab, fontsize=fontsize)
    plt.legend((p2[0], p1[0]), (var2, var1), loc=loc, fontsize=fontsize)
    plt.tight_layout()
    plt.savefig(path + ".png", dpi=300)
    plt.savefig(path + ".pdf")


def stacked_bar_plot_crosstab(
    cr,
    ax,
    xlabel,
    path,
    ylabel="share of working (%)",
    width=0.8,
    fontsize="large",
    loc="best",
    reverse=False,
    colors=None,
):
    if not colors:
        no_cat = len(cr.columns)
        clr = [i for i in cl.get_colors("ordered", no_cat)]
        colors = sns.color_palette(clr)
    if reverse:
        clr.reverse()
    cr.plot.bar(stacked=True, width=width, ax=ax, color=colors)
    ax.grid(axis="x")
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    plt.xticks(rotation=0, fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.xlabel(xlabel, fontsize=fontsize)
    plt.ylabel(ylabel, fontsize=fontsize)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc=loc, fontsize=fontsize)
    plt.tight_layout()
    plt.savefig(path + ".png", dpi=300)
    plt.savefig(path + ".pdf")


def stacked_bar_plot_multiple_groups(
    plot_df,
    by,
    fig,
    axes,
    path,
    ind_xticks,
    ind_xlabels,
    xlab,
    ylabel="working hours (per week)",
    width=0.8,
    colors=cl.get_colors("blue", 2),
    loc=(0.5, 0.8),
    fontsize="large",
    labelsize=16,
):

    bei = list(plot_df[by].unique())
    plt.ylabel(ylabel)
    plt.setp(axes, xticks=ind_xlabels, xticklabels=xlab)
    for group, ax in zip(bei, axes):
        plot_df1 = plot_df[plot_df[by] == group][["workplace", "home", by]].copy()

        menMeans = plot_df1["workplace"].values
        womenMeans = plot_df1["home"].values

        p1 = ax.bar(ind_xticks, menMeans, width, color=colors[0])
        p2 = ax.bar(ind_xticks, womenMeans, width, bottom=menMeans, color=colors[1])

        ax.label_outer()
        ax.grid(axis="x")
        ax.tick_params(axis="both", labelsize=labelsize)
        ax.spines["left"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        ax.set_title(f"{group}", fontdict={"fontsize": fontsize})

    fig.legend((p2[0], p1[0]), ("home", "workplace"), fontsize=fontsize, loc=loc)
    fig.tight_layout()
    plt.savefig(path + ".png", dpi=300)
    plt.savefig(path + ".pdf")


def changes_bar_plot(
    rel,
    ax,
    path,
    fontsize="large",
    colors=sns.color_palette(cl.get_colors("categorical", 3)),
):
    rel.plot.bar(ax=ax, color=colors)
    ax.grid(axis="x")
    ax.grid(axis="y")
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    plt.axhline(y=0, color="lightgrey")
    plt.xticks(rotation=0, fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.legend(fontsize=fontsize)
    plt.tight_layout()
    plt.savefig(path + ".png", dpi=300)
    plt.savefig(path + ".pdf")
