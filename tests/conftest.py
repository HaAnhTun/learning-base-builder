import pytest
import yaml

from engine import database
from engine.config import ROOT


@pytest.fixture
def cfg(tmp_path):
    """Project default config (config.local.yaml is not read) with root pointing to a temp dir."""
    c = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    c["root"] = tmp_path
    return c


@pytest.fixture
def conn(tmp_path):
    c = database.connect(tmp_path / "test.db")
    yield c
    c.close()
