from datetime import datetime

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent


def build(
    config: SynthConfig, seed: int | None = None, start_time: datetime | None = None
) -> ClinicalTimeline:
    if start_time is None:
        from datetime import timezone

        start_time = datetime.now(timezone.utc)

    events: list[TimelineEvent] = []

    events.append(
        TimelineEvent(
            event_type="procedure",
            timestamp_minutes=0,
            parameters={"code": "0FT44ZZ", "display": "Laparoscopic cholecystectomy"},
        )
    )

    for t in range(0, config.duration_minutes + 1, config.sample_interval_minutes):
        if t <= 30:
            hr = 110 - 0.3 * t
            rr = 22 - 0.1 * t
            sbp = 140 - 0.5 * t
            dbp = 90 - 0.3 * t
            temp = 37.2
        elif t <= 120:
            dt = t - 30
            decay = 2.718 ** (-dt / 45)
            hr = 80 + 27 * decay
            rr = 16 + 5 * decay
            sbp = 120 + 15 * decay
            dbp = 80 + 7 * decay
            temp = 36.5 + 0.5 * decay
        else:
            hr = 80
            rr = 16
            sbp = 120
            dbp = 80
            temp = 36.5

        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr, "slope": 0, "noise_std": hr * 0.05},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr, "slope": 0, "noise_std": rr * 0.05},
                    "spo2": {"trend_type": "linear", "baseline": 97, "slope": 0, "noise_std": 1.0},
                    "systolic_bp": {"trend_type": "linear", "baseline": sbp, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": dbp, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": temp, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    return ClinicalTimeline(
        patient_id=f"postop-{seed or 0}",
        start_time=start_time,
        events=events,
        seed=seed,
    )
