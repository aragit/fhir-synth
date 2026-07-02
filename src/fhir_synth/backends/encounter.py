import hashlib
from datetime import timezone, timedelta


class EncounterBackend:
    @property
    def resource_type(self) -> str:
        return "Encounter"

    def _make_uuid(self, seed: str) -> str:
        h = hashlib.md5(f"encounter-{seed}".encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    def generate(
        self, timeline: "ClinicalTimeline", config: "SynthConfig"
    ) -> list[dict]:
        from fhir_synth.models import ClinicalTimeline, SynthConfig

        seed_str = str(timeline.seed or 0)
        enc_id = self._make_uuid(seed_str)

        diagnosis_events = [e for e in timeline.events if e.event_type == "diagnosis"]
        procedure_events = [e for e in timeline.events if e.event_type == "procedure"]

        start_dt = timeline.start_time
        end_dt = start_dt + timedelta(minutes=config.duration_minutes)

        type_codings = []
        for e in diagnosis_events[:1]:
            type_codings.append(
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/icd-10-cm",
                            "code": e.parameters.get("code", "Z00.00"),
                            "display": e.parameters.get("display", ""),
                        }
                    ]
                }
            )

        resource = {
            "resourceType": "Encounter",
            "id": enc_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter",
            },
            "type": type_codings if type_codings else [{"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "Z00.00", "display": "Medical examination"}]}],
            "subject": {"reference": f"Patient/{timeline.patient_id}"},
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
            },
        }
        return [resource]
