# Behavior Packs

Behavior packs map app events to character animation names. They are reusable across pets: a new character only needs to add matching animation folders and `asset.json` entries.

Default packs:

- `screensaver-sleep`: `screen_saver_enter` prefers `sleep`, `sleeping`, `lying-sleep`, then falls back to `waiting` or `idle`.
- `wake-stretch`: `startup` and `screen_saver_exit` prefer `stretch`, `wake-stretch`, then fall back to `waving`, `jumping`, or `idle`.

Optional per-pet override in `asset.json`:

```json
{
  "behavior_packs": {
    "screen_saver_enter": "screensaver-sleep",
    "screen_saver_exit": "wake-stretch",
    "startup": "wake-stretch"
  }
}
```

Recommended future role animation folders:

- `sleep`: looping sleeping or lying-down pose.
- `stretch`: short non-looping wake-up stretch.

The app falls back gracefully when those folders are missing.
