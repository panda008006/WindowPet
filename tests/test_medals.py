from datetime import date, timedelta

from window_pet_app.medals import MedalStore, REQUIRED_MEDAL_TRIGGERS


def test_launch_records_static_idle_once_per_day(tmp_path):
    store = MedalStore(tmp_path / "medals.json", today=date(2026, 7, 20))

    store.record_launch()
    store.record_launch()

    assert store.data["active_days"] == ["2026-07-20"]
    assert store.data["triggers"] == ["static-idle"]
    assert (tmp_path / "medals.json").is_file()


def test_three_responses_unlock_only_after_all_basic_states(tmp_path):
    store = MedalStore(tmp_path / "medals.json", today=date(2026, 7, 20))
    store.record_launch()
    for trigger in REQUIRED_MEDAL_TRIGGERS - {"static-idle", "left-click"}:
        store.record_trigger(trigger)

    before = {item["id"]: item for item in store.snapshot()}
    assert before["three-responses"]["unlocked"] is False

    store.record_trigger("left-click")

    after = {item["id"]: item for item in store.snapshot()}
    assert after["three-responses"]["unlocked"] is True


def test_companion_day_and_pet_milestones_are_natural_and_persistent(tmp_path):
    path = tmp_path / "medals.json"
    start = date(2026, 7, 20)
    for offset in range(7):
        MedalStore(path, today=start + timedelta(days=offset)).record_launch()

    store = MedalStore(path, today=start + timedelta(days=7))
    for pet_id in ("jiyi", "dora", "fox"):
        store.record_pet(pet_id)

    medals = {item["id"]: item for item in store.snapshot()}
    assert medals["three-days"]["unlocked"] is True
    assert medals["one-week"]["unlocked"] is True
    assert medals["pet-collector"]["unlocked"] is True
    assert medals["one-week"]["status"] == "已解锁"


def test_hidden_preference_survives_restart(tmp_path):
    path = tmp_path / "medals.json"
    store = MedalStore(path)
    store.set_hidden(True)

    assert MedalStore(path).hidden is True


def test_unknown_trigger_does_not_pollute_progress(tmp_path):
    store = MedalStore(tmp_path / "medals.json")

    assert store.record_trigger("wheel-long-press") is False
    assert store.data["triggers"] == []


def test_corrupt_state_recovers_without_crashing(tmp_path):
    path = tmp_path / "medals.json"
    path.write_text("not-json", encoding="utf-8")

    store = MedalStore(path)

    assert store.data["active_days"] == []
    assert store.snapshot()[0]["title"] == "第一次回应"
