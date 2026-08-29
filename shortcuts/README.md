# HomePod Sensors — iOS Shortcut Template

This directory contains the iOS Shortcuts automation that bridges HomePod mini sensor data to Home Assistant.

## Import the Shortcut

There is no prebuilt `.shortcut` file to import yet. Build it manually using the
steps below.

---

## What the Shortcut Does

Every **5 minutes** (default), the shortcut:

1. Queries HomeKit for all HomePod mini accessories
2. Reads each device's **temperature** and **humidity** values
3. POSTs a JSON payload to your Home Assistant webhook URL

---

## Shortcut Actions (step-by-step)

Build a new Shortcut in the iOS Shortcuts app with the following actions:

### Action 1 — Get HomeKit accessories
```
Get HomeKit Accessories
  Filter: Type = Thermostat (HomePod mini reports as Thermostat)
  Store result in: homepods
```

### Action 2 — Build devices list
```
Set Variable: devices = []

Repeat with each item in homepods:
  Get Details of HomeKit Accessory (item)
    → Current Temperature → store as: temp_c
    → Current Relative Humidity → store as: humidity_pct
    → Accessory Serial Number → store as: serial
    → Accessory Name → store as: device_name

  Add to Variable: devices
    {
      "name": device_name,
      "serial": serial,
      "temperature_c": temp_c,
      "humidity_pct": humidity_pct
    }
End Repeat
```

### Action 3 — POST to Home Assistant
```
Get Contents of URL:
  URL: http://<YOUR_HA_IP>:8123/api/webhook/<YOUR_WEBHOOK_TOKEN>
  Method: POST
  Headers:
    Content-Type: application/json
  Body (JSON):
    {
      "devices": devices
    }
```

If you configured a shared secret in the integration's **Configure** dialog, add
it as a top-level field: `{ "secret": "<your secret>", "devices": devices }`.
The webhook is `local_only`, so the iPhone must be on the home network or reach
Home Assistant over VPN.

---

## Automation Setup

Once the Shortcut is working manually:

1. Open **Shortcuts → Automation → New Automation**
2. Trigger: **Time of Day** → Every **5 minutes** (or match your HA update interval)
3. Action: **Run Shortcut** → select *HomePod Sensors*
4. Disable "Ask Before Running" → enable "Run After Confirmation"

---

## Expected Payload

```json
{
  "devices": [
    {
      "name": "Living Room HomePod",
      "serial": "H1AB2CD3EF4G",
      "temperature_c": 21.5,
      "humidity_pct": 48.2
    },
    {
      "name": "Bedroom HomePod",
      "serial": "H5XY6ZA7BC8D",
      "temperature_c": 20.1,
      "humidity_pct": 52.0
    }
  ]
}
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| No entities appear | Run the Shortcut manually once; check HA logs |
| Temperature shows wrong | Verify HomeKit accessory type is "Thermostat" |
| Multiple devices show as one | Ensure each HomePod has a unique serial in HomeKit |
| Stale sensor turns ON | Shortcut automation may have stopped; check iOS battery optimization |

---

## Notes

- No prebuilt `.shortcut` file is published; build it manually from the steps above
- HomePod mini must be in the same Apple Home as the iOS device running the Shortcut
- iOS 16.4+ recommended; Shortcuts 5.0+
