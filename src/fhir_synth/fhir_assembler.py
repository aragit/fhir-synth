from fhir_synth.backends.encounter import EncounterBackend
from fhir_synth.backends.observation import ObservationBackend
from fhir_synth.backends.patient import PatientBackend
from fhir_synth.models import ClinicalTimeline, SynthConfig
from fhir_synth.validator import validate_fhir_resource


_BACKEND_MAP = {
    "observation": ObservationBackend,
    "patient": PatientBackend,
    "encounter": EncounterBackend,
}


def _build_bundle_entry(resource: dict) -> dict:
    return {
        "fullUrl": f"urn:uuid:{resource['id']}",
        "resource": resource,
    }


def assemble_fhir_bundle(timeline: ClinicalTimeline, config: SynthConfig) -> dict:
    entries: list[dict] = []

    for backend_name in config.backends:
        backend_cls = _BACKEND_MAP.get(backend_name)
        if backend_cls is None:
            msg = f"Unknown backend: {backend_name}"
            raise ValueError(msg)
        backend = backend_cls()
        resources = backend.generate(timeline, config)
        for resource in resources:
            validate_fhir_resource(resource, resource.get("resourceType"))
            entries.append(_build_bundle_entry(resource))

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
    }
    return bundle


def assemble_patient(timeline: ClinicalTimeline) -> dict:
    backend = PatientBackend()
    resources = backend.generate(timeline, SynthConfig())
    return resources[0] if resources else {}


def assemble_observations(
    timeline: ClinicalTimeline, config: SynthConfig
) -> list[dict]:
    backend = ObservationBackend()
    return backend.generate(timeline, config)


def assemble_encounter(timeline: ClinicalTimeline) -> dict | None:
    backend = EncounterBackend()
    resources = backend.generate(timeline, SynthConfig())
    return resources[0] if resources else None
