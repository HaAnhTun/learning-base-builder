"""Every skill's frontmatter must be valid YAML: a broken block is silently ignored by Claude Code,
which then falls back to the first body line and drops flags such as disable-model-invocation."""
import re
from pathlib import Path

import pytest
import yaml

SKILLS = sorted((Path(__file__).resolve().parent.parent / ".claude" / "skills").glob("*/SKILL.md"))


def frontmatter(path):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path} has no frontmatter block"
    return yaml.safe_load(m.group(1))


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_frontmatter_parses_and_is_well_formed(path):
    data = frontmatter(path)
    assert isinstance(data, dict)
    assert data["name"] == path.parent.name
    assert isinstance(data["description"], str) and 0 < len(data["description"]) <= 1024
    if "disable-model-invocation" in data:
        assert data["disable-model-invocation"] is True
