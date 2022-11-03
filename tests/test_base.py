#!/usr/bin/env python

from typing import Any, NoReturn

import salient


def raise_Exception(*args: Any) -> NoReturn:
    raise RuntimeError("testing exception")


def test_salient_base() -> None:
    salient.base.Circle.set_pos(5, 6)
