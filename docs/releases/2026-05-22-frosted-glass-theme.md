# 2026-05-22 Frosted Glass Theme

## Change

- Added a blue-white frosted glass visual theme aligned with the new paw icon.
- Updated the real PySide6 desktop control surfaces:
  - `window_pet_app/constants.py`
  - `window_pet_app/style_utils.py`
  - `window_pet_app/control_panel.py`
- Updated the product console design mockup:
  - `docs/cockpit_console_mockup.html`
- Kept the theme practical for tool use: translucent cards, blue glass borders, soft controls, readable list panels, and unified menu/dialog colors.

## Preview

- Control panel preview image:
  - `docs/releases/2026-05-22-frosted-glass-control-panel-preview.png`
- HTML concept preview:
  - `docs/cockpit_console_mockup.html`
- Browser screenshot of the HTML preview:
  - `docs/releases/2026-05-22-frosted-glass-html-preview.png`

## Build And Sync

- Rebuilt the executable with:
  - `py -3.11 -m PyInstaller WindowPet.spec --clean --noconfirm`
- Synced the rebuilt executable to:
  - `03_Windows运行版/Window Pet.exe`

## Verification

- `py -3.11 -m compileall window_pet_app` passed.
- PyInstaller build completed successfully.
- PyInstaller log confirmed `Copying icon to EXE`.
- The rebuilt source exe and runtime exe were both `101529543` bytes after sync.
- A Qt offscreen render of the control panel completed and produced the preview image listed above.
- A Playwright browser screenshot of `docs/cockpit_console_mockup.html` completed and produced the HTML preview image listed above.

## Notes

- This is a Qt stylesheet frosted-glass theme, so it simulates glass through translucent blue-white surfaces and soft borders.
- A true Windows Acrylic/Mica material would require deeper Windows composition integration and should be handled as a separate implementation step.
