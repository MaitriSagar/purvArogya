"""Rules for what the API accepts. Pydantic checks every request before our code runs."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class PredictRequest(BaseModel):
    # required answers
    age: int = Field(ge=18, le=99, description="Age in years")
    sex: Literal["Male", "Female"]
    height_cm: float = Field(ge=120, le=220)
    weight_kg: float = Field(ge=30, le=250)
    general_health: Literal["Excellent", "Very good", "Good", "Fair", "Poor"]
    blood_pressure: Literal["No", "Borderline", "Yes"]
    cholesterol: Literal["No", "Yes", "Not sure"]

    # optional answers, None means the person skipped the question
    smoking: Optional[Literal["Every day", "Some days", "Used to", "Never"]] = None
    activity: Optional[Literal["Yes", "No"]] = None
    drinks: Optional[float] = Field(default=None, ge=0, le=50)
    physical_days: Optional[int] = Field(default=None, ge=0, le=30)
    mental_days: Optional[int] = Field(default=None, ge=0, le=30)

    @model_validator(mode="after")
    def bmi_must_be_realistic(self):
        # the models were trained on BMI 12 to 100, so anything outside is not a real answer
        bmi = self.weight_kg / (self.height_cm / 100) ** 2
        if not 12 <= bmi <= 100:
            raise ValueError(f"height and weight give BMI {bmi:.1f}, outside 12 to 100")
        return self