from typing import Iterable, TypeVar, Union, cast

T = TypeVar("T")


def to_array(x: Union[T, Iterable[T]]) -> Iterable[T]:
    if isinstance(x, (str, bytes)):
        return cast(list[T], [x])
    if isinstance(x, Iterable):
        return x
    return [x]
