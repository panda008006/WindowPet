from window_pet_app.behavior_packs import (
    SCREEN_SAVER_ENTER,
    SCREEN_SAVER_EXIT,
    STARTUP,
    behavior_pack_mapping,
    resolve_behavior_action,
)


def test_default_behavior_pack_mapping_is_available():
    mapping = behavior_pack_mapping({})

    assert mapping[SCREEN_SAVER_ENTER] == "screensaver-sleep"
    assert mapping[SCREEN_SAVER_EXIT] == "wake-stretch"
    assert mapping[STARTUP] == "wake-stretch"


def test_screensaver_sleep_prefers_real_sleep_animation():
    metadata = {"animations": {"idle": {}, "waiting": {}, "sleep": {}}}

    action = resolve_behavior_action(metadata, SCREEN_SAVER_ENTER, metadata["animations"].keys())

    assert action.animation_name == "sleep"
    assert action.loop is True
    assert action.return_to_idle is False


def test_screensaver_sleep_falls_back_to_waiting():
    metadata = {"animations": {"idle": {}, "waiting": {}}}

    action = resolve_behavior_action(metadata, SCREEN_SAVER_ENTER, metadata["animations"].keys())

    assert action.animation_name == "waiting"
    assert action.loop is True


def test_wake_stretch_prefers_stretch_and_returns_to_idle():
    metadata = {"animations": {"idle": {}, "waving": {}, "stretch": {}}}

    action = resolve_behavior_action(metadata, STARTUP, metadata["animations"].keys())

    assert action.animation_name == "stretch"
    assert action.loop is False
    assert action.return_to_idle is True


def test_behavior_pack_can_be_disabled_per_event():
    metadata = {
        "animations": {"idle": {}, "sleep": {}},
        "behavior_packs": {SCREEN_SAVER_ENTER: ""},
    }

    assert resolve_behavior_action(metadata, SCREEN_SAVER_ENTER, metadata["animations"].keys()) is None
