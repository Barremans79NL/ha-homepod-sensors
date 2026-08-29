# Icons

App symbol for the HomePod Sensors integration: a HomePod mini body with a
thermometer (temperature) and a droplet (humidity).

| File | Size | Use |
| --- | --- | --- |
| `icon.svg` | vector | Editable source — transparent background, no tile |
| `app-icon.svg` | vector | Editable source — with rounded app tile + shadow |
| `icon.png` | 256×256 | Home Assistant [brands] `icon.png` (transparent, trimmed) |
| `[email protected]` | 512×512 | Home Assistant [brands] `[email protected]` |
| `logo.png` | 512×512 | Same mark, reusable as a logo / README image |
| `app-icon-512.png` | 512×512 | App-tile version (Shortcut icon, store art, social) |
| `app-icon-1024.png` | 1024×1024 | App-tile version, hi-res |

## Getting the icon into Home Assistant / HACS

HA and HACS pull integration icons from the [home-assistant/brands][brands]
repository, not from this repo. To ship it:

1. Fork `home-assistant/brands`.
2. Add `custom_integrations/homepod_sensors/icon.png` and `[email protected]`
   from this folder.
3. Open a PR. Until it merges, HACS shows a generic placeholder — that is
   expected and does not affect functionality.

[brands]: https://github.com/home-assistant/brands

## Regenerating the PNGs from the SVGs (macOS)

```bash
qlmanage -t -s 1024 -o icons icons/icon.svg icons/app-icon.svg
# then trim / resize the resulting *.svg.png with Pillow or sips
```
