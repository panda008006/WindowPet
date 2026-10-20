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
    guide_name = "角色" if resource_path("角色").is_dir() or (app_root / "角色").is_dir() else "AI角色制作"
    bundled_guide = resource_path(guide_name).resolve()
    external_guide = app_root / guide_name
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


DEEPSEEK_REFERENCE_RULES = """REFERENCE IMAGE MODE (MANDATORY):
Read AI角色制作/reference_image_mode.md before making any frame.
If the user provides one or more character reference images, treat the original attached image as the authoritative source of truth.
Do not redraw, redesign, reinterpret, beautify, simplify, or replace the character with a text-only lookalike.
First inspect and extract the supplied image: preserve the exact silhouette, body proportions, face, markings, palette, line weight, accessories, and asymmetrical details.
Create the base idle frame by extracting/cleaning the supplied image, then create every animation frame as a controlled edit of that extracted character.
Every animation frame must keep the same character identity, canvas anchor, scale, bounding box, palette, outline, and transparent background. Change only the pose or expression required by the action.
Attach the original reference image or the extracted canonical base to every action-generation task. Never generate an action from text alone when a reference image exists.
Before saving, compare every frame against the supplied image and reject any frame that looks like a newly invented or different character.
If the reference image cannot be accessed, stop and ask the user to attach it again; do not invent a replacement character."""

DEEPSEEK_ACTION_RULES = """ACTION DESIGN MODE (MANDATORY):
Read AI角色制作/action_design_mode.md before making any frame.
Do not fake animation with only scale, zoom, translation, opacity, or whole-image wobble.
Use the image-generation or image-editing API/account configured for the current task.
Generate one complete full-frame character image per frame.
Do not overlay icons, stickers, props, badges, or separate PNGs.
Compose/package frames only after the full images are generated.
If the configured provider cannot use the reference image, stop.
When the character is recognizable, research 3-5 recognizable gestures, habits, expressions, signature poses, or prop interactions.
Adapt the required motion concepts: idle, click for left_click, and drag for left_drag.
Follow the six-frame motion arc: anticipation, action, and settle.
Every adjacent frame must have a meaningful pose, limb, expression, or prop change.
one image per frame.

WindowPet 2.0 拥有 5 大核心动作插槽标准体系：
1. 【常规待机 idle】：呆萌平稳站立或端坐，带有轻微的呼吸起伏与重心摆动，首尾无缝平滑闭环 (Looping)；
2. 【点击互动 click】：被鼠标戳中后的招牌动作，如开心挥手、举双手欢呼或招牌卖萌；
3. 【提溜悬空 drag】：被鼠标拎起后颈皮或悬空拖拽，两脚微晃自然悬空，神情呆萌惊讶；
4. 【思考中 thinking / habit1】：AI深度推理思考状态，小手托腮望向斜上方，灵动思考；
5. 【回答完成 result / habit2】：AI推理结束生成结果，自信打响指、满意点头或欢呼庆祝。

同时 WindowPet 2.0 搭载「静态随机动作池」，支持在待机时随机展示打瞌睡、伸懒腰、吃零食等趣味表演。"""

DEEPSEEK_MASTER_SHEET_RULES = """MASTER SHEET AND LOCAL INSTALL MODE (MANDATORY):
Use the original reference image and the completed action storyboards to generate one high-resolution 6-column by 3-row master sprite sheet containing exactly 18 cells.
Columns are frames 1 through 6. Rows are strictly idle, click, and drag.
The sheet is a generation deliverable, not the installed character. After visually checking all 18 cells, save it to a local working path and call WindowPet's build_character_from_sheet.py tool.
The local tool must perform deterministic grid splitting, plain-background removal, shared crop/scale normalisation, metadata creation, validation, and atomic installation.
Do not ask the user to crop, split, configure, import, or move files manually. Do not overwrite or delete any existing character."""

DEEPSEEK_EXEC_GUIDE = """【DeepSeek AI 角色生成指引（WindowPet 2.0 官方自适应规范）】：
1. 🎨 极简出图提示词模式（发给生图 AI 绘图，强烈推荐）：
   DeepSeek 将为你深度思考并产出专业的 Midjourney / FLUX / 即梦 AI / 可灵 提示词：
   - 角色形象：2~2.5 头身超萌 Q 版二次元立绘，正面全身无遮挡无截断；
   - 纯净底色：绝对纯白背景（#FFFFFF）或影视级纯绿幕（#00FF00），便于 WindowPet 发丝级无损透明抠像；
   - 动作套系：精准覆盖待机 (idle)、点击 (click)、拖拽 (drag)、深度思考 (thinking)、回答完成 (result)；
   - 用户只需将图片/视频拖入 WindowPet 2.0 的「九宫格动作工坊」，1 秒即可点亮桌面！
2. 💻 本地全自动部署模式（配备终端执行环境）：
   DeepSeek 生成标准 JSON 动作编排与安装代码，自动装配至 assets 目录并注入系统注册表。"""

DOUBAO_REFERENCE_RULES = DEEPSEEK_REFERENCE_RULES
DOUBAO_ACTION_RULES = DEEPSEEK_ACTION_RULES
DOUBAO_MASTER_SHEET_RULES = DEEPSEEK_MASTER_SHEET_RULES
DOUBAO_EXEC_GUIDE = DEEPSEEK_EXEC_GUIDE


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


def build_deepseek_image_prompt(character_description="XXX"):
    desc = str(character_description or "").strip().rstrip("。") or "超萌可爱的桌面宠物小动物"
    return f"""作为 WindowPet 2.0 桌面宠物角色资深概念设计师，请帮我为【{desc}】设计一套完整的超清桌宠立绘与动作提示词。

【WindowPet 2.0 角色标准规范】：
1. 风格定位：Q版二次元治愈系桌宠立绘，2~2.5 头身萌系比例，大头小身，大眼睛清澈灵动，线条干净圆润，无杂乱背景干扰。
2. 视角与画幅：正面正视全身立绘（Full Body View），角色居中站立，全身完整无截断，杜绝半身像或大头贴。
3. 纯净背景（核心关键）：必须是绝对纯白背景（#FFFFFF）或纯正绿幕（#00FF00）！绝对不要地平线、地板杂色阴影、室内外装饰或花草杂物，确保 WindowPet 2.0 的 UltraKey 原生发丝级透明抠像能 100% 干净提取！

【5 大核心动作剧本与生图提示词（请按以下格式逐一生成中英文 Midjourney/FLUX Prompt）】：
1. 【待机 idle】（常规待机）：正面呆萌站立或端坐，微微歪头眨眼，轻松放松的静止陪伴姿态，身体重心平衡稳定。
   - 画面描述：Q-version cute character, full body front view, standing peacefully, blinking adorably, isolated on pure solid white background #FFFFFF, no shadows, no floor.
2. 【点击 click】（交互响应）：鼠标轻戳时做出的招牌互动，开心地双臂欢呼、单脚轻蹦或得意卖萌，神情极度灿烂治愈。
   - 画面描述：Q-version character jumping joyfully with arms raised, cheering happily, dynamic cute pose, isolated on pure solid white background #FFFFFF.
3. 【拖拽 drag】（悬空提溜）：被鼠标拎起后颈皮或悬空抓起，两脚悬空微晃，四肢自然下垂，露出惊讶呆萌的委屈小表情。
   - 画面描述：Q-version character lifted up in mid-air, dangling feet gently, surprised and cute face, centered, isolated on pure solid white background #FFFFFF.
4. 【思考 thinking】（AI思考模式）：两只小手托腮或托下巴，眼睛望向斜上方，头顶冒出灵感小气泡，专心沉思中。
   - 画面描述：Q-version character pondering deeply, hand on chin, looking upwards thoughtfully, cute thinking pose, isolated on pure solid white background #FFFFFF.
5. 【回答 result】（AI作答庆祝）：思考得出满意答案，自豪地打响指、双手抱胸点头或举起写着满分的小牌子，开心得意。
   - 画面描述：Q-version character celebrating an answer proudly, nodding with a triumphant cute smile, isolated on pure solid white background #FFFFFF.

💡【WindowPet 2.0 极速使用指引】：
图片生成后，直接右键保存为 PNG，打开 WindowPet 2.0 点击「🎨 九宫格动作工坊」，直接拖入对应动作槽位，即可在桌面上享受 1440P 原生超清透明互动！"""


build_doubao_image_prompt = build_deepseek_image_prompt
build_doubao_simple_prompt = build_deepseek_image_prompt
build_deepseek_simple_prompt = build_deepseek_image_prompt


def _base_doubao_prompt(app_root=None, assets_root=None, character_description="XXX"):
    app_root = Path(app_root or BASE_DIR).resolve()
    assets_root = Path(assets_root or state.ASSETS_DIR).resolve()
    guide_folder = "角色" if (app_root / "角色").is_dir() else "AI角色制作"
    guide_root = app_root / guide_folder
    character_package = assets_root / "{角色英文名}Pet"
    master_sheet = app_root / guide_folder / "角色制作工作区" / "{角色英文名}-master-sheet.png"
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


def build_deepseek_prompt(app_root=None, assets_root=None, character_description="XXX"):
    app_root = Path(app_root or BASE_DIR).resolve()
    assets_root = Path(assets_root or state.ASSETS_DIR).resolve()
    guide_folder = "角色" if (app_root / "角色").is_dir() else "AI角色制作"
    return _inject_reference_rules(
        _base_doubao_prompt(app_root, assets_root, character_description),
        app_root / guide_folder / "reference_image_mode.md",
        app_root / guide_folder / "action_design_mode.md",
    )


build_doubao_prompt = build_deepseek_prompt
_build_doubao_prompt = _base_doubao_prompt


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
