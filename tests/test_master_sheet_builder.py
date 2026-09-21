import importlib.util
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = PROJECT_ROOT / "AI角色制作" / "build_character_from_sheet.py"
ACTION_ROWS = [
    "idle",
    "click",
    "drag",
]


def load_builder():
    spec = importlib.util.spec_from_file_location("windowpet_master_sheet_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def make_test_sheet(path):
    image = Image.new("RGB", (600, 300), "white")
    draw = ImageDraw.Draw(image)
    colours = {}
    for row, action in enumerate(ACTION_ROWS):
        for column in range(6):
            colour = (
                20 + row * 25,
                25 + column * 30,
                40 + (row * 19 + column * 11) % 180,
            )
            colours[(action, column)] = colour
            left = column * 100 + 20
            top = row * 100 + 20
            draw.rectangle((left, top, left + 59, top + 69), fill=colour)
    image.save(path)
    return colours


def test_builder_splits_6_by_3_sheet_into_correct_action_rows(tmp_path):
    builder = load_builder()
    sheet = tmp_path / "master.png"
    colours = make_test_sheet(sheet)

    target = builder.build_character_from_sheet(
        sheet=sheet,
        display_name="桃桃",
        character_id="MomoPet",
        assets_root=tmp_path / "assets",
        background="auto",
    )

    assert target == tmp_path / "assets" / "MomoPet"
    assert len(list(target.rglob("*.png"))) == 18
    for row, action in enumerate(ACTION_ROWS):
        paths = (
            sorted(target.glob("MomoPet_*.png"))
            if action == "idle"
            else sorted((target / action).glob("*.png"))
        )
        assert len(paths) == 6
        for column, frame_path in enumerate(paths):
            with Image.open(frame_path) as frame:
                assert frame.mode == "RGBA"
                assert frame.size == (192, 208)
                bbox = frame.getchannel("A").getbbox()
                assert bbox is not None
                centre = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
                actual = frame.getpixel(centre)[:3]
                expected = colours[(action, column)]
                assert all(abs(a - e) <= 3 for a, e in zip(actual, expected))


def test_builder_removes_plain_background_and_bottom_centres_every_frame(tmp_path):
    builder = load_builder()
    sheet = tmp_path / "master.png"
    make_test_sheet(sheet)

    target = builder.build_character_from_sheet(
        sheet=sheet,
        display_name="桃桃",
        character_id="MomoPet",
        assets_root=tmp_path / "assets",
        background="#FFFFFF",
    )

    for frame_path in target.rglob("*.png"):
        with Image.open(frame_path) as frame:
            alpha = frame.getchannel("A")
            bbox = alpha.getbbox()
            assert frame.getpixel((0, 0))[3] == 0
            assert bbox is not None
            assert bbox[3] == 196
            assert abs(((bbox[0] + bbox[2]) / 2) - 96) <= 1


def test_builder_uses_one_transform_and_preserves_authored_motion_offset(tmp_path):
    builder = load_builder()
    sheet = tmp_path / "master.png"
    make_test_sheet(sheet)
    with Image.open(sheet) as original:
        image = original.copy()
    draw = ImageDraw.Draw(image)
    click_column = 3
    click_row = ACTION_ROWS.index("click")
    cell_left = click_column * 100
    cell_top = click_row * 100
    draw.rectangle(
        (cell_left, cell_top, cell_left + 99, cell_top + 99),
        fill="white",
    )
    draw.rectangle(
        (cell_left + 20, cell_top + 5, cell_left + 79, cell_top + 74),
        fill=(220, 30, 80),
    )
    image.save(sheet)

    target = builder.build_character_from_sheet(
        sheet=sheet,
        display_name="桃桃",
        character_id="MomoPet",
        assets_root=tmp_path / "assets",
    )
    with Image.open(target / "click" / "02.png") as grounded:
        grounded_bbox = grounded.getchannel("A").getbbox()
    with Image.open(target / "click" / "03.png") as airborne:
        airborne_bbox = airborne.getchannel("A").getbbox()

    assert grounded_bbox is not None
    assert airborne_bbox is not None
    assert airborne_bbox[1] < grounded_bbox[1]
    assert airborne_bbox[3] < grounded_bbox[3]
    assert abs((airborne_bbox[2] - airborne_bbox[0]) - (grounded_bbox[2] - grounded_bbox[0])) <= 1


def test_builder_auto_mode_preserves_black_character_on_real_transparency(tmp_path):
    builder = load_builder()
    sheet = tmp_path / "transparent.png"
    image = Image.new("RGBA", (600, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for row in range(3):
        for column in range(6):
            left = column * 100 + 20
            top = row * 100 + 20
            draw.rectangle((left, top, left + 59, top + 69), fill=(0, 0, 0, 255))
    image.save(sheet)

    target = builder.build_character_from_sheet(
        sheet=sheet,
        display_name="小黑",
        character_id="BlackPet",
        assets_root=tmp_path / "assets",
        background="auto",
    )

    with Image.open(target / "BlackPet_01.png") as frame:
        bbox = frame.getchannel("A").getbbox()
        assert bbox is not None
        assert frame.getpixel(((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)) == (
            0,
            0,
            0,
            255,
        )


def test_builder_writes_three_basic_action_metadata(tmp_path):
    builder = load_builder()
    sheet = tmp_path / "master.png"
    make_test_sheet(sheet)

    target = builder.build_character_from_sheet(
        sheet=sheet,
        display_name="桃桃",
        character_id="MomoPet",
        assets_root=tmp_path / "assets",
    )
    metadata = json.loads((target / "asset.json").read_text(encoding="utf-8"))

    assert metadata["type"] == "frame_animation"
    assert metadata["name"] == "桃桃"
    assert metadata["preview"] == "MomoPet_01.png"
    assert list(metadata["animations"])[: len(ACTION_ROWS)] == ACTION_ROWS
    assert set(metadata["animations"]) == set(ACTION_ROWS)
    assert "interaction_bindings" not in metadata
    assert metadata["animations"]["idle"]["folder"] == "."
    for action in ACTION_ROWS[1:]:
        assert metadata["animations"][action]["folder"] == action


def test_builder_refuses_to_overwrite_an_existing_character(tmp_path):
    builder = load_builder()
    sheet = tmp_path / "master.png"
    make_test_sheet(sheet)
    existing = tmp_path / "assets" / "MomoPet"
    existing.mkdir(parents=True)
    marker = existing / "keep.txt"
    marker.write_text("do not replace", encoding="utf-8")

    with pytest.raises(builder.CharacterBuildError, match="已经存在"):
        builder.build_character_from_sheet(
            sheet=sheet,
            display_name="桃桃",
            character_id="MomoPet",
            assets_root=tmp_path / "assets",
        )

    assert marker.read_text(encoding="utf-8") == "do not replace"


def test_builder_failure_leaves_no_partial_character_and_preserves_other_roles(
    tmp_path, monkeypatch
):
    builder = load_builder()
    sheet = tmp_path / "master.png"
    make_test_sheet(sheet)
    other = tmp_path / "assets" / "ExistingPet"
    other.mkdir(parents=True)
    marker = other / "keep.txt"
    marker.write_text("existing", encoding="utf-8")

    def reject_staging(_character_dir):
        raise builder.CharacterBuildError("synthetic validation failure")

    monkeypatch.setattr(builder, "_validate_staged_character", reject_staging)
    with pytest.raises(builder.CharacterBuildError, match="synthetic"):
        builder.build_character_from_sheet(
            sheet=sheet,
            display_name="桃桃",
            character_id="MomoPet",
            assets_root=tmp_path / "assets",
        )

    assert not (tmp_path / "assets" / "MomoPet").exists()
    assert marker.read_text(encoding="utf-8") == "existing"
    assert not list(tmp_path.glob(".windowpet-build-*"))
