def clean_manipulation_check(data):
    """
    Data cleaning for manipulation check
    """

    # Rename conditions
    cond_renaming = {
        "[ln14a088] + no feedback": "third_trick",
        "Control group": "control",
        "[ln14a015] + feedback & [ln14a049] + no feedback": "first_feedback_second",
        "[ln14a015] + no feedback": "first_trick",
        "[ln14a015] & [ln14a049] + no feedback": "first_trick_second",
        "[ln14a015] + feedback & [ln14a088] + no feedback": "first_feedback_third",
        "[ln14a049] + no feedback": "second_trick",
        "[ln14a049] + feedback & [ln14a088] + no feedback": "second_feedback_third",
    }
    data["condition"] = data["condition"].cat.rename_categories(cond_renaming)

    # Calculate indicators if trick questions are missed
    data["missed_first_trick"] = ~data["first_trick_question"].isna()
    data["missed_second_trick"] = (
        ~data["trick_instruction"].isna() & data["click_on_title"].isna()
    )
    data["missed_third_trick"] = ~data["second_trick_question"].isna()

    data["missed_any_trick"] = (
        data["missed_first_trick"]
        | data["missed_second_trick"]
        | data["missed_third_trick"]
    )
    return data
