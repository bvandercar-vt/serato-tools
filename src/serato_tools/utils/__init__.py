import logging
from typing import Iterable, TypeVar, Union, cast, Any

try:
    from typing import NotRequired  # Python 3.11+ # pyright: ignore[reportAttributeAccessIssue]
except ImportError:
    from typing_extensions import NotRequired  # For Python 3.10

T = TypeVar("T")

logger = logging.getLogger("serato-tools")


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
