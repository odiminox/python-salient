from __future__ import annotations

from typing import Any

import tcod

from salient.loader import ffi, lib


class Point(object):
    def __init__(self, x: int, y: int, mouse_hover: bool, mouse_down: bool) -> None:
        self.x = x
        self.y = y
        self.mouse_hover = mouse_hover
        self.mouse_down = mouse_down
        self.point_c = self.__as_cdata()

    def __as_cdata(self) -> Any:
        return ffi.new("SALIENT_points_data_t *", (self.x, self.y, self.mouse_hover, self.mouse_down))

    def set(self, x: int, y: int) -> None:
        lib.SALIENT_point_set(x, y, self.point_c)

    def is_xy(self, x: int, y: int) -> bool:
        return bool(lib.SALIENT_point_is_xy(x, y, self.point_c))

    def is_point(self, point: Point) -> bool:
        return bool(lib.SALIENT_point_is_point(point, self.point_c))

    def mouse_xy(self, x: int, y: int, mouse: tcod.Mouse) -> None:
        lib.SALIENT_point_mouse_xy(x, y, mouse, self.point_c)

    def mouse_point(self, point: Point, mouse: tcod.Mouse) -> None:
        lib.SALIENT_point_mouse_point(point, mouse, self.point_c)


class Circle(object):
    def __init__(self, px: int, py: int, pr: int):
        self.x = px
        self.y = py
        self.r = pr
        self.mouse_hover = False
        self.mouse_down = False
        self.circle_c = self.__as_cdata()

    def __as_cdata(self) -> Any:
        return ffi.new(
            "SALIENT_circle_data_t *",
            (self.x, self.y, self.mouse_hover, self.mouse_down),
        )

    def set_pos(self, x: int, y: int) -> None:
        lib.SALIENT_circle_set_pos(x, y, self.circle_c)
