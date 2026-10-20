import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from . import state
from .assets import assets_for_pack, config_warning, import_gif_to_assets, load_config, resolved_path, save_config, seed_default_assets_dir
from .character_acquisition import ensure_ai_authoring_guide
from .constants import APP_DISPLAY_NAME, BASE_DIR, DARK_STYLE, DEFAULT_GIF, ICON_PATH, resource_path
from .control_panel import ControlPanel
from .logging_utils import configure_logging, log_info, log_warning, log_error
from .medals import MedalStore
from .interactions import PetInteractionController
from .overlay import add_window, exit_app, refresh_control_panel
from .recovery import bring_all_overlays_to_center, disable_click_through_for_all, show_all_overlays
from .style_utils import apply_light_palette, apply_non_native_dialogs, style_menu
from .updater import check_for_updates, check_for_updates_async, open_official_site
from .assets import auto_update_check_enabled

_SINGLE_INSTANCE_MUTEX = None


def show_control_panel():
    if state.CONTROL_PANEL is not None:
        state.CONTROL_PANEL.show()
        state.CONTROL_PANEL.showNormal()
        state.CONTROL_PANEL.raise_()
        state.CONTROL_PANEL.activateWindow()


def load_app_icon():
    candidates = [
        BASE_DIR / "icon.ico",
        resource_path("icon.ico"),
        ICON_PATH,
        BASE_DIR / "icon.png",
        resource_path("icon.png"),
        BASE_DIR / "icon-256.png",
        resource_path("icon-256.png"),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            icon = QIcon(str(candidate.resolve()))
            if not icon.isNull():
                return icon
    return QIcon()


def run_tray_recovery_action(action):
    action()
    refresh_control_panel()



def create_tray_icon(app, app_icon):
    if app_icon is None or app_icon.isNull():
        app_icon = load_app_icon()
    tray_icon = app_icon if (app_icon and not app_icon.isNull()) else app.style().standardIcon(QStyle.SP_ComputerIcon)
    tray = QSystemTrayIcon(tray_icon, app)
    tray.setToolTip(APP_DISPLAY_NAME)

    menu = style_menu(QMenu())
    show_action = QAction("打开控制台", menu)
    show_overlays_action = QAction("显示所有桌宠", menu)
    disable_click_action = QAction("取消所有点击穿透", menu)
    center_action = QAction("所有桌宠移到屏幕中央", menu)
    update_action = QAction("检查更新", menu)
    website_action = QAction("打开官网", menu)
    exit_action = QAction("退出", menu)
    show_action.triggered.connect(show_control_panel)
    show_overlays_action.triggered.connect(lambda: run_tray_recovery_action(show_all_overlays))
    disable_click_action.triggered.connect(lambda: run_tray_recovery_action(disable_click_through_for_all))
    center_action.triggered.connect(lambda: run_tray_recovery_action(bring_all_overlays_to_center))
    update_action.triggered.connect(lambda: check_for_updates(state.CONTROL_PANEL))
    website_action.triggered.connect(lambda: open_official_site(state.CONTROL_PANEL))
    exit_action.triggered.connect(exit_app)
    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(show_overlays_action)
    menu.addAction(disable_click_action)
    menu.addAction(center_action)
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
        if not hwnd:
            found = []

            def enum_proc(h, extra):
                length = user32.GetWindowTextLengthW(h)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(h, buf, length + 1)
                    title = buf.value
                    if "Window Pet" in title or "WindowPet" in title:
                        found.append(h)
                return True

            from ctypes import wintypes
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
            user32.EnumWindows.restype = wintypes.BOOL
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
            if found:
                hwnd = found[0]

        if hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
            user32.SetForegroundWindow(hwnd)
            log_info("Activated existing instance window: %s", hwnd)
            return True
    except Exception as exc:
        log_info("Failed to activate existing instance: %s", exc)
    return False


def is_recently_started(max_age_sec=8.0):
    """检查 PID 文件，判断是否有进程在最近 max_age_sec 秒内刚刚启动"""
    from .constants import BASE_DIR
    import time
    pid_file = BASE_DIR / ".window_pet.pid"
    if not pid_file.exists():
        return False
    try:
        content = pid_file.read_text(encoding="utf-8").strip()
        if ":" in content:
            pid_str, ts_str = content.split(":", 1)
            ts = float(ts_str)
            if (time.time() - ts) < max_age_sec:
                import psutil
                if psutil.pid_exists(int(pid_str)):
                    return True
    except Exception:
        pass
    return False


def kill_stale_instance_if_needed():
    """检查 PID 文件，若之前进程为无窗口孤儿僵尸进程（且启动已超过8秒），终止之以解除互斥锁死锁"""
    from .constants import BASE_DIR
    import os
    import time
    pid_file = BASE_DIR / ".window_pet.pid"
    if not pid_file.exists():
        return False
    try:
        content = pid_file.read_text(encoding="utf-8").strip()
        stale_pid = None
        start_time = 0.0
        if ":" in content:
            pid_str, ts_str = content.split(":", 1)
            if pid_str.isdigit():
                stale_pid = int(pid_str)
                start_time = float(ts_str)
        elif content.isdigit():
            stale_pid = int(content)

        if not stale_pid or stale_pid == os.getpid():
            return False

        # 若进程启动时间在 8 秒以内，属于正在启动的新进程，绝不误杀！
        if start_time > 0 and (time.time() - start_time) < 8.0:
            log_info("Instance PID %s was started recently (%.1fs ago); skipping kill", stale_pid, time.time() - start_time)
            return False

        import psutil
        if not psutil.pid_exists(stale_pid):
            pid_file.unlink(missing_ok=True)
            return False

        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        PROCESS_TERMINATE = 0x0001
        h_proc = kernel32.OpenProcess(PROCESS_TERMINATE, False, stale_pid)
        if h_proc:
            kernel32.TerminateProcess(h_proc, 1)
            kernel32.CloseHandle(h_proc)
            log_info("Terminated truly stale background process %s", stale_pid)
            time.sleep(0.3)
            pid_file.unlink(missing_ok=True)
            return True
    except Exception as exc:
        log_info("kill_stale_instance error: %s", exc)
    return False


def cleanup_zombie_instances():
    """清理属于当前工作目录的无窗口僵死 Python / Window Pet 进程（不杀死启动8秒内的进程）"""
    if sys.platform != "win32":
        return False
    import os
    import time
    my_pid = os.getpid()
    script_dir = str(Path(__file__).resolve().parent.parent).lower()
    terminated_any = False

    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['pid'] == my_pid:
                    continue
                create_time = proc.info.get('create_time') or 0
                if create_time > 0 and (time.time() - create_time) < 8.0:
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
    import time
    from .constants import BASE_DIR
    pid_file = BASE_DIR / ".window_pet.pid"
    try:
        pid_file.write_text(f"{os.getpid()}:{time.time()}", encoding="utf-8")
    except Exception:
        pass


def remove_pid():
    from .constants import BASE_DIR
    pid_file = BASE_DIR / ".window_pet.pid"
    try:
        pid_file.unlink(missing_ok=True)
    except Exception:
        pass


def release_single_instance():
    global _SINGLE_INSTANCE_MUTEX
    if _SINGLE_INSTANCE_MUTEX is not None and sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle(_SINGLE_INSTANCE_MUTEX)
        except Exception:
            pass
        _SINGLE_INSTANCE_MUTEX = None


def acquire_single_instance():
    if sys.platform != "win32":
        return True

    try:
        import ctypes

        global _SINGLE_INSTANCE_MUTEX
        if _SINGLE_INSTANCE_MUTEX is not None:
            return True

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.CreateMutexW(None, True, "Local\\WindowPetSingleInstance")
        if not handle:
            return True
        last_err = ctypes.get_last_error()
        if last_err == 183:  # ERROR_ALREADY_EXISTS
            kernel32.CloseHandle(handle)
            return False
        _SINGLE_INSTANCE_MUTEX = handle
        return True
    except Exception as exc:
        log_info("Single instance guard skipped: %s", exc)
        return True


def startup_configs(configs):
    res = []
    for item in list(configs or []):
        if isinstance(item, (str, dict)):
            res.append(item)
    return res


PET_NAME_MAP = {
    "dafeiyu": ("DaFeiYuPet", "大肥鱼"),
    "feiyu": ("DaFeiYuPet", "大肥鱼"),
    "jiyi": ("JiyiPet", "吉伊"),
    "nuonuo": ("NuonuoPet", "糯糯 Dora"),
    "dora": ("NuonuoPet", "糯糯 Dora"),
    "fox": ("HuhuPet", "小狐狸"),
    "huhu": ("HuhuPet", "小狐狸"),
    "xiaoba": ("XiaobaPet", "小八猫"),
    "usagi": ("UsagiPet", "乌萨奇兔兔"),
    "xiaochai": ("XiaochaiPet", "小柴犬"),
    "lulu": ("LuluCapybaraPet", "卡皮巴拉 水豚"),
    "capybara": ("LuluCapybaraPet", "卡皮巴拉 水豚"),
    "bubu": ("BubuPet", "布布鼠"),
    "salary-cat": ("SalaryCatPet", "打工猫"),
    "salary_cat": ("SalaryCatPet", "打工猫"),
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
    "xiaowang": ("XiaoWangPet", "小汪"),
    "redwolf": ("RedWolfPet", "曼波红狼"),
    "beecat": ("BeeCatPet", "哈基蜂"),
    "hajibee": ("BeeCatPet", "哈基蜂"),
    "boba": ("BobaPet", "Boba"),
    "round-maodie": ("RoundMaodiePet", "圆头耄耋"),
    "round_maodie": ("RoundMaodiePet", "圆头耄耋"),
    "round-maodie-c63864e8": ("RoundMaodiePet", "圆头耄耋"),
    "daodun": ("DaoDunPet", "刀盾"),
    "doubao": ("DoubaoPet", "豆包"),
    "doubao-2": ("DoubaoPet", "豆包"),
    "wangcai": ("WangcaiPet", "旺财"),
    "gangbeng": ("GangbengPet", "钢蹦"),
    "gangbeng-v2": ("GangbengPet", "钢蹦"),
    "bananacat": ("BananaCatPet", "香蕉猫"),
    "banana-cat": ("BananaCatPet", "香蕉猫"),
    "nightleaf": ("NightleafPet", "小黑"),
    "xiaohei": ("NightleafPet", "小黑"),
    "xiao-hei": ("NightleafPet", "小黑"),
    "liangzi": ("LiangziPet", "大胃袋良子"),
    "liangzi-2": ("LiangziPet", "大胃袋良子"),
    "oiiai": ("OiiaiPet", "oiiai"),
    "momonga": ("MomongaPet", "飞鼠"),
    "jaychou": ("JayChouQPet", "Q版周杰伦"),
    "jay-chou-q": ("JayChouQPet", "Q版周杰伦"),
    "saltyclerk": ("SaltyClerkPet", "咸鱼店员"),
    "salty-clerk": ("SaltyClerkPet", "咸鱼店员"),
    "duo": ("DuoPet", "Duo"),
    "chubbygoldencat": ("ChubbyGoldenCatPet", "金渐层胖猫"),
    "chubby-golden-cat": ("ChubbyGoldenCatPet", "金渐层胖猫"),
    "leopardgecko": ("LeopardGeckoPet", "微笑守宫"),
    "leopard-gecko": ("LeopardGeckoPet", "微笑守宫"),
    "munchkincat": ("MunchkinCatPet", "矮脚橘白猫"),
    "munchkin-cat": ("MunchkinCatPet", "矮脚橘白猫"),
    "sugarglider": ("SugarGliderPet", "白化蜜袋鼯"),
    "sugar-glider": ("SugarGliderPet", "白化蜜袋鼯"),
    "westie": ("WestiePet", "西高地白白"),
    "deepseek": ("DaDeepSeekPet", "大DeepSeek"),
    "dadeepseek": ("DaDeepSeekPet", "大DeepSeek"),
    "doubao-ai": ("DoubaoAiPet", "豆包"),
    "doubao-video": ("DoubaoAiPet", "豆包"),
    "zhuzhuxia": ("ZhuZhuXiaPet", "猪猪侠"),
    "tesla": ("TeslaPet", "特斯拉超跑"),
    "teslapet": ("TeslaPet", "特斯拉超跑"),
    "cybertruck": ("TeslaPet", "特斯拉超跑"),
    "ggbond": ("ZhuZhuXiaPet", "猪猪侠"),
    "xiaodeepseek": ("XiaoDeepSeekPet", "小DeepSeek"),
    "claude": ("ClaudePet", "Claude"),
    "codex": ("CodexPet", "Codex (白龙娘)"),
    "glm": ("ZlmPet", "智谱清言"),
    "zlm": ("ZlmPet", "智谱清言"),
    "linchuxue": ("LinChuXuePet", "林初雪"),
    "lin-chu-xue": ("LinChuXuePet", "林初雪"),
    "qianduoduo": ("QianDuoDuoPet", "钱多多"),
    "qian-duo-duo": ("QianDuoDuoPet", "钱多多"),
    "liangsheng": ("LiangShengPet", "梁圣"),
    "liang-sheng": ("LiangShengPet", "梁圣"),
    "doubaoai": ("DoubaoAiPet", "豆包 (视频版)"),
    "jokebear": ("JokeBearPet", "自嘲熊"),
    "huanhuan": ("HuanhuanPet", "欢欢小羊"),
    "linna": ("LinnaPet", "琳娜"),
    "yujiang": ("YuJiangPet", "鱼酱"),
    "kanna": ("KannaPet", "康娜"),
    "duducapybara": ("DuduCapybaraPet", "嘟嘟水豚"),
    "goldencat": ("ChubbyGoldenCatPet", "金渐层胖猫"),
    "gecko": ("LeopardGeckoPet", "微笑守宫"),
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
        status = query.get("state", query.get("status", [None]))[0]
        provider = query.get("ai", query.get("provider", query.get("integration", [None])))[0]
        return {
            "action": action,
            "pet": pet,
            "code": code,
            "name": name,
            "state": status,
            "provider": provider,
        }
    except Exception as exc:
        log_info("parse_windowpet_url error: %s", exc)
        return None


def handle_deep_link_import(pet_key, display_name=None, code=None):
    folder = None
    default_name = None

    # 1. 查询硬编码映射表
    if pet_key:
        folder, default_name = PET_NAME_MAP.get(str(pet_key).strip().lower(), (None, None))

    # 2. 从 package_registry.json 中动态查找
    if not folder:
        try:
            import json
            from .constants import BASE_DIR
            registry_paths = [
                BASE_DIR / "package_registry.json",
                Path(__file__).resolve().parent.parent / "package_registry.json",
                state.ASSETS_DIR.parent / "package_registry.json",
            ]
            for reg_path in registry_paths:
                if reg_path.is_file():
                    with open(reg_path, encoding="utf-8") as f:
                        data = json.load(f)
                    packages = data.get("packages", [])
                    target_key = str(pet_key or "").strip().lower()
                    target_code = str(code or "").strip().lower()
                    for pkg in packages:
                        pkg_id = str(pkg.get("package_id", "")).strip().lower()
                        pkg_folder = pkg.get("folder_name", "")
                        pkg_code = str(pkg.get("code", "")).strip().lower()
                        pkg_name = pkg.get("display_name", "")
                        if (target_key and target_key in (pkg_id, pkg_folder.lower())) or (target_code and target_code == pkg_code):
                            folder = pkg_folder
                            default_name = pkg_name
                            break
                    if folder:
                        break
        except Exception as exc:
            log_info("Failed to lookup package_registry: %s", exc)

    # 3. 动态模糊目录匹配 (忽略大小写、支持自动补齐 Pet 后缀)
    if not folder and pet_key:
        target_name_clean = str(pet_key).lower().replace("-", "").replace("_", "")
        search_roots = [
            state.ASSETS_DIR,
            Path(__file__).resolve().parent.parent / "assets",
        ]
        for s_root in search_roots:
            if s_root.is_dir():
                for sub in s_root.iterdir():
                    if sub.is_dir():
                        sub_clean = sub.name.lower().replace("-", "").replace("_", "")
                        if sub_clean in (target_name_clean, f"{target_name_clean}pet"):
                            folder = sub.name
                            default_name = sub.name
                            break
            if folder:
                break

    if not folder:
        folder = str(pet_key) if pet_key else ""
        default_name = str(pet_key) if pet_key else ""

    if not folder:
        log_info("handle_deep_link_import: could not resolve pet_key '%s', code '%s'", pet_key, code)
        return False

    name = display_name or default_name

    target_path = state.ASSETS_DIR / folder
    # 若在客户端运行目录未找到，尝试从源码库或归档库自动同步安装
    if not target_path.exists():
        repo_asset_cands = [
            Path(__file__).resolve().parent.parent / "assets" / folder,
            Path("assets") / folder,
            Path(__file__).resolve().parent.parent / "00_历史交接归档" / "小角色" / folder.replace("Pet", ""),
        ]
        for cand in repo_asset_cands:
            if cand.is_dir():
                try:
                    import shutil
                    shutil.copytree(cand, target_path, dirs_exist_ok=True)
                    log_info("Auto-installed imported pet from repo: %s -> %s", cand, target_path)
                except Exception as exc:
                    target_path = cand
                break

    if target_path.exists():
        target = state.WINDOWS[0] if state.WINDOWS else None
        if target is not None:
            target.switch_to_asset(target_path)
            target.show()
            target.raise_()
        else:
            add_window(target_path)

        refresh_control_panel()
        if state.CONTROL_PANEL:
            state.CONTROL_PANEL.show()
            state.CONTROL_PANEL.raise_()
            state.CONTROL_PANEL.activateWindow()
            if hasattr(state.CONTROL_PANEL, "select_imported_library_item"):
                state.CONTROL_PANEL.select_imported_library_item(target_path)
        log_info("Deep link imported pet successfully: %s -> %s", pet_key, target_path)
        return True
    else:
        log_info("Deep link target asset directory not found: %s", target_path)
    return False


def handle_deep_link_status(pet_key, status, provider=None):
    """Route a local AI-tool status callback to the selected pet/provider."""
    provider_key = str(provider or "").strip().lower()
    if provider_key:
        from .external_integrations import integration_for

        provider_item = integration_for(provider_key)
        provider_key = provider_item.key if provider_item is not None else provider_key
    for window in list(getattr(state, "WINDOWS", [])):
        character_id = str(getattr(window, "character_id", "") or "").lower()
        if "deepseek" not in character_id and not getattr(window, "supports_external_ai_integration", lambda: False)():
            continue
        if str(pet_key or "dadeepseek").lower() not in {"dadeepseek", "deepseek", character_id}:
            continue
        selected_provider = str(getattr(window, "ai_integration_key", "") or "").lower()
        if provider_key and selected_provider and selected_provider != provider_key:
            continue
        handler = getattr(window, "play_external_integration_status", None)
        if callable(handler) and handler(status):
            log_info("DeepSeek integration status: %s (%s)", status, provider_key or selected_provider or "legacy")
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
        if cmd_text in {"WAKE", "SHOW_DASHBOARD", "SHOW_CONTROL_PANEL", "windowpet://open"}:
            show_control_panel()
            show_all_overlays()
            log_info("Received %s command; restored control panel and overlays", cmd_text)
        elif cmd_text.startswith("windowpet:"):
            info = parse_windowpet_url(cmd_text)
            if info and info.get("action") in {"status", "event"} and info.get("pet"):
                handle_deep_link_status(info["pet"], info.get("state"), info.get("provider"))
            elif info and (info.get("pet") or info.get("code")):
                handle_deep_link_import(info.get("pet"), info.get("name"), info.get("code"))
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

        # 唤醒已存在的实例并打开控制面板与桌宠
        send_command_to_existing_instance("WAKE")
        if wake_existing_instance():
            log_info("%s already running; activated existing instance", APP_DISPLAY_NAME)
            return

        # 若有实例正在 8 秒内启动，属于正常双击并发，静默退出让其正常展示
        if is_recently_started(max_age_sec=8.0):
            log_info("%s is currently starting up, waiting gracefully", APP_DISPLAY_NAME)
            return

        # 若未找到前台窗口且并非刚刚启动，检查是否存在孤儿/僵死后台进程
        stale_killed = kill_stale_instance_if_needed()
        zombie_killed = cleanup_zombie_instances()
        if stale_killed or zombie_killed:
            import time
            time.sleep(0.4)

        if not acquire_single_instance():
            log_info("%s already running; sent wake command to existing instance", APP_DISPLAY_NAME)
            send_command_to_existing_instance("WAKE")
            wake_existing_instance()
            return

    record_pid()
    log_info("%s startup", APP_DISPLAY_NAME)
    try:
        ensure_ai_authoring_guide()
        log_info("Startup: ensure_ai_authoring_guide done")
        configs = load_config()
        log_info("Startup: load_config done (%d entries)", len(configs) if configs else 0)
        seed_default_assets_dir()
        log_info("Startup: seed_default_assets_dir done")
        state.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        if DEFAULT_GIF.exists():
            import_gif_to_assets(DEFAULT_GIF, reuse_existing=True)

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WindowPet.DesktopPet.2.0")
            except Exception:
                pass

        app = QApplication(sys.argv)
        log_info("Startup: QApplication initialized")
        app.setQuitOnLastWindowClosed(False)
        app.setStyle("Fusion")
        apply_light_palette(app)
        app.setStyleSheet(DARK_STYLE)
        app_icon = load_app_icon()
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
        app.aboutToQuit.connect(save_config)
        app.aboutToQuit.connect(remove_pid)
        app.aboutToQuit.connect(release_single_instance)

        command_timer = QTimer(app)
        command_timer.timeout.connect(check_pending_deep_link_commands)
        command_timer.start(250)

        state.MEDAL_STORE = MedalStore()
        state.MEDAL_STORE.record_launch()

        state.CONTROL_PANEL = ControlPanel(app_icon)
        state.CONTROL_PANEL.show()
        state.CONTROL_PANEL.raise_()
        state.CONTROL_PANEL.activateWindow()
        state.CONTROL_PANEL.tray_icon = create_tray_icon(app, app_icon)
        state.TRAY_ICON = state.CONTROL_PANEL.tray_icon
        log_info("Startup: ControlPanel and TrayIcon created")
    except Exception as exc:
        log_warning("Exception during early startup: %s", exc)
        raise

    if deep_link_arg:
        info = parse_windowpet_url(deep_link_arg)
        if info and info.get("action") in {"status", "event"} and info.get("pet"):
            handle_deep_link_status(info["pet"], info.get("state"), info.get("provider"))
        elif info and (info.get("pet") or info.get("code")):
            handle_deep_link_import(info.get("pet"), info.get("name"), info.get("code"))
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
            # 默认打开大DeepSeek与大肥鱼
            for pet_name in ("DaDeepSeekPet", "DaFeiYuPet"):
                pet_path = state.ASSETS_DIR / pet_name
                if pet_path.exists():
                    add_window(pet_path)
            if not state.WINDOWS:
                assets = assets_for_pack(state.ASSETS_DIR)
                if assets:
                    add_window(assets[0].path)

    refresh_control_panel()
    state.INTERACTION_CONTROLLER = PetInteractionController(app)
    state.INTERACTION_CONTROLLER.start()
    if auto_update_check_enabled():
        QTimer.singleShot(4000, lambda: check_for_updates_async(state.CONTROL_PANEL, silent=True))
    exit_code = app.exec()
    log_info("%s shutdown", APP_DISPLAY_NAME)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

