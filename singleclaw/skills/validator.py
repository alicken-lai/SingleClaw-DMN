"""Skill Validator – validate input/output JSON Schemas declared in ``skill.yaml``.

Provides ``SkillValidator`` which checks:

1. **Manifest validation** – the ``input_schema`` and ``output_schema`` fields
   (when present) are valid JSON Schema Draft 7 objects.  Also forwards any
   pre-existing registry-level errors from the ``Skill`` dataclass.

2. **Input validation** – a data ``dict`` conforms to the skill's
   ``input_schema`` (if one is declared).

3. **Output validation** – a data ``dict`` conforms to the skill's
   ``output_schema`` (if one is declared).

When no schema is declared, validation passes unconditionally (backward
compatible with skills that pre-date v0.4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import jsonschema
import jsonschema.exceptions

from singleclaw.skills.registry import Skill


@dataclass
class ValidationResult:
    """Result of a validation check.

    Attributes:
        is_valid: ``True`` when all checks passed.
        errors:   Human-readable error messages (empty when ``is_valid`` is ``True``).
    """

    is_valid: bool
    errors: list[str] = field(default_factory=list)


class SkillValidator:
    """Validate skill manifests and runtime data against declared JSON Schemas.

    All methods return a :class:`ValidationResult`; they never raise.
    """

    # ─── public API ───────────────────────────────────────────────────────────

    def validate_manifest(self, skill: Skill) -> ValidationResult:
        """Validate the skill manifest.

        Checks:
        - Forwards any existing registry-level ``skill.errors``.
        - Meta-validates ``input_schema`` (if present) against JSON Schema Draft 7.
        - Meta-validates ``output_schema`` (if present) against JSON Schema Draft 7.

        Args:
            skill: A :class:`~singleclaw.skills.registry.Skill` instance.

        Returns:
            :class:`ValidationResult` with combined errors.
        """
        errors: list[str] = []

        # Forward pre-existing registry validation errors.
        errors.extend(skill.errors)

        # Meta-validate declared schemas.
        for field_name in ("input_schema", "output_schema"):
            schema = skill.metadata.get(field_name)
            if schema is not None:
                schema_errors = self._meta_validate(schema, field_name)
                errors.extend(schema_errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def validate_input(self, skill: Skill, data: dict) -> ValidationResult:
        """Validate ``data`` against the skill's ``input_schema``.

        If the skill has no ``input_schema``, the check always passes.

        Args:
            skill: A :class:`~singleclaw.skills.registry.Skill` instance.
            data:  The input data dictionary to validate.

        Returns:
            :class:`ValidationResult`.
        """
        return self._validate_data(skill, data, "input_schema")

    def validate_output(self, skill: Skill, data: dict) -> ValidationResult:
        """Validate ``data`` against the skill's ``output_schema``.

        If the skill has no ``output_schema``, the check always passes.

        Args:
            skill: A :class:`~singleclaw.skills.registry.Skill` instance.
            data:  The output data dictionary to validate.

        Returns:
            :class:`ValidationResult`.
        """
        return self._validate_data(skill, data, "output_schema")

    # ─── internals ────────────────────────────────────────────────────────────

    def _validate_data(self, skill: Skill, data: dict, field_name: str) -> ValidationResult:
        """Validate *data* against the JSON Schema stored in *field_name*."""
        schema = skill.metadata.get(field_name)
        if schema is None:
            return ValidationResult(is_valid=True)

        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as exc:
            return ValidationResult(is_valid=False, errors=[exc.message])
        except jsonschema.exceptions.SchemaError as exc:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid {field_name} (schema error): {exc.message}"],
            )

        return ValidationResult(is_valid=True)

    @staticmethod
    def _meta_validate(schema: object, field_name: str) -> list[str]:
        """Check that *schema* is a valid JSON Schema Draft 7 object.

        Returns a list of error messages (empty on success).
        """
        try:
            jsonschema.Draft7Validator.check_schema(schema)
        except jsonschema.exceptions.SchemaError as exc:
            return [f"Invalid {field_name}: {exc.message}"]
        return []
