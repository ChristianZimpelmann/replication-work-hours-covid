"""Here define which columns to keep from background and covid datasets.

To keep the data_management more readable, there are two lists defined here.

- background_variables: list of column names to keep from the background data
- covid_variables: list of column names to keep from the covid data set.

If you want to add additional variables, do it here.

"""
background_variables = [
    "health_general",
    "home_ownership_status",
    "sector",
    "primary_occupation",
    "job_social",
    # "profession_firstjob",
    "work_home",
    "profession",
    "job_people",
    "job_supervise",
    "job_supervise_number",
    "fin_numeracy",
    "prob_numeracy",
    "basic_numeracy",
    "risk_aversion_index",
    # "wave",
    "housing_part_of_wealth",
    "wealth_hh",
    "home_price_hh",
    "home_remaining_mortgage_hh",
    "wealth_hh_eqv",
    "net_income_hh_eqv",
    "health_group",
]
timevarying_variables = [
    "hh_id",
    "birth_year",
    "age",
    "hh_members",
    "hh_children",
    "hhh_partner",
    "hh_position",
    "dom_situation",
    "civil_status",
    # "occupation",
    "net_income_hh",
    "gross_income_hh",
    "edu",
    "edu_4",
    "gender",
    "female",
    "net_income",
    "gross_income",
    "origin",
]

time_invariant_vars = [
    "cc_self_home",
    "cc_partner_home",
    "cc_older_siblings",
    "cc_grand_parents",
    "cc_other_relatives",
    "cc_share_neighbors",
    "cc_state",
    "cc_ex_partner",
    "cc_home_alone",
    "cc_other",
    "cc_emergency_helpful",
    "nr_children_below_12",
    "comply_curfew_self",
    "essential_worker",
    "children_school",
    "children_not_school",
    # "work_perc_home",
    "work_actual_hours_2019",
    "work_contract_hours_2019",
    "work_actual_hours_2020",
    "work_contract_hours_2020",
]

# Generated variables for 2020
other = ["age_youngest_child"]


covid_vars = [
    "start_date",
    "end_date",
    "comply_curfew_self",
    "nr_children_below_12",
    "cc_self_home",
    "cc_partner_home",
    "cc_older_siblings",
    "cc_grand_parents",
    "cc_other_relatives",
    "cc_share_neighbors",
    "cc_state",
    "cc_ex_partner",
    "cc_home_alone",
    "cc_other",
    "cc_other_str",
    "cc_emergency_helpful",
    "cc_emergency_comment",
    "duration_restrictions_general",
    "hours_workplace",
    "hours_home",
    "empl_not_work_lessbusiness",
    "empl_not_work_infection_empl",
    "empl_not_work_care",
    "empl_not_work_fear_infection",
    "empl_not_work_fired",
    "empl_not_work_other",
    "empl_not_work_other_str",
    "empl_less_work_lessbusiness",
    "empl_less_work_infection_empl",
    "empl_less_work_care",
    "empl_less_work_fear_infection",
    "empl_less_work_other",
    "empl_less_work_other_str",
    "selfempl_less_business",
    "selfempl_less_care",
    "selfempl_less_closure",
    "selfempl_less_other",
    "selfempl_less_other_str",
    "contact_young_people",
    "pensioner_useful_skill",
    "pensioner_prepared_to_help",
    "intend_crisis_save_more",
    "intend_crisis_postpone_purchase",
    "intend_crisis_postpone_house",
    "intend_crisis_reduce_housing",
    "intend_crisis_sell_shares",
    "intend_crisis_buy_shares",
    "intend_crisis_no_action",
    "eur_1k_basic_needs",
    "eur_1k_expenses",
    "eur_1k_durables",
    "eur_1k_savings",
    "eur_1k_support_others",
    "p_low_or_no_income",
    "low_inc_cope_savings",
    "low_inc_cope_loan",
    "low_inc_cope_family",
    "low_inc_cope_unemp",
    "low_inc_cope_retire",
    "low_inc_cope_soc_assist",
    "low_inc_cope_other",
    "low_inc_cope_other_str",
    # "mhi5_7d",
    # "nervous_7d",
    # "depressed_7d",
    # "calm_7d",
    # "gloomy_7d",
    # "happy_7d",
    # "mhi5_month",
    # "nervous_month",
    # "depressed_month",
    # "calm_month",
    # "gloomy_month",
    # "happy_month",
    "concern_4w_bored",
    "concern_4w_serious_ill",
    "concern_4w_infect_others",
    "concern_4w_loved_ill",
    "concern_4w_unemp",
    "concern_4w_company",
    "concern_4w_new_job",
    "concern_4w_food",
    "concern_4w_health_care",
    "concern_4w_fav_shop_bancrupt",
    "duration_econ_crisis",
    "l_12m_job_loss_employee",
    "l_12m_no_contracts_selfempl",
    "l_12m_reduction_pension",
    "l_12m_drop_in_assets",
    "l_12m_bank_bankrupt",
    "l_12m_struggle_repay_debts",
    "e_12m_house_prices_direction",
    "e_12m_house_prices_change",
    "intend_12m_spend_less",
    "intend_12m_work_more",
    "intend_12m_work_less",
    "intend_12m_borrow",
    "intend_12m_postpone_house",
    "p_2m_employee_keep",
    "p_2m_employee_keep_gov",
    "p_2m_employee_lost",
    "p_2m_employee_other",
    "date_fieldwork",
    "p_3m_selfempl_normal",
    "p_3m_selfempl_fewer",
    "p_3m_selfempl_helped_by_gov",
    "p_3m_selfempl_shutdown",
    "p_3m_selfempl_other",
    "p_2m_infected",
    "p_2m_acquaintance_infected",
    "p_2m_hospital_if_infect_self",
    "p_2m_infected_and_pass_on",
    "work_status",
    "change_empl",
    "change_selfempl",
    "work_change_because_corona",
    "month_lost_job",
    "year_lost_job",
    "have_children_prim_school",
    "have_children_sec_school",
    "no_children_prim_sec_school",
    "amount_children_primary",
    "amount_children_sec",
    "e_2m_findoldjob",
    "e_6m_findoldjob",
    "e_2m_findjob",
    "e_6m_findjob",
    "l_findoldjob_rel",
    "impact_corona_findoldjob",
    "finoldjob_wage_rel",
    "e_2m_findcurrentjob",
    "e_6m_findcurrentjob",
    "l_findcurrentjob_rel",
    "impact_corona_findcurrentjob",
    "findcurrentjob_wage_rel",
    "seeking_intensity",
    "job_search_same",
    "no_search_empl_not_lose_job",
    "no_search_empl_not_change_job",
    "no_search_empl_corona",
    "no_search_empl_cant_find_other",
    "no_search_empl_other",
    "no_search_empl_other_str",
    "no_search_study",
    "no_search_household",
    "no_search_incapacitated",
    "no_search_rentier",
    "no_search_retirement",
    "no_search_impact_corona",
    "no_search_cant_find_other",
    "no_search_corona_not_safe",
    "no_search_other",
    "no_search_other_str",
    "reason_seeking_loss_corona",
    "reason_seeking_loss_other",
    "reason_seeking_temporary",
    "reason_seeking_earn_more",
    "reason_seeking_conditions",
    "reason_seeking_side",
    "reason_seeking_less",
    "reason_seeking_more",
    "reason_seeking_unhappy",
    "reason_seeking_security",
    "search_home_home",
    "reason_seeking_other",
    "reason_seeking_other_str",
    "seeking_ad",
    "seeking_placed",
    "seeking_employers",
    "seeking_relatives",
    "seeking_labor",
    "seeking_agency",
    "seeking_internet",
    "seeking_coach",
    "seeking_follow",
    "seeking_other",
    "seeking_none",
    "applied_job",
    "seeking_none_reason",
    "seeking_hours",
    "seeking_wage",
    "job_important_flexible_hours",
    "job_important_salary",
    "job_important_contact",
    "job_important_no_contact",
    "job_important_homeoffice",
    "job_important_security",
    "job_important_travel_time",
    "job_important_transport",
    "p_2m_employee_new_job",
    "p_2m_employee_unemployed",
    "day_off_leisure",
    "day_off_childcare",
    "day_off_other",
    "day_off_sick",
    "day_off_official",
    "work_perc_home",
    "employer_application_now",
    "employer_application_togs",
    "employer_application_deferral",
    "self_application_now",
    "self_application_togs",
    "self_application_deferral",
    "self_application_tozo",
    "self_grekening",
    "self_used_apa",
    "self_used_guarantee",
    "self_used_go",
    "self_used_qredits",
    "self_used_loan_fund",
    "p_employer_application_now3",
    "p_self_application_now3",
    "p_self_application_tozo3",
    "workplace_pot_distance",
    "e_retirement",
    "retire_early_reason",
    "retire_later_reason",
    "p_year_employee_keep",
    "p_year_employee_keep_gov",
    "p_year_employee_new_job",
    "p_year_employee_unemployed",
    "p_year_employee_other",
    "p_year_selfempl_normal",
    "p_year_selfempl_fewer",
    "p_year_selfempl_helped_by_gov",
    "p_year_selfempl_shutdown",
    "p_year_selfempl_other",
    "p_3m_unemployed_job",
    "p_3m_unemployed_educ",
    "p_3m_unemployed_looking",
    "p_3m_unemployed_not_looking",
    "p_3m_unemployed_other",
    "e_pension_cut",
    "e_amount_pension_cut",
    # "activities_give_money",
    # "activities_save_more",
    # "activities_more_care",
    # "activities_less_care",
    # "activities_postpone_doctor",
    # "activities_postpone_hospital",
    # "activities_postpone_pickup_meds",
    # "activities_less_physio",
    # "activities_move_less",
    # "activities_eat_healthy",
    # "activities_lonely",
    "empl_not_work_infection_gov",
    "empl_not_work_sick",
    "empl_not_work_vacation",
    "empl_less_work_infection_gov",
    "empl_less_work_sick",
    "empl_less_work_vacation",
    "empl_less_work_unrel_corona",
    "selfempl_less_infection_gov",
    "selfempl_less_infection_self",
    "selfempl_less_sick",
    "selfempl_less_vacation",
    "selfempl_less_unrel_corona",
    "essential_worker",
    "age_sex_marital_weighting",
    "hours_total",
    "seeking_job",
    "seeking_diff_profession",
    "seeking_diff_profession_str",
    "change_proff_job",
    "change_proff_education",
    "hours_workplace_september",
    "hours_workplace_october",
    "hours_workplace_november",
    "hours_home_september",
    "hours_home_october",
    "hours_home_november",
    "hours_total_september",
    "hours_total_october",
    "hours_total_november",
    "hours_workplace_pre_corona",
    "hours_workplace_expected_post",
    "hours_workplace_preferred_post",
    "hours_home_pre_corona",
    "hours_home_expected_post",
    "hours_home_preferred_post",
    "hours_total_pre_corona",
    "hours_total_expected_post",
    "hours_total_preferred_post",
]