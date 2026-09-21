import zipfile
from pathlib import Path

import pytest

from window_pet_app.updater import extracted_package_root, fetch_json, is_newer_version, safe_extract_zip


def test_fetch_json_accepts_utf8_bom(tmp_path):
    manifest = tmp_path / "latest.json"
    manifest.write_bytes(b'\xef\xbb\xbf{"version":"1.0.27"}')

    assert fetch_json(manifest.as_uri()) == {"version": "1.0.27"}


def test_version_comparison_detects_newer_release():
    assert is_newer_version("1.0.1", "1.0.0")
    assert not is_newer_version("1.0.0", "1.0.0")
    assert not is_newer_version("1.0.0", "1.0.1")


def test_extracted_package_root_accepts_flat_or_folder_package(tmp_path):
    flat = tmp_path / "flat"
    flat.mkdir()
    (flat / "Window Pet.exe").write_text("", encoding="utf-8")
    assert extracted_package_root(flat) == flat

    nested_parent = tmp_path / "nested"
    nested = nested_parent / "Window Pet_中文版"
    nested.mkdir(parents=True)
    (nested / "Window Pet.exe").write_text("", encoding="utf-8")
    assert extracted_package_root(nested_parent) == nested


def test_safe_extract_rejects_zip_slip_paths(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("../bad.txt", "bad")

    with pytest.raises(ValueError):
        safe_extract_zip(archive, tmp_path / "out")
