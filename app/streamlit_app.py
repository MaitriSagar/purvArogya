import math
import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

# so "purvarogya" can be imported when the app is started with: streamlit run app/streamlit_app.py
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, ROOT.as_posix())

import options as opt
from purvarogya.scoring import assess

st.set_page_config(page_title="PurvAarogya", page_icon="🧡", layout="centered")

MODEL_FOLDER = ROOT / "models"
GITHUB_URL = "https://github.com/MaitriSagar/purvArogya"

# name on the page, short note, flagged people who really have it (recall) and flags that are right (precision)
DISEASE_TEXT = {
    "diabetes": ("Diabetes", "includes pre-diabetes", "76", "34"),
    "cvd": ("Heart disease", "heart attack or coronary heart disease", "79", "21"),
    "stroke": ("Stroke", "", "77", "10"),
}

HEART = ('<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 28C6 20 3 13 7 8.5C10 5.5 14.5 6.5 16 10'
         'C17.5 6.5 22 5.5 25 8.5C29 13 26 20 16 28Z" fill="#D4532E"/></svg>')

# a simple picture for the welcome screen: three soft circles and a heart with a pulse line
HERO = ('<svg class="hero-art" viewBox="0 0 220 160" aria-hidden="true">'
        '<circle cx="70" cy="90" r="52" fill="#DDEFE5"/><circle cx="152" cy="68" r="46" fill="#FCEBC8"/>'
        '<circle cx="122" cy="108" r="40" fill="#FFE1D2"/>'
        '<path d="M110 132C74 104 66 76 86 66C99 60 108 68 110 77C112 68 121 60 134 66C154 76 146 104 110 132Z" fill="#D4532E"/>'
        '<polyline points="82,94 98,94 104,82 112,108 119,90 138,90" fill="none" stroke="#fff" stroke-width="4" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>')


@st.cache_resource(show_spinner="Loading the models...")
def load_models():
    # loaded once, so the files are not read again on every click
    models = {name: joblib.load(MODEL_FOLDER / f"{name}_model.joblib") for name in DISEASE_TEXT}
    feature_names = joblib.load(MODEL_FOLDER / "feature_names.joblib")
    percentiles = joblib.load(MODEL_FOLDER / "score_percentiles.joblib")
    return models, feature_names, percentiles


def load_css():
    css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------- state
# step 0 = welcome, 1 to 6 = the questions, 7 = optional questions, 8 = results
if "step" not in st.session_state:
    st.session_state.step = 0
    st.session_state.answers = {}
    st.session_state.run = 0          # goes up on "Start again", so every box starts empty
    st.session_state.error = ""


def wkey(name):
    return f"{name}_{st.session_state.run}"


def go(step):
    st.session_state.step = step
    st.session_state.error = ""


def start_again():
    st.session_state.answers = {}
    st.session_state.run += 1
    go(0)


def choose(name, label):
    # a tapped option: save it and move straight on
    st.session_state.answers[name] = label
    go(st.session_state.step + 1)


def save_age():
    age = st.session_state[wkey("age")]
    if age is None:
        st.session_state.error = "Please enter your age."
    else:
        st.session_state.answers["age"] = int(age)
        go(2)


def save_body():
    height = st.session_state[wkey("height")]
    weight = st.session_state[wkey("weight")]
    if not height or not weight:
        st.session_state.error = "Please enter both your height and your weight."
        return
    bmi = weight / (height / 100) ** 2
    if not opt.BMI_RANGE[0] <= bmi <= opt.BMI_RANGE[1]:
        st.session_state.error = (f"Those numbers give a BMI of {bmi:.1f}, outside the range this tool "
                                  f"learned from ({opt.BMI_RANGE[0]} to {opt.BMI_RANGE[1]}). Please check them.")
        return
    st.session_state.answers["height"] = height
    st.session_state.answers["weight"] = weight
    go(4)


def save_optional():
    answers = st.session_state.answers
    for name in ["smoking", "activity", "income", "education"]:
        value = st.session_state[wkey(name)]
        if value is None:
            answers.pop(name, None)      # skipped: the typical answer is used later
        else:
            answers[name] = value
    for name in ["drinks", "physical_days", "mental_days"]:
        answers[name] = st.session_state[wkey(name)]
    go(8)


# ---------------------------------------------------------------- small pieces of the page
def header(step):
    st.markdown(f'<div class="brand">{HEART}PurvAarogya</div>', unsafe_allow_html=True)
    if 1 <= step <= 7:
        done = min(step, 6)
        dots = "".join(f'<span class="{"on" if i < done else ""}"></span>' for i in range(6))
        text = f"Question {step} of 6" if step <= 6 else "Almost there"
        st.markdown(f'<div class="dots">{dots}</div><p class="dots-text">{text}</p>', unsafe_allow_html=True)


def question(title, why):
    st.markdown(f'<h2 class="q">{title}</h2><p class="why">{why}</p>', unsafe_allow_html=True)


def show_error():
    if st.session_state.error:
        st.markdown(f'<p class="error">{st.session_state.error}</p>', unsafe_allow_html=True)


def back_button():
    st.button("← Back", key="back", on_click=go, args=(st.session_state.step - 1,))


def next_button(on_click):
    st.button("Next", key="next", type="primary", on_click=on_click)


# ---------------------------------------------------------------- the screens
def welcome_screen():
    st.markdown(HERO, unsafe_allow_html=True)
    st.markdown('<h1 class="hello">Hi! Let\'s check in on your health.</h1>'
                '<p class="hello-sub">Answer six quick questions and see how your answers compare with '
                '400,000 other people in a large US health survey.</p>'
                '<p class="note"><b>Nothing you enter is saved.</b> It takes about a minute.</p>',
                unsafe_allow_html=True)
    st.button("Let's begin", key="go", type="primary", on_click=go, args=(1,))


def age_screen():
    question("How old are you?", "Age is one of the biggest things doctors weigh for diabetes, heart disease and stroke.")
    st.number_input("Age in years", min_value=opt.AGE_RANGE[0], max_value=opt.AGE_RANGE[1], step=1,
                    value=st.session_state.answers.get("age"), placeholder="For example, 42",
                    key=wkey("age"), label_visibility="collapsed")
    show_error()
    next_button(save_age)
    back_button()


def body_screen():
    question("How tall are you, and how much do you weigh?", "We use these to work out your BMI.")
    a = st.session_state.answers
    c1, c2 = st.columns(2)
    height = c1.number_input("Height (cm)", min_value=120, max_value=220, step=1, value=a.get("height"),
                             placeholder="e.g. 165", key=wkey("height"))
    weight = c2.number_input("Weight (kg)", min_value=30.0, max_value=250.0, step=0.5, format="%.1f",
                             value=a.get("weight"), placeholder="e.g. 65", key=wkey("weight"))
    if height and weight:
        st.markdown(f'<p class="bmi-line">Your BMI is <b>{weight / (height / 100) ** 2:.1f}</b></p>',
                    unsafe_allow_html=True)
    show_error()
    next_button(save_body)
    back_button()


def choice_screen(title, why, name, options):
    question(title, why)
    current = st.session_state.answers.get(name)
    with st.container(key="options"):
        for label in options:
            selected = current == label
            st.button(("✓  " if selected else "") + label, key=f"opt_{name}_{label}",
                      type="primary" if selected else "secondary", on_click=choose, args=(name, label))
    if current is not None:             # coming back to change an earlier answer
        st.button("Next", key="next", type="primary", on_click=go, args=(st.session_state.step + 1,))
    back_button()


def optional_screen():
    question("Want a sharper result?", "These seven are optional. Skip any you like and we use the most "
             "common answer from the survey.")
    a = st.session_state.answers

    def start_index(name, options):
        return list(options).index(a[name]) if name in a else None

    st.markdown('<p class="group">Habits</p>', unsafe_allow_html=True)
    st.segmented_control("Do you smoke?", list(opt.SMOKING), default=a.get("smoking"), key=wkey("smoking"))
    st.segmented_control("Any exercise or physical activity in the past 30 days, outside of work?",
                         list(opt.ACTIVITY), default=a.get("activity"), key=wkey("activity"))
    st.slider("Alcoholic drinks in a typical week", 0, 50, a.get("drinks", 0), key=wkey("drinks"))

    st.markdown('<p class="group">The past 30 days</p>', unsafe_allow_html=True)
    st.slider("Days your physical health was not good", 0, 30, a.get("physical_days", 0), key=wkey("physical_days"))
    st.slider("Days your mental health was not good", 0, 30, a.get("mental_days", 0), key=wkey("mental_days"))

    st.markdown('<p class="group">Background</p>', unsafe_allow_html=True)
    st.selectbox("Household income per year (US dollars, the survey is American)", list(opt.INCOME),
                 index=start_index("income", opt.INCOME), placeholder="Choose", key=wkey("income"))
    st.selectbox("Education", list(opt.EDUCATION), index=start_index("education", opt.EDUCATION),
                 placeholder="Choose", key=wkey("education"))

    st.button("See my results", key="see", type="primary", on_click=save_optional)
    back_button()


# ---------------------------------------------------------------- results
def build_person(a, feature_names):
    """One row in the training format and column order. Skipped optional answers use the typical one."""
    typical = opt.TYPICAL
    row = {
        "genhlth": opt.GENERAL_HEALTH[a["general_health"]],
        "_bmi5": a["weight"] / (a["height"] / 100) ** 2,
        "_smoker3": opt.SMOKING[a["smoking"]] if "smoking" in a else typical["smoking"],
        "_drnkwk2": a.get("drinks", typical["drinks"]),
        "_totinda": opt.ACTIVITY[a["activity"]] if "activity" in a else typical["activity"],
        "menthlth": a.get("mental_days", typical["mental_days"]),
        "physhlth": a.get("physical_days", typical["physical_days"]),
        "bphigh6": opt.BLOOD_PRESSURE[a["blood_pressure"]],
        "_rfchol3": opt.CHOLESTEROL[a["cholesterol"]],
        "_ageg5yr": opt.age_group(a["age"]),
        "_sex": opt.SEX[a["sex"]],
        "income3": opt.INCOME[a["income"]] if "income" in a else typical["income"],
        "_educag": opt.EDUCATION[a["education"]] if "education" in a else typical["education"],
    }
    return pd.DataFrame([row])[feature_names]


def gauge_point(percent, radius=88):
    angle = math.pi * (1 - percent / 100)        # 0 = far left of the half circle, 100 = far right
    return 110 + radius * math.cos(angle), 108 - radius * math.sin(angle)


def gauge_arc(start, end):
    x1, y1 = gauge_point(start)
    x2, y2 = gauge_point(end)
    return f"M {x1:.1f} {y1:.1f} A 88 88 0 0 1 {x2:.1f} {y2:.1f}"


def gauge_svg(percentile, flag_line):
    """Half circle in three zones. The Higher zone starts exactly at the flag line."""
    flag_line = min(max(flag_line, 10), 95)
    cuts = [0, flag_line / 2, flag_line, 100]
    colours = ["#4F9D7B", "#E9A23B", "#C8415B"]
    gap = 1.3                                     # small gap between the zones
    arcs = ""
    for i in range(3):
        start = cuts[i] + (gap if i > 0 else 0)
        end = cuts[i + 1] - (gap if i < 2 else 0)
        arcs += f'<path d="{gauge_arc(start, end)}" stroke="{colours[i]}" stroke-width="16" fill="none"/>'
    x, y = gauge_point(min(max(percentile, 2), 98))
    marker = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#fff" stroke="#3B2F2A" stroke-width="4"/>'
    return f'<svg class="gauge" viewBox="0 0 220 124" aria-hidden="true">{arcs}{marker}</svg>'


def risk_card(disease, r):
    name, note, _, _ = DISEASE_TEXT[disease]
    note_html = f'<span class="risk-sub">{note}</span>' if note else ""
    chips = ""
    if r["pushing_up"]:
        chips += ('<div class="chips"><span class="chips-label">Pushing it up</span>'
                  + "".join(f'<span class="chip up">{c}</span>' for c in r["pushing_up"]) + "</div>")
    if r["pulling_down"]:
        chips += ('<div class="chips"><span class="chips-label">Helping</span>'
                  + "".join(f'<span class="chip down">{c}</span>' for c in r["pulling_down"]) + "</div>")
    return f"""
<div class="risk-card">
  <div class="risk-top"><h3 class="risk-name">{name}</h3>{note_html}</div>
  {gauge_svg(r['percentile'], r['flag_line'])}
  <p class="risk-level lvl-{r['level']}">{r['level']} range</p>
  <p class="risk-line">Your answers score higher than <b>{r['percentile']} of every 100</b> people in the survey.</p>
  {chips}
</div>"""


def join_names(names):
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def results_screen():
    models, feature_names, percentiles = load_models()
    a = st.session_state.answers
    results = assess(models, percentiles, build_person(a, feature_names))

    higher = [DISEASE_TEXT[d][0] for d, r in results.items() if r["level"] == "Higher"]
    middle = [d for d, r in results.items() if r["level"] == "Moderate"]
    if higher:
        verb = "is" if len(higher) == 1 else "are"
        summary = f"Worth a closer look: {join_names(higher)} {verb} in the higher range."
    elif middle:
        summary = "None of the three is in the higher range, but a few sit in the middle."
    else:
        summary = "Good news: none of the three is in the higher range."

    skipped = [n for n in ["smoking", "activity", "income", "education"] if n not in a]
    if skipped:
        basis = (f"For the questions you skipped ({', '.join(skipped)}) we used the typical survey answer. "
                 "Answer them for a sharper result.")
    else:
        basis = "Based on all your answers."

    st.markdown(f'<h1 class="res-title">Here is how your answers compare</h1><p class="res-sum">{summary}</p>'
                f'<p class="res-basis">{basis}</p>', unsafe_allow_html=True)
    for disease in DISEASE_TEXT:
        st.markdown(risk_card(disease, results[disease]), unsafe_allow_html=True)

    if higher:
        next_step = ("<h3>A gentle next step</h3>A higher range is a good reason to ask a doctor for a simple "
                     "test: blood sugar for diabetes, and blood pressure and cholesterol for heart disease and stroke.")
    else:
        next_step = ("<h3>Keep in mind</h3>A lower range is not a clean bill of health. This tool only sees a few "
                     "answers. If you have symptoms or worries, please see a doctor.")
    st.markdown(f'<div class="next-card">{next_step}</div>', unsafe_allow_html=True)

    with st.expander("How accurate is this?"):
        rows = "".join(f"<tr><td>{DISEASE_TEXT[d][0]}</td><td>{DISEASE_TEXT[d][2]} in 100</td>"
                       f"<td>{DISEASE_TEXT[d][3]} in 100</td></tr>" for d in DISEASE_TEXT)
        st.markdown(f"""
<table class="hit-table">
<tr><th></th><th>People with it who get flagged</th><th>Flags that are right</th></tr>
{rows}
</table>
<p class="fineprint" style="margin-top:0">Measured on 119,244 survey respondents the model had never seen, using all
13 answers. "Higher range" is a flag: the model is set to miss few people, so it also flags many who are fine. Most
flags are false alarms, especially for stroke, which is rare. Treat it as a reason to get checked, not as a result.</p>
<p class="fineprint" style="margin-top:.8rem">The model is a logistic regression trained on the 2023 CDC Behavioral
Risk Factor Surveillance System, a survey of US adults, so it may fit other populations less well. It sees only these
13 answers, with no blood tests or family history. Skipped optional questions and "not sure" about cholesterol use the
most common answer in the survey, as the model did in training. Drinks, smoking and the days of poor health count in
the score but are not listed as factors, because on their own they are easy to misread (for example, in this survey
people who are ill often drink less).</p>
""", unsafe_allow_html=True)

    st.button("Change my answers", key="edit", on_click=go, args=(1,))
    st.button("Start again", key="again", on_click=start_again)
    st.markdown(f'<p class="fineprint">This tool cannot replace a doctor. <a href="{GITHUB_URL}">Source code</a></p>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- page
load_css()
step = st.session_state.step
header(step)

if step == 8:
    results_screen()
else:
    with st.container(key="card"):
        if step == 0:
            welcome_screen()
        elif step == 1:
            age_screen()
        elif step == 2:
            choice_screen("What is your sex?", "The survey recorded sex as male or female, so the tool uses "
                          "those two options.", "sex", opt.SEX)
        elif step == 3:
            body_screen()
        elif step == 4:
            choice_screen("How would you describe your health in general?",
                          "Just your own sense of it. There is no wrong answer.", "general_health", opt.GENERAL_HEALTH)
        elif step == 5:
            choice_screen("Has a doctor ever told you that you have high blood pressure?",
                          "Borderline means a doctor said it was close to high.", "blood_pressure", opt.BLOOD_PRESSURE)
        elif step == 6:
            choice_screen("Has a doctor ever told you that you have high cholesterol?",
                          "If you are not sure, choose Not sure. We will use the most common answer, which is No.",
                          "cholesterol", opt.CHOLESTEROL)
        else:
            optional_screen()
