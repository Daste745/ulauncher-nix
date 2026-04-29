from __future__ import annotations

from collections.abc import Callable, Generator, Hashable, Iterable


def deduplicate[T, Key: Hashable](
    objs: Iterable[T],
    key: Callable[[T], Key],
) -> Generator[T]:
    """Deduplicate an iterable of objects using a key function"""

    seen = set[Key]()
    for obj in objs:
        k = key(obj)
        if k in seen:
            continue

        seen.add(k)
        yield obj
