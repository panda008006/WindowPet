# WindowPet AI 接手规则

本目录是 `1.0.32 candidate` 的继续开发工作区，不是线上正式版。线上正式版仍为 `1.0.31`。

开始任何工作前：

1. 读取 `SOURCE_STATE.md`、根目录 `README.md` 和 `website/SOURCE_STATE.md`。
2. 运行 `git status`，不要覆盖接手人或其他代理已有修改。
3. 桌面端修改后运行 `py -3.11 -m pytest -q`。
4. 官网/API 修改后在 `website` 运行 `npm ci`、`npm run lint`、`npm run build`，并启动 API 后运行 `npm run api:smoke`。
5. 不得读取、提交或输出私钥、`.env`、Token、用户数据和验证码。
6. 不得自行发布或修改生产。云端操作先使用交接包中的状态脚本和计划模式；只有获得负责人明确批准后才能使用 `-Apply`。

云服务器目录、SSH 别名和发布边界以项目包根目录的 `handoff.manifest.json` 为准。

## AI 角色制作入口

当用户要求新建、修改或扩展 WindowPet 角色时，必须先完整阅读 `AI角色制作/AI先读我.md`，再开始生成图片或修改 JSON。

如果当前环境提供 `hatch-pet-window-pet` skill，应使用该 skill 的角色一致性、透明背景、打包和视觉检查流程；帧数与平台边界以本软件的 `AI角色制作/质量标准.json` 为准。

- 新角色只能放在 `assets/<角色英文名Pet>/`。
- 不要修改或替换 `Window Pet.exe`。
- 不要覆盖现有角色，除非用户明确指定该角色。
- 完成后运行：`python AI角色制作/validate_character.py assets/<角色英文名Pet>`。
- 校验通过后，向用户说明角色目录、动作数量和仍存在的警告。
