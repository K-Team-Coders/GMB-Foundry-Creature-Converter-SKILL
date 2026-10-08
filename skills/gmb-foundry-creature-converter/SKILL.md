---
name: gmb-foundry-creature-converter
description: Converts D&D 5e content into import-ready Foundry VTT JSON (dnd5e system) — monster and NPC statblocks, homebrew creatures, single abilities, attacks, spells, items, armor — from pasted text (Russian or English, 2014 or 2024 rules), screenshots or photos of statblocks, or a plain description. Use this skill whenever the user mentions Foundry, FVTT, «фаундри», importing a monster or ability into a virtual tabletop, «перегнать статблок в json», or pastes a statblock / ability and wants it usable in Foundry — even if they don't say "JSON" explicitly. Also use it when they want to fix or extend an existing Foundry actor/item JSON.
---

# GMB Foundry Creature Converter

Turn whatever the user gives you — a statblock, a list of abilities, a picture of a
monster page, or "make me a CR 3 goblin shaman" — into `.json` files that Foundry VTT
imports with **Import Data**, with working attack rolls, saves, damage, uses and recharges.

The hard part of Foundry JSON is not the content, it's the plumbing: random 16-char IDs
that must match, activities keyed by their IDs, proficiency math, weapon damage that must
*exclude* the ability modifier, enums that silently fail when written in Russian. So the
workflow separates the two: **you** read the statblock into a small *spec*; the **script**
does the plumbing and validates it.

## Files in this skill
- `scripts/build_foundry.py` — spec → full Foundry JSON (no dependencies, Python 3.8+)
- `scripts/validate_foundry.py` — checks a Foundry JSON and prints a statblock summary
- `references/spec-format.md` — every spec field and pattern (read before writing a spec)
- `references/dictionary-ru.md` — Russian/English terms → system keys
- `references/foundry-schema.md` — raw Foundry format, for when Python is unavailable
- `examples/` — input text → spec → output for a simple creature (nothic), a complex
  one (legendary, recharge, spells, reaction, conditions) and a standalone ability

## Workflow

### 1. Understand the input
- **Text statblock / abilities**: work from it directly.
- **Image of a statblock** (screenshot, photo, PDF page): transcribe it carefully first.
  Double-check numbers that OCR easily confuses (1/7, 3/8, 5/6, «к»/«d»). If something
  is unreadable, say which field and use the most plausible value.
- **Image of creature art**: it becomes the portrait/token. Foundry can't embed images in
  JSON — set `img`/`token_img` to `tokens/<slug>.webp` (or a path the user gives), and
  if you can write files, save the picture next to the JSON under that name. Tell the user
  to upload it to that path in Foundry (or pick the image after import).
- **Several creatures** → one spec and one output file per creature.
- **A single ability / item / spell** → a standalone item spec (`"kind": "item"`).
- **A request to invent something** ("сделай босса для 4 игроков 5 уровня"): design it,
  show the statblock in chat for approval if the request is vague, then convert.
- **An existing Foundry JSON to fix**: edit it directly, then validate.

### 2. Write the spec
Read `references/spec-format.md` (and `references/dictionary-ru.md` for Russian text).
Look at `examples/*.spec.json` — copying their shape is the fastest way to get it right.

Principles that matter:
- **Copy numbers verbatim** — AC, HP, to-hit totals, damage dice with bonus, DCs, save
  and skill totals. The builder works out proficiency and modifiers so that Foundry's rolls
  reproduce the statblock. Don't pre-compute anything and don't "correct" the source.
- **Keep the user's language** for names and descriptions; system enums are always English
  keys (`"poison"`, not `"яд"`).
- **Always include the original text as `description`** of each item — players read it on
  the sheet and in chat, and it preserves anything the mechanics don't model.
- **Model mechanics where Foundry can roll them**: attacks, saves, damage, healing,
  conditions, uses, recharge, legendary costs. Pure flavour stays a `passive` feat.
- Detect the rules edition: 2024 markers are «Инициатива», «БМ/PB», «Триггер/Ответ»,
  «Атака оружием ближнего боя» without «Рукопашная», habitats; otherwise 2014.

### 3. Build and validate
```bash
python scripts/build_foundry.py spec.json -o fvtt-Actor-<slug>.json
python scripts/validate_foundry.py fvtt-Actor-<slug>.json
```
- Default output targets **Foundry v14 + dnd5e 6.x**. If the user is on Foundry v13 /
  dnd5e 5.x, add `--format v5`. If unknown, use the default and mention the flag.
- The validator prints a summary (AC, HP, saves, skills, to-hit, damage, DCs, uses).
  **Compare it line by line with the source.** A mismatch almost always means a spec
  mistake (wrong ability, damage type, forgotten `uses`). Fix the spec and rebuild.
- A spec file may hold an array of specs → one output per element.

**No Python available?** (pure chat, restricted sandbox) Write the JSON by hand: copy
`examples/fvtt-Actor-nothic.json` or `examples/fvtt-Actor-myconid-tyrant.json` and edit
it, following `references/foundry-schema.md` — especially §7 "Common mistakes". Generate
fresh 16-character IDs and make each activity's key equal its `_id`.

### 4. Deliver
- Save files where the environment shows them to the user (Claude.ai:
  `/mnt/user-data/outputs/` + present them; Codex / CLI: the working directory; pure chat:
  a single ```json block per document).
- Name files `fvtt-Actor-<slug>.json` / `fvtt-Item-<slug>.json`.
- Reply briefly, in the user's language:
  1. what was created (one line per file);
  2. how to import: *Actors (or Items) sidebar → create any NPC/item → right-click →
     Import Data → choose the file*;
  3. **assumptions and gaps** — anything you guessed, couldn't model, or that the
     source got wrong (e.g. «урон Когтя не сходится с СИЛ — оставил как в тексте»).
  Skip the full statblock recap; the user already has it.

## Edge cases
- **Spellcasters**: one passive "Spellcasting" feat with the original text + a `spell`
  item per spell (`method` atwill / innate with uses / spell with `spell_slots`). Give
  spells real save/damage/area when you know them; otherwise description only. Mention
  the GM can swap in compendium spells by drag-and-drop.
- **Variable damage / formulas** («урон равен 2к6 + уровень») → write the formula as the
  dice string; the builder falls back to a custom formula.
- **Damage resistance "from nonmagical attacks"** → B/P/S + `"dr_bypasses": ["mgc"]`.
- **Swarms, shapechangers, multiple stat variants** → model the main form; put the rest in
  descriptions and mention it.
- **Player characters / classes / subclasses** are out of scope for the builder (class
  advancement is complex). Offer to export their features as standalone items instead.
- **Other game systems** (PF2e, etc.) are out of scope — say so rather than guessing.
