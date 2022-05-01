# Replication package for "Hours and income dynamics during the CoViD-19 pandemic: The case of the Netherlands"

This repository contains the replication package for the paper ["Hours and income dynamics during the CoViD-19 pandemic: The case of the Netherlands"](https://www.sciencedirect.com/science/article/pii/S0927537121000907) by Christian Zimpelmann, Hans-Martin von Gaudecker, Radost Holler, Lena Janys, and Bettina Siflinger as published in Labour Economics 2021.

The data is based on the [LISS (Longitudinal Internet Studies for the Social sciences)](https://www.lissdata.nl/) -- an internet-based household panel administered by CentERdata (Tilburg University, The Netherlands).

The replication of figures and tables proceeds in two steps:

## Step 1: Basic data cleaning

In this step, general data cleaning steps (renaming of variables and values, merging of yearly files) are conducted on the raw data files of the LISS. This step is based on a general LISS data cleaning repository. See [this documentation](https://liss-data-management-documentation.readthedocs.io/en/latest/#) for more information.

- Download all LISS raw data files and put them in the directory `raw_data/liss`. Alternatively, you can contact us and we can give you access to these files once you have registered for LISS data access.
- Install an anaconda python distribution on your computer and create a conda environment using `environment.yml`.
- Enter the directory `basic_data_cleaning` in a terminal
- Run `conda develop .`
- Run `pytask`
- The cleaned data sets will be saved in the directory `data_after_basic_cleaning`.

## Step 2: Project specific analyses

In this step, project specific data cleaning, the analyses, and the creation of tables and figures are conducted.

- Run basic data cleaning as described above. Alternatively, you can contact us and we can give you access to the data files after basic cleaning.
- If you haven't done so: install an anaconda python distribution on your computer and create a conda environment using `environment.yml`.
- Run `waf configure`
- Run `waf`
- All created tables and figures will be saved in the directory `output`.
