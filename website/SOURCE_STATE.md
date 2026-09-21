# 官网与 API 候选源码状态

- 本目录属于 `1.0.32 candidate` 开发工作区，尚未部署。
- 官网页面中的正式下载版本仍为 `1.0.31`。
- 候选 `server/mock-cloud-api.mjs` SHA256：`959b695102d4ecf81006033442d2c97abbe9603e7626d5f4eb8564bf4f246ed9`。
- 当前生产 API SHA256：`5796cf50c6c02c88a5fe89e142e4bb2c85e1aa4c91ca1c195836f523166b450e`。
- `package.json`、`package-lock.json`、官网 UI 和 API 均应按候选代码重新测试，不能沿用旧的“与线上一致”结论。
- `node_modules`、`dist`、`preview_logs`、`server/.data`、生产 `.env` 和下载 ZIP 不进入 Git。

正式生产官网/API 的交接快照另存于 `04_官网_API与Git/官网_API源码基线`。

