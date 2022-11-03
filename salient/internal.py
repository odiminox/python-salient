"""This module internal helper functions used by the rest of the library.
"""
from __future__ import annotations

import functools
import warnings
from typing import Any, AnyStr, Callable, TypeVar, cast

import numpy as np
from numpy.typing import NDArray
from typing_extensions import Literal, NoReturn
