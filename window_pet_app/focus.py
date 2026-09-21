FOCUS_MODE_CUSTOM = "custom"
FOCUS_MODE_FOCUS = "focus"
FOCUS_MODE_BREAK = "break"
FOCUS_MODES = {FOCUS_MODE_CUSTOM, FOCUS_MODE_FOCUS, FOCUS_MODE_BREAK}


def normalize_focus_mode(value):
    mode = str(value or FOCUS_MODE_CUSTOM).strip().lower()
    return mode if mode in FOCUS_MODES else FOCUS_MODE_CUSTOM


def timer_prefix(mode):
    mode = normalize_focus_mode(mode)
    if mode == FOCUS_MODE_FOCUS:
        return "专注"
    if mode == FOCUS_MODE_BREAK:
        return "休息"
    return "计时"


def timer_done_text(mode, focus_sessions_completed=0):
    mode = normalize_focus_mode(mode)
    if mode == FOCUS_MODE_FOCUS:
        return f"专注完成 x{max(0, int(focus_sessions_completed))}"
    if mode == FOCUS_MODE_BREAK:
        return "休息完成"
    return "时间到!"


def completion_message(mode, focus_sessions_completed=0):
    mode = normalize_focus_mode(mode)
    if mode == FOCUS_MODE_FOCUS:
        return f"完成第 {max(0, int(focus_sessions_completed))} 次专注"
    if mode == FOCUS_MODE_BREAK:
        return "休息结束，可以继续专注了"
    return "计时结束"


def should_count_focus_session(mode):
    return normalize_focus_mode(mode) == FOCUS_MODE_FOCUS
