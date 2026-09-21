import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from . import state
from .asset_validation import validate_asset_metadata
from .assets import detect_asset
from .constants import BASE_DIR, resource_path


ALLOWED_CHARACTER_FILE_SUFFIXES = {
    ".json", ".png", ".webp", ".jpg", ".jpeg",
    ".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v",
}


class CharacterAcquisitionError(Exception):
    pass


def ensure_ai_authoring_guide(app_root=None):
    app_root = Path(app_root or BASE_DIR).resolve()
    bundled_guide = resource_path("AI角色制作").resolve()
    external_guide = app_root / "AI角色制作"
    if bundled_guide != external_guide.resolve():
        try:
            shutil.copytree(bundled_guide, external_guide, dirs_exist_ok=True)
            for name in ("AGENTS.md", "CLAUDE.md", "README_AI角色制作.md"):
                bundled_file = resource_path(name)
                if bundled_file.is_file():
                    shutil.copy2(bundled_file, app_root / name)
        except OSError:
            return bundled_guide
    return external_guide if external_guide.is_dir() else bundled_guide


DOUBAO_REFERENCE_RULES = """REFERENCE IMAGE MODE (MANDATORY):
Read AI角色制作/reference_image_mode.md before making any frame.
If the user provides one or more character reference images, treat the original attached image as the authoritative source of truth.
Do not redraw, redesign, reinterpret, beautify, simplify, or replace the character with a text-only lookalike.
First inspect and extract the supplied image: preserve the exact silhouette, body proportions, face, markings, palette, line weight, accessories, and asymmetrical details.
Create the base idle frame by extracting/cleaning the supplied image, then create every animation frame as a controlled edit of that extracted character.
Every animation frame must keep the same character identity, canvas anchor, scale, bounding box, palette, outline, and transparent background. Change only the pose or expression required by the action.
Attach the original reference image or the extracted canonical base to every action-generation task. Never generate an action from text alone when a reference image exists.
Before saving, compare every frame against the supplied image and reject any frame that looks like a newly invented or different character.
If the reference image cannot be accessed, stop and ask the user to attach it again; do not invent a replacement character."""


DOUBAO_ACTION_RULES = """ACTION DESIGN MODE (MANDATORY):
Use the image-generation or image-editing API/account configured for the current task. WindowPet does not require a specific provider or built-in tool. The deterministic scripts may only extract frames, validate, and package already-generated images.
Read AI角色制作/action_design_mode.md before planning actions.
Do not fake animation with only scale, zoom, translation, opacity, or whole-image wobble. Those are camera/transform effects, not character actions.
Before drawing frames, identify the character from the user's text and image. If the character or franchise is recognizable and web/search tools are available, research 3-5 recognizable, character-appropriate classic gestures, habits, expressions, or prop interactions. Use research for motion ideas only; do not copy existing animation frames.
Design only three independently drawn WindowPet basic actions: idle, click for left_click, and drag for left_drag. Do not let these three basic actions reuse, share, or alias another basic action folder. Hover, double-click, right-click, wheel, middle-click, release, random behavior, edge proximity, and rewards do not trigger character actions.
Additional actions such as waving, dance, feather-tickle, whip-hit, fall, or land are optional named animation folders. Give each a human-readable label in animations.<name>.label, animations.<name>.display_name, or action_labels.<name>. Right-click only opens the menu; its Actions submenu lists these named actions. Selecting one plays it once and returns to idle. Do not add interaction_bindings that make extra actions automatic.
For each trigger, write a one-sentence action storyboard with anticipation, action, and settle. The pose must visibly evolve through the sequence.
Draw one image per frame conceptually: inside the single master sheet, every cell must be a newly drawn complete frame. Every adjacent frame must contain a meaningful pose, limb, expression, or prop change caused by the action; body shape, clothing, hair, tail, and ears may also provide secondary motion.
Generate one complete full-frame character image per frame. Do not overlay icons, stickers, props, badges, or separate PNGs onto a static base image to pretend that the character moved.
Compose/package frames only after the full images are generated and visually inspected. If the configured provider cannot use the reference image, stop and ask for a compatible image-editing/generation provider; do not fall back to icon compositing.
Default to 6 frames per action: frame 1 neutral/anticipation; frames 2-3 preparation; frame 4 main action; frame 5 overshoot/reaction; frame 6 settle or return toward idle. Add frames when the action needs more motion, never replace frame drawing with whole-image transforms.
Keep the feet/body anchor stable unless the storyboard requires travel. Use small scale changes only as a secondary squash-and-stretch detail after the pose itself changes.
The drag folder is a stable picked-up/suspended loop only. Do not draw falling or landing inside the looping drag frames; use separate fall/land actions when supported, otherwise return to idle after release.
Reject any sequence whose frames are the same drawing merely enlarged, reduced, shifted, rotated, faded, or shaken."""

DOUBAO_MASTER_SHEET_RULES = """MASTER SHEET AND LOCAL INSTALL MODE (MANDATORY):
Use the original reference image and the completed action storyboards to generate one high-resolution 6-column by 3-row master sprite sheet containing exactly 18 cells.
Columns are frames 1 through 6. Rows are strictly idle, click, and drag.
The sheet is a generation deliverable, not the installed character. After visually checking all 18 cells, save it to a local working path and call WindowPet's build_character_from_sheet.py tool.
The local tool must perform deterministic grid splitting, plain-background removal, shared crop/scale normalisation, metadata creation, validation, and atomic installation.
Do not ask the user to crop, split, configure, import, or move files manually. Do not overwrite or delete any existing character."""


DOUBAO_EXEC_GUIDE = """【豆包生图指引（双模式自适应说明）】：
1. 极简生图模式（若在手机或网页端对话生图，强烈推荐）：
   请直接为用户绘制该角色的超萌 Q 版白底全身立绘（纯白背景 #FFFFFF 或透明底，2~2.5头身，正面全身无截断，无复杂背景杂物）：
   - 分别绘制【待机 idle】、【点击欢呼 click】、【悬空拖拽 drag】姿态（哪怕先画出 1 张待机图也可以！）；
   - 图片生成后，用户直接右键保存图片并拖入 WindowPet 软件的「九宫格动作工坊」，即可 1 秒自动生成并运行桌宠！
2. 本地全自动部署模式（办公任务 Turbo / 本地代码执行）：
   如果你具备本地终端执行权限，请严格按以下设计规范与自动化流程完成 18 格主精灵图生成、自动拆帧及原子安装。"""


def _inject_reference_rules(prompt, reference_doc=None, action_doc=None):
    lines = str(prompt).splitlines()
    rules = (
        f"{DOUBAO_EXEC_GUIDE}\n\n"
        f"{DOUBAO_REFERENCE_RULES}\n\n"
        f"{DOUBAO_ACTION_RULES}\n\n"
        f"{DOUBAO_MASTER_SHEET_RULES}"
    )
    if reference_doc is not None:
        rules = rules.replace(
            "AI角色制作/reference_image_mode.md",
            str(Path(reference_doc).resolve()),
        )
    if action_doc is not None:
        rules = rules.replace(
            "AI角色制作/action_design_mode.md",
            str(Path(action_doc).resolve()),
        )
    if not lines:
        return rules
    return "\n".join((lines[0], "", rules, *lines[1:]))


def build_doubao_image_prompt(character_description="XXX"):
    desc = str(character_description or "").strip().rstrip("。") or "超萌可爱的宠物小动物"
    return f"""请帮我设计并绘制一个超萌的桌面宠物角色立绘：【{desc}】。

【立绘风格与构图要求（画出高品质桌宠的关键）】：
1. 风格定位：Q版治愈系二次元桌宠立绘，2~2.5 头身超萌比例，大头小身，大眼睛清澈灵动，线条干净圆润，色彩鲜亮治愈。
2. 视角与画幅：正面正视全身立绘（Full Body View），角色居中站立，全身完整无遮挡截断，不要任何外边框或背景框。
3. 背景纯白（非常重要）：必须是绝对纯白背景（#FFFFFF）或纯透明背景！严禁地平线、地板阴影、草地花纹或环境装饰，确保角色轮廓清晰利落，便于一键抠图。
4. 动作状态（请分别绘制以下 3 个动作，或先绘制 1 张待机动作）：
   - 【待机动作 idle】：呆萌正面站立或端坐，微微歪头眨眼，轻松放松的静止陪伴姿态；
   - 【点击动作 click】：开心地跳跃或举起双手欢呼，做出专属得意卖萌动作，表情极度灿烂；
   - 【拖拽动作 drag】：仿佛被鼠标拎起后颈皮或悬空抓起，两脚悬空微晃，表情惊讶呆萌，四肢自然下垂。

💡【使用指引】：
出图后，我只需在豆包中右键保存图片，直接拖进电脑上的 WindowPet 软件「九宫格动作工坊」，软件会自动填充待机/点击/拖拽并生成专属桌宠，直接在桌面上开始互动！"""


build_doubao_simple_prompt = build_doubao_image_prompt


def build_doubao_prompt(app_root=None, assets_root=None, character_description="XXX"):
    app_root = Path(app_root or BASE_DIR).resolve()
    assets_root = Path(assets_root or state.ASSETS_DIR).resolve()
    guide_root = app_root / "AI角色制作"
    character_package = assets_root / "{角色英文名}Pet"
    master_sheet = app_root / "AI角色制作" / "角色制作工作区" / "{角色英文名}-master-sheet.png"
    character_description = str(character_description or "").strip().rstrip("。") or "XXX"
    return f"""我创建这个角色是{character_description}。
请直接为当前 WindowPet 软件生成并添加一个新角色。

这不是让我学习制作方法。你必须使用当前配置的图片生成/编辑 API 或账号先生成一张主精灵图，再调用 WindowPet 本地工具完成拆帧、去背景、配置、质检和安装。不要只返回教程、提示词、预览图或压缩包，也不要让我手动裁剪、拆帧、配置或导入。

第一步：读懂软件。开始前完整读取以下文件，并严格按其中规范执行：
1. {guide_root / 'START_HERE.md'}
2. {guide_root / 'AI先读我.md'}
3. {guide_root / 'master_sheet_prompt.md'}
4. {guide_root / 'master_sheet_schema.json'}
5. {guide_root / '质量标准.json'}

WindowPet 角色库根目录：
{assets_root}

角色包最终地址（本地工具必须在这里直接创建完整角色包并原子安装）：
{character_package}

第二步：生成主帧图。根据用户提供的原始角色图和文字，先锁定角色身份；若角色可识别且可以检索，查找 3–5 个经典动作作为动作设计参考。为 idle、click 和 drag 分别写好六帧动作脚本，再用当前配置的图片生成 API 或账号一次生成一张严格 6 列 × 3 行、共 18 格的高分辨率主精灵图。每格必须是完整重新绘制的真实动作帧，三行顺序和全部绘图限制以 master_sheet_prompt.md 为准。禁止仅缩放、平移或给静态图叠加图标。舞蹈、挥手等额外动作另建同名动画，并用可读名称放入右键“动作”菜单。

主精灵图本地工作地址：
{master_sheet}

第三步：自动部署。先目视检查 18 格的角色一致性和动作连贯性，然后把“{{角色英文名}}”替换为实际英文名，直接执行：
python "{guide_root / 'build_character_from_sheet.py'}" --sheet "{master_sheet}" --display-name "<角色显示名>" --character-id "<角色英文名Pet>" --assets-root "{assets_root}" --background auto

这个工具会按固定网格拆出 18 帧，去除纯色背景，让全部帧共用同一裁剪窗口和缩放比例，生成 192×208 RGBA PNG 和 asset.json；校验通过后原子安装。它遇到同名目录会拒绝覆盖；不得删除、覆盖或修改任何已有角色、程序 EXE 或公共配置。

基础动画只使用 idle、click、drag，每个动作默认 6 帧。完成后再运行质量检查：
python "{guide_root / 'validate_character.py'}" "{character_package}"

检查通过后刷新 WindowPet 角色库，确认角色已经保存在上述最终地址，并告诉我实际角色目录、18 帧数量和检查结果。"""


_build_doubao_prompt = build_doubao_prompt


def build_doubao_prompt(app_root=None, assets_root=None, character_description="XXX"):
    app_root = Path(app_root or BASE_DIR).resolve()
    return _inject_reference_rules(
        _build_doubao_prompt(app_root, assets_root, character_description),
        app_root / "AI角色制作" / "reference_image_mode.md",
        app_root / "AI角色制作" / "action_design_mode.md",
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_archive_member(info):
    raw_name = str(info.filename or "").replace("\\", "/")
    path = PurePosixPath(raw_name)
    if not raw_name or raw_name.startswith("/") or re.match(r"^[A-Za-z]:", raw_name):
        raise CharacterAcquisitionError("角色 ZIP 含有不安全的绝对路径。")
    if any(part in {"..", ""} for part in path.parts):
        raise CharacterAcquisitionError("角色 ZIP 含有不安全的路径。")
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    if unix_mode and stat.S_ISLNK(unix_mode):
        raise CharacterAcquisitionError("角色 ZIP 不允许包含快捷方式或符号链接。")
    if info.flag_bits & 0x1:
        raise CharacterAcquisitionError("暂不支持带密码的角色 ZIP。")
    if not info.is_dir():
        suffix = Path(path.name).suffix.lower()
        if suffix not in ALLOWED_CHARACTER_FILE_SUFFIXES:
            raise CharacterAcquisitionError(f"角色 ZIP 含有不支持的文件：{path.name}")
    return path


def _extract_character_archive(archive, staging_root):
    try:
        with zipfile.ZipFile(archive) as bundle:
            corrupt = bundle.testzip()
            if corrupt:
                raise CharacterAcquisitionError(f"角色 ZIP 已损坏：{corrupt}")
            for info in bundle.infolist():
                member = _safe_archive_member(info)
                destination = staging_root.joinpath(*member.parts)
                try:
                    destination.resolve().relative_to(staging_root.resolve())
                except ValueError as exc:
                    raise CharacterAcquisitionError("角色 ZIP 含有不安全的路径。") from exc
                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, destination.open("wb") as target:
                    shutil.copyfileobj(source, target)
    except (OSError, zipfile.BadZipFile) as exc:
        raise CharacterAcquisitionError("无法读取角色 ZIP，请确认文件完整。") from exc


def _character_root(staging_root):
    manifests = sorted(staging_root.rglob("asset.json"))
    if len(manifests) != 1:
        raise CharacterAcquisitionError("角色 ZIP 必须且只能包含一个 asset.json。")
    return manifests[0].parent, manifests[0]


def _folder_name(character_root, staging_root, archive):
    source = character_root.name if character_root != staging_root else Path(archive).stem
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", source).strip(" .-")
    return safe or "ImportedPet"


def install_character_archive(archive, assets_root=None, expected_sha256=None):
    archive = Path(archive).resolve()
    assets_root = Path(assets_root or state.ASSETS_DIR).resolve()
    if not archive.is_file() or archive.suffix.lower() != ".zip":
        raise CharacterAcquisitionError("请选择有效的角色 ZIP 文件。")
    if expected_sha256:
        actual = sha256_file(archive)
        if actual.lower() != str(expected_sha256).strip().lower():
            raise CharacterAcquisitionError("角色包校验失败，文件可能不完整或已被替换。")

    assets_root.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix=".windowpet-import-", dir=assets_root.parent))
    try:
        _extract_character_archive(archive, staging_root)
        character_root, manifest_path = _character_root(staging_root)
        try:
            metadata = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CharacterAcquisitionError("asset.json 无法读取或不是有效 JSON。") from exc
        if not isinstance(metadata, dict):
            raise CharacterAcquisitionError("asset.json 顶层必须是 JSON 对象。")

        asset = detect_asset(character_root)
        if asset is None:
            raise CharacterAcquisitionError("角色包缺少可读取的动画图片，无法导入。")
        validation_errors = validate_asset_metadata(asset)
        if validation_errors:
            raise CharacterAcquisitionError("角色包未通过素材校验：\n" + "\n".join(validation_errors))

        target = assets_root / _folder_name(character_root, staging_root, archive)
        if target.exists():
            raise CharacterAcquisitionError(f"角色“{target.name}”已经存在，本次没有覆盖原角色。")
        os.replace(character_root, target)
        return target
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)


def download_and_install_character(download, assets_root=None, timeout=60):
    download = download if isinstance(download, dict) else {}
    url = str(download.get("url") or "").strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise CharacterAcquisitionError("云端没有返回安全的角色包下载地址。")

    assets_root = Path(assets_root or state.ASSETS_DIR).resolve()
    assets_root.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".windowpet-download-",
        suffix=".zip",
        dir=assets_root.parent,
    )
    os.close(descriptor)
    temp_archive = Path(temp_name)
    try:
        try:
            request = urllib.request.Request(url, headers={"Accept": "application/zip"})
            with urllib.request.urlopen(request, timeout=timeout) as response, temp_archive.open("wb") as target:
                shutil.copyfileobj(response, target)
        except (OSError, urllib.error.URLError, TimeoutError) as exc:
            raise CharacterAcquisitionError("角色包下载失败，请检查网络后重试。") from exc

        declared_size = download.get("size_bytes")
        if declared_size not in (None, ""):
            try:
                expected_size = int(declared_size)
            except (TypeError, ValueError) as exc:
                raise CharacterAcquisitionError("云端返回的角色包大小信息无效。") from exc
            if temp_archive.stat().st_size != expected_size:
                raise CharacterAcquisitionError("角色包大小校验失败，下载可能不完整。")
        return install_character_archive(
            temp_archive,
            assets_root,
            expected_sha256=download.get("sha256"),
        )
    finally:
        temp_archive.unlink(missing_ok=True)
