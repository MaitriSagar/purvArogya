"""Turns one person's answers into what the app shows: a flag, a percentile and the
factors that pushed the score up or down.

It lives in the package (not in the app file) so it can be tested without Streamlit.
"""

import numpy as np

# the three diseases, named like the saved model files (diabetes_model.joblib, ...)
DISEASES = ["diabetes", "cvd", "stroke"]

# plain names for the factors the app lists
FACTOR_NAMES = {
    "_bmi5": "BMI",
    "_rfchol3": "cholesterol",
    "income3": "income",
    "genhlth": "general health",
    "_totinda": "physical activity",
    "bphigh6": "blood pressure",
    "_ageg5yr": "age",
    "_sex": "sex",
    "_educag": "education",
}

# model score above this = flagged. 0.5 is the cut-off I evaluated in the notebook.
FLAG_CUTOFF = 0.5

# contributions smaller than this are too small to mention
MIN_CONTRIBUTION = 0.05


def percentile_of(score, saved_percentiles):
    """Where a score sits among the training people (0 to 99).

    saved_percentiles holds the 0th, 1st ... 100th percentile of the training scores
    (saved in the notebook). searchsorted counts how many of them are below the score.
    """
    return int(np.clip(np.searchsorted(saved_percentiles, score), 0, 99))


def risk_level(flagged, percentile, flag_line):
    """Lower / Moderate / Higher, for the app's cards.

    Higher    = the model flags the person (score above the cut-off).
    Moderate  = not flagged, but in the upper half of the way up to the flag line.
    Lower     = everyone else.
    The levels are relative to the survey people, not a probability of having the disease.
    """
    if flagged:
        return "Higher"
    if percentile >= flag_line / 2:
        return "Moderate"
    return "Lower"


def _output_names(prep):
    """Names of the columns that come out of the preprocessing step, in order."""
    names = []
    for name, transformer, columns in prep.transformers_:
        if name == "remainder":
            continue
        if hasattr(transformer, "categories_"):          # the one-hot encoder: one column per category
            for col, categories in zip(columns, transformer.categories_):
                names += [f"{col}_{int(c)}" for c in categories]
        else:
            names += list(columns)
    return names


def score_drivers(model, person, top_n=3):
    """The factors that pushed this person's score up or down, compared with an average person.

    Logistic regression adds up coefficient x (scaled value). The scaler centres every
    column on the training average, so a positive product means "above the average person".
    """
    prep = model.named_steps["prep"]
    lr = model.named_steps["lr"]

    # each model only looks at the columns it was trained on (the quick one uses 6 of the 13)
    values = prep.transform(person[list(model.feature_names_in_)])
    values = values.toarray()[0] if hasattr(values, "toarray") else np.asarray(values)[0]

    names = _output_names(prep)
    assert len(names) == len(values)
    contributions = lr.coef_[0] * values

    # drinks, smoking and the days of poor health are left out of the list. They still count in
    # the score, but their coefficients are hard to read on their own: drinks has a negative link
    # in this data (people who get sick often drink less), and the days columns overlap with
    # general health. Only FACTOR_NAMES are shown.
    shown = {n: c for n, c in zip(names, contributions) if n in FACTOR_NAMES}

    up = [n for n, c in sorted(shown.items(), key=lambda x: -x[1]) if c > MIN_CONTRIBUTION][:top_n]
    down = [n for n, c in sorted(shown.items(), key=lambda x: x[1]) if c < -MIN_CONTRIBUTION][:top_n]
    return [FACTOR_NAMES[n] for n in up], [FACTOR_NAMES[n] for n in down]


def assess(models, percentiles, person):
    """Results for one person (a one-row dataframe in the training format).

    models      : {"diabetes": pipeline, "cvd": pipeline, "stroke": pipeline}
    percentiles : {"diabetes_target": array, ...} saved by the notebook
    """
    results = {}
    for disease, model in models.items():
        score = model.predict_proba(person[list(model.feature_names_in_)])[0, 1]
        saved = percentiles[disease + "_target"]
        pushing_up, pulling_down = score_drivers(model, person)
        flagged = bool(score > FLAG_CUTOFF)
        percentile = percentile_of(score, saved)
        flag_line = percentile_of(FLAG_CUTOFF, saved)          # where the "Higher" zone starts on the gauge
        results[disease] = {
            "flagged": flagged,
            "level": risk_level(flagged, percentile, flag_line),
            "percentile": percentile,
            "flag_line": flag_line,
            "pushing_up": pushing_up,
            "pulling_down": pulling_down,
        }
    return results
