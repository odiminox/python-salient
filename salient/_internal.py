"""This module internal helper functions used by the rest of the library.
"""
from __future__ import annotations

import functools
import warnings
from typing import Any, Callable, TypeVar, cast

FuncType = Callable[..., Any]
F = TypeVar("F", bound=FuncType)


def deprecate(message: str, category: Any = DeprecationWarning, stacklevel: int = 0) -> Callable[[F], F]:
    """Return a decorator which adds a warning to functions."""

    def decorator(func: F) -> F:
        if not __debug__:
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore
            warnings.warn(message, category, stacklevel=stacklevel + 2)
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
