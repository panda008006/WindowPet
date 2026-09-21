from pathlib import Path
from window_pet_app.app import parse_windowpet_url, PET_NAME_MAP, handle_deep_link_import
from window_pet_app import state


def test_parse_windowpet_url():
    url = "windowpet://import?pet=jiyi&code=WPX-2026-JIYI&name=%E5%90%89%E4%BC%8A"
    res = parse_windowpet_url(url)
    assert res is not None
    assert res["action"] == "import"
    assert res["pet"] == "jiyi"
    assert res["code"] == "WPX-2026-JIYI"
    assert res["name"] == "吉伊"


def test_parse_invalid_url():
    assert parse_windowpet_url("http://example.com") is None
    assert parse_windowpet_url("invalid_url") is None


def test_pet_name_map_coverage():
    assert "jiyi" in PET_NAME_MAP
    assert "xiaochai" in PET_NAME_MAP
    assert "lulu" in PET_NAME_MAP
    assert "fox" in PET_NAME_MAP
    assert "maicuijiao" in PET_NAME_MAP
    assert "xiaoba-turn" in PET_NAME_MAP
    folder, name = PET_NAME_MAP["jiyi"]
    assert folder == "JiyiPet"
    assert name == "吉伊"
    cat_folder, cat_name = PET_NAME_MAP["maicuijiao"]
    assert cat_folder == "XiaobaTurnPet"
    assert cat_name == "家宠·麦脆角 (摇头猫)"


def test_handle_deep_link_import_nonexistent():
    # Non-existent pet should return False safely
    assert handle_deep_link_import("non_existent_monster_9999") is False
