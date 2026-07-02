import json

import pytest

from fhir_synth import (
    assemble_encounter,
    assemble_fhir_bundle,
    assemble_observations,
    assemble_patient,
    build_timeline,
    SynthConfig,
)
from fhir_synth.backends.observation import ObservationBackend


class TestAssemblePatient:
    def test_returns_dict(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        pat = assemble_patient(tl)
        assert isinstance(pat, dict)
        assert pat["resourceType"] == "Patient"
        assert "id" in pat
        assert "gender" in pat
        assert "birthDate" in pat

    def test_deterministic(self):
        config = SynthConfig(duration_minutes=10)
        tl1 = build_timeline("normal", config, seed=42)
        tl2 = build_timeline("normal", config, seed=42)
        assert assemble_patient(tl1) == assemble_patient(tl2)

    def test_patient_id_matches(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        pat = assemble_patient(tl)
        assert pat["id"] == tl.patient_id


class TestAssembleObservations:
    def test_returns_list(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        obs = assemble_observations(tl, config)
        assert isinstance(obs, list)
        assert len(obs) > 0

    def test_valid_loinc(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        obs = assemble_observations(tl, config)
        supported = {"8867-4", "8480-6", "8462-4", "2708-6", "9279-1", "8310-5"}
        for o in obs:
            code = o["code"]["coding"][0]["code"]
            assert code in supported

    def test_structure(self):
        config = SynthConfig(duration_minutes=1)
        tl = build_timeline("normal", config, seed=42)
        obs = assemble_observations(tl, config)
        for o in obs:
            assert o["resourceType"] == "Observation"
            assert o["status"] == "final"
            assert "category" in o
            assert "subject" in o
            assert o["subject"]["reference"].startswith("Patient/")
            assert "effectiveDateTime" in o
            assert "valueQuantity" in o
            assert "value" in o["valueQuantity"]
            assert "unit" in o["valueQuantity"]


class TestAssembleEncounter:
    def test_returns_dict(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("icu_sepsis", config, seed=42)
        enc = assemble_encounter(tl)
        assert enc is not None
        assert enc["resourceType"] == "Encounter"
        assert enc["status"] == "finished"
        assert "period" in enc

    def test_no_diagnosis(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        enc = assemble_encounter(tl)
        assert enc is not None


class TestAssembleFhirBundle:
    def test_bundle_structure(self):
        config = SynthConfig(
            duration_minutes=10,
            backends=["observation", "patient"],
        )
        tl = build_timeline("normal", config, seed=42)
        bundle = assemble_fhir_bundle(tl, config)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "collection"
        assert "entry" in bundle
        assert len(bundle["entry"]) > 0

    def test_bundle_contains_all_backends(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        bundle = assemble_fhir_bundle(tl, config)
        types = {e["resource"]["resourceType"] for e in bundle["entry"]}
        assert "Observation" in types
        assert "Patient" in types
        assert "Encounter" in types

    def test_deterministic_bundle(self):
        config = SynthConfig(duration_minutes=10)
        tl1 = build_timeline("normal", config, seed=42)
        tl2 = build_timeline("normal", config, seed=42)
        b1 = assemble_fhir_bundle(tl1, config)
        b2 = assemble_fhir_bundle(tl2, config)
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)

    def test_valid_observation_loinc_codes(self):
        config = SynthConfig(duration_minutes=1)
        tl = build_timeline("normal", config, seed=42)
        bundle = assemble_fhir_bundle(tl, config)
        for entry in bundle["entry"]:
            r = entry["resource"]
            if r["resourceType"] == "Observation":
                code = r["code"]["coding"][0]["code"]
                assert code in ObservationBackend.SUPPORTED_LOINC

    def test_patient_has_required_fields(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        bundle = assemble_fhir_bundle(tl, config)
        for entry in bundle["entry"]:
            r = entry["resource"]
            if r["resourceType"] == "Patient":
                assert "identifier" in r
                assert "gender" in r
                assert "birthDate" in r

    def test_encounter_has_required_fields(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("icu_sepsis", config, seed=42)
        bundle = assemble_fhir_bundle(tl, config)
        for entry in bundle["entry"]:
            r = entry["resource"]
            if r["resourceType"] == "Encounter":
                assert "status" in r
                assert "class" in r
                assert "subject" in r
                assert "period" in r

    def test_unknown_backend_raises(self):
        config = SynthConfig(duration_minutes=10, backends=["nonexistent"])
        tl = build_timeline("normal", config)
        with pytest.raises(ValueError, match="Unknown backend"):
            assemble_fhir_bundle(tl, config)
