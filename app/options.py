"""The answers shown in the form, and the survey code each one is saved as.

The model was trained on BRFSS survey codes, so every answer is turned back into the
same code before it reaches the model.
"""

SEX = {"Male": 1, "Female": 2}

GENERAL_HEALTH = {"Excellent": 1, "Very good": 2, "Good": 3, "Fair": 4, "Poor": 5}

BLOOD_PRESSURE = {"No": 0, "Borderline": 1, "Yes": 2}

# "Not sure" becomes 1 (no), the most common survey answer. Training filled missing
# cholesterol answers with the same value.
CHOLESTEROL = {"No": 1, "Yes": 2, "Not sure": 1}

# ---- optional questions: if skipped, the typical answer is used ----
SMOKING = {"Every day": 1, "Some days": 2, "Used to": 3, "Never": 4}
ACTIVITY = {"Yes": 1, "No": 2}
INCOME = {"Under $10,000": 1, "$10,000 to $15,000": 2, "$15,000 to $20,000": 3,
          "$20,000 to $25,000": 4, "$25,000 to $35,000": 5, "$35,000 to $50,000": 6,
          "$50,000 to $75,000": 7, "$75,000 to $100,000": 8, "$100,000 to $150,000": 9,
          "$150,000 to $200,000": 10, "$200,000 or more": 11}
EDUCATION = {"Did not finish high school": 1, "Finished high school": 2,
             "Some college or technical school": 3, "College graduate": 4}

# The most common answer in the training data (median for the numbers). The notebook cell
# "what do we lose if the optional questions are skipped" prints these so they can be checked.
TYPICAL = {"smoking": 4,        # never smoked
           "activity": 1,       # was active
           "income": 7,         # $50,000 to $75,000
           "education": 4,      # college graduate
           "drinks": 0.0,       # drinks per week (training median is 0.23)
           "physical_days": 0,
           "mental_days": 0}

# what the model learned from, so we can warn about inputs outside it
BMI_RANGE = (12, 100)
AGE_RANGE = (18, 99)


def age_group(age):
    """Age in years -> BRFSS 5-year age group (1 = 18 to 24 ... 13 = 80 or older)."""
    if age >= 80:
        return 13
    if age < 25:
        return 1
    return (age - 25) // 5 + 2
