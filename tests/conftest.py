from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_legacy_path = Path(__file__).with_name("confest.py")
_spec = spec_from_file_location("_legacy_confest", _legacy_path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Could not load legacy fixtures module: {_legacy_path}")

_legacy = module_from_spec(_spec)
_spec.loader.exec_module(_legacy)

for _name, _value in vars(_legacy).items():
    if not _name.startswith("__"):
        globals()[_name] = _value
