from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import deque
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw


TARGET_SIZE = (192, 208)
CONTACT_COLUMNS = 4
BOTTOM_PADDING = 5
CHECKER = ((238, 241, 245, 255), (223, 228, 235, 255))
LABEL_BG = (43, 54, 67, 255)
LABEL_FG = (255, 255, 255, 255)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a chroma-key sprite strip into Window Pet reaction frames."
    )
    parser.add_argument("--character", required=True)
    parser.add_argument("--animation", required=True)
    parser.add_argument("--source", required=True, help="Generated sprite strip image.")
    parser.add_argument("--asset-dir", required=True, help="Pet asset folder.")
    parser.add_argument("--work-dir", required=True, help="QA work folder for this reaction.")
    parser.add_argument("--reference-sheet", required=True, help="Reference sheet to copy into work dir.")
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--chroma-key", default="#00FF00")
    parser.add_argument("--transparent-threshold", type=int, default=30)
    parser.add_argument("--opaque-threshold", type=int, default=96)
    return parser.parse_args()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def chroma_to_alpha(image: Image.Image, key_rgb: tuple[int, int, int], t0: int, t1: int) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    key_r, key_g, key_b = key_rgb

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            green_bias = g - max(r, b)
            if g >= 220 and green_bias >= 160 and r <= 90 and b <= 90:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            diff = math.sqrt((r - key_r) ** 2 + (g - key_g) ** 2 + (b - key_b) ** 2)
            if diff <= t0:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            if diff < t1:
                alpha = round(a * (diff - t0) / max(1, (t1 - t0)))
            else:
                alpha = a

            if alpha < 255 and g > r and g > b:
                despill = round((g - max(r, b)) * (255 - alpha) / 255)
                g = max(max(r, b), g - despill)
            pixels[x, y] = (r, g, b, alpha)
    return rgba


def slot_bounds(width: int, frames: int, index: int) -> tuple[int, int]:
    left = round(width * index / frames)
    right = round(width * (index + 1) / frames)
    return left, right


def largest_component_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    alpha = image.getchannel("A")
    width, height = image.size
    mask = alpha.load()
    visited = bytearray(width * height)
    best_size = 0
    best_bbox: tuple[int, int, int, int] | None = None
    best_pixels: list[tuple[int, int]] = []

    def idx(px: int, py: int) -> int:
        return py * width + px

    for y in range(height):
        for x in range(width):
            if mask[x, y] <= 24 or visited[idx(x, y)]:
                continue
            queue = deque([(x, y)])
            visited[idx(x, y)] = 1
            pixels_in_component: list[tuple[int, int]] = []
            min_x = max_x = x
            min_y = max_y = y

            while queue:
                cx, cy = queue.popleft()
                pixels_in_component.append((cx, cy))
                if cx < min_x:
                    min_x = cx
                if cx > max_x:
                    max_x = cx
                if cy < min_y:
                    min_y = cy
                if cy > max_y:
                    max_y = cy

                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    flat = idx(nx, ny)
                    if visited[flat] or mask[nx, ny] <= 24:
                        continue
                    visited[flat] = 1
                    queue.append((nx, ny))

            if len(pixels_in_component) > best_size:
                best_size = len(pixels_in_component)
                best_bbox = (min_x, min_y, max_x + 1, max_y + 1)
                best_pixels = pixels_in_component

    if not best_bbox:
        return None

    keep = Image.new("L", image.size, 0)
    keep_pixels = keep.load()
    for px, py in best_pixels:
        keep_pixels[px, py] = 255

    rgba = image.copy()
    rgba.putalpha(ImageChops_multiply(rgba.getchannel("A"), keep))
    image.paste(rgba)
    return best_bbox


def ImageChops_multiply(alpha: Image.Image, keep: Image.Image) -> Image.Image:
    width, height = alpha.size
    out = Image.new("L", alpha.size, 0)
    src = alpha.load()
    mask = keep.load()
    dst = out.load()
    for y in range(height):
        for x in range(width):
            dst[x, y] = round(src[x, y] * mask[x, y] / 255)
    return out


def normalize_frame(slot: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    working = slot.copy()
    bbox = largest_component_bbox(working)
    if not bbox:
        return Image.new("RGBA", target_size, (0, 0, 0, 0))

    cropped = working.crop(bbox)
    max_width = target_size[0] - 10
    max_height = target_size[1] - 10
    scale = min(1.0, max_width / max(1, cropped.width), max_height / max(1, cropped.height))
    if scale < 1.0:
        resized = cropped.resize(
            (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))),
            Image.Resampling.NEAREST,
        )
    else:
        resized = cropped

    target = Image.new("RGBA", target_size, (0, 0, 0, 0))
    x = round((target_size[0] - resized.width) / 2)
    y = target_size[1] - resized.height - BOTTOM_PADDING
    target.alpha_composite(resized, (x, y))
    return target


def make_checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, CHECKER[0])
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            color = CHECKER[(x // cell + y // cell) % 2]
            draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=color)
    return image


def build_contact_sheet(frames: list[Image.Image], labels: list[str]) -> Image.Image:
    columns = CONTACT_COLUMNS
    rows = math.ceil(len(frames) / columns)
    cell_w, cell_h = TARGET_SIZE
    label_h = 22
    sheet = Image.new("RGBA", (columns * cell_w, rows * (cell_h + label_h)), (255, 255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    for index, frame in enumerate(frames):
        row = index // columns
        col = index % columns
        x = col * cell_w
        y = row * (cell_h + label_h)
        checker = make_checkerboard(TARGET_SIZE)
        checker.alpha_composite(frame, (0, 0))
        sheet.alpha_composite(checker, (x, y))
        draw.rectangle((x, y + cell_h, x + cell_w - 1, y + cell_h + label_h - 1), fill=LABEL_BG)
        draw.text((x + 8, y + cell_h + 4), labels[index], fill=LABEL_FG)
    return sheet


def main() -> None:
    args = parse_args()
    source = Path(args.source).resolve()
    asset_dir = Path(args.asset_dir).resolve()
    work_dir = ensure_dir(Path(args.work_dir).resolve())
    reference_sheet = Path(args.reference_sheet).resolve()

    reaction_asset_dir = ensure_dir(asset_dir / args.animation)
    copied_source = work_dir / f"{args.animation}-generated-strip.png"
    shutil.copy2(source, copied_source)
    shutil.copy2(reference_sheet, work_dir / "reference_sheet.png")

    strip = Image.open(source)
    strip_rgba = chroma_to_alpha(
        strip,
        ImageColor.getrgb(args.chroma_key),
        args.transparent_threshold,
        args.opaque_threshold,
    )

    final_frames: list[Image.Image] = []
    frame_paths: list[str] = []
    for index in range(args.frames):
        left, right = slot_bounds(strip_rgba.width, args.frames, index)
        slot = strip_rgba.crop((left, 0, right, strip_rgba.height))
        frame = normalize_frame(slot, TARGET_SIZE)
        frame_path = reaction_asset_dir / f"{index:02d}.png"
        frame.save(frame_path)
        final_frames.append(frame)
        frame_paths.append(str(frame_path))

    contact = build_contact_sheet(final_frames, [f"{args.animation} {i:02d}" for i in range(args.frames)])
    contact_path = work_dir / f"{args.animation}-contact-sheet.png"
    contact.save(contact_path)

    review = {
        "character": args.character,
        "animation": args.animation,
        "source": str(copied_source),
        "frames": frame_paths,
        "frame_count": args.frames,
        "cell_size": list(TARGET_SIZE),
        "chroma_key": args.chroma_key,
        "notes": (
            f"Generated with built-in image generation from {args.character} reference sheet; "
            "extraction removed chroma key and detached motion marks by retaining the main "
            "connected pet component per slot."
        ),
    }
    (work_dir / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
