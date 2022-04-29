from functools import reduce

import numpy as np
import pandas as pd
from statsmodels.compat.python import lrange
from statsmodels.iolib.summary2 import _col_info
from statsmodels.iolib.summary2 import _col_params
from statsmodels.iolib.summary2 import _make_unique
from statsmodels.iolib.summary2 import Summary

from project_specific_analyses.analysis.plot_functions import _weight_cols


def calc_means_and_se(df, by, cols):
    mean = df.groupby(by)[cols].mean()
    std = df.groupby(by)[cols].std()
    count = df.groupby(by)[cols].count()
    se = std / np.sqrt(count - 1)
    if "month" in mean.index.names:
        mean.index = mean.index.set_levels(
            [mean.index.levels[0].astype(str), mean.index.levels[1].strftime("%Y-%m")]
        )
        se.index = se.index.set_levels(
            [std.index.levels[0].astype(str), std.index.levels[1].strftime("%Y-%m")]
        )
        count.index = count.index.set_levels(
            [count.index.levels[0].astype(str), count.index.levels[1].strftime("%Y-%m")]
        )
    return mean, se, count


def add_diff_to_mean_se(mean, se, index1, index2):

    assert len(index1) == len(
        index2
    ), "index1 and index2 needs to be of the same length"
    assert len(index1) == 2, "only implemented for index length of 2"

    new_index = [""] * len(index1)
    if index1[0] == index2[0]:
        new_index = (index1[0], f"diff-{index1[1]}-{index2[1]}")
    elif index1[1] == index2[1]:
        new_index = (f"diff-{index1[0]}-{index2[0]}", index1[1])
    else:
        raise ValueError("one of the index levels need to be the same")

    mean.loc[new_index, :] = mean.loc[index1] - mean.loc[index2]
    se.loc[new_index, :] = np.sqrt((se.loc[index1] ** 2) + (se.loc[index2] ** 2))
    return mean, se


def means_and_stds(df, name_before, name_after):
    _df = df[
        [
            "workplace_h_before",
            "home_h_before",
            "workplace_h_after",
            "home_h_after",
            "work_h_before",
            "work_h_after",
        ]
    ].dropna()

    x = _df.mean().to_frame(name="hours").round(1)
    x["stat"] = "mean"
    y = (_df.std() / _df.count() ** 0.5).to_frame(name="hours")
    y["stat"] = "std"
    x = x.append(y).reset_index()
    x["time"] = name_before
    x.loc[x["index"].apply(lambda y: y.endswith("after")), "time"] = name_after
    x["loc"] = "workplace"
    x.loc[x["index"].apply(lambda y: y.startswith("home")), "loc"] = "home"
    x.loc[x["index"].apply(lambda y: y.startswith("work_")), "loc"] = "total"
    x = x[["time", "stat", "loc", "hours"]].pivot_table(
        index=["time", "stat"], columns="loc", values="hours"
    )
    for col in x.columns:
        for time in "before Covid-19", "late March":
            x.loc[(time, "std"), col] = f"({x.loc[(time, 'std'), col]:3.2f})"

    x = x.reset_index().set_index("time")
    x.columns.name = ""
    x.index.name = ""
    index = x.index.to_list()
    index[1] = ""
    index[3] = ""
    x.index = index

    return x[["workplace", "home", "total"]].round(2)


def weighted_rel_freq(column, df, weight_col):
    d = _weight_cols(df, [column], weight_col=weight_col, other_cols=[])

    norm = d[weight_col].sum()
    d[weight_col] = d[weight_col] / norm * d[column].count()

    n = d[column].count()
    return d.groupby([column])[weight_col].sum() / n


def create_means_output_table(out, cols, out_path, rounding=None):
    out = out.copy()
    if rounding is None:
        rounding = {c: 2 for c in cols}
    out.loc["N"] = out.loc["N"].apply(lambda x: f"{x:.0f}").replace({"0": ""})

    # Change order of rows
    index = []
    for c in cols:
        index.append(c)
        index.append("se_" + c)
        round_num = rounding[c]
        out.loc["se_" + c] = out.loc["se_" + c].apply(lambda x: f"({x:.{round_num}f})")
        out.loc[c] = out.loc[c].apply(lambda x: f"{x:.{round_num}f}")
    index.append("N")
    out = out.reindex(index)
    final_index = ["" if i.startswith("se_") else i for i in index]
    out.index = final_index
    if out_path:
        my_table = open(out_path, "w")
        my_table.write(out.to_latex(escape=False, column_format="llrrrrrrrr"))
        my_table.close()
    return out


def weighted_cross_tab(A, B, weight_col, normalize, df):
    d = df.dropna(subset=[A, B, weight_col]).copy()
    norm = d[weight_col].sum()
    d[weight_col] = d[weight_col] / norm * d[A].count()
    return pd.crosstab(d[A], d[B], d[weight_col], aggfunc=sum, normalize=normalize)


def summary_col(
    results,
    float_format="%.4f",
    model_names=(),
    stars=False,
    info_dict=None,
    regressor_order=(),
    drop_omitted=False,
):
    """
    Summarize multiple results instances side-by-side (coefs and SEs)

    Parameters
    ----------
    results : statsmodels results instance or list of result instances
    float_format : str, optional
        float format for coefficients and standard errors
        Default : '%.4f'
    model_names : list[str], optional
        Must have same length as the number of results. If the names are not
        unique, a roman number will be appended to all model names
    stars : bool
        print significance stars
    info_dict : dict
        dict of functions to be applied to results instances to retrieve
        model info. To use specific information for different models, add a
        (nested) info_dict with model name as the key.
        Example: `info_dict = {"N":lambda x:(x.nobs), "R2": ..., "OLS":{
        "R2":...}}` would only show `R2` for OLS regression models, but
        additionally `N` for all other results.
        Default : None (use the info_dict specified in
        result.default_model_infos, if this property exists)
    regressor_order : list[str], optional
        list of names of the regressors in the desired order. All regressors
        not specified will be appended to the end of the list.
    drop_omitted : bool, optional
        Includes regressors that are not specified in regressor_order. If
        False, regressors not specified will be appended to end of the list.
        If True, only regressors in regressor_order will be included.
    """

    if not isinstance(results, list):
        results = [results]

    # Allow for different float format for different results
    if isinstance(float_format, list):
        cols = [
            _col_params(x, stars=stars, float_format=float_format[i])
            for i, x in enumerate(results)
        ]
    else:
        cols = [_col_params(x, stars=stars, float_format=float_format) for x in results]

    # Unique column names (pandas has problems merging otherwise)
    if model_names:
        colnames = _make_unique(model_names)
    else:
        colnames = _make_unique([x.columns[0] for x in cols])
    for i in range(len(cols)):
        cols[i].columns = [colnames[i]]

    def merg(x, y):
        return x.merge(y, how="outer", right_index=True, left_index=True)

    summ = reduce(merg, cols)
    if regressor_order:
        varnames = summ.index.get_level_values(0).tolist()
        ordered = [x for x in regressor_order if x in varnames]
        unordered = [x for x in varnames if x not in regressor_order + [""]]
        order = ordered
        if drop_omitted and len(unordered) > 0:
            print("the following columns have been dropped", np.unique(unordered))
        else:
            order += list(np.unique(unordered))

        def f(idx):
            return sum([[x + "coef", x + "stde"] for x in idx], [])

        summ.index = f(pd.unique(varnames))
        summ = summ.reindex(f(order))

        summ.index = [x[:-4] for x in summ.index]

    idx = pd.Series(lrange(summ.shape[0])) % 2 == 1
    summ.index = np.where(idx, "", summ.index.get_level_values(0))

    # add infos about the models.
    if info_dict:
        cols = [
            _col_info(x, info_dict.get(x.model.__class__.__name__, info_dict))
            for x in results
        ]
    else:
        cols = [_col_info(x, getattr(x, "default_model_infos", None)) for x in results]
    # use unique column names, otherwise the merge will not succeed
    for df, name in zip(cols, _make_unique([df.columns[0] for df in cols])):
        df.columns = [name]

    info = reduce(merg, cols)
    dat = pd.DataFrame(np.vstack([summ, info]))  # pd.concat better, but error
    dat.columns = summ.columns
    dat.index = pd.Index(summ.index.tolist() + info.index.tolist())
    summ = dat

    summ = summ.fillna("")

    smry = Summary()
    smry._merge_latex = True
    smry.add_df(summ, header=True, align="l")
    smry.add_text("Standard errors in parentheses.")
    if stars:
        smry.add_text("* p<.1, ** p<.05, ***p<.01")

    return smry


def write_table(
    tab,
    path,
    column_format,
    escape=False,
    multicolumn_format="c",
    multirow=True,
    full_width=False,
    header=True,
    longtable=False,
    caption=None,
    label=None,
    midrules_body_count=None,
):

    # Make sure index is not cut short
    with pd.option_context("max_colwidth", 1000):
        latex = tab.to_latex(
            escape=escape,
            column_format=column_format,
            multicolumn_format=multicolumn_format,
            multirow=multirow,
            header=header,
            longtable=longtable,
            caption=caption,
            label=label,
        )
    if full_width:
        latex = latex.replace(r"\begin{tabular}{l", r"\begin{tabularx}{\textwidth}{X")
        latex = latex.replace(r"\end{tabular}", r"\end{tabularx}")

    # Add non-continuous mid-lines for multiindex-columns
    if len(tab.columns.names) > 1:
        latex = latex.replace(r"{l}", r"{c}")

        offset = len(tab.index.names)
        midrule_str = ""
        for i, col in enumerate(tab.columns.levels[0]):
            indices = np.nonzero(np.array(tab.columns.codes[0]) == i)[0]
            hstart = 1 + offset + indices[0]
            hend = 1 + offset + indices[-1]
            midrule_str += rf"\cmidrule(lr){{{hstart}-{hend}}} "

        # Ensure that headers don't get colored by row highlighting
        midrule_str += r"\rowcolor{white}"
        latex_lines = latex.splitlines()
        if longtable:
            latex_lines.insert(4, midrule_str)
        else:
            latex_lines.insert(3, midrule_str)
        latex = "\n".join(latex_lines)
    if len(tab.columns.names) > 2:
        midrule_str = ""
        for i, col in enumerate(tab.columns.levels[1]):
            indices = np.nonzero(np.array(tab.columns.codes[1]) == i)[0]
            hstart = 1 + offset + indices[0]
            hend = 1 + offset + indices[-1]
            midrule_str += rf"\cmidrule(lr){{{hstart}-{hend}}} "

        # Ensure that headers don't get colored by row highlighting
        midrule_str += r"\rowcolor{white}"
        latex_lines = latex.splitlines()
        if longtable:
            latex_lines.insert(6, midrule_str)
        else:
            latex_lines.insert(5, midrule_str)
        latex = "\n".join(latex_lines)
        latex = "\n".join(latex_lines)
    # Add midrules
    if midrules_body_count:
        assert len(midrules_body_count) == 3

        latex_list_new = [
            l + "\n\\midrule"
            if ((i - midrules_body_count[1]) % midrules_body_count[2] == 0)
            and i > midrules_body_count[0]
            else l
            for i, l in enumerate(latex.splitlines())
        ]
        latex = "\n".join(latex_list_new)
    if path:
        with open(path, "w") as my_table:
            my_table.write(latex)
    return latex


def regression_table_wrapper(
    models,
    regressor_order=None,
    reg_to_table=None,
    depvar_to_table=None,
    prec=2,
    drop_omitted=False,
    info_dict=None,
    export_csv=None,
):
    """
    A wrapper for statsmodels summary_cols
    """
    # Export coefficients as csv
    if export_csv:
        out = pd.concat(
            {
                f"({i + 1})": pd.DataFrame(
                    {"params": models[i].params, "se": models[i].bse}
                )
                for i in range(len(models))
            },
            axis=1,
        )
        out.to_csv(export_csv, sep=";")

    if not info_dict:
        info_dict = {
            "N": lambda x: f"{int(x.nobs):d}",
            "$R^2$": lambda x: f"{x.rsquared:.3f}",
        }
    if isinstance(prec, list):
        assert len(prec) == len(
            models
        ), f"{len(models)} models, but prec of length {len(prec)}"
        float_format = [f"%.{p}f" for p in prec]
    else:
        float_format = f"%.{prec}f"
    basic_table = summary_col(
        results=models,
        regressor_order=regressor_order,
        float_format=float_format,
        stars=True,
        info_dict=info_dict,
        drop_omitted=drop_omitted,
    ).tables[0]

    # fix duplicated R-squared
    if "R-squared" in basic_table.index:
        pos_r_squared = basic_table.index.get_loc("R-squared")
        basic_table = pd.concat(
            [basic_table.iloc[:pos_r_squared], basic_table.iloc[pos_r_squared + 2 :]]
        )

    if reg_to_table:
        basic_table.rename(index=reg_to_table, inplace=True)
    if depvar_to_table:
        basic_table.rename(columns=depvar_to_table, inplace=True)
    return basic_table
