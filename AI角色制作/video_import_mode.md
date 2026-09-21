# 视频导入模式 / Video Import Mode

把"去掉背景的动态视频"直接变成 WindowPet 角色动作的第三种官方制作方法。
工具：`video_to_character.py`（与 `build_character_from_sheet.py` 并列）。

## 输入格式与选择

| 素材 | 参数 | 说明 |
|---|---|---|
| 透明 mov（qtrle/png 编码，argb/rgba） | `--background transparent` 或 `auto` | 首选格式，alpha 完整保留 |
| 透明 webm（VP8/VP9 alpha） | 同上 | 注意：部分 ffmpeg 构建的 libvpx 会静默丢弃 alpha，导入后务必目视检查帧 |
| 绿幕 / 洋红幕视频 | `--background "#00FF00"` / `"#FF00FF"` | ffmpeg colorkey 自动抠像 |
| GIF / APNG / 动图 WebP | 无需参数 | PIL 直接逐帧拆 |

工具用"实际抽帧检查透明度"做真源判断，不信任 ffprobe 的 pix_fmt 报告。
`auto` 模式：抽到 alpha 就按透明处理；没有 alpha 且未指定抠像色则报错并提示。

## 用法 A：新建角色

```powershell
python "AI角色制作\video_to_character.py" `
  --video "D:\pets\dance_alpha.mov" `
  --character-id MyDogPet `
  --display-name "我家狗狗" `
  --assets-root "assets"
```

视频帧会同时装入三个基础动作（idle/click/drag），
保证角色立即可运行；之后用用法 B 逐个替换，或添加右键“动作”菜单里的具名动作。
`asset.json` 会带 `"source": {"method": "video_import", "actions": {...}}` 记录来源。

## 用法 B：给现有角色添加或替换动作

```powershell
python "AI角色制作\video_to_character.py" `
  --video "D:\pets\wave.mov" `
  --character-id MyDogPet `
  --action click
```

`--action` 支持 `idle`、`click`、`drag` 和安全的自定义动作名（例如 `dance`、`waving`）；idle 写到角色根目录
（`<character_id>_01.png`...），其他动作写入同名子文件夹（`00.png`...）。
同名动作的旧帧会被替换（先删除再写入）。可选 `--fps 12` 覆盖播放帧率，
`--max-frames 96` 限制帧数（超长视频按比例抽稀，默认 96）。

## 工具自动完成的事

1. ffprobe 探测画面流；ffmpeg 抽帧（PNG 保留 alpha；抠像色时加 colorkey 滤镜）。
2. 第一帧实际透明度检测（alpha extrema < 250 才算真透明）。
3. 全帧共享 bbox 裁剪 → 按比例缩放到 192×208 画布内 → 底边对齐（脚底基线一致）。
4. 写帧 + 更新 `asset.json`（含 loop 规则：idle/drag 循环）。自定义动作会在右键“动作”菜单中显示；可在 `animations.<动作名>.label` 写显示名称。
5. 自动调用 `validate_character.py`；有 ERROR 则退出码 1。

## 质量要求（与逐帧生图一致）

- 视频里的角色应：构图稳定、比例一致、脚底基线平稳、无场景残留、无文字水印。
- 透明视频先在播放器里确认边缘干净（黑边/半透明边会在桌宠上显现）。
- 绿幕视频背景必须是均匀纯色，避免角色身上有大面积同色。
- 动作第一帧最好接近 idle 姿态，最后一帧能自然接回 idle。
- 帧率建议：视频 10-15 FPS 录制/导出，抽帧后动作连续。

## 与运行时的关系

产出就是标准 `frame_animation` 格式（与逐帧生图管线完全相同）。运行时只自动使用 `idle`、`click`、`drag`；
其他动作由用户从右键“动作”菜单手动选择，默认播放一次后回到待机；如果动作定义里写入
`"repeat_count": 3`，则会连续播放三遍后回到待机。视频导入动作已有 `duration_seconds` 时，
循环次数会同时作用于画面帧和原视频音轨。

导入器会把视频抽出的 PNG 帧作为稳定的透明画面，同时把原视频保存在角色包的
`video_sources` 目录并写入 `asset.json`。运行时播放 PNG 帧时，会从对应的视频源同步播放原始音轨；
因此视频有声音时会保留声音，切换到没有视频源的普通图片动作时会停止旧音轨。

调试时也可以直接把 `.mp4`、`.webm`、`.mov` 等视频放入动作文件夹：运行时会自动用 ffmpeg
抽帧并缓存到该文件夹的 `.media_cache`，同时播放动作文件夹里的视频音轨。直接选中一个视频文件也能
作为独立视频素材播放画面和声音。正式角色仍建议使用导入器生成的 PNG 帧加 `video_sources` 记录，
便于透明背景、动作切换和跨机器运行。
