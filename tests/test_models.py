import pytest
from pydantic import ValidationError

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent, TrendConfig


class TestTrendConfig:
    def test_basic(self):
        c = TrendConfig(trend_type="linear", baseline=100, slope=2)
        assert c.trend_type == "linear"
        assert c.baseline == 100
        assert c.slope == 2

    def test_invalid_trend_type(self):
        with pytest.raises(ValidationError):
            TrendConfig(trend_type="invalid", baseline=0)

    def test_defaults(self):
        c = TrendConfig(trend_type="linear", baseline=0)
        assert c.slope is None
        assert c.noise_std == 0.0
        assert c.dropout_rate == 0.0
        assert c.min_value is None
        assert c.max_value is None

    def test_all_fields(self):
        c = TrendConfig(
            trend_type="sinusoidal",
            slope=1.0,
            half_life=30.0,
            amplitude=10.0,
            period_minutes=60.0,
            baseline=50.0,
            noise_std=2.0,
            dropout_rate=0.1,
            min_value=0.0,
            max_value=100.0,
        )
        assert c.amplitude == 10.0
        assert c.period_minutes == 60.0


class TestTimelineEvent:
    def test_basic(self):
        e = TimelineEvent(event_type="vital_drift", timestamp_minutes=30)
        assert e.event_type == "vital_drift"
        assert e.timestamp_minutes == 30
        assert e.parameters == {}

    def test_with_parameters(self):
        e = TimelineEvent(
            event_type="diagnosis",
            timestamp_minutes=45,
            parameters={"code": "A41.9"},
        )
        assert e.parameters["code"] == "A41.9"

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            TimelineEvent(event_type=123, timestamp_minutes="bad")


class TestClinicalTimeline:
    def test_basic(self):
        from datetime import datetime, timezone
        tl = ClinicalTimeline(
            patient_id="test-1",
            start_time=datetime.now(timezone.utc),
            events=[],
        )
        assert tl.patient_id == "test-1"
        assert tl.seed is None

    def test_with_seed(self):
        from datetime import datetime, timezone
        tl = ClinicalTimeline(
            patient_id="test-2",
            start_time=datetime.now(timezone.utc),
            events=[],
            seed=42,
        )
        assert tl.seed == 42

    def test_events_validation(self):
        from datetime import datetime, timezone
        with pytest.raises(ValidationError):
            ClinicalTimeline(
                patient_id="test",
                start_time=datetime.now(timezone.utc),
                events="not_a_list",
            )


class TestSynthConfig:
    def test_defaults(self):
        c = SynthConfig()
        assert c.duration_minutes == 240
        assert c.sample_interval_minutes == 1
        assert c.backends == ["observation", "patient", "encounter"]

    def test_custom(self):
        c = SynthConfig(
            duration_minutes=120,
            sample_interval_minutes=5,
            backends=["observation"],
        )
        assert c.duration_minutes == 120
        assert c.sample_interval_minutes == 5
        assert c.backends == ["observation"]

    def test_invalid_duration(self):
        with pytest.raises(ValidationError):
            SynthConfig(duration_minutes="bad")

    def test_serialization_roundtrip(self):
        c = SynthConfig(duration_minutes=60, backends=["patient"])
        data = c.model_dump()
        assert data["duration_minutes"] == 60
        c2 = SynthConfig.model_validate(data)
        assert c2.duration_minutes == c.duration_minutes
        assert c2.backends == c.backends
