.. getting_started:

***************
Getting Started
***************

Get Access
==========

The project is a private repository on our GitLab-Server due to data requirements by LISS. We are, however, happy to share our code if you have access to LISS.

To do so, please follow these steps:

- Register for LISS access `here <https://www.dataarchive.lissdata.nl/>`_
- Join the OSE `Zulip Workspace <https://ose.zulipchat.com/join/rqccatmdndepvpftco4tyvyz/>`_
- Contact XXX

Modes of Use
============
There are three prototypical ways how to use the repository:

1. **Raw Files:** You can use this repository just to have an easy access to the raw LISS files all in one place.
2. **Prepared Files:** For many use cases it is more efficient if you make use of the already implemented data cleaning and use the prepared files. For this, you need to run the pipeline using **pytask**. Just select your preferred format(s) (.dta, .csv, .pickle) in `config.py`. You find the prepared files under `out/data`.
3. **Implement your own changes:** Once you start to use the prepared files, it is not unlikely that you would like to change something (possible due to errors, or incompletely cleaned variables). Feel free to change the renaming files, adjust the specific cleanings for a given study, or add new waves to your study. In this case, you need to know about the precise implementation details and you should continue reading. You will you need to know some Python.

Setting up the Project
======================
Make sure you have your conda environment up to date. Basic requirements are specified in the `environment.yml` file.
In the root folder of the project:

- run `conda develop .`
- run `pytask`

This resource can be helpful to get an understanding of pytask: `pytask documentation <https://pytask-dev.readthedocs.io/en/latest/>`_

Structure
==========
- `data/` contains all raw data sets of the LISS panel that are publicly available (if you miss something feel free to add it). For each questionnaire, we collected (1) the English codebook as .pdf and (2) the Stata data file. Each folder contains either these files directly (if it is a Single Wave Study) or subfolders for each wave "wave-1", "wave-2", etc.
- `liss_data_specs/` contains several renaming files that specify the new variable names for each study. In addition, the file `specification/data_sets_specs.json` lists all studies that should be cleaned and specifies more information about these studies (like the file name).
- `liss_data/` contains the files for the data cleaning.
- `corona_preparation/` contains the files for the cleaning the data from corona questionaire.
- `corona_prep_specs/` contains renaming and replacing files for corona questionaire.

The repository only contains raw files and scripts. All output files need to be produced by running `pytask` and can then be found under `out/data`.