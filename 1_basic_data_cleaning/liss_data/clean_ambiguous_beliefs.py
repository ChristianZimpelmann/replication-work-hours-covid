import pandas as pd
import yaml
from config import IN_SPECS_LISS
from liss_data.clean_pref_numeracy import get_ce
from liss_data.clean_pref_numeracy import get_map_to_risk_av_scores
from liss_data.clean_pref_numeracy import std_normalise
from liss_data.cleaning_helpers import replace_values
from liss_data.cleaning_helpers import set_types_file
from liss_data.data_checks import general_data_checks
from liss_data.data_management_ambig_beliefs import create_ambig_beliefs_basic_files
from liss_data.utils_liss_data import clean_background_vars


def clean_ambiguous_beliefs(data, file_format):
    """
    Data cleaning for fin literacy questionnaire.
    """

    # Create some basic files
    create_ambig_beliefs_basic_files(data, file_format)

    # replace portfolio names and convert values to numerics
    with open(IN_SPECS_LISS / "xxx-ambiguous-beliefs_replacing.yaml") as file:
        replace_dict = yaml.safe_load(file)

    rename_df = pd.read_csv(
        IN_SPECS_LISS / "xxx-ambiguous-beliefs_renaming.csv",
        sep=";",
    )

    data = replace_values(data, replace_dict, rename_df)
    fin_num_to_sol = {
        "fin_num_interest_basic": "meer dan 1010 euro",
        "fin_num_interest": 1003.0,
        "fin_num_interest_compound": "meer dan 1015 euro",
        "fin_num_inflation": "minder dan vandaag",
    }
    data = make_numeracy_vars(fin_num_to_sol, data, "fin_numeracy")

    prob_num_to_sol = {
        "prob_num_10w0r_chance_r": 0.0,
        "prob_num_7w3r_chance_w": 70.0,
        "prob_num_70_chance_not": 30.0,
        "prob_num_50_50_indepchance_both": 25.0,
        "prob_num_coin_gamblers_fallacy": 50.0,
        "prob_num_chance_subset": "minder dan 50%",
        "prob_num_chance_superset": "meer dan 50%",
    }
    data = make_numeracy_vars(prob_num_to_sol, data, "prob_numeracy")

    # Make basic numeracy variable
    num_to_sol = {
        "num1": "150 euro",
        "num2": "100",
        "num3": "9.000 euro",
        "num4": "15 cent",
        "num5": "400.000 euro",
        "num6": "242 euro",
    }
    data = make_numeracy_vars(num_to_sol, data, "basic_numeracy")

    # Calculate risk-aversion variables
    data = add_risk_pref(data)

    # Calculate stereotypes_vars
    for var in [
        "self_assessment_greedy",
        "self_assessment_gambler",
        "self_assessment_selfish",
        "other_stocks_greedy",
        "other_stocks_gambler",
        "other_stocks_selfish",
        "other_nostocks_greedy",
        "other_nostocks_gambler",
        "other_nostocks_selfish",
        "response_stocks_greedy",
        "response_stocks_gambler",
        "response_stocks_selfish",
        "response_nostocks_greedy",
        "response_nostocks_gambler",
        "response_nostocks_selfish",
    ]:
        data[var] = data[var].astype(float)

    # Clean demographic variables
    data = clean_background_vars(data)

    # Set types of variables using renaming file.
    data = set_types_file(
        panel=data,
        rename_df=rename_df,
        cat_sep="|",
        int_to_float=True,
        bool_to_float=True,
        few_int_to_cat=False,
    )

    # Check some consistency in the data.
    _check_ambiguous_beliefs(data)

    return data


def make_numeracy_vars(var_to_sol, data, var_name):
    """
    Calculates numeracy vars from sets of quesions with correct solutions
    :param mean: aggregate by mean (if False take sum instead)
    """

    temp = pd.DataFrame(index=data.index)
    for var, sol in var_to_sol.items():
        temp[var] = data[var]
        temp[f"{var}_correct"] = (temp[var].dropna() == sol).astype("float")
    temp = temp[[c for c in temp.columns if "correct" in c]].dropna(how="all")

    # Aggregate over questions
    if var_name == "basic_numeracy":
        data["num_mean_correct"] = temp.sum(axis=1) / temp.count(axis=1).max()
        data[var_name + "_stdzd"] = std_normalise(data["num_mean_correct"])
    else:
        data[var_name] = temp.mean(axis=1)
        data[var_name + "_stdzd"] = std_normalise(data[var_name])

    return data


def add_risk_pref(data):
    """Calculates risk aversion and risk taking parameters from sets of
    questions on portfolio holdings and the general risk question asked in the data.
    Returns the data with the corresponding columns added to it.
    """
    portfolio_choices = [
        "portfolio1",
        "portfolio2",
        "portfolio3",
        "portfolio4",
        "portfolio5",
    ]
    portfolio_amounts = [
        "portfolio2_amt",
        "portfolio3_amt",
        "portfolio4_amt",
        "portfolio5_amt",
    ]
    ce_results = data.apply(
        lambda x: get_ce(x, portfolio_choices, portfolio_amounts, 160), axis=1
    )
    reversal = ce_results.apply(lambda x: x[0])
    ce = ce_results.apply(lambda x: x[1])
    ce = ce.where(~reversal)
    actual_ce_to_score = get_map_to_risk_av_scores(ce.dropna().unique())
    data["ce_for_300eur_50pct"] = ce
    data["quantitative_risk_q"] = data["ce_for_300eur_50pct"].map(actual_ce_to_score)
    # from I.I. Computation of Preference Indices at the Individual Level of
    # qje paper "Global Evidence on Economic Preferences"
    data["general_risk_q"] = (
        data["general_risk_q"]
        .replace(
            {
                "0 totaal niet bereid bent om risico\x92s te nemen": 0,
                "10 zeer bereid bent om risico\x92s te nemen": 10,
            }
        )
        .astype(float)
    )

    data["risk_taking_index"] = (
        std_normalise(data["quantitative_risk_q"]) * 0.472_998_5
        + std_normalise(data["general_risk_q"]) * 0.527_001_5
    )
    data["risk_aversion_index"] = std_normalise(data["risk_taking_index"] * -1)

    return data


def _check_ambiguous_beliefs(panel):
    """Check some of the data in the ambigous_beliefs database.

    Args:
        panel(pandas.DataFrame): The data frame to be checked.
    """
    out = panel.copy()
    general_data_checks(out)
