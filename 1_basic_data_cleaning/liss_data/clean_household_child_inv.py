import numpy as np


def clean_household_child_inv(data):
    """
    Data cleaning for extra wave data collection 2018 questionnaire.
    """

    # Replace some values
    data = data.replace({"Ja": True, "Nee": False, "ja": True, "nee": False})
    data["prenup"] = data["prenup"].replace(
        {
            "Nee, we zijn niet getrouwd op huwelijkse voorwaarden": False,
            "Ja, we zijn getrouwd op huwelijkse voorwaarden": True,
        }
    )
    data["pot_prenup"] = data["pot_prenup"].replace(
        {
            "waarschijnlijk wel": "probably yes",
            "weet ik nog niet": "not sure yet",
            "waarschijnlijk niet": "probably no",
        }
    )
    data["prenup_divorce"] = data["prenup_divorce"].replace(
        {
            "beperkte gemeenschap van goederen: alles vóór het huwelijk blijft privé. Alle": "lim_community_prop",  # noqa
            "andere vorm van beperkte gemeenschap van goederen, namelijk:": "lim_community_prop_other",  # noqa
            "koude uitsluiting: alle rijkdom en schulden blijven privé-eigendom": "separate_prop",  # noqa
            "algehele gemeenschap van goederen: alle rijkdom en schulden worden gedeeld - ook": "commmunity_prop",  # noqa
            "iets anders, namelijk:": "other",
        }
    )
    data["pot_prenup_divorce"] = data["pot_prenup_divorce"].replace(
        {
            "beperkte gemeenschap van goederen: rijkdom en schulden die u bezat vóór het hu": "lim_community_prop",  # noqa
            "andere vorm van beperkte gemeenschap van goederen, namelijk:": "lim_community_prop_other",  # noqa
            "koude uitsluiting: alle rijkdom en schulden blijven privé-eigendom": "separate_prop",  # noqa
            "algehele gemeenschap van goederen: alle rijkdom en schulden worden gedeeld - ook": "commmunity_prop",  # noqa
            "iets anders, namelijk:": "other",
        }
    )
    data.loc[data["prenup_date"] == " ", "prenup_date"] = data.loc[
        data["prenup_date"] == " ", "marriage_date"
    ]

    data["marriage_year"] = data["marriage_date"].apply(lambda x: x[:4])
    data["marriage_year"] = data["marriage_year"].replace({" ": np.nan}).astype("float")
    data["married_after_2018"] = data["marriage_year"].isin([2018, 2019])

    return data
