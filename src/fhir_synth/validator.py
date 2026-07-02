import json
import os
import warnings

import jsonschema
from jsonschema import ValidationError, Draft6Validator
from jsonschema.validators import RefResolver


_SCHEMA: dict | None = None
_VALIDATORS: dict[str, Draft6Validator] | None = None


def _ensure_schema() -> tuple[dict, dict[str, Draft6Validator]]:
    global _SCHEMA, _VALIDATORS
    if _SCHEMA is not None and _VALIDATORS is not None:
        return _SCHEMA, _VALIDATORS

    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "schemas", "fhir-r4-schema.json"
    )
    schema_path = os.path.normpath(schema_path)

    if not os.path.exists(schema_path):
        msg = f"FHIR R4 schema not found at {schema_path}"
        raise FileNotFoundError(msg)

    with open(schema_path) as f:
        schema = json.load(f)

    resolver = RefResolver.from_schema(schema)
    validators = {}
    for def_name in list(schema.get("definitions", {}).keys()):
        schema_def = schema["definitions"][def_name]
        if isinstance(schema_def, dict):
            validators[def_name] = Draft6Validator(
                schema_def, resolver=resolver
            )

    _SCHEMA = schema
    _VALIDATORS = validators
    return schema, validators


def validate_fhir_resource(resource: dict, resource_type: str | None = None) -> bool:
    schema, validators = _ensure_schema()

    if resource_type is None:
        resource_type = resource.get("resourceType", "")
    if not resource_type:
        msg = "Resource has no resourceType"
        raise ValidationError(msg)

    validator = validators.get(resource_type)
    if validator is None:
        msg = f"No schema definition for resource type: {resource_type}"
        raise ValidationError(msg)

    errors = list(validator.iter_errors(resource))
    if errors:
        raise errors[0]

    return True
