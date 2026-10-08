#!/usr/bin/env python3
"""
validate_foundry.py — sanity-checks a Foundry VTT dnd5e Actor/Item JSON and
prints a short statblock summary so a human (or an agent) can eyeball it
against the source text.

    python validate_foundry.py fvtt-Actor-nothic.json [more.json ...]
    python validate_foundry.py out.json --quiet      # errors only

Exit code 0 = no errors (warnings allowed), 1 = errors found.
Checks structure that breaks imports or rolls: IDs, activity keys, enums,
cross-references between activities and effects, numeric fields.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_foundry import (ABILITIES, ACTIVATIONS, CONDITIONS, CREATURE_TYPES,  # noqa: E402
                           DAMAGE_TYPES, HEAL_TYPES, SIZES, SKILLS, TEMPLATE_TYPES,
                           mod, prof_bonus)

ID_RE = re.compile(r"^[A-Za-z0-9]{16}$")
ITEM_TYPES = {"feat", "weapon", "spell", "equipment", "consumable", "loot",
              "tool", "container", "background", "class", "subclass", "race"}
ACTIVITY_TYPES = {"attack", "save", "damage", "heal", "utility", "cast",
                  "check", "summon", "enchant", "forward", "transform", "order"}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def check_damage_parts(r, where, parts):
    for i, p in enumerate(parts or []):
        for t in p.get("types", []):
            if t not in DAMAGE_TYPES and t not in HEAL_TYPES:
                r.err(where, f"damage part {i}: unknown type '{t}'")
        custom = (p.get("custom") or {}).get("enabled")
        if not custom and p.get("denomination") and not p.get("number"):
            r.err(where, f"damage part {i}: denomination without number")


def check_item(r, item, where, seen_ids, top_level=False):
    itype = item.get("type")
    if itype not in ITEM_TYPES:
        r.err(where, f"unknown item type '{itype}'")
    if not item.get("name"):
        r.err(where, "item without name")
    if not top_level:
        iid = item.get("_id")
        if not iid or not ID_RE.match(iid):
            r.err(where, f"bad _id '{iid}' (need 16 alphanumeric chars)")
        elif iid in seen_ids:
            r.err(where, f"duplicate _id '{iid}'")
        seen_ids.add(iid)
    sysd = item.get("system") or {}
    if "description" not in sysd:
        r.warn(where, "no system.description")
    eff_ids = {e.get("_id") for e in item.get("effects") or []}
    for e in item.get("effects") or []:
        if not ID_RE.match(str(e.get("_id", ""))):
            r.err(where, f"effect with bad _id '{e.get('_id')}'")
        for st in e.get("statuses", []):
            if st not in CONDITIONS:
                r.warn(where, f"effect status '{st}' is not a standard condition")
    acts = sysd.get("activities") or {}
    if not isinstance(acts, dict):
        r.err(where, "system.activities must be an object keyed by activity _id")
        acts = {}
    for key, a in acts.items():
        aw = f"{where} › activity {a.get('type')}"
        if a.get("_id") != key:
            r.err(aw, f"key '{key}' != _id '{a.get('_id')}'")
        if not ID_RE.match(str(key)):
            r.err(aw, f"bad activity id '{key}'")
        if a.get("type") not in ACTIVITY_TYPES:
            r.err(aw, f"unknown activity type '{a.get('type')}'")
        act_t = (a.get("activation") or {}).get("type", "")
        if act_t not in ACTIVATIONS:
            r.err(aw, f"unknown activation '{act_t}'")
        tpl = ((a.get("target") or {}).get("template") or {}).get("type", "")
        if tpl and tpl not in TEMPLATE_TYPES:
            r.err(aw, f"unknown template type '{tpl}'")
        if a.get("type") == "save":
            ab = (a.get("save") or {}).get("ability", [])
            if not ab:
                r.err(aw, "save without ability")
            for x in ab:
                if x not in ABILITIES:
                    r.err(aw, f"unknown save ability '{x}'")
        dmg = a.get("damage") or {}
        check_damage_parts(r, aw, dmg.get("parts"))
        if a.get("type") == "heal":
            check_damage_parts(r, aw, [a.get("healing") or {}])
        for ref in a.get("effects") or []:
            if ref.get("_id") not in eff_ids:
                r.err(aw, f"references missing effect '{ref.get('_id')}'")
        for t in (a.get("consumption") or {}).get("targets", []):
            if t.get("type") == "itemUses" and not (sysd.get("uses") or {}).get("max"):
                r.warn(aw, "consumes item uses but item has no uses.max")
    if itype == "weapon":
        base = ((sysd.get("damage") or {}).get("base")) or {}
        check_damage_parts(r, where + " › base damage", [base])
        if not any(a.get("type") == "attack" for a in acts.values()):
            r.warn(where, "weapon without attack activity (it will not roll)")
    if itype == "spell":
        lvl = sysd.get("level")
        if not isinstance(lvl, int) or not 0 <= lvl <= 9:
            r.err(where, f"spell level must be 0-9, got {lvl!r}")


def check_actor(r, doc):
    s = doc.get("system") or {}
    ab = s.get("abilities") or {}
    for a in ABILITIES:
        v = (ab.get(a) or {}).get("value")
        if not isinstance(v, int) or not 1 <= v <= 30:
            r.err("abilities", f"{a} = {v!r} (expected 1-30)")
    attr = s.get("attributes") or {}
    hp = attr.get("hp") or {}
    if not hp.get("max") or hp.get("max") <= 0:
        r.err("hp", f"max = {hp.get('max')!r}")
    if hp.get("value") != hp.get("max"):
        r.warn("hp", "value != max")
    traits = s.get("traits") or {}
    if traits.get("size") not in SIZES:
        r.err("traits.size", f"'{traits.get('size')}'")
    t = ((s.get("details") or {}).get("type") or {}).get("value")
    if t not in CREATURE_TYPES and t != "custom":
        r.err("details.type", f"'{t}'")
    for k in ("di", "dr", "dv"):
        for v in (traits.get(k) or {}).get("value", []):
            if v not in DAMAGE_TYPES and v not in CONDITIONS:
                r.err(f"traits.{k}", f"unknown '{v}' (move to custom)")
    for v in (traits.get("ci") or {}).get("value", []):
        if v not in CONDITIONS:
            r.err("traits.ci", f"unknown condition '{v}'")
    for k, sk in (s.get("skills") or {}).items():
        if k not in SKILLS:
            r.err("skills", f"unknown skill '{k}'")
        if sk.get("value") not in (0, 0.5, 1, 2):
            r.err("skills", f"{k}.value = {sk.get('value')!r}")
    seen = set()
    legendary_used = False
    for it in doc.get("items") or []:
        check_item(r, it, f"item «{it.get('name')}»", seen)
        for a in ((it.get("system") or {}).get("activities") or {}).values():
            if (a.get("activation") or {}).get("type") == "legendary":
                legendary_used = True
    res = s.get("resources") or {}
    if legendary_used and not (res.get("legact") or {}).get("max"):
        r.warn("resources.legact", "legendary actions present but legact.max = 0")
    if not doc.get("prototypeToken"):
        r.warn("prototypeToken", "missing — Foundry will use defaults")


def fmt_mod(n):
    return f"+{n}" if n >= 0 else str(n)


def default_ability(item, scores):
    props = item["system"].get("properties") or []
    wtype = (item["system"].get("type") or {}).get("value", "")
    atk = next((a for a in (item["system"].get("activities") or {}).values() if a["type"] == "attack"), None)
    kind = ((atk or {}).get("attack") or {}).get("type", {}).get("value", "")
    if kind == "ranged" or wtype.endswith("R"):
        return "dex"
    if "fin" in props or wtype == "natural":
        return max(("str", "dex"), key=lambda a: mod(scores[a]["value"]))
    return "str"


def summary(doc):
    if doc.get("type") != "npc":
        s = doc.get("system", {})
        acts = ", ".join(a.get("type") for a in (s.get("activities") or {}).values()) or "—"
        return f"[{doc.get('type')}] {doc.get('name')}  activities: {acts}"
    s = doc["system"]
    attr, det, tr = s["attributes"], s["details"], s["traits"]
    cr = det.get("cr", 0)
    pb = prof_bonus(cr)
    ac = attr["ac"].get("flat") or "/".join(attr["ac"].get("calcs") or [attr["ac"].get("calc") or "default"])
    speeds = (attr["movement"].get("speeds") if "speeds" in attr["movement"]
              else {k: v for k, v in attr["movement"].items() if k in ("walk", "fly", "swim", "climb", "burrow")})
    speeds = {k: v for k, v in speeds.items() if v and str(v) != "0"}
    sens = attr["senses"].get("ranges") if "ranges" in attr["senses"] else attr["senses"]
    sens = {k: v for k, v in sens.items() if k in ("darkvision", "blindsight", "tremorsense", "truesight") and v}
    lines = [
        f"══ {doc['name']} ══  ({tr['size']} {det['type']['value']}"
        f"{', ' + det['type'].get('subtype') if det['type'].get('subtype') else ''}; CR {cr}, PB +{pb})",
        f"AC {ac}   HP {attr['hp']['max']} ({attr['hp'].get('formula') or '—'})   Speed "
        + ", ".join(f"{k} {v}" for k, v in speeds.items()),
        "  ".join(f"{a.upper()} {s['abilities'][a]['value']} ({fmt_mod(mod(s['abilities'][a]['value']))})" for a in ABILITIES),
    ]
    saves = [f"{a.upper()} {fmt_mod(mod(s['abilities'][a]['value']) + pb + int(s['abilities'][a].get('bonuses', {}).get('save') or 0))}"
             for a in ABILITIES if s["abilities"][a].get("proficient")]
    if saves:
        lines.append("Saves: " + ", ".join(saves))
    sk = []
    for k, v in s["skills"].items():
        if v.get("value"):
            tot = mod(s["abilities"][v["ability"]]["value"]) + int(pb * v["value"]) + int(v.get("bonuses", {}).get("check") or 0)
            sk.append(f"{k} {fmt_mod(tot)}")
    if sk:
        lines.append("Skills: " + ", ".join(sk))
    for k, label in (("di", "Immune"), ("dr", "Resist"), ("dv", "Vulnerable"), ("ci", "Cond. immune")):
        v = tr[k].get("value", []) + ([tr[k]["custom"]] if tr[k].get("custom") else [])
        if v:
            lines.append(f"{label}: {', '.join(v)}")
    if sens:
        lines.append("Senses: " + ", ".join(f"{k} {v}" for k, v in sens.items()))
    langs = tr["languages"]["value"] + ([tr["languages"]["custom"]] if tr["languages"].get("custom") else [])
    if langs:
        lines.append("Languages: " + ", ".join(langs))
    res = s["resources"]
    if res["legact"]["max"] or res["legres"]["max"]:
        lines.append(f"Legendary actions {res['legact']['max']}, legendary resistance {res['legres']['max']}")
    lines.append("Items:")
    for it in doc.get("items", []):
        bits = []
        for a in (it["system"].get("activities") or {}).values():
            act = a.get("activation", {}).get("type") or "passive"
            b = f"{a['type']}/{act}"
            if a["type"] == "attack":
                at = a["attack"]
                abil = at.get("ability") or default_ability(it, s["abilities"])
                tot = (mod(s["abilities"][abil]["value"]) + pb if abil in ABILITIES else 0) + int(at.get("bonus") or 0)
                b += f" {fmt_mod(tot)} to hit"
            if a["type"] == "save":
                b += f" DC {a['save']['dc'].get('formula') or a['save']['dc'].get('calculation')} {'/'.join(a['save']['ability'])}"
            bits.append(b)
        if it["type"] == "weapon":
            base = it["system"]["damage"]["base"]
            atk = next((a for a in it["system"]["activities"].values() if a["type"] == "attack"), None)
            abil = (atk["attack"].get("ability") or default_ability(it, s["abilities"])) if atk else ""
            m = mod(s["abilities"][abil]["value"]) if abil in ABILITIES else 0
            if base.get("number"):
                tot_b = m + int(base.get("bonus") or 0)
                bits.append(f"dmg {base['number']}d{base['denomination']}{fmt_mod(tot_b) if tot_b else ''} {'/'.join(base['types'])}")
        uses = it["system"].get("uses") or {}
        if uses.get("max"):
            rec = uses.get("recovery") or [{}]
            per = rec[0].get("period", "")
            if per == "recharge":
                per = f"recharge {rec[0].get('formula', '6')}-6"
            bits.append(f"uses {uses['max']}/{per}")
        lines.append(f"  • [{it['type']}] {it['name']}: " + ("; ".join(bits) if bits else "passive"))
    return "\n".join(lines)


def validate_doc(doc):
    r = Report()
    if not isinstance(doc, dict):
        r.err("root", "document must be a JSON object")
        return r
    if not doc.get("name"):
        r.err("root", "missing name")
    if "system" not in doc:
        r.err("root", "missing system")
        return r
    if doc.get("type") == "npc" or doc.get("type") == "character":
        check_actor(r, doc)
    else:
        check_item(r, doc, f"item «{doc.get('name')}»", set(), top_level=True)
    return r


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    quiet = "--quiet" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 1
    bad = False
    for f in files:
        try:
            doc = json.loads(Path(f).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"✗ {f}: invalid JSON — {e}")
            bad = True
            continue
        r = validate_doc(doc)
        status = "✗" if r.errors else "✓"
        print(f"{status} {f}: {len(r.errors)} error(s), {len(r.warnings)} warning(s)")
        for e in r.errors:
            print(f"   ERROR   {e}")
        for w in r.warnings:
            print(f"   warning {w}")
        if not quiet and not r.errors:
            print(summary(doc))
        bad = bad or bool(r.errors)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
