"""Cleaning steps for the BRFSS 2023 data.

Order of use:
    1. build_clean_dataset(raw_df)   -> before the train/test split (row-level rules only)
    2. train_test_split(...)         -> in the notebook / training code
    3. build_imputer()               -> fit on X_train only, then transform X_train and X_test
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer

from purvarogya import config


def create_targets(df):
    """Add the 3 binary target columns and drop rows where any target is unknown."""
    df = df.copy()
    for target_name, (raw_col, code_map) in config.TARGET_MAPS.items():
        # codes not in the map (7, 9, NaN) become NaN here
        df[target_name] = df[raw_col].map(code_map)
    return df.dropna(subset=config.TARGET_COLUMNS)


def clean_special_codes(df):
    """Turn BRFSS survey codes into real values or NaN."""
    df = df.copy()

    # 88 = "zero days" must be fixed BEFORE 77/99 are turned into NaN
    for col in config.DAYS_COLUMNS:
        df[col] = df[col].replace(88, 0)

    # CDC stores BMI multiplied by 100 to avoid decimals
    df["_bmi5"] = df["_bmi5"] / 100

    # use np.nan (not pd.NA) so columns stay numeric and pandas gives no dtype warning
    for col, codes in config.MISSING_CODES.items():
        df[col] = df[col].replace(codes, np.nan)

    # drinks per week is also stored x 100 (99900 was already turned into NaN above)
    df["_drnkwk2"] = df["_drnkwk2"] / 100

    return df


def drop_low_missing_rows(df):
    """Drop rows that miss a value in the low-missingness columns (< 5% missing)."""
    return df.dropna(subset=config.LOW_MISSING_COLUMNS)


def recode_bphigh6(df):
    """Reorder bphigh6 codes (3 -> 0, 4 -> 1, 1 -> 2) so they go up with the risk.

    Run it only once: running it twice would scramble the values, so it checks first.
    """
    df = df.copy()
    assert set(df["bphigh6"].dropna().unique()) <= set(config.BPHIGH6_ORDER), \
        "bphigh6 is already recoded or has unexpected codes"
    df["bphigh6"] = df["bphigh6"].map(config.BPHIGH6_ORDER)
    return df


def build_clean_dataset(raw_df):
    """Raw BRFSS dataframe -> dataframe with FEATURES + 3 targets, ready to split."""
    df = create_targets(raw_df)
    df = clean_special_codes(df)
    df = drop_low_missing_rows(df)
    df = recode_bphigh6(df)
    return df[config.FEATURES + config.TARGET_COLUMNS].reset_index(drop=True)


def build_imputer():
    """Imputer for the high-missingness columns.

    Not fitted yet. Call .fit(X_train) and then .transform() on train AND test, so the
    median / most frequent value come from the training rows only (no data leakage).
    """
    imputer = ColumnTransformer(
        transformers=[
            ("median", SimpleImputer(strategy="median"), config.IMPUTE_MEDIAN),
            ("mode", SimpleImputer(strategy="most_frequent"), config.IMPUTE_MODE),
        ],
        remainder="passthrough",          # all other features have no missing values left
        verbose_feature_names_out=False,  # keep the original column names
    )
    imputer.set_output(transform="pandas")
    return imputer
