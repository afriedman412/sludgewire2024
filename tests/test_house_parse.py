import os
import pdfplumber
import pandas as pd
from pandas.testing import assert_frame_equal
from src.house.pdf_processing import extract_ptr_entries


def test_extractor():
    path = os.path.abspath("./tests/house_test_assets")
    files = set([f[:-4] for f in os.listdir(path) if not f.startswith(".")])
    for file in files:
        print(file)
        p = pdfplumber.open(os.path.join(path, file + ".pdf"))
        df = extract_ptr_entries(p).fillna("").drop("URL", axis=1)
        print(df.columns)
        check_df = pd.read_csv(
            os.path.join(path, file + ".csv")).drop(
                ["URL"], axis=1
                )
        print(check_df.columns)
        assert_frame_equal(
            df,
            check_df.fillna("")
        )
