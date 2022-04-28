"""
QUickly debug csv files
"""
import os

import pandas as pd

files = [x for x in os.listdir("specifications") if ".csv" in x and "~lock" not in x]

for x in files:
    df_new = pd.read_csv(f"hy/{x}", sep=";").drop(columns=["new_name"])
    df_old = pd.read_csv(f"specifications/{x}", sep=";").drop(columns=["new_name"])
    try:
        pd.testing.assert_series_equal(df_new["labels"], df_old["labels"])
    except AssertionError:
        print(x)


for x in files:
    print(x)
    try:
        df = pd.read_csv(
            f"specifications/automatically_generated_renaming_files/{x}", sep=";"
        )
    except pd.errors.ParserError:
        df = pd.read_csv(
            f"specifications/automatically_generated_renaming_files/{x}", sep=","
        )
        df_new = pd.read_csv(f"specifications/{x}", sep=";")
        df_new["new_name"] = df["new_name"]
        df_new.to_csv(f"specifications/{x}", sep=";")
    try:
        df.dropna(subset=["new_name"], inplace=True)
    except KeyError:
        df = pd.read_csv(
            f"specifications/automatically_generated_renaming_files/{x}", sep=","
        )
        df_new = pd.read_csv(f"specifications/{x}", sep=";")
        df_new["new_name"] = df["new_name"]
        df_new.to_csv(f"specifications/{x}", sep=";")
