import ast
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAYERS = ["core", "accounts", "board", "projects", "sprints", "backlog", "gantt", "budget", "tickets"]
SERVICES = sorted((ROOT / "apps").glob("*/services.py"))


def _imported_apps(path):
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("apps."):
            found.add(node.module.split(".")[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("apps."):
                    found.add(alias.name.split(".")[1])
    return found


@pytest.mark.parametrize("path", SERVICES, ids=lambda p: p.parent.name)
def test_services_respect_layer_order(path):
    own = path.parent.name
    for imported in _imported_apps(path):
        assert LAYERS.index(imported) <= LAYERS.index(own), f"{own}.services importa {imported}, una capa superior"


@pytest.mark.parametrize("path", SERVICES, ids=lambda p: p.parent.name)
def test_services_import_in_fresh_interpreter(path):
    module = f"apps.{path.parent.name}.services"
    code = f"import django; django.setup(); import {module}"
    env = {"SECRET_KEY": "x", "DEBUG": "true", "DJANGO_SETTINGS_MODULE": "config.settings"}
    import os

    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, env={**os.environ, **env}
    )
    assert result.returncode == 0, result.stderr
