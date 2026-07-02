from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TrendConfig(BaseModel):
    trend_type: Literal["linear", "exponential", "step", "sinusoidal"]
    slope: float | None = None
    half_life: float | None = None
    amplitude: float | None = None
    period_minutes: float | None = None
    baseline: float = 0.0
    noise_std: float = 0.0
    dropout_rate: float = 0.0
    min_value: float | None = None
    max_value: float | None = None


class TimelineEvent(BaseModel):
    event_type: str
    timestamp_minutes: int
    parameters: dict = Field(default_factory=dict)


class ClinicalTimeline(BaseModel):
    patient_id: str
    start_time: datetime
    events: list[TimelineEvent]
    seed: int | None = None


class SynthConfig(BaseModel):
    duration_minutes: int = 240
    sample_interval_minutes: int = 1
    backends: list[str] = Field(default_factory=lambda: ["observation", "patient", "encounter"])
