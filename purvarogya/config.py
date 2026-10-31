"""All dataset-specific choices live here, so the notebooks, training code and
the web app all use exactly the same rules.

Every code below was checked against the value counts in BRFSS2023.csv and the
CDC BRFSS codebook (see docs/DECISIONS.md). Column names are lowercase in this file.
"""

# ---------------------------------------------------------------- targets
# Each target: raw column -> {raw code: 0 or 1}. Codes not listed (7 = don't know,
# 9 = refused, NaN) become NaN and those rows are dropped.
TARGET_MAPS = {
    # diabete4: 1 = yes, 2 = yes but only during pregnancy, 3 = no, 4 = pre-diabetes
    # I count pre-diabetes as positive because this is a risk screening tool.
    # Pregnancy-only diabetes (2) is labelled 0 (not chronic diabetes).
    "diabetes_target": ("diabete4", {1: 1, 4: 1, 3: 0, 2: 0}),
    # _michd: CDC's calculated "ever had heart attack or coronary heart disease"
    "cvd_target": ("_michd", {1: 1, 2: 0}),
    # cvdstrk3: ever told you had a stroke
    "stroke_target": ("cvdstrk3", {1: 1, 2: 0}),
}

TARGET_COLUMNS = list(TARGET_MAPS.keys())

# ---------------------------------------------------------------- features
FEATURES = [
    "genhlth",    # general health, 1 (excellent) to 5 (poor)
    "_bmi5",      # BMI, stored by CDC as BMI * 100
    "_smoker3",   # smoking status (calculated)
    "_drnkwk2",   # drinks per week (calculated, stored by CDC as drinks x 100)
    "_totinda",   # did any physical activity in last 30 days
    "menthlth",   # days of poor mental health in last 30 days
    "physhlth",   # days of poor physical health in last 30 days
    "bphigh6",    # told you have high blood pressure
    "_rfchol3",   # told you have high cholesterol (calculated flag)
    "_ageg5yr",   # age group, 5-year buckets
    "_sex",
    "income3",    # income bracket
    "_educag",    # education group (calculated)
]

# ------------------------------------------------------- cleaning rules
# Columns where code 88 means "none / zero days" (NOT missing!)
DAYS_COLUMNS = ["menthlth", "physhlth"]

# Codes that mean "don't know", "refused" or "not applicable" -> treated as missing
MISSING_CODES = {
    "genhlth": [7, 9],
    "_smoker3": [9],
    "_drnkwk2": [99900],
    "_totinda": [9],
    "menthlth": [77, 99],
    "physhlth": [77, 99],
    "bphigh6": [2, 7, 9],   # 2 = only during pregnancy, not relevant for general risk
    "_rfchol3": [9],
    "income3": [77, 99],
    "_educag": [9],
    "_ageg5yr": [14],       # 14 = don't know / refused / missing (confirm in codebook)
}

# ------------------------------------------------- missing value strategy
# Columns with < 5% missing: drop those rows (cheap, nothing is invented)
LOW_MISSING_COLUMNS = ["genhlth", "_totinda", "menthlth", "physhlth", "bphigh6", "_educag", "_ageg5yr"]

# Columns with >= 5% missing: impute, but only AFTER the train/test split,
# fitting on the training rows only (no test information may leak into preprocessing)
IMPUTE_MEDIAN = ["_bmi5", "_drnkwk2"]
IMPUTE_MODE = ["_smoker3", "_rfchol3", "income3"]

# bphigh6 raw codes: 1 = yes, 3 = no, 4 = borderline. I reorder them so the number goes up
# with the risk (no < borderline < yes), because the disease rate follows that order.
BPHIGH6_ORDER = {3: 0, 4: 1, 1: 2}

# ---------------------------------------------------------------- misc
RANDOM_STATE = 42
TEST_SIZE = 0.3   # 70/30 split
