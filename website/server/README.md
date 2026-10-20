# WindowPet Mock Cloud API

This is the smallest account, campaign, and cloud-sync backend for the WindowPet website MVP.

It intentionally uses only Node built-ins, so it can run now without buying a server or adding a database dependency. The data is persisted to `server/.data/sync-db.json`. When a real cloud server is ready, the same API shape can be moved to a database-backed service.

## Run

```bash
npm run api
```

The API listens on:

```txt
http://127.0.0.1:8787
```

## Smoke Test

Run the API first, then:

```bash
npm run api:smoke
```

## MVP Endpoints

```txt
GET  /api/health
GET  /api/auth/providers
GET  /api/store/pets
GET  /api/store/packages
GET  /api/store/packages/:code
POST /api/submissions
GET  /api/submissions/:id?token=:trackingToken
GET  /api/submissions/:id/package
GET  /api/submissions/:id/demo
GET  /api/admin/submissions
POST /api/admin/submissions/:id/review
POST /api/auth/email-code
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
POST /api/auth/mock-login
GET  /api/admin/egg-codes
POST /api/admin/egg-codes/batch
POST /api/admin/egg-codes/:code/status
GET  /api/campaign/egg-draw/status
POST /api/campaign/egg-draw
POST /api/campaign/egg-redeem
GET  /api/sync/:userId?deviceId=:deviceId
PUT  /api/sync/:userId/devices/:deviceId
POST /api/sync/:userId/installations
```

## 角色投稿审核

官网的“角色投稿”页面使用 `multipart/form-data` 提交自动生成的 `packageFile`（`.wpet` 或 `.zip`）和 `demoVideo`（`.mp4`）。页面会把静态图、待机、单击、拖拽以及可选的思考、回答、补充动作打包成一个角色包；角色名称、创作者、联系邮箱、至少 20 字说明、版权/授权说明和授权确认也必须填写。角色包限制 120 MB，演示 MP4 限制 100 MB。抖音号、B 站名称/UID 和 QQ 号通过 `douyin`、`bilibili`、`qq` 字段作为可选创作者资料保存。

投稿会先写入 `server/.data/submission-uploads` 并进入 `pending_review`，不会自动出现在公开角色列表。管理员使用 `X-WindowPet-Admin-Token` 调用审核接口，将状态改为 `approved` 后，投稿才会加入 `/api/store/pets`、生成公开下载地址，并可直接导入 WindowPet；`rejected` 和 `changes_requested` 均不会公开。投稿返回的 `trackingToken` 只展示一次，用于查询自己的审核状态和在审核期间预览文件。

登录用户的投稿会记录 `userId` / `userEmail`，可用 `GET /api/me/submissions` 查看自己的投稿；创作者资料通过登录后的 `PATCH /api/auth/profile` 保存。游客仍然可以投稿，并使用返回的 `trackingToken` 查询状态。

当前候选 API 使用本地文件存储和管理员口令，正式上线前需要替换为真实对象存储、管理员账号、病毒扫描、邮件通知和审计日志。

Production email-code registration sends the code through Resend using `WINDOWPET_RESEND_API_KEY`, `WINDOWPET_EMAIL_FROM`, and `WINDOWPET_EMAIL_FROM_NAME`. The API does not return the code to clients in production. Local-only testing can return `devCode` only when `NODE_ENV=development`, `WINDOWPET_ALLOW_DEV_EMAIL_CODE=true`, and `WINDOWPET_RETURN_DEV_CODE=true`.

`/api/auth/providers` reports only configured capabilities. The current MVP supports password login and email-code registration. WeChat QR and SMS remain disabled until provider credentials, callback validation, rate limits, abuse monitoring, and account-linking rules are configured.

The egg campaign now uses admin-managed redeem codes. Local data starts with the demo code `XBG-2026`; the admin token is `WINDOWPET_ADMIN_TOKEN` or `windowpet-admin-local`. Admins can list codes, batch-generate codes, and enable/disable individual codes. Logged-in users redeem codes through `/api/campaign/egg-redeem`; successful records are written to `eggRedemptions`.

## Data Boundary

Store/catalog fields live under `packages`.

Account ownership fields live under `installs`.

Per-device desktop runtime fields live under `deviceStates`, including position, scale, opacity, speed, current animation, accessory selection, and memo state.

Account login fields live under `users`. Passwords are stored as salted scrypt hashes, and API responses should use the public user object rather than returning `passwordHash`, `salt`, or `sessions`.

Redeem-code inventory lives under `eggCodes`, and user redemption history lives under `eggRedemptions`. Legacy `eggClaims` data is still normalized for local compatibility only.
