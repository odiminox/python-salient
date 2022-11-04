from __future__ import annotations

from salient.loader import ffi, lib


class Circle:
    def __init__(self, x: int, y: int, r: int, mouse_hover: bool, mouse_down: bool):
        self.x = x
        self.y = y
        self.r = r
        self.mouse_hover = mouse_hover
        self.mouse_down = mouse_down
        self.circle_data = self.circle_c = ffi.new(
            "struct SALIENT_circle_data_t",
            {"x": x, "y": y, "r": r, "mouse_hover": mouse_hover, "mouse_down": mouse_down},
        )

    @classmethod
    def set_pos(self, x: int, y: int) -> None:
        lib.SALIENT_circle_set_pos(x, y, self, self.circle_c)
