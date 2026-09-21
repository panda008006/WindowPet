import json
from pathlib import Path

from window_pet_app import state
from window_pet_app.assets import asset_packs, assets_for_pack


def test_tool_assets_are_not_shown_as_pet_library_items():
    state.ASSETS_DIR = Path("assets").resolve()

    pack_names = {name for name, _path in asset_packs()}
    root_assets = assets_for_pack(state.ASSETS_DIR)

    assert "ToolAssets" not in pack_names
    assert all("ToolAssets" not in str(asset.path) for asset in root_assets)
    assert all("feather" not in asset.name.lower() for asset in root_assets)


def test_standing_fox_is_named_huhu():
    metadata = json.loads((Path("assets") / "Huhu2Pet" / "asset.json").read_text(encoding="utf-8"))
    other_fox_metadata = json.loads((Path("assets") / "HuhuPet" / "asset.json").read_text(encoding="utf-8"))

    assert metadata["name"] == "呼呼"
    assert other_fox_metadata["name"] == "小狐"

