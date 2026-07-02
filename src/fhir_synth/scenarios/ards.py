from datetime import datetime

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent


def build(
    config: SynthConfig, seed: int | None = None, start_time: datetime | None = None
) -> ClinicalTimeline:
    if start_time is None:
        from datetime import timezone

        start_time = datetime.now(timezone.utc)

    events: list[TimelineEvent] = []

    for t in range(0, min(31, config.duration_minutes + 1), config.sample_interval_minutes):
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": 72, "slope": 0, "noise_std": 3.6},
                    "respiratory_rate": {"trend_type": "linear", "baseline": 16, "slope": 0, "noise_std": 0.8},
                    "spo2": {"trend_type": "linear", "baseline": 98, "slope": 0, "noise_std": 1.0},
                    "systolic_bp": {"trend_type": "linear", "baseline": 120, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": 80, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": 36.5, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    for t in range(30, min(61, config.duration_minutes + 1), config.sample_interval_minutes):
        dt = t - 30
        spo2 = max(98 - (13 / 30) * dt, 85)
        rr = min(16 + (19 / 30) * dt, 35)
        hr = 72 + dt * 1.5
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr, "slope": 0, "noise_std": hr * 0.05},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr, "slope": 0, "noise_std": rr * 0.05},
                    "spo2": {"trend_type": "linear", "baseline": spo2, "slope": 0, "noise_std": 0.5},
                    "systolic_bp": {"trend_type": "linear", "baseline": 125, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": 80, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": 37.0, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    for t in range(60, config.duration_minutes + 1, config.sample_interval_minutes):
        hr = 120 + (t - 60) * 0.1
        rr = 30 + (t - 60) * 0.02
        spo2 = 85 - 0.01 * (t - 60) + 2 * ((t % 20) / 20 - 0.5)
        spo2 = max(82, min(88, spo2))
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr, "slope": 0, "noise_std": hr * 0.05},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr, "slope": 0, "noise_std": rr * 0.05},
                    "spo2": {"trend_type": "linear", "baseline": spo2, "slope": 0, "noise_std": 0.5},
                    "systolic_bp": {"trend_type": "linear", "baseline": 100, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": 60, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": 37.5, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    events.append(
        TimelineEvent(
            event_type="diagnosis",
            timestamp_minutes=45,
            parameters={"code": "J80", "display": "Acute respiratory distress syndrome"},
        )
    )
    events.append(
        TimelineEvent(
            event_type="procedure",
            timestamp_minutes=60,
            parameters={"code": "0BH17EZ", "display": "Intubation"},
        )
    )

    return ClinicalTimeline(
        patient_id=f"ards-{seed or 0}",
        start_time=start_time,
        events=events,
        seed=seed,
    )
