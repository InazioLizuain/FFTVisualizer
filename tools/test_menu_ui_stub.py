#!/usr/bin/env python3
import time
import yaml

from menu_system import MenuSystem


class StubVisualizer:
    def __init__(self, config: dict):
        self._config = config

    def change_input_mode(self, mode: str):
        self._config["audio"]["default_mode"] = mode
        print(f"[stub] input_mode={mode}")

    def set_brightness(self, brightness: int):
        self._config["display"]["brightness"] = int(brightness)
        print(f"[stub] brightness={brightness}")

    def set_color_scheme(self, scheme: str):
        self._config["visualization"]["color_scheme"] = str(scheme)
        print(f"[stub] color_scheme={scheme}")

    def get_status(self) -> dict:
        return {
            "running": False,
            "input_mode": self._config["audio"].get("default_mode", "low_level"),
            "brightness": self._config["display"].get("brightness", 75),
            "color_scheme": self._config["visualization"].get("color_scheme", "rainbow"),
            "sample_rate": self._config["audio"].get("sample_rate", 44100),
        }


def main() -> int:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    visualizer = StubVisualizer(config)
    menu = MenuSystem(config.get("menu", {}), visualizer)
    menu.start()

    print("Menu UI stub running for 60s.")
    print("Rotate/press the encoder. You should see the OLED update and console logs when actions trigger.")

    try:
        time.sleep(60)
    finally:
        menu.stop()

    print("Menu UI stub completed OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
