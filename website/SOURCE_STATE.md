# 官网与 API 候选源码状态

- 本目录属于候选开发工作区，尚未部署；当前桌面候选源码元数据为 `1.0.33`。
- 官网页面中的正式下载入口仍指向已发布的稳定版 `1.0.32`，直到新版本完成审核和发布。
- `website/src/releaseConfig.ts` 是官网各下载入口的唯一版本来源；发版脚本只在隔离副本中更新它。
- 候选 `server/mock-cloud-api.mjs` SHA256：`783fa8d6e303dbebb1d25cd3ea823f1f2d9eb4543b18439802921dbc210cc95c`。
- 当前生产 API SHA256：`5796cf50c6c02c88a5fe89e142e4bb2c85e1aa4c91ca1c195836f523166b450e`。
- `package.json`、`package-lock.json`、官网 UI 和 API 均应按候选代码重新测试，不能沿用旧的“与线上一致”结论。
- 候选官网已增加角色投稿页面和审核 API：投稿包与 MP4 进入 `pending_review`，管理员通过后才加入公开角色目录并提供可直接导入的下载地址。
- `node_modules`、`dist`、`preview_logs`、`server/.data`、生产 `.env` 和下载 ZIP 不进入 Git。

正式生产官网/API 的交接快照另存于 `04_官网_API与Git/官网_API源码基线`。

