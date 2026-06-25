"""Stage 2 Extension Harness — Per-Extension State Store."""

import math
from .errors import StateSchemaError

_ALLOWED_SCALARS = (int, float, bool, str, type(None))


def _validate_state_value(value, path="root"):
    if isinstance(value, _ALLOWED_SCALARS):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            raise StateSchemaError(f"float NaN/Inf not allowed at {path}: {value!r}")
        return
    if isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            _validate_state_value(item, f"{path}[{idx}]")
        return
    if isinstance(value, dict):
        for key, val in value.items():
            if not isinstance(key, str):
                raise StateSchemaError(
                    f"dict keys must be strings at {path}"
                )
            _validate_state_value(val, f"{path}.{key}")
        return
    raise StateSchemaError(f"Unsupported type {type(value).__name__} at {path}")


class StateStore:
    """Sandboxed key-value store for extension private state."""

    def __init__(self):
        self._stores = {}

    def get_state(self, run_id, ext_id, ext_version):
        key = (run_id, ext_id, ext_version)
        store = self._stores.get(key)
        if store is None:
            return {}
        return dict(store["data"])

    def set_state(self, run_id, ext_id, ext_version, state, schema_version):
        if not isinstance(state, dict):
            raise StateSchemaError("state must be a dict")
        if not isinstance(schema_version, int) or schema_version < 1:
            raise StateSchemaError("schema_version must be a positive int")
        _validate_state_value(state)
        key = (run_id, ext_id, ext_version)
        self._stores[key] = {
            "data": _deepcopy_state(state),
            "schema_version": schema_version,
        }

    def reset_run(self, run_id):
        kept = {}
        for k, v in self._stores.items():
            if k[0] != run_id:
                kept[k] = v
        self._stores = kept

    def reset_all(self):
        self._stores = {}

    def __repr__(self):
        return f"StateStore(runs={len(self._stores)})"


def _deepcopy_state(value):
    if isinstance(value, _ALLOWED_SCALARS):
        return value
    if isinstance(value, (list, tuple)):
        return type(value)(_deepcopy_state(item) for item in value)
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            result[str(k)] = _deepcopy_state(v)
        return result
    raise StateSchemaError(f"Cannot deepcopy type {type(value).__name__}")
