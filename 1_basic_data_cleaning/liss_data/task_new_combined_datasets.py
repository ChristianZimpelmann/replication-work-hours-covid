import numpy as np
import pandas as pd
import pytask
from config import FILE_FORMATS_LISS
from config import OUT_DATA_LISS
from liss_data.utils_liss_data import save_panel  # noqa

pd.options.mode.chained_assignment = "raise"


@pytask.mark.depends_on(
    {
        "background": OUT_DATA_LISS / "background.pickle",
        "assets": OUT_DATA_LISS / "assets.pickle",
    }
)
@pytask.mark.produces([OUT_DATA_LISS / f"assets_on_hh.{f}" for f in FILE_FORMATS_LISS])
def task_hh_level_assets(depends_on, produces):
    """Generate aggregated asset variables for each household"""
    # Load data
    background = pd.read_pickle(depends_on["background"])
    assets = pd.read_pickle(depends_on["assets"])

    data = assets.join(background[["hh_id", "hh_position", "age"]])

    # Full household
    fin_vars = [
        "banking",
        "insurance",
        "risky_financial_assets",
        "real_estate",
        "durables",
        "mortgage",
        "loan_out",
        "other_inv",
        "study_grant",
        "priv_comp",
        "pship",
        "self_empl_comp",
        "debt_excl_housing",
        "non_fin_assets_excl_housing",
        "total_financial_assets",
        "wealth_excl_housing",
    ]
    res = data.groupby(["hh_id", "year"])[fin_vars].sum()
    res.columns = [c + "_hh" for c in res]
    res["hh_members"] = background.groupby(["hh_id", "year"])["hh_members"].first()
    for c in fin_vars:
        res[c + "_hh_equiv"] = res[c + "_hh"] / np.sqrt(res["hh_members"])

    # Save result
    for out_path in produces.values():
        save_panel(res, out_path.stem, out_format=out_path.suffix)
