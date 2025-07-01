"""Compatibility package exposing project modules as ``immanuel_mcp``."""
from __future__ import annotations

import pathlib

__path__ = [str(pathlib.Path(__file__).resolve().parent.parent)]