"""Turns the answers a person gives into the row the models expect."""
import pandas as pd

# label shown to the person -> BRFSS code the models were trained on
SEX = {"Male": 1, "Female": 2}
GENERAL_HEALTH = {"Excellent": 1, "Very good": 2, "Good": 3, "Fair": 4, "Poor": 5}
BLOOD_PRESSURE = {"No": 0, "Borderline": 1, "Yes": 2}
CHOLESTEROL = {"No": 1, "Yes": 2, "Not sure": 1}
SMOKING = {"Every day": 1, "Some days": 2, "Used to": 3, "Never": 4}
ACTIVITY = {"Yes": 1, "No": 2}

# used when the person skips an optional question (typical survey answers)
TYPICAL = {
    "smoking": 4,
    "activity": 1,
    "drinks": 0.0,
    "physical_days": 0,
    "mental_days": 0,
    "income": 7,      # not asked in the app
    "education": 4,   # not asked in the app
}


def age_group(age):
    """Convert age in years to the BRFSS _ageg5yr code (1 to 13)."""
    if age >= 80:
        return 13
    if age < 25:
        return 1
    return (age - 25) // 5 + 2

def build_person(age, sex, height_cm, weight_kg, general_health,
                 blood_pressure, cholesterol, feature_names,
                 smoking=None, activity=None, drinks=None,
                 physical_days=None, mental_days=None):
    """Build the one-row DataFrame in the column order the models were trained on."""
    bmi = weight_kg / (height_cm / 100) ** 2

    row = {
        "genhlth": GENERAL_HEALTH[general_health],
        "_bmi5": bmi,
        "_smoker3": TYPICAL["smoking"] if smoking is None else SMOKING[smoking],
        "_drnkwk2": TYPICAL["drinks"] if drinks is None else drinks,
        "_totinda": TYPICAL["activity"] if activity is None else ACTIVITY[activity],
        "menthlth": TYPICAL["mental_days"] if mental_days is None else mental_days,
        "physhlth": TYPICAL["physical_days"] if physical_days is None else physical_days,
        "bphigh6": BLOOD_PRESSURE[blood_pressure],
        "_rfchol3": CHOLESTEROL[cholesterol],
        "_ageg5yr": age_group(age),
        "_sex": SEX[sex],
        "income3": TYPICAL["income"],
        "_educag": TYPICAL["education"],
    }
    # feature_names fixes the column order, which the model depends on
    return pd.DataFrame([row])[feature_names]