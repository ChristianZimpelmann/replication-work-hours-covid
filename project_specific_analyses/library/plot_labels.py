"""Define labels for plots."""
import json

import pandas as pd

from output.project_paths import project_paths_join as ppj

labels = {
    "hours_childcare_total": "total childcare",
    "hours_childcare_total_strict": "childcare & homeschooling",
    "hours_work_total": "working",
    "hours_chores": "chores",
    "hours_childcare": "other childcare",
    "hours_workplace": "workplace",
    "hours_home_office_no_kids": "home office",
    "hours_home_office_kids_care": "home office + childcare",
    "hours_homeschooling": "homeschooling",
    "hours_leisure": "other leisure",
    "hours_leisure_alone": "leisure, alone",
    "hours_leisure_friends": "leisure, friends",
    "hours_commute": "commute",
    "hours_help_parents": "help parents",
    "hours_help_family": "help other familty",
    "hours_help_other": "other",
    "hours_schooling": "schooling",
    "hours_other_activity": "other activities",
    "hours_resting": "resting, sleeping",
    "hours_cc_young_self": "self",
    "hours_cc_young_partner": "partner",
    "hours_cc_young_gp": "grandparents",
    "hours_cc_young_siblings": "siblinngs",
    "hours_cc_young_otherfam": "other family",
    "hours_cc_young_daycare": "host parents/daycare",
    "hours_cc_young_careparents": "care parents",
    "hours_cc_young_kg": "kindergarden",
    "hours_cc_young_friends": "friends/neighbors/other parents",
    "hours_cc_young_bs": "babysitter or au-pair",
    "hours_cc_young_other": "other",
    "hours_cc_self": "self",
    "hours_cc_partner": "partner",
    "hours_cc_gp": "grandparents",
    "hours_cc_siblings": "siblinngs",
    "hours_cc_otherfam": "other family",
    "hours_cc_school": "school",
    "hours_cc_schoolcare": "after school care",
    "hours_cc_careparents": "nursery",
    "hours_cc_daycare": "host parents/daycare",
    "hours_cc_friends": "friends/neighbors/other parents",
    "hours_cc_bs": "babysitter/ au-pair",
    "hours_cc_other": "other",
    "hours_cc_nobody": "nobody",
    "hours_cc_young_female": "mother",
    "hours_cc_young_male": "father",
    "hours_cc_female": "mother",
    "hours_cc_male": "father",
    "hours_cc_only_female": "mother",
    "hours_cc_only_male": "father",
    "hours_cc_formal_care": "formal care",
    "hours_cc_young_formal_care": "formal care",
    "hours_formal_care": "formal care",
    "hours_cc_expartner_alt": "ex-partner",
    "hours_cc_partner_alt": "partner",
    "hours_cc_total": "total childcare hours",
    "hours_cc_kg": "kindergarden",
    "hours_leisure_total": "leisure",
    "hours_workplace_tu": "workplace",
    "hours_work": "working hours",
    "market_hours": "market work",
    "non_market_hours": "non-market work",
    "hours_work_total_strict": "working hours",
    "hours_help_total": "help others",
}

time_labels_raw = {
    "2019-11-01": "nov. 2019",
    "2020-02-01": "before Covid-19",
    "2020-03-01": "march 2020",
    "2020-04-01": "april 2020",
    "2020-05-01": "may 2020",
    "2020-06-01": "june 2020",
    "2020-07-01": "july 2020",
    "2020-08-01": "august 2020",
    "2020-09-01": "september 2020",
    "2020-10-01": "october 2020",
    "2020-11-01": "november 2020",
    "2020-12-01": "december 2020",
}
time_labels = {
    **time_labels_raw,
    **{pd.to_datetime(k): v for k, v in time_labels_raw.items()},
}

time_labels_no_year_raw = {
    "2020-02-01": "before Covid-19",
    "2020-03-01": "late march",
    "2020-04-01": "april",
    "2020-05-01": "may",
    "2020-06-01": "june",
    "2020-07-01": "july",
    "2020-08-01": "august",
    "2020-09-01": "september",
    "2020-10-01": "october",
    "2020-11-01": "november",
    "2020-12-01": "december",
}
time_labels_no_year = {
    **time_labels_no_year_raw,
    **{pd.to_datetime(k): v for k, v in time_labels_no_year_raw.items()},
}

time_labels_short_no_year_raw = {
    "2020-02-01": "before Covid-19",
    "2020-03-01": "Mar",
    "2020-04-01": "Apr",
    "2020-05-01": "May",
    "2020-06-01": "Jun",
    "2020-07-01": "Jul",
    "2020-08-01": "Aug",
    "2020-09-01": "Sep",
    "2020-10-01": "Oct",
    "2020-11-01": "Nov",
    "2020-12-01": "Dec",
}
time_labels_short_no_year = {
    **time_labels_short_no_year_raw,
    **{pd.to_datetime(k): v for k, v in time_labels_short_no_year_raw.items()},
}


months_raw_dict = {
    "": "",
    "March_April": "march/april",
    "May": "may",
    "June": "june",
    "March_June": "march-june",
    "September": "september",
    "December": "december",
    "September_December": "september/december",
}

months_dict = {
    "": "",
    "March_April:": "march/april $\times$ ",
    "May:": "may $\times$ ",
    "June:": "june $\times$ ",
    "March_June:": "march-june $\times$ ",
    "September:": "september $\times$ ",
    "December:": "december $\times$ ",
    "September_December:": "september/december $\times$ ",
}

reg_vars = {
    "applied_any_policy_any": "affected by support program",
    "applied_any_policy_05": "affected by support program",
    "applied_any_policy": "affected by support program",
    "ever_affect_by_policy_str_Affected by policy": "affected by policy: yes",
    "ever_affect_by_policy_str_Never affected by policy": "affected by policy: no",
    "ever_affect_by_policy_str_Don't know": "affected by policy: don't know",
    "application_now_yes_05": "affected by NOW",
    "application_togs_yes_05": "affected by TOGS",
    "application_now_togs_yes_05": "affected by NOW or TOGS",
    "application_deferral_yes_05": "affected by tax deferral",
    "p_2m_employee_keep_gov": "likeli. employed \\& gov. intervention",
    "p_2m_employee_lost": "likeli. lost current job",
    "p_2m_employee_other": "likeli. other",
    "hours_uncond_baseline": "working hours pre-Covid",
    "abs_change_hours_uncond": "change working hours",
    "abs_change_hours_uncond_03": "change hours March",
    "abs_change_hours_uncond_avg_0304": "avg. hours change march/april",
    "abs_change_hours_uncond_avg_0305": "avg. change hours March, April, May",
    "abs_change_hours_uncond_05": "change hours May",
    "abs_change_hours_uncond_09": "change hours September",
    "abs_change_hours_uncond:self_employed_baseline": "change hours $\times$ self-employed",
    "abs_change_hours_uncond_03:self_employed_baseline": "change hours $\times$ self-employed",
    "hours_total_uncond": "working hours",
    "hours_home_uncond": "hours worked from home",
    "home_share": "share of hours worked from home",
    "unemployed": "unemployed",
    "out_of_laborf": "out of laborforce",
    "unemployed_baseline": "unemployed pre-Covid",
    "out_of_laborf_baseline": "out of laborforce pre-Covid",
    "age": "age",
    "nr_children_below_12": "no. children below 12",
    "p_2m_employee_lost_baseline": "likeli. lost job in March",
    "p_2m_lost_baseline": "likeli. loose job/shutdown company",
    "fulltime_baseline_covid[T.True]": "fulltime",
    "female": "female",
    "edu[T.upper_secondary]": "education: upper sec.",
    "edu[T.tertiary]": "education: tertiary",
    "edu_lower_secondary_and_lower": "education: lower sec. and below",
    "edu_upper_secondary": "education: upper secondary",
    "edu_tertiary": "education: tertiary",
    "gross_income_groups[T.bet. 2500 and 3500]": "income bet. 2500 and 3500",
    "gross_income_groups[T.above 3500]": "income above 3500",
    "gross_income_groups_below 2500": "gross income: below 2500",
    "gross_income_groups_bet. 2500 and 3500": "gross income: bet. 2500 and 3500",
    "gross_income_groups_above 3500": "gross income: above 3500",
    "gross_income": "gross income",
    "net_income_2y_equiv": "net hh income 18/19 (equiv)",
    "C(net_income_2y_equiv_q)[T.2.0]": "net hh income 18/19 Q2",
    "C(net_income_2y_equiv_q)[T.3.0]": "net hh income 18/19 Q3",
    "C(net_income_2y_equiv_q)[T.4.0]": "net hh income 18/19 Q4",
    "C(net_income_2y_equiv_q)[T.5.0]": "net hh income 18/19 Q5",
    "C(net_income_2y_equiv_q3)[T.2.0]": "net hh income 18/19 Q2",
    "C(net_income_2y_equiv_q3)[T.3.0]": "net hh income 18/19 Q3",
    "employed_baseline": "employed pre-Covid",
    "self_employed_baseline": "self-employed pre-Covid",
    "self-employed_baseline": "self-employed pre-Covid",
    "parttime_baseline_covid": "part time pre-Covid",
    "C(work_status_spec_baseline, Treatment('full time'))[T.part time]": "part time pre-Covid",
    "C(work_status_spec_baseline, Treatment('full time'))[T.self-employed]": "self-employed pre-Covid",
    "C(work_status_spec_baseline, Treatment('full time'))[T.not working]": "not working pre-Covid",
    "work_status_spec_baseline_part time": "part time employed pre-Covid",
    "work_status_spec_baseline_self-employed": "self-employed pre-Covid",
    "work_status_spec_baseline_full time": "full time employed pre-Covid",
    "work_status_spec_baseline_not working": "not working pre-Covid",
    "C(work_status_spec_short_baseline, Treatment('full time'))[T.part time]": "part time pre-Covid",
    "C(work_status_spec_short_baseline, Treatment('full time'))[T.self-employed]": "self-employed pre-Covid",
    "work_status_spec_short_baseline_part time": "part time employed pre-Covid",
    "work_status_spec_short_baseline_self-employed": "self-employed pre-Covid",
    "work_status_spec_short_baseline_full time": "full time employed pre-Covid",
    "age_groups[T.36-55]": "age: between 36 and 55",
    "age_groups[T.above 55]": "age: above 55",
    "hhh_partner": "has partner",
    "married": "married ",
    "child_below_12": "child below 12",
    "essential_worker_w2": "essential worker",
    "essential_worker": "essential worker (alt. def)",
    "work_perc_home": "frac. work doable from home",
    "essential_worker_w2:work_perc_home": "essential $\\times$ work doable from home",
    "essential_worker:work_perc_home": "essential $\\times$ work doable from home",
    "profession[T.other office]": "prof.: other office",
    "profession[T.intermediate supervisory/academic]": "prof.: interm. superv./academic",
    "profession[T.higher supervisory/academic]": "prof.: higher superv./academic",
    "reason_lost_job_baseline": "lost job",
    "reason_closure_baseline": "closure",
    "reason_less_business_baseline": "less business",
    "reason_care_baseline": "care",
    "reason_unrel_corona_baseline": "unrelated to corona",
    "reason_fear_infection_baseline": "fear of infection",
    "sector[T.construction]": "sector: construction",
    "sector[T.education]": "sector: education",
    "sector[T.env., culture, recr.]": "sector: env., culture, recr.",
    "sector[T.financial & business services]": "sector: financial \\& business services",
    "sector[T.healthcare & welfare]": "sector: healthcare \\& welfare",
    "sector[T.industry]": "sector: industry",
    "sector[T.other]": "sector: other",
    "sector[T.public services]": "sector: public services",
    "sector[T.retail]": "sector: retail",
    "sector[T.transport, communication, & utilities]": "sector: transport, communication, \\& utilities",
}

regressor_order = (
    [
        "Intercept",
    ]
    + [m for m in months_raw_dict]
    + [f"{m}{v}" for v in reg_vars for m in months_dict]
    + [
        "N",
        "$R^2$",
        "R-squared",
    ]
)

index_to_table = {
    **{
        f"{m}{v}": f"{months_dict[m]}{reg_vars[v]}"
        for v in reg_vars
        for m in months_dict
    },
    **months_raw_dict,
}

dep_vars_dict = {
    "unemployed_after_may": "unemployed in May or June",
    "abs_change_hours_uncond": "change total working hours",
    "abs_change_hours_tu_uncond": "change total working hours",
    "rel_change_hours_uncond": "change total working hours",
    "rel_change_hours_tu_uncond": "change total working hours",
    "unemployed": "unemployed",
    "not_working": "no job",
    "parttime_baseline": "part time pre-Covid",
    "out_of_laborf": "out of the laborforce",
    "abs_change_hours_home_uncond": "change hours worked from home",
    "rel_change_hours_home_uncond": "change hours worked from home",
    "applied_any_policy_any": "affected by any support policy",
    "applied_any_policy_05": "affected by any support policy",
    "application_now_yes": "affected by NOW",
    "application_togs_yes": "affected by TOGS",
    "application_deferral_yes": "affected by tax deferral",
    "p_2m_employee_keep_gov": r"\shortstack{likeli. employed \\ \& gov. intervention}",
    "p_2m_employee_unemployed": "likeli. unemployed",
    "p_2m_lost_job": "expected job loss prob.",
    "concern_4w_job": "concerned about job",
    "not_working_after_may": "not working in May or June",
    "not_working_after_may_perc": r"not working in May or June (\%)",
    "participated_next": "participated in next wave",
    "participated": "participated",
    "p_year_lost_job": "expected job loss prob. (May)",
    "concern_4w_job_may": "concerned about job (May)",
    "change_hh_income": "change household income",
    "change_net_income_hh": "change household income",
}

# ToDo: Remove I's before
column_to_table = {
    **dep_vars_dict,
    **{v + " " + "I" * i: nv for v, nv in dep_vars_dict.items() for i in range(1, 10)},
    **{
        "count": "N",
        "std": "std. dev.",
        "10%": "$q_{0.1}$",
        "50%": "$q_{0.5}$",
        "90%": "$q_{0.9}$",
        "25%": "$q_{0.25}$",
        "50%": "$q_{0.5}$",
        "75%": "$q_{0.75}$",
    },
}

labels_gender_childcare = {
    "labor_force": "labor force status (pre-Covid)",
    "parttime_baseline": "part-time (pre-Covid)",
    "fulltime_baseline": "full-time (pre-Covid)",
    "work_perc_home": "frac. work doable from home",
    "essential_worker_w2": "essential worker",
    "essential_worker": "essential worker",
    "child_school_or_younger": "has children (living at HH)",
    "self_employed_baseline": "self-employed (pre-Covid)",
    "age_groups": "age ",
    "eduupper_secondary": "Upper secondary edu.",
    "edutertiary": "Tertiary edu.",
    "out_of_laborf_baseline": "out of the labor force (pre-Covid)",
    "work_gap": "male-female work gap",
    "March_April": "March/April",
    "hours_total_uncond": "hours worked (pre-Covid)",
    "single_parent": "single",
    "has_partner": "has partner",
    "less_care_comb": "reduced for care ",
    "reason_lost_job_baseline": "lost job",
    "reason_closure_baseline": "closure",
    "reason_less_business_baseline": "less business",
    "reason_care_baseline": "care",
    "reason_fear_infection_baseline": "fear of infection",
    "reason_unrel_corona_baseline": "unrelated to corona",
    "reason_other_baseline": "other",
    "reason_lost_job_march": "lost job",
    "reason_closure_march": "closure",
    "reason_less_business_march": "less business",
    "reason_care_march": "care",
    "reason_fear_infection_march": "fear of infection",
    "reason_unrel_corona_march": "unrelated to corona",
    "reason_other_march": "other",
    "reason_lost_job_april": "lost job",
    "reason_closure_april": "closure",
    "reason_less_business_april": "less business",
    "reason_care_april": "care",
    "reason_fear_infection_april": "fear of infection",
    "reason_unrel_corona_april": "unrelated to corona",
    "reason_other_april": "other",
    "not_working_baseline": "not working",
}
labels_gender_childcare.update(labels)
labels_parents = {
    f"{k}_mother": f"mother: {labels_gender_childcare[k]}"
    for k in labels_gender_childcare
    if k != "March_April"
}
labels_father = {
    f"{k}_father": f"father: {labels_gender_childcare[k]}"
    for k in labels_gender_childcare
    if k != "March_April"
}

labels_parents.update(labels_father)
labels_parents.update(
    {
        "March_April": "March/April",
        "work_gap": "Male-female work gap",
        "less_care_comb": "reduced for care ",
        "_imputed_april": "",
    }
)

industry_ger = {
    "public services": "Öffentlicher Dienst",
    "env., culture, recr.": "Kultur und Tourismus",
    "catering": "Gastronomie",
    "healthcare & welfare": "Gesundheits- und Sozialwesen",
    "other": "Sonstige",
    "retail": "Einzelhandel",
    "financial & business services": "Finanz- und Unternehmensdienstl.",
    "transport, communication, & utilities": "Verkehr und Kommunikation",
    "education": "Bildung",
    "industry": "Industrie",
    "construction": "Bau",
}

month_ger = {
    "before \n Covid-19": "vor CoViD-19",
    "march": "März",
    "late March": "Ende März",
    "april": "April",
    "march_april": "März/April",
    "April": "April",
    "may": "Mai",
    "May": "Mai",
    "june": "Juni",
    "June": "Juni",
    "september": "September",
    "September": "September",
    "december": "Dezember",
    "December": "Dezember",
}

if __name__ == "__main__":

    with open(ppj("OUT_DATA", "labels_gender_childcare.json"), "w") as json_file:
        json.dump(labels_gender_childcare, json_file)

    with open(ppj("OUT_DATA", "labels_parents.json"), "w") as json_file:
        json.dump(labels_parents, json_file)
