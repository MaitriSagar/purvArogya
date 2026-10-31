# Decisions Log

Every choice I made in this project, with the reason. I keep this updated as I go.

---

## 1. Problem framing
- Predict 3 chronic conditions (Diabetes, CVD, Stroke) **independently** from one population
  survey, using the same feature vector for all three.
- I did not merge different datasets (like Pima Diabetes + Cleveland Heart Disease). They come
  from different populations, so a combined "overall health score" would not be scientifically valid.
- It is a **screening / risk tool, not a diagnosis tool.**

## 2. Dataset
- CDC BRFSS Survey 2023, downloaded from Kaggle: `isuruprabath/brfss-2023-csv-dataset`
  (file `BRFSS2023.csv`, 433,323 rows x 350 columns, license shown by Kaggle: CC0-1.0).
- Kaggle's page does not list the columns, so I checked every column name and code in the
  actual file instead of trusting memory.

## 3. Target definitions (`purvarogya/config.py`)
| Target | Raw column | 1 (positive) | 0 (negative) | Dropped |
|---|---|---|---|---|
| diabetes_target | `diabete4` | 1 (yes), 4 (pre-diabetes) | 3 (no), 2 (pregnancy only) | 7, 9, NaN |
| cvd_target | `_michd` | 1 | 2 | NaN |
| stroke_target | `cvdstrk3` | 1 | 2 | 7, 9, NaN |

- **Pre-diabetes counted as positive:** this is a risk screening tool, so flagging people who
  are heading towards diabetes is the point. The alternative (treat as negative) would tell
  at-risk people they are healthy. Honest limitation: pre-diabetes is not the same as diabetes.
- **Pregnancy-only diabetes labelled 0:** it is not chronic diabetes (about 3,000 rows).
  This can be revisited.
- **`_michd` for CVD:** CDC's own calculated variable that already combines heart attack and
  coronary heart disease, and it has no 7/9 junk codes.

## 4. Feature shortlist (13 of 350 columns)
`genhlth, _bmi5, _smoker3, _drnkwk2, _totinda, menthlth, physhlth, bphigh6, _rfchol3,
_ageg5yr, _sex, income3, _educag`

- Dropped administrative columns (interview date, state, etc.): not health information.
- Dropped **leakage columns** such as `diabage4` (age when told you have diabetes). It only
  exists if the person already has the condition, so the model would cheat.
- Where one question has several versions (raw / category / flag), I kept one CDC-calculated version.
- This file has no sleep-duration column, so sleep is not a feature.

## 5. Special codes (BRFSS does not use blanks for "unknown")
- `7, 9, 77, 99, 99900` mean don't know / refused, so they become NaN.
- `88` in `menthlth` / `physhlth` means **zero days**, not missing. It is fixed first.
- `_bmi5` is stored as BMI x 100, so I divide by 100.
- `bphigh6` code 2 (pregnancy only) is treated as missing.
- `_ageg5yr` code 14 (don't know / refused / missing) becomes NaN.
- `bphigh6` is reordered 3 (no) -> 0, 4 (borderline) -> 1, 1 (yes) -> 2, because the disease rate goes up in that order. The recode checks the codes first so it cannot be run twice by mistake.
- `_drnkwk2` is stored as drinks per week x 100 (the values 23, 47, 70, 93 match 1 to 4 drinks a
  month as a weekly rate), so I divide by 100. Still to confirm in the CDC codebook.
- The largest value is then 532 drinks per week, which is impossible (about 76 a day). I keep it
  (log1p squeezes it) and the app limits the input range.

## 6. Missing values
| Group | Rule | Columns |
|---|---|---|
| < 5% missing | drop those rows | genhlth, _totinda, menthlth, physhlth, bphigh6, _educag, _ageg5yr |
| >= 5% missing | impute | _bmi5, _drnkwk2 (median); _smoker3, _rfchol3, income3 (most frequent) |

- 427,034 rows -> 397,478 rows after dropping (about 7% lost). Class proportions stayed about the
  same (diabetes ~16%, CVD ~8.3%, stroke ~4.0%), so the dropping did not bias the targets.
- **Data leakage fix:** my first version computed the median / mode on the whole dataset
  before the split. Preprocessing must be fitted on training data only,
  so the imputation now lives in `build_imputer()` and is fitted on `X_train` only.
  (Covered by a unit test in `tests/test_preprocessing.py`.)

## 7. Train-test split
- 70/30, stratified on the three targets joined together, `random_state=42`. 30% gives enough
  stroke cases (about 4%) in the test set to measure recall properly.

## 8. Class imbalance
Positives: diabetes ~16%, CVD ~8.3%, stroke ~4.0%. Accuracy alone is misleading, so I report
precision, recall, F1 and ROC-AUC. I compared class weights with SMOTE (SMOTE only inside the
training pipeline) and kept class weights: simpler, and no synthetic rows.
- Side effect: class weights push the scores up, so they are not real probabilities. The app
  shows a risk flag and not a percentage.

## 9. Models
- Baseline: plain Logistic Regression. Compared with balanced Logistic Regression, Random Forest
  and XGBoost. Tuned with GridSearchCV (ROC-AUC, 3-fold, on a 50k-row training sample).
- Final choice: Logistic Regression, C=0.01, balanced. All models are within 0.007 test ROC-AUC
  (and the cross-validation scores agree), so I pick the simplest one I can explain.
- Test results (119,244 people): ROC-AUC 0.811 / 0.834 / 0.802, recall 0.763 / 0.793 / 0.772,
  precision 0.337 / 0.207 / 0.097 for diabetes / CVD / stroke.
- Honest note: I looked at test scores while comparing methods (class weights vs SMOTE, models).
  The tuning itself used cross-validation only, and the cross-validation scores show the same ranking.

## 10. Interpretation
- Logistic Regression odds ratios: age group is strongest (2.70 CVD), then general health and
  blood pressure. XGBoost ranks blood pressure far above everything else.
- Drinks has an odds ratio below 1. I read it as an association (sick people may drink less),
  not as "drinking protects".
- The model misses sick people who look healthy on the 13 answers (younger, lower BMI, fewer
  days of poor health, higher drinks). No lab values or family history are available.

## 11. App decisions
- **FastAPI backend with static frontend:** I chose FastAPI for three reasons: request validation with Pydantic, automatic interactive docs at `/docs`, and one app serving both the API and the page.
- **"How it was built" tab and `web/about.js`:** The numbers on the "How it was built" page live in `web/about.js`. The reason is that the numbers are the notebook's fixed test results, shown in one place, and they change only if the models are retrained.
- **Sex question:** Sex is asked as male or female because the survey the models learned from recorded sex as male or female.
- **Flag, percentile, and level (never a probability):** The models use balanced class weights, which artificially inflate the raw predicted scores, so they are not real probabilities. Instead, the app shows:
  - a flag (whether the score crosses the 0.5 threshold evaluated in the notebook),
  - a percentile showing where the score sits among the survey respondents (0 to 99), and
  - a risk level ("Lower", "Moderate", or "Higher") relative to the cohort.
- **Results message:** The advice message on the results page changes depending on whether any disease is flagged. It suggests speaking to a doctor if something is flagged, or notes that nothing is flagged right now. It never describes anyone as "healthy" (a screening is not a diagnosis and cannot guarantee health) and never gives a probability.
- **Why income and education are not asked:** Income and education describe a person's background, not their health, so I decided not to ask for them. The models were still trained on them (income lowers the risk a little in the odds ratios), so typical survey values are filled in internally. This is a known limitation.
- **Why income and education are hidden from the reasons list:** Because the user is never asked about income and education, showing either as a factor that pushed their risk up or down would be confusing and unhelpful. They are filtered out from `pushing_up` and `pulling_down`.
- **Score drivers:** "What pushed the score" uses the logistic regression coefficient multiplied by the person's scaled value relative to the training average. Drinks, smoking, and days of poor health are excluded from the list: drinks has a negative association (sick people may drink less) and the days columns overlap with general health, so listing them would mislead. They still count in the overall score.
- **One question per screen:** Six questions are required (age, sex, height and weight, general health, blood pressure, cholesterol). Optional lifestyle questions (smoking, physical activity, drinks, mental/physical health days) can be answered or skipped.
- **Validation:** Inputs outside what the model was trained on (BMI under 12 or over 100) are rejected by Pydantic before scoring. Drinks are capped at 50 per week.
- **Pinned dependency:** `scikit-learn==1.6.1` is strictly pinned so the serialized joblib pipelines load cleanly.

## 12. Still open
- Confirm `_drnkwk2` x 100 and `_ageg5yr` code 14 in the CDC codebook.
- Put the measured cost of skipping the optional questions into the app accuracy panel.
- Optional: ablation without `_sex` / `_educag`, wider tuning grid (C = 0.001, depth 2).
