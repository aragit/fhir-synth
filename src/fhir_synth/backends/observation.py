import hashlib
import random
from datetime import timedelta

from fhir_synth.models import ClinicalTimeline, SynthConfig, TrendConfig


class ObservationBackend:
    SUPPORTED_LOINC = {
        "8867-4": ("heart_rate", "bpm", (40, 200)),
        "8480-6": ("systolic_bp", "mmHg", (60, 250)),
        "8462-4": ("diastolic_bp", "mmHg", (30, 150)),
        "2708-6": ("spo2", "%", (70, 100)),
        "9279-1": ("respiratory_rate", "rpm", (4, 60)),
        "8310-5": ("temperature", "Cel", (30.0, 43.0)),
    }

    LOINC_KEY_MAP = {
        "8867-4": "heart_rate",
        "8480-6": "systolic_bp",
        "8462-4": "diastolic_bp",
        "2708-6": "spo2",
        "9279-1": "respiratory_rate",
        "8310-5": "temperature",
    }

    KEY_TO_LOINC = {v: k for k, v in LOINC_KEY_MAP.items()}

    @property
    def resource_type(self) -> str:
        return "Observation"

    def _make_uuid(self, seed: str, timestamp: int, loinc: str) -> str:
        raw = f"{seed}-{timestamp}-{loinc}"
        h = hashlib.md5(raw.encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    def generate(
        self, timeline: ClinicalTimeline, config: SynthConfig
    ) -> list[dict]:
        seed_str = str(timeline.seed or 0)
        rng = random.Random(timeline.seed)
        resources: list[dict] = []

        drift_events = [
            e for e in timeline.events if e.event_type == "vital_drift"
        ]

        for event in drift_events:
            t = event.timestamp_minutes
            for loinc, (key, unit, bounds) in self.SUPPORTED_LOINC.items():
                if key not in event.parameters:
                    continue
                p = event.parameters[key]
                trend_cfg = TrendConfig(
                    trend_type=p.get("trend_type", "linear"),
                    slope=p.get("slope", 0.0),
                    baseline=p.get("baseline", 0.0),
                    noise_std=p.get("noise_std", 0.0),
                    dropout_rate=p.get("dropout_rate", 0.0),
                    min_value=p.get("min_value", bounds[0]),
                    max_value=p.get("max_value", bounds[1]),
                )
                value = _evaluate_parameter(t, trend_cfg, rng)

                if value is None:
                    continue
                value = max(bounds[0], min(bounds[1], value))

                obs_id = self._make_uuid(seed_str, t, loinc)
                effective = (timeline.start_time + timedelta(minutes=t)).isoformat()
                resource = {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": loinc,
                                "display": key.replace("_", " ").title(),
                            }
                        ]
                    },
                    "subject": {"reference": f"Patient/{timeline.patient_id}"},
                    "effectiveDateTime": effective,
                    "valueQuantity": {
                        "value": round(value, 2),
                        "unit": unit,
                        "system": "http://unitsofmeasure.org",
                        "code": unit,
                    },
                }
                resources.append(resource)

        return resources


def _evaluate_parameter(
    t: int, cfg: TrendConfig, rng: random.Random
) -> float | None:
    from fhir_synth.trends import apply_trend
    values = apply_trend(cfg, [t], rng)
    return values[0]
