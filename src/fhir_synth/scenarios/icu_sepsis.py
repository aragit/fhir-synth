from datetime import datetime

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent


def build(
    config: SynthConfig, seed: int | None = None, start_time: datetime | None = None
) -> ClinicalTimeline:
    if start_time is None:
        from datetime import timezone

        start_time = datetime.now(timezone.utc)

    events: list[TimelineEvent] = []

    for t in range(0, min(61, config.duration_minutes + 1), config.sample_interval_minutes):
        hr = 72 + 0.5 * t
        rr = 16 + 0.2 * t
        spo2 = 98 - 0.05 * t
        sbp = 120
        dbp = 80
        temp = 36.5 + 0.01 * t
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr, "slope": 0, "noise_std": hr * 0.05},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr, "slope": 0, "noise_std": rr * 0.05},
                    "spo2": {"trend_type": "linear", "baseline": spo2, "slope": 0, "noise_std": 1.0},
                    "systolic_bp": {"trend_type": "linear", "baseline": sbp, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": dbp, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": temp, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    for t in range(60, min(121, config.duration_minutes + 1), config.sample_interval_minutes):
        hr = 72 + 0.5 * 60 + 1.0 * (t - 60)
        rr = 16 + 0.2 * 60 + 0.4 * (t - 60)
        spo2 = 98 - 0.05 * 60 - 0.1 * (t - 60)
        sbp = 120 - 0.3 * (t - 60)
        dbp = 80 - 0.2 * (t - 60)
        temp = 36.5 + 0.01 * 60 + 0.02 * (t - 60)
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr, "slope": 0, "noise_std": hr * 0.05},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr, "slope": 0, "noise_std": rr * 0.05},
                    "spo2": {"trend_type": "linear", "baseline": spo2, "slope": 0, "noise_std": 1.0},
                    "systolic_bp": {"trend_type": "linear", "baseline": sbp, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": dbp, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": temp, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    for t in range(120, config.duration_minutes + 1, config.sample_interval_minutes):
        dt = t - 120
        hr = min(140 + 0.3 * dt, 160)
        rr = min(28 + 0.1 * dt, 40)
        spo2 = max(88 - 0.05 * dt, 82)
        sbp = max(120 - 1.0 * dt, 70)
        dbp = max(80 - 0.5 * dt, 40)
        temp = 39.5
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr, "slope": 0, "noise_std": hr * 0.05},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr, "slope": 0, "noise_std": rr * 0.05},
                    "spo2": {"trend_type": "linear", "baseline": spo2, "slope": 0, "noise_std": 1.0},
                    "systolic_bp": {"trend_type": "linear", "baseline": sbp, "slope": 0, "noise_std": 6.0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": dbp, "slope": 0, "noise_std": 4.0},
                    "temperature": {"trend_type": "linear", "baseline": temp, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    events.append(
        TimelineEvent(
            event_type="diagnosis",
            timestamp_minutes=30,
            parameters={"code": "A41.9", "display": "Sepsis, unspecified organism"},
        )
    )
    events.append(
        TimelineEvent(
            event_type="diagnosis",
            timestamp_minutes=60,
            parameters={"code": "R65.20", "display": "Severe sepsis without septic shock"},
        )
    )
    events.append(
        TimelineEvent(
            event_type="procedure",
            timestamp_minutes=90,
            parameters={"code": "03EO3ZZ", "display": "Central line placement"},
        )
    )

    return ClinicalTimeline(
        patient_id=f"sepsis-{seed or 0}",
        start_time=start_time,
        events=events,
        seed=seed,
    )
