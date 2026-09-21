# 2026-05-23 Email Auth And Redeem-Code Handoff

## Scope

- Email registration/login is wired to the local Mock Cloud API.
- The egg activity now uses admin-managed redeem codes instead of a fixed single-code flow.
- No payment integration is included.

## Local Run

```powershell
npm run api
npm run dev
```

Vite proxies `/pet-api/*` to `http://127.0.0.1:8787`.

## Local Test Values

- Email code: `246810`
- Demo redeem code seed: `XBG-2026`
- Admin token: `windowpet-admin-local`

## Account Flow

1. Open `http://127.0.0.1:5173/pet/`.
2. Go to `账号`.
3. Switch to `注册`.
4. Click `获取验证码`.
5. Use the local code `246810`.
6. Register with a test email and password.
7. Log out and log back in with the same email/password.

## Redeem-Code Flow

1. Log in first.
2. Go to `活动`.
3. Enter `XBG-2026` or a code generated from the admin panel.
4. Click `兑换金蛋`.
5. Successful redemptions write to `eggRedemptions`, and pet rewards can be added to `我的资源`.

Disabled or exhausted codes are rejected by the backend.

## Admin Flow

1. Go to `控制台预览`.
2. Open `兑换码管理`.
3. Use the default token `windowpet-admin-local`.
4. Click `读取兑换码`.
5. Batch-generate codes, change reward targets, and enable/disable individual codes.

The current UI mirrors the paibanpai-style backend management pattern: code inventory, status control, and redemption records.

## QA Evidence

- `output/playwright/windowpet-account-logged-in.png`
- `output/playwright/windowpet-campaign-redeemed.png`
- `output/playwright/windowpet-admin-codes.png`

## Production Notes

- Replace the local email-code stub with a real mail provider.
- Move JSON persistence in `server/mock-cloud-api.mjs` to a database before launch.
- Keep redeem-code generation, status changes, and redemption records behind admin auth.
- Add payment only if the product plan really needs it.
