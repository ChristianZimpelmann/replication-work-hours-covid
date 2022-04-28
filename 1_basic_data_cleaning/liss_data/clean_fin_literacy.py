def clean_fin_literacy(data):
    """
    Data cleaning for fin literacy questionnaire.
    """
    data["fin_literacy"] = (
        (data["literacy_q1"] == "more than 102 euros") * 1
        + (data["literacy_q2"] == "less than today") * 1
        + (data["literacy_q3"] == "not true") * 1
        + (data["literacy_q4"] == "they should decrease") * 1
    ) / 4
    return data
