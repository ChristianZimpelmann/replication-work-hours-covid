import warnings

import numpy as np
import pandas as pd
from config import DATA_RAW
from config import OUT_DATA_LISS


def clean_aex_intervals(data, savings_rate):
    """
    Adjust endpoints by savings_rate and build pandas intervals.
    """

    # Adjust endpoints by savings_rate
    adjustment = np.round(savings_rate * 1000)

    for c in ["aex_iv_1_l", "aex_iv_1_r", "aex_iv_2_l", "aex_iv_2_r"]:
        if data[c] in [0, np.inf]:
            data[c + "_adj"] = data[c]
        else:
            data[c + "_adj"] = data[c] + adjustment

    # Build intervals

    data["aex_interval_1"] = pd.Interval(
        data["aex_iv_1_l_adj"], data["aex_iv_1_r_adj"], closed=data["aex_iv_1_closed"]
    )
    data["aex_interval_2"] = pd.Interval(
        data["aex_iv_2_l_adj"], data["aex_iv_2_r_adj"], closed=data["aex_iv_2_closed"]
    )

    return data


def clean_event_properties(wave):
    """
    Collect properties about all available events.
    """

    df = pd.DataFrame(
        columns=[
            "aex_iv_1_l",
            "aex_iv_1_r",
            "aex_iv_1_closed",
            "aex_iv_2_l",
            "aex_iv_2_r",
            "aex_iv_2_closed",
            "aex_1",
            "aex_pi_0",
            "aex_pi_1",
            "aex_pi_2",
        ]
    )
    if wave == "temp":
        df.loc["0"] = [0, np.inf, "neither", 0, 0, "neither", 0, 1, 0, 0]
        df.loc["1"] = [1, np.inf, "neither", 0, 0, "neither", 0, 0, 1, 0]
        df.loc["2"] = [-np.inf, -0.5, "left", 0, 0, "neither", 0, 0, 0, 1]
        df.loc["3"] = [-0.5, 1, "both", 0, 0, "neither", 1, 0, -1, -1]
        df.loc["1c"] = [-np.inf, 1, "both", 0, 0, "neither", 1, 0, -1, 0]
        df.loc["2c"] = [-0.5, np.inf, "left", 0, 0, "neither", 1, 0, 0, -1]
        df.loc["3c"] = [-np.inf, -0.5, "left", 1, np.inf, "neither", 0, 0, 1, 1]
    else:
        df.loc["0"] = [1000, np.inf, "neither", 0, 0, "neither", 0, 1, 0, 0]
        df.loc["1"] = [1100, np.inf, "neither", 0, 0, "neither", 0, 0, 1, 0]
        df.loc["2"] = [0, 950, "left", 0, 0, "neither", 0, 0, 0, 1]
        df.loc["3"] = [950, 1100, "both", 0, 0, "neither", 1, 0, -1, -1]
        df.loc["1c"] = [0, 1100, "both", 0, 0, "neither", 1, 0, -1, 0]
        df.loc["2c"] = [950, np.inf, "left", 0, 0, "neither", 1, 0, 0, -1]
        df.loc["3c"] = [0, 950, "left", 1100, np.inf, "neither", 0, 0, 1, 1]

    savings_rate = {1: 0.001, 2: 0, 3: 0, 4: 0, "temp": 0, 5: 0, 6: 0, 7: 0}
    df = df.apply(clean_aex_intervals, axis=1, args=[savings_rate[wave]])

    df.index.name = "event"
    return df


def generate_choice_properties(event_prop, wave):
    """
    Collect properties about all available choices.
    """
    # Two short functions to calculate the corresponding aex_event and lottery

    def calc_event(arandom):
        event, lottery = divmod(arandom, 13)
        event += 1
        if lottery == 0:
            event -= 1
            lottery = 13
        number_to_event = {1: "0", 2: "1", 3: "2", 4: "3", 5: "1c", 6: "2c", 7: "3c"}
        return number_to_event[event]

    def calc_lottery(arandom):
        event, lottery = divmod(arandom, 13)
        event += 1
        if lottery == 0:
            event -= 1
            lottery = 13
        return int(lottery)

    choice_prop = pd.DataFrame({"choice_num": range(1, 92)})
    choice_prop["aex_event"] = choice_prop["choice_num"].apply(calc_event)
    choice_prop["lottery"] = choice_prop["choice_num"].apply(calc_lottery)

    # Calculate winning probability for lottery
    suffix_to_lott_risk = {
        1: 50,
        2: 90,
        3: 10,
        4: 95,
        5: 70,
        6: 30,
        7: 5,
        8: 99,
        9: 80,
        10: 60,
        11: 40,
        12: 20,
        13: 1,
    }
    choice_prop["lottery_p_win"] = choice_prop["lottery"].replace(suffix_to_lott_risk)

    # Merge aex_events properties.
    choice_prop = choice_prop.merge(event_prop, left_on="aex_event", right_index=True)

    # Calculate string
    choice_prop["choice_string"] = (
        "event_e"
        + choice_prop["aex_event"]
        + "_"
        + choice_prop["lottery"].astype("str")
    )

    # Set index
    choice_prop = choice_prop.set_index("choice_num")

    # Specify order of questions (needed for simulations later)
    choice_after_aex = {
        50: 1,
        90: 2,
        10: 3,
        95: 4,
        70: 4,
        30: 5,
        5: 7,
        99: 6,
        80: 5,
        60: 4,
        40: 3,
        20: 2,
        1: 1,
    }
    choice_after_lot = {
        50: 2,
        90: 3,
        10: 4,
        95: 10,
        70: 5,
        30: 6,
        5: 6,
        99: 6,
        80: 5,
        60: 4,
        40: 3,
        20: 2,
        1: 1,
    }

    choice_prop["next_choice_after_aex"] = choice_prop.index + choice_prop[
        "lottery_p_win"
    ].map(choice_after_aex)
    choice_prop["next_choice_after_lot"] = choice_prop.index + choice_prop[
        "lottery_p_win"
    ].map(choice_after_lot)
    return choice_prop


def generate_choices_df(renamed_raw, choice_prop):

    # Find all columns of non-final and final choices
    non_final_choices = renamed_raw[
        [
            c
            for c in renamed_raw.columns
            if c.startswith("event_e")
            and len(c.split("_")) > 2
            and (c[-4] == "e" or c[-5] == "e" or not c.endswith("_1"))
        ]
    ]
    final_choices = renamed_raw[
        [
            c
            for c in renamed_raw.columns
            if c.startswith("event_")
            and len(c.split("_")) > 2
            and not (c[-4] == "e" or c[-5] == "e" or not c.endswith("_1"))
        ]
    ]

    # Melt DataFrame (wide to long format)
    non_final_choices = pd.melt(
        non_final_choices.reset_index(),
        id_vars="personal_id",
        var_name="choice_string",
        value_name="choice",
    )
    non_final_choices = non_final_choices.set_index(
        ["personal_id", "choice_string"]
    ).sort_index()

    final_choices = pd.melt(
        final_choices.reset_index(),
        id_vars="personal_id",
        var_name="choice_string",
        value_name="choice",
    )
    final_choices["choice_string"] = final_choices["choice_string"].apply(
        lambda x: x[:-2]
    )
    final_choices = final_choices.set_index(
        ["personal_id", "choice_string"]
    ).sort_index()

    # Join non-final and final choices and keep information if final choice or not
    choices = non_final_choices
    choices["final_choice"] = final_choices["choice"]
    choices["choice"] = choices["choice"].fillna(choices["final_choice"])
    choices["choice_final"] = choices["final_choice"].isin(["optie 1", "optie 2"])

    # Some data cleaning
    choices = choices[["choice", "choice_final"]]
    choices = choices.dropna(axis=0, subset=["choice"])
    choices["choice"] = choices["choice"].replace({"optie 1": "AEX", "optie 2": "lot"})

    # Merge choice properties
    choices = choices.reset_index().set_index("choice_string")
    choices = choices.join(choice_prop.reset_index().set_index("choice_string"))

    # Set index and make sure it is int
    choices = choices.reset_index()
    choices["personal_id"] = choices["personal_id"].astype("int")
    choices = choices.set_index(["personal_id", "choice_num"]).sort_index()

    choices = choices.drop(["lottery"], axis=1)

    return choices


def clean_matching_probabilites(choices):
    def get_matching_prob(choice_and_prob):
        """
        Calculates the baseline matching probability.
        args:
            choice_and_prob: tuple, containing string and integer
        returns:
            pandas interval
        """
        dic = {
            1: {
                "AEX": pd.Interval(left=1, right=5, closed="both"),
                "lot": pd.Interval(left=0, right=1, closed="both"),
            },
            5: {"AEX": pd.Interval(left=5, right=10, closed="both")},
            20: {
                "AEX": pd.Interval(left=20, right=30, closed="both"),
                "lot": pd.Interval(left=10, right=20, closed="both"),
            },
            40: {
                "AEX": pd.Interval(left=40, right=50, closed="both"),
                "lot": pd.Interval(left=30, right=40, closed="both"),
            },
            60: {
                "AEX": pd.Interval(left=60, right=70, closed="both"),
                "lot": pd.Interval(left=50, right=60, closed="both"),
            },
            80: {
                "AEX": pd.Interval(left=80, right=90, closed="both"),
                "lot": pd.Interval(left=70, right=80, closed="both"),
            },
            95: {"lot": pd.Interval(left=90, right=95, closed="both")},
            99: {
                "AEX": pd.Interval(left=99, right=100, closed="both"),
                "lot": pd.Interval(left=95, right=99, closed="both"),
            },
        }
        return dic[choice_and_prob["lottery_p_win"].values[0]][
            choice_and_prob["choice"].values[0]
        ]

    def select_final_nodes(df):
        """
        Extracts the final choice and node from the choices dataframe
        args:
            df: pandas dataframe
        returns:
            tuple, containing string and integer
        """
        end_nodes = [1, 5, 20, 40, 60, 80, 95, 99]

        # Ignore answers to extra questions
        df = df.copy().query("choice_final == False")

        # Select only rows at end nodes
        df = df[df[["lottery_p_win"]].isin(end_nodes).values]
        df = df.query("~(choice=='lot' & lottery_p_win==5)")
        df = df.query("~(choice=='AEX' & lottery_p_win==95)")

        return df

    final_nodes = select_final_nodes(choices)

    # Calculate baseline matching probability
    matching_prob_interval = final_nodes.groupby(["personal_id", "aex_event"])[
        ["choice", "lottery_p_win"]
    ].apply(get_matching_prob)

    # Put interesting stuff in a dataframe
    df = pd.DataFrame(
        matching_prob_interval, columns=["baseline_matching_prob_interval"]
    )
    df["baseline_matching_prob_leftb"] = matching_prob_interval.apply(lambda x: x.left)
    df["baseline_matching_prob_midp"] = matching_prob_interval.apply(lambda x: x.mid)
    df["baseline_matching_prob_rightb"] = matching_prob_interval.apply(
        lambda x: x.right
    )

    return df


def clean_indices(matching_probs):
    """
    Calculate ambiguity indices and adjusted probabilities based on matching probabilities.
    """
    # Long to wide
    data = (
        matching_probs.reset_index().pivot(
            index="personal_id",
            columns="aex_event",
            values="baseline_matching_prob_midp",
        )
        / 100
    )
    data.columns = ["mp_e" + c for c in data.columns]

    # ambiguity_indices
    m_E = data[["mp_e1", "mp_e2", "mp_e3"]].mean(axis=1)
    m_Ec = data[["mp_e1c", "mp_e2c", "mp_e3c"]].mean(axis=1)

    data["ambig_av"] = 1 - (m_E + m_Ec)
    # NB We scale ambiguity aversion to lie in -0.5 to 0.5 instead of [-1, 1]
    data["ambig_av"] *= 1 / 2
    data["ll_insen"] = 3 * (1 / 3 - (m_Ec - m_E))

    data["sigma"] = 1 - data["ll_insen"]
    data["tau"] = 0.5 * (data["ll_insen"] - data["ambig_av"] * 2)

    # adjusted (subjective) probability
    events = [c[4:] for c in data.columns if c.startswith("mp_e")]
    for e in events:
        data["subj_p_e" + e] = (data["mp_e" + e] - data["tau"]) / data["sigma"].where(
            data["sigma"] != 0
        )

    return data


def calc_pay_outs(data_original, choices):
    def win_prob_and_result_to_wheel_postion(win_prob, has_won):
        """
        Maps a lottery win probability and the result of that lottery into a final
        position for the wheel. Pos is the *start* of the golden pie chart. Thus
        for the pie chart to reach upt to the arrow at position 360
        we need pos >= 360 * (1 - win_prob)
        """
        pos_lb_for_visual_win = 360 * (1 - win_prob)
        # The second condition is for when you lose with 0.99 win prob.
        # It then sets position to mid point
        visual_margin = 5 if (1 - win_prob) * 360 > 10 else ((1 - win_prob) * 360) / 2

        if has_won:
            pos = np.random.uniform(pos_lb_for_visual_win, 360)
        else:
            # we don't want losses to be too close to win region
            pos = np.random.uniform(
                visual_margin, pos_lb_for_visual_win - visual_margin
            )
        return pos

    def play_lottery(win_prob):
        """
        Returns a tuple with a boolean and a wheel position
        """
        win_prob /= 100
        result = np.random.binomial(n=1, p=win_prob, size=1)
        result = bool(result)

        return result, np.round(win_prob_and_result_to_wheel_postion(win_prob, result))

    # Load historical aex returns
    # ToDo: update historical returns

    # Use this side to update the file: https://finance.yahoo.com/quote/%5EAEX/history/
    aex_rates = pd.read_excel(DATA_RAW / "aex_historic.xlsx")
    aex_rates = aex_rates.set_index("day")
    aex_rates = aex_rates.fillna(method="bfill")
    data_original.loc[data_original["end_date"] == " ", "end_date"] = data_original.loc[
        data_original["end_date"] == " ", "start_date"
    ]
    data_original["end_date"] = pd.to_datetime(
        data_original["end_date"], format="%d-%m-%Y"
    )
    data_original = pd.merge(
        data_original.reset_index(),
        aex_rates.reset_index(),
        left_on="end_date",
        right_on="day",
        how="left",
    )
    # Calculate the pay out question for each wave
    data_original["pay_out_question"] = np.nan
    for wave in range(1, data_original["wave"].max() + 1):
        data_original.loc[
            data_original["wave"] == wave, "pay_out_question"
        ] = data_original.loc[
            data_original["wave"] == wave, "pay_out_question_w" + str(wave)
        ]
        data_original[
            ["personal_id", "wave"] + [c for c in data_original if "pay_out" in c]
        ]

        # Make sure pay_out_question_w4_temp_aex is only specified in wave 4
        data_original.loc[
            data_original["wave"] != 4, "pay_out_question_w4_temp_aex"
        ] = np.nan

    # Calculate AEX performance from day of answering to 30th April/ 31st October (close)
    # Use e.g. this site: https://finance.yahoo.com/quote/%5EAEX/history/
    # Adjust these values
    # ToDo: update wave
    rate_end_by_wave = {
        1: 518.71,
        2: 571.60,
        3: 577.06,
        4: 512.92,
        5: 533.88,
        6: 707.56,
        7: 792.36,
    }

    # Fill with 0 if wave not specified
    for w in [w for w in data_original["wave"] if w not in rate_end_by_wave]:
        rate_end_by_wave[w] = 0
    data_original["rate_end"] = data_original["wave"].apply(
        lambda x: rate_end_by_wave[x]
    )
    data_original["rate_last_wave"] = data_original["close"]
    data_original["aex_perf"] = np.round(
        (data_original["rate_end"] / data_original["rate_last_wave"]) * 1000
    )

    # Merge choices with pay_out data
    choices = choices.copy()
    choices_aex = pd.merge(
        choices.drop("temp", axis=0, level="wave").reset_index(),
        data_original[
            [
                "personal_id",
                "wave",
                "day",
                "aex_perf",
                "rate_end",
                "rate_last_wave",
                "pay_out_question_w4_temp_aex",
                "pay_out_question",
            ]
        ],
        left_on=["personal_id", "wave"],
        right_on=["personal_id", "wave"],
    )
    choices_temp = pd.merge(
        choices.loc[pd.IndexSlice[:, "temp", :], :].reset_index(),
        data_original.loc[
            data_original["wave"] == 4,
            [
                "personal_id",
                "day",
                "aex_perf",
                "pay_out_question_w4_temp_aex",
                "pay_out_question",
            ],
        ],
        left_on=["personal_id"],
        right_on=["personal_id"],
    )

    # temperature performance is hard-coded
    choices_temp["aex_perf"] = 1.9

    choices = pd.concat([choices_aex, choices_temp])

    # Calc lottery won
    np.random.seed(2)
    choices["lottery_won"], choices["final_position"] = zip(
        *choices["lottery_p_win"].apply(play_lottery)
    )
    choices["lot_prob"] = choices["lottery_p_win"] / 100

    # Calc if AEX was won
    def calc_aex_won(df):
        return (df["aex_perf"] in df["aex_interval_1"]) or (
            df["aex_perf"] in df["aex_interval_2"]
        )

    choices["aex_won"] = choices.apply(calc_aex_won, axis=1)

    # Calc if overall was won
    choices["won_20_eur"] = False
    choices.loc[choices["choice"] == "AEX", "won_20_eur"] = choices.loc[
        choices["choice"] == "AEX", "aex_won"
    ]
    choices.loc[choices["choice"] == "lot", "won_20_eur"] = choices.loc[
        choices["choice"] == "lot", "lottery_won"
    ]

    # Calc p overall won (without lottery played out)
    choices["p_won_20_eur"] = 0.0
    choices.loc[choices["choice"] == "AEX", "p_won_20_eur"] = choices.loc[
        choices["choice"] == "AEX", "aex_won"
    ].astype(float)
    choices.loc[choices["choice"] == "lot", "p_won_20_eur"] = choices.loc[
        choices["choice"] == "lot", "lot_prob"
    ]
    return choices


def create_ambig_beliefs_basic_files(data_original, file_format):
    """
    Create some basic files that are helpful for all projects using these data.
    """
    data = data_original.copy()

    # ToDo: Update wave spec
    waves_spec = {
        1: {"original_wave": 1, "temperature": False},
        2: {"original_wave": 2, "temperature": False},
        3: {"original_wave": 3, "temperature": False},
        4: {"original_wave": 4, "temperature": False},
        "temp": {"original_wave": 4, "temperature": True},
        5: {"original_wave": 5, "temperature": False},
        6: {"original_wave": 6, "temperature": False},
        7: {"original_wave": 7, "temperature": False},
    }

    waves_to_merge = {
        "event_properties": [],
        "choice_properties": [],
        "choices": [],
        "baseline_matching_probs": [],
        "indices": [],
    }
    for wave in waves_spec:
        ind_wave_spec = waves_spec[wave]
        data_one_wave = data.loc[data["wave"] == ind_wave_spec["original_wave"]]
        data_one_wave = data_one_wave.set_index("personal_id")

        event_properties = clean_event_properties(wave)
        event_properties["wave"] = wave
        waves_to_merge["event_properties"].append(event_properties)

        choice_properties = generate_choice_properties(event_properties, wave)
        choice_properties["wave"] = wave
        waves_to_merge["choice_properties"].append(choice_properties)

        # For temperature wave use temperature questions
        if waves_spec[wave]["temperature"]:
            ambig_cols = [
                c
                for c in data_one_wave.columns
                if c.startswith("event_e") and not c.endswith("_temp")
            ]
            data_one_wave = data_one_wave.drop(ambig_cols, axis=1)
            for c in ambig_cols:
                data_one_wave[c] = data_one_wave[c + "_temp"]

            data_one_wave = data_one_wave.drop(848721)

        temp_cols = [
            c
            for c in data_one_wave.columns
            if c.startswith("event_e") and c.endswith("_temp")
        ]
        data_one_wave = data_one_wave.drop(temp_cols, axis=1)

        choices = generate_choices_df(data_one_wave, choice_properties)
        choices["wave"] = wave
        waves_to_merge["choices"].append(choices)

        baseline_probs = clean_matching_probabilites(choices)
        baseline_probs["wave"] = wave
        waves_to_merge["baseline_matching_probs"].append(baseline_probs)

        indices = clean_indices(baseline_probs["baseline_matching_prob_midp"])
        indices["wave"] = wave
        waves_to_merge["indices"].append(indices)

    # Merge waves
    files = {}
    for description, contents in waves_to_merge.items():
        single_wave_index_cols = list(contents[0].index.names)
        merged_waves_index_cols = (
            [single_wave_index_cols[0]] + ["wave"] + single_wave_index_cols[1:]
        )

        dframe = pd.concat(contents, axis=0, sort=True)
        dframe = dframe.reset_index().set_index(merged_waves_index_cols).sort_index()
        files[description] = dframe

    # Save the files
    for name in files:

        if file_format in ["pickle", "csv"]:
            getattr(files[name], f"to_{file_format}")(
                OUT_DATA_LISS / "ambiguous_beliefs" / f"{name}.{file_format}"
            )
        elif file_format == "dta":
            warnings.warn(
                "dta not supported for ambig-beliefs data files. Exporting as pickle instead."
            )
            files[name].to_pickle(
                OUT_DATA_LISS / "ambiguous_beliefs" / f"{name}.pickle"
            )
    choices_pay_out_info = calc_pay_outs(data_original, files["choices"])
    if file_format in ["pickle", "csv"]:
        getattr(choices_pay_out_info, f"to_{file_format}")(
            OUT_DATA_LISS / "ambiguous_beliefs" / f"choices_pay_out_info.{file_format}"
        )

    elif file_format == "dta":
        choices_pay_out_info.to_pickle(
            OUT_DATA_LISS / "ambiguous_beliefs" / "choices_pay_out_info.pickle"
        )
