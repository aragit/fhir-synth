import json

import pytest

from fhir_synth import (
    assemble_fhir_bundle,
    build_timeline,
    SynthConfig,
)
from fhir_synth.backends.observation import ObservationBackend


@pytest.fixture
def obs_backend():
    return ObservationBackend()


class TestNormalScenario:
    def test_generates_without_error(self):
        config = SynthConfig(duration_minutes=60)
        tl = build_timeline("normal", config, seed=42)
        assert len(tl.events) > 0

    def test_all_vitals_in_safe_ranges(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("normal", config, seed=42)
        for e in tl.events:
            if e.event_type == "vital_drift":
                p = e.parameters
                for loinc, (key, _, bounds) in ObservationBackend.SUPPORTED_LOINC.items():
                    if key in p:
                        val = p[key]["baseline"]
                        assert bounds[0] <= val <= bounds[1], (
                            f"{key} = {val} out of bounds {bounds}"
                        )

    def test_bundle_validates(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        bundle = assemble_fhir_bundle(tl, config)
        assert bundle["resourceType"] == "Bundle"

    def test_determinism(self):
        config = SynthConfig(duration_minutes=60)
        tl1 = build_timeline("normal", config, seed=42)
        tl2 = build_timeline("normal", config, seed=42)
        b1 = assemble_fhir_bundle(tl1, config)
        b2 = assemble_fhir_bundle(tl2, config)
        assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)


class TestIcuSepsisScenario:
    def test_generates_without_error(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        assert len(tl.events) > 0

    def test_hr_elevated_at_t180(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        events = [e for e in tl.events if e.timestamp_minutes == 180 and e.event_type == "vital_drift"]
        assert len(events) >= 1
        hr = events[0].parameters["heart_rate"]["baseline"]
        assert hr > 120, f"HR should be > 120 at t=180, got {hr}"

    def test_spo2_low_at_t180(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        events = [e for e in tl.events if e.timestamp_minutes == 180 and e.event_type == "vital_drift"]
        assert len(events) >= 1
        spo2 = events[0].parameters["spo2"]["baseline"]
        assert spo2 < 90, f"SpO2 should be < 90 at t=180, got {spo2}"

    def test_rr_elevated_at_t180(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        events = [e for e in tl.events if e.timestamp_minutes == 180 and e.event_type == "vital_drift"]
        assert len(events) >= 1
        rr = events[0].parameters["respiratory_rate"]["baseline"]
        assert rr > 25, f"RR should be > 25 at t=180, got {rr}"

    def test_has_diagnosis_and_procedure(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        diagnoses = [e for e in tl.events if e.event_type == "diagnosis"]
        procedures = [e for e in tl.events if e.event_type == "procedure"]
        assert len(diagnoses) >= 1
        assert len(procedures) >= 1


class TestPostOpRecoveryScenario:
    def test_generates_without_error(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("post_op_recovery", config, seed=42)
        assert len(tl.events) > 0

    def test_hr_near_baseline_at_t240(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("post_op_recovery", config, seed=42)
        events = [e for e in tl.events if e.timestamp_minutes == 240 and e.event_type == "vital_drift"]
        assert len(events) >= 1
        hr = events[0].parameters["heart_rate"]["baseline"]
        assert abs(hr - 80) <= 8, f"HR should be within 10% of baseline (80) at t=240, got {hr}"

    def test_has_procedure(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("post_op_recovery", config, seed=42)
        procedures = [e for e in tl.events if e.event_type == "procedure"]
        assert len(procedures) == 1
        assert procedures[0].parameters["code"] == "0FT44ZZ"


class TestArdsScenario:
    def test_generates_without_error(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("ards", config, seed=42)
        assert len(tl.events) > 0

    def test_spo2_drops_after_t30(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("ards", config, seed=42)
        events_before = [e for e in tl.events if e.timestamp_minutes <= 30 and e.event_type == "vital_drift"]
        events_after = [e for e in tl.events if e.timestamp_minutes >= 60 and e.event_type == "vital_drift"]
        if events_before and events_after:
            spo2_before = events_before[-1].parameters["spo2"]["baseline"]
            spo2_after = events_after[0].parameters["spo2"]["baseline"]
            assert spo2_after < spo2_before

    def test_has_diagnosis_and_procedure(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("ards", config, seed=42)
        diagnoses = [e for e in tl.events if e.event_type == "diagnosis"]
        procedures = [e for e in tl.events if e.event_type == "procedure"]
        assert len(diagnoses) >= 1
        assert len(procedures) >= 1


class TestCardiacArrestScenario:
    def test_generates_without_error(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("cardiac_arrest", config, seed=42)
        assert len(tl.events) > 0

    def test_hr_zero_at_t122(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("cardiac_arrest", config, seed=42)
        events = [e for e in tl.events if e.timestamp_minutes == 122 and e.event_type == "vital_drift"]
        assert len(events) >= 1
        hr = events[0].parameters["heart_rate"]["baseline"]
        assert hr == 0, f"HR should be 0 at t=122 (flatline), got {hr}"

    def test_hr_spike_at_t120(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("cardiac_arrest", config, seed=42)
        events = [e for e in tl.events if e.timestamp_minutes == 120 and e.event_type == "vital_drift"]
        assert len(events) >= 1
        hr = events[0].parameters["heart_rate"]["baseline"]
        assert hr > 150, f"HR should be > 150 (VTach) at t=120, got {hr}"

    def test_has_diagnosis_and_procedure(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("cardiac_arrest", config, seed=42)
        diagnoses = [e for e in tl.events if e.event_type == "diagnosis"]
        procedures = [e for e in tl.events if e.event_type == "procedure"]
        assert len(diagnoses) >= 1
        assert len(procedures) >= 1


class TestAllScenarios:
    def test_all_scenarios_generate_without_error(self):
        config = SynthConfig(duration_minutes=60)
        for scenario in ["normal", "icu_sepsis", "post_op_recovery", "ards", "cardiac_arrest"]:
            tl = build_timeline(scenario, config, seed=42)
            assert len(tl.events) > 0, f"{scenario} generated no events"

    def test_all_scenarios_produce_valid_bundles(self):
        config = SynthConfig(duration_minutes=10)
        for scenario in ["normal", "icu_sepsis", "post_op_recovery", "ards", "cardiac_arrest"]:
            tl = build_timeline(scenario, config, seed=42)
            bundle = assemble_fhir_bundle(tl, config)
            assert bundle["resourceType"] == "Bundle"
            assert len(bundle["entry"]) > 0

    def test_determinism_across_scenarios(self):
        config = SynthConfig(duration_minutes=10)
        for scenario in ["normal", "icu_sepsis", "post_op_recovery", "ards", "cardiac_arrest"]:
            tl1 = build_timeline(scenario, config, seed=42)
            tl2 = build_timeline(scenario, config, seed=42)
            b1 = assemble_fhir_bundle(tl1, config)
            b2 = assemble_fhir_bundle(tl2, config)
            assert json.dumps(b1, sort_keys=True) == json.dumps(b2, sort_keys=True)


class TestGenericScenario:
    def test_build_generic(self):
        from fhir_synth.scenarios.generic import build
        config = SynthConfig(duration_minutes=10)
        tl = build(config, seed=42)
        assert tl.patient_id == "generic-42"
        assert len(tl.events) > 0

    def test_generic_default_start_time(self):
        from fhir_synth.scenarios.generic import build
        tl = build(SynthConfig(duration_minutes=5))
        assert tl.patient_id == "generic-0"

    def test_generic_vital_drift_events(self):
        from fhir_synth.scenarios.generic import build
        tl = build(SynthConfig(duration_minutes=5))
        vital_events = [e for e in tl.events if e.event_type == "vital_drift"]
        assert len(vital_events) == 6


class TestScenarioDirectBuild:
    def test_normal_without_start_time(self):
        from fhir_synth.scenarios.normal import build
        tl = build(SynthConfig(duration_minutes=5))
        assert tl.patient_id == "normal-0"

    def test_icu_sepsis_without_start_time(self):
        from fhir_synth.scenarios.icu_sepsis import build
        tl = build(SynthConfig(duration_minutes=10))
        assert "sepsis" in tl.patient_id

    def test_post_op_without_start_time(self):
        from fhir_synth.scenarios.post_op import build
        tl = build(SynthConfig(duration_minutes=10))
        assert "postop" in tl.patient_id

    def test_ards_without_start_time(self):
        from fhir_synth.scenarios.ards import build
        tl = build(SynthConfig(duration_minutes=10))
        assert "ards" in tl.patient_id

    def test_cardiac_arrest_without_start_time(self):
        from fhir_synth.scenarios.cardiac_arrest import build
        tl = build(SynthConfig(duration_minutes=10))
        assert "arrest" in tl.patient_id
