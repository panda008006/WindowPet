import argparse
import json
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen


ACTIONS = (
    "idle",
    "hover",
    "click",
    "jumping",
    "drag",
    "review",
    "right-double-click",
    "whip-hit",
    "feather-tickle",
)
SUPPORTED_IMAGES = {".png", ".jpg", ".jpeg", ".webp"}


def natural_key(path):
    import re

    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", Path(path).name)]


def frame_image(asset_dir, metadata, action):
    definition = metadata["animations"][action]
    if metadata.get("type") == "spritesheet":
        source = QImage(str(asset_dir / str(metadata.get("image") or "")))
        frames = definition.get("frames") or []
        if source.isNull() or not frames:
            return QImage(), 0
        frame = frames[len(frames) // 2]
        width = int(metadata.get("frame_width") or 0)
        height = int(metadata.get("frame_height") or 0)
        x = int(frame.get("x", int(frame.get("col", 0)) * width))
        y = int(frame.get("y", int(frame.get("row", 0)) * height))
        return source.copy(x, y, width, height), len(frames)

    folder_name = str(definition.get("folder") or ".")
    folder = asset_dir if folder_name in {"", "."} else asset_dir / folder_name
    frames = sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGES),
        key=natural_key,
    ) if folder.exists() else []
    if not frames:
        return QImage(), 0
    return QImage(str(frames[len(frames) // 2])), len(frames)


def draw_checkerboard(painter, rect):
    size = 12
    colors = (QColor("#f7fbff"), QColor("#dfefff"))
    for y in range(rect.top(), rect.bottom() + 1, size):
        for x in range(rect.left(), rect.right() + 1, size):
            painter.fillRect(QRect(x, y, size, size), colors[((x - rect.left()) // size + (y - rect.top()) // size) % 2])


def render_page(rows, output_path, page_index, page_count):
    label_width = 170
    cell_width = 132
    row_height = 150
    header_height = 58
    width = label_width + len(ACTIONS) * cell_width + 24
    height = header_height + len(rows) * row_height + 18
    canvas = QImage(width, height, QImage.Format_ARGB32)
    canvas.fill(QColor("#edf8ff"))
    painter = QPainter(canvas)
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

    title_font = QFont("Microsoft YaHei UI", 13, QFont.Bold)
    label_font = QFont("Microsoft YaHei UI", 9, QFont.Bold)
    small_font = QFont("Microsoft YaHei UI", 7)
    painter.setFont(title_font)
    painter.setPen(QColor("#0b2b50"))
    painter.drawText(QRect(16, 6, width - 32, 26), Qt.AlignLeft | Qt.AlignVCenter, f"Window Pet 9-action audit · page {page_index}/{page_count}")
    painter.setFont(small_font)
    for index, action in enumerate(ACTIONS):
        painter.drawText(QRect(label_width + index * cell_width, 32, cell_width, 20), Qt.AlignCenter, action)

    for row_index, row in enumerate(rows):
        top = header_height + row_index * row_height
        painter.setPen(QPen(QColor("#9cc7eb"), 1))
        painter.drawLine(12, top, width - 12, top)
        painter.setFont(label_font)
        painter.setPen(QColor("#0b2b50"))
        painter.drawText(QRect(16, top + 20, label_width - 24, 44), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, row["name"])
        painter.setFont(small_font)
        painter.setPen(QColor("#58738b"))
        painter.drawText(QRect(16, top + 68, label_width - 24, 44), Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, f"{row['type']}\n{row['character_id'] or '-'}")

        for action_index, action in enumerate(ACTIONS):
            left = label_width + action_index * cell_width
            cell = QRect(left + 7, top + 7, cell_width - 14, row_height - 24)
            draw_checkerboard(painter, cell)
            image = row["images"][action]
            if image.isNull():
                painter.setPen(QColor("#b42318"))
                painter.drawText(cell, Qt.AlignCenter, "MISSING")
            else:
                target = image.scaled(cell.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x = cell.left() + (cell.width() - target.width()) // 2
                y = cell.top() + (cell.height() - target.height()) // 2
                painter.drawImage(x, y, target)
            painter.setPen(QPen(QColor("#8cbbe3"), 1))
            painter.drawRect(cell)
            painter.setPen(QColor("#315a7e"))
            painter.drawText(QRect(left, top + row_height - 19, cell_width, 16), Qt.AlignCenter, f"{row['counts'][action]} frames")

    painter.end()
    if not canvas.save(str(output_path), "PNG"):
        raise RuntimeError(f"Could not save {output_path}")


def main():
    app = QGuiApplication.instance() or QGuiApplication([])
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=Path("assets"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    rows = []
    errors = []
    for asset_dir in sorted((path for path in args.assets.iterdir() if path.is_dir()), key=natural_key):
        manifest = asset_dir / "asset.json"
        if not manifest.exists():
            continue
        metadata = json.loads(manifest.read_text(encoding="utf-8-sig"))
        images = {}
        counts = {}
        action_errors = []
        animations = metadata.get("animations") or {}
        for action in ACTIONS:
            if action not in animations:
                images[action] = QImage()
                counts[action] = 0
                action_errors.append(f"missing action: {action}")
                continue
            image, count = frame_image(asset_dir, metadata, action)
            images[action] = image
            counts[action] = count
            if image.isNull():
                action_errors.append(f"unreadable action: {action}")
        row = {
            "folder": asset_dir.name,
            "name": str(metadata.get("name") or asset_dir.name),
            "type": str(metadata.get("type") or ""),
            "character_id": str(metadata.get("character_id") or ""),
            "images": images,
            "counts": counts,
            "errors": action_errors,
        }
        rows.append(row)
        if action_errors:
            errors.append({"pet": asset_dir.name, "errors": action_errors})

    page_size = 6
    page_count = (len(rows) + page_size - 1) // page_size
    for index in range(page_count):
        render_page(
            rows[index * page_size : (index + 1) * page_size],
            args.output / f"all-pets-actions-page-{index + 1}.png",
            index + 1,
            page_count,
        )

    report = {
        "pet_count": len(rows),
        "required_actions": list(ACTIONS),
        "passed": not errors,
        "errors": errors,
        "pets": [
            {
                "folder": row["folder"],
                "name": row["name"],
                "type": row["type"],
                "character_id": row["character_id"],
                "frame_counts": row["counts"],
            }
            for row in rows
        ],
    }
    (args.output / "all-pets-actions-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"pet_count": len(rows), "pages": page_count, "passed": not errors}, ensure_ascii=False))
    app.quit()
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
