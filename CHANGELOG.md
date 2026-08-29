# Changelog

All notable changes to this integration are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
follows [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-08-29

The integration now ships its own icon to Home Assistant directly — no
`home-assistant/brands` pull request required.

### Added

- **`brand/` folder** in `custom_components/homepod_sensors/`, holding
  `icon.png` and `icon@2x.png`. Home Assistant 2026.3+ serves these through the
  [brands proxy API](https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/)
  at `/api/brands/integration/homepod_sensors/{image}`, and local brand images
  take priority over the brands CDN. This resolves the placeholder-icon note
  from 1.1.0. On older Home Assistant the folder is ignored (cosmetic only).

### Fixed

- Source file `icons/[email protected]` was committed under a mangled
  name; renamed to `icons/icon@2x.png`.

## [1.1.0] - 2026-08-29

Quality-of-life release: the setup and options dialogs are now available in
Dutch, and the integration finally has its own icon. No changes to how sensor
data is received or processed — upgrading is safe and needs no reconfiguration.

### Added

- **Dutch translation (`nl`).** The config flow, options flow, entity names
  (Temperatuur, Luchtvochtigheid, Laatst bijgewerkt) and the staleness binary
  sensor (Verouderd / Actueel) now render in Dutch when Home Assistant is set to
  that language. English remains the default and fallback.
- **Integration icon.** A HomePod mini mark with a thermometer and humidity
  droplet, shipped as SVG source plus rendered PNGs under `icons/`
  (`icon.png`, `icon@2x.png`, `logo.png`, and app-tile variants). See
  `icons/README.md` for how the icon reaches Home Assistant. (1.1.0 shipped
  the sources only, so HA and HACS still showed a placeholder; 1.2.0 wires it
  up.)

### Changed

- `.gitignore` now excludes `.DS_Store`.

## [1.0.0] - 2026-08-29

Initial release of this fork.

### Added

- Push-driven HomePod mini temperature and humidity sensors, fed by an iOS
  Shortcut that POSTs JSON to a Home Assistant webhook on a schedule.
- Config flow (update interval) and options flow (update interval + optional
  shared secret). Single instance; it manages every HomePod mini in your Home.
- Per-device entities added dynamically as new serials appear in the payload,
  including a `Last Updated` timestamp sensor and a `Stale` problem binary
  sensor.
- Staleness handling: sensors report `unavailable` once no push has arrived for
  3x the configured interval; the binary sensor turns on.
- Out-of-range and malformed readings are dropped per device without failing the
  whole payload.
- Device names follow renames made in the Apple Home app unless you have set your
  own name in Home Assistant.
- Device list (serial + name only, never readings) is persisted, so entities
  come back after a restart and report `unavailable` until the next push.
