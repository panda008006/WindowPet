# Third-party visual references

## OpenWhip

- Source: https://github.com/GitFrog1111/OpenWhip
- License: MIT as declared in `package.json`
- Use in this project: the `window_pet_app.whip_tool` overlay adapts only the whip visual shape and mouse-driven rope motion, recolored to light blue and connected to local pet hit detection. It does not include OpenWhip's Claude control macros, keyboard automation, Electron tray app, or sound assets.

## cursor-effects

- Source: https://github.com/tholman/cursor-effects
- License: MIT as declared in `package.json` and README.
- Use in this project: reference only for the general transparent cursor-effect pattern. The small feather tool in `window_pet_app.feather_tool` is animated natively in PySide6; no cursor-effects code or assets are copied.

## Premium feather asset

- Source: generated specifically for this project with the built-in image generation tool; original source copy is stored at `docs/feather_premium_imagegen_source.png`.
- Use in this project: `assets/ToolAssets/feather_premium.png` is a transparent, cropped light-blue feather asset. It is loaded by `window_pet_app.feather_tool` and rendered at one fifth of the active pet area.
