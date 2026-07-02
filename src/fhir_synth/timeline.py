from datetime import datetime, timedelta, timezone

from fhir_synth.models import ClinicalTimeline, SynthConfig, TimelineEvent
from fhir_synth.scenarios import (
    ards,
    cardiac_arrest,
    generic,
    icu_sepsis,
    normal,
    post_op,
)


_SCENARIO_REGISTRY: dict[str, str] = {
    "normal": "fhir_synth.scenarios.normal",
    "icu_sepsis": "fhir_synth.scenarios.icu_sepsis",
    "post_op_recovery": "fhir_synth.scenarios.post_op",
    "ards": "fhir_synth.scenarios.ards",
    "cardiac_arrest": "fhir_synth.scenarios.cardiac_arrest",
}


def list_scenarios() -> list[str]:
    return list(_SCENARIO_REGISTRY.keys())


def build_timeline(
    scenario: str, config: SynthConfig, seed: int | None = None
) -> ClinicalTimeline:
    builders = {
        "normal": normal.build,
        "icu_sepsis": icu_sepsis.build,
        "post_op_recovery": post_op.build,
        "ards": ards.build,
        "cardiac_arrest": cardiac_arrest.build,
    }
    if scenario not in builders:
        msg = f"Unknown scenario: {scenario}. Available: {list(builders.keys())}"
        raise ValueError(msg)

    if seed is not None:
        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=seed)
    else:
        start_time = datetime.now(timezone.utc)
    return builders[scenario](config, seed=seed, start_time=start_time)


def query_timeline(
    timeline: ClinicalTimeline,
    event_type: str | None = None,
    start: int | None = None,
    end: int | None = None,
) -> list[TimelineEvent]:
    results = timeline.events
    if event_type is not None:
        results = [e for e in results if e.event_type == event_type]
    if start is not None:
        results = [e for e in results if e.timestamp_minutes >= start]
    if end is not None:
        results = [e for e in results if e.timestamp_minutes <= end]
    return results
