from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"


DATA_RAW = ROOT.parent / "raw_data"
IN_DATA_LISS = ROOT.parent / "raw_data" / "liss"
print(IN_DATA_LISS)
IN_SPECS_LISS = ROOT / "liss_data_specs"
OUT_DATA_LISS = OUT / "data" / "liss-data"
OUT_DATA_CORONA_PREP = OUT / "data" / "liss-prep"
OUT_TESTS = ROOT / "regression_test_files"
# define file format as one of "pickle", "dta", "csv", "parquet"
FILE_FORMATS_LISS = ["pickle"]

# "Prepare several additional files used for CoViD-19-Impact research.
# These files are installed in liss-data-covid-19/"
CORONA_PREP_LISS = True
CORONA_INSTALL = True

OUT_DATA_CORONA_INSTALL = ROOT.parent / "data_after_basic_cleaning"
IN_SPECS_CORONA = ROOT / "corona_prep_specs"
OUT_TABLES_CORONA = OUT / "data" / "corona-tables"
