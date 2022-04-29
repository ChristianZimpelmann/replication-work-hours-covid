"""Produce regression tables for working hours regressions.


"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.analysis.table_functions import regression_table_wrapper
from project_specific_analyses.analysis.table_functions import write_table
from project_specific_analyses.library.plot_labels import column_to_table
from project_specific_analyses.library.plot_labels import index_to_table
from project_specific_analyses.library.plot_labels import regressor_order

personal_char = [
    "edu",
    "gross_income_groups",
    "age_groups",
    "female",
    "work_status_spec_short_baseline",
]

personal_char_general = [
    "edu",
    "gross_income_groups",
    "female",
]

job_char = [
    "essential_worker_w2",
    "work_perc_home",
]

job_char_unemployed = [
    "essential_worker_w2",
    "work_perc_home",
]

reason_controls = [
    "reason_closure_baseline",
    "reason_less_business_baseline",
    "reason_care_baseline",
]
reason_controls_long = [
    "reason_closure_baseline",
    "reason_less_business_baseline",
    "reason_care_baseline",
    "reason_unrel_corona_baseline",
    "reason_fear_infection_baseline",
]


def formula_string_from_list(var_list, interaction_job_char="interact"):
    replacements = {
        "work_status_spec_baseline": "C(work_status_spec_baseline, Treatment('full time'))",
        "work_status_spec_short_baseline": "C(work_status_spec_short_baseline, Treatment('full time'))",
        "net_income_2y_equiv_q": "C(net_income_2y_equiv_q)",
        "net_income_2y_equiv_q3": "C(net_income_2y_equiv_q3)",
    }
    var_list_adj = [replacements.get(x, x) for x in var_list]
    if (
        "essential_worker_w2" in var_list_adj
        and "work_perc_home" in var_list_adj
        and interaction_job_char
    ):
        if interaction_job_char == "interact":
            var_list_adj.append("essential_worker_w2:work_perc_home")
        elif interaction_job_char == "full":
            var_list_adj = [c for c in var_list_adj if c != "work_perc_home"]
            var_list_adj.append("I(essential_worker_w2 == 1):work_perc_home")
        else:
            raise ValueError(
                "interaction_job_char expected as 'interact', 'full', or None"
            )
    print(var_list_adj)

    return "+".join(var_list_adj)


def make_one_reg(
    depvar, rhs_formula, data, cov_type, models, cov_kwds=None, mean_depvar=None
):
    mod = smf.ols(
        f"{depvar} ~ {rhs_formula}",
        data=data,
    ).fit(cov_type=cov_type, cov_kwds=cov_kwds)
    models.append(mod)
    if mean_depvar is not None:
        mean_depvar.append(data[depvar].mean())
        return models, mean_depvar
    else:
        return models


def make_one_reg_het(
    models, data, depvar, indepvars, month_str, interaction_job_char="interact"
):
    temp = data.dropna(subset=[depvar] + indepvars)
    var_string = formula_string_from_list(indepvars, interaction_job_char)

    models, make_one_reg(
        depvar,
        f" 0 + ({month_str}) + ({month_str}) : (" + var_string + ")",
        temp,
        cov_type="cluster",
        cov_kwds={"groups": temp["personal_id"]},
        models=models,
    )
    # print(f" 0 + ({month_str}) + ({month_str}) : (" + var_string + ")")
    return models


def create_effect_working_hours_reg(df_full, hh_income, prec):
    data = df_full.query("18 <= age <= 66 and hours_baseline >= 10").copy()

    var_string = formula_string_from_list(personal_char)

    # Adjust some variables
    data["concern_4w_job"] = data["concern_4w_unemp"].fillna(data["concern_4w_company"])
    data["concern_4w_job"] = (
        data["concern_4w_job"]
        .replace({"1 not worried at all": 1, "5 very worried": 5})
        .astype(float)
    )
    data["p_2m_employee_lost"] = data["p_2m_employee_lost"].fillna(
        data["p_2m_employee_new_job"] + data["p_2m_employee_unemployed"]
    )
    data["p_2m_lost_job"] = data["p_2m_employee_lost"].fillna(
        data["p_3m_selfempl_shutdown"]
    )
    data["p_year_employee_lost"] = (
        data["p_year_employee_new_job"] + data["p_year_employee_unemployed"]
    )
    data["p_year_lost_job"] = data["p_year_employee_lost"].fillna(
        data["p_year_selfempl_shutdown"]
    )
    data["p_year_unempl"] = data["p_year_employee_unemployed"].fillna(
        data["p_year_selfempl_shutdown"]
    )
    data["p_2m_unempl"] = data["p_2m_employee_unemployed"].fillna(
        data["p_3m_selfempl_shutdown"]
    )
    data["rel_change_hours_uncond_10"] = data["rel_change_hours_uncond"] / 10
    data["concern_4w_job"] = (
        data["concern_4w_job"] - data["concern_4w_job"].mean()
    ) / data["concern_4w_job"].std()
    data["not_working_after_may_perc"] = data["not_working_after_may"] * 100

    # Add household income data
    data = data.join(hh_income["change_net_income_hh"])

    # Run regressions
    models = []
    mean_depvar = []
    models, mean_depvar = make_one_reg(
        "concern_4w_job",
        f"abs_change_hours_uncond_03 + {var_string}",
        data.query("month == '2020-03-01'"),
        cov_type="HC1",
        models=models,
        mean_depvar=mean_depvar,
    )
    models, mean_depvar = make_one_reg(
        "p_2m_lost_job",
        f"abs_change_hours_uncond_03 + {var_string}",
        data.query("month == '2020-03-01'"),
        cov_type="HC1",
        models=models,
        mean_depvar=mean_depvar,
    )
    models, mean_depvar = make_one_reg(
        "p_2m_lost_job",
        f"abs_change_hours_uncond_03 + {var_string}",
        data.query("month == '2020-03-01' and reason_lost_job != 1"),
        cov_type="HC1",
        models=models,
        mean_depvar=mean_depvar,
    )

    tab = regression_table_wrapper(
        models,
        regressor_order=regressor_order,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=prec,
        drop_omitted=True,
    )
    tab.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab.columns)
        ]
    )
    tab = tab.iloc[2:, :]
    tab = tab.rename(
        columns={
            "p_2m_lost_job IIII": "expected job loss prob. (May)",
            "p_2m_lost_job IIIII": "expected job loss prob. (September)",
            "p_2m_unempl I": "expected unempl. prob. (May)",
            "p_2m_unempl II": "expected unempl. prob. (September)",
        }
    )
    tab.loc["mean dependent variable"] = np.round(mean_depvar, prec)
    tab.loc["Subset: didn't loose job"] = ["No"] * 2 + ["Yes"] * 1

    file_name = f"effect_working_hours"
    write_table(
        tab,
        ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "p{1.5cm}" * (len(tab.columns) - 2) + "p{2cm}" * 2,
        multicolumn_format="c",
        multirow=True,
        longtable=False,
    )
    file_name = f"effect_working_hours_short"
    tab.loc["Demographic controls"] = ["Yes"] * 3  # + ["No"] * 2
    write_table(
        pd.concat([tab.iloc[:4], tab.iloc[-5:]]),
        ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "p{1.5cm}" * (len(tab.columns)),
        multicolumn_format="c",
        multirow=True,
        longtable=False,
    )


def create_hh_income_table(
    depvar,
    data,
    file_name,
    prec=2,
    full_month_str="March_April + May + June + September + December",
):
    controls = ["hours_uncond_baseline", "net_income_2y_equiv_q3"]
    data = data.copy().dropna(subset=[depvar] + controls)

    models = []
    indepvars = controls
    models = make_one_reg_het(
        models,
        data,
        depvar,
        indepvars,
        full_month_str,
    )

    tab = regression_table_wrapper(
        models,
        regressor_order=regressor_order,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=prec,
        drop_omitted=True,
    )

    tab.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab.columns)
        ]
    )
    if file_name:
        write_table(
            tab,
            ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
            column_format="l" + "r" * len(tab.columns),
            multicolumn_format="c",
            multirow=True,
            longtable=False,
            escape=False,
            midrules_body_count=(6, 5, 10),
        )
    return models


def create_long_heterogeneity_table(
    depvar,
    data,
    name=None,
    caption=None,
    prec=2,
    full_month_str="March_April + May + June + September + December",
    dynamic_month_str="May + June + September + December",
    interaction_job_char="interact",
):
    data = data.copy().dropna(
        subset=[depvar]
        + personal_char
        + job_char
        # + ["sector"]
    )

    personal_controls = personal_char
    job_controls = job_char
    models = []
    indepvars = personal_controls

    models = make_one_reg_het(
        models, data, depvar, indepvars, full_month_str, interaction_job_char
    )

    indepvars = personal_controls + job_controls
    models = make_one_reg_het(
        models, data, depvar, indepvars, full_month_str, interaction_job_char
    )

    indepvars = personal_controls + job_controls + ["sector"]
    models = make_one_reg_het(
        models, data, depvar, indepvars, full_month_str, interaction_job_char
    )

    tab = regression_table_wrapper(
        models,
        regressor_order=regressor_order,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=prec,
        drop_omitted=True,
    )

    tab.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab.columns)
        ]
    )
    if name:
        file_name = f"regression_{name}_heterogeneity"
        write_table(
            tab,
            ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
            column_format="l" + "r" * len(tab.columns),
            multicolumn_format="c",
            multirow=True,
            longtable=True,
            caption=caption,
            label=f"tab:{file_name}",
        )
    return models


def create_heterogeneity_tables(data):

    hours_models = create_long_heterogeneity_table(
        "rel_change_hours_uncond",
        data,
        "hours",
        "Hours worked by individual and job characteristics",
        2,
    )
    hours_models_month_comb = create_long_heterogeneity_table(
        "rel_change_hours_uncond",
        data,
        "hours",
        "Hours worked by individual and job characteristics",
        2,
        full_month_str="March_June + September_December",
    )
    hours_models_abs = create_long_heterogeneity_table(
        "abs_change_hours_uncond",
        data,
        "hours_abs",
        "Hours worked by individual and job characteristics",
        1,
    )

    hours_models_3 = create_long_heterogeneity_table(
        "rel_change_hours_uncond",
        data,
        "hours_3",
        "Hours worked by individual and job characteristics",
        3,
    )

    not_working_models = create_long_heterogeneity_table(
        "not_working",
        data,
        "not_working",
        "Not working by individual and job characteristics",
        3,
    )
    create_long_heterogeneity_table(
        "rel_change_hours_home_uncond",
        data,
        "hours_home",
        "Hours worked from home by individual and job characteristics",
        2,
    )
    create_long_heterogeneity_table(
        "abs_change_hours_home_uncond",
        data,
        "hours_home_abs",
        "Hours worked from home by individual and job characteristics",
        1,
    )

    # Robustness
    rob_models_tu = create_long_heterogeneity_table(
        "rel_change_hours_tu_uncond",
        data,
        None,
        "Hours worked by individual and job characteristics (alternative baseline)",
        2,
    )

    rob_models_day_off = create_long_heterogeneity_table(
        "rel_change_hours_uncond",
        data.query("not_working_unrel_corona == 0"),
        None,
        "Hours worked by individual and job characteristics (alternative baseline)",
        2,
        full_month_str="March_April + May + September + December",
        dynamic_month_str="May + September + December",
    )

    # Create short heterogeneity table
    regressor_order_short = [
        "March_April:edu[T.upper_secondary]",
        "May:edu[T.upper_secondary]",
        "June:edu[T.upper_secondary]",
        "September:edu[T.upper_secondary]",
        "December:edu[T.upper_secondary]",
        "March_April:edu[T.tertiary]",
        "May:edu[T.tertiary]",
        "June:edu[T.tertiary]",
        "September:edu[T.tertiary]",
        "December:edu[T.tertiary]",
        "March_April:C(net_income_2y_equiv_q3)[T.2.0]",
        "May:C(net_income_2y_equiv_q3)[T.2.0]",
        "June:C(net_income_2y_equiv_q3)[T.2.0]",
        "September:C(net_income_2y_equiv_q3)[T.2.0]",
        "December:C(net_income_2y_equiv_q3)[T.2.0]",
        "March_April:C(net_income_2y_equiv_q3)[T.3.0]",
        "May:C(net_income_2y_equiv_q3)[T.3.0]",
        "June:C(net_income_2y_equiv_q3)[T.3.0]",
        "September:C(net_income_2y_equiv_q3)[T.3.0]",
        "December:C(net_income_2y_equiv_q3)[T.3.0]",
        "March_April:gross_income_groups[T.bet. 2500 and 3500]",
        "May:gross_income_groups[T.bet. 2500 and 3500]",
        "June:gross_income_groups[T.bet. 2500 and 3500]",
        "September:gross_income_groups[T.bet. 2500 and 3500]",
        "December:gross_income_groups[T.bet. 2500 and 3500]",
        "March_April:gross_income_groups[T.above 3500]",
        "May:gross_income_groups[T.above 3500]",
        "June:gross_income_groups[T.above 3500]",
        "September:gross_income_groups[T.above 3500]",
        "December:gross_income_groups[T.above 3500]",
        "March_April:essential_worker_w2",
        "May:essential_worker_w2",
        "June:essential_worker_w2",
        "September:essential_worker_w2",
        "December:essential_worker_w2",
        "March_April:work_perc_home",
        "May:work_perc_home",
        "June:work_perc_home",
        "September:work_perc_home",
        "December:work_perc_home",
        "essential_worker_w2:work_perc_home",
        "March_April:essential_worker_w2:work_perc_home",
        "May:essential_worker_w2:work_perc_home",
        "June:essential_worker_w2:work_perc_home",
        "September:essential_worker_w2:work_perc_home",
        "December:essential_worker_w2:work_perc_home",
    ]
    file_name = "regression_hours_heterogeneity_short"
    tab_short = regression_table_wrapper(
        hours_models,
        regressor_order=regressor_order_short,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=2,
        drop_omitted=True,
        export_csv=ppj("OUT_TABLES", "work_hours", f"{file_name}.csv"),
    )
    tab_short = tab_short.iloc[:, 0:3]
    tab_short.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab_short.columns)
        ]
    )
    tab_short.loc["demographic controls"] = ["No"] * 0 + ["Yes"] * 3
    tab_short.loc["month $\times$ sector FE"] = ["No"] * 2 + ["Yes"] * 1

    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=False,
        escape=False,
        midrules_body_count=(7, 5, 10),
    )
    # longtable
    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}_longtable.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=True,
        escape=False,
        midrules_body_count=(14, 4, 10),
        caption="Hours worked by individual and job characteristics",
        label="tab:regression_hours_heterogeneity_short",
    )

    # Create short heterogeneity table months combined
    regressor_order_short_month_comb = [
        "March_June:edu[T.upper_secondary]",
        "September_December:edu[T.upper_secondary]",
        "March_June:edu[T.tertiary]",
        "September_December:edu[T.tertiary]",
        "March_June:C(net_income_2y_equiv_q3)[T.2.0]",
        "September_December:C(net_income_2y_equiv_q3)[T.2.0]",
        "March_June:C(net_income_2y_equiv_q3)[T.3.0]",
        "September_December:C(net_income_2y_equiv_q3)[T.3.0]",
        "March_June:gross_income_groups[T.bet. 2500 and 3500]",
        "September_December:gross_income_groups[T.bet. 2500 and 3500]",
        "March_June:gross_income_groups[T.above 3500]",
        "September_December:gross_income_groups[T.above 3500]",
        "March_June:essential_worker_w2",
        "September_December:essential_worker_w2",
        "March_June:work_perc_home",
        "September_December:work_perc_home",
        "March_June:essential_worker_w2:work_perc_home",
        "September_December:essential_worker_w2:work_perc_home",
    ]
    file_name = "regression_hours_heterogeneity_short_month_comb"
    tab_short = regression_table_wrapper(
        hours_models_month_comb,
        regressor_order=regressor_order_short_month_comb,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=2,
        drop_omitted=True,
        export_csv=ppj("OUT_TABLES", "work_hours", f"{file_name}.csv"),
    )
    tab_short = tab_short.iloc[:, 0:3]
    tab_short.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab_short.columns)
        ]
    )
    tab_short.loc["demographic controls"] = ["No"] * 0 + ["Yes"] * 3
    tab_short.loc["month $\times$ sector FE"] = ["No"] * 2 + ["Yes"] * 1

    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=False,
        escape=False,
        midrules_body_count=(7, 5, 4),
    )
    regressor_order_short_month_comb = [
        "March_June:edu[T.upper_secondary]",
        "September_December:edu[T.upper_secondary]",
        "March_June:edu[T.tertiary]",
        "September_December:edu[T.tertiary]",
        "March_June:C(net_income_2y_equiv_q3)[T.2.0]",
        "September_December:C(net_income_2y_equiv_q3)[T.2.0]",
        "March_June:C(net_income_2y_equiv_q3)[T.3.0]",
        "September_December:C(net_income_2y_equiv_q3)[T.3.0]",
        "March_June:gross_income_groups[T.bet. 2500 and 3500]",
        "September_December:gross_income_groups[T.bet. 2500 and 3500]",
        "March_June:gross_income_groups[T.above 3500]",
        "September_December:gross_income_groups[T.above 3500]",
        "March_June:essential_worker_w2",
        "September_December:essential_worker_w2",
        "March_June:work_perc_home",
        "September_December:work_perc_home",
        "March_June:essential_worker_w2:work_perc_home",
        "September_December:essential_worker_w2:work_perc_home",
    ]
    file_name = "regression_hours_heterogeneity_short_month_comb_two_cols"
    tab_short = regression_table_wrapper(
        hours_models_month_comb,
        regressor_order=regressor_order_short_month_comb,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=2,
        drop_omitted=True,
        export_csv=ppj("OUT_TABLES", "work_hours", f"{file_name}.csv"),
    )
    tab_short = tab_short.iloc[:, [0, 2]]
    tab_short.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab_short.columns)
        ]
    )
    tab_short.loc["demographic controls"] = ["No"] * 0 + ["Yes"] * 2
    tab_short.loc["month $\times$ sector FE"] = ["No"] * 1 + ["Yes"] * 1

    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=False,
        escape=False,
        midrules_body_count=(7, 5, 4),
    )
    # longtable
    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}_longtable.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=True,
        escape=False,
        midrules_body_count=(15, 2, 4),
        caption="Hours worked by individual and job characteristics",
        label="tab:regression_hours_heterogeneity_short_month_comb",
    )

    # Create longer heterogeneity table
    tab_short = regression_table_wrapper(
        hours_models[0:3] + not_working_models[0:3],
        regressor_order=regressor_order,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=[
            2,
            2,
            2,
            3,
            3,
            3,
        ],
        drop_omitted=True,
    )
    tab_short.columns = pd.MultiIndex.from_tuples(
        [
            (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab_short.columns)
        ]
    )

    file_name = f"regression_hours_heterogeneity_combined"
    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=True,
        escape=False,
        midrules_body_count=(14, 4, 10),
        caption="Hours worked and not working by individual and job characteristics",
        label=f"tab:{file_name}",
    )

    # Create (short) robustness heterogeneity table
    tab_short = regression_table_wrapper(
        rob_models_day_off[0:3] + rob_models_tu[0:3],
        regressor_order=regressor_order_short,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=2,
        drop_omitted=True,
    )
    tab_short = tab_short
    tab_short.columns = pd.MultiIndex.from_tuples(
        [
            (
                j,
                "subset: no day taken off" if i <= 1 else "baseline: time use survey",
                rf"\multicolumn{{1}}{{c}}{{({i + 1})}}",
            )
            for i, j in enumerate(tab_short.columns)
        ]
    )

    tab_short.loc["demographic controls"] = ["No"] * 0 + ["Yes"] * 6
    tab_short.loc["month $\times$ sector FE"] = ["No", "No", "Yes"] * 2

    file_name = f"regression_hours_heterogeneity_short_robustness"
    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=False,
        escape=False,
        midrules_body_count=(7, 7, 10),
    )

    hours_models_full_interact = create_long_heterogeneity_table(
        "rel_change_hours_uncond",
        data,
        "hours",
        "Hours worked by individual and job characteristics",
        2,
        interaction_job_char="full",
    )
    tab_short = regression_table_wrapper(
        hours_models_full_interact,
        regressor_order=regressor_order_short,
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=2,
        drop_omitted=True,
        export_csv=ppj(
            "OUT_TABLES",
            "work_hours",
            "regression_hours_heterogeneity_short_full_interact.csv",
        ),
    )


def create_effect_policies_table(data, prec=2):
    data = data.copy()

    # Regressions including support policies
    month_str = "June + September"

    # Run regressions
    models = {}
    data["application_now_togs_yes_05"] = (
        data[["application_now_yes_05", "application_togs_yes_05"]].dropna().sum(axis=1)
        > 0
    ).astype(float)

    for policy_var in [
        "applied_any_policy_05",
    ]:
        models[policy_var] = []
        for depvar in [
            "rel_change_hours_uncond",
            "not_working",
            # "change_empl_diff_narrow",
        ]:
            data_policies = (
                data.query("month > '2020-05-01'").dropna(
                    subset=[depvar, policy_var]
                    + personal_char
                    + job_char
                    + [
                        "sector",
                        "abs_change_hours_uncond_avg_0304",
                        "p_2m_lost_baseline",
                    ]
                    # + reason_controls
                )
            ).copy()
            basic_indepvars = [
                policy_var,
                "abs_change_hours_uncond_avg_0304",
                "p_2m_lost_baseline",
            ]
            models[policy_var] = make_one_reg_het(
                models[policy_var],
                data_policies,
                depvar,
                basic_indepvars,
                month_str,
            )
            indepvars = basic_indepvars + personal_char + job_char
            models[policy_var] = make_one_reg_het(
                models[policy_var],
                data_policies,
                depvar,
                indepvars,
                month_str,
            )
            indepvars = (
                [
                    "sector",
                ]
                + basic_indepvars
                + personal_char
                + job_char
                # + reason_controls_long
            )
            models[policy_var] = make_one_reg_het(
                models[policy_var],
                data_policies,
                depvar,
                indepvars,
                month_str,
            )

        tab = regression_table_wrapper(
            models[policy_var],
            regressor_order=[r for r in regressor_order if "sector" not in r],
            reg_to_table=index_to_table,
            depvar_to_table=column_to_table,
            prec=[
                2,
                2,
                2,
                3,
                3,
                3,
            ],
            drop_omitted=True,
        )

        tab.loc["month $\times$ sector FE"] = ["No", "No", "Yes"] * 2

        tab.columns = pd.MultiIndex.from_tuples(
            [
                (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
                for i, j in enumerate(tab.columns)
            ]
        )
        file_name = f"regression_effect_policies_{policy_var}_incl_june"
        write_table(
            tab,
            ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
            column_format="l" + "r" * len(tab.columns),
            multicolumn_format="c",
            multirow=True,
        )
    basic_indepvars = [
        "abs_change_hours_uncond_avg_0304",
        "p_2m_lost_baseline",
    ]
    indep_vars_full = [
        basic_indepvars,
        basic_indepvars + personal_char + job_char,
        basic_indepvars
        + personal_char
        + job_char
        + [
            "sector",
        ],
    ]
    models = {}
    for policy_var in [
        "applied_any_policy_05",
        "application_now_yes_05",
        "application_togs_yes_05",
    ]:
        models[policy_var] = []
        for depvar in [
            "rel_change_hours_uncond",
            "not_working",
        ]:
            data_policies = (
                data.query("month > '2020-06-01'").dropna(
                    subset=[depvar] + indep_vars_full[-1]
                )
            ).copy()
            for indep_vars in indep_vars_full:
                rhs_formula = formula_string_from_list([policy_var] + indep_vars)
                models[policy_var] = make_one_reg(
                    depvar,
                    rhs_formula,
                    data_policies,
                    cov_type="HC1",
                    models=models[policy_var],
                )

        tab = regression_table_wrapper(
            models[policy_var],
            regressor_order=[r for r in regressor_order if "sector" not in r],
            reg_to_table=index_to_table,
            depvar_to_table=column_to_table,
            prec=[
                2,
                2,
                2,
                3,
                3,
                3,
            ],
            drop_omitted=True,
        )
        tab.loc["sector FE"] = ["No", "No", "Yes"] * 2
        tab.columns = pd.MultiIndex.from_tuples(
            [
                (j, rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
                for i, j in enumerate(tab.columns)
            ]
        )
        file_name = f"regression_effect_policies_{policy_var}"
        write_table(
            tab,
            ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
            column_format="l" + "r" * len(tab.columns),
            multicolumn_format="c",
            multirow=True,
        )

    # Create short policy table

    tab_short = regression_table_wrapper(
        models["applied_any_policy_05"][1:3] + models["applied_any_policy_05"][4:6],
        regressor_order=[
            "applied_any_policy_05",
            "abs_change_hours_uncond_avg_0304",
            "p_2m_lost_baseline",
        ],
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=[2, 2, 3, 3],
        drop_omitted=True,
    )
    tab_now = regression_table_wrapper(
        [models["application_now_yes_05"][2], models["application_now_yes_05"][5]],
        regressor_order=[
            "application_now_yes_05",
            "abs_change_hours_uncond_avg_0304",
            "p_2m_lost_baseline",
        ],
        reg_to_table=index_to_table,
        depvar_to_table=column_to_table,
        prec=[2, 3],
        drop_omitted=True,
    )
    tab_now = tab_now.rename({"affected by NOW": "affected by support program"})

    tab_short = pd.concat({"any program": tab_short, "NOW": tab_now}, axis=1)
    tab_short = pd.concat(
        [
            tab_short.iloc[:, :2],
            tab_short.iloc[:, 4:5],
            tab_short.iloc[:, 2:4],
            tab_short.iloc[:, 5:6],
        ],
        axis=1,
    )

    # switch labels
    tab_short.columns = pd.MultiIndex.from_tuples(
        [
            (j[1], j[0], rf"\multicolumn{{1}}{{c}}{{({i + 1})}}")
            for i, j in enumerate(tab_short.columns)
        ]
    )

    tab_short.loc["demographic controls"] = ["Yes"] * 6
    tab_short.loc["job controls"] = ["Yes"] * 6
    tab_short.loc["month $\times$ sector FE"] = ["No", "Yes", "Yes"] * 2

    file_name = f"regression_hours_policies_short"
    latex = write_table(
        tab_short,
        path=ppj("OUT_TABLES", "work_hours", f"{file_name}.tex"),
        column_format="l" + "r" * len(tab_short.columns),
        multicolumn_format="c",
        multirow=True,
        longtable=False,
        escape=False,
    )


if __name__ == "__main__":
    df_full = pd.read_parquet(ppj("OUT_DATA", "work-childcare-long.parquet"))

    data = df_full.query(
        "18 <= age <= 66 and hours_uncond_baseline >= 10 and month != ['2019-11-01', '2020-11-01']"
    ).copy()

    # ToDo: Move this part to data management
    data["March_June"] = data["March_April"] + data["May_June"]
    data["September_December"] = data["September"] + data["December"]

    data["not_working_unrel_corona"] = data["reason_unrel_corona"]
    data.loc[
        data[
            [
                "day_off_leisure",
                "day_off_other",
                "day_off_sick",
                "day_off_official",
            ]
        ].max(axis=1)
        > 0,
        "not_working_unrel_corona",
    ] = 1
    data.loc[
        data[
            [
                "day_off_leisure",
                "day_off_other",
                "day_off_sick",
                "day_off_official",
            ]
        ].max(axis=1)
        == 0,
        "not_working_unrel_corona",
    ] = 0

    data = data.reset_index()
    create_heterogeneity_tables(data)

    hh_income = pd.read_parquet(ppj("OUT_DATA", "hh_income.parquet"))

    # ToDo: Adjust index in data management and remove here
    hh_income = hh_income.reset_index().set_index(["personal_id", "month"])

    create_effect_working_hours_reg(df_full, hh_income, 3)

    # create_effect_policies_table(data, 2)
    create_hh_income_table(
        "rel_change_hours_uncond",
        data,
        "reg_hours_hh_income_quintiles_rel",
        prec=2,
    )
    create_hh_income_table(
        "abs_change_hours_uncond",
        data,
        "reg_hours_hh_income_quintiles_abs",
        prec=1,
    )
