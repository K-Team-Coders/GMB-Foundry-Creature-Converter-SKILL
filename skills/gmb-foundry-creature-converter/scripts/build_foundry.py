#!/usr/bin/env python3
"""
build_foundry.py — turns a compact, human-friendly "spec" JSON into a complete
Foundry VTT (dnd5e system) document ready for "Import Data".

Why a spec?  A Foundry actor export is ~20-160 KB of deeply nested JSON with
random IDs that must match each other.  Writing that by hand (or by an LLM) is
error-prone.  The spec keeps only what a statblock actually says; this script
fills in every default, generates IDs, works out proficiency, attack and damage
bonuses, and wires activities, uses and recharge correctly.

Usage:
    python build_foundry.py spec.json                 # -> <slug>.json next to spec
    python build_foundry.py spec.json -o out.json
    python build_foundry.py spec.json --format v5     # dnd5e 5.x / Foundry v13 layout
    python build_foundry.py spec.json --stdout
    python build_foundry.py --banner                  # the colored GMB banner

Spec kinds:
    "kind": "npc"   -> Actor (type npc) with embedded items      (default)
    "kind": "item"  -> a single Item (feat / weapon / spell / equipment / consumable / loot)

No third-party dependencies; Python 3.8+.
"""
import argparse
import copy
import json
import math
import random
import re
import string
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------
ABILITIES = ["str", "dex", "con", "int", "wis", "cha"]
SKILLS = {
    "acr": "dex", "ani": "wis", "arc": "int", "ath": "str", "dec": "cha",
    "his": "int", "ins": "wis", "itm": "cha", "inv": "int", "med": "wis",
    "nat": "int", "prc": "wis", "prf": "cha", "per": "cha", "rel": "int",
    "slt": "dex", "ste": "dex", "sur": "wis",
}
SIZES = {"tiny": 0.5, "sm": 1, "med": 1, "lg": 2, "huge": 3, "grg": 4}
CREATURE_TYPES = {"aberration", "beast", "celestial", "construct", "dragon",
                  "elemental", "fey", "fiend", "giant", "humanoid",
                  "monstrosity", "ooze", "plant", "undead"}
DAMAGE_TYPES = {"acid", "bludgeoning", "cold", "fire", "force", "lightning",
                "necrotic", "piercing", "poison", "psychic", "radiant",
                "slashing", "thunder"}
HEAL_TYPES = {"healing", "temphp"}
CONDITIONS = {"blinded", "charmed", "deafened", "diseased", "exhaustion",
              "frightened", "grappled", "incapacitated", "invisible",
              "paralyzed", "petrified", "poisoned", "prone", "restrained",
              "stunned", "unconscious"}
ACTIVATIONS = {"action", "bonus", "reaction", "minute", "hour", "day",
               "special", "legendary", "mythic", "lair", "crew", ""}
TEMPLATE_TYPES = {"circle", "cone", "cube", "cylinder", "line", "radius",
                  "sphere", "square", "wall"}
SCHOOLS = {"abj", "con", "div", "enc", "evo", "ill", "nec", "trs"}
PERIODS = {"lr", "sr", "day", "dawn", "dusk", "recharge", "turnStart",
           "turnEnd", "turn"}

DEFAULT_ICONS = {
    "npc": "icons/svg/mystery-man.svg",
    "weapon": "icons/svg/sword.svg",
    "equipment": "icons/svg/shield.svg",
    "spell": "icons/svg/book.svg",
    "consumable": "icons/svg/item-bag.svg",
    "loot": "icons/svg/item-bag.svg",
    "feat": "icons/svg/aura.svg",
}
DAMAGE_ICONS = {
    "fire": "icons/svg/fire.svg", "cold": "icons/svg/frozen.svg",
    "lightning": "icons/svg/lightning.svg", "thunder": "icons/svg/sound.svg",
    "poison": "icons/svg/poison.svg", "acid": "icons/svg/acid.svg",
    "necrotic": "icons/svg/skull.svg", "radiant": "icons/svg/sun.svg",
    "psychic": "icons/svg/daze.svg", "force": "icons/svg/explosion.svg",
    "healing": "icons/svg/heal.svg",
}

VERSIONS = {
    "v6": {"coreVersion": "14.367", "systemVersion": "6.0.2"},
    "v5": {"coreVersion": "13.348", "systemVersion": "5.1.2"},
}


class SpecError(ValueError):
    pass


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
_ID_CHARS = string.ascii_letters + string.digits


def new_id():
    return "".join(random.choice(_ID_CHARS) for _ in range(16))


def mod(score):
    return math.floor((int(score) - 10) / 2)


def prof_bonus(cr):
    cr = float(cr or 0)
    if cr < 5:
        return 2
    return 2 + math.ceil((cr - 4) / 4)


def parse_cr(value):
    if value in (None, ""):
        return 0
    if isinstance(value, (int, float)):
        return value
    s = str(value).strip().replace(",", ".")
    if "/" in s:
        a, b = s.split("/", 1)
        return round(float(a) / float(b), 3)
    return float(s) if "." in s else int(s)


def slugify(text):
    text = str(text or "creature").lower()
    tr = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
          "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
          "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
          "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch",
          "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}
    text = "".join(tr.get(c, c) for c in text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "creature"


DICE_RE = re.compile(r"^\s*(\d*)\s*[dкд]\s*(\d+)\s*(?:([+-])\s*(\d+))?\s*$", re.I)


def parse_dice(expr):
    """'2d6+3' -> (2, 6, 3); '5' -> (0, 0, 5); unparseable -> None."""
    if expr is None:
        return None
    s = str(expr).replace(" ", "").replace("−", "-").replace("к", "d").replace("д", "d")
    m = DICE_RE.match(s)
    if m:
        n = int(m.group(1) or 1)
        bonus = int(m.group(4) or 0) * (-1 if m.group(3) == "-" else 1)
        return n, int(m.group(2)), bonus
    if re.fullmatch(r"[+-]?\d+", s):
        return 0, 0, int(s)
    return None


def html(text):
    """Plain text -> HTML paragraphs.  Already-HTML text passes through."""
    if not text:
        return ""
    text = str(text)
    if re.search(r"<\s*(p|div|h\d|ul|ol|table|br)\b", text, re.I):
        return text
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return "".join(f"<p>{esc(p)}</p>" for p in paras)


def roll_block():
    return {"min": None, "max": None, "mode": 0}


def norm_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return list(value)


def as_number(value):
    if value in (None, ""):
        return None
    try:
        f = float(value)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# activity / item builders
# --------------------------------------------------------------------------
def base_activity(kind, activation="action", cost=None, condition=""):
    if activation not in ACTIVATIONS:
        raise SpecError(f"unknown activation '{activation}'")
    aid = new_id()
    return {
        "_id": aid,
        "type": kind,
        "sort": 0,
        "name": "",
        "img": None,
        "activation": {"type": activation, "value": cost, "override": False,
                       "condition": condition},
        "consumption": {"scaling": {"allowed": False, "max": ""},
                        "spellSlot": True, "targets": []},
        "description": {"chatFlavor": "", "value": ""},
        "duration": {"units": "inst", "concentration": False, "override": False,
                     "expiry": None},
        "effects": [],
        "range": {"override": False, "units": "self", "special": ""},
        "target": {
            "template": {"contiguous": False, "units": "ft", "type": "",
                         "size": "", "width": "", "height": "", "count": "",
                         "stationary": False},
            "affects": {"choice": False, "count": "", "type": "", "special": ""},
            "override": False,
            "prompt": True,
        },
        "uses": {"spent": 0, "recovery": [], "max": ""},
        "flags": {},
        "visibility": {"level": {}, "requireAttunement": False,
                       "requireIdentification": False, "requireMagic": False},
        "behaviors": [],
    }


def damage_part(dice, dtype, extra_bonus=None):
    parsed = parse_dice(dice)
    types = [t for t in norm_list(dtype)]
    for t in types:
        if t not in DAMAGE_TYPES and t not in HEAL_TYPES:
            raise SpecError(f"unknown damage type '{t}' (use English keys, e.g. 'slashing')")
    part = {"custom": {"enabled": False, "formula": ""}, "number": None,
            "denomination": None, "bonus": "", "types": types,
            "scaling": {"mode": "whole", "number": 1, "formula": ""},
            "modifiers": []}
    if parsed is None:
        part["custom"] = {"enabled": True, "formula": str(dice)}
        return part
    n, d, b = parsed
    if extra_bonus is not None:
        b = extra_bonus
    if d:
        part["number"], part["denomination"] = n, d
        part["bonus"] = str(b) if b else ""
    else:
        part["custom"] = {"enabled": True, "formula": str(b)}
    return part


def apply_range(act, spec):
    rng = spec.get("range")
    if rng is None:
        return
    if isinstance(rng, (int, float, str)) and str(rng).replace(".", "").isdigit():
        act["range"] = {"override": False, "value": str(rng), "units": "ft", "special": ""}
    elif str(rng).lower() in ("self", "touch", "spec", "any"):
        act["range"] = {"override": False, "units": str(rng).lower(), "special": ""}
    else:
        act["range"] = {"override": False, "units": "spec", "special": str(rng)}


def apply_area(act, spec):
    area = spec.get("area")
    if area:
        t = area.get("type", "")
        if t and t not in TEMPLATE_TYPES:
            raise SpecError(f"unknown area type '{t}'")
        tpl = act["target"]["template"]
        tpl["type"] = t
        tpl["size"] = str(area.get("size", "") or "")
        tpl["width"] = str(area.get("width", "") or "")
        tpl["height"] = str(area.get("height", "") or "")
        act["target"]["affects"]["type"] = area.get("affects", "creature")
    targets = spec.get("targets")
    if targets:
        act["target"]["affects"]["count"] = str(targets)
        act["target"]["affects"]["type"] = act["target"]["affects"]["type"] or "creature"


def recovery_from(spec_uses):
    """{'max':3,'per':'day'} / {'recharge':5} -> (max, recovery list)."""
    if not spec_uses:
        return "", []
    if "recharge" in spec_uses:
        r = int(spec_uses["recharge"])
        rec = {"period": "recharge", "type": "recoverAll"}
        if r != 6:
            rec["formula"] = str(r)
        return "1", [rec]
    per = spec_uses.get("per", "day")
    if per not in PERIODS:
        raise SpecError(f"unknown uses period '{per}'")
    return str(spec_uses.get("max", 1)), [{"period": per, "type": "recoverAll"}]


def make_effect(condition, name=None):
    if condition not in CONDITIONS:
        raise SpecError(f"unknown condition '{condition}'")
    return {
        "_id": new_id(), "name": name or condition.capitalize(),
        "img": f"systems/dnd5e/icons/svg/statuses/{condition}.svg",
        "type": "base", "system": {}, "changes": [], "disabled": False,
        "duration": {"startTime": None, "seconds": None, "combat": None,
                     "rounds": None, "turns": None, "startRound": None,
                     "startTurn": None},
        "description": "", "origin": None, "tint": "#ffffff",
        "transfer": False, "statuses": [condition], "sort": 0, "flags": {},
    }


def build_activities(spec, ctx, item_type):
    """Return (activities dict, item-level effects list, item-level uses)."""
    acts, effects = {}, []
    activation = spec.get("activation", "action")
    cost = spec.get("cost")
    if activation == "legendary" and cost is None:
        cost = 1
    condition = spec.get("trigger", "")
    item_uses_max, item_recovery = recovery_from(spec.get("uses"))

    def add(act):
        acts[act["_id"]] = act
        return act

    def consume_item_use(act):
        if item_uses_max:
            act["consumption"]["targets"].append(
                {"type": "itemUses", "value": "1", "target": "", "scaling": {}})

    def attach_conditions(act, on_save=None):
        for cond in norm_list(spec.get("conditions")):
            eff = make_effect(cond)
            effects.append(eff)
            ref = {"_id": eff["_id"]}
            if on_save is not None:
                ref["onSave"] = False
            act["effects"].append(ref)

    made = False

    # --- attack --------------------------------------------------------
    atk = spec.get("attack")
    if atk:
        act = base_activity("attack", activation, cost, condition)
        kind = atk.get("kind", "melee")
        ability, flat_bonus = resolve_attack_ability(atk, ctx, item_type, spec)
        act["attack"] = {"critical": {"threshold": None}, "flat": False,
                         "type": {"value": kind, "classification": atk.get("classification", "weapon")},
                         "ability": ability, "bonus": flat_bonus, }
        parts = []
        dmg = spec.get("damage") or []
        extra = dmg[1:] if item_type == "weapon" else dmg
        for d in extra:
            parts.append(damage_part(d[0], d[1]))
        act["damage"] = {"critical": {"bonus": ""},
                         "includeBase": item_type == "weapon", "parts": parts}
        if item_type != "weapon":
            # non-weapon attacks: put the whole damage in parts as written
            act["damage"]["parts"] = [damage_part(d[0], d[1]) for d in dmg]
        apply_range(act, spec)
        apply_area(act, spec)
        consume_item_use(act)
        attach_conditions(act)
        add(act)
        made = True

    # --- save ------------------------------------------------------------
    sv = spec.get("save")
    if sv:
        act = base_activity("save", activation, cost, condition)
        abil = norm_list(sv.get("ability"))
        for a in abil:
            if a not in ABILITIES:
                raise SpecError(f"unknown save ability '{a}'")
        dc = sv.get("dc")
        dc_block = {"calculation": "", "formula": str(dc)} if dc not in (None, "", "spellcasting") \
            else {"calculation": "spellcasting", "formula": ""}
        act["save"] = {"ability": abil, "dc": dc_block, "visible": True}
        dmg = spec.get("save_damage") if spec.get("save_damage") is not None else (
            [] if atk else spec.get("damage") or [])
        act["damage"] = {"onSave": spec.get("on_save", "half" if dmg else "none"),
                         "parts": [damage_part(d[0], d[1]) for d in dmg]}
        apply_range(act, spec)
        apply_area(act, spec)
        if not atk:
            consume_item_use(act)
        attach_conditions(act, on_save=True)
        add(act)
        made = True

    # --- heal ------------------------------------------------------------
    hl = spec.get("heal")
    if hl:
        act = base_activity("heal", activation, cost, condition)
        act["healing"] = damage_part(hl[0] if isinstance(hl, list) else hl,
                                     hl[1] if isinstance(hl, list) and len(hl) > 1 else "healing")
        apply_range(act, spec)
        apply_area(act, spec)
        consume_item_use(act)
        add(act)
        made = True

    # --- plain damage (no attack / no save) ---------------------------------
    if not made and spec.get("damage") and item_type != "weapon":
        act = base_activity("damage", activation, cost, condition)
        act["damage"] = {"critical": {"allow": False, "bonus": ""},
                         "parts": [damage_part(d[0], d[1]) for d in spec["damage"]]}
        apply_range(act, spec)
        apply_area(act, spec)
        consume_item_use(act)
        attach_conditions(act)
        add(act)
        made = True

    # --- utility (multiattack, legendary "make an attack", reactions …) --
    passive = spec.get("passive", False)
    if not made and not passive:
        act = base_activity("utility", activation, cost, condition)
        act["roll"] = {"prompt": False, "visible": False, "name": "", "formula": spec.get("roll", "")}
        apply_range(act, spec)
        apply_area(act, spec)
        consume_item_use(act)
        attach_conditions(act)
        if spec.get("legendary_resistance"):
            act["activation"] = {"type": "special", "value": None, "override": False,
                                 "condition": "fails a saving throw"}
            act["name"] = "Expend Use"
            act["consumption"]["targets"].append(
                {"type": "attribute", "value": "1",
                 "target": "resources.legres.value", "scaling": {}})
        add(act)

    if passive and spec.get("legendary_resistance"):
        raise SpecError("legendary_resistance cannot be passive")

    # legendary actions cost actor resource automatically in dnd5e; nothing to do.
    uses = {"spent": 0, "recovery": item_recovery, "max": item_uses_max}
    return acts, effects, uses


def resolve_attack_ability(atk, ctx, item_type, spec):
    """Work out which ability + extra bonus reproduces the statblock to-hit."""
    total = atk.get("bonus")
    ability = atk.get("ability")
    if ctx is None or total is None:
        return ability or "", ""
    total = int(total)
    pb = ctx["pb"]
    scores = ctx["abilities"]
    if ability:
        delta = total - (mod(scores[ability]) + pb)
        return ability, (str(delta) if delta else "")
    candidates = ["dex", "str"] if atk.get("kind", "melee") == "ranged" else ["str", "dex"]
    if item_type == "spell" or atk.get("classification") == "spell":
        candidates = [ctx.get("spell_ability") or "cha", "int", "wis", "cha"]
    for a in candidates + ABILITIES:
        if mod(scores[a]) + pb == total:
            return a, ""
    best = max(candidates, key=lambda a: mod(scores[a]))
    delta = total - (mod(scores[best]) + pb)
    return best, (str(delta) if delta else "")


def build_item(spec, ctx=None, rules="2024"):
    itype = spec.get("type", "feat")
    if itype not in ("feat", "weapon", "spell", "equipment", "consumable", "loot"):
        raise SpecError(f"unknown item type '{itype}'")
    name = spec.get("name") or "Unnamed"
    desc = html(spec.get("description", ""))
    source = {"revision": 1, "rules": spec.get("rules", rules), "book": spec.get("source", ""),
              "page": "", "custom": "", "license": ""}

    system = {"description": {"value": desc, "chat": ""}, "source": source,
              "identifier": slugify(spec.get("identifier") or name)}
    effects = []

    if itype in ("feat", "weapon", "spell", "consumable"):
        acts, effects, uses = build_activities(spec, ctx, itype)
        system["activities"] = acts
        system["uses"] = uses
    else:
        system["activities"] = {}
        system["uses"] = {"spent": 0, "recovery": [], "max": ""}

    if itype == "feat":
        system.update({
            "type": {"value": spec.get("feat_type", "monster"), "subtype": ""},
            "requirements": spec.get("requirements", ""),
            "properties": ["trait"] if spec.get("passive") or spec.get("legendary_resistance") else [],
            "enchant": {}, "prerequisites": {"level": None, "repeatable": False, "items": []},
            "advancement": {}, "cover": None, "crewed": False,
        })

    elif itype == "weapon":
        dmg = spec.get("damage") or []
        base = {"number": None, "denomination": None, "bonus": "", "types": [],
                "custom": {"enabled": False, "formula": ""},
                "scaling": {"mode": "", "number": 1, "formula": ""}, "modifiers": []}
        if dmg:
            first = dmg[0]
            parsed = parse_dice(first[0])
            atk_act = next((a for a in system["activities"].values() if a["type"] == "attack"), None)
            ability = atk_act["attack"]["ability"] if atk_act else ""
            abil_mod = mod(ctx["abilities"][ability]) if (ctx and ability) else 0
            if parsed and parsed[1]:
                n, d, b = parsed
                base.update({"number": n, "denomination": d,
                             "bonus": str(b - abil_mod) if (b - abil_mod) else "",
                             "types": norm_list(first[1])})
            else:
                base.update({"custom": {"enabled": True, "formula": str(first[0])},
                             "types": norm_list(first[1])})
        versatile = {"number": None, "denomination": None, "bonus": "", "types": [],
                     "custom": {"enabled": False, "formula": ""},
                     "scaling": {"mode": "", "number": 1, "formula": ""}, "modifiers": []}
        if spec.get("versatile"):
            p = parse_dice(spec["versatile"])
            if p and p[1]:
                versatile.update({"number": p[0], "denomination": p[1], "types": base["types"]})
        atk = spec.get("attack") or {}
        rng = {"value": None, "long": None, "reach": None, "units": "ft"}
        if atk.get("kind") == "ranged" or spec.get("long_range"):
            rng["value"] = as_number(spec.get("range"))
            rng["long"] = as_number(spec.get("long_range"))
        else:
            reach = as_number(spec.get("reach") or spec.get("range") or 5)
            rng["reach"] = reach if reach and reach != 5 else None
        # keep weapon range on the item, not on the activity
        for a in system["activities"].values():
            a["range"] = {"override": False, "units": "self", "special": ""}
        system.update({
            "type": {"value": spec.get("weapon_type", "natural"), "baseItem": ""},
            "damage": {"base": base, "versatile": versatile},
            "range": rng, "properties": norm_list(spec.get("properties")),
            "quantity": 1, "weight": {"value": 0, "units": "lb"},
            "price": {"value": 0, "denomination": "gp"}, "attunement": "",
            "attuned": False, "equipped": True, "identified": True,
            "unidentified": {"description": ""}, "container": None, "cover": None,
            "ammunition": {}, "armor": {"value": None},
            "hp": {"value": None, "max": None, "dt": None, "conditions": ""},
            "proficient": None if spec.get("weapon_type", "natural") == "natural" else 1,
            "mastery": spec.get("mastery", ""), "crew": {"value": []}, "rarities": [],
            "magicalBonus": spec.get("magical_bonus"),
        })
        if system["magicalBonus"] is None:
            system.pop("magicalBonus")

    elif itype == "spell":
        level = int(spec.get("level", 0))
        school = spec.get("school", "evo")
        if school not in SCHOOLS:
            raise SpecError(f"unknown spell school '{school}'")
        props = norm_list(spec.get("components", ["vocal", "somatic"]))
        if spec.get("concentration"):
            props.append("concentration")
        if spec.get("ritual"):
            props.append("ritual")
        method = spec.get("method", "spell")      # spell | innate | atwill | pact | ritual
        prepared = 2 if method in ("innate", "atwill") or spec.get("always_prepared") else int(spec.get("prepared", 1))
        rng = spec.get("range")
        range_block = {"value": "", "units": "self", "special": ""}
        if rng is not None:
            if str(rng).replace(".", "").isdigit():
                range_block = {"value": str(rng), "units": "ft", "special": ""}
            elif str(rng).lower() in ("self", "touch", "any", "spec"):
                range_block = {"value": "", "units": str(rng).lower(), "special": ""}
            else:
                range_block = {"value": "", "units": "spec", "special": str(rng)}
        dur = spec.get("duration") or {}
        act_type = spec.get("activation", "action")
        system.update({
            "level": level, "school": school, "properties": props,
            "materials": {"value": spec.get("materials", ""), "consumed": False, "cost": 0, "supply": 0},
            "activation": {"type": act_type, "condition": "", "value": spec.get("cost")},
            "duration": {"value": str(dur.get("value", "")), "units": dur.get("units", "inst"), "expiry": None},
            "range": range_block,
            "target": {"affects": {"type": "", "count": "", "choice": False, "special": ""},
                       "template": {"units": "ft", "contiguous": False, "type": "", "size": "",
                                    "count": "", "stationary": False}},
            "method": method, "prepared": prepared,
        })
        for a in system["activities"].values():
            a["range"]["override"] = False
            a["duration"]["concentration"] = bool(spec.get("concentration"))
            if a["type"] == "save" and not spec.get("save", {}).get("dc"):
                a["save"]["dc"] = {"calculation": "spellcasting", "formula": ""}
        # innate "1/day each": uses live on the spell; consumption must hit itemUses
        if system["uses"]["max"]:
            for a in system["activities"].values():
                if not any(t["type"] == "itemUses" for t in a["consumption"]["targets"]):
                    a["consumption"]["targets"].append(
                        {"type": "itemUses", "value": "1", "target": "", "scaling": {}})
            for a in system["activities"].values():
                a["consumption"]["spellSlot"] = False

    elif itype == "equipment":
        arm = spec.get("armor") or {}
        system.update({
            "type": {"value": arm.get("type", "trinket"), "baseItem": ""},
            "armor": {"value": as_number(arm.get("value")), "dex": as_number(arm.get("dex")), "magicalBonus": None},
            "strength": as_number(arm.get("strength")),
            "properties": norm_list(spec.get("properties")),
            "quantity": 1, "weight": {"value": spec.get("weight", 0), "units": "lb"},
            "price": {"value": spec.get("price", 0), "denomination": "gp"},
            "attunement": "", "attuned": False, "equipped": True, "identified": True,
            "unidentified": {"description": ""}, "container": None, "cover": None,
            "hp": {"value": None, "max": None, "dt": None, "conditions": ""},
            "speed": {"value": None, "conditions": "", "units": "ft"},
            "proficient": 1, "crew": {"value": []}, "rarities": [],
        })

    elif itype in ("consumable", "loot"):
        system.update({
            "type": {"value": spec.get("subtype", "potion" if itype == "consumable" else ""), "subtype": ""},
            "quantity": int(spec.get("quantity", 1)), "weight": {"value": spec.get("weight", 0), "units": "lb"},
            "price": {"value": spec.get("price", 0), "denomination": "gp"},
            "rarity": spec.get("rarity", ""), "identified": True,
            "unidentified": {"description": ""}, "container": None,
            "properties": norm_list(spec.get("properties")),
        })
        if itype == "consumable":
            system["uses"]["autoDestroy"] = True
            if not system["uses"]["max"]:
                system["uses"]["max"] = "1"

    img = spec.get("img") or pick_icon(itype, spec)
    return {
        "_id": new_id(), "name": name, "type": itype, "img": img,
        "system": system, "effects": effects, "folder": None, "sort": 0,
        "flags": {"dnd5e": {"riders": {"activity": [], "effect": []}}},
        "ownership": {"default": 0},
    }


def pick_icon(itype, spec):
    for d in (spec.get("damage") or []):
        for t in norm_list(d[1]):
            if itype != "weapon" and t in DAMAGE_ICONS:
                return DAMAGE_ICONS[t]
    if spec.get("heal"):
        return DAMAGE_ICONS["healing"]
    if itype == "feat" and spec.get("activation") == "legendary":
        return "icons/svg/upgrade.svg"
    if itype == "feat" and spec.get("activation") == "reaction":
        return "icons/svg/mage-shield.svg"
    if itype == "feat" and spec.get("passive"):
        return "icons/svg/eye.svg"
    return DEFAULT_ICONS[itype]


# --------------------------------------------------------------------------
# actor builder
# --------------------------------------------------------------------------
def build_npc(spec, fmt="v6"):
    name = spec.get("name")
    if not name:
        raise SpecError("npc needs a 'name'")
    rules = str(spec.get("rules", "2024"))
    cr = parse_cr(spec.get("cr", 0))
    pb = prof_bonus(cr)
    scores = {a: int((spec.get("abilities") or {}).get(a, 10)) for a in ABILITIES}

    size = spec.get("size", "med")
    if size not in SIZES:
        raise SpecError(f"unknown size '{size}' (tiny/sm/med/lg/huge/grg)")
    ctype = spec.get("type", "humanoid")
    custom_type = ""
    if ctype not in CREATURE_TYPES:
        custom_type, ctype = ctype, "custom"

    # abilities + saves
    saves = spec.get("saves") or {}
    if isinstance(saves, list):
        saves = {a: None for a in saves}
    abilities = {}
    for a in ABILITIES:
        prof = 0
        if a in saves:
            prof = 1
            tot = saves[a]
            if tot is not None and int(tot) == mod(scores[a]):
                prof = 0
        abilities[a] = {"value": scores[a], "proficient": prof, "max": None,
                        "bonuses": {"check": "", "save": ""},
                        "check": {"roll": roll_block()}, "save": {"roll": roll_block()},
                        "attack": {"roll": roll_block()}}
        if a in saves and saves[a] is not None:
            delta = int(saves[a]) - (mod(scores[a]) + pb * prof)
            if delta:
                abilities[a]["bonuses"]["save"] = str(delta)

    # skills: number = total bonus from statblock; "prof"/"expert" also accepted
    skills = {}
    sk_spec = spec.get("skills") or {}
    for key, abil in SKILLS.items():
        value, bonus = 0, ""
        if key in sk_spec:
            v = sk_spec[key]
            if isinstance(v, str) and v.lower() in ("prof", "proficient"):
                value = 1
            elif isinstance(v, str) and v.lower() in ("expert", "expertise"):
                value = 2
            else:
                tot = int(v)
                base = mod(scores[abil])
                options = {0: base, 1: base + pb, 2: base + 2 * pb}
                value = min(options, key=lambda k: (abs(options[k] - tot), -k))
                delta = tot - options[value]
                if delta:
                    bonus = str(delta)
        skills[key] = {"ability": abil, "roll": roll_block(), "value": value,
                       "bonuses": {"check": bonus, "passive": ""}}

    # speed / senses
    speed = {k: str(v) for k, v in (spec.get("speed") or {"walk": 30}).items() if v}
    senses = {k: as_number(v) for k, v in (spec.get("senses") or {}).items()}
    for k in ("darkvision", "blindsight", "tremorsense", "truesight"):
        senses.setdefault(k, None)

    # AC
    ac_val = as_number(spec.get("ac", 10))
    if fmt == "v5":
        ac = {"flat": ac_val, "calc": "natural", "formula": ""}
        movement = {"burrow": None, "climb": None, "fly": None, "swim": None, "walk": None,
                    "units": "ft", "hover": bool(spec.get("hover"))}
        movement.update({k: as_number(v) for k, v in speed.items()})
        senses_block = dict(senses, units="ft", special=spec.get("senses_special", ""))
    else:
        ac = {"flat": ac_val, "calcs": ["natural"], "formulas": [], "override": None}
        movement = {"units": None, "hover": bool(spec.get("hover")),
                    "ignoredDifficultTerrain": [], "speeds": speed}
        senses_block = {"units": None, "special": spec.get("senses_special", ""), "ranges": senses}

    hp = int(spec.get("hp", 1))
    init_total = spec.get("initiative")
    init_bonus = ""
    if init_total is not None:
        d = int(init_total) - mod(scores["dex"])
        init_bonus = str(d) if d else ""

    def trait(key):
        vals = norm_list(spec.get(key))
        known = [v for v in vals if v in DAMAGE_TYPES or v in CONDITIONS]
        unknown = [v for v in vals if v not in known]
        extra = spec.get(key + "_custom")
        extra = [extra] if isinstance(extra, str) and extra else list(extra or [])
        custom = "; ".join(unknown + extra)
        block = {"value": known, "custom": custom}
        if key != "ci":
            block["bypasses"] = norm_list(spec.get(key + "_bypasses"))
        return block

    langs = norm_list(spec.get("languages"))
    lc = spec.get("languages_custom")
    lang_custom = [lc] if isinstance(lc, str) and lc else list(lc or [])
    if spec.get("telepathy"):
        lang_custom.append(f"telepathy {spec['telepathy']} ft.")

    ctx = {"pb": pb, "abilities": scores, "spell_ability": spec.get("spellcasting_ability")}

    items, warnings = [], []
    for it in spec.get("items") or []:
        items.append(build_item(it, ctx, rules))

    leg_actions = int(spec.get("legendary_actions", 0) or 0)
    leg_res = int(spec.get("legendary_resistance", 0) or 0)
    if leg_res and not any(s.get("legendary_resistance") for s in spec.get("items") or []):
        warnings.append("legendary_resistance set but no item with legendary_resistance:true")

    system = {
        "abilities": abilities,
        "attributes": {
            "init": {"ability": "", "roll": dict(roll_block(), bonus=init_bonus)},
            "movement": movement,
            "attunement": {"max": 3},
            "senses": senses_block,
            "spellcasting": spec.get("spellcasting_ability", ""),
            "exhaustion": 0,
            "concentration": {"ability": "", "roll": roll_block(), "limit": 1},
            "ac": ac,
            "hd": {"spent": 0},
            "hp": {"value": hp, "max": hp, "temp": None, "tempmax": None,
                   "formula": str(spec.get("hp_formula", "")).replace(" ", "").replace("+", " + ")},
            "death": {"roll": roll_block(), "success": 0, "failure": 0},
            "spell": {"level": int(spec.get("spell_level", 0) or 0)},
            "loyalty": {"value": None},
            "price": {"value": None, "denomination": "gp"},
        },
        "details": {
            "biography": {"value": html(spec.get("biography", "")), "public": ""},
            "alignment": spec.get("alignment", ""),
            "ideal": "", "bond": "", "flaw": "", "race": None,
            "type": {"value": ctype, "subtype": spec.get("subtype", ""), "swarm": spec.get("swarm", ""),
                     "custom": custom_type},
            "cr": cr,
            "habitat": {"value": [{"type": h} for h in norm_list(spec.get("habitat"))], "custom": spec.get("habitat_custom", "")},
            "treasure": {"value": norm_list(spec.get("treasure"))},
        },
        "traits": {
            "size": size,
            "di": trait("di"), "dr": trait("dr"), "dv": trait("dv"),
            "dm": {"amount": {}, "bypasses": []},
            "ci": trait("ci"),
            "languages": {"value": langs, "custom": "; ".join(lang_custom), "communication": {}},
            "important": False,
        },
        "currency": {"pp": 0, "gp": 0, "ep": 0, "sp": 0, "cp": 0},
        "skills": skills,
        "tools": {},
        "spells": {**{f"spell{i}": {"value": 0, "override": None} for i in range(1, 10)},
                   "pact": {"value": 0, "override": None}},
        "bonuses": {"spell": {"dc": ""}},
        "resources": {"legact": {"max": leg_actions, "spent": 0},
                      "legres": {"max": leg_res, "spent": 0},
                      "lair": {"value": bool(spec.get("lair")), "initiative": None, "inside": False}},
        "source": {"revision": 1, "rules": rules, "book": spec.get("source", ""), "license": ""},
        "identifier": slugify(spec.get("identifier") or name),
        "rolls": {},
    }
    for slot, n in (spec.get("spell_slots") or {}).items():
        key = slot if str(slot).startswith(("spell", "pact")) else f"spell{slot}"
        system["spells"][key] = {"value": int(n), "override": int(n)}

    img = spec.get("img") or DEFAULT_ICONS["npc"]
    token_img = spec.get("token_img") or img
    side = SIZES[size]
    dv = senses.get("darkvision") or 0
    ver = VERSIONS[fmt]
    now = int(time.time() * 1000)
    actor = {
        "name": name, "type": "npc", "img": img, "system": system,
        "prototypeToken": {
            "name": spec.get("token_name", name), "displayName": 20, "actorLink": False,
            "appendNumber": True, "prependAdjective": False,
            "width": side, "height": side,
            "texture": {"src": token_img, "anchorX": 0.5, "anchorY": 0.5, "fit": "contain",
                        "scaleX": 1, "scaleY": 1, "tint": "#ffffff", "alphaThreshold": 0.75},
            "lockRotation": False, "rotation": 0, "alpha": 1,
            "disposition": int(spec.get("disposition", -1)),
            "displayBars": 40, "bar1": {"attribute": "attributes.hp"}, "bar2": {"attribute": None},
            "light": {"negative": False, "priority": 0, "alpha": 0.5, "angle": 360, "bright": 0,
                      "color": None, "coloration": 1, "dim": 0, "attenuation": 0.5,
                      "luminosity": 0.5, "saturation": 0, "contrast": 0, "shadows": 0,
                      "animation": {"type": None, "speed": 5, "intensity": 5, "reverse": False},
                      "darkness": {"min": 0, "max": 1}},
            "sight": {"enabled": False, "range": dv, "angle": 360,
                      "visionMode": "darkvision" if dv else "basic", "color": None,
                      "attenuation": 0.1, "brightness": 0, "saturation": 0, "contrast": 0},
            "detectionModes": [] if fmt == "v5" else {},
            "occludable": {"radius": 0},
            "ring": {"enabled": False, "colors": {"ring": None, "background": None},
                     "effects": 1, "subject": {"scale": 1, "texture": None}},
            "flags": {}, "randomImg": False,
        },
        "items": items,
        "effects": [],
        "folder": None,
        "flags": {},
        "_stats": {"coreVersion": ver["coreVersion"], "systemId": "dnd5e",
                   "systemVersion": ver["systemVersion"], "createdTime": now,
                   "modifiedTime": now, "lastModifiedBy": None,
                   "compendiumSource": None, "duplicateSource": None, "exportSource": None},
        "ownership": {"default": 0},
    }
    return actor, warnings


def build(spec, fmt="v6"):
    kind = spec.get("kind", "npc")
    if kind == "npc":
        return build_npc(spec, fmt)
    if kind == "item":
        item = build_item(spec, None, str(spec.get("rules", "2024")))
        ver = VERSIONS[fmt]
        item["_stats"] = {"coreVersion": ver["coreVersion"], "systemId": "dnd5e",
                          "systemVersion": ver["systemVersion"]}
        item.pop("_id")
        return item, []
    raise SpecError(f"unknown kind '{kind}' (npc | item)")


def _welcome(argv):
    """Colored banner: once on the first interactive run, or on demand with --banner."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import banner
    except Exception:
        return False
    if "--banner" in argv:
        banner.show()
        return True
    banner.maybe_show_first_run()
    return False


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if _welcome(argv):
        return 0
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("spec", help="spec JSON file ('-' for stdin)")
    p.add_argument("-o", "--output", help="output file (default: fvtt-<Type>-<slug>.json beside spec)")
    p.add_argument("--format", choices=sorted(VERSIONS), default="v6",
                   help="v6 = dnd5e 6.x / Foundry v14 (default); v5 = dnd5e 5.x / Foundry v13")
    p.add_argument("--stdout", action="store_true", help="print JSON instead of writing a file")
    p.add_argument("--seed", type=int, help="random seed for reproducible IDs")
    p.add_argument("--banner", action="store_true", help="show the GMB banner and exit")
    a = p.parse_args(argv)
    if a.seed is not None:
        random.seed(a.seed)

    raw = sys.stdin.read() if a.spec == "-" else Path(a.spec).read_text(encoding="utf-8")
    spec = json.loads(raw)
    specs = spec if isinstance(spec, list) else [spec]
    outputs = []
    try:
        for s in specs:
            doc, warnings = build(s, a.format)
            for w in warnings:
                print(f"warning: {w}", file=sys.stderr)
            outputs.append(doc)
    except SpecError as e:
        print(f"spec error: {e}", file=sys.stderr)
        return 2

    if a.stdout:
        print(json.dumps(outputs[0] if len(outputs) == 1 else outputs, ensure_ascii=False, indent=2))
        return 0
    base_dir = Path(a.spec).parent if a.spec != "-" else Path.cwd()
    for i, doc in enumerate(outputs):
        if a.output and len(outputs) == 1:
            out = Path(a.output)
        else:
            kind = "Actor" if doc.get("type") == "npc" else "Item"
            out = (Path(a.output).parent if a.output else base_dir) / f"fvtt-{kind}-{slugify(doc['name'])}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
