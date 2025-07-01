"""Compatibility package providing access to project modules."""
from __future__ import annotations

import importlib.util
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name: str, file_name: str):
    path = _ROOT / file_name
    spec = importlib.util.spec_from_file_location(f"immanuel_mcp.{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"immanuel_mcp.{name}"] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module

models = _load("models", "models.py")
utils = _load("utils", "utils.py")
chart_service = _load("chart_service", "chart_service.py")

try:  # Optional modules requiring external deps
    api = _load("api", "api.py")
    main = _load("main", "main.py")
    cli = _load("cli", "cli.py")
    app = main.app
except Exception:  # pragma: no cover - optional imports may fail in minimal env
    api = None
    main = None
    cli = None
    app = None
ChartService = chart_service.ChartService
ChartRequest = models.ChartRequest
ChartResponse = models.ChartResponse
ChartSettings = models.ChartSettings
Subject = models.Subject
InterpretationRequest = models.InterpretationRequest
ComparisonRequest = models.ComparisonRequest
TransitRequest = models.TransitRequest

__all__ = [
    "app",
    "ChartService",
    "ChartRequest",
    "ChartResponse",
    "ChartSettings",
    "Subject",
    "InterpretationRequest",
    "ComparisonRequest",
    "TransitRequest",
]
