import os
import re
import warnings
from importlib import import_module
from inspect import currentframe
from inspect import getframeinfo

import pandas as pd
import pytask
import yaml
from config import FILE_FORMATS_LISS
from config import IN_DATA_LISS
from config import IN_SPECS_LISS
from config import OUT_DATA_LISS
from liss_data.utils_liss_data import get_traceback  # noqa
from liss_data.utils_liss_data import load_data_set_and_specs  # noqa
from liss_data.utils_liss_data import read_stata  # noqa
from liss_data.utils_liss_data import save_panel  # noqa
from liss_data.utils_liss_data import send_warnings_to_log as swtl

pd.options.mode.chained_assignment = "raise"


with open(IN_SPECS_LISS / "data_sets_specs.yaml") as f:
    dir_dict = yaml.safe_load(f)


PARAMETRIZATION = []
# for directory in ["008-politics-and-values"]:
for directory in dir_dict:
    for file_format in FILE_FORMATS_LISS:
        data_set_name = dir_dict[directory]["file_name"]
        deps = {
            f"{directory}_renaming": IN_SPECS_LISS / f"{directory}_renaming.csv",
            "data_sets_specs": IN_SPECS_LISS / "data_sets_specs.yaml",
            "utils": "utils_liss_data.py",
            "cleaning": "cleaning_helpers.py",
        }
        if dir_dict[directory]["specific_calc"]:
            deps.update({"clean_" + data_set_name: "clean_" + data_set_name + ".py"})
        if directory == "xxx-ambiguous-beliefs":
            deps.update(
                {"data_management_ambig_beliefs": "data_management_ambig_beliefs.py"}
            )
        for file in (IN_DATA_LISS / directory).glob("**/*.dta"):
            if "do_not_use" not in str(file):
                deps.update({f"file_path_{file}": file})

        target = {
            f"{data_set_name}_{file_format}": OUT_DATA_LISS
            / f"{data_set_name}.{file_format}"
        }
        if directory == "xxx-ambiguous-beliefs" and file_format == "pickle":
            target.update(
                {
                    "event_properties": OUT_DATA_LISS
                    / "ambiguous_beliefs"
                    / "event_properties.pickle",
                    "choice_properties": OUT_DATA_LISS
                    / "ambiguous_beliefs"
                    / "choice_properties.pickle",
                    "choices": OUT_DATA_LISS / "ambiguous_beliefs" / "choices.pickle",
                    "baseline_matching_probs": OUT_DATA_LISS
                    / "ambiguous_beliefs"
                    / "baseline_matching_probs.pickle",
                    "indices": OUT_DATA_LISS / "ambiguous_beliefs" / "indices.pickle",
                    "choices_pay_out_info": OUT_DATA_LISS
                    / "ambiguous_beliefs"
                    / "choices_pay_out_info.pickle",
                }
            )
        if directory == "001-background-variables":
            target.update(
                {
                    f"background_full_{year}": OUT_DATA_LISS
                    / f"background_full_{year}.{file_format}"
                    for year in range(2007, 2021)
                }
            )
        PARAMETRIZATION.append((deps, target, directory, file_format))


def _common_cleaning(panel):
    """Some data cleaning conducted on all data sets."""
    panel = panel.copy()

    # Remove some characters from all strings
    str_col = list(panel.select_dtypes(include=["object"]).columns)

    for c in str_col:
        # Replace line breaks in free text answers
        panel[c] = panel[c].replace("\n", " ", regex=True)
        panel[c] = panel[c].replace("\r", " ", regex=True)

        # Replace all semicolons (important to save it as .csv)
        panel[c] = panel[c].replace(";", ",", regex=True)

    # convert personal_id to int
    panel["personal_id"] = panel["personal_id"].astype(int)
    return panel


def prepare_panel(out_format, file_paths, data_set_name):
    """Data cleaning and pre preparation for some data set."""
    # Get basic specs
    # data_set_name, file_paths, specs, out_format = _get_file_paths(data_set)
    specs, rename_df, cleaning_specs = load_data_set_and_specs(data_set_name)

    data_set_list = []
    for file_path in file_paths:
        path_components = os.path.normpath(file_path).split(os.sep)
        file_name = path_components[-1]
        if path_components[-2] == data_set_name:
            wave = None
        elif path_components[-3] == data_set_name:
            wave_match = re.match("wave-([0-9]+)", path_components[-2])
            if wave_match:
                wave = int(wave_match.group(1))
            else:
                wave_match = re.match("20[012][0-9]-[01][0-9]", path_components[-2])
                wave = pd.to_datetime(path_components[-2])
        else:
            raise ValueError("Unexpected directory structure in: {file_path}")

        if file_name not in rename_df:
            frameinfo = getframeinfo(currentframe())
            module_name = frameinfo.filename
            lineno = frameinfo.lineno - 1
            message = f"{file_name} not yet in {data_set_name}_renaming.csv."
            warnings.warn(message)
            swtl(message=message, module_name=module_name, lineno=lineno)
        else:
            vars_to_keep = list(rename_df[file_name].dropna())
            data = read_stata(
                file_path,
                convert_categoricals=True,
                vars_to_keep=vars_to_keep,
                renaming_complete=(file_name == "xyx-corona-questionnaire"),
            )

            # rename vars
            rename_dict = rename_df.set_index(file_name)["new_name"].to_dict()
            data = data.rename(columns=rename_dict)

            if wave is not None:
                data["wave"] = wave

            # Calc year (if multiple files per year exist, keep months)
            assert "date_fieldwork" in data
            if specs["multiple_files_per_year"]:
                year = (
                    data[data["date_fieldwork"].notnull()]["date_fieldwork"]
                    .astype(int)
                    .mode()[0]
                )
            else:
                year = (
                    data[data["date_fieldwork"].notnull()]["date_fieldwork"]
                    .apply(lambda x: int(x / 100))
                    .mode()[0]
                )

            data["year"] = year
            if any(data.columns.duplicated()):
                msg = (
                    f"The columns {data.columns[data.columns.duplicated()]}"
                    + f" in wave {wave} are duplicated"
                )
                raise ValueError(msg)
            data_set_list.append(data)

    # Put panel data_set together
    if data_set_name == "001-background-variables":
        pass
    elif len(data_set_list) > 1:
        panel = pd.concat(data_set_list, ignore_index=True, sort=False)
    else:
        panel = data_set_list[0]

    # keep hh_id only in background data sets
    if (
        data_set_name
        not in [
            "001-background-variables",
            "xyx-corona-questionnaire",
            "xxx-ambiguous-beliefs",
        ]
        and "hh_id" in panel
    ):
        panel = panel.drop("hh_id", axis=1)

    # Panel-specific calculations
    if specs["specific_calc"]:
        function_name = "clean_" + specs["file_name"]
        module = import_module(f"liss_data.{function_name}")
        func = getattr(module, function_name)
        if data_set_name == "001-background-variables":
            panel = func(data_set_list, out_format)
        elif data_set_name == "xxx-ambiguous-beliefs":
            save_panel(
                panel=panel,
                file_name=specs["file_name"] + "_before_ind_clean",
                out_format=out_format,
            )
            panel = func(panel, out_format)
        else:
            save_panel(
                panel=panel,
                file_name=specs["file_name"] + "_before_ind_clean",
                out_format="pickle",
            )
            panel = func(panel)

    # Some data cleaning for every data set
    panel = _common_cleaning(panel)

    # Set index and save file
    panel = panel.set_index(["personal_id", "year"]).sort_index()
    save_panel(panel=panel, file_name=specs["file_name"], out_format=out_format)


#
# def _get_file_paths(data_set):
#     with open(OUT_DATA_LISS / "dir_to_parameters.json") as file:
#         dir_to_paths = json.load(file)
#
#     parameter_to_append = str(dir_to_paths[data_set])
#
#     parameters = parameter_to_append.split(" ")
#     out_format = parameters[0]
#     my_directory = parameters[1]
#     file_paths = parameters[2:]
#
#     with open(IN_SPECS_LISS / "data_sets_specs.yaml") as fn:
#         my_specs = json.load(fn)[my_directory]
#
#     return my_directory, file_paths, my_specs, out_format


@pytask.mark.parametrize(
    "depends_on, produces, data_set_name, file_format", PARAMETRIZATION
)
def task_prepare_panel(depends_on, produces, data_set_name, file_format):
    file_paths = [depends_on[k] for k in depends_on if k.startswith("file_path_")]
    try:
        prepare_panel(file_format, file_paths, data_set_name)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        print(f"\n\nUnexpected error in: {data_set_name}\n\n")
        print(get_traceback())
        raise e
