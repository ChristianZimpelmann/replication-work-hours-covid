"""Include background data from other years into datasets.

Currently from 2019-11-01.

Generates additional child indicators because of inconsistencies across waves.

"""
import pandas as pd

from output.project_paths import project_paths_join as ppj
from project_specific_analyses.data_management.variables_to_keep import (
    timevarying_variables,
)


def clean_other_background_data(background_year, months, variables):
    """Clean additional monthly background data for merge.

    This is particularly designed for the 2019 background data.
    It might need adjustment for other years.

    Args:
        background_year (DataFrame): full background data from a particular years.
        months (list): list of months to select the data from.
        variables (list): list of variables that are selected.

    Return:

    """
    background = background_year.reset_index().copy()

    # Transform index in timestamp
    def makedatetime(date_fieldwork):
        date = str(int(date_fieldwork))
        year = date[0:4]
        month = date[4:6]
        if month.startswith("0"):
            month = month.replace("0", "")

        return pd.Timestamp(year=int(year), month=int(month), day=1)

    background["month"] = background["date_fieldwork"].apply(makedatetime)

    # Set index and select months
    out = background.set_index(["personal_id", "month"]).query("month.isin(@months)")

    return out[variables + ["occupation"]]


def clean_employment_status(background):
    """Generate employment status variable and drop occupation."""
    background = background.copy()

    # Value replacement
    trans_dict = {
        "Performs unpaid work while retaining unemployment benefit": "unemployed",
        "Paid employment": "employed",
        "Autonomous professional, freelancer, or self-employed": "self-employed",
        "Is pensioner ([voluntary] early retirement, old age pension scheme)": "retired",
        "Performs voluntary work": "other",
        "Attends school or is studying": "student or trainee",
        "Takes care of the housekeeping": "homemaker",
        "Has (partial) work disability": "other",
        "Works or assists in family business": "self-employed",
        "Is too young to have an occupation": "other",
        "Job seeker following job loss": "unemployed",
        "Does something else": "other",
        "First-time job seeker": "unemployed",
        "Exempted from job seeking following job loss": "other",
    }

    background["work_status"] = background["occupation"].replace(to_replace=trans_dict)
    background.drop("occupation", axis=1, inplace=True)

    return background


def generate_age_youngest_child(background):
    """Generate age of youngest child."""
    background = background.reset_index().copy()

    temp = (
        background.query("(hh_position == 'Child living at home')")
        .copy()[["age", "hh_id", "month"]]
        .groupby(["hh_id", "month"])
        .min()
    )
    temp = temp.rename(columns={"age": "age_youngest_child"}).reset_index()

    background = pd.merge(background, temp, on=["hh_id", "month"], how="left")

    return background.set_index(["personal_id", "month"])


def generate_additional_variables(background):
    """Generate additional variables."""
    background = background.copy()

    background = generate_age_youngest_child(background)
    background = clean_employment_status(background)

    return background


if __name__ == "__main__":
    background_2019 = pd.read_pickle(
        ppj("IN_DATA", "unmerged_files/background_full_2019.pickle")
    )
    months = ["2019-11-01"]
    variables = timevarying_variables
    background = clean_other_background_data(background_2019, months, variables)
    background = generate_additional_variables(background)

    # Save data
    background.to_parquet(ppj("OUT_DATA", "background_2019.parquet"))
