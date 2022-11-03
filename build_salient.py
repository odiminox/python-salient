#!/usr/bin/env python3
from __future__ import annotations

import glob
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Set, Tuple, Union

from cffi import FFI  # type: ignore

sys.path.append(str(Path(__file__).parent))  # Allow importing local modules.

import build_sdl  # noqa: E402

Py_LIMITED_API = 0x03060000

HEADER_PARSE_PATHS = ("salient/", "libsalient/src/salient/,", "libsalient/src/salient/*")
HEADER_PARSE_EXCLUDES = ("gl2_ext_.h", "renderer_gl_internal.h", "event.h")

BITSIZE, LINKAGE = platform.architecture()

# Regular expressions to parse the headers for cffi.
RE_COMMENT = re.compile(r"\s*/\*.*?\*/|\s*//*?$", re.DOTALL | re.MULTILINE)
RE_CPLUSPLUS = re.compile(r"#ifdef __cplusplus.*?#endif.*?$", re.DOTALL | re.MULTILINE)
RE_PREPROCESSOR = re.compile(r"(?!#define\s+\w+\s+\d+$)#.*?(?<!\\)$", re.DOTALL | re.MULTILINE)
RE_INCLUDE = re.compile(r'#include "([^"]*)"')
RE_TAGS = re.compile(
    r"SALIENTLIB_C?API|SALIENT_PUBLIC|SALIENT_NODISCARD|SALIENT_DEPRECATED_NOMESSAGE|SALIENT_DEPRECATED_ENUM"
    r"|(SALIENT_DEPRECATED|SALIENTLIB_FORMAT)\([^)]*\)|__restrict"
)
RE_VAFUNC = re.compile(r"^[^;]*\([^;]*va_list.*\);", re.MULTILINE)
RE_INLINE = re.compile(r"(^.*?inline.*?\(.*?\))\s*\{.*?\}$", re.DOTALL | re.MULTILINE)


class ParsedHeader:
    """Header manager class for parsing headers.

    Holds parsed sources and keeps information needed to resolve header order.
    """

    # Class dictionary of all parsed headers.
    all_headers: Dict[Path, ParsedHeader] = {}

    def __init__(self, path: Path) -> None:
        self.path = path = path.resolve(True)
        directory = path.parent
        depends = set()
        with open(self.path, "r", encoding="utf-8") as f:
            header = f.read()
        header = RE_COMMENT.sub("", header)
        header = RE_CPLUSPLUS.sub("", header)
        for dependency in RE_INCLUDE.findall(header):
            depends.add((directory / dependency).resolve(True))
        header = RE_PREPROCESSOR.sub("", header)
        header = RE_TAGS.sub("", header)
        header = RE_VAFUNC.sub("", header)
        header = RE_INLINE.sub(r"\1;", header)
        self.header = header.strip()
        self.depends = frozenset(depends)
        self.all_headers[self.path] = self

    def parsed_depends(self) -> Iterator["ParsedHeader"]:
        """Return dependencies excluding ones that were not loaded."""
        for dep in self.depends:
            try:
                yield self.all_headers[dep]
            except KeyError:
                pass

    def __str__(self) -> str:
        return "Parsed harder at '%s'\n Depends on: %s" % (
            self.path,
            "\n\t".join(self.depends),
        )

    def __repr__(self) -> str:
        return f"ParsedHeader({self.path})"


def walk_includes(directory: str) -> Iterator[ParsedHeader]:
    """Parse all the include files in a directory and subdirectories."""
    for path, _dirs, files in os.walk(directory):
        for file in files:
            if file in HEADER_PARSE_EXCLUDES:
                continue
            if file.endswith(".h"):
                yield ParsedHeader(Path(path, file).resolve(True))


def resolve_dependencies(
    includes: Iterable[ParsedHeader],
) -> List[ParsedHeader]:
    """Sort headers by their correct include order."""
    unresolved = set(includes)
    resolved: Set[ParsedHeader] = set()
    result = []
    while unresolved:
        for item in unresolved:
            if frozenset(item.parsed_depends()).issubset(resolved):
                resolved.add(item)
                result.append(item)
        if not unresolved & resolved:
            raise RuntimeError(
                "Could not resolve header load order.\n"
                f"Possible cyclic dependency with the unresolved headers:\n{unresolved}"
            )
        unresolved -= resolved
    return result


def parse_includes() -> List[ParsedHeader]:
    """Collect all parsed header files and return them.

    Reads HEADER_PARSE_PATHS and HEADER_PARSE_EXCLUDES.
    """
    includes: List[ParsedHeader] = []
    for dirpath in HEADER_PARSE_PATHS:
        includes.extend(walk_includes(dirpath))
    return resolve_dependencies(includes)


def walk_sources(directory: str) -> Iterator[str]:
    for path, _dirs, files in os.walk(directory):
        for source in files:
            if source.endswith(".c"):
                yield str(Path(path, source))


includes = parse_includes()

module_name = "salient._libsalient"
include_dirs: List[str] = [
    ".",
    "libsalient/src/vendor/",
    "libsalient/src/vendor/utf8proc",
    "libsalient/src/vendor/zlib/",
    *build_sdl.include_dirs,
]

extra_compile_args: List[str] = [*build_sdl.extra_compile_args]
extra_link_args: List[str] = [*build_sdl.extra_link_args]
sources: List[str] = []

libraries: List[str] = [*build_sdl.libraries]
library_dirs: List[str] = [*build_sdl.library_dirs]
define_macros: List[Tuple[str, Any]] = [("Py_LIMITED_API", Py_LIMITED_API)]

sources += walk_sources("salient/")
sources += walk_sources("libsalient/src/salient/")
sources += ["libsalient/src/vendor/stb.c"]
sources += ["libsalient/src/vendor/glad.c"]
sources += ["libsalient/src/vendor/lodepng.c"]
sources += ["libsalient/src/vendor/utf8proc/utf8proc.c"]
sources += glob.glob("libsalient/src/vendor/zlib/*.c")

if sys.platform == "win32":
    libraries += ["User32"]
    define_macros.append(("SALIENTLIB_API", ""))
    define_macros.append(("_CRT_SECURE_NO_WARNINGS", None))

if sys.platform in ["win32", "darwin"]:
    include_dirs.append("libsalient/src/zlib/")


if sys.platform == "darwin":
    # Fix "implicit declaration of function 'close'" in zlib.
    define_macros.append(("HAVE_UNISTD_H", 1))


tdl_build = os.environ.get("TDL_BUILD", "RELEASE").upper()

MSVC_CFLAGS = {"DEBUG": ["/Od"], "RELEASE": ["/GL", "/O2", "/GS-", "/wd4996"]}
MSVC_LDFLAGS: Dict[str, List[str]] = {"DEBUG": [], "RELEASE": ["/LTCG"]}
GCC_CFLAGS = {
    "DEBUG": ["-std=c99", "-Og", "-g", "-fPIC"],
    "RELEASE": [
        "-std=c99",
        "-flto",
        "-O3",
        "-g",
        "-fPIC",
        "-Wno-deprecated-declarations",
        "-Wno-discarded-qualifiers",  # Ignore discarded restrict qualifiers.
    ],
}

if sys.platform == "win32" and "--compiler=mingw32" not in sys.argv:
    extra_compile_args.extend(MSVC_CFLAGS[tdl_build])
    extra_link_args.extend(MSVC_LDFLAGS[tdl_build])
else:
    extra_compile_args.extend(GCC_CFLAGS[tdl_build])
    extra_link_args.extend(GCC_CFLAGS[tdl_build])

ffi = FFI()
ffi.cdef(build_sdl.get_cdef())
for include in includes:
    try:
        ffi.cdef(include.header)
    except Exception:
        # Print the source, for debugging.
        print(f"Error with: {include.path}")
        for i, line in enumerate(include.header.split("\n"), 1):
            print("%03i %s" % (i, line))
        raise
ffi.cdef(
    """
#define SALIENT_COMPILEDVERSION ...
"""
)
ffi.set_source(
    module_name,
    "#include <salient/cffi.h>\n#include <SDL.h>",
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    sources=sources,
    libraries=libraries,
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    define_macros=define_macros,
    py_limited_api=True,
)

CONSTANT_MODULE_HEADER = '''"""Constants from the libsalient C API.

This module is auto-generated by `build_salient.py`.
"""
from salient.color import Color

'''

EVENT_CONSTANT_MODULE_HEADER = '''"""Event constants from SDL's C API.

This module is auto-generated by `build_libtcod.py`.
"""
'''


EXCLUDE_CONSTANTS = [
    "SALIENT_MAJOR_VERSION",
    "SALIENT_MINOR_VERSION",
    "SALIENT_PATCHLEVEL",
    "SALIENT_COMPILEDVERSION",
    "SALIENT_PATHFINDER_MAX_DIMENSIONS",
    "SALIENT_KEY_TEXT_SIZE",
    "SALIENT_NOISE_MAX_DIMENSIONS",
    "SALIENT_NOISE_MAX_OCTAVES",
    "SALIENT_FALLBACK_FONT_SIZE",
]

EXCLUDE_CONSTANT_PREFIXES = [
    "SALIENT_E_",
    "SALIENT_HEAP_",
    "SALIENT_LEX_",
    "SALIENT_CHARMAP_",
    "SALIENT_LOG_",
]


def update_module_all(filename: str, new_all: str) -> None:
    """Update the __all__ of a file with the constants from new_all."""
    RE_CONSTANTS_ALL = re.compile(
        r"(.*# --- From constants.py ---).*(# --- End constants.py ---.*)",
        re.DOTALL,
    )
    with open(filename, "r", encoding="utf-8") as f:
        match = RE_CONSTANTS_ALL.match(f.read())
    assert match, f"Can't determine __all__ subsection in {filename}!"
    header, footer = match.groups()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"{header}\n    {new_all},\n    {footer}")


def generate_enums(prefix: str) -> Iterator[str]:
    """Generate attribute assignments suitable for a Python enum."""
    for name, value in sorted(find_sdl_attrs(prefix), key=lambda item: item[1]):
        name = name.split("_", 1)[1]
        if name.isdigit():
            name = f"N{name}"
        if name in "IOl":  # Handle Flake8 warnings.
            yield f"{name} = {value}  # noqa: E741"
        else:
            yield f"{name} = {value}"
