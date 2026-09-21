# WindowPet 通用 AI 角色制作协议

本文件是角色制作的唯一主说明，适用于 Codex、Claude Code、豆包、Cursor、VSCode 智能插件及其他能够读写文件的 AI。目标是直接为当前 WindowPet 软件生成可加载角色，不依赖某个聊天软件，也不要求运行独立工坊。

## 收到角色制作任务后必须执行

1. 先阅读 `START_HERE.md`，再阅读本文件并查看 `角色模板/asset.json`。
2. 如果用户提供了角色原图，先分析并固定角色的脸型、比例、配色、饰品和线条风格。
3. 在软件根目录的 `assets/<英文角色名Pet>/` 新建角色；不要覆盖其他角色。
4. 优先按 `master_sheet_prompt.md` 一次生成固定 6 列 × 3 行主精灵图，再调用 `build_character_from_sheet.py` 自动生成透明背景 PNG 动画帧和 `asset.json`。
5. 基础状态只有 `idle`、`click`、`drag`。额外功能动作单独命名，并从右键“动作”菜单手动选择；不要为它们创造新的鼠标手势或自动行为。
6. 运行 `python AI角色制作/validate_character.py assets/<英文角色名Pet>`。
7. 修复所有 ERROR；WARNING 应尽量修复，无法修复时向用户说明。

## 默认质控档：创作者自由版

默认读取同目录的 `质量标准.json`，按创作者自由档制作：

- 3 个基础动画：`idle`、`click`、`drag`。
- 每个基础动作默认 6 帧，共 18 帧；这是起点，不是上限。
- 额外动作也默认从 6 帧开始，玩家可以自由增加动作和帧数。
- 平台只报告角色目录体积，不因超过 3 MB、总帧数较多或额外动作较多而警告或拒绝。
- 质控只关注能否运行、图片是否有效、动作是否齐全、画布是否一致和动画是否明显损坏。

| 动作 | 目标帧数 | 合理范围 | FPS | 用途 |
|---|---:|---:|---:|---|
| `idle` | 6 | 至少 4 | 8 | 基础呼吸循环 |
| `click` | 6 | 至少 4 | 10 | 单击问候 |
| `drag` | 6 | 至少 4 | 10 | 抓起/拖动循环 |

玩家可以自由添加 waiting、waving、dance、concert、feather-tickle、whip-hit、fall、land 或其他原创动作；每个额外动作都要有独立 `animations.<动作名>` 定义和用户可读名称，例如 `"label": "跳个舞"`。

## 三种基础状态与手动动作菜单

用户只需要记住三种基础状态：

| 动作键 | 用户行为 | 运行方式 |
|---|---|---|
| `idle` | 默认待机 | 循环 |
| `click` | 左键单击 | 播放一次后回待机 |
| `drag` | 左键拖动 | 拖动期间循环，松开后回待机 |

右键只打开功能菜单，不触发表演。菜单内的“动作”子菜单列出所有额外命名动作；用户点选某一项后播放一次并回到 `idle`。悬停、双击、滚轮、中键、随机、奖励、屏幕边界和靠近其他角色都不触发角色动作。

普通角色至少制作：`idle`、`click`、`drag`。

额外动作直接写入 `animations`，并在动作定义中写 `label`、`display_name` 或顶层 `action_labels`。不要写 `interaction_bindings` 让它们随机播放。旧角色的 `hover`、`jumping`、`review` 等动作仍会兼容显示在手动菜单中，不会丢失。

## 图片硬性要求

- 推荐画布：`192 × 208 px`，同一角色所有帧必须一致。
- PNG、RGBA、透明背景；不要生成棋盘格、场景、文字、对话框或 UI。
- 脚底基线、身体中心、头身比、线条粗细、固定服装和饰品保持稳定。
- 文件按自然数字顺序命名：`00.png`、`01.png`、`02.png`……
- `idle` 帧放在角色根目录，命名为 `<character_id>_01.png`、`<character_id>_02.png`……
- 其他动作放进同名子文件夹。
- 每个动作建议 6–12 帧；轻动作 8–10 FPS，快速反应 10–12 FPS。
- 默认从 6 帧开始；如果动作需要更细腻的过程，可以自由增加帧数。
- 动作第一帧应能从 idle 自然进入，最后一帧应自然回到 idle。
- 道具不能突然出现或消失，尺寸不能突然放大或缩小。

## 第三种制作方法：视频导入

用户手上有"去掉背景的动态视频"时，直接把视频变成角色动作，无需逐帧生图：

- 透明视频：qtrle/png 编码的 `.mov`，或带 alpha 通道的 `.webm`（`--background transparent`，默认 auto 自动识别）。
- 绿幕/洋红幕视频：`.mp4`/`.webm` 纯色背景，用 `--background "#00FF00"` 或 `"#FF00FF"` 自动抠像。
- 动图：`.gif`/`.apng`/动图 `.webp` 直接逐帧拆。
- 新建角色：`python AI角色制作/video_to_character.py --video 视频 --character-id XxxPet --display-name 名称 --assets-root assets`（视频帧装入 `idle`、`click`、`drag`，之后可逐个替换）。
- 给现有角色加/换动作：加 `--action idle|click|drag`；额外手动动作可用 `--action dance` 等安全英文名。
- 工具自动完成：抽帧、透明度真源检测、抠像、统一画布 192×208、底边对齐、写 `asset.json`、调 `validate_character.py`。
- 详见 `video_import_mode.md`。

三种官方制作方法并存：① 主精灵图逐帧生图（`build_character_from_sheet.py`）；
② 头部追踪/参数网格角色（如 XiaobaTurnPet 的 5×5 `head_track`）；
③ 视频导入（`video_to_character.py`）。三者产出相同的 `frame_animation` 格式，可自由组合。

运行时"文件夹即素材"：软件加载任意动作文件夹时，里面无论是 PNG 帧序列、
单张图片、GIF/APNG/动图 webp、还是 mp4/webm/mov 视频（自动 ffmpeg 抽帧，
缓存在文件夹内 `.media_cache\`），都会被展开成可播放的帧序列；单帧也能运行
（静态显示）。因此调试素材时可以直接把 GIF/视频丢进动作文件夹验证效果，
无需预先转换。找不到 ffmpeg 时视频来源跳过（日志有 WARNING），其余媒体不受影响。

## 目录范例

```text
assets/MyCatPet/
├─ asset.json
├─ my-cat_01.png
├─ my-cat_02.png
├─ click/00.png ...
├─ drag/00.png ...
├─ feather-tickle/00.png ...
└─ concert-special/00.png ...
```

`asset.json` 中 `animations.<动作名>.folder` 必须与文件夹名称完全一致。`idle.folder` 使用 `"."`。

## 连贯性检查

制作动作时不要只检查单帧是否好看，还要逐帧检查：

- 相邻两帧角色位置、比例、轮廓和道具是否突然变化。
- 循环动作的最后一帧能否接回第一帧。
- 非循环动作的首尾能否接近 idle。
- 拖拽链是否至少包含稳定的抓起/拖动帧；如制作了 `fall` 或 `land`，它们仅是右键菜单里的手动动作，不能在松开鼠标时自动播放。

可选的可视化角色工坊位于项目外部，用于播放和诊断；它不是角色运行所必需的。此目录中的说明、模板与校验脚本才是跨 AI 制作的核心。

体积仅作为信息显示，不作为创作者限制。如果创作者主动要求优化，只使用无损方式：清除 PNG 元数据或使用 `oxipng` 等无损压缩；不要为了减小文件破坏透明通道或画面质量。

## 安全边界

- 角色包只能包含图片、受支持的视频源和声明式 JSON，不得把 PowerShell、EXE、DLL 或任意可执行代码塞进角色目录。
- 不修改 `Window Pet.exe`。
- 不删除或覆盖既有角色。
- 不修改 `config.json` 中用户当前窗口、账号或解锁状态，除非用户明确要求。
