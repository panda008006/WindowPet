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

Production email-code registration sends the code through Resend using `WINDOWPET_RESEND_API_KEY`, `WINDOWPET_EMAIL_FROM`, and `WINDOWPET_EMAIL_FROM_NAME`. The API does not return the code to clients in production. Local-only testing can return `devCode` only when `NODE_ENV=development`, `WINDOWPET_ALLOW_DEV_EMAIL_CODE=true`, and `WINDOWPET_RETURN_DEV_CODE=true`.

`/api/auth/providers` reports only configured capabilities. The current MVP supports password login and email-code registration. WeChat QR and SMS remain disabled until provider credentials, callback validation, rate limits, abuse monitoring, and account-linking rules are configured.

The egg campaign now uses admin-managed redeem codes. Local data starts with the demo code `XBG-2026`; the admin token is `WINDOWPET_ADMIN_TOKEN` or `windowpet-admin-local`. Admins can list codes, batch-generate codes, and enable/disable individual codes. Logged-in users redeem codes through `/api/campaign/egg-redeem`; successful records are written to `eggRedemptions`.

## Data Boundary

Store/catalog fields live under `packages`.

Account ownership fields live under `installs`.

Per-device desktop runtime fields live under `deviceStates`, including position, scale, opacity, speed, current animation, accessory selection, and memo state.

Account login fields live under `users`. Passwords are stored as salted scrypt hashes, and API responses should use the public user object rather than returning `passwordHash`, `salt`, or `sessions`.

Redeem-code inventory lives under `eggCodes`, and user redemption history lives under `eggRedemptions`. Legacy `eggClaims` data is still normalized for local compatibility only.
