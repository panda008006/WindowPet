from window_pet_app.assets import detect_asset
from window_pet_app.package_registry import (
    normalize_package_code,
    package_code_for_folder,
    package_code_for_id,
    package_for_code,
)


def test_four_digit_package_codes_are_stable_and_zero_padded():
    assert normalize_package_code("6") == "0006"
    assert normalize_package_code("0006") == "0006"
    assert normalize_package_code("pet-6") == ""
    assert package_code_for_folder("JiyiPet") == "0006"
    assert package_code_for_id("huhu") == "0005"
    assert package_for_code("21")["package_id"] == "dora"


def test_detected_asset_receives_package_code_from_folder_registry():
    asset = detect_asset("assets/JiyiPet")
    assert asset is not None
    assert asset.metadata["package_code"] == "0006"
