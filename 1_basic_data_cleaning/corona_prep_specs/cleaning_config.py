"""
Some configurations!
"""
import numpy as np


BACKGROUND_VARS_IN_CORONA = [
    "hh_id",
    "gender",
    "female",
    "hh_position",
    "birth_year",
    "age",
    "hh_members",
    "hh_children",
    "hhh_partner",
    "civil_status",
    "dom_situation",
    "dwelling_type",
    "location_urban",
    "occupation",
    "gross_income_hh",
    "net_income_hh",
    "education_nodiploma",
    "education_diploma",
    "education_cbs",
    "edu",
    "edu_4",
    "net_income",
    "gross_income",
]

INFORMATION_TREATMENT_VARS_WAVE_2 = [
    "q_information_treatment",
    "hist_perf_e1_nocheck",
    "hist_perf_e3_nocheck",
    "hist_perf_e2_nocheck",
    "hist_perf_e1",
    "hist_perf_e3",
    "hist_perf_e2",
    "hist_perf_e0_nocheck",
    "memory_str",
    "forw_look_e1_nocheck",
    "forw_look_e3_nocheck",
    "forw_look_e2_nocheck",
    "forw_look_e1",
    "forw_look_e3",
    "forw_look_e2",
    "forw_look_e0_nocheck",
    "p_1m_purchase_risky",
    "p_1m_sell_risky",
    "financial_decider",
    "hist_perf_e1_combined",
    "hist_perf_e2_combined",
    "hist_perf_e3_combined",
    "forw_look_e1_combined",
    "forw_look_e2_combined",
    "forw_look_e3_combined",
]

RENAME_EVENING_FRIENDS = {"not applicable": np.nan, "don't know": np.nan}


CAT_EVENING_FRIENDS = [
    "never",
    "about once a year",
    "a number of times per year",
    "about once a month",
    "a few times per month",
    "once or twice a week",
    "almost every day",
]

VARIABLES_TO_DROP = {
    "no_school_sick_prim_child3",
    "no_school_infect_prim_child3",
    "no_school_infect_hh_prim_child3",
    "no_school_exempt_prim_child3",
    "no_school_household_prim_child3",
    "no_school_other_prim_child3",
    "no_school_sick_prim_child4",
    "no_school_infect_prim_child4",
    "no_school_infect_hh_prim_child4",
    "no_school_exempt_prim_child4",
    "no_school_household_prim_child4",
    "no_school_other_prim_child4",
    "no_school_sick_prim_child5",
    "no_school_infect_prim_child5",
    "no_school_infect_hh_prim_child5",
    "no_school_exempt_prim_child5",
    "no_school_household_prim_child5",
    "no_school_other_prim_child5",
    "school_start_thu_sec_child3",
    "school_start_fr_sec_child3",
    "school_end_thu_sec_child3",
    "school_end_fr_sec_child3",
    "no_school_sick_sec_child3",
    "no_school_infect_sec_child3",
    "no_school_infect_hh_sec_child3",
    "no_school_exempt_sec_child3",
    "no_school_household_sec_child3",
    "no_school_other_sec_child3",
    "school_start_mo_sec_child4",
    "school_start_tue_sec_child4",
    "school_start_wed_sec_child4",
    "school_start_thu_sec_child4",
    "school_start_fr_sec_child4",
    "school_end_mo_sec_child4",
    "school_end_tue_sec_child4",
    "school_end_wed_sec_child4",
    "school_end_thu_sec_child4",
    "school_end_fr_sec_child4",
    "not_mo_sec_child4",
    "not_tue_sec_child4",
    "not_wed_sec_child4",
    "not_thu_sec_child4",
    "not_fr_sec_child4",
    "no_school_sick_sec_child4",
    "no_school_infect_sec_child4",
    "no_school_infect_hh_sec_child4",
    "no_school_exempt_sec_child4",
    "no_school_household_sec_child4",
    "no_school_other_sec_child4",
    "school_start_mo_sec_child5",
    "school_start_tue_sec_child5",
    "school_start_wed_sec_child5",
    "school_start_thu_sec_child5",
    "school_start_fr_sec_child5",
    "school_end_mo_sec_child5",
    "school_end_tue_sec_child5",
    "school_end_wed_sec_child5",
    "school_end_thu_sec_child5",
    "school_end_fr_sec_child5",
    "not_mo_sec_child5",
    "not_tue_sec_child5",
    "not_wed_sec_child5",
    "not_thu_sec_child5",
    "not_fr_sec_child5",
    "no_school_sick_sec_child5",
    "no_school_infect_sec_child5",
    "no_school_infect_hh_sec_child5",
    "no_school_exempt_sec_child5",
    "no_school_household_sec_child5",
    "no_school_other_sec_child5",
}
