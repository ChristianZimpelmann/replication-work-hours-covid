# Replication package for "Hours and income dynamics during the CoViD-19 pandemic: The case of the Netherlands"

This repository contains the replication package for the paper ["Hours and income dynamics during the CoViD-19 pandemic: The case of the Netherlands"](https://www.sciencedirect.com/science/article/pii/S0927537121000907) by Christian Zimpelmann, Hans-Martin von Gaudecker, Radost Holler, Lena Janys, and Bettina Siflinger as published in Labour Economics 2021.

## Data

The data is based on the [LISS (Longitudinal Internet Studies for the Social sciences)](https://www.lissdata.nl/) -- an internet-based household panel administered by CentERdata (Tilburg University, The Netherlands).

- Our self-collected data on the pandemic is [documented here](https://liss-covid-19-questionnaires-documentation.readthedocs.io/en/latest/). And can be cited using [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4616813.svg)](https://doi.org/10.5281/zenodo.4616813).
- Before running the project (see below), download all LISS raw data files and put them in the directory `raw_data/liss`. Alternatively, you can contact us and we can give you access to the raw files once you have registered for LISS data access. As of 2022 not all data sets that we collected ourselves are publicly available on the website, but we are happy to share them.
- The directory `raw_data` already contains the following files:
  - `owid-covid-data.csv`: COVID-19 cases over time based on [Our World in Data](https://ourworldindata.org/coronavirus)
  - `OxCGRT_latest.csv`: Measures of the [COVID-19 government response tracker](https://www.bsg.ox.ac.uk/research/research-projects/covid-19-government-response-tracker) over time

The replication of figures and tables proceeds in two steps:

## Step 1: Basic data cleaning

In this step, general data cleaning steps (renaming of variables and values, merging of yearly files, etc.) are conducted on the raw data files of the LISS. This step is based on a general LISS data cleaning repository. See [this documentation](https://liss-data-management-documentation.readthedocs.io/en/latest/#) for more information.

- Install a [Miniconda](https://docs.conda.io/projects/continuumio-conda/en/latest/user-guide/install/index.html) python distribution on your computer and create a conda environment using `environment.yml`.
- Move to the directory `basic_data_cleaning` in a terminal
- Run `conda develop .`
- Run `pytask`
- The cleaned data sets will be saved in the directory `data_after_basic_cleaning`.

We can also give you access to the data files after basic cleaning such that you can skip Step 1.

## Step 2: Project specific analyses

In this step, project specific data cleaning, the analyses, and the creation of tables and figures are conducted.

- Move to the top directory of the repository in a terminal
- Run `waf configure`
- Run `waf`
- All created tables and figures will be saved in the directory `output`.
