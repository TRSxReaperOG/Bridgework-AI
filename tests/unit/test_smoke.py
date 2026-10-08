import importlib

import pytest


@pytest.mark.parametrize(
    "package",
    [
        "bridgework",
        "bridgework.config",
        "bridgework.schemas",
        "bridgework.agents",
        "bridgework.orchestrator",
        "bridgework.controllers",
        "bridgework.services",
        "bridgework.repositories",
        "bridgework.prompts",
        "bridgework.cli",
    ],
)
def test_project_packages_import(package):
    importlib.import_module(package)


@pytest.mark.parametrize("dependency", ["pydantic"])
def test_dependencies_installed(dependency):
    importlib.import_module(dependency)
