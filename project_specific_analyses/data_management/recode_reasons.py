import numpy as np


def recode_reasons_for_other_responses(df):

    # create new variables
    df["empl_less_work_fired"] = np.nan

    ##########################
    # Employee -- not working
    ##########################

    #   fired/resigned/contract not prolonged, excemption unit termination of contract [883517]
    for i in [
        853317,
        862933,
    ]:
        df.loc[(i, "2020-03-01"), "empl_not_work_fired"] = 1
    for i in [
        854101,
        812375,
        835010,
        835183,
        846792,
        858865,
        862933,
        863649,
        879925,
        835415,
        853317,
        883517,
        866241,
        888642,
    ]:
        df.loc[(i, "2020-04-01"), "empl_not_work_fired"] = 1

    #   less business activity with no additional info, working on voluntary basis [861701]
    for i in [853695, 865997, 876633, 877882, 897653, 808794]:
        df.loc[(i, "2020-03-01"), "empl_not_work_lessbusiness"] = 1
    for i in [877882, 861557, 861701, 808794, 898237]:
        df.loc[(i, "2020-04-01"), "empl_not_work_lessbusiness"] = 1

    #   out of laborf: retired/student/maternity leave etc etc.
    for i in [
        822763,
        846286,
        848732,
        808712,
        819482,
        842510,
        877139,
        811627,
        834326,
        835415,
        834326,
        835415,
    ]:
        df.loc[(i, "2020-03-01"), "empl_not_work_out_of_laborf"] = 1
    for i in [
        802960,
        822763,
        841632,
        877139,
        848732,
        808712,
        842510,
        851037,
        819482,
        878222,
        811309,
        811627,
        813858,
        811920,
        889983,
    ]:
        df.loc[(i, "2020-04-01"), "empl_not_work_out_of_laborf"] = 1

    #   vacation, taking a break
    for i in [
        813290,
        813885,
        827601,
        836657,
        839581,
        847989,
        867172,
        876882,
        880725,
        888411,
        891567,
    ]:
        df.loc[(i, "2020-03-01"), "empl_not_work_vacation"] = 1
    for i in [809579, 813885, 827601, 829112, 835479, 837068, 891567]:
        df.loc[(i, "2020-04-01"), "empl_not_work_vacation"] = 1

    #   sick, injured icl: burn out, stroke, fatigue[825886, 879492], symptoms
    for i in [
        807891,
        811196,
        811298,
        814645,
        813290,
        814645,
        820779,
        821221,
        821441,
        823449,
        812860,
        817483,
        828067,
        830993,
        831414,
        833317,
        835231,
        835791,
        835894,
        838424,
        843325,
        843582,
        845675,
        852175,
        852499,
        852636,
        846450,
        846792,
        848748,
        849139,
        850317,
        851306,
        850531,
        855532,
        867367,
        871103,
        875140,
        876633,
        878115,
        879306,
        879492,
        881832,
        883712,
        885373,
        888217,
        879352,
        890323,
        891101,
        891461,
        893814,
        895825,
        897369,
        898028,
        898498,
        898856,
        898935,
    ]:
        df.loc[(i, "2020-03-01"), "empl_not_work_sick"] = 1
    for i in [818533, 825886, 822705, 833786, 852175, 848968, 885373, 890949, 891101]:
        df.loc[(i, "2020-04-01"), "empl_not_work_sick"] = 1

    #   care, family care, family-circumstances
    for i in [
        814868,
        815219,
    ]:
        df.loc[(i, "2020-03-01"), "empl_not_work_care"] = 1
    for i in [861740]:
        df.loc[(i, "2020-04-01"), "empl_not_work_care"] = 1

    #   risk of infection

    for i in [841903, 856387, 874060, 896334]:
        df.loc[(i, "2020-03-01"), "empl_not_work_fear_infection"] = 1
    for i in [841903, 874060]:
        df.loc[(i, "2020-04-01"), "empl_not_work_fear_infection"] = 1

    # Government closure
    for i in [
        809814,
        816680,
        861758,
        802761,
        806729,
        844467,
        811768,
        839960,
        847241,
        855649,
        830185,
        845867,
        856072,
        869674,
        875937,
        887750,
        890942,
        892105,
        893502,
        895242,
        896536,
    ]:
        df.loc[(i, "2020-03-01"), "empl_not_work_infection_gov"] = 1
    for i in [889983, 855649]:
        df.loc[(i, "2020-04-01"), "empl_not_work_infection_gov"] = 1

    ##########################
    # Employee -- less working
    ##########################

    #   sick, in pain, injured, concentration issues, stress, pregnancy, mandatory quarantaine etc.
    for i in [
        800085,
        801004,
        810302,
        819143,
        837167,
        844953,
        846782,
        851425,
        853521,
        854101,
        859776,
        861322,
        861471,
        867197,
        871362,
        871554,
        876294,
        877169,
        877761,
        878265,
        878271,
        880913,
        883202,
        884341,
        881884,
        882260,
        888272,
        890706,
        897058,
    ]:
        df.loc[(i, "2020-03-01"), "empl_less_work_sick"] = 1
    for i in [820748, 840930, 847743, 892878]:
        df.loc[(i, "2020-04-01"), "empl_less_work_sick"] = 1

    #   vacation
    for i in [801626, 825964, 844042, 851535, 855752, 858667, 865890, 891006]:
        df.loc[(i, "2020-03-01"), "empl_less_work_vacation"] = 1
    for i in [815125, 843724, 854495, 861111, 874652]:
        df.loc[(i, "2020-04-01"), "empl_less_work_vacation"] = 1

    #   non covid related: national holidays, mistakes, retirement, moving, passing of relative
    for i in [801373, 804925, 805858, 802340, 845199, 854208, 835818, 881091]:
        df.loc[(i, "2020-03-01"), "empl_less_work_unrel_corona"] = 1
    for i in [
        804455,
        810990,
        811369,
        816052,
        808195,
        820181,
        827566,
        831912,
        832408,
        842898,
        844425,
        824478,
        833249,
        863435,
        875622,
        875772,
        884350,
        887826,
        891097,
        891890,
        892718,
        895633,
        896276,
        892969,
        839990,
    ]:
        df.loc[(i, "2020-04-01"), "empl_less_work_unrel_corona"] = 1

    # fear : risk-group, work spreading to avoid contact, avoiding cross-contamination
    for i in [816052, 809887, 802999, 843469, 843945, 877661, 880737, 885641, 899407]:
        df.loc[(i, "2020-03-01"), "empl_less_work_fear_infection"] = 1
    for i in [832052, 838959, 875204, 885809]:
        df.loc[(i, "2020-04-01"), "empl_less_work_fear_infection"] = 1

    # lessbusiness :    working at home is not possible (yet) [804000],
    #                   previous week very busy (due to corona-precautions),
    #                   efficiency gain, requested to use vacation days
    for i in [
        804000,
        805444,
        808279,
        808551,
        814947,
        818234,
        820660,
        819891,
        820846,
        822002,
        826065,
        826294,
        829112,
        831631,
        834690,
        839154,
        839382,
        841526,
        841775,
        843869,
        844924,
        844949,
        850942,
        851596,
        855255,
        858464,
        858691,
        854937,
        860317,
        860922,
        899673,
        867700,
        872616,
        875473,
        879244,
        880510,
        880512,
        899511,
        899462,
        894503,
        899407,
    ]:
        df.loc[(i, "2020-03-01"), "empl_less_work_lessbusiness"] = 1
    for i in [
        804284,
        806460,
        807546,
        808346,
        812399,
        819549,
        822271,
        826118,
        829293,
        832614,
        841526,
        830679,
        840023,
        846535,
        853091,
        853564,
        899794,
        828952,
        825634,
        852545,
        852645,
        855203,
        855255,
        855564,
        821212,
        860287,
        851821,
        860287,
        861681,
        862899,
        865902,
        866833,
        870176,
        870964,
        871034,
        875808,
        879675,
        883650,
        886904,
        888167,
        879796,
        896179,
    ]:
        df.loc[(i, "2020-04-01"), "empl_less_work_lessbusiness"] = 1

    #   care
    for i in [814324]:
        df.loc[(i, "2020-03-01"), "empl_less_work_care"] = 1
    for i in [879943]:
        df.loc[(i, "2020-04-01"), "empl_less_work_care"] = 1

    #   less work due to governmet intervention
    for i in [
        815560,
        805761,
        809579,
        814138,
        832409,
        841772,
        842150,
        845336,
        845486,
        853091,
        875885,
        891271,
        899462,
        809875,
    ]:
        df.loc[(i, "2020-03-01"), "empl_less_work_infection_gov"] = 1
    for i in [
        840737,
        805908,
        867733,
    ]:
        df.loc[(i, "2020-04-01"), "empl_less_work_infection_gov"] = 1

    # fired
    for i in [812734, 819509, 833105, 835183, 818292]:
        df.loc[(i, "2020-03-01"), "empl_less_work_fired"] = 1
    for i in [813705, 834539, 842296, 897854]:
        df.loc[(i, "2020-04-01"), "empl_less_work_fired"] = 1

    ##########################
    # Self employed -- less/not working
    ##########################

    # closure       by intervention
    for i in [827522, 848818, 814728, 886722]:
        df.loc[(i, "2020-03-01"), "selfempl_less_infection_gov"] = 1
    for i in [878454]:
        df.loc[(i, "2020-04-01"), "selfempl_less_infection_gov"] = 1

    # closure       personal choice
    for i in [805252, 807598, 827235, 831738, 843457, 862835, 889876]:
        df.loc[(i, "2020-03-01"), "selfempl_less_infection_self"] = 1
    for i in [827235, 831722]:
        df.loc[(i, "2020-04-01"), "selfempl_less_infection_self"] = 1

    # sick      incl. concentration/motivation issues
    for i in [809224, 815283, 842721, 863406]:
        df.loc[(i, "2020-03-01"), "selfempl_less_sick"] = 1
    for i in [861452, 861477]:
        df.loc[(i, "2020-04-01"), "selfempl_less_sick"] = 1

    # vacation:     planned vacation
    for i in [803268]:
        df.loc[(i, "2020-03-01"), "selfempl_less_vacation"] = 1
    for i in []:
        df.loc[(i, "2020-04-01"), "selfempl_less_vacation"] = 1

    # unrelated to corona
    for i in [829804]:
        df.loc[(i, "2020-03-01"), "selfempl_less_unrel_corona"] = 1
    for i in [873056, 825271, 843890]:
        df.loc[(i, "2020-04-01"), "selfempl_less_unrel_corona"] = 1

    # less business
    for i in [
        801055,
        849719,
        871969,
        877848,
        884164,
        894354,
        852658,
        813515,
        887454,
        875533,
        865424,
    ]:
        df.loc[(i, "2020-03-01"), "selfempl_less_business"] = 1
    for i in [817344]:
        df.loc[(i, "2020-04-01"), "selfempl_less_business"] = 1

    return df
