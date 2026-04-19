from __future__ import annotations

from typing import TypeAlias

from warlock_sentinel.adapters.base import BaseAdapter

AdapterType: TypeAlias = type[BaseAdapter]

_ADAPTERS: dict[str, AdapterType] = {}


def register_adapter(framework: str, adapter_cls: AdapterType) -> None:
    _ADAPTERS[framework] = adapter_cls


def get_adapter(framework: str) -> BaseAdapter:
    try:
        adapter_cls = _ADAPTERS[framework]
    except KeyError as error:
        raise KeyError(f"No adapter registered for framework '{framework}'") from error
    return adapter_cls()


def supported_frameworks() -> list[str]:
    return sorted(_ADAPTERS)


from warlock_sentinel.adapters.flutter_adapter import FlutterAdapter  # noqa: E402
from warlock_sentinel.adapters.react_adapter import ReactAdapter  # noqa: E402

register_adapter("flutter", FlutterAdapter)
register_adapter("react", ReactAdapter)