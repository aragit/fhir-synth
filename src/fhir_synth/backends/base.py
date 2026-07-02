from typing import Protocol, runtime_checkable

from fhir_synth.models import ClinicalTimeline, SynthConfig


@runtime_checkable
class ResourceBackend(Protocol):
    def generate(self, timeline: ClinicalTimeline, config: SynthConfig) -> list[dict]: ...

    @property
    def resource_type(self) -> str: ...
