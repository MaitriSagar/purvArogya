"""The "How it was built" tab: the machine learning behind the app, in plain words.

All numbers come from the notebook (notebooks/purvarogya.ipynb), measured on the 30% of survey
respondents that the models never saw during training.
"""

import streamlit as st

# test ROC-AUC (diabetes, heart disease, stroke), from the model comparison table in the notebook
COMPARISON = [
    ("Logistic regression, default settings", (0.811, 0.834, 0.802)),
    ("Logistic regression, tuned (the one in this app)", (0.811, 0.834, 0.802)),
    ("Random forest", (0.817, 0.835, 0.802)),
    ("XGBoost, tuned", (0.817, 0.836, 0.803)),
]

# people who really have the condition and get flagged, out of 100 (recall at the 0.5 cut-off)
CAUGHT = [
    ("Default settings", (18, 7, 0)),
    ("Class weights (this app)", (76, 79, 77)),
]

# odds ratio for one standard deviation more of the answer, from the final logistic regressions
# (diabetes, heart disease, stroke). Above 1 raises the score.
ODDS = [
    ("Age group", (1.71, 2.70, 2.22)),
    ("General health", (1.67, 1.71, 1.53)),
    ("Blood pressure", (1.44, 1.37, 1.37)),
    ("BMI", (1.52, 1.00, 0.96)),
    ("Cholesterol", (1.36, 1.33, 1.12)),
]


def table(head, rows):
    cells = "".join(f"<th>{h}</th>" for h in head)
    body = ""
    for label, values in rows:
        body += f"<tr><td>{label}</td>" + "".join(f"<td>{v}</td>" for v in values) + "</tr>"
    return f'<table class="hit-table"><tr>{cells}</tr>{body}</table>'


def odds_bars():
    rows = ""
    for label, values in ODDS:
        cells = ""
        for v in values:
            width = max(0, min(100, (v - 1) / 1.7 * 100))
            cells += f'<td><div class="mini"><i style="width:{width:.0f}%"></i></div><span>{v:.2f}</span></td>'
        rows += f"<tr><td>{label}</td>{cells}</tr>"
    return ('<table class="hit-table odds"><tr><th></th><th>Diabetes</th><th>Heart disease</th><th>Stroke</th></tr>'
            + rows + "</table>")


def show_about(github_url):
    st.markdown('<h2 class="about-title">How it was built</h2>'
                '<p class="why">The machine learning behind the three results, in plain words.</p>',
                unsafe_allow_html=True)

    st.markdown('<h3 class="about-h">The data</h3>'
                '<p class="about-p">The 2023 Behavioral Risk Factor Surveillance System, a health survey run by the '
                'US CDC. About 400,000 adults answered it. Each of the three outcomes (diabetes, heart disease and '
                'stroke) is predicted by its own model, from the same 13 answers.</p>',
                unsafe_allow_html=True)

    st.markdown('<h3 class="about-h">How it was done</h3><ol class="steps">'
                '<li>Cleaned the survey codes. "Don\'t know" and "refused" became missing values.</li>'
                '<li>Split the people 70 / 30 first, before looking at anything, so the 30% stays untouched.</li>'
                '<li>Filled gaps using the 70% only, so nothing leaks from the test group.</li>'
                '<li>Scaled the numbers and turned smoking into separate yes / no columns.</li>'
                '<li>Compared four models, tuned them with 3-fold cross-validation, then scored them on the 30%.</li>'
                '</ol>', unsafe_allow_html=True)

    st.markdown('<h3 class="about-h">Which model won</h3>'
                '<p class="about-p">Test ROC-AUC, where 0.5 is a coin flip and 1.0 is perfect.</p>'
                + table(["", "Diabetes", "Heart disease", "Stroke"],
                        [(n, [f"{x:.3f}" for x in v]) for n, v in COMPARISON])
                + '<p class="about-p">The four are within 0.007 of each other, so the simplest one, logistic '
                  'regression, is in the app. It is easy to explain, and it is what lets the app say which answers '
                  'pushed your score up.</p>', unsafe_allow_html=True)

    st.markdown('<h3 class="about-h">Why class weights matter</h3>'
                '<p class="about-p">Only a few people in the survey have each condition (16 in 100 for diabetes, '
                '8 for heart disease, 4 for stroke). Left alone, a model learns to say "healthy" for almost '
                'everyone. Out of 100 people who really have it, this many get flagged:</p>'
                + table(["", "Diabetes", "Heart disease", "Stroke"],
                        [(n, [f"{x} in 100" for x in v]) for n, v in CAUGHT])
                + '<p class="about-p">The price is more false alarms. That is why the app shows a range and a '
                  'suggestion to get checked, never a diagnosis.</p>', unsafe_allow_html=True)

    st.markdown('<h3 class="about-h">What moves the score most</h3>'
                '<p class="about-p">How much the score rises when an answer goes up by one standard deviation '
                '(an odds ratio from the logistic regression). Above 1.00 means a higher score. Longer bars, '
                'bigger effect.</p>' + odds_bars(), unsafe_allow_html=True)

    st.markdown('<h3 class="about-h">What it cannot do</h3><ul class="steps">'
                '<li>It learned from US adults, so it may fit other populations less well.</li>'
                '<li>It sees 13 self-reported answers. No blood tests, no family history.</li>'
                '<li>Most flags are false alarms, especially for stroke, which is rare.</li>'
                '<li>It is a screening aid. It cannot replace a doctor.</li></ul>'
                f'<p class="fineprint">The full notebook, code and tests are on <a href="{github_url}">GitHub</a>.</p>',
                unsafe_allow_html=True)
