import numpy as np
import pandas as pd
from sklearn.decomposition import FactorAnalysis as sk_FA


def clean_pref_numeracy(data):
    """
    Data cleaning for preferences numeracy (first part extra wave 2018) questionnaire.

    """
    # Make risk variable

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
    reached_bad_node_error = (data[portfolio_choices] == [1, 1, 1, 2, 1]).all(axis=1)
    reached_bad_node_noerror = (data[portfolio_choices] == [1, 1, 1, 2, 2]).all(axis=1)
    reached_bad_node = reached_bad_node_error | reached_bad_node_noerror
    ce = ce_results.apply(lambda x: x[1])
    ce = ce.where(~reversal)
    actual_ce_to_score = get_map_to_risk_av_scores(ce.dropna().unique())
    data["ce_for_300eur_50pct"] = ce
    data["reached_bad_node"] = reached_bad_node
    data["reached_bad_node_error"] = reached_bad_node_error
    data["quantitative_risk_q"] = data["ce_for_300eur_50pct"].map(actual_ce_to_score)

    portfolio_choices_b = [
        "portfolio1b",
        "portfolio2b",
        "portfolio3b",
        "portfolio4b",
        "portfolio5b",
    ]
    portfolio_amounts_b = [
        "portfolio2b_amt",
        "portfolio3b_amt",
        "portfolio4b_amt",
        "portfolio5b_amt",
    ]
    ce_results_b = data.apply(
        lambda x: get_ce(x, portfolio_choices_b, portfolio_amounts_b, 160), axis=1
    )
    reversal_b = ce_results_b.apply(lambda x: x[0])
    reached_bad_node_error_b = (data[portfolio_choices_b] == [1, 1, 1, 2, 1]).all(
        axis=1
    )
    reached_bad_node_noerror_b = (data[portfolio_choices_b] == [1, 1, 1, 2, 2]).all(
        axis=1
    )
    reached_bad_node_b = reached_bad_node_error_b | reached_bad_node_noerror_b
    ce_b = ce_results_b.apply(lambda x: x[1])
    ce_b = ce_b.where(~reversal_b)
    data["ce_20pct_for_300eur_90pct"] = ce_b
    data["reached_bad_node_20pct"] = reached_bad_node_b
    data["reached_bad_node_error_20pct"] = reached_bad_node_error_b
    data["quantitative_risk_q_20pct"] = data["ce_20pct_for_300eur_90pct"].map(
        actual_ce_to_score
    )
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

    # Make locus of control vars
    cols = ["loc1", "loc2", "loc3", "loc4", "loc5", "loc6", "loc7"]
    temp = data[cols].copy()
    temp = temp.dropna()

    # multiply by -1 = larger val more control
    fa = std_normalise(-sk_FA(n_components=1).fit_transform(temp))
    data["loc_fa_score"] = pd.Series(fa.squeeze(), index=temp.index)

    # Make basic numeracy variable
    num_to_sol = {
        "num1": "150 euro",
        "num2": "100",
        "num3": "9.000 euro",
        "num4": "15 cent",
        "num5": "400.000 euro",
        "num6": "242 euro",
    }
    temp = pd.DataFrame(index=data.index)
    for var, sol in num_to_sol.items():
        temp[f"{var}_correct"] = (data[var].dropna() == sol).astype("float")

    temp = temp[[c for c in temp.columns if "correct" in c]].dropna(how="all")

    # Aggregate over questions
    data["num_mean_correct"] = temp.sum(axis=1) / temp.count(axis=1).max()
    data["basic_numeracy"] = std_normalise(data["num_mean_correct"])

    # Clean some other variables
    for c in [
        "qual_altruism",
        "revenge",
        "trust",
        "time_pref",
        "neg_rp_self",
        "neg_rp_other",
        "pos_rp_self",
        "good_at_maths",
        "procrastinate",
    ]:
        data[c] = (
            data[c]
            .replace(
                {
                    "0 totaal niet bereid om zo te handelen": 0,
                    "0 beschrijft me in het geheel niet": 0,
                    "10 zeer bereid om zo te handelen": 10,
                    "10 beschrijft me perfect": 10,
                }
            )
            .astype(float)
        )
    data["gift_to_strangers"] = data["gift_to_strangers"].replace(
        {
            "Ja, het cadeau ter waarde van 20 euro": 20,
            "Ja, het cadeau ter waarde van 25 euro": 25,
            "Nee, ik zou geen cadeau geven": 0,
            "Ja, het cadeau ter waarde van 10 euro": 10,
            "Ja, het cadeau ter waarde van 5 euro": 5,
            "Ja, het cadeau ter waarde van 15 euro": 15,
            "Ja, het cadeau ter waarde van 30 euro": 30,
        }
    )
    return data


def std_normalise(x):
    return (x - x.mean()) / x.std()


def get_ce(x, choice_vars, amount_vars, variable_option_init_para=160):
    # ce bounds if choices do not restrict them
    ce_lower_bound = 0
    ce_upper_bound = 320
    for i, choice_var in enumerate(choice_vars):
        choice = x[choice_var]
        amt = variable_option_init_para if i == 0 else x[amount_vars[i - 1]]
        if choice == 1.0:
            ce_lower_bound = amt
        elif choice == 2.0:
            ce_upper_bound = amt
    ce = (ce_lower_bound + ce_upper_bound) / 2
    reversal = ce_lower_bound > ce_upper_bound
    return reversal, ce


def get_map_to_risk_av_scores(unique_ces):
    # From Fig 7 of Online Appendix of Global Evidence on Economic Preferences, QJE
    proper_ce_to_score = {float(5 + (10) * i): (i + 1) for i in range(32)}
    proper_ces = list(proper_ce_to_score.keys())
    actual_ce_to_score = {}
    # if someone stops early or if there is a coding error, the CE isn't one of the
    # 32 proper ones
    # in that case, determine the two closest proper CEs and make the score a
    # weighted average of the scores of these, using the distances as weights
    for val in unique_ces:
        closest_vals_index = (
            pd.Series(val - np.array(proper_ces)).abs().nsmallest(2).index
        )
        val_1 = proper_ces[closest_vals_index[0]]
        val_2 = proper_ces[closest_vals_index[1]]
        upper = max(val_1, val_2)
        lower = min(val_1, val_2)
        weight_upper = (val - lower) / (upper - lower)
        score = (
            weight_upper * proper_ce_to_score[upper]
            + (1 - weight_upper) * proper_ce_to_score[lower]
        )
        actual_ce_to_score[val] = score
    return actual_ce_to_score
