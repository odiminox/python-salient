"""This module just an alias for salient"""
import warnings

warnings.warn(
    "'import salient as salientpy' is preferred.",
    DeprecationWarning,
    stacklevel=2,
)
from salient import *  # noqa: F4
