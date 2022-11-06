#!/usr/bin/env python

from typing import Any, NoReturn

import salient


def raise_Exception(*args: Any) -> NoReturn:
    raise RuntimeError("testing exception")


def test_salient_base() -> None:
    circle_1 = salient.base.Circle(5, 6, 10)
    circle_1.set_pos(5, 6)
    assert circle_1.x == 5
    assert circle_1.y == 6
    assert circle_1.r == 10
