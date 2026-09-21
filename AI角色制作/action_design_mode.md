# Real action design mode / 真实动作设计模式

Animation means drawing a changing character pose one frame at a time. Moving, scaling, rotating, fading, or shaking one unchanged picture is not an acceptable character animation.

## Full-frame image generation

Use the image-generation or image-editing API/account configured for the current task. WindowPet does not require a specific provider or built-in tool. Generate one complete character image for every frame, using the supplied reference image or canonical base as an image input.

Do not paste glasses, wands, stars, badges, emoji, icons, props, separate PNGs, or other stickers over a static character to fake an action. Do not use vector overlays, UI compositing, or a transform-only pipeline. The character's body, face, limbs, expression, clothing, hair, tail, ears, or held prop must be redrawn/edited as part of the complete frame.

Compose the GIF or frame folders only after all full-frame images have been generated and visually inspected. If the configured provider cannot use the reference image for image generation/editing, stop and ask for a compatible provider instead of falling back to icon compositing.

## Research before drawing

Identify the character from the user's image and text. When the character or franchise is recognizable and search tools are available, research 3-5 well-known gestures, habits, expressions, signature poses, or prop interactions. Use that research only to choose motion ideas; never copy somebody else's frames.

If the character is original or cannot be identified, infer actions from visible anatomy, personality, clothing, props, and the user's description. Do not invent a different appearance.

Write a short action plan before drawing:

```text
Character identity:
Stable visual traits:
Classic/signature action candidates:
idle:
left_click / click:
left_drag / drag:
manual named actions (optional):
```

## Required default action concepts

Adapt these concepts to the character instead of using generic scale animation:

| Output | Runtime entry | Required motion concept |
|---|---|---|
| `idle` | default state | breathing through chest/shoulder/ear/tail movement, blink, and small weight shift; do not pulse the whole image |
| `click` | left click | touched reaction: local squash, blink/recoil, paw/hand response, then recovery |
| `drag` | left-drag hold | stable picked-up/suspended loop with changed limbs and body tension; do not include falling or landing in this looping folder |

`idle`、`click` and `drag` are the only independently drawn basic folders. There is no hover, double-click, right-click, wheel, middle-click, release, random, edge, or reward action trigger. Right-click only opens the menu.

Additional character actions such as `waving`, `dance`, `feather-tickle`, `whip-hit`, `fall`, or `land` are optional named animation folders. Give each one a human-readable `label` (for example `"挥挥手"`) in `animations.<name>` or `action_labels.<name>`. The runtime lists them under right-click “动作”; selecting one plays it once and then returns to `idle`. Do not use `interaction_bindings` to make these actions automatic.

## Six-frame motion arc

Six frames are the default, not six copies:

1. neutral pose with visible anticipation;
2. preparation begins;
3. motion develops;
4. main action/key pose;
5. overshoot, secondary motion, or reaction;
6. settle, recovery, or loop connection.

Every adjacent frame must include a meaningful change in pose, limbs, face, body shape, ears, tail, hair, clothing, or props. Small scale changes are allowed only as secondary squash-and-stretch after the pose changes.

Reject the action if the frames are the same drawing merely enlarged, reduced, moved, rotated, faded, or shaken.

## 中文硬性规则

必须一帧一帧画动作。先查角色的经典动作，再给 `idle`、`click` 和 `drag` 分别写动作分镜。每个基础动作默认六帧，至少包含预备、主动作和收势；相邻帧必须出现姿势、肢体、表情、身体形变或道具变化。额外动作单独建同名文件夹，并在配置里写清中文名称；它们只能从右键“动作”菜单手动选择。只把同一张图放大、缩小、平移、旋转、透明或抖动，不算动画，必须判定失败并重做。
