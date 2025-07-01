import types
from immanuel_mcp.chart_service import ChartService


def _create_service() -> ChartService:
    """Create ChartService without triggering immanuel setup."""
    ChartService._setup_immanuel = lambda self: None  # type: ignore[attr-defined]
    return ChartService()


def test_interpret_aspect_dict():
    cs = _create_service()
    aspect = {
        'first': 'Sun',
        'second': 'Moon',
        'type': 'trine',
    }
    result = cs._interpret_aspect(aspect)
    assert 'Sun' in result
    assert 'Moon' in result
    assert 'harmony' in result


def test_interpret_aspect_object():
    cs = _create_service()
    aspect_obj = types.SimpleNamespace(
        first=types.SimpleNamespace(name='Sun'),
        second=types.SimpleNamespace(name='Moon'),
        type=types.SimpleNamespace(name='trine')
    )
    result = cs._interpret_aspect(aspect_obj)
    assert 'Sun' in result
    assert 'Moon' in result
    assert 'harmony' in result
