# HomePod Sensors for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)

Expose your **HomePod Mini temperature and humidity sensors** in Home Assistant.

Apple enables the HomePod Mini's built-in sensors in the Apple Home app but deliberately blocks third-party access via the HomeKit Controller API. This integration bridges the gap using an **iOS Shortcuts automation** that pushes sensor data to a Home Assistant webhook every 5 minutes (configurable).

---

## Features

- 🌡️ **Temperature sensor** per HomePod Mini
- 💧 **Humidity sensor** per HomePod Mini
- ⚠️ **Stale data sensor** — alerts when iOS has stopped pushing updates
- 🔍 **Auto-discovery** — new HomePods appear automatically when they first report in
- ⚙️ **Configurable interval** — set how often the Shortcut runs (1–60 min)
- 📦 **Zero dependencies** — no extra Python packages required
- 🏠 **Local push** — data never leaves your home network

---

## Requirements

- Home Assistant 2024.1 or newer
- [HACS](https://hacs.xyz) installed
- An iPhone or iPad on the same Apple Home as your HomePod Mini(s)
- iOS 16.2 or newer (for HomePod sensor access in Shortcuts)

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → **⋮** → **Custom repositories**
2. Add `https://github.com/pujux/ha-homepod-sensors` as an **Integration**
3. Search for **HomePod Sensors** and install
4. Restart Home Assistant

### Manual

Copy `custom_components/homepod_sensors/` to your HA `config/custom_components/` directory and restart.

---

## Setup

### Step 1 — Add the Integration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **HomePod Sensors**
3. Note the **webhook URL** displayed (you'll need it in Step 2)
4. Set your preferred update interval (default: 5 minutes)
5. Click **Submit**

> **Optional shared secret:** after setup, open the integration's **Configure**
> dialog to set a secret. When set, the Shortcut's JSON body must include a
> matching `"secret"` field or the webhook returns `401`. Leave it blank to
> disable. The webhook is also registered `local_only`, so the iPhone must be
> on the home network (or reach HA over VPN).

### Step 2 — Create the iOS Shortcut

There is no prebuilt `.shortcut` template yet — build it manually:

1. Open the **Shortcuts** app on your iPhone
2. Tap **Automation** → **+** → **Time of Day**
3. Set it to run every **5 minutes** (or your chosen interval), repeat daily
4. Add the following actions in order:

**Action 1: Get details of Home**
- Action: *Get details of home*
- Select your HomePod Mini → pick **Current temperature** and **Current humidity**
- Repeat for each HomePod Mini you want to track

**Action 2: Get Contents of URL**
- URL: *(paste your webhook URL from Step 1)*
- Method: **POST**
- Request Body: **JSON**
- Add a JSON body like this (adjust for each device):

```json
{
  "devices": [
    {
      "serial": "REPLACE_WITH_SERIAL",
      "name": "Living Room HomePod",
      "temperature_c": [Temperature variable from Action 1],
      "humidity_pct": [Humidity variable from Action 1]
    }
  ]
}
```

> If you set a shared secret in Step 1, add a top-level `"secret": "…"` field
> alongside `"devices"`.

> **Finding your HomePod serial**: Open the **Home** app → tap your HomePod → tap the ⚙️ icon → scroll to *Serial Number*.

5. Tap **Done** and enable the automation

### Step 3 — Verify

Run the Shortcut once manually (tap ▷ in the Automation tab). Within a few seconds, devices should appear under **Settings → Devices & Services → HomePod Sensors**.

---

## Entities

Each HomePod Mini device gets:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.<name>_temperature` | Sensor | Room temperature (°C) |
| `sensor.<name>_humidity` | Sensor | Relative humidity (%) |
| `sensor.<name>_last_updated` | Sensor | Last push time (diagnostic, hidden by default) |
| `binary_sensor.<name>_stale` | Binary sensor | ON if no update received in >3× the interval |

---

## Example Automations

**Alert when data stops arriving:**
```yaml
automation:
  - alias: "HomePod sensor stale alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_homepod_stale
        to: "on"
        for: "00:05:00"
    action:
      - service: notify.mobile_app
        data:
          message: "HomePod sensor data is stale — check your iOS Shortcut"
```

**Climate control based on HomePod temperature:**
```yaml
automation:
  - alias: "Cool down living room"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_homepod_temperature
        above: 25
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.living_room_ac
        data:
          temperature: 22
```

---

## Troubleshooting

**No devices appearing after running the Shortcut**
- Check that your HA webhook URL is reachable from your iPhone (try opening it in Safari)
- Ensure the JSON body in your Shortcut includes `serial`, `name`, `temperature_c`, and `humidity_pct`
- Check HA logs: **Settings → System → Logs** → search for `homepod_sensors`

**Webhook returns 401 / 405, or pushes fail when away from home**
- `401` — the request's `"secret"` does not match the one set in the integration's Configure dialog
- The webhook is `local_only`; when the iPhone is on cellular it must reach HA over VPN

**Sensors show as unavailable**
- The integration has not received data yet — run the Shortcut manually once to populate initial values

**Stale sensor is always ON**
- Your iOS Shortcut may not be running. Check **Shortcuts → Automation** and ensure it is enabled and not paused by iOS Low Power Mode

---

## Version History

| Version | Changes |
|---------|---------|
| 1.0.0 | Initial release — webhook bridge, auto-discovery, temp/humidity/stale entities |

---

## License

MIT — see [LICENSE](LICENSE). This is a fork of
[pujux/ha-homepod-sensors](https://github.com/pujux/ha-homepod-sensors);
copyright is shared with the original contributors.
