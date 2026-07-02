import pytest
from jsonschema import ValidationError

from fhir_synth.validator import validate_fhir_resource


class TestValidator:
    def test_valid_patient(self):
        resource = {
            "resourceType": "Patient",
            "id": "test-1",
            "identifier": [{"system": "https://example.com", "value": "test-1"}],
            "gender": "male",
            "birthDate": "1990-01-01",
        }
        assert validate_fhir_resource(resource, "Patient") is True

    def test_valid_observation(self):
        resource = {
            "resourceType": "Observation",
            "id": "obs-1",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8867-4",
                        "display": "Heart Rate",
                    }
                ]
            },
            "subject": {"reference": "Patient/test-1"},
            "effectiveDateTime": "2024-01-01T00:00:00Z",
            "valueQuantity": {
                "value": 72.0,
                "unit": "bpm",
                "system": "http://unitsofmeasure.org",
                "code": "bpm",
            },
        }
        assert validate_fhir_resource(resource, "Observation") is True

    def test_valid_encounter(self):
        resource = {
            "resourceType": "Encounter",
            "id": "enc-1",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "IMP",
                "display": "inpatient encounter",
            },
            "subject": {"reference": "Patient/test-1"},
            "period": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-02T00:00:00Z",
            },
        }
        assert validate_fhir_resource(resource, "Encounter") is True

    def test_valid_minimal_resource(self):
        resource = {
            "resourceType": "Patient",
            "id": "test-1",
        }
        assert validate_fhir_resource(resource, "Patient") is True

    def test_invalid_resource_type_value(self):
        resource = {
            "resourceType": "Patient",
            "gender": "invalid_gender_value",
        }
        with pytest.raises(ValidationError):
            validate_fhir_resource(resource, "Patient")

    def test_invalid_missing_resource_type(self):
        resource = {"id": "test"}
        with pytest.raises(ValidationError, match="Resource has no resourceType"):
            validate_fhir_resource(resource)

    def test_auto_detect_resource_type(self):
        resource = {
            "resourceType": "Patient",
            "id": "test-1",
            "identifier": [{"system": "https://example.com", "value": "test-1"}],
            "gender": "male",
            "birthDate": "1990-01-01",
        }
        assert validate_fhir_resource(resource) is True

    def test_schema_not_found(self, monkeypatch):
        import fhir_synth.validator as v
        import os
        v._SCHEMA = None
        v._VALIDATORS = None
        real_exists = os.path.exists
        def fake_exists(path):
            if "fhir-r4-schema.json" in path:
                return False
            return real_exists(path)
        monkeypatch.setattr(os.path, "exists", fake_exists)
        with pytest.raises(FileNotFoundError, match="FHIR R4 schema not found"):
            validate_fhir_resource({"resourceType": "Patient", "id": "1"})

    def test_unknown_resource_type_raises(self):
        with pytest.raises(ValidationError, match="No schema definition for resource type"):
            validate_fhir_resource({"resourceType": "NonexistentType"}, "NonexistentType")
