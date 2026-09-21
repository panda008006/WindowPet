# 2026-05-22 Fox And Feather Library Fix

## Change

- Removed `ToolAssets` from the visible pet asset library so the small feather stays a tool only and no longer appears as a role/character.
- Kept the feather asset in the packaged runtime for the feather tool.
- Renamed the standing fox to `呼呼` in the asset metadata and runtime config.
- Renamed the other fox entry from a broken `??` label to `小狐` so the library no longer shows a garbage name.

## Code And Data

- Updated scanning logic in `window_pet_app/assets.py` to skip `ToolAssets` in asset packs and root asset listings.
- Updated:
  - `assets/HuhuPet/asset.json`
  - `assets/Huhu2Pet/asset.json`
  - `config.json`
- Synced the same fox metadata to the runtime bundle.

## Verification

- `py -3.11 -m compileall window_pet_app` passed.
- `py -3.11 -m pytest tests/test_asset_library_visibility.py` passed.
- Runtime asset scan confirmed:
  - `ToolAssets` is not in the visible pack list.
  - `feather_premium` is not in the visible root asset list.
  - `assets/Huhu2Pet` is named `呼呼`.
  - `assets/HuhuPet` is named `小狐`.

## Build

- Rebuilt `Window Pet.exe` and copied it to the runtime bundle.

