"""Window Pet 打包入口：与 build/WindowPet/Analysis-00.toc 记录的入口一致。"""
import sys
import traceback
from pathlib import Path


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log_file = Path(__file__).resolve().parent / "crash.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=== UNHANDLED EXCEPTION ===\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_exception

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WindowPet.DesktopPet.1.0")
    except Exception:
        pass

from window_pet_app.app import main

if __name__ == "__main__":
    try:
        main()
    except Exception:
        handle_exception(*sys.exc_info())
