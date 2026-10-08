# AGENTS.md

This repository contains **GMB Foundry Creature Converter** — an agent skill that converts D&D 5e content
(statblocks, abilities, spells, items, screenshots of statblocks, or creature ideas) into
import-ready Foundry VTT JSON for the dnd5e system.

When the user asks to convert something for Foundry / FVTT / «фаундри», or to fix a Foundry
actor or item JSON:

1. Read `skills/gmb-foundry-creature-converter/SKILL.md` and follow its workflow.
2. Build with `python skills/gmb-foundry-creature-converter/scripts/build_foundry.py <spec.json>`.
3. Validate with `python skills/gmb-foundry-creature-converter/scripts/validate_foundry.py <output.json>`
   and compare the printed summary with the source.
4. Write output files to the current working directory unless the user names another path.

Python 3.8+ with the standard library is all the scripts need.

## Working on the skill itself
- Keep `SKILL.md` under ~500 lines; detailed material belongs in `references/`.
- Every change to the builder must keep `examples/*.spec.json` building cleanly:
  ```bash
  cd skills/gmb-foundry-creature-converter/examples
  for f in *.spec.json; do python ../scripts/build_foundry.py "$f" --seed 1 >/dev/null; done
  python ../scripts/validate_foundry.py fvtt-*.json --quiet
  ```
- Regenerate all banners (README SVG + terminal) with `python assets/src/make_banner.py` (needs Pillow).
