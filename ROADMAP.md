# Roadmap

Planned work for this fork, roughly in priority order. Shipped items move to
`CHANGELOG.md`.

## Restore the last reading across restarts and updates

### Problem

The integration is purely push-driven: readings live only in
`HomePodCoordinator.data`, in memory. Any config-entry reload clears that dict —
a Home Assistant restart, a HACS update (HACS reloads the entry), or an options
change (the update listener calls `async_reload`). `async_load_stored_devices()`
then re-creates the entities from the `Store`, but the `Store` holds only
`serial` + `name`, never readings. So after every reload the temperature and
humidity sensors sit at `unavailable` and the `Stale` binary sensor at `on`
until the next scheduled webhook POST arrives — **up to one full
`update_interval`**.

Observed on the 1.1.0 update (times Europe/Amsterdam, `update_interval` = 60):

| time | event |
| --- | --- |
| 21:56:25 | HACS finished downloading 1.1.0, files swapped on disk |
| 21:57:00 | entry reloaded → `sensor.*` went `unavailable`, `binary_sensor.*_stale` → `on` |
| 22:01:05 | next iOS Shortcut POST → values restored |

That reload happened to land ~4 min before a push; an earlier reload at 17:10
stayed blank until 17:22. Worst case is the whole push interval. There were no
errors in the log — this is the documented current behaviour, not a 1.1.0
regression.

### Proposal

Rehydrate entities from Home Assistant's own restore-state store when they are
added, so they come back showing their last value immediately and the existing
staleness rules decide whether that value is still trustworthy.

1. **`HomePodMeasurementSensor`** (temperature, humidity): mix in
   `RestoreSensor`; in `async_added_to_hass` read `async_get_last_sensor_data()`
   and seed the value + unit.
2. **`Last Updated` sensor**: mix in `RestoreEntity`; restore the ISO timestamp
   from its last state so the staleness threshold is correct from the first tick
   after a reload.
3. From whichever entity restores first, feed the restored
   `(value, timestamp)` back into `coordinator.data[serial]` as a
   `HomePodDeviceData` flagged `restored=True`, so `available`, the `Stale`
   binary sensor and `Last Updated` all derive from one consistent model instead
   of each entity restoring in isolation.
4. `staleness.is_stale` already handles an old timestamp: a restored reading
   older than `interval x DEFAULT_STALENESS_MULTIPLIER` still resolves to
   `unavailable` / `Stale`, so a genuinely dead feed does not get papered over.

Leave the `Store` untouched (serial + name only). Restore-state is Home
Assistant's mechanism and already survives restarts; the integration should not
start writing readings into its own `Store`.

### Not doing

- Persisting readings in `helpers.storage.Store` — duplicates restore-state and
  breaks the deliberate "never store readings" rule.
- Polling or a synthetic keepalive — the integration is push-only by design.

### Acceptance criteria

- After `hass.config_entries.async_reload(<entry>)` with no intervening webhook,
  a previously-fresh sensor reports its last value, not `unavailable`.
- After a reload where the last reading is older than the stale threshold, the
  sensor still reports `unavailable` and `Stale` is `on`.
- `tests/test_sensor.py` covers both paths using `mock_restore_cache`
  (or `mock_restore_cache_with_extra_data` for the native value + unit).

### Follow-up

- `README.md`: note that a restart or update blanks the sensors until the next
  scheduled push. Still true after this change when the interval is long, just
  much shorter in the common case.
