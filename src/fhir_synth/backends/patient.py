import hashlib
import random
from datetime import datetime, timezone, timedelta


class PatientBackend:
    @property
    def resource_type(self) -> str:
        return "Patient"

    def generate(
        self, timeline: "ClinicalTimeline", config: "SynthConfig"
    ) -> list[dict]:
        from fhir_synth.models import ClinicalTimeline, SynthConfig

        seed_str = str(timeline.seed or 0)
        rng = random.Random(timeline.seed)
        pat_id = timeline.patient_id
        gender = rng.choice(["male", "female"])
        age = rng.randint(18, 90)
        birth_date = (datetime.now(timezone.utc) - timedelta(days=age * 365.25)).strftime("%Y-%m-%d")

        resource = {
            "resourceType": "Patient",
            "id": pat_id,
            "identifier": [
                {
                    "system": "https://github.com/aragit/fhir-synth",
                    "value": pat_id,
                }
            ],
            "gender": gender,
            "birthDate": birth_date,
            "deceasedBoolean": False,
        }
        return [resource]
