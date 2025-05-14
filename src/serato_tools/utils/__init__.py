import logging
import os
from typing import Iterable, TypeVar, Type, cast, Any
from enum import Enum

T = TypeVar("T")

logger = logging.getLogger("serato-tools")

SERATO_FOLDER = os.path.join(os.path.expanduser("~"), "Music", "_Serato_")


def get_key_from_value(value: T, dict: dict[str, T]) -> str:
    for key, v in dict.items():
        if v == value:
            return key
    raise ValueError(f"no key for value {value}")


def get_enum_key_from_value(value: str | bytes, enum_class: Type[Enum]):
    for member in enum_class:
        if member.value == value:
            return member.name
    raise ValueError(f"no key for value {value}")


def to_array(x: T | Iterable[T]) -> Iterable[T]:
    if isinstance(x, (str, bytes)):
        return cast(list[T], [x])
    if isinstance(x, Iterable):
        return x
    return [x]


class DataTypeError(Exception):
    def __init__(self, value: Any, expected_type: type | Iterable[type], field: str | None):
        super().__init__(
            f"value must be {' or '.join(e.__name__ for e in to_array(expected_type))} when field is {field} (type: {type(value).__name__}) (value: {str(value)})"
        )
