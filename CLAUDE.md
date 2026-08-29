# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant **custom integration** (HACS, domain `homepod_sensors`) that surfaces HomePod
mini temperature/humidity in HA. Apple blocks these sensors from the HomeKit Controller API, so
data arrives out-of-band: an iOS Shortcut POSTs JSON to a HA **webhook** on a schedule. The
integration is therefore **purely push-driven** — there is no polling anywhere.

Ships only `custom_components/homepod_sensors/`. `pyproject.toml` exists for the dev toolchain, not
because the package is meant to be pip-installed at runtime.

## Environment & commands

There is no system Python here. Create a 3.12 venv and install dev deps:

```bash
uv venv --python 3.12 --seed .venv
.venv/bin/pip install -e ".[dev]" --config-settings editable_mode=compat
```

`editable_mode=compat` is **required**: the modern setuptools editable hook puts a synthetic
`__editable__.*.finder.__path_hook__` entry on `sys.path` that HA's integration loader walks with
`os.listdir` and crashes on (`FileNotFoundError`). CI (`.github/workflows/ci.yml`) passes the same
flag.

```bash
.venv/bin/python -m pytest tests/ -q          # full suite
.venv/bin/python -m pytest tests/test_coordinator.py -q
.venv/bin/python -m pytest tests/test_sensor.py -q -k stale   # single test / pattern
.venv/bin/ruff check .                          # lint (CI runs this; must be clean)
.venv/bin/ruff check . --fix
```

CI runs `ruff check .` then `pytest tests/ -v` on Python 3.12.

### Releasing

`release.yml` fires on a `v*` tag push. It extracts the `## [X.Y.Z]` section from `CHANGELOG.md`
that matches the tag and uses **only that** as the GitHub Release body — the job *fails* if there
is no matching section. Steps for version `X.Y.Z`:

1. Bump the version in **both** `custom_components/homepod_sensors/manifest.json` and
   `pyproject.toml` — keep them identical.
2. Add a `## [X.Y.Z] - <date>` section to `CHANGELOG.md` (Keep a Changelog style).
3. Commit to `main`, push.
4. `git tag -a vX.Y.Z -m vX.Y.Z && git push origin vX.Y.Z` — the tag must sit on `main`.

HACS offers the update to users straight from that published GitHub Release, so the workflow run
has to actually succeed.

- **Fork gotcha:** this repo is a fork of `pujux/ha-homepod-sensors`. GitHub disables Actions on
  forks by default; the owner enabled them on 2026-08-29 and confirmed `release.yml` now runs. If
  the API / Actions tab shows **zero** workflow runs, Actions was switched off again — re-enable
  it on the repo's Actions tab. There is no other trigger: `release.yml` has no
  `workflow_dispatch`.
- **Re-triggering a release** whose tag already exists on the remote (e.g. Actions was off the
  first time it was pushed): delete the remote tag, then push it again —

  ```bash
  git push origin :refs/tags/vX.Y.Z
  git push origin vX.Y.Z
  ```

## Architecture

Data flow: **iOS Shortcut → HA webhook (`webhook.py`) → `HomePodCoordinator` → entities**.

- **`__init__.py`** — `async_setup_entry` builds the coordinator, calls
  `async_load_stored_devices()`, then registers the webhook as
  `partial(async_handle_webhook, coordinator, entry)` with `local_only=True`. The options-update
  listener does a full `async_reload` so a changed interval/secret takes effect immediately.
  - **Gotcha:** HA's webhook module is imported as `ha_webhook`. Importing the local `.webhook`
    submodule binds the name `webhook` on the package and would shadow a plain
    `from homeassistant.components import webhook`. Do not "simplify" this back.

- **`coordinator.py`** — `HomePodCoordinator` extends `DataUpdateCoordinator` only to reuse its
  listener plumbing; `_async_update_data` is a deliberate no-op. `data: dict[serial,
  HomePodDeviceData]`. `handle_webhook_payload` is the core: per device it validates required
  fields → `float()` in a guarded block → plausibility range check (`MIN/MAX_*` in `const.py`);
  any failure logs and skips **that device only**. It then creates or updates the
  `HomePodDeviceData`, follows a rename from the Home app (updates the device-registry entry
  unless the user set their own name), fires `_new_device_callbacks` for brand-new serials, and
  debounce-persists the device list.
  - **Persistence** (`helpers.storage.Store`): only `serial` + `name` are saved, never readings.
    Restored devices exist as entities immediately after a restart but report `unavailable` until
    the next push.

- **`webhook.py`** — `async_handle_webhook(coordinator, entry, hass, webhook_id, request)`
  (coordinator/entry bound via `partial`; `single_instance_allowed` guarantees exactly one).
  Validates the JSON body, enforces the optional shared secret (`entry.options`/`entry.data`
  `secret` → 401 on mismatch), dispatches to the coordinator.

- **`sensor.py` / `binary_sensor.py`** — Entities are added dynamically: each platform's
  `async_setup_entry` registers a new-device callback **and** loops over already-known devices.
  Class hierarchy carries the staleness policy: `HomePodBaseSensor` (available = has a reading) →
  `HomePodMeasurementSensor` (also `not is_stale(...)`) → temperature/humidity. The `Last Updated`
  timestamp sensor extends the **base** directly so it stays readable when stale;
  `HomePodStaleSensor` is the `problem` binary sensor.

- **`staleness.py`** — single source of truth shared by the sensors' `available` and the binary
  sensor's `is_on`. Threshold = configured interval × `DEFAULT_STALENESS_MULTIPLIER` (3), read
  live from the config entry (options fall back to data fall back to default).

- **`const.py`** — config keys, defaults, `DEFAULT_STALENESS_MULTIPLIER`, reading range bounds,
  `STORAGE_*`.

- **`config_flow.py`** — one-step user flow (interval only; webhook id via
  `webhook.async_generate_id()`). Options flow adds interval + optional secret and reads
  `self.config_entry` (no custom `__init__`). Single instance only.

- **`translations/`** — `en.json` only; there is no `strings.json`.

## Testing notes

- `tests/conftest.py` has an autouse `enable_custom_integrations` fixture — without it every
  integration-loading test fails with "Integration not found".
- Coordinator behaviour is tested by calling `handle_webhook_payload` / `async_handle_webhook`
  directly with a bare `HomePodCoordinator(hass)` and `MockConfigEntry`. Entity/state-machine
  behaviour goes through a full `hass.config_entries.async_setup`.
- The `Last Updated` sensor is `entity_registry_enabled_default = False`, so it is absent from the
  state machine in a normal setup — assert on its `available` property directly.

## Conventions

- Apple's product name is **"HomePod mini"** (lowercase `m`) — used in the device `model`, docs,
  and strings. "HomePod Sensors" is this integration's own name and stays title-case.
- Commit style: Conventional Commits (`fix:`, `feat:`, `refactor:`, `docs:`, `ci:`, `test:`).
- `REVIEW.md` is the historical pre-fork code review; its checklist items are all addressed as of
  v1.0.0.
