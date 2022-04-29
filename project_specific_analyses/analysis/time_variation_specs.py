"""Define groups to split the time variation plots
"""
time_variation_groups = {
    "None": {"group": None, "label_rename_dict": {}, "create_unempl_rate": True},
    "abs_change_hours_uncond_avg_0304_groups": {
        "group": "abs_change_hours_uncond_avg_0304_groups",
        "label_rename_dict": {},
        "query": "not_working_baseline == 0",
        "create_unempl_rate": True,
        "legend_title": "\navg. change working hours March/April",
        "ylim_change_hours": (-33, 5),
        "ylim_not_working": (0, 0.175),
    },
    "gender": {
        "group": "gender",
        "label_rename_dict": {},
        "create_unempl_rate": True,
    },
    "self_employed_baseline": {
        "group": "self_employed_baseline",
        "label_rename_dict": {
            "0.0": "employed",
            "1.0": "self-employed",
        },
        "create_unempl_rate": False,
    },
    "edu": {
        "group": "edu",
        "label_rename_dict": {
            "lower_secondary_and_lower": "lower sec. & less",
            "upper_secondary": "upper sec.",
            "tertiary": "tertiary",
        },
        "create_unempl_rate": True,
        "ylim_rel_change_hours": (-0.3, 0),
        "ylim_change_hours_home": (-2, 20),
    },
    "work_perc_home_cat_only_ess": {
        "group": "work_perc_home_cat",
        "create_unempl_rate": False,
        "query": "essential_worker_w2 == 1",
        "ylim_change_hours": (-12, 0),
        "ylim_rel_change_hours": (-0.4, 0.05),
        "ylim_change_hours_home": (-2, 25),
        "legend_title": "perc. work doable from home",
    },
    "work_perc_home_cat_only_noness": {
        "group": "work_perc_home_cat",
        "create_unempl_rate": False,
        "query": "essential_worker_w2 == 0",
        "ylim_change_hours": (-12, 0),
        "ylim_rel_change_hours": (-0.4, 0.05),
        "ylim_change_hours_home": (-2, 25),
        "legend_title": "perc. work doable from home",
    },
    "gross_income_groups_full": {
        "group": "gross_income_groups",
        "label_rename_dict": {},
        "create_unempl_rate": True,
        "ylim_rel_change_hours": (-0.3, 0),
        "ylim_change_hours_home": (-2, 20),
    },
    "ever_affected_by_policy_selfempl": {
        "group": "ever_affected_by_policy",
        "create_unempl_rate": False,
        "query": "self_employed_baseline == 1 and not_working_baseline == 0",
        "ylim_change_hours": (-23, 0),
        "ylim_rel_change_hours": (-0.6, 0),
    },
    "ever_affected_by_policy_empl_str": {
        "group": "ever_affect_by_policy_str",
        "create_unempl_rate": False,
        "query": "self_employed_baseline == 0 and not_working_baseline == 0",
        "ylim_change_hours": (-23, 0),
        "ylim_rel_change_hours": (-0.6, 0),
    },
    "net_income_2y_equiv_q": {
        "group": "net_income_2y_equiv_q",
        "label_rename_dict": {},
        "create_unempl_rate": True,
        "query": "hours_baseline >= 30",
    },
    "net_income_2y_equiv_q3": {
        "group": "net_income_2y_equiv_q3",
        "label_rename_dict": {},
        "create_unempl_rate": True,
        "query": "hours_baseline >= 30",
    },
    "net_income_2y_equiv_q3_full": {
        "group": "net_income_2y_equiv_q3",
        "label_rename_dict": {},
        "create_unempl_rate": True,
    },
}
