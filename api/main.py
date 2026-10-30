"""FastAPI app for PurvAarogya. The models are loaded once, when the server starts."""
from contextlib import asynccontextmanager
from pathlib import Path

import joblib
from fastapi import FastAPI

from api.schemas import PredictRequest
from purvarogya.inputs import build_person
from purvarogya.scoring import assess

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
DISEASES = ["diabetes", "cvd", "stroke"]

# holds the loaded files so every request can reuse them
state = {}


@asynccontextmanager
async def lifespan(app):
    # runs once at startup: load the models instead of loading them on every request
    state["models"] = {d: joblib.load(MODEL_DIR / f"{d}_model.joblib") for d in DISEASES}
    state["feature_names"] = joblib.load(MODEL_DIR / "feature_names.joblib")
    state["percentiles"] = joblib.load(MODEL_DIR / "score_percentiles.joblib")
    yield
    state.clear()


app = FastAPI(title="PurvAarogya", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "models_loaded": list(state["models"])}

# these two were never asked in the app, so we don't show them as reasons
HIDDEN_FACTORS = {"education", "income"}


@app.post("/predict")
def predict(request: PredictRequest):
    # request is already validated by pydantic, so the values are safe to use
    person = build_person(**request.model_dump(), feature_names=state["feature_names"])
    results = assess(state["models"], state["percentiles"], person)

    for result in results.values():
        result["pushing_up"] = [f for f in result["pushing_up"] if f not in HIDDEN_FACTORS]
        result["pulling_down"] = [f for f in result["pulling_down"] if f not in HIDDEN_FACTORS]

    return results

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(WEB_DIR / "index.html")


# serves style.css and app.js; keep this after the routes above
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

