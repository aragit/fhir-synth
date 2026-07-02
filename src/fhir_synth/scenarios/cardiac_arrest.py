from datetime import datetime

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent


def build(
    config: SynthConfig, seed: int | None = None, start_time: datetime | None = None
) -> ClinicalTimeline:
    if start_time is None:
        from datetime import timezone

        start_time = datetime.now(timezone.utc)

    events: list[TimelineEvent] = []

    max_normal = min(120, config.duration_minutes)
    for t in range(0, max_normal, config.sample_interval_minutes):
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

    max_vtach = min(122, config.duration_minutes)
    for t in range(120, max_vtach, config.sample_interval_minutes):
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": 180, "slope": 0, "noise_std": 0},
                    "respiratory_rate": {"trend_type": "linear", "baseline": 8, "slope": 0, "noise_std": 2},
                    "spo2": {"trend_type": "linear", "baseline": 85, "slope": 0, "noise_std": 3},
                    "systolic_bp": {"trend_type": "linear", "baseline": 60, "slope": 0, "noise_std": 5},
                    "diastolic_bp": {"trend_type": "linear", "baseline": 30, "slope": 0, "noise_std": 5},
                    "temperature": {"trend_type": "linear", "baseline": 36.5, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    max_flatline = min(123, config.duration_minutes)
    for t in range(122, max_flatline, config.sample_interval_minutes):
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": 0, "slope": 0, "noise_std": 0},
                    "respiratory_rate": {"trend_type": "linear", "baseline": 0, "slope": 0, "noise_std": 0},
                    "spo2": {"trend_type": "linear", "baseline": 70, "slope": -5, "min_value": 40, "noise_std": 2},
                    "systolic_bp": {"trend_type": "linear", "baseline": 0, "slope": 0, "noise_std": 0},
                    "diastolic_bp": {"trend_type": "linear", "baseline": 0, "slope": 0, "noise_std": 0},
                    "temperature": {"trend_type": "linear", "baseline": 36.5, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    for t in range(123, config.duration_minutes + 1, config.sample_interval_minutes):
        rng_seed = f"{seed or 0}-{t}"
        import hashlib
        h = hashlib.md5(rng_seed.encode()).hexdigest()
        hr_seed = int(h[:8], 16)
        import random
        r = random.Random(hr_seed)
        hr_cpr = r.randint(60, 120)
        rr_cpr = r.uniform(5, 15)
        spo2_cpr = r.uniform(70, 90)
        sbp_cpr = r.uniform(60, 100)
        events.append(
            TimelineEvent(
                event_type="vital_drift",
                timestamp_minutes=t,
                parameters={
                    "heart_rate": {"trend_type": "linear", "baseline": hr_cpr, "slope": 0, "noise_std": 10},
                    "respiratory_rate": {"trend_type": "linear", "baseline": rr_cpr, "slope": 0, "noise_std": 3},
                    "spo2": {"trend_type": "linear", "baseline": spo2_cpr, "slope": 0, "noise_std": 5},
                    "systolic_bp": {"trend_type": "linear", "baseline": sbp_cpr, "slope": 0, "noise_std": 10},
                    "diastolic_bp": {"trend_type": "linear", "baseline": max(sbp_cpr - 30, 20), "slope": 0, "noise_std": 10},
                    "temperature": {"trend_type": "linear", "baseline": 36.5, "slope": 0, "noise_std": 0.2},
                },
            )
        )

    events.append(
        TimelineEvent(
            event_type="diagnosis",
            timestamp_minutes=122,
            parameters={"code": "I46.9", "display": "Cardiac arrest, cause unspecified"},
        )
    )
    events.append(
        TimelineEvent(
            event_type="procedure",
            timestamp_minutes=123,
            parameters={"code": "5A12012", "display": "CPR initiated"},
        )
    )

    return ClinicalTimeline(
        patient_id=f"arrest-{seed or 0}",
        start_time=start_time,
        events=events,
        seed=seed,
    )
