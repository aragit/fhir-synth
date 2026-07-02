import pytest

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent
from fhir_synth.timeline import build_timeline, list_scenarios, query_timeline


class TestListScenarios:
    def test_list_contains_all(self):
        names = list_scenarios()
        assert "normal" in names
        assert "icu_sepsis" in names
        assert "post_op_recovery" in names
        assert "ards" in names
        assert "cardiac_arrest" in names

    def test_list_is_deterministic(self):
        assert list_scenarios() == list_scenarios()


class TestBuildTimeline:
    def test_build_normal(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config, seed=42)
        assert tl.patient_id == "normal-42"
        assert len(tl.events) == 11

    def test_build_icu_sepsis(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        assert "sepsis" in tl.patient_id
        events = tl.events
        drift = [e for e in events if e.event_type == "vital_drift"]
        diagnoses = [e for e in events if e.event_type == "diagnosis"]
        procedures = [e for e in events if e.event_type == "procedure"]
        assert len(drift) > 0
        assert len(diagnoses) == 2
        assert len(procedures) == 1

    def test_build_post_op(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("post_op_recovery", config, seed=42)
        assert "postop" in tl.patient_id
        procedures = [e for e in tl.events if e.event_type == "procedure"]
        assert len(procedures) == 1

    def test_build_ards(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("ards", config, seed=42)
        assert "ards" in tl.patient_id
        diagnoses = [e for e in tl.events if e.event_type == "diagnosis"]
        procedures = [e for e in tl.events if e.event_type == "procedure"]
        assert len(diagnoses) >= 1
        assert any(e.parameters.get("code") == "J80" for e in diagnoses)
        assert any(e.parameters.get("code") == "0BH17EZ" for e in procedures)

    def test_build_cardiac_arrest(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("cardiac_arrest", config, seed=42)
        assert "arrest" in tl.patient_id
        diagnoses = [e for e in tl.events if e.event_type == "diagnosis"]
        assert any(e.parameters.get("code") == "I46.9" for e in diagnoses)

    def test_build_unknown_scenario(self):
        config = SynthConfig(duration_minutes=10)
        with pytest.raises(ValueError, match="Unknown scenario"):
            build_timeline("nonexistent", config)

    def test_icu_sepsis_at_t180(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config, seed=42)
        events_at_180 = [e for e in tl.events if e.timestamp_minutes == 180]
        assert len(events_at_180) >= 1
        event = events_at_180[0]
        p = event.parameters
        assert p["heart_rate"]["baseline"] > 120
        assert p["spo2"]["baseline"] < 90
        assert p["respiratory_rate"]["baseline"] > 25

    def test_normal_vitals_in_bounds(self):
        config = SynthConfig(duration_minutes=60)
        tl = build_timeline("normal", config, seed=42)
        for e in tl.events:
            if e.event_type == "vital_drift":
                p = e.parameters
                assert 40 <= p["heart_rate"]["baseline"] <= 200
                assert 60 <= p["systolic_bp"]["baseline"] <= 250
                assert 30 <= p["diastolic_bp"]["baseline"] <= 150
                assert 70 <= p["spo2"]["baseline"] <= 100
                assert 4 <= p["respiratory_rate"]["baseline"] <= 60
                assert 30 <= p["temperature"]["baseline"] <= 43

    def test_cardiac_arrest_at_t122(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("cardiac_arrest", config, seed=42)
        events_at_122 = [e for e in tl.events if e.timestamp_minutes == 122]
        assert len(events_at_122) >= 1
        p = events_at_122[0].parameters
        hr = p["heart_rate"]["baseline"]
        assert hr == 0.0

    def test_deterministic_same_seed(self):
        config = SynthConfig(duration_minutes=60)
        tl1 = build_timeline("normal", config, seed=42)
        tl2 = build_timeline("normal", config, seed=42)
        assert len(tl1.events) == len(tl2.events)
        for e1, e2 in zip(tl1.events, tl2.events):
            assert e1.timestamp_minutes == e2.timestamp_minutes
            assert e1.parameters == e2.parameters

    def test_different_seed_different_patient_id(self):
        config = SynthConfig(duration_minutes=10)
        tl1 = build_timeline("normal", config, seed=1)
        tl2 = build_timeline("normal", config, seed=2)
        assert tl1.patient_id != tl2.patient_id


class TestQueryTimeline:
    def test_query_all(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config)
        result = query_timeline(tl)
        assert len(result) == len(tl.events)

    def test_query_by_type(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("icu_sepsis", config)
        result = query_timeline(tl, event_type="diagnosis")
        assert all(e.event_type == "diagnosis" for e in result)
        assert len(result) >= 1

    def test_query_by_time_range(self):
        config = SynthConfig(duration_minutes=60)
        tl = build_timeline("normal", config)
        result = query_timeline(tl, start=10, end=20)
        for e in result:
            assert 10 <= e.timestamp_minutes <= 20

    def test_query_combined(self):
        config = SynthConfig(duration_minutes=240)
        tl = build_timeline("icu_sepsis", config)
        result = query_timeline(tl, event_type="procedure", start=80, end=100)
        assert len(result) >= 1

    def test_query_empty_result(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config)
        result = query_timeline(tl, event_type="diagnosis")
        assert result == []

    def test_query_none_type(self):
        config = SynthConfig(duration_minutes=10)
        tl = build_timeline("normal", config)
        result = query_timeline(tl, event_type=None)
        assert len(result) == len(tl.events)
