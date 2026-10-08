# Spec format (input for `scripts/build_foundry.py`)

The spec is a small JSON that mirrors what a statblock says. The builder turns it
into a full Foundry document. All keys are optional unless marked **required**.
Use English system keys for enums (see `dictionary-ru.md` for Russian → key).

## Contents
1. NPC (actor) fields
2. Item fields (shared)
3. Per-item-type fields
4. How numbers from the statblock are treated
5. Patterns: multiattack, legendary, recharge, reactions, spellcasting, auras
6. Standalone item spec

---

## 1. NPC fields

| key | example | notes |
|---|---|---|
| `kind` | `"npc"` | default |
| `name` **required** | `"Нотик"` | keep the user's language |
| `rules` | `"2024"` / `"2014"` | 2014 if text says «спасбросок», «Сл», «Опасность X (N опыта)» without PB; 2024 if «Инициатива», «БМ», «Триггер/Ответ» |
| `size` | `tiny sm med lg huge grg` | |
| `type` | `"aberration"` | any other word → stored as custom type |
| `subtype` | `"гоблиноид"` | text in parentheses after type |
| `swarm` | `"tiny"` | for «рой крошечных зверей» |
| `alignment` | `"законно-злой"` | free text |
| `ac` | `15` | final AC number from the statblock |
| `hp`, `hp_formula` | `45`, `"6d8+18"` | `к/д` dice letters are fine |
| `initiative` | `4` | total init modifier (2024 statblocks); builder computes the bonus over DEX |
| `speed` | `{"walk":30,"fly":60,"swim":0,"climb":20,"burrow":0}` | feet |
| `hover` | `true` | «(парит)» |
| `abilities` **required** | `{"str":14,…}` | scores, not modifiers |
| `saves` | `{"dex":5,"wis":7}` or `["dex","wis"]` | totals from the statblock; builder sets proficiency and adds a bonus if the total doesn't match |
| `skills` | `{"prc":8,"ste":5}` | totals; builder picks proficient/expert and adds any remainder. `"prof"`/`"expert"` strings also allowed |
| `dr` / `di` / `dv` | `["fire","poison"]` | damage types; unknown words go to custom automatically |
| `dr_custom` etc. | `"урон от серебра"` | free text |
| `dr_bypasses` | `["mgc"]` | «от немагических атак» → `mgc`; `ada` adamantine, `sil` silver |
| `ci` | `["charmed","poisoned"]` | condition immunities |
| `senses` | `{"darkvision":120,"blindsight":30,"tremorsense":0,"truesight":0}` | |
| `senses_special` | `"слеп за пределами этого радиуса"` | |
| `languages` | `["common","draconic"]` | keys; unknown → put in `languages_custom` |
| `languages_custom` | `"понимает Бездны, но не говорит"` | |
| `telepathy` | `120` | appended to custom languages |
| `cr` | `2`, `"1/4"`, `0.5` | drives proficiency bonus |
| `legendary_actions` | `3` | count per round |
| `legendary_resistance` | `3` | uses per day |
| `lair` | `true` | creature has lair actions |
| `spellcasting_ability` | `"cha"` | used for spell DC/attack |
| `spell_level` | `5` | caster level for slot-based casters |
| `spell_slots` | `{"1":4,"2":3,"3":2}` | slot casters only |
| `biography` | `"<p>…</p>"` or plain text | lore / description |
| `habitat` | `["forest","swamp"]` | 2024 keys: arctic coastal desert forest grassland hill mountain planar swamp underdark urban underwater any |
| `img` / `token_img` | `"tokens/nothic.webp"` | path inside Foundry `Data/`; default mystery-man |
| `disposition` | `-1` | -1 hostile, 0 neutral, 1 friendly |
| `items` | `[...]` | every trait, action, weapon, spell, armor |

## 2. Item fields (all item types)

| key | example | notes |
|---|---|---|
| `type` **required** | `feat weapon spell equipment consumable loot` | |
| `name` **required** | `"Коготь"` | |
| `description` | text or HTML | **always paste the original text** — it is what players read |
| `activation` | `action bonus reaction legendary lair special minute hour day ""` | `""` = no activation |
| `cost` | `2` | legendary action cost, or minutes/hours |
| `trigger` | `"существо попадает по нему"` | reaction trigger / activation condition |
| `passive` | `true` | no activity at all (pure trait) |
| `uses` | `{"max":3,"per":"day"}` / `{"recharge":5}` | per: `lr sr day dawn dusk turnStart turnEnd`; recharge 5 = «перезарядка 5–6» |
| `range` | `30` / `"self"` / `"touch"` / `"в пределах видимости"` | feet if number |
| `targets` | `1` | number of targets |
| `area` | `{"type":"cone","size":30}` | types: `cone cube cylinder line radius sphere square wall`; line also `width` |
| `attack` | `{"kind":"melee","bonus":5,"ability":"dex"}` | `kind` melee/ranged; `bonus` = to-hit total from statblock; `ability` optional; `"classification":"spell"` for spell attacks |
| `damage` | `[["1d6+3","slashing"],["2d6","poison"]]` | dice exactly as written in the statblock. First part on a weapon = base damage |
| `save` | `{"ability":"con","dc":12}` | `dc` omitted on spells → spellcasting DC |
| `save_damage` | `[["4d6","fire"]]` | only when an item has BOTH an attack and a save with its own damage |
| `on_save` | `half` / `none` / `full` | |
| `heal` | `["2d4+2","healing"]` | `temphp` for temporary HP |
| `conditions` | `["poisoned"]` | adds an Active Effect applied on hit / failed save |
| `roll` | `"1d6"` | utility roll formula |
| `legendary_resistance` | `true` | makes the «Легендарное сопротивление» use consume `resources.legres` |
| `img` | path | optional; builder picks a core icon by damage type |

## 3. Per-type fields

**weapon**: `reach` (melee, ft), `range` + `long_range` (ranged), `weapon_type`
(`natural simpleM simpleR martialM martialR improv`, default natural),
`properties` (`fin lgt hvy two ver thr amm lod rch rel ret spc mgc sil ada`),
`versatile` (`"1d10"`), `mastery` (2024: `cleave graze nick push sap slow topple vex`),
`magical_bonus` (`1`).

**spell**: `level` 0-9, `school` (`abj con div enc evo ill nec trs`),
`components` (`["vocal","somatic","material"]`), `materials` (text),
`concentration`, `ritual`, `duration` (`{"value":1,"units":"minute"}`; units
`inst turn round minute hour day perm spec`), `method` (`spell` for slot casting,
`innate` for X/day, `atwill` for at-will, `pact` for warlock), `prepared` (0/1/2).

**equipment**: `armor` `{"type":"light|medium|heavy|shield|natural|clothing|trinket","value":11,"dex":2,"strength":13}`.

**consumable / loot**: `subtype` (`potion scroll wand rod food poison ammo trinket`), `quantity`, `price`, `weight`, `rarity`.

**feat**: `feat_type` — `monster` (default for creatures), `class`, `race`, `feat`, `background`.

## 4. How numbers are treated

The builder never makes you do PB math:
- **to-hit**: give the total (`+9`). It finds the ability whose modifier + PB equals it; if none, it adds the remainder as a flat bonus. The roll in Foundry equals the statblock.
- **weapon damage**: give the dice as printed (`2d8+5`). The ability modifier is subtracted automatically because Foundry adds it back.
- **non-weapon damage** (feats, spells): given as printed, nothing is added.
- **save DC**: given as printed (flat). For spells without `dc` the spellcasting DC is used.
- **saves / skills / initiative**: given as printed totals.

Always copy numbers verbatim from the source; never «fix» them, even if they look
off for the CR. If the source is inconsistent, keep the source and mention it.

## 5. Patterns

**Multiattack** — `{"type":"feat","name":"Мультиатака","activation":"action","description":"…"}`.

**Legendary actions** — set `legendary_actions` on the NPC, then each action is a feat with
`"activation":"legendary","cost":N`. If it just repeats an attack, a description is enough.
Legendary actions may contain a `save`/`damage` of their own.

**Legendary resistance** — NPC `legendary_resistance: 3` + one feat with
`"legendary_resistance": true`.

**Recharge** — `"uses":{"recharge":5}` (5–6), `{"recharge":6}` (6).

**X/day** — `"uses":{"max":3,"per":"day"}`.

**Reaction** — `"activation":"reaction","trigger":"…"`. Add `damage`/`save` if it deals damage.

**Auras / passives** — `"passive": true`. If an aura deals damage on a save, make it an
item with `"activation":"special"` + `save` + `damage` so the GM can roll it.

**Spellcasting (monster)** — one passive feat with the original text, plus one `spell`
item per spell: at-will → `"method":"atwill"`, N/day → `"method":"innate","uses":{"max":N,"per":"day"}`.
Spells with saves leave `dc` empty so they use the actor's spellcasting DC; set
`spellcasting_ability` on the NPC. Give each spell real `damage`/`save`/`area`
if you know the spell; otherwise description only. (A GM can later swap them for
compendium spells by drag-and-drop.)

**Lair actions** — NPC `lair: true`, feats with `"activation":"lair"`.

**Attack + rider save** (e.g. bite + poison save) — `attack` + `damage` for the hit,
`save` + `save_damage` + `conditions` for the rider.

## 6. Standalone item spec

```json
{"kind":"item","type":"feat","feat_type":"race","name":"Морозное дыхание",
 "activation":"action","uses":{"max":2,"per":"lr"},
 "area":{"type":"cone","size":15},"save":{"ability":"con","dc":"13"},
 "damage":[["2d8","cold"]],"on_save":"half","description":"…"}
```
A file may contain a JSON **array** of specs — the builder writes one output file each.
