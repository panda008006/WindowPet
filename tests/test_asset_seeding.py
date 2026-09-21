from pathlib import Path

from window_pet_app import assets as assets_module
from window_pet_app import state


def test_seed_repairs_partial_assets_without_overwriting_existing_or_custom_roles(
    monkeypatch,
    tmp_path,
):
    bundled = tmp_path / "bundled-assets"
    runtime = tmp_path / "runtime-assets"

    (bundled / "BuiltInOne").mkdir(parents=True)
    (bundled / "BuiltInOne" / "asset.json").write_text("bundled-one", encoding="utf-8")
    (bundled / "BuiltInOne" / "missing-frame.png").write_bytes(b"missing-frame")
    (bundled / "BuiltInTwo").mkdir(parents=True)
    (bundled / "BuiltInTwo" / "asset.json").write_text("bundled-two", encoding="utf-8")

    (runtime / "BuiltInOne").mkdir(parents=True)
    (runtime / "BuiltInOne" / "asset.json").write_text(
        "user-preserved-version",
        encoding="utf-8",
    )
    (runtime / "CustomRole").mkdir(parents=True)
    (runtime / "CustomRole" / "asset.json").write_text("custom-role", encoding="utf-8")

    monkeypatch.setattr(assets_module, "BUNDLED_ASSETS_DIR", bundled)
    monkeypatch.setattr(assets_module, "DEFAULT_ASSETS_DIR", runtime)
    monkeypatch.setattr(state, "ASSETS_DIR", runtime)

    assets_module.seed_default_assets_dir()

    assert (runtime / "BuiltInOne" / "asset.json").read_text(encoding="utf-8") == (
        "user-preserved-version"
    )
    assert (runtime / "BuiltInOne" / "missing-frame.png").read_bytes() == b"missing-frame"
    assert (runtime / "BuiltInTwo" / "asset.json").read_text(encoding="utf-8") == "bundled-two"
    assert (runtime / "CustomRole" / "asset.json").read_text(encoding="utf-8") == "custom-role"


def test_interrupted_seed_does_not_leave_a_partial_file_that_blocks_repair(
    monkeypatch,
    tmp_path,
):
    bundled = tmp_path / "bundled-assets"
    runtime = tmp_path / "runtime-assets"
    source_file = bundled / "BuiltIn" / "frame.png"
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(b"complete-frame")

    monkeypatch.setattr(assets_module, "BUNDLED_ASSETS_DIR", bundled)
    monkeypatch.setattr(assets_module, "DEFAULT_ASSETS_DIR", runtime)
    monkeypatch.setattr(state, "ASSETS_DIR", runtime)

    def interrupted_copy(_source, destination):
        Path(destination).write_bytes(b"partial")
        raise OSError("simulated interruption")

    monkeypatch.setattr(assets_module.shutil, "copy2", interrupted_copy)

    assets_module.seed_default_assets_dir()

    assert not (runtime / "BuiltIn" / "frame.png").exists()
    assert not list(runtime.rglob("*.seed-*.tmp"))
