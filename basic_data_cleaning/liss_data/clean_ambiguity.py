import numpy as np


def clean_ambiguity(df):
    """
    Data cleaning for ambiguity questionnaire.

    Calculates ambiguity indeces

    """
    # calculate matching probabilities
    df["matched_prob_50"] = (
        df[["q1_iters", "q1_choice_6", "q1_prob_6"]].apply(
            lambda x: get_matched_prob_q1(
                iters=x[0], final_choice=x[1], final_prob=x[2]
            ),
            axis=1,
        )
        / 100
    )

    df["matched_prob_10"] = (
        df[["q2_iters", "q2_choice_1", "q2_prob_1", "q2_choice_7", "q2_prob_7"]].apply(
            lambda x: get_matched_prob_q2(
                iters=x[0],
                first_choice=x[1],
                first_prob=x[2],
                final_choice=x[3],
                final_prob=x[4],
            ),
            axis=1,
        )
        / 100
    )

    df["matched_prob_90"] = (
        df[["q3_iters", "q3_choice_1", "q3_prob_1", "q3_choice_7", "q3_prob_7"]].apply(
            lambda x: get_matched_prob_q3(
                iters=x[0],
                first_choice=x[1],
                first_prob=x[2],
                final_choice=x[3],
                final_prob=x[4],
            ),
            axis=1,
        )
        / 100
    )
    # calculate best linear fit of m(p)= c + sp
    temp = df[["matched_prob_10", "matched_prob_50", "matched_prob_90"]].apply(
        lambda x: ols(y=[x[0], x[1], x[2]]), axis=1
    )
    df["constant"] = temp.apply(lambda x: x[0])
    df["slope"] = temp.apply(lambda x: x[1])
    # calculate indeces
    df["ambig_av"] = 1 - df["slope"] - 2 * df["constant"]
    df["ll_insens"] = 1 - df["slope"]
    return df


def get_matched_prob_q1(iters, final_choice, final_prob):
    """
    q1. risky urn: 50-50. win condition: ball with win color drawn.
    """
    # indifference condition is exactly what we want to approximate
    if final_choice == "Indifferent":
        matched_prob = final_prob
    else:
        half_interval_length = 50 * 0.5**iters
        # prefer risk
        if final_choice == "Box B":
            matched_prob = final_prob - half_interval_length
        # prefer uncertainty
        elif final_choice == "Box O":
            matched_prob = final_prob + half_interval_length
    return matched_prob


def get_matched_prob_q2(iters, first_choice, first_prob, final_choice, final_prob):
    """
    q2. risky urn: 10-90. win condition: ball with win color drawn.
    """
    # indifference condition is exactly what we want to approximate
    if final_choice == "Indifferent":
        matched_prob = final_prob
    else:
        # if risky prefered, it's the lower interval
        initial_interval = 10 if first_choice == "Box B" else 90
        half_interval_length = initial_interval * 0.5**iters
        # prefer risk
        if final_choice == "Box B":
            matched_prob = final_prob - half_interval_length
        # prefer uncertainty
        elif final_choice == "Box O":
            matched_prob = final_prob + half_interval_length
    return matched_prob


def get_matched_prob_q3(iters, first_choice, first_prob, final_choice, final_prob):
    """
    q3. risky urn: 90-10. win condition: ball with win color NOT drawn.
    This reverses the logic

    """
    # indifference condition is exactly what we want to approximate
    if final_choice == "Indifferent":
        matched_prob = final_prob
    else:
        # if risky prefered, it's the upper interval.
        initial_interval = 10 if first_choice == "Box O" else 90
        half_interval_length = initial_interval * 0.5**iters
        # prefer risk. make final prob a bit lower still
        if final_choice == "Box B":
            matched_prob = final_prob + half_interval_length
        # prefer uncertainty. make final prob a bit larger
        elif final_choice == "Box O":
            matched_prob = final_prob - half_interval_length
    return 100 - matched_prob


def ols(y):
    X = np.array([[1, 1, 1], [0.1, 0.5, 0.9]]).T
    return tuple(np.dot(np.linalg.inv(X.T.dot(X)), X.T.dot(y)))
