import argparse
import os
import sys
import tempfile
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import control_panel as control_panel_module
from window_pet_app import state
from window_pet_app.constants import APP_STYLE
from window_pet_app.control_panel import ControlPanel
from window_pet_app.medals import MedalStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    app = QApplication.instance() or QApplication([])
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(APP_STYLE)

    with tempfile.TemporaryDirectory(prefix="windowpet-medal-qa-") as temp_dir:
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
        panel.tabs.setCurrentIndex(panel.medals_tab_index)
        panel.show()
        app.processEvents()

        if panel.page_stack.currentIndex() != panel.medals_tab_index:
            raise RuntimeError("Medal page did not become the active cockpit page")
        if len(panel.medal_cards) != 9:
            raise RuntimeError(f"Expected 9 medal cards, got {len(panel.medal_cards)}")
        if not panel.grab().save(str(args.output), "PNG"):
            raise RuntimeError(f"Could not save screenshot: {args.output}")

        panel.set_medals_hidden(True)
        app.processEvents()
        if not panel.medal_grid_widget.isHidden() or panel.medals_hidden_card.isHidden():
            raise RuntimeError("Hide-medal-wall state did not render correctly")
        panel.set_medals_hidden(False)
        app.processEvents()
        if panel.medal_grid_widget.isHidden() or not panel.medals_hidden_card.isHidden():
            raise RuntimeError("Restore-medal-wall state did not render correctly")

        panel.close()
        panel.deleteLater()
        app.processEvents()

    print(str(args.output.resolve()))
    app.quit()


if __name__ == "__main__":
    main()
