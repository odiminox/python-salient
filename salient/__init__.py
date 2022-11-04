"""The Python port of Salient.

Bring any issues or feature requests to GitHub: https://github.com/Odiminox/python-salient

Read the documentation online: https://python-salient.readthedocs.io/en/latest/
"""

from __future__ import annotations

import sys
import warnings

from salient import base
from salient.constants import *
from salient.loader import __sdl_version__, ffi, lib

try:
    from salient.version import __version__
except ImportError:  # Gets imported without version.py by ReadTheDocs
    __version__ = ""

if sys.version_info < (3, 6):
    warnings.warn(
        "Support for Python 3.5 has been dropped from python-salient.",
        DeprecationWarning,
        stacklevel=2,
    )

__all__ = [  # noqa: F405
    "__version__",
    "lib",
    "ffi",
    "base"
    # --- From salientpy.py ---
    # --- From constants.py ---
    # --- End constants.py ---
]
