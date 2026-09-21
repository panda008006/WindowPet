# Reference image first mode / 参考图优先模式

This rule is mandatory whenever the user supplies a character image.

## Source of truth

The original attached image is the character's only visual source of truth. It is not a mood board or a loose style reference.

- Inspect and extract the supplied image before creating any animation.
- Preserve the exact silhouette, body proportions, face, markings, colors, line weight, accessories, asymmetrical details, and transparent/background treatment.
- Do not redraw, redesign, beautify, simplify, reinterpret, or replace the character with a text-only lookalike.
- If the image contains one pose, use that pose as the canonical idle/base frame.

## Frame-by-frame workflow

Every action must be made from the extracted canonical character, one frame at a time.

1. Extract/clean the supplied image and make the canonical base frame.
2. Attach the original reference image or canonical base to every action-generation task.
3. Change only the pose, expression, or prop motion required by the action.
4. Keep the same canvas anchor, scale, bounding box, palette, outline, face, and identity in every frame.
5. Compare all frames against the original before packaging. Reject any frame that looks like a newly invented character.

Never generate an action row from text alone when a reference image exists. “Make a similar character” is not acceptable. If the visual tool cannot access the attached image, stop and ask the user to attach it again instead of inventing a replacement.

## 中文硬性规则

用户给了角色图片时，图片就是唯一视觉真源，不是参考灵感。必须先提取原图，再以提取出的角色为基础逐帧制作 `idle`、`click`、`drag`；需要的 `waving`、`dance`、`feather-tickle` 等额外动作单独制作，并在右键“动作”菜单中按名称提供。每一帧都要保持原图的轮廓、比例、脸部、颜色、线条、配饰和不对称细节，只改变动作需要改变的姿势或表情。禁止脱离图片重新画一只“相似角色”；如果 AI 无法访问原图，必须暂停并要求重新附图。
