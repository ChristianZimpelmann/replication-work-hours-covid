.. _introduction:

************
Introduction
************

Documentation on the liss-data cleaning repository (by OSE?). This repository cleans the datasets of the LISS (Longitudinal Internet Studies for the Social sciences) panel. It is written in Python.

.. _liss_panel:

About LISS Panel
================
The `LISS panel <https://www.lissdata.nl/>`_ is an internet-based household panel administered by CentERdata (Tilburg University, The Netherlands). The sample is drawn from the Dutch population via random sampling. Every month, participants answer questionnaires that are exclusively reserved for research purposes. Respondents are financially compensated for all questions they answer.

.. _motivation:

Motivation
==========
- Data cleaning is an important component of empirical research projects.
- But it can be very tedious.
- Cleaned data sets can be used for several different research projects → public good
- The goal of this repository is to share the effort associated with the most basic parts of data cleaning.

The basic idea is that all fundamental data cleaning that is helpful in (almost) all projects using this data set should be done within the liss-data repo. Examples are the renaming of variables, renaming of values (e.g. "I don't know -> np.nan"), or the calculation of simple variables that are often used (e.g. `has_risky_financial_assets = risky_financial_assets > 0`).

Conversely, specific data management that is mostly relevant for your project, in particular the merging of data sets and selecting of specific observations, should be done outside of this repo in your own project folder.
