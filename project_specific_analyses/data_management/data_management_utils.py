"""utils for data management
"""
import warnings


def set_types_file(
    panel, rename_df, cat_sep=", ", int_to_float=True, bool_to_float=True
):
    """Assign types to the columns in `panel` using the renaming file.
    > copied from liss-data repository

    Args:
        panel (pandas.DataFrame): The dataframe which types need to be
            assigned.
        rename_df (pandas.DataFrame): The renaming dataframe taken from the
            renaming file.
        cat_sep(string): The separator of the categories in the file.

    Returns:
        pandas.DataFrame: The dataframe with the new types assigned.

    """
    out = panel.copy()

    rename_df = rename_df.set_index("new_name")
    rename_df["type"] = rename_df["type"].replace(
        {
            "int": "Int64",
            "float": "float64",
            "bool": "boolean",
            "Categorical": "category",
            "Int": "Int64",
        }
    )

    if int_to_float:
        rename_df["type"] = rename_df["type"].replace({"Int64": "float64"})
    if bool_to_float:
        rename_df["type"] = rename_df["type"].replace({"boolean": "float64"})

    for var in out.columns.values:
        try:
            expected_type = rename_df.loc[var, "type"]
        except KeyError:
            continue

        if expected_type == expected_type:
            try:
                out[var] = out[var].astype(expected_type)
            except TypeError:
                print(f"could not convert {var} to {expected_type}")
            except Exception:
                print(
                    f"unexpected error converting the type of {var} to {expected_type}"
                )

            if (
                expected_type == "category"
                and rename_df.loc[var, "categories_english"]
                == rename_df.loc[var, "categories_english"]
            ):
                try:
                    cats = [
                        int(s)
                        for s in rename_df.loc[var, "categories_english"].split(cat_sep)
                    ]
                except Exception:
                    cats = rename_df.loc[var, "categories_english"].split(cat_sep)
                if rename_df.loc[var, "ordered"] == rename_df.loc[var, "ordered"]:
                    try:
                        out[var].cat.set_categories(
                            cats,
                            ordered=rename_df.loc[var, "ordered"],
                            inplace=True,
                        )
                    except Exception:
                        warnings.warn(
                            f"for {out[var]} there is an error in the "
                            "categories specified in the file",
                            UserWarning,
                        )

                else:
                    try:
                        out[var].cat.set_categories(cats, inplace=True)
                    except Exception:
                        warnings.warn(
                            f"for {out[var]} there is an error in the "
                            "categories specified in the file",
                            UserWarning,
                        )
        else:
            out.loc[:, var] = _set_inferred_types(
                out[var], int_to_float=int_to_float, bool_to_float=bool_to_float
            )

    return out
