import logging
import os
from typing import Iterable, TypeVar, Union, cast, Any


T = TypeVar("T")

logger = logging.getLogger("serato-tools")

SERATO_FOLDER = os.path.join(os.path.expanduser("~"), "Music\\_Serato_")


def to_array(x: Union[T, Iterable[T]]) -> Iterable[T]:
    if isinstance(x, (str, bytes)):
        return cast(list[T], [x])
    if isinstance(x, Iterable):
        return x
    return [x]


class DataTypeError(Exception):
    def __init__(
        self,
        value: Any,
        expected_type: Union[type, Iterable[type]],
        field: Union[str, None],
    ):
        super().__init__(
            f"value must be {' or '.join(e.__name__ for e in to_array(expected_type))} when field is {field} (type: {type(value).__name__}) (value: {str(value)})"
        )
