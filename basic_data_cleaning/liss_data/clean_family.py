import numpy as np
import pandas as pd
from liss_data.utils_liss_data import remove_order_from_categorical


def clean_family(data):
    """Data cleaning of family and household.
    Date and time of the questionnaire are not cleaned, due to unclear coding.
    """

    rename_childs = {
        3.0: "child 3",
        1.0: "child 1",
        2.0: "child 2",
        4.0: "child 4",
        5.0: "child 5",
        6.0: "child 6",
        7.0: "child 7",
        8.0: "child 8",
        9.0: "child 9",
    }

    data["random_child"] = (
        data["random_child"].replace(rename_childs).astype("category")
    )

    data.replace(
        {"I don't know": np.nan, "Ik weet het nie": np.nan, "I don\x92t know": np.nan},
        inplace=True,
    )

    childcare_options = [
        "preschool",
        "afterschool",
        "host",
        "paid",
        "home",
        "unpaid",
        "other",
        "none",
    ]

    bool_variables = (
        [
            "father_alive",
            "mother_alive",
            "father_partner",
            "mother_partner",
            "partner",
            "partner_live",
            "married",
            "children",
            "married_before",
        ]
        + [f"child{num}_partner" for num in range(1, 16)]
        + [
            "children_future",
            "receive_father",
            "receive_mother",
            "receive_parents",
            "give_father",
            "give_mother",
            "give_parents",
        ]
        + [
            f"child_{care}"
            for care in ["food", "laundry", "cleaning", "chores", "groceries"]
        ]
        + [
            f"childcare_young_{option}"
            for option in childcare_options + ["nursery", "daycare"]
        ]
        + [f"childcare_mid_{option}" for option in childcare_options + ["between"]]
        + [f"childcare_old_{option}" for option in childcare_options]
        + [f"child{num}_school" for num in range(1, 16)]
        + [f"child{num}_continuous" for num in range(1, 16)]
        + [f"child{num}_died" for num in range(1, 16)]
        + ["childcare_receipts", "partner_same", "children_died", "children_alive"]
        + ["children_amount_changed", "children_alive_change"]
    )

    bool_dict = {"yes": 1, "no": 0}

    for var in bool_variables:
        if data[var].dtype == "float":
            pass
        else:
            data[var].replace(bool_dict, inplace=True)
            data[var] = data[var].astype(np.float32)

    behavior_variables = [
        "quarrel",
        "focus",
        "confused",
        "social",
        "worthless",
        "disliked",
        "headstrong",
        "sad",
        "adults",
        "dependent",
        "disobedient",
        "teachers",
    ]

    household_vars = ["time", "boring", "flexible", "stress"]
    division_vars = ["household", "paidwork", "children"]
    care_vars = ["burden", "demands", "taxing", "energy", "easy"]
    category_variables = (
        ["parents_divorce", "parents_postal", "partner_country", "maried_before_end"]
        + [f"child{num}_sex" for num in range(1, 16)]
        + [f"child{num}_home" for num in range(1, 16)]
        + [f"child{num}_parent" for num in range(1, 16)]
        + [f"child{num}_track" for num in range(1, 16)]
        + [f"child{num}_denom" for num in range(1, 16)]
        + [f"child{num}_break" for num in range(1, 16)]
        + [f"child{num}_fulltime" for num in range(1, 16)]
        + [f"child{num}_sectrack" for num in range(1, 16)]
        + ["activity_alone", "activity_partner"]
        + [
            f"division_{task}"
            for task in [
                "food",
                "laundry",
                "cleaning",
                "chores",
                "finances",
                "groceries",
            ]
        ]
        + [
            "unpaid_childsitter_young",
            "unpaid_childsitter_mid",
            "unpaid_childsitter_old",
        ]
        + [
            "partner_different",
            "partner_separate",
            "childless_choice",
            "childless_loss",
            "relation_family",
            "father_phone",
            "mother_phone",
            "father_contact",
            "mother_contact",
        ]
        + [f"behavior_{var}" for var in behavior_variables]
        + [f"household_{var}" for var in household_vars]
        + [f"division_{var}" for var in division_vars]
        + [f"care_{var}" for var in care_vars]
    )

    for var in category_variables:
        data[var] = data[var].astype("category")

    for parent in ["mother", "father"]:
        data[f"never_knew_{parent}"] = np.nan
        data.loc[
            data[f"{parent}_birth_period"] == f"I never knew my {parent}",
            f"never_knew_{parent}",
        ] = 1
        data.loc[data[f"{parent}_birth"] > 0, f"never_knew_{parent}"] = 0
        data.loc[
            data[f"{parent}_birth_period"] == f"I never knew my {parent}",
            f"{parent}_birth_period",
        ] = np.nan
        data[f"{parent}_birth_period"] = data[f"{parent}_birth_period"].astype(
            "category"
        )

    # Satisfaction questions are mixed coded
    satisfaction_scale = {
        "entirely satisfied": 10,
        "entirely dissatisfied": 0,
        999: np.nan,
    }

    for var in ["single_satisfied", "relation_satisfaction", "family_satisfaction"]:
        data[var].replace(satisfaction_scale, inplace=True)

    rename_act_scale = {
        "only me": 1,
        "my partner and I do this equally often": 4,
        "my partner and I did this equally often": 4,
        "4 = my partner and I do this equally often": 4,
        "4 = my partner and I did this equally often": 4,
        "1 = only me": 1,
        "7 = only my partner": 7,
        "only my partner": 7,
    }

    care_tasks = ["diapers", "night", "washing", "doctor", "home"]
    act_variables = [f"act_{task}" for task in care_tasks] + [
        f"acted_{task}" for task in care_tasks
    ]

    for var in act_variables:
        data[var].replace(rename_act_scale, inplace=True)

    work = ["playing", "logistic", "behaviour", "outings"]
    rename_work_dutch = {
        "we doen ongeveer even veel": "we do roughly the same amount of work",
        "ik doe veel meer dan mijn partner": "I do a lot more than my partner",
        "ik doe meer dan mijn partner": "I do more than my partner",
        "mijn partner doet meer dan ik": "my partner does more than I",
        "mijn partner doet veel meer dan ik": "my partner does a lot more than I",
    }

    for var in [f"raising_{activity}" for activity in work]:
        data[var].replace(rename_work_dutch, inplace=True)
        data[var] = data[var].astype("category")
    rename_work_times = {
        "we do roughly the same amount of work": "we did roughly the same amount of work",
        "I do a lot more than my partner": "I did a lot more than my partner",
        "I do more than my partner": "I did more than my partner",
        "my partner does more than I": "my partner did more than I",
        "my partner does a lot more than I": "my partner did a lot more than I",
    }

    for var in [f"raised_{activity}" for activity in work]:
        data[var].replace(rename_work_times, inplace=True)
        data[var] = data[var].astype("category")

    rename_questionnaire_scale = {
        "1 = certainly not": 1,
        "5 = certainly yes": 5,
        "1 = definitely no": 1,
        "5 = definitely yes": 5,
    }

    for var in ["difficult", "clear", "thinking", "interesting", "enjoy"]:
        data[f"questionnaire_{var}"].replace(rename_questionnaire_scale, inplace=True)

    for var in ["parents", "father", "mother"]:
        data[f"distance_{var}"].replace({"unknown": np.nan}, inplace=True)
        data[f"distance_{var}"] = data[f"distance_{var}"].astype(np.float32)

    feelings = [
        "fond",
        "close",
        "mixed",
        "irritation",
        "connected",
        "guilt",
        "angry",
        "unstable",
        "embarrassed",
    ]

    rename_feelings = {"7=totally applicable": 7, "1=not applicable": 1}

    for feel in feelings:
        data[f"mother_{feel}"].replace(rename_feelings, inplace=True)
        data[f"mother_{feel}"] = data[f"mother_{feel}"].astype(np.float32)
        data[f"child_{feel}"].replace(rename_feelings, inplace=True)
        data[f"child_{feel}"] = data[f"child_{feel}"].astype(np.float32)

    obedience_rename = {
        "Parents today too often let children do what they want to do - agree": 7,
        "Parents today too often let children do what they want to do - fairly agree": 6,
        "Parents today too often let children do what they want to do - slightly agree": 5,
        "agree as much with statement on the left as on the right": 4,
        "Today there is too much emphasis on children being obedient - slightly agree": 3,
        "Today there is too much emphasis on children being obedient - fairly agree": 2,
        "Today there is too much emphasis on children being obedient - agree": 1,
    }
    data["parenting_obedience1"].replace(obedience_rename, inplace=True)

    partner_vars = [
        "younger",
        "same_age",
        "older",
        "religious",
        "atheist",
        "primary",
        "secondary",
        "vocational",
        "academic",
        "unemployed",
        "employed",
        "single",
        "married",
    ]

    rename_partner_scale = {
        "1 = highly undesirable": 1,
        "3 = does not matter": 3,
        "5 = highly desirable": 5,
    }

    for col in [f"partner_{var}" for var in partner_vars]:
        data[col].replace(rename_partner_scale, inplace=True)
        data[col] = data[col].astype(np.float32)

    remove_cols = [f"child{num}_sex" for num in range(1, 16)] + [
        f"child{num}_parent" for num in range(1, 16)
    ]

    # Check order or no order of categoricals
    # ToDo: Maybe no need to remove it if some are set correctly
    data = remove_order_from_categorical(data, remove_cols)

    for var in [f"child{num}_break" for num in range(1, 16)]:
        data[var] = pd.Categorical(
            data[var],
            pd.CategoricalIndex(data["child1_break"]).categories,
            ordered=True,
        )

    for var in [f"child{num}_fulltime" for num in range(1, 16)]:
        data[var] = pd.Categorical(
            data[var],
            pd.CategoricalIndex(data["child2_fulltime"]).categories,
            ordered=True,
        )
    reorder_division = [
        "I do a lot more than my partner",
        "I do more than my partner",
        "we do roughly the same amount of work",
        "my partner does more than I",
        "my partner does a lot more than I",
    ]

    for var in [
        f"division_{task}"
        for task in ["food", "laundry", "cleaning", "chores", "finances", "groceries"]
    ]:
        data[var] = pd.Categorical(data[var], reorder_division, ordered=True)

    data["relation_family"] = pd.Categorical(
        data["relation_family"],
        ["poor", "very poor", "not good, not poor", "good", "very good"],
        ordered=True,
    )

    for parent in ["mother", "father"]:
        for var in ["phone", "contact"]:
            data[f"{parent}_{var}"] = pd.Categorical(
                data[f"{parent}_{var}"],
                [
                    "never",
                    "once",
                    "a few times",
                    "at least every month",
                    "at least every week",
                    "a few times per week",
                    "every day",
                ],
                ordered=True,
            )
    for c in [
        "division_food",
        "division_laundry",
        "division_cleaning",
        "division_chores",
        "division_finances",
        "division_groceries",
        "raising_playing",
        "raising_logistic",
        "raising_behaviour",
        "raising_outings",
    ]:
        data[c] = pd.Categorical(
            data[c],
            [
                "I do a lot more than my partner",
                "I do more than my partner",
                "we do roughly the same amount of work",
                "my partner does more than I",
                "my partner does a lot more than I",
            ],
            ordered=True,
        )
    for c in ["division_household", "division_paidwork", "division_children"]:
        data[c] = pd.Categorical(
            data[c],
            [
                "very unreasonable with respect to me",
                "somewhat unreasonable with respect to me",
                "reasonable for both of us",
                "somewhat unreasonable with respect to my partner",
                "very unreasonable with respect to my partner",
            ],
            ordered=True,
        )
    for var in [f"behavior_{var}" for var in behavior_variables]:
        data[var] = pd.Categorical(
            data[var], ["often true", "sometimes true", "not true"], ordered=True
        )

    for var in [f"care_{var}" for var in care_vars]:
        data[var] = pd.Categorical(
            data[var],
            [
                "disagree entirely",
                "fairly disagree",
                "slightly disagree",
                "slightly agree",
                "fairly agree",
                "agree entirely",
            ],
            ordered=True,
        )
    return data
