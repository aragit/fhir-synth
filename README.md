# fhir-synth — Deterministic FHIR R4 Synthetic Data Generator

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

⚠️ **Clinical Safety Disclaimer:** This software generates **synthetic data only**. It is not derived from real patients, electronic health records, or clinical datasets. It is **not for clinical use**, clinical decision support, research validation, or regulatory submission without independent verification. No real patient information is contained in any generated output.

---

## Table of Contents

- [What This Is](#what-this-is)
- [What This Is Not](#what-this-is-not)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Python API Reference](#python-api-reference)
- [Scenarios](#scenarios)
  - [normal](#normal)
  - [icu_sepsis](#icu_sepsis)
  - [post_op_recovery](#post_op_recovery)
  - [ards](#ards)
  - [cardiac_arrest](#cardiac_arrest)
- [Trend Functions](#trend-functions)
- [Backends](#backends)
  - [Built-in Backends](#built-in-backends)
  - [ResourceBackend Protocol](#resourcebackend-protocol)
  - [Custom Backend Example](#custom-backend-example)
- [Configuration](#configuration)
- [Integration Examples](#integration-examples)
- [Testing](#testing)
- [Development](#development)
- [License](#license)

---

## What This Is

`fhir-synth` is a **deterministic, pluggable, scenario-driven FHIR R4 synthetic data generator** for clinical simulation, testing, and research. It produces reproducible FHIR R4 resources (Patient, Observation, Encounter) from parameterized clinical scenarios.

**Key design decisions:**

- **Deterministic core** — seeded `random.Random` objects, trend arithmetic (linear, exponential, step, sinusoidal), and Gaussian noise. Same seed → byte-identical FHIR Bundle output. Crucial for regression testing and reproducible research.
- **Pluggable resource backends** — the `ResourceBackend` protocol lets anyone add support for AllergyIntolerance, ImagingStudy, Claim, or any FHIR resource without modifying core code.
- **Scenario-driven** — clinical timelines describe *what happens* (sepsis onset, surgery, cardiac arrest). Backends define *how it maps* to FHIR. Clean separation of concerns.
- **FHIR R4 valid output** — every generated resource validates against the official HL7 FHIR R4 JSON Schema at generation time. Invalid resources raise immediately.
- **No real FHIR server** — outputs Python dictionaries or JSON strings. No HTTP, no authentication, no persistence layer.
- **No GPU dependency** — runs on any CPU. Pure Python + NumPy-free.
- **No neural networks** — all generation uses explicit clinical trend models. You control the trajectory.

---

## What This Is Not

- ❌ Not a real EHR or patient data source
- ❌ Not a substitute for de-identified clinical datasets
- ❌ Not a FHIR server (no HTTP, no persistence)
- ❌ Not GPU-dependent
- ❌ Not a neural/ML-based generator
- ❌ Not a clinical decision support tool
- ❌ Not HIPAA-compliant (it's synthetic — no PHI is possible)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         fhir-synth                                   │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │Scenario  │───▶│Timeline  │───▶│Trend     │───▶│Backend   │      │
│  │(sepsis,  │    │Engine    │    │Functions │    │(Patient, │      │
│  │ ARDS,    │    │          │    │          │    │ Obs,     │      │
│  │ arrest)  │    │          │    │          │    │ Enc)     │      │
│  └──────────┘    └──────────┘    └──────────┘    └─────┬────┘      │
│                                                         │          │
│                                                         ▼          │
│                                              ┌──────────────────┐  │
│                                              │FHIR Assembler    │  │
│                                              │(Bundle builder)  │  │
│                                              └────────┬─────────┘  │
│                                                       │            │
│                                                       ▼            │
│                                              ┌──────────────────┐  │
│                                              │Validator         │  │
│                                              │(jsonschema FHIR) │  │
│                                              └────────┬─────────┘  │
│                                                       │            │
│                                                       ▼            │
│                                              ┌──────────────────┐  │
│                                              │Output (dict/JSON)│  │
│                                              └──────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Data flow:**

1. **Scenario** — A named clinical trajectory (e.g., `icu_sepsis`) defines a sequence of `TimelineEvent` objects describing vitals drift, diagnoses, and procedures at specific time offsets.
2. **Timeline Engine** — Builds and validates the `ClinicalTimeline`, which is a time-ordered list of events anchored to an ISO 8601 start time.
3. **Trend Functions** — For each vital sign at each time point, a configurable trend (linear, exponential, step, sinusoidal) is evaluated with additive Gaussian noise, dropout, and clamping.
4. **Backend** — Each `ResourceBackend` consumes the timeline and produces FHIR resources (dicts). The `ObservationBackend` maps each `vital_drift` event to a LOINC-coded Observation.
5. **FHIR Assembler** — Collects resources from all active backends and wraps them in a FHIR R4 `Bundle` of type `collection`.
6. **Validator** — Every resource is validated against the official HL7 FHIR R4 JSON Schema before inclusion in the bundle. Invalid resources raise `ValidationError` at generation time.
7. **Output** — The bundle is returned as a Python `dict` or serialised to JSON via the CLI.

---

## Quick Start

### Installation

```bash
# From PyPI (once published)
pip install fhir-synth

# From source
git clone https://github.com/aragit/fhir-synth.git
cd fhir-synth
pip install -e .
```

### CLI — 10 seconds to synthetic data

```bash
# Generate a 4-hour ICU sepsis trajectory
python -m fhir_synth --scenario icu_sepsis --duration 240 --seed 42 --output pretty
```

```bash
# List all available scenarios
python -m fhir_synth --list-scenarios
# Output:
# normal
# icu_sepsis
# post_op_recovery
# ards
# cardiac_arrest
```

```bash
# Generate only Patient and Observation resources for 1 hour
python -m fhir_synth --scenario normal --duration 60 --seed 7 --backends patient,observation --output json > patient_1h.json
```

```bash
# Invalid scenario name → non-zero exit with clear error
python -m fhir_synth --scenario nonexistent
# Error: Unknown scenario: nonexistent. Available: ['normal', 'icu_sepsis', ...]
```

### Python API — 5 lines to a FHIR Bundle

```python
from fhir_synth import build_timeline, assemble_fhir_bundle, SynthConfig

# Configure a 4-hour simulation with all three backends
config = SynthConfig(
    duration_minutes=240,
    sample_interval_minutes=1,
    backends=["observation", "patient", "encounter"],
)

# Build the clinical timeline from a named scenario
timeline = build_timeline("icu_sepsis", config, seed=42)

# Assemble into a validated FHIR R4 Bundle
bundle = assemble_fhir_bundle(timeline, config)

# Inspect the generated observations
for entry in bundle["entry"]:
    r = entry["resource"]
    if r["resourceType"] == "Observation":
        loinc = r["code"]["coding"][0]["code"]
        value = r["valueQuantity"]["value"]
        print(f"{loinc}: {value}")

# Serialise to JSON
import json
with open("sepsis_bundle.json", "w") as f:
    json.dump(bundle, f, indent=2)
```

---

## CLI Reference

```
usage: python -m fhir_synth [--scenario SCENARIO] [--duration MINUTES]
                            [--seed SEED] [--backends LIST]
                            [--output FORMAT] [--list-scenarios]

Arguments:
  --scenario SCENARIO    Clinical scenario to simulate
                         (default: normal)
  --duration MINUTES     Duration in minutes (default: 240)
  --seed SEED            Random seed for reproducibility
                         (default: None → current time)
  --backends LIST        Comma-separated list of backends
                         (default: observation,patient,encounter)
  --output FORMAT        Output format: json | pretty (default: json)
  --list-scenarios       List available scenario names and exit

Exit codes:
  0  Success
  1  Error (unknown scenario, generation failure, etc.)
```

---

## Python API Reference

### `fhir_synth.build_timeline(scenario, config, seed=None)`

Build a `ClinicalTimeline` from a named scenario.

| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario` | `str` | One of `normal`, `icu_sepsis`, `post_op_recovery`, `ards`, `cardiac_arrest` |
| `config` | `SynthConfig` | Simulation configuration |
| `seed` | `int \| None` | PRNG seed. Same seed → identical output |

**Returns:** `ClinicalTimeline`

**Raises:** `ValueError` if scenario name is unknown.

### `fhir_synth.query_timeline(timeline, event_type=None, start=None, end=None)`

Filter events by type and time range.

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeline` | `ClinicalTimeline` | Timeline to query |
| `event_type` | `str \| None` | Filter by `vital_drift`, `diagnosis`, `procedure`, `medication` |
| `start` | `int \| None` | Minimum `timestamp_minutes` (inclusive) |
| `end` | `int \| None` | Maximum `timestamp_minutes` (inclusive) |

**Returns:** `list[TimelineEvent]`

### `fhir_synth.assemble_fhir_bundle(timeline, config)`

Convert a timeline to a validated FHIR R4 Bundle.

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeline` | `ClinicalTimeline` | Built timeline |
| `config` | `SynthConfig` | Must include active backend names |

**Returns:** `dict` — FHIR Bundle with resourceType `Bundle`, type `collection`

**Raises:** `ValueError` if an unknown backend is requested. `ValidationError` if any resource fails FHIR R4 schema validation.

### `fhir_synth.assemble_patient(timeline)`

Build a single FHIR Patient resource dict from a timeline.

### `fhir_synth.assemble_observations(timeline, config)`

Build a list of FHIR Observation resource dicts from `vital_drift` events.

### `fhir_synth.assemble_encounter(timeline)`

Build a single FHIR Encounter resource dict (or `None` if no events).

### `fhir_synth.list_scenarios()`

Return `list[str]` of available scenario names.

### `fhir_synth.TrendConfig`

Pydantic model for trend function configuration.

```python
class TrendConfig(BaseModel):
    trend_type: Literal["linear", "exponential", "step", "sinusoidal"]
    slope: float | None          # For linear
    half_life: float | None      # For exponential
    amplitude: float | None      # For sinusoidal; "after" value for step
    period_minutes: float | None # For sinusoidal
    baseline: float              # Starting value / asymptote
    noise_std: float = 0.0      # Gaussian noise std. dev.
    dropout_rate: float = 0.0   # Fraction of points to set None
    min_value: float | None      # Clamp minimum
    max_value: float | None      # Clamp maximum
```

### `fhir_synth.ClinicalTimeline`

```python
class ClinicalTimeline(BaseModel):
    patient_id: str
    start_time: datetime         # ISO 8601 anchor
    events: list[TimelineEvent]  # Time-ordered event list
    seed: int | None             # PRNG seed used to build this timeline
```

### `fhir_synth.TimelineEvent`

```python
class TimelineEvent(BaseModel):
    event_type: str     # "vital_drift", "diagnosis", "procedure", "medication"
    timestamp_minutes: int  # Minutes from timeline start
    parameters: dict    # Event-specific parameters (vital baselines, ICD codes, etc.)
```

### `fhir_synth.SynthConfig`

```python
class SynthConfig(BaseModel):
    duration_minutes: int = 240
    sample_interval_minutes: int = 1
    backends: list[str] = ["observation", "patient", "encounter"]
```

---

## Scenarios

Each scenario defines a phased clinical trajectory with specific vital sign behaviours, diagnoses, and procedures at precise time offsets. All scenarios run for `duration_minutes` (default 240) with 1-minute resolution.

### `normal`

**Purpose:** Healthy baseline with Gaussian noise. Used as control/negative case.

| Phase | Time (min) | HR | SBP | DBP | SpO2 | RR | Temp |
|-------|-----------|----|-----|-----|------|----|------|
| Entire | 0–N | 72 | 120 | 80 | 98 | 16 | 36.5 |

- **Trend:** None (flat)
- **Noise:** σ = 5% of each baseline value
- **Events:** None
- **Dropout:** None

### `icu_sepsis`

**Purpose:** Sepsis-3 trajectory from subtle onset through rapid deterioration to decompensation. Models a typical ICU sepsis case.

| Phase | Time (min) | HR | SBP | DBP | SpO2 | RR | Temp |
|-------|-----------|----|-----|-----|------|----|------|
| Subtle onset | 0–60 | 72 → +0.5/min | 120 | 80 | 98 → −0.05/min | 16 → +0.2/min | 36.5 → +0.01/min |
| Acceleration | 60–120 | 102 → +1.0/min | 120 → −0.3/min | 80 → −0.2/min | 95 → −0.1/min | 28 → +0.4/min | 37.1 → +0.02/min |
| Decompensation | 120–240 | 140+ (capped 160) | → −1.0/min (min 70) | → −0.5/min (min 40) | 88–82% | 28+ (capped 40) | 39.5 |

**Events:**
- t=30: Diagnosis — `A41.9` Sepsis, unspecified organism
- t=60: Diagnosis — `R65.20` Severe sepsis without septic shock
- t=90: Procedure — `03EO3ZZ` Central line placement

**Property tests assert at t=180:**
- HR > 120 bpm
- SpO2 < 90%
- RR > 25 rpm

### `post_op_recovery`

**Purpose:** Post-operative recovery after laparoscopic cholecystectomy. Models surgical stress response with exponential decay toward baseline.

| Phase | Time (min) | HR | SBP | DBP | SpO2 | RR | Temp |
|-------|-----------|----|-----|-----|------|----|------|
| Stress | 0–30 | 110 → −0.3/min | 140 → −0.5/min | 90 → −0.3/min | 97 | 22 → −0.1/min | 37.2 |
| Exponential decay | 30–120 | 80 + 27·e^(−t/45) | 120 + 15·e^(−t/45) | 80 + 7·e^(−t/45) | 97 | 16 + 5·e^(−t/45) | 36.5 + 0.5·e^(−t/45) |
| Stable baseline | 120–240 | 80 | 120 | 80 | 97 | 16 | 36.5 |

**Events:**
- t=0: Procedure — `0FT44ZZ` Laparoscopic cholecystectomy

**Property tests assert at t=240:**
- HR within 10% of baseline (80 bpm)

### `ards`

**Purpose:** Acute Respiratory Distress Syndrome with refractory hypoxemia. Models rapid desaturation followed by prolonged refractory phase.

| Phase | Time (min) | HR | SBP | DBP | SpO2 | RR | Temp |
|-------|-----------|----|-----|-----|------|----|------|
| Normal | 0–30 | 72 | 120 | 80 | 98 | 16 | 36.5 |
| Rapid drop | 30–60 | +1.5/min | 125 | 80 | 98 → 82% over 30 min | 16 → 35 over 30 min | 37.0 |
| Refractory | 60–240 | 120–140 | 100 (maintained) | 60 | 82–88% (oscillating) | 30–36 | 37.5 |

**Events:**
- t=45: Diagnosis — `J80` Acute respiratory distress syndrome
- t=60: Procedure — `0BH17EZ` Intubation

### `cardiac_arrest`

**Purpose:** Sudden cardiac arrest with VTach → flatline → CPR artifacts. Models a catastrophic decompensation.

| Phase | Time (min) | HR | SBP | DBP | SpO2 | RR | Temp |
|-------|-----------|----|-----|-----|------|----|------|
| Normal | 0–120 | 72 | 120 | 80 | 98 | 16 | 36.5 |
| VTach spike | 120–122 | 180 | 60 | 30 | 85 | 8 | 36.5 |
| Flatline | 122–123 | 0 | 0 | 0 | 70 → dropping | 0 | 36.5 |
| CPR artifacts | 123–240 | 60–120 (noisy) | 60–100 (noisy) | compress | 70–90 (noisy) | 5–15 | 36.5 |

**Events:**
- t=122: Diagnosis — `I46.9` Cardiac arrest, cause unspecified
- t=123: Procedure — `5A12012` CPR initiated

**Property tests assert:**
- At t=120: HR > 150 (VTach spike)
- At t=122: HR == 0 (flatline)

---

## Trend Functions

All trend functions are in `fhir_synth.trends.py`. The `apply_trend` pipeline applies: **trend → noise → dropout → clamp**.

### `linear_trend(t, slope, baseline)`

```
value = baseline + slope * t
```

### `exponential_trend(t, half_life, baseline, asymptote)`

```
λ = ln(2) / half_life
value = asymptote + (baseline - asymptote) * e^(-λ * t)
```

### `step_trend(t, step_at, before, after)`

```
value = after  if t >= step_at
        before if t < step_at
```

### `sinusoidal_trend(t, amplitude, period, baseline)`

```
ω = 2π / period
value = baseline + amplitude * sin(ω * t)
```

### `add_noise(values, std, rng)`

Adds zero-mean Gaussian noise with standard deviation `std` using the seeded `random.Random` instance.

### `apply_dropout(values, rate, rng)`

Randomly sets each value to `None` with probability `rate`.

### `clamp_values(values, min_v, max_v)`

Clamps each non-None value to `[min_v, max_v]`.

### Pipeline

```python
def apply_trend(trend: TrendConfig, time_points: list[int], rng: random.Random) -> list[float | None]:
    # 1. Evaluate trend function
    # 2. Add Gaussian noise
    # 3. Apply dropout
    # 4. Clamp to bounds
```

---

## Backends

### Built-in Backends

#### `ObservationBackend`

Maps `vital_drift` events to FHIR R4 `Observation` resources.

| LOINC Code | Display | Unit | Clinical Range |
|-----------|---------|------|----------------|
| `8867-4` | Heart Rate | bpm | 40–200 |
| `8480-6` | Systolic Blood Pressure | mmHg | 60–250 |
| `8462-4` | Diastolic Blood Pressure | mmHg | 30–150 |
| `2708-6` | Oxygen Saturation | % | 70–100 |
| `9279-1` | Respiratory Rate | rpm | 4–60 |
| `8310-5` | Body Temperature | Cel | 30.0–43.0 |

Each Observation includes:
- `category`: `vital-signs` (HL7 observation category)
- `code`: LOINC coding with display name
- `subject`: Reference to `Patient/<id>`
- `effectiveDateTime`: ISO 8601 timestamp
- `valueQuantity`: Numeric value with UCUM unit coding
- `id`: Deterministic UUID (MD5 of seed + timestamp + LOINC)

#### `PatientBackend`

Generates a single FHIR R4 `Patient` resource with:
- `identifier`: Deterministic identifier
- `gender`: Randomly chosen from `male`/`female`
- `birthDate`: Age 18–90 determined by seed
- `deceasedBoolean`: `false`

#### `EncounterBackend`

Generates a single FHIR R4 `Encounter` resource with:
- `status`: `finished`
- `class`: `IMP` (inpatient encounter)
- `type`: ICD-10-CM codes from `diagnosis` events
- `period.start`/`period.end`: Timeline start to start + duration

### ResourceBackend Protocol

```python
from typing import Protocol
from fhir_synth.models import ClinicalTimeline, SynthConfig

class ResourceBackend(Protocol):
    def generate(self, timeline: ClinicalTimeline, config: SynthConfig) -> list[dict]: ...
    
    @property
    def resource_type(self) -> str: ...
```

Any object that conforms to this protocol is a valid backend. No inheritance required — Python structural subtyping.

### Custom Backend Example

This example adds an `AllergyIntolerance` backend that generates allergy records from timeline events:

```python
import hashlib
from fhir_synth.models import ClinicalTimeline, SynthConfig

class AllergyIntoleranceBackend:
    @property
    def resource_type(self) -> str:
        return "AllergyIntolerance"

    def _make_uuid(self, seed: str, idx: int) -> str:
        raw = f"allergy-{seed}-{idx}"
        h = hashlib.md5(raw.encode()).hexdigest()
        return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"

    def generate(self, timeline: ClinicalTimeline, config: SynthConfig) -> list[dict]:
        resources = []
        allergy_events = [e for e in timeline.events if e.event_type == "allergy"]
        for i, event in enumerate(allergy_events):
            resources.append({
                "resourceType": "AllergyIntolerance",
                "id": self._make_uuid(str(timeline.seed or 0), i),
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active",
                    }]
                },
                "code": {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": event.parameters.get("rxnorm", "7980"),
                        "display": event.parameters.get("display", "Penicillin"),
                    }]
                },
                "patient": {"reference": f"Patient/{timeline.patient_id}"},
            })
        return resources

# Register in fhir_assembler._BACKEND_MAP or pass directly:
backend = AllergyIntoleranceBackend()
resources = backend.generate(timeline, config)
```

To make the custom backend available via the CLI, register it in `fhir_assembler.py`:

```python
_BACKEND_MAP = {
    "observation": ObservationBackend,
    "patient": PatientBackend,
    "encounter": EncounterBackend,
    "allergy": AllergyIntoleranceBackend,  # <-- add this
}
```

---

## Configuration

### `SynthConfig` Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `duration_minutes` | `int` | `240` | Total simulation duration in minutes |
| `sample_interval_minutes` | `int` | `1` | Time between consecutive vital sign samples |
| `backends` | `list[str]` | `["observation", "patient", "encounter"]` | Backend names to activate during assembly |

### Environment Variables

| Variable | Effect |
|----------|--------|
| `PYTHONHASHSEED=0` | Disables hash randomisation for fully deterministic dict ordering across runs |
| `PYTHONDONTWRITEBYTECODE=1` | Prevents `.pyc` file creation during development |

---

## Integration Examples

### With `icu-vitals-transformer`

```python
from fhir_synth import build_timeline, assemble_fhir_bundle, SynthConfig

# 1. Generate a synthetic ICU patient with sepsis
config = SynthConfig(
    duration_minutes=480,  # 8-hour ICU stay
    backends=["observation", "patient", "encounter"],
)
timeline = build_timeline("icu_sepsis", config, seed=42)
bundle = assemble_fhir_bundle(timeline, config)

# 2. Extract observations for the transformer pipeline
observations = [
    entry["resource"]
    for entry in bundle["entry"]
    if entry["resource"]["resourceType"] == "Observation"
]

# 3. Pass to icu-vitals-transformer
# from icu_vitals_transformer.ingestion.fhir_parser import parse_batch
# parsed = parse_batch(observations)
```

### Batch Generation for ML Training

```python
from fhir_synth import build_timeline, assemble_fhir_bundle, SynthConfig
import json

scenarios = ["normal", "icu_sepsis", "ards", "cardiac_arrest"]
for scenario in scenarios:
    for seed in range(100):
        config = SynthConfig(duration_minutes=240)
        timeline = build_timeline(scenario, config, seed=seed)
        bundle = assemble_fhir_bundle(timeline, config)
        with open(f"data/{scenario}_seed{seed}.json", "w") as f:
            json.dump(bundle, f)
```

### Custom Scenario with Generic Builder

```python
from fhir_synth import build_timeline, assemble_fhir_bundle, SynthConfig
from fhir_synth.models import TimelineEvent

# Build generic timeline and inject custom events
config = SynthConfig(duration_minutes=120, backends=["observation"])
tl = build_timeline("normal", config, seed=42)
tl.events.append(TimelineEvent(
    event_type="diagnosis",
    timestamp_minutes=60,
    parameters={"code": "E11.9", "display": "Type 2 diabetes"},
))
bundle = assemble_fhir_bundle(tl, config)
```

---

## Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest -v

# Run with coverage report
pytest -v --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_scenarios.py -v

# Run a specific test
pytest tests/test_timeline.py::TestBuildTimeline::test_icu_sepsis_at_t180 -v
```

### Test Coverage

| Module | Coverage | Key Tests |
|--------|----------|-----------|
| `models.py` | 100% | Validation, serialisation, edge cases |
| `timeline.py` | 100% | All 5 scenarios, query filters, determinism |
| `trends.py` | 100% | All 4 trend functions, noise stats, dropout accuracy, clamping |
| `fhir_assembler.py` | 100% | FHIR structure, LOINC codes, deterministic UUIDs, unknown backends |
| `validator.py` | 100% | Valid resources pass, invalid raise, schema-not-found |
| `backends/` | 100% | Protocol compliance, resource counts, LOINC completeness |
| `scenarios/` | 100% | All 5 scenarios, clinical property assertions |
| `cli.py` | 97% | Direct API and subprocess CLI tests |

### Property Tests

- **Sepsis at t=180:** HR > 120, SpO2 < 90%, RR > 25
- **Normal at any t:** All vitals within SUPPORTED_LOINC clinical bounds
- **Cardiac arrest at t=122:** HR == 0 (flatline)
- **Post-op at t=240:** HR within 10% of baseline
- **Determinism:** Same seed → byte-identical JSON bundle
- **Noise statistics:** 10,000 samples, mean error < 0.1·σ, std ≈ σ

---

## Development

### Project Structure

```
fhir-synth/
├── src/fhir_synth/
│   ├── __init__.py           # Public API exports
│   ├── models.py             # TrendConfig, TimelineEvent, ClinicalTimeline, SynthConfig
│   ├── timeline.py           # build_timeline(), query_timeline(), list_scenarios()
│   ├── trends.py             # Trend functions, noise, dropout, clamp
│   ├── fhir_assembler.py     # Bundle assembly, resource dispatch
│   ├── validator.py          # FHIR R4 JSON Schema validation
│   ├── backends/
│   │   ├── base.py           # ResourceBackend protocol
│   │   ├── observation.py    # LOINC-coded vitals
│   │   ├── patient.py        # Demographics
│   │   └── encounter.py      # Admission/discharge
│   ├── scenarios/
│   │   ├── base.py
│   │   ├── normal.py
│   │   ├── icu_sepsis.py
│   │   ├── post_op.py
│   │   ├── ards.py
│   │   ├── cardiac_arrest.py
│   │   └── generic.py
│   └── cli.py                # CLI entry point
├── tests/
│   ├── test_models.py
│   ├── test_timeline.py
│   ├── test_trends.py
│   ├── test_fhir_assembler.py
│   ├── test_validator.py
│   ├── test_backends.py
│   ├── test_scenarios.py
│   └── test_cli.py
├── schemas/
│   └── fhir-r4-schema.json   # HL7 FHIR R4 JSON Schema
├── pyproject.toml
└── README.md
```

### Adding a New Scenario

1. Create `src/fhir_synth/scenarios/my_scenario.py`
2. Implement `build(config, seed=None, start_time=None) -> ClinicalTimeline`
3. Register in `src/fhir_synth/timeline.py` `_SCENARIO_REGISTRY` and `builders` dict
4. Add tests in `tests/test_scenarios.py`
5. Add documentation in this README

### Adding a New Backend

1. Create a class implementing the `ResourceBackend` protocol
2. Register in `src/fhir_synth/fhir_assembler.py` `_BACKEND_MAP`
3. Add tests in `tests/test_backends.py`

### Determinism Guarantee

`fhir-synth` guarantees that for the same arguments (`scenario`, `SynthConfig`, `seed`), the output FHIR Bundle will be byte-identical:

```python
bundle1 = assemble_fhir_bundle(build_timeline("icu_sepsis", config, seed=42), config)
bundle2 = assemble_fhir_bundle(build_timeline("icu_sepsis", config, seed=42), config)
assert json.dumps(bundle1, sort_keys=True) == json.dumps(bundle2, sort_keys=True)
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 ArashNIC

---

*Built for clinical simulation, testing, and research. Not for clinical use.*
