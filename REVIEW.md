# Code review — ha-homepod-sensors (fork)

Review van commit `main` @ pujux/ha-homepod-sensors, uitgevoerd vóór het forken.
Volgorde: blockers eerst, daarna hardening, daarna nice-to-have.

---

## Blockers — fixen vóór installatie

### 1. Config flow crasht op ontbrekende placeholder
`translations/en.json` → `config.step.user.description` gebruikt **twee** placeholders:
`{webhook_url}` én `{update_interval}`.

`config_flow.py` (regel ~56) geeft er maar één mee:

```python
description_placeholders={
    "webhook_url": webhook_url,
}
```

HA rendert de beschrijving met `.format()`-achtige substitutie; de ontbrekende
`{update_interval}` levert een KeyError / lege of gebroken setup-dialoog op.

**Fix:** `"update_interval": str(DEFAULT_UPDATE_INTERVAL)` toevoegen aan de dict,
óf `{update_interval}` uit de vertaalstring halen (die waarde stelt de gebruiker
in datzelfde formulier al in — de vermelding is daar sowieso overbodig).

### 2. Entities verdwijnen na elke HA-herstart
`coordinator.py` houdt `self.data` puur in geheugen. Bij herstart is die dict leeg,
dus de lus in `sensor.py`:

```python
# Add entities for devices already known (e.g. after HA restart).
for serial in coordinator.data:
```

...loopt over niets. De comment belooft iets wat de code niet doet. Gevolg: na elke
herstart zijn temperatuur/luchtvochtigheid `unavailable` tot de volgende push
binnenkomt — met een interval van 15–30 min is dat een flink gat, en automatiseringen
die op die entities triggeren falen stil in die periode.

**Fix:** laatst bekende devices persisteren via `homeassistant.helpers.storage.Store`
(of minimaal de serials + namen, zodat entities meteen worden aangemaakt en op
`unknown` staan i.p.v. te ontbreken). `RestoreEntity` als alternatief per entity.

### 3. `float()` zonder foutafhandeling
`coordinator.py` regel ~73:

```python
self.data[serial].update(float(temp), float(humidity))
```

Malformed velden (lege string, `null` als string, tekst uit een misgeconfigureerde
Shortcut) gooien een `ValueError`/`TypeError` die de verwerking van het **hele**
payload afbreekt — terwijl ontbrekende velden er net boven wél netjes per device
worden overgeslagen. Inconsistent.

**Fix:** de conversie in de bestaande validatie-blok trekken, met `try/except
(TypeError, ValueError)` → `_LOGGER.warning` + `continue`.

---

## Hardening — aanbevolen

### 4. Webhook is niet beperkt tot het lokale netwerk
`__init__.py` roept `webhook.async_register()` aan zonder `local_only=True`.
Draait HA achter een reverse proxy met externe toegang, dan is het webhook-endpoint
vanaf internet bereikbaar. De enige beveiliging is dan de geheimhouding van de
webhook-URL.

**Fix:** `local_only=True` meegeven. Let op: de iPhone moet dan op het thuisnetwerk
zitten of via VPN binnenkomen — met WireGuard is dat gedekt, maar het betekent wel
dat pushes wegvallen als de telefoon onderweg is. Afweging: dat is precies wat je
wilt (de HomePod-waarden zijn alleen relevant als er iemand thuis is), maar het laat
de stale-sensor wel afgaan.

### 5. Geen validatie van de meetwaarden
Er is geen enkele sanity check op bereik. Een verdwaalde `-999` of `1e9` landt
rechtstreeks in de sensor mét `state_class: measurement` — en vervuilt daarmee
permanent de long-term statistics in de HA-recorder. Dat is achteraf lastig op te
schonen.

**Fix:** plausibiliteitsgrenzen, bijv. temperatuur −40…80 °C, luchtvochtigheid 0…100 %.
Daarbuiten: loggen en negeren.

### 6. Sensoren blijven "beschikbaar" met verouderde data
`sensor.py` → `available` is `True` zodra `last_seen` ooit gezet is. Stopt de
Shortcut met draaien (Low Power Mode, iOS die de automatisering pauzeert), dan
blijft de temperatuursensor uren of dagen een oude waarde als actueel presenteren.
De stale binary_sensor signaleert dat wel, maar de temperatuurentiteit zelf liegt.

**Fix:** `available` koppelen aan dezelfde staleness-drempel als de binary_sensor
(gedeelde helper), zodat de waarde na 3× het interval `unavailable` wordt.

### 7. Gebruik HA's eigen webhook-ID-generator
`config_flow.py` gebruikt `secrets.token_hex(16)`. Functioneel prima, maar
`webhook.async_generate_id()` is de conventie en sluit aan op HA's eigen
lengte/formaat-verwachtingen.

### 8. Overweeg een gedeeld geheim in de payload
Bovenop de webhook-URL: een `secret`-veld dat de coordinator vergelijkt met een in
de config entry opgeslagen waarde. Verdedigt tegen een gelekte URL (screenshot,
logregel, gedeelde config). Optioneel, maar goedkoop te implementeren.

---

## Opruimen — lage prioriteit

### 9. Webhook-lookup is onnodig omslachtig
`webhook.py` → `async_handle_webhook` itereert over alle config entries om de
coordinator te vinden die bij `webhook_id` hoort. De config flow staat maar één
instance toe (`single_instance_allowed`), dus die lus lost een probleem op dat niet
bestaat. Simpeler: coordinator meegeven via `functools.partial` bij het registreren.

### 10. Dode code: `coordinator.update_interval_minutes`
Wordt gezet in `__init__.py` en bijgewerkt in `async_update_options`, maar nergens
uitgelezen — `binary_sensor.py` leest het interval rechtstreeks uit de config entry.
Of aansluiten, of weghalen.

### 11. Device-naam wordt nooit bijgewerkt
`coordinator.py` zet `name` alleen bij het eerste contact (`is_new`). Hernoem je de
HomePod in de Home-app, dan blijft de oude naam staan tot je de integratie opnieuw
toevoegt.

### 12. `OptionsFlow.__init__` slaat de config entry zelf op
`self._config_entry = config_entry` — in recentere HA-versies wordt de entry
automatisch beschikbaar gesteld en is expliciet meegeven afgeraden. Controleer tegen
de HA-versie die je draait; kan een deprecation warning geven.

### 13. README belooft bestanden die er niet zijn
- Hoofd-README linkt naar `shortcuts/HomePod Sensors.shortcut` → **bestaat niet**.
- `shortcuts/README.md` heeft een iCloud-link met de tekst *"link added on first release"* → placeholder.

Betekent in de praktijk: "Optie A: importeer het sjabloon" werkt niet, je bouwt de
Shortcut sowieso handmatig. Pas de README aan zodat die klopt, of maak het sjabloon
zelf en host het.

### 14. Geen LICENSE-bestand
README zegt "MIT", maar er staat geen licentiebestand in de repo. Voor eigen gebruik
irrelevant; wil je de fork publiceren, vraag de auteur om verduidelijking of neem de
MIT-tekst op met attributie.

---

## Vangnet

De repo heeft al `tests/` (14 tests over config flow, init, sensor, webhook) en
CI via GitHub Actions (`ruff` + `pytest` op Python 3.12). Laat die draaien tijdens
het verbouwen — vooral bij punt 2 en 3, waar de kans op regressie het grootst is.
Voor punt 1 bestaat nog geen test; die is triviaal toe te voegen aan
`test_config_flow.py`.
