"""Functions useful for variable generation in panel framework."""


def get_baseline(df, newvar, oldvar, baseline="2020-02-01"):
    """Generate variable that contains before Covid values for all periods.

    Example: want to have variable that contains hours_total from before
             Covid-19 at all points in time.

    Args:
        df (pd.DataFrame)
        newvar (str): name of the variable to be generated
        oldvar (str): name of the variable out of which the new variable
                      shall be generated.
        baseline (str): data of the baseline

    Return:
        original dataframe + newvar

    """
    base = df.index.get_level_values("month") == baseline
    var = df.loc[base, oldvar].reset_index().set_index("personal_id").copy()
    var.rename(columns={oldvar: newvar}, inplace=True)
    var = var[newvar].copy()
    return df.join(var)
