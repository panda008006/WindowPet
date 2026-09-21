import argparse
import os
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import control_panel as control_panel_module
from window_pet_app import state
from window_pet_app.constants import APP_STYLE
from window_pet_app.control_panel import ControlPanel
from window_pet_app.medals import MedalStore


PAGE_NAMES = {
    "桌宠": "01-pets",
    "工具": "02-tools",
    "兑换": "03-redeem",
    "勋章": "04-medals",
    "日程": "05-schedule",
    "设置": "06-settings",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(APP_STYLE)

    with tempfile.TemporaryDirectory(prefix="windowpet-ui-capture-") as temp_dir:
        temp = Path(temp_dir)
        config_path = temp / "config.json"
        config_path.write_text("{}", encoding="utf-8")
        store = MedalStore(temp / "medals.json")
        store.record_launch()
        for trigger in ("left-click", "wheel-scroll", "right-double-click"):
            store.record_trigger(trigger)
        store.record_pet("xiaoba")

        assets_module.CONFIG_PATH = config_path
        assets_module.SETTINGS_PATH = config_path
        control_panel_module.CONFIG_PATH = config_path
        state.ASSETS_DIR = Path("assets").resolve()
        state.PET_UNLOCKS = None
        state.MEDAL_STORE = store
        state.WINDOWS = []

        panel = ControlPanel()
        panel.resize(1180, 820)
        panel.show()
        app.processEvents()

        captured = []
        for index, button in enumerate(panel.tabs.buttons):
            label = button.toolTip().strip()
            stem = PAGE_NAMES.get(label, f"{index + 1:02d}-{label or 'page'}")
            panel.tabs.setCurrentIndex(index)
            app.processEvents()
            path = args.output / f"{stem}.png"
            if not panel.grab().save(str(path), "PNG"):
                raise RuntimeError(f"Could not save {path}")
            captured.append(path.name)

        panel.close()
        panel.deleteLater()
        app.processEvents()

    print("\n".join(captured))
    app.quit()


if __name__ == "__main__":
    main()
