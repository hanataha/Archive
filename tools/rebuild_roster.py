#!/usr/bin/env python3
import json, re
from pathlib import Path

W = Path("/workspace/grok_export_redo/wiki")
DATA = W / "data"
LIB = Path("/workspace/grok_export_redo/library")
CHATS = Path("/workspace/grok_export_redo/chats")
EX = W / "extracts"
WEB = Path("/workspace/grok_export_redo/web/data.js")

sagas = json.loads((DATA / "sagas.json").read_text())
places = json.loads((DATA / "places.json").read_text())
old = json.loads(re.search(r"window\.MT_DATA\s*=\s*(\{.*\})", WEB.read_text(), re.S).group(1))

def slugify(t: str) -> str:
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:72] or "x"

VERBISH = re.compile(
    r"\b(and|the|was|were|have|has|had|will|would|can|could|against|behind|before|"
    r"after|during|when|while|chapter|birth|body|both|but|party|struggled|waited|"
    r"reforms|divine|ahegao|sisters|opened|continued|screaming|university|tomorrow|"
    r"cycle|repeat|nothing|everywhere|influence|beyond|center|cherish|moment)\b",
    re.I,
)

def is_clean_name(n: str) -> bool:
    n = n.strip()
    if not n or len(n) < 2 or len(n) > 55:
        return False
    if re.search(r"\d", n) and not re.search(r"\b(II|III|IV)\b", n):
        return False
    if re.search(r"[.!?:,/]", n):
        return False
    if "—" in n:
        return False
    if VERBISH.search(n):
        return False
    words = n.split()
    if not (1 <= len(words) <= 4):
        return False
    small = {"of", "de", "von", "van", "da", "del", "la", "le"}
    for w in words:
        if w.lower() in small:
            continue
        ch0 = w[0]
        if not (ch0.isupper() or "\u4e00" <= ch0 <= "\u9fff" or "가" <= ch0 <= "힣"):
            return False
    return True

characters = {}
whitelist_lower = set()

def upsert(name: str, **kw):
    name = name.strip()
    if not name:
        return None
    if not is_clean_name(name) and name.lower() not in whitelist_lower:
        return None
    cid = "char-" + slugify(name)
    scope = kw.pop("scope", None)
    if scope:
        cid = f"{cid}--{scope}"
    if cid not in characters:
        characters[cid] = {
            "id": cid,
            "name": name,
            "aliases": [],
            "sagaIds": [],
            "primarySagaId": "",
            "role": "",
            "uniqueTitle": "",
            "relationshipToEon": "",
            "biography": "",
            "appearance": "",
            "personality": "",
            "powers": "",
            "status": "",
            "ranks": "",
            "evolution": [],
            "placesRelated": [],
            "details": {},
            "sourceExcerpts": [],
        }
    ch = characters[cid]
    for k, v in kw.items():
        if k == "sagaId" and v:
            if v not in ch["sagaIds"]:
                ch["sagaIds"].append(v)
            if not ch["primarySagaId"]:
                ch["primarySagaId"] = v
        elif k == "aliases" and v:
            for a in v:
                if a and a not in ch["aliases"] and a != ch["name"]:
                    ch["aliases"].append(a)
        elif k == "sourceExcerpts" and v:
            for e in v:
                if e and e not in ch["sourceExcerpts"]:
                    ch["sourceExcerpts"].append(e[:400])
        elif k == "evolution" and v and not ch["evolution"]:
            ch["evolution"] = v
        elif k == "details" and v:
            ch["details"].update(v)
        elif isinstance(v, str) and v and len(v) > len(ch.get(k) or ""):
            ch[k] = v
    return cid

# Old characters
for c in old["characters"]:
    whitelist_lower.add(c["name"].lower())
    upsert(c["name"], biography=c.get("summary") or "", role=(c.get("summary") or "")[:200])

for s in old["sagas"]:
    ns = next((x for x in sagas if x["num"] == s["num"]), None)
    if not ns:
        continue
    for mt in s.get("meatToilets") or []:
        nm = mt.get("name") or ""
        if not nm:
            continue
        whitelist_lower.add(nm.lower())
        upsert(
            nm,
            sagaId=ns["id"],
            role=mt.get("role") or "",
            uniqueTitle=mt.get("role") or "",
            relationshipToEon=mt.get("role") or "",
            biography=(mt.get("role") or nm),
        )

def parse_titles(text):
    for part in re.split(r"\nTITLE\s*[—\-]\s*", text)[1:]:
        lines = part.splitlines()
        nameline = lines[0].strip()
        name = re.split(r"\s*\(|/", nameline)[0].strip()
        aliases = []
        m = re.search(r"\(([^)]+)\)", nameline)
        if m:
            aliases = [a.strip() for a in re.split(r"[/,]", m.group(1)) if a.strip() and len(a) < 50]
        fields = {}
        for ln in lines[1:]:
            if ln.startswith("TITLE"):
                break
            if ":" in ln[:60]:
                k, v = ln.split(":", 1)
                fields[k.strip().lower()] = v.strip()
        yield name, aliases, fields, "\n".join(lines[1:80])

for p in list(LIB.glob("MT_*Template*.md")) + [LIB / "xuanye_meat_toilet_template.md"]:
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for name, aliases, fields, body in parse_titles(text):
        whitelist_lower.add(name.lower())
        app = "\n".join(
            filter(
                None,
                [
                    fields.get("height / body"),
                    fields.get("hair / eyes / scent / marks"),
                    fields.get("clothes default / access-modified") or fields.get("clothes default"),
                ],
            )
        )
        bio = (
            "\n\n".join(
                filter(
                    None,
                    [
                        fields.get("origin"),
                        fields.get("sexual role + holes used"),
                        fields.get("fertility / pregnancy history"),
                    ],
                )
            )
            or body[:2500]
        )
        evo = [
            {"title": k, "summary": fields[k][:500]}
            for k in ("fertility / pregnancy history", "age appearance / freeze", "origin")
            if fields.get(k)
        ]
        details = {k: fields[k][:800] for k in ("hard rules", "distinct from", "collar / tag / leash") if fields.get(k)}
        upsert(
            name,
            aliases=aliases,
            role=fields.get("status") or "",
            uniqueTitle=fields.get("status") or "",
            relationshipToEon=fields.get("status") or "",
            biography=bio[:3500],
            appearance=app[:1500],
            personality=fields.get("personality public / private") or "",
            powers=fields.get("powers") or "",
            status=fields.get("status") or "",
            evolution=evo,
            details=details,
            sourceExcerpts=[f"Template {p.name}"],
        )

for ep in EX.glob("*.json"):
    if ep.name.startswith("_"):
        continue
    ex = json.loads(ep.read_text())
    sid = ex["id"]
    for raw in ex.get("dumpNames") or []:
        if "—" not in raw:
            continue
        left, right = raw.split("—", 1)
        name = left.split("/")[0].strip()
        name = re.sub(r"\s*\(.*\)$", "", name).strip()
        role = right.strip()[:300]
        if not is_clean_name(name):
            continue
        whitelist_lower.add(name.lower())
        upsert(
            name,
            sagaId=sid,
            role=role,
            uniqueTitle=role,
            relationshipToEon=role,
            biography=raw[:900],
            sourceExcerpts=[raw[:400]],
        )

for s in sagas:
    p = CHATS / f"{s['hex']}.md"
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"^([A-Z][^—\n]{1,50})\s*—\s*(.+)$", text, re.M):
        name = m.group(1).split("/")[0].strip()
        name = re.sub(r"\s*\(.*\)$", "", name).strip()
        role = m.group(2).strip()[:300]
        if not is_clean_name(name):
            continue
        if len(role) < 10:
            continue
        whitelist_lower.add(name.lower())
        upsert(
            name,
            sagaId=s["id"],
            role=role,
            uniqueTitle=role,
            relationshipToEon=role,
            biography=f"{name} — {role}",
            sourceExcerpts=[f"{name} — {role}"],
        )

old_names = {c["name"].lower() for c in old["characters"]}
char_list = sorted(characters.values(), key=lambda c: c["name"].lower())
char_list = [c for c in char_list if is_clean_name(c["name"]) or c["name"].lower() in old_names]

for s in sagas:
    ids = []
    for c in char_list:
        if s["id"] in c["sagaIds"] and c["id"] not in ids:
            ids.append(c["id"])
    os = next((x for x in old["sagas"] if x["num"] == s["num"]), None)
    if os:
        for mt in os.get("meatToilets") or []:
            nm = (mt.get("name") or "").lower()
            for c in char_list:
                if c["name"].lower() == nm and c["id"] not in ids:
                    ids.append(c["id"])
                    if s["id"] not in c["sagaIds"]:
                        c["sagaIds"].append(s["id"])
    s["meatToiletIds"] = ids
    s["counts"]["meatToilets"] = len(ids)

def is_clean_place(n: str) -> bool:
    n = n.strip()
    if not n or len(n) < 3 or len(n) > 70:
        return False
    if re.search(
        r"^(access:|age|after |adult|ahegao|a leaf|create |fill |every |eon walks|file |saved |schema|mt |title|status|origin:|height|hair |clothes|collar|powers|sexual|note|dump |category |worked |cover story|trio |echo-|demc)",
        n,
        re.I,
    ):
        return False
    if n.count(" ") >= 7:
        return False
    if re.search(r"\b(Lv\s*\d|H-cup|LOCKED|maidenhood)\b", n):
        return False
    return True

place_list = [p for p in places if is_clean_place(p["name"])]
kept_p = {p["id"] for p in place_list}
for s in sagas:
    ids = [i for i in (s.get("placeIds") or []) if i in kept_p]
    for p in place_list:
        if s["id"] in p.get("sagaIds", []) and p["id"] not in ids:
            ids.append(p["id"])
    s["placeIds"] = ids
    s["counts"]["places"] = len(ids)

meta = {
    "title": "Eon Saga Fandom Wiki",
    "sagaCount": len(sagas),
    "characterCount": len(char_list),
    "placeCount": len(place_list),
    "source": "full_chats + chats dumps + library + SAGA index",
    "adult": True,
    "notes": "Built from existing exports only. NSFW kept faithful to source.",
}
(DATA / "sagas.json").write_text(json.dumps(sagas, ensure_ascii=False, indent=2))
(DATA / "characters.json").write_text(json.dumps(char_list, ensure_ascii=False, indent=2))
(DATA / "places.json").write_text(json.dumps(place_list, ensure_ascii=False, indent=2))
(DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
(W / "data.js").write_text(
    "window.WIKI_DATA = "
    + json.dumps({"meta": meta, "sagas": sagas, "characters": char_list, "places": place_list}, ensure_ascii=False)
    + ";\n"
)
print(json.dumps(meta, indent=2))
print("0 MT", sum(1 for s in sagas if s["counts"]["meatToilets"] == 0))
print("chars", [c["name"] for c in char_list[:40]])
print("rich", sum(1 for c in char_list if len(c.get("biography") or "") > 400))
print("MB", round((W / "data.js").stat().st_size / 1e6, 2))
