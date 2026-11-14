from __future__ import annotations

import importlib
from typing import Type

from core.base_unit import BaseUnit

# Maps unit name -> "module.path:ClassName".
# Adding a new unit means adding one line here and a section in settings.yaml.
UNIT_PATHS: dict[str, str] = {
    "order_sync": "units.order_sync.unit:OrderSyncUnit",
    "report_gen": "units.report_gen.unit:ReportGenUnit",
}


def resolve(name: str) -> Type[BaseUnit]:
    if name not in UNIT_PATHS:
        raise KeyError(f"unknown unit: {name}")
    module_path, class_name = UNIT_PATHS[name].split(":")
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    if not issubclass(cls, BaseUnit):
        raise TypeError(f"{class_name} is not a BaseUnit subclass")
    return cls
