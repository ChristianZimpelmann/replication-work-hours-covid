import numpy as np


def clean_consumer_outlook(data):
    """
    Data cleaning for consumer outlook
    """

    for c in [
        "economy_development_past",
        "economy_development_future",
        "hh_development_past",
        "hh_development_future",
    ]:
        data[c] = (
            data[c]
            .replace(
                {
                    "clearly get worse": 1,
                    "get a bit worse": 2,
                    "stay the same": 3,
                    "get a bit better": 4,
                    "clearly get better": 5,
                    "clearly gotten worse": 1,
                    "gotten a bit worse": 2,
                    "stayed the same": 3,
                    "gotten a bit better": 4,
                    "clearly gotten better": 5,
                    "clearly got worse": 1,
                    "got a bit worse": 2,
                    "stayed the same": 3,
                    "got a bit better": 4,
                    "clearly got better": 5,
                    "I don\x92t know": np.nan,
                    "I don't know": np.nan,
                }
            )
            .astype(float)
        )
    return data
