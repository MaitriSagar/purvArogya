# purvArogya

**A multi-risk health screening system: Diabetes, Cardiovascular Disease and Stroke, predicted independently from one population survey.**

---

## The Problem

Many ML projects either predict a single disease, or merge unrelated datasets (for example Pima Diabetes with Cleveland Heart Disease) to build an "overall health score". That merged score is not scientifically valid, because the rows come from different populations.

purvArogya takes a different route: **one population cohort, one identical feature vector, three independent binary classifiers.** It is a preventive **screening tool, not a diagnostic one.**

## Dataset

- **CDC BRFSS Survey 2023** (Behavioral Risk Factor Surveillance System), downloaded from Kaggle: <https://www.kaggle.com/datasets/isuruprabath/brfss-2023-csv-dataset>
- 433,323 respondents x 350 columns. License shown on Kaggle: CC0-1.0.
- After cleaning: 397,478 rows, 13 features.

| Target | Positive cases (approx.) |
|---|---|
| Diabetes (incl. pre-diabetes) | ~16% |
| Cardiovascular disease | ~8.3% |
| Stroke | ~4.0% |

All three targets are imbalanced, so the models are judged on precision, recall, F1 and ROC-AUC, not accuracy alone.

## Project Status

| Stage | Status |
|---|---|
| Problem definition, dataset acquisition | Done |
| Dataset understanding, target definition | Done |
| Data quality check, cleaning (special codes, missing values) | Done |
| Exploratory data analysis | Done |
| Train-test split (70/30, stratified), feature selection (ANOVA / Cramer's V) | Done |
| Baseline, 3+ models, tuning, class imbalance | Done |
| Final comparison table with cross-validation, interpretation, error analysis | Done |
| Streamlit app | To do |
| Final report | To do |

Every modelling decision and its reason is written in [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Tech Stack

Python, pandas, NumPy, scikit-learn, imbalanced-learn, XGBoost, Matplotlib, Seaborn, Streamlit. Developed on Google Colab. Traditional ML only (no deep learning).

## Repository Anatomy

```
purvArogya/
├── purvarogya/             # reusable code (used by notebooks AND the app)
│   ├── config.py           # features, targets, BRFSS code maps, cleaning rules
│   └── preprocessing.py    # cleaning functions + train-only imputer
├── notebooks/              # the full modelling notebook (purvarogya.ipynb)
├── app/                    # Streamlit app
├── models/                 # saved trained models
├── docs/                   # decisions log, figures, report sections
├── tests/                  # pytest tests for the preprocessing rules
├── requirements.txt        # what the app needs
├── requirements-dev.txt    # notebook + tests
└── README.md
```

## Quickstart

```bash
pip install -r requirements-dev.txt   # notebook + tests (the app only needs requirements.txt)
python -m pytest                      # checks the cleaning rules
```

The raw dataset is not stored in this repo (it is large and free to download). To get it, create a Kaggle API token and store it as a **Colab Secret** (never paste it into a notebook cell), then:

```bash
kaggle datasets download -d isuruprabath/brfss-2023-csv-dataset
```

## Results

Final model per disease: Logistic Regression (C=0.01, balanced class weights), scored once on the 30% test set (119,244 people).

| Target | ROC-AUC | Recall | Precision | F1 |
|---|---|---|---|---|
| Diabetes | 0.811 | 0.763 | 0.337 | 0.468 |
| Cardiovascular disease | 0.834 | 0.793 | 0.207 | 0.328 |
| Stroke | 0.802 | 0.772 | 0.097 | 0.172 |

Random Forest and XGBoost land within 0.007 ROC-AUC of this, so the 13 survey features, not the algorithm, are the limit. I kept Logistic Regression because it is the simplest and its coefficients can be explained. Its scores are **not real probabilities** (class weights inflate them), so the app shows a risk flag, not "X% chance". Full notebook: [`notebooks/purvarogya.ipynb`](notebooks/purvarogya.ipynb).

## Key Design Choices

- **Pre-diabetes counts as positive**, because this is a risk screening tool.
- **BRFSS "special codes"** (7, 9, 77, 99 = don't know / refused; 88 = zero days) are handled explicitly, not left as numbers.
- **70/30 stratified split** on all three targets together, so rare cases (stroke) appear in both sets.
- **No data leakage:** imputation is fitted on training data only, and leakage columns like `diabage4` are excluded.
- **Training and app share one cleaning module**, so a user's form input is processed exactly like the training data.

