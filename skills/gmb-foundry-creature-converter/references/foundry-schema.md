# Foundry dnd5e JSON anatomy (for writing by hand, without Python)

Use this only when you cannot run `scripts/build_foundry.py`. The cleanest
method is to copy `examples/fvtt-Actor-nothic.json` (simple) or
`examples/fvtt-Actor-myconid-tyrant.json` (legendary, recharge, spells,
reaction, effects) and edit values. Foundry fills in any omitted field with
defaults, so a smaller document is fine — wrong values are worse than missing ones.

Target: **Foundry v13–v14, dnd5e 5.x–6.x** (activities system).

## Contents
1. Import mechanics
2. Actor skeleton
3. Version differences (v6 vs v5)
4. Items and activities
5. Activity snippets
6. Active effects (conditions)
7. Common mistakes

## 1. Import mechanics
- One file = one document. Several creatures → several files.
- In Foundry: Actors sidebar → create an NPC (any name) → right-click it → **Import Data** → choose file.
  The import overwrites everything including the name. Items: same in the Items sidebar.
- `_id` of the root document is ignored on import; embedded items/effects/activities need IDs.
- IDs: exactly 16 characters `[A-Za-z0-9]`, unique inside the document.
- Activities are an **object keyed by their own `_id`**: `"activities": {"abc…16": {"_id": "abc…16", …}}`.

## 2. Actor skeleton (v6)
```json
{
  "name": "…", "type": "npc", "img": "icons/svg/mystery-man.svg",
  "system": {
    "abilities": {"str": {"value": 14, "proficient": 0}, "dex": {…}, "con": {…}, "int": {…}, "wis": {…}, "cha": {…}},
    "attributes": {
      "ac": {"flat": 15, "calcs": ["natural"], "formulas": [], "override": null},
      "hp": {"value": 45, "max": 45, "formula": "6d8 + 18"},
      "init": {"ability": "", "roll": {"min": null, "max": null, "mode": 0, "bonus": ""}},
      "movement": {"units": null, "hover": false, "speeds": {"walk": "30", "fly": "60"}},
      "senses": {"units": null, "special": "", "ranges": {"darkvision": 60, "blindsight": null, "tremorsense": null, "truesight": null}},
      "spellcasting": "cha"
    },
    "details": {
      "cr": 2, "alignment": "…",
      "type": {"value": "aberration", "subtype": "", "swarm": "", "custom": ""},
      "biography": {"value": "<p>…</p>", "public": ""}
    },
    "traits": {
      "size": "med",
      "di": {"value": [], "bypasses": [], "custom": ""},
      "dr": {"value": [], "bypasses": [], "custom": ""},
      "dv": {"value": [], "bypasses": [], "custom": ""},
      "ci": {"value": [], "custom": ""},
      "languages": {"value": ["deep"], "custom": "", "communication": {}}
    },
    "skills": {"prc": {"ability": "wis", "value": 1}, "ste": {"ability": "dex", "value": 1}},
    "resources": {"legact": {"max": 0, "spent": 0}, "legres": {"max": 0, "spent": 0}, "lair": {"value": false}},
    "source": {"rules": "2024", "book": ""}
  },
  "prototypeToken": {"name": "…", "width": 1, "height": 1, "disposition": -1,
                     "texture": {"src": "icons/svg/mystery-man.svg"}, "bar1": {"attribute": "attributes.hp"}},
  "items": [],
  "effects": [],
  "_stats": {"systemId": "dnd5e", "systemVersion": "6.0.2", "coreVersion": "14.367"}
}
```
- `abilities.X.proficient` 1 = save proficiency. `skills.X.value` 0 / 1 / 2 (expertise).
  Bonuses beyond PB: `abilities.X.bonuses.save`, `skills.X.bonuses.check` (strings like `"1"`).
- Proficiency bonus comes from `cr`. Token size: tiny 0.5, sm/med 1, lg 2, huge 3, grg 4.

## 3. Version differences
| field | dnd5e 6.x (Foundry v14) | dnd5e 5.x (Foundry v13) |
|---|---|---|
| AC | `ac.calcs: ["natural"]`, `ac.flat` | `ac.calc: "natural"`, `ac.flat` |
| speed | `movement.speeds.walk: "30"` | `movement.walk: 30` |
| senses | `senses.ranges.darkvision: 60` | `senses.darkvision: 60` |
| `_stats` | systemVersion 6.x / core 14 | 5.x / core 13 |
Spells use `"method"` + `"prepared"` in both. dnd5e ≤ 4.x (`preparation.mode`) is not targeted.

## 4. Items
Common item keys: `_id, name, type, img, system, effects, flags, sort, ownership`.
`system` always has `description.value` (HTML), `source`, `identifier`, `activities`, `uses`.

| type | key system fields |
|---|---|
| feat | `type: {value: "monster"}`, `properties: ["trait"]` for passives |
| weapon | `type: {value: "natural"}`, `damage.base {number, denomination, bonus, types}`, `range {reach | value, long}`, `properties`, `equipped: true` |
| spell | `level`, `school`, `properties ["vocal","somatic","material","concentration","ritual"]`, `activation`, `range`, `duration`, `method`, `prepared` |
| equipment | `type: {value: "light"}`, `armor {value, dex}`, `equipped: true` |

`uses`: `{"max": "3", "spent": 0, "recovery": [{"period": "day", "type": "recoverAll"}]}`.
Recharge 5–6: `{"max": "1", "recovery": [{"period": "recharge", "type": "recoverAll", "formula": "5"}]}`.

**Weapon damage**: base part excludes the ability modifier (Foundry adds it). Statblock
`2d8+5` with STR 20 (+5) → `{"number":2,"denomination":8,"bonus":""}`.
Extra damage («плюс 7 (2к6) ядом») goes into the attack activity's `damage.parts`.

## 5. Activity snippets
Shared shell (omit nothing marked here):
```json
{"_id": "ID16", "type": "…", "activation": {"type": "action", "value": null, "condition": ""},
 "consumption": {"targets": [], "spellSlot": true, "scaling": {"allowed": false}},
 "range": {"units": "self"}, "target": {"template": {"type": "", "size": "", "units": "ft"}, "affects": {"type": "", "count": ""}, "prompt": true},
 "uses": {"spent": 0, "max": "", "recovery": []}, "effects": [], "name": ""}
```
- **attack**: `"attack": {"ability": "str", "bonus": "", "flat": false, "type": {"value": "melee", "classification": "weapon"}}, "damage": {"includeBase": true, "parts": []}`
- **save**: `"save": {"ability": ["dex"], "dc": {"calculation": "", "formula": "15"}}, "damage": {"onSave": "half", "parts": [{"number": 8, "denomination": 6, "bonus": "", "types": ["fire"]}]}`
  Spell DC: `"dc": {"calculation": "spellcasting", "formula": ""}`.
- **damage** (no roll to hit / save): `"damage": {"parts": [...]}`
- **heal**: `"healing": {"number": 2, "denomination": 4, "bonus": "2", "types": ["healing"]}`
- **utility** (multiattack, flavour): `"roll": {"formula": "", "prompt": false, "visible": false}`
- Consume item uses: `consumption.targets: [{"type": "itemUses", "value": "1", "target": ""}]`
- Legendary resistance: utility, activation `special`, consumption `{"type": "attribute", "value": "1", "target": "resources.legres.value"}`
- Legendary action: activation `{"type": "legendary", "value": 2}` (value = cost)
- Area: `target.template {"type": "cone", "size": "30"}`; line adds `"width": "5"`.
Damage part full form: `{"number": 2, "denomination": 6, "bonus": "", "types": ["poison"], "custom": {"enabled": false, "formula": ""}, "scaling": {"number": 1}}`.
Formula that is not plain dice → `"custom": {"enabled": true, "formula": "1d6 + @mod"}`.

## 6. Active effects (applying a condition)
On the item: `"effects": [{"_id": "ID16", "name": "Poisoned", "type": "base", "statuses": ["poisoned"], "changes": [], "transfer": false, "disabled": false, "img": "systems/dnd5e/icons/svg/statuses/poisoned.svg"}]`.
In the activity: `"effects": [{"_id": "ID16"}]` (save activities: `{"_id": "ID16", "onSave": false}`).

## 7. Common mistakes
- Activities as an array → Foundry drops them. Must be an object keyed by `_id`.
- Activity key ≠ its `_id`.
- Russian words in enum fields (`"types": ["огонь"]`) → silently ignored. Use keys.
- Adding the ability modifier into weapon base damage → double counted.
- Numbers as strings where numbers are expected (`hp.max`, `cr`, ability `value`). Speeds/sense
  ranges in v6 tolerate strings; `uses.max` is a formula string.
- Trailing commas / comments → invalid JSON, import fails silently. Validate.
