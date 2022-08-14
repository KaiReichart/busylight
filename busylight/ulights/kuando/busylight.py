"""
"""

from typing import Tuple

from loguru import logger

from ..hidlight import HIDLight
from ..light import LightInfo

from ._busylight import CommandBuffer, Instruction


class Busylight(HIDLight):
    @staticmethod
    def supported_device_ids() -> dict[tuple[int, int], str]:
        return {
            (0x04D8, 0xF848): "Busylight Alpha",
            (0x27BB, 0x3BCA): "Busylight Alpha",
            (0x27BB, 0x3BCD): "Busylight Omega",
            (0x27BB, 0x3BCF): "Busylight Omega",
        }

    @staticmethod
    def vendor() -> str:
        return "Kuando"

    def __init__(
        self,
        light_info: LightInfo,
        reset: bool = True,
        exclusive: bool = True,
    ) -> None:

        self.command = CommandBuffer()
        super().__init__(light_info, reset=reset, exclusive=exclusive)

    def __bytes__(self) -> bytes:

        return bytes(self.command)

    async def keepalive(self, interval: int = 0xF) -> None:

        interval = interval & 0x0F
        sleep_interval = round(interval / 2)
        command = Instruction.KeepAlive(interval).value

        while True:
            with self.batch_update():
                light.command.line0 = command
            await asyncio.sleep(sleep_interval)

    def on(self, color: Tuple[int, int, int]) -> None:

        with self.batch_update():
            self.color = color
            instruction = Instruction.Jump(target=0, color=color, on_time=0, off_time=0)
            self.command.line0 = instruction.value

        self.add_task("keepalive", self.keepalive)

    def off(self) -> None:

        with self.batch_update():
            self.color = (0, 0, 0)
            instruction = Instruction.Jump(
                target=0, color=self.color, on_time=0, off_time=0
            )
            self.command.line0 = instruction.value

    @property
    def red(self) -> int:
        return getattr(self, "_red", 0)

    @red.setter
    def red(self, new_value: int) -> int:
        self._red = new_value

    @property
    def green(self) -> int:
        return getattr(self, "_green", 0)

    @green.setter
    def green(self, new_value: int) -> int:
        self._green = new_value

    @property
    def blue(self) -> int:
        return getattr(self, "_blue", 0)

    @blue.setter
    def blue(self, new_value: int) -> int:
        self._blue = new_value
