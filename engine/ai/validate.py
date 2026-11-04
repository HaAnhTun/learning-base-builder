"""Minimal JSON-Schema subset validator for task results (no external dependency) and shared soft checks."""
import re

TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


class ValidationError(ValueError):
    pass


def _is_type(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, TYPES[name])


def validate(value, schema: dict, path: str = "$") -> None:
    """Supports: type (str or list), enum, required, properties, additionalProperties=False, items,
    minimum/maximum, minLength, minItems/maxItems."""
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_is_type(value, t) for t in types):
            raise ValidationError(f"{path}: expected {'/'.join(types)}, got {type(value).__name__}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise ValidationError(f"{path}: missing '{key}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(props)
            if extra:
                raise ValidationError(f"{path}: unexpected keys {sorted(extra)}")
        for key, sub in props.items():
            if key in value:
                validate(value[key], sub, f"{path}.{key}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValidationError(f"{path}: needs at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValidationError(f"{path}: at most {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                validate(item, schema["items"], f"{path}[{i}]")
    if _is_type(value, "number"):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValidationError(f"{path}: {value} < {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValidationError(f"{path}: {value} > {schema['maximum']}")
    if isinstance(value, str) and "minLength" in schema and len(value.strip()) < schema["minLength"]:
        raise ValidationError(f"{path}: string too short")


def mentions(text: str, term: str) -> bool:
    """Soft check: every word of the term (as a prefix, to tolerate inflection) appears in the text."""
    words = re.findall(r"[a-z0-9]+", term.lower())
    haystack = text.lower()
    return all(w[:max(3, len(w) - 2)] in haystack for w in words) if words else False


def soft_status(confidence: float | None, threshold: float, ok: bool) -> str:
    return "auto_approved" if ok and confidence is not None and confidence >= threshold else "needs_review"
