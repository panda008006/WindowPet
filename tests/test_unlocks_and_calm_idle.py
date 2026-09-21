from dataclasses import dataclass
from pathlib import Path

from window_pet_app import state
from window_pet_app import assets as assets_module
from window_pet_app.assets import (
    UNLOCK_RULE_VERSION,
    ensure_pet_unlock_state,
    invite_code_for_identity,
    is_asset_unlocked,
    normalize_pet_unlocks,
)
from window_pet_app.interactions import PetInteractionController
from window_pet_app.overlay import OverlayWindow


@dataclass
class FakeAsset:
    index: int

    @property
    def id(self):
        return f"assets/FakePet{self.index}"

    @property
    def name(self):
        return f"Fake {self.index}"

    @property
    def metadata(self):
        return {"character_id": f"fake-{self.index}"}

    @property
    def path(self):
        return Path(self.id)


def fake_assets(count):
    return [FakeAsset(index) for index in range(count)]


def test_current_rule_unlocks_all_pets(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    state.PET_UNLOCKS = None

    pets = fake_assets(12)
    unlock_state = ensure_pet_unlock_state(pets)
    state.PET_UNLOCKS = unlock_state

    assert unlock_state["unlock_rule_version"] == UNLOCK_RULE_VERSION
    assert unlock_state["all_unlocked"] is True
    assert len(unlock_state["unlocked_asset_ids"]) == len(pets)
    assert is_asset_unlocked(pets[0], pets) is True
    assert is_asset_unlocked(pets[-1], pets) is True


def test_login_does_not_change_always_unlocked_rule(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    state.PET_UNLOCKS = None

    pets = fake_assets(12)
    unlock_state = ensure_pet_unlock_state(pets, grant_login_pets=True)

    assert unlock_state["egg_chances"] == 0
    assert unlock_state["all_unlocked"] is True
    assert len(unlock_state["unlocked_asset_ids"]) == len(pets)


def test_always_unlocked_state_survives_normalization_and_reload(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    state.PET_UNLOCKS = None

    pets = fake_assets(12)
    unlock_state = ensure_pet_unlock_state(pets, grant_login_pets=True)
    state.PET_UNLOCKS = normalize_pet_unlocks(unlock_state)
    reloaded = ensure_pet_unlock_state(pets)

    assert reloaded["egg_chances"] == 0
    assert reloaded["all_unlocked"] is True
    assert len(reloaded["unlocked_asset_ids"]) == len(pets)


def test_invite_code_is_stable_for_same_account():
    assert invite_code_for_identity("User@example.com") == invite_code_for_identity(" user@EXAMPLE.com ")
    assert invite_code_for_identity("User@example.com").startswith("WP-")


def test_all_pets_prefer_static_idle():
    assert OverlayWindow.prefers_calm_static_idle(object()) is True


def test_interaction_controller_starts_easter_egg_timer():
    controller = type("Controller", (), {})()
    calls = []
    controller.timer = type("Timer", (), {"start": lambda _self: calls.append("start"), "stop": lambda _self: calls.append("stop")})()

    PetInteractionController.start(controller)

    assert calls == ["start"]
