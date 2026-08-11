import tomllib
from pathlib import Path
import reality_handoff
from reality_handoff.webapp import app


def test_public_version_is_consistent():
    pyproject = tomllib.loads(Path('pyproject.toml').read_text())
    expected = pyproject['project']['version']
    assert reality_handoff.__version__ == expected
    assert app.version == expected
