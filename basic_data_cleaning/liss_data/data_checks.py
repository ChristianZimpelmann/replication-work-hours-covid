"""
This file contains some functions that are shared
across cleaning modules
"""
import warnings
from inspect import currentframe
from inspect import getframeinfo

from liss_data.utils_liss_data import send_warnings_to_log as swtl


def general_data_checks(panel, config=None):
    if config:
        # Check for nan cols!
        nan_cols = config.pop("nan_cols", [])
        cols = [col for col in panel.columns if col not in nan_cols]
        if panel[cols].isnull().all(axis=0).any():
            frameinfo = getframeinfo(currentframe())
            module_name = frameinfo.filename
            lineno = frameinfo.lineno - 1
            for i in panel[cols].loc[:, panel[cols].isnull().all(axis=0)]:
                message = f"{i} column contains only NaNs."
                warnings.warn(message, UserWarning)
                swtl(message=message, module_name=module_name, lineno=lineno)
        assert ~panel[cols].isnull().all(axis=0).any()

        # Sum check
        if "sum_checks" in config:
            sum_checks(panel, config["sum_checks"])


def sum_checks(panel, sc_config):
    """Implements a set of sum checks that make sure that a list of variables
    sum to a specific value

    Args:
        panel (DataFrame): data to be checked
        sc_config (dict): specification of sum check. Might include:
            - 'starts' or 'vars' to select columns
            - 'sum' (float) expected sum of columns
            - 'query' to check only on subset of dataframe (optional)
            - 'round' (float) to round some before check (optional)

    Raises:
        NotImplementedError: [description]
    """
    for sci_config in sc_config:
        # columns can be selected by the beginning of the variable name or explicitly
        if "starts" in sci_config:
            cols = [x for x in panel.columns if x.startswith(sci_config["starts"])]
        elif "vars" in sci_config:
            cols = sci_config["vars"]
        else:
            raise NotImplementedError("sum_checks expects either 'starts' or 'vars'")

        # Only check subset of all observations if specified
        temp = panel.query(sci_config["query"]) if "query" in sci_config else panel

        # Calculate sum
        sum_of_cols = temp[cols].sum(axis=1)

        # Round sum if specified
        if "round" in sci_config:
            sum_of_cols = sum_of_cols.round(sci_config["round"])

        # Check sum
        valid_sum = sum_of_cols.isin([0, sci_config["sum"]])
        assert valid_sum.all(), (
            f"The following columns do not add up to {sci_config['sum']}:"
            f"\n{sum_of_cols.loc[~valid_sum]}"
        )
