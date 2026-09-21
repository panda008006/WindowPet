# WindowPet Official Site and API Candidate

> Handoff status: this directory belongs to the undeployed `1.0.32 candidate` workspace. The website still publishes the formal desktop release `1.0.31`. Read `SOURCE_STATE.md` before changing or deploying it.

This is the first runnable product surface for WindowPet:

- official website
- pet-pack store
- email registration/login through the local Mock Cloud API
- redeem-code egg campaign with admin-managed code inventory
- account authorization and download-token demo
- local cloud-sync API prototype
- admin-console preview

## Run The Website

```bash
npm install
npm run dev
```

Default Vite URL:

```txt
http://127.0.0.1:5173/pet/
```

## Run The Mock Cloud API

Open another terminal:

```bash
npm run api
```

The API listens on:

```txt
http://127.0.0.1:8787
```

Vite proxies `/pet-api/*` to this API during local development. Data is persisted locally in `server/.data/sync-db.json`, which is ignored by git.

Local account testing uses the development email code `246810` unless `WP_DEV_EMAIL_CODE` is set. The local redeem-code demo starts with `XBG-2026`, and the admin panel uses `windowpet-admin-local` unless `WINDOWPET_ADMIN_TOKEN` is set. No payment flow is included in this website MVP.

## Verify API

```bash
npm run api:smoke
```

The smoke test covers health, store catalog, email-code registration, password login, admin code generation, redeem-code egg claim, and device-state sync.

## Pet Package Spec

The current website catalog is based on the verified assets in `../01_桌面端源码_WindowPet/assets`.
See `docs/pet-package-spec.md` for the `.wpet` folder format, minimum `asset.json`,
review rules, and backend field contract.

## 2026-05-23 Promotional Download Refresh

The public homepage has been simplified into a promotional download page inspired by the structure of public game landing pages:
fixed top navigation, full-screen hero, one primary download CTA, a small version strip, three official roles, highlights, and download details.
The visual direction is now light-blue frosted glass with animated pet previews.
The highlights section now uses a richer product-experience layout: a Cockpit preview panel plus three concrete install benefits covering animated companions, the large control console, and the update/download channel.

The current visible protagonists are `JiyiPet` / 吉伊, `NuonuoPet` / Dora, and `HuhuPet` / 狐狸. Their preview PNGs are copied into `public/pets`.
Animated WebP previews are generated from the desktop `waving` action frames:

- `public/pets/jiyi-animated.webp`
- `public/pets/dora-animated.webp`
- `public/pets/fox-animated.webp`

Reference capture for lawful layout study only:

```txt
output/captures/pvpqq-sample/
```

Do not reuse Tencent images, logos, text, scripts, or bundled assets. The published Window Pet page uses project-owned pet assets and original copy.

## 2026-05-23 Fullscreen Snap Redesign

The homepage has been rebuilt from a long module page into a four-screen promotional flow modeled on the interaction idea of the PVP QQ public homepage, implemented from scratch:

1. `#home` is a full-screen hero with a replaceable visual background area, primary download CTA, and animated 吉伊 / Dora / 狐狸 lineup.
2. `#pets` is an interactive role-selection screen. Clicking 吉伊、Dora or 狐狸 updates the large animated display, copy, tags, action coverage, and resource stats.
3. `#features` presents concrete desktop functions as an interface preview: 备忘录、闹钟、提醒队列 and desktop interaction.
4. `#control` shows the large `Window Pet Cockpit` concept plus the current Windows package download panel.

Desktop wheel scrolling is section-locked through the React page shell, with CSS scroll snap as the layout base. Mobile keeps a natural scrolling flow with the same sections. Verification artifacts:

- `output/playwright/windowpet-fullpage-hero.png`
- `output/playwright/windowpet-fullpage-desktop.png`
- `output/playwright/windowpet-fullpage-features.png`
- `output/playwright/windowpet-fullpage-mobile.png`
- `output/playwright/fullpage-check.mjs`

Historical note from the 2026-05-23 website-only redesign: that task did not repack the desktop download or `latest.json`. It mentioned `window-pet-1.0.14.zip` as the then-current release. The current formal release is now `window-pet-1.0.31.zip`; use the handoff manifest as the source of truth.

Deployed public URL: `http://124.222.41.82/pet/`
Remote backup before deployment: `/www/wwwroot/apps/window-pet/backups/public-20260523-114331-fullpage-snap`
Remote verification passed with `node output\playwright\fullpage-check.mjs http://124.222.41.82/pet/`.

2026-05-23 client-facing interaction update: the role-section copy was changed from internal design notes to visitor-facing product copy. Each protagonist now exposes three clickable action previews instead of a long static action list. 吉伊 uses 挥手 / 演奏 / 害羞, Dora uses 挥手 / 跳跃 / 羽毛逗弄, and 狐狸 uses 挥手 / 羽毛逗弄 / 鞭子命中. The Cockpit preview in `#control` also has three clickable views: 角色管理、动作调试、更新中心. New action preview assets are `public/pets/*-action-*.webp`. Deployed to `http://124.222.41.82/pet/` after remote backup `/www/wwwroot/apps/window-pet/backups/public-20260523-144648-client-interactions`; remote Playwright verification passed.

2026-05-23 customer-copy pass: rewrote the homepage copy for ordinary download users. The page now emphasizes companionship, light reminders, practical desktop tools, and simple control, instead of internal terms such as resource packs, canvases, or implementation details. Deployed to `http://124.222.41.82/pet/` after remote backup `/www/wwwroot/apps/window-pet/backups/public-20260523-231822-customer-copy`; remote Playwright verification passed.

## Production Migration Notes

When a cloud server is ready:

- replace `http://127.0.0.1:8787` with the real API domain
- move `server/mock-cloud-api.mjs` data storage from JSON to a database
- wire `/api/auth/email-code` to a real email provider
- keep redeem-code generation, status changes, and redemption records behind the admin backend
- put package files in private object storage
- generate short-lived download links from the backend
- add payment later only if the product plan needs it; this version intentionally has no payment integration
