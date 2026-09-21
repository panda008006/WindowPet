import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from . import state
from .assets import assets_for_pack, config_warning, import_gif_to_assets, load_config, resolved_path, save_config, seed_default_assets_dir
from .character_acquisition import ensure_ai_authoring_guide
from .constants import APP_DISPLAY_NAME, DARK_STYLE, DEFAULT_GIF, ICON_PATH
from .control_panel import ControlPanel
from .logging_utils import configure_logging, log_info
from .medals import MedalStore
from .interactions import PetInteractionController
from .overlay import add_window, exit_app, refresh_control_panel
from .recovery import bring_all_overlays_to_center, disable_click_through_for_all, show_all_overlays
from .style_utils import apply_light_palette, apply_non_native_dialogs, style_menu
from .updater import check_for_updates, open_official_site
from .feather_tool import show_feather_tool
from .whip_tool import show_whip_tool

_SINGLE_INSTANCE_MUTEX = None


def show_control_panel():
    if state.CONTROL_PANEL is not None:
        state.CONTROL_PANEL.show()
        state.CONTROL_PANEL.raise_()
        state.CONTROL_PANEL.activateWindow()


def load_app_icon():
    icon = QIcon()
    if ICON_PATH.exists():
        icon.addFile(str(ICON_PATH))
    png_path = ICON_PATH.with_suffix(".png")
    if png_path.exists():
        icon.addFile(str(png_path))
    if not icon.isNull():
        return icon
    return QIcon(str(ICON_PATH)) if ICON_PATH.exists() else QIcon()


def run_tray_recovery_action(action):
    action()
    refresh_control_panel()



def create_tray_icon(app, app_icon):
    tray_icon = app_icon if not app_icon.isNull() else app.style().standardIcon(QStyle.SP_ComputerIcon)
    tray = QSystemTrayIcon(tray_icon, app)
    tray.setToolTip(APP_DISPLAY_NAME)

    menu = style_menu(QMenu())
    show_action = QAction("打开控制台", menu)
    show_overlays_action = QAction("显示所有桌宠", menu)
    disable_click_action = QAction("取消所有点击穿透", menu)
    center_action = QAction("所有桌宠移到屏幕中央", menu)
    whip_action = QAction("抽鞭子", menu)
    feather_action = QAction("小羽毛", menu)
    update_action = QAction("检查更新", menu)
    website_action = QAction("打开官网", menu)
    exit_action = QAction("退出", menu)
    show_action.triggered.connect(show_control_panel)
    show_overlays_action.triggered.connect(lambda: run_tray_recovery_action(show_all_overlays))
    disable_click_action.triggered.connect(lambda: run_tray_recovery_action(disable_click_through_for_all))
    center_action.triggered.connect(lambda: run_tray_recovery_action(bring_all_overlays_to_center))
    whip_action.triggered.connect(lambda: show_whip_tool(state.CONTROL_PANEL))
    feather_action.triggered.connect(lambda: show_feather_tool(state.CONTROL_PANEL))
    update_action.triggered.connect(lambda: check_for_updates(state.CONTROL_PANEL))
    website_action.triggered.connect(lambda: open_official_site(state.CONTROL_PANEL))
    exit_action.triggered.connect(exit_app)
    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(show_overlays_action)
    menu.addAction(disable_click_action)
    menu.addAction(center_action)
    menu.addAction(whip_action)
    menu.addAction(feather_action)
    menu.addSeparator()
    menu.addAction(update_action)
    menu.addAction(website_action)
    menu.addSeparator()
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.menu = menu
    tray.activated.connect(lambda reason: show_control_panel() if reason == QSystemTrayIcon.DoubleClick else None)
    tray.show()
    return tray


def wake_existing_instance():
    """当检测到已存在实例时，寻找该实例的窗口并将其唤醒并置于最前。"""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        hwnd = user32.FindWindowW(None, f"{APP_DISPLAY_NAME} Cockpit")
        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
            user32.SetForegroundWindow(hwnd)
            log_info("Activated existing instance window: %s", hwnd)
            return True
    except Exception as exc:
        log_info("Failed to activate existing instance: %s", exc)
    return False


def kill_stale_instance_if_needed():
    """检查 PID 文件，若之前进程为无窗口孤儿僵尸进程，则终止之以解除互斥锁死锁"""
    from .constants import BASE_DIR
    import os
    pid_file = BASE_DIR / ".window_pet.pid"
    if not pid_file.exists():
        return False
    try:
        pid_str = pid_file.read_text(encoding="utf-8").strip()
        if not pid_str.isdigit():
            return False
        stale_pid = int(pid_str)
        if stale_pid == os.getpid():
            return False
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        PROCESS_TERMINATE = 0x0001
        h_proc = kernel32.OpenProcess(PROCESS_TERMINATE, False, stale_pid)
        if h_proc:
            kernel32.TerminateProcess(h_proc, 1)
            kernel32.CloseHandle(h_proc)
            log_info("Terminated stale background process %s", stale_pid)
            import time
            time.sleep(0.5)
            pid_file.unlink(missing_ok=True)
            return True
    except Exception as exc:
        log_info("kill_stale_instance error: %s", exc)
    return False


def cleanup_zombie_instances():
    """清理属于当前工作目录的无窗口僵死 Python / Window Pet 进程"""
    if sys.platform != "win32":
        return False
    import os
    my_pid = os.getpid()
    script_dir = str(Path(__file__).resolve().parent.parent).lower()
    terminated_any = False

    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == my_pid:
                    continue
                cmdline = proc.info.get('cmdline') or []
                cmd_str = " ".join(str(c) for c in cmdline).lower()
                name = (proc.info.get('name') or "").lower()
                if ("python" in name or "window pet" in name) and (script_dir in cmd_str or "windowpet" in cmd_str):
                    proc.terminate()
                    terminated_any = True
                    log_info("Terminated zombie process %s (%s)", proc.info['pid'], name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as exc:
        log_info("cleanup_zombie_instances error: %s", exc)

    return terminated_any


def record_pid():
    import os
    from .constants import BASE_DIR
    pid_file = BASE_DIR / ".window_pet.pid"
    try:
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass


def remove_pid():
    from .constants import BASE_DIR
    pid_file = BASE_DIR / ".window_pet.pid"
    try:
        pid_file.unlink(missing_ok=True)
    except Exception:
        pass


def acquire_single_instance():
    if sys.platform != "win32":
        return True

    try:
        import ctypes

        global _SINGLE_INSTANCE_MUTEX
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.CreateMutexW(None, False, "Local\\WindowPetSingleInstance")
        if not handle:
            return True
        _SINGLE_INSTANCE_MUTEX = handle
        return ctypes.get_last_error() != 183
    except Exception as exc:
        log_info("Single instance guard skipped: %s", exc)
        return True


def startup_configs(configs):
    for item in reversed(list(configs or [])):
        if isinstance(item, (str, dict)):
            return [item]
    return []


PET_NAME_MAP = {
    "jiyi": ("JiyiPet", "吉伊"),
    "nuonuo": ("NuonuoPet", "糯糯 Dora"),
    "dora": ("NuonuoPet", "糯糯 Dora"),
    "fox": ("HuhuPet", "小狐狸"),
    "huhu": ("HuhuPet", "小狐狸"),
    "huhu2": ("Huhu2Pet", "赤狐烈焰"),
    "xiaoba": ("XiaobaPet", "小八猫"),
    "usagi": ("UsagiPet", "乌萨奇兔兔"),
    "xiaochai": ("XiaochaiPet", "小柴犬"),
    "lulu": ("LuluCapybaraPet", "卡皮巴拉 水豚"),
    "capybara": ("LuluCapybaraPet", "卡皮巴拉 水豚"),
    "bear": ("BearPet", "抱抱小熊"),
    "bubu": ("BubuPet", "布布鼠"),
    "buya": ("BuyaPet", "不鸭"),
    "salary-cat": ("SalaryCatPet", "打工猫"),
    "salary_cat": ("SalaryCatPet", "打工猫"),
    "kun-like": ("KunLikePet", "小中分"),
    "kun_like": ("KunLikePet", "小中分"),
    "popo": ("PopoPet", "啵啵 Popo"),
    "logo-guinea-pig": ("LogoGuineaPigPet", "豚鼠小鼻嘎"),
    "logo_guinea_pig": ("LogoGuineaPigPet", "豚鼠小鼻嘎"),
    "mianmian": ("MianmianPet", "绵绵羊"),
    "panda": ("PandaPet", "功夫大熊猫"),
    "penguin-sister": ("PenguinSisterPet", "企鹅妹妹"),
    "penguin_sister": ("PenguinSisterPet", "企鹅妹妹"),
    "kukukaka": ("KumikoPet", "库库咔咔"),
    "kumiko": ("KumikoPet", "库库咔咔"),
    "xiaoba-turn": ("XiaobaTurnPet", "家宠·麦脆角 (摇头猫)"),
    "xiaoba_turn": ("XiaobaTurnPet", "家宠·麦脆角 (摇头猫)"),
    "maicuijiao": ("XiaobaTurnPet", "家宠·麦脆角 (摇头猫)"),
    "nezuko": ("NezukoPet", "祢豆子"),
    "xiaowang": ("XiaoWangPet", "小汪"),
    "redwolf": ("RedWolfPet", "曼波红狼"),
    "beecat": ("BeeCatPet", "哈基蜂"),
    "hajibee": ("BeeCatPet", "哈基蜂"),
    "weichong": ("WeiChongPet", "威虫"),
}


def register_windowpet_protocol():
    """在当前用户的 Windows 注册表中注册 windowpet:// 自定义 URL 协议（无需管理员权限）"""
    if sys.platform != "win32":
        return
    try:
        import winreg

        if getattr(sys, "frozen", False):
            exe_cmd = f'"{sys.executable}" "%1"'
        else:
            python_exe = sys.executable
            main_script = Path(__file__).resolve().parent.parent / "main.py"
            if not main_script.exists():
                main_script = Path(__file__).resolve().parent / "__main__.py"
            exe_cmd = f'"{python_exe}" "{main_script}" "%1"'

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\windowpet") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:WindowPet Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, exe_cmd)
        log_info("Registered windowpet:// protocol handler")
    except Exception as exc:
        log_info("Failed to register windowpet:// protocol: %s", exc)


def parse_windowpet_url(url_str):
    import urllib.parse

    try:
        parsed = urllib.parse.urlparse(url_str)
        if parsed.scheme.lower() != "windowpet":
            return None
        query = urllib.parse.parse_qs(parsed.query)
        action = parsed.netloc or parsed.path.strip("/")
        pet = query.get("pet", [None])[0]
        code = query.get("code", [None])[0]
        name = query.get("name", [None])[0]
        return {"action": action, "pet": pet, "code": code, "name": name}
    except Exception as exc:
        log_info("parse_windowpet_url error: %s", exc)
        return None


def handle_deep_link_import(pet_key, display_name=None):
    folder, default_name = PET_NAME_MAP.get(str(pet_key).lower(), (None, None))
    if not folder:
        folder = str(pet_key)
        default_name = str(pet_key)
    name = display_name or default_name

    target_path = state.ASSETS_DIR / folder
    if not target_path.exists():
        cand = Path(__file__).resolve().parent.parent / "assets" / folder
        if cand.exists():
            target_path = cand

    if target_path.exists():
        add_window(target_path)
        refresh_control_panel()
        if state.CONTROL_PANEL:
            state.CONTROL_PANEL.show()
            state.CONTROL_PANEL.raise_()
            state.CONTROL_PANEL.activateWindow()
        log_info("Deep link imported pet: %s -> %s", pet_key, target_path)
        return True
    return False


def send_command_to_existing_instance(cmd_str):
    from .constants import BASE_DIR

    try:
        cmd_file = BASE_DIR / ".windowpet_cmd"
        cmd_file.write_text(cmd_str.strip(), encoding="utf-8")
        log_info("Sent command to running instance: %s", cmd_str)
    except Exception as exc:
        log_info("send_command_to_existing_instance error: %s", exc)


def check_pending_deep_link_commands():
    from .constants import BASE_DIR

    cmd_file = BASE_DIR / ".windowpet_cmd"
    if not cmd_file.exists():
        return
    try:
        cmd_text = cmd_file.read_text(encoding="utf-8").strip()
        cmd_file.unlink(missing_ok=True)
        if cmd_text.startswith("windowpet:"):
            info = parse_windowpet_url(cmd_text)
            if info and info.get("pet"):
                handle_deep_link_import(info["pet"], info.get("name"))
    except Exception as exc:
        log_info("check_pending_deep_link_commands error: %s", exc)


def main():
    configure_logging()
    apply_non_native_dialogs()
    register_windowpet_protocol()

    deep_link_arg = None
    for arg in sys.argv[1:]:
        if arg.startswith("windowpet:"):
            deep_link_arg = arg
            break

    if not acquire_single_instance():
        if deep_link_arg:
            send_command_to_existing_instance(deep_link_arg)
            wake_existing_instance()
            log_info("Deep link sent to running instance; exiting protocol caller")
            return
        if wake_existing_instance():
            log_info("%s already running; activated existing instance", APP_DISPLAY_NAME)
            return

        # 若未找到前台窗口，清理孤儿/僵死后台进程以解除互斥锁占用
        stale_killed = kill_stale_instance_if_needed()
        zombie_killed = cleanup_zombie_instances()
        if stale_killed or zombie_killed:
            import time
            time.sleep(0.4)

        if not acquire_single_instance():
            log_info("%s already running; notifying user", APP_DISPLAY_NAME)
            if sys.platform == "win32":
                try:
                    import ctypes
                    MB_ICONINFORMATION = 0x40
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        "Window Pet 已经在后台运行中！\n\n请查看屏幕右下角任务栏的系统托盘图标（可点击“^”箭头展开折叠托盘），双击托盘图标即可打开控制台，或者在桌宠身上右键进行设置。",
                        "Window Pet 正在运行",
                        MB_ICONINFORMATION
                    )
                except Exception:
                    pass
            return

    record_pid()
    log_info("%s startup", APP_DISPLAY_NAME)
    ensure_ai_authoring_guide()
    configs = load_config()
    seed_default_assets_dir()
    state.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if DEFAULT_GIF.exists():
        import_gif_to_assets(DEFAULT_GIF, reuse_existing=True)

    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WindowPet.DesktopPet.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    apply_light_palette(app)
    app.setStyleSheet(DARK_STYLE)
    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    app.aboutToQuit.connect(save_config)
    app.aboutToQuit.connect(remove_pid)

    command_timer = QTimer(app)
    command_timer.timeout.connect(check_pending_deep_link_commands)
    command_timer.start(800)

    state.MEDAL_STORE = MedalStore()
    state.MEDAL_STORE.record_launch()

    state.CONTROL_PANEL = ControlPanel(app_icon)
    state.CONTROL_PANEL.show()
    state.CONTROL_PANEL.raise_()
    state.CONTROL_PANEL.activateWindow()
    state.CONTROL_PANEL.tray_icon = create_tray_icon(app, app_icon)
    state.TRAY_ICON = state.CONTROL_PANEL.tray_icon

    if deep_link_arg:
        info = parse_windowpet_url(deep_link_arg)
        if info and info.get("pet"):
            handle_deep_link_import(info["pet"], info.get("name"))
    elif len(sys.argv) > 1:
        paths = [Path(arg) for arg in sys.argv[1:]]
        for path in paths:
            if path.exists():
                add_window(path)
    else:
        for item in startup_configs(configs):
            if isinstance(item, str):
                path = resolved_path(item)
                config = {}
            elif isinstance(item, dict):
                path = resolved_path(item.get("path") or item.get("gif_path") or item.get("asset_path") or "")
                config = item
            else:
                continue
            if path.exists():
                add_window(path, config, save=False)
            else:
                config_warning(f"Saved asset missing, skipped: {path}")

        if not state.WINDOWS:
            assets = assets_for_pack(state.ASSETS_DIR)
            if assets:
                add_window(assets[0].path)

    refresh_control_panel()
    state.INTERACTION_CONTROLLER = PetInteractionController(app)
    state.INTERACTION_CONTROLLER.start()
    exit_code = app.exec()
    log_info("%s shutdown", APP_DISPLAY_NAME)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

