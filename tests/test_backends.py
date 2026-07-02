import pytest

from fhir_synth.backends.encounter import EncounterBackend
from fhir_synth.backends.observation import ObservationBackend
from fhir_synth.backends.patient import PatientBackend
from fhir_synth.backends.base import ResourceBackend
from fhir_synth.models import ClinicalTimeline, SynthConfig
from datetime import datetime, timezone


def _check_protocol(obj):
    assert hasattr(obj, "generate")
    assert hasattr(obj, "resource_type")
    assert callable(obj.generate)
    assert isinstance(obj.resource_type, str)


@pytest.fixture
def normal_timeline():
    from fhir_synth.timeline import build_timeline
    return build_timeline("normal", SynthConfig(duration_minutes=10), seed=42)


@pytest.fixture
def sepsis_timeline():
    from fhir_synth.timeline import build_timeline
    return build_timeline("icu_sepsis", SynthConfig(duration_minutes=240), seed=42)


class TestObservationBackend:
    def test_protocol_compliance(self):
        _check_protocol(ObservationBackend())

    def test_resource_type(self):
        assert ObservationBackend().resource_type == "Observation"

    def test_generate_returns_list(self, normal_timeline):
        backend = ObservationBackend()
        config = SynthConfig(duration_minutes=10)
        resources = backend.generate(normal_timeline, config)
        assert isinstance(resources, list)
        assert len(resources) > 0

    def test_all_have_resource_type(self, normal_timeline):
        backend = ObservationBackend()
        config = SynthConfig(duration_minutes=10)
        for r in backend.generate(normal_timeline, config):
            assert r["resourceType"] == "Observation"

    def test_supported_loinc_completeness(self):
        assert len(ObservationBackend.SUPPORTED_LOINC) == 6
        assert "8867-4" in ObservationBackend.SUPPORTED_LOINC
        assert "8480-6" in ObservationBackend.SUPPORTED_LOINC
        assert "8462-4" in ObservationBackend.SUPPORTED_LOINC
        assert "2708-6" in ObservationBackend.SUPPORTED_LOINC
        assert "9279-1" in ObservationBackend.SUPPORTED_LOINC
        assert "8310-5" in ObservationBackend.SUPPORTED_LOINC

    def test_correct_loinc_keys(self, normal_timeline):
        backend = ObservationBackend()
        config = SynthConfig(duration_minutes=1)
        resources = backend.generate(normal_timeline, config)
        for r in resources:
            loinc = r["code"]["coding"][0]["code"]
            assert loinc in backend.SUPPORTED_LOINC

    def test_deterministic(self, normal_timeline):
        backend = ObservationBackend()
        config = SynthConfig(duration_minutes=10)
        r1 = backend.generate(normal_timeline, config)
        r2 = backend.generate(normal_timeline, config)
        assert r1 == r2

    def test_correct_resource_count(self):
        config = SynthConfig(duration_minutes=5)
        from fhir_synth.timeline import build_timeline
        tl = build_timeline("normal", config, seed=42)
        backend = ObservationBackend()
        resources = backend.generate(tl, config)
        expected_obs_per_tick = len(backend.SUPPORTED_LOINC)
        expected_total = (5 // 1 + 1) * expected_obs_per_tick
        assert len(resources) == expected_total


class TestPatientBackend:
    def test_protocol_compliance(self):
        _check_protocol(PatientBackend())

    def test_resource_type(self):
        assert PatientBackend().resource_type == "Patient"

    def test_generate_returns_list(self, normal_timeline):
        backend = PatientBackend()
        resources = backend.generate(normal_timeline, SynthConfig())
        assert isinstance(resources, list)
        assert len(resources) == 1

    def test_patient_structure(self, normal_timeline):
        backend = PatientBackend()
        pat = backend.generate(normal_timeline, SynthConfig())[0]
        assert pat["resourceType"] == "Patient"
        assert "id" in pat
        assert "identifier" in pat
        assert "gender" in pat
        assert "birthDate" in pat
        assert "deceasedBoolean" in pat

    def test_patient_id_matches(self, normal_timeline):
        backend = PatientBackend()
        pat = backend.generate(normal_timeline, SynthConfig())[0]
        assert pat["id"] == normal_timeline.patient_id

    def test_deterministic(self, normal_timeline):
        backend = PatientBackend()
        r1 = backend.generate(normal_timeline, SynthConfig())
        r2 = backend.generate(normal_timeline, SynthConfig())
        assert r1 == r2


class TestObservationEdgeCases:
    def test_event_with_missing_parameter_keys(self):
        from fhir_synth.timeline import build_timeline
        config = SynthConfig(duration_minutes=0)
        tl = build_timeline("normal", config, seed=42)
        tl.events[0].parameters.pop("spo2", None)
        backend = ObservationBackend()
        resources = backend.generate(tl, config)
        obs_loinc = {r["code"]["coding"][0]["code"] for r in resources}
        assert "2708-6" not in obs_loinc

    def test_dropout_can_produce_none(self):
        from fhir_synth.timeline import build_timeline
        config = SynthConfig(duration_minutes=0)
        tl = build_timeline("normal", config, seed=42)
        tl.events[0].parameters["heart_rate"]["dropout_rate"] = 1.0
        backend = ObservationBackend()
        resources = backend.generate(tl, config)
        hr_obs = [r for r in resources if r["code"]["coding"][0]["code"] == "8867-4"]
        assert len(hr_obs) == 0


class TestEncounterBackend:
    def test_protocol_compliance(self):
        _check_protocol(EncounterBackend())

    def test_resource_type(self):
        assert EncounterBackend().resource_type == "Encounter"

    def test_generate_returns_list(self, sepsis_timeline):
        backend = EncounterBackend()
        resources = backend.generate(sepsis_timeline, SynthConfig())
        assert isinstance(resources, list)
        assert len(resources) == 1

    def test_encounter_structure(self, sepsis_timeline):
        backend = EncounterBackend()
        enc = backend.generate(sepsis_timeline, SynthConfig())[0]
        assert enc["resourceType"] == "Encounter"
        assert "id" in enc
        assert "status" in enc
        assert "class" in enc
        assert "type" in enc
        assert "subject" in enc
        assert "period" in enc

    def test_encounter_with_diagnosis(self, sepsis_timeline):
        backend = EncounterBackend()
        enc = backend.generate(sepsis_timeline, SynthConfig())[0]
        assert len(enc["type"]) >= 1

    def test_deterministic(self, sepsis_timeline):
        backend = EncounterBackend()
        r1 = backend.generate(sepsis_timeline, SynthConfig())
        r2 = backend.generate(sepsis_timeline, SynthConfig())
        assert r1 == r2


class TestProtocol:
    def test_all_backends_conform(self):
        backends = [ObservationBackend(), PatientBackend(), EncounterBackend()]
        config = SynthConfig()
        from fhir_synth.timeline import build_timeline
        tl = build_timeline("normal", config, seed=42)
        for b in backends:
            resources = b.generate(tl, config)
            assert isinstance(resources, list)
            assert all(isinstance(r, dict) for r in resources)
            for r in resources:
                assert r["resourceType"] == b.resource_type
