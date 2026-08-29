# Icons

App symbol for the HomePod Sensors integration: a HomePod mini body with a
thermometer (temperature) and a droplet (humidity).

| File | Size | Use |
| --- | --- | --- |
| `icon.svg` | vector | Editable source — transparent background, no tile |
| `app-icon.svg` | vector | Editable source — with rounded app tile + shadow |
| `icon.png` | 256×256 | Home Assistant brand `icon.png` (transparent, trimmed) |
| `icon@2x.png` | 512×512 | Home Assistant brand `icon@2x.png` |
| `logo.png` | 512×512 | Same mark, reusable as a logo / README image |
| `app-icon-512.png` | 512×512 | App-tile version (Shortcut icon, store art, social) |
| `app-icon-1024.png` | 1024×1024 | App-tile version, hi-res |

This folder holds the **sources**. The copies Home Assistant actually serves
live in [`custom_components/homepod_sensors/brand/`](../custom_components/homepod_sensors/brand/).

## Getting the icon into Home Assistant / HACS

Since Home Assistant 2026.3 a custom integration ships its own brand images in a
`brand/` folder next to `manifest.json`; the [brands proxy API][proxy] serves
them from `/api/brands/integration/homepod_sensors/{image}` and they take
priority over anything on the brands CDN. **No PR to
[home-assistant/brands][brands] is needed.**

`custom_components/homepod_sensors/brand/` therefore contains:

| Brand file | Copied from |
| --- | --- |
| `icon.png` | `icons/icon.png` |
| `icon@2x.png` | `icons/icon@2x.png` |

Supported names are `icon.png`, `logo.png`, their `@2x` variants, and
`dark_` prefixes for dark-theme overrides. We ship only the icon; Home
Assistant falls back to it wherever a logo would be used.

On Home Assistant older than 2026.3 the `brand/` folder is ignored and the
integration shows the generic placeholder icon — cosmetic only.

Regenerate the served copies after editing the sources:

```bash
cp icons/icon.png    custom_components/homepod_sensors/brand/icon.png
cp icons/icon@2x.png custom_components/homepod_sensors/brand/icon@2x.png
```

[proxy]: https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/
[brands]: https://github.com/home-assistant/brands

## Regenerating the PNGs from the SVGs (macOS)

```bash
qlmanage -t -s 1024 -o icons icons/icon.svg icons/app-icon.svg
# then trim / resize the resulting *.svg.png with Pillow or sips
```
