from datetime import datetime

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent


def build(
    config: SynthConfig, seed: int | None = None, start_time: datetime | None = None
) -> ClinicalTimeline:
    if start_time is None:
        from datetime import timezone

        start_time = datetime.now(timezone.utc)

    events: list[TimelineEvent] = []
    for t in range(0, config.duration_minutes + 1, config.sample_interval_minutes):
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": 72, "slope": 0, "noise_std": 3.6},
                    "systolic_bp": {"trend_type": "linear", "baseline": 120, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": 80, "slope": 0, "noise_std": 4.0},
                    "spo2": {"trend_type": "linear", "baseline": 98, "slope": 0, "noise_std": 1.0},
                    "respiratory_rate": {"trend_type": "linear", "baseline": 16, "slope": 0, "noise_std": 0.8},
                    "temperature": {"trend_type": "linear", "baseline": 36.5, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    return ClinicalTimeline(
        patient_id=f"normal-{seed or 0}",
        start_time=start_time,
        events=events,
        seed=seed,
    )
