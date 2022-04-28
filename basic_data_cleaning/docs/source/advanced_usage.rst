.. advanced_usage:

**************
Advanced Usage
**************

Adding new Files
================
To add new studies or new waves of existing studies, please follow the following steps:

- Download both the respective data file as .dta and the English codebook as .pdf
- Put those files in `data/` and make sure the folder structure is consistent to the previous studies
- You can add `_do_not_use.dta` at the end of a .dta file to make sure it is not considered in the cleaning process
- If it's a completely new study (not just a new wave), adjust `data/specification/data_sets_specs.json` accordingly
- Run `create_renaming_files` from the sandbox to automatically add the new columns in the respective renaming files
- Manually adjust the renaming file
- Run `pytask`

CoViD-19 Impact Lab
===================

Our code is used by the `CoViD-19 Impact Lab <https://covid-19-impact-lab.readthedocs.io/en/latest/>`_.

To create the additional files used for the corona studies:

- set `CORONA_PREP_LISS = True` in `config.py`.
- run `pytask`
