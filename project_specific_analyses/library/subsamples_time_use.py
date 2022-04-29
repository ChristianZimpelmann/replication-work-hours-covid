"""Define subsamples for time-use analysis."""

subsamples = {
    "full": None,
    "parents": "child_school_or_younger == 1",
    "parents_below_12": "child_below_12 == 1",
    "working_parents": "child_school_or_younger ==1 & work_status_baseline.isin(['employed', 'self-employed'])",
    "working_parents_below_12": "child_below_12 == 1 & work_status_baseline.isin(['employed', 'self-employed'])",
    "single_parents": "child_school_or_younger == 1 & (single_parent == 1)",
    "single_parents_below_12": "child_below_12 == 1 & (single_parent == 1)",
    "parents_with_partner": "child_school_or_younger == 1 & (single_parent == 0)",
    "parents_below_12_with_partner": "child_below_12 == 1 & (single_parent == 0)",
    "working_parents_with_partner": "child_school_or_younger ==1 & work_status_baseline.isin(['employed', 'self-employed']) & (single_parent == 0)",
    "working_parents_below_12_with_partner": "child_below_12 == 1 & work_status_baseline.isin(['employed', 'self-employed']) & (single_parent == 0)",
}

subsamples_childcaremix = {
    "full": (
        "(personal_id != 841632 )"
        + "& month.isin(['2020-02-01', '2020-04-01', '2020-11-01'])"
        + "& single_parent == 0"
    ),
    "regression_sample": (
        "month.isin(['2020-02-01', '2020-04-01', '2020-11-01'])"
        + "& youngest_child == 1"
        + "& gender != gender_partner"
        + "& single_parent == 0"
        + "& essential_worker_w2_mother.notnull()"
        + "& essential_worker_w2_father.notnull()"
        + "& (not_working_baseline_mother == 1 | not_working_baseline_father == 1"
        + " | (work_gap_imputed_april.notnull()))"
    ),
}
