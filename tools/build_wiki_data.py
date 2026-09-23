#!/usr/bin/env python3
"""Build fandom-wiki JSON + data.js from extracts, library, old web index, chats dumps."""
from __future__ import annotations
import json, re, unicodedata, html
from pathlib import Path
from collections import defaultdict

ROOT = Path("/workspace/grok_export_redo")
WIKI = ROOT / "wiki"
EX = WIKI / "extracts"
LIB = ROOT / "library"
CHATS = ROOT / "chats"
DATA = WIKI / "data"
DATA.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:72] or "x"

def clean_ws(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def paras(text: str, max_paras: int = 6, max_chars: int = 3500) -> list[str]:
    text = clean_ws(text)
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) <= 1:
        # chunk long single block by sentences
        sents = re.split(r"(?<=[.!?])\s+", text)
        parts, buf = [], ""
        for s in sents:
            if len(buf) + len(s) > 450 and buf:
                parts.append(buf.strip())
                buf = s
            else:
                buf = (buf + " " + s).strip()
        if buf:
            parts.append(buf)
    out, n = [], 0
    for p in parts:
        if len(out) >= max_paras or n >= max_chars:
            break
        out.append(p[:900])
        n += len(p)
    return out

def summarize_user_prompt(first_user: str) -> str:
    """Faithful multi-paragraph premise from the user's opening prompt."""
    ps = paras(first_user, max_paras=6, max_chars=2800)
    if not ps:
        return ""
    # Light framing without inventing: keep user's words as the how-it-started ask
    body = "\n\n".join(ps)
    return body

def short_summary(first_user: str, opening: str, mid: str, late: str, powers: list[str], dump: list[str]) -> str:
    bits = []
    # Setting from opening grok
    op = paras(opening, 2, 900)
    if op:
        bits.append(op[0])
    # Core ask compressed
    fu = re.sub(r"\s+", " ", first_user.strip())
    if len(fu) > 80:
        # first ~2 sentences of user intent
        sents = re.split(r"(?<=[.!?])\s+", fu)
        ask = " ".join(sents[:3])[:500]
        bits.append("Opening ask (condensed from source): " + ask)
    if powers:
        bits.append("Powers / systems called out in-source: " + "; ".join(powers) + ".")
    # Named roster
    clean_names = []
    for d in dump:
        name = d.split("—")[0].split("-")[0].strip()
        name = re.sub(r"\s+", " ", name)
        if 2 < len(name) < 60 and not name.lower().startswith(("schema", "files", "index", "roster", "places", "characters", "result", "the mansion", "when they", "years of", "mealtimes")):
            if name not in clean_names:
                clean_names.append(name)
    if clean_names:
        bits.append("Named figures from dumps/sheets: " + ", ".join(clean_names[:12]) + ".")
    # Arc endpoint hint from late
    lp = paras(late or mid or "", 1, 400)
    if lp:
        bits.append("Later-state snapshot (from late transcript): " + lp[0][:350])
    return "\n\n".join(bits[:5])

def pick_progress(beats: list[dict], story_headers: list[str], turn_count: int) -> list[dict]:
    """Select 8–30 progress beats from user-driven beats + headers."""
    out = []
    # Always include first beat
    for i, b in enumerate(beats):
        title = (b.get("title") or "").strip()
        src = (b.get("summarySource") or "").strip()
        user = (b.get("userSnippet") or "").strip()
        hdrs = b.get("grokHeaders") or []
        # Skip pure "continue / make long" with no substance
        low = user.lower()
        if i > 0 and len(user) < 40 and re.match(r"^(continue|make it|next|go on)", low):
            if not hdrs and not src:
                continue
        # Prefer header as title when available and user title is vague
        use_title = title
        if hdrs and (len(title) < 20 or title.lower().startswith(("continue", "the next", "make it"))):
            use_title = hdrs[0]
        summary = src
        if not summary and user:
            summary = "User direction: " + user[:400]
        else:
            # blend short user intent + grok start
            summary = clean_ws(summary)[:700]
            if user and not user.lower().startswith("continue") and len(user) > 30:
                summary = "Direction: " + user[:220] + "\n\n" + summary
        out.append({"title": use_title[:140], "summary": summary[:900]})
        # target density
        target = 12 if turn_count < 30 else (18 if turn_count < 60 else 26)
        if len(out) >= target:
            break
    # If too few, add story headers as structural beats
    if len(out) < 6 and story_headers:
        for h in story_headers:
            if any(h.lower() in x["title"].lower() for x in out):
                continue
            out.append({"title": h[:140], "summary": f"Story section heading from transcript: {h}"})
            if len(out) >= 10:
                break
    return out[:30]

def important_details(first_user: str, powers: list[str], dump: list[str], beats: list) -> list[str]:
    details = []
    for p in powers:
        details.append(f"Power/system: {p}")
    # Numbers from first user
    for m in re.finditer(r"(\d+\s*cm|\d+\s*inch(?:es)?|\d+\s*(?:years?|kids?|daughters?|wives?|floors?|hours?))", first_user, re.I):
        details.append(f"Stated measure/count: {m.group(1)}")
        if len(details) > 12:
            break
    for d in dump[:15]:
        line = d.strip()
        if len(line) > 20 and len(line) < 220:
            details.append(line)
    # Unique titles / rules phrases
    for pat in [r"exclusive to Eon", r"fertility OFF", r"sleep-?lock", r"inmon", r"DNA firewall", r"private meat", r"専用"]:
        if re.search(pat, first_user + " " + " ".join(dump), re.I):
            details.append(f"Rule/motif present: {pat}")
    # dedupe
    seen, out = set(), []
    for d in details:
        k = d.lower()[:80]
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out[:25]

# ---------- old web ----------
def load_old_web():
    text = (ROOT / "web" / "data.js").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"window\.MT_DATA\s*=\s*(\{.*\})\s*;?\s*$", text, re.S)
    if not m:
        m = re.search(r"window\.MT_DATA\s*=\s*(\{.*\})", text, re.S)
    return json.loads(m.group(1))

# ---------- library character templates ----------
def parse_title_blocks(text: str, saga_hint: str = "") -> list[dict]:
    """Parse TITLE — Name blocks from MT templates."""
    chars = []
    # Split on TITLE — 
    parts = re.split(r"\nTITLE\s*[—\-]\s*", text)
    for part in parts[1:]:
        lines = part.splitlines()
        if not lines:
            continue
        nameline = lines[0].strip()
        name = re.split(r"\s*\(|/", nameline)[0].strip()
        aliases = []
        paren = re.search(r"\(([^)]+)\)", nameline)
        if paren:
            aliases = [a.strip() for a in re.split(r"[/,—]", paren.group(1)) if a.strip()]
        fields = {}
        for ln in lines[1:]:
            if ln.startswith("TITLE"):
                break
            if ":" in ln[:40]:
                k, v = ln.split(":", 1)
                fields[k.strip().lower()] = v.strip()
        body = "\n".join(lines[1:80])
        chars.append({
            "name": name,
            "aliases": aliases,
            "fields": fields,
            "body": body,
            "sagaHint": saga_hint,
        })
    return chars

def load_library_chars() -> list[dict]:
    out = []
    for p in sorted(LIB.glob("MT_*Template*.md")) + sorted(LIB.glob("*_Template.md")) + [LIB / "DEMC_Eon_MeatToilet_Master_Template.md"]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        out.extend(parse_title_blocks(text, saga_hint=p.stem))
    # Also Salaryman template already covered
    # xuanye
    xu = LIB / "xuanye_meat_toilet_template.md"
    if xu.exists():
        t = xu.read_text(encoding="utf-8", errors="replace")
        out.append({
            "name": "Xuanye",
            "aliases": [],
            "fields": {},
            "body": t[:4000],
            "sagaHint": "xuanye",
        })
    return out

# ---------- places ----------
PLACE_TYPE_HINTS = [
    (r"\bworld\b|planet|realm|plane", "world"),
    (r"\bempire\b", "empire"),
    (r"\bkingdom\b", "kingdom"),
    (r"\bcity\b|capital|metropolis|holy city", "city"),
    (r"\bvillage\b|town\b|settlement", "city"),
    (r"\bmansion\b|apartment|academy|cathedral|coliseum|dungeon|grove|caves|onsen|office|cafe|penthouse|domain|estate|enclave|glade|citadel|farm|pens|palace|manor", "venue"),
    (r"\bdomain\b|sanctum|sanctuary", "domain"),
]

def guess_type(name: str, blob: str = "") -> str:
    t = (name + " " + blob).lower()
    for pat, typ in PLACE_TYPE_HINTS:
        if re.search(pat, t):
            return typ
    return "other"

def load_places() -> list[dict]:
    places = {}
    def add(name, typ, summary, details, saga_ids=None, facts=None):
        if not name or len(name) < 2:
            return
        # filter noise
        low = name.lower().strip()
        if low in {"name", "type", "notes", "origin", "function", "pre-existing", "eon-made"}:
            return
        if name.startswith("http") or name.startswith("artifacts/"):
            return
        pid = "place-" + slugify(name)
        if pid in places:
            # merge
            pl = places[pid]
            if summary and len(summary) > len(pl.get("summary") or ""):
                pl["summary"] = summary
            if details and len(details) > len(pl.get("details") or ""):
                pl["details"] = details
            if saga_ids:
                pl["sagaIds"] = sorted(set(pl.get("sagaIds", []) + saga_ids))
            if facts:
                pl["notableFacts"] = list(dict.fromkeys((pl.get("notableFacts") or []) + facts))[:20]
            return
        places[pid] = {
            "id": pid,
            "name": name.strip()[:120],
            "type": typ or guess_type(name, summary or ""),
            "sagaIds": saga_ids or [],
            "summary": (summary or "")[:1200],
            "details": (details or "")[:4000],
            "relatedCharacterIds": [],
            "notableFacts": facts or [],
        }

    # PLACE_* files
    for p in sorted(LIB.glob("PLACE_*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        title = p.stem.replace("PLACE_", "").replace("_", " ")
        # first heading
        m = re.search(r"^#\s+(.+)$", text, re.M)
        if m:
            title = m.group(1).strip()
        add(title, guess_type(title, text), paras(text, 2, 800)[0] if paras(text) else "", text[:3000], facts=[f"Library file: {p.name}"])

    # Gazetteers
    for p in sorted(LIB.glob("MT_*Places*.md")) + sorted(LIB.glob("MT_*Gazetteer*.md")) + [LIB / "DEMC_master_place_roster.md", LIB / "EON_WORLDS_AND_PLACES.md"]:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        # Name lines like "Kingdom of Aetheria" as headings or bold starts
        for m in re.finditer(r"^(?:#{1,3}\s+)?([A-Z][^\n]{2,80})$", text, re.M):
            name = m.group(1).strip()
            if name.lower().startswith(("saved library", "chat:", "file preview", "places gazetteer", "dump date", "related:", "rule:", "search scope", "worlds /", "polities", "cities", "landmarks", "type:", "features", "who controls", "public face", "private", "magic:", "note:", "connected", "event:", "use:", "origin:", "wealth:", "trait:", "seat:", "cover story", "true use", "demc")):
                continue
            if name.startswith("File ") or "—" in name[:3]:
                continue
            # get following block
            start = m.end()
            nxt = text.find("\n", start)
            block = text[start:start+600]
            add(name, guess_type(name, block), clean_ws(block)[:500], clean_ws(block)[:2000], facts=[f"Source: {p.name}"])

        # Table rows Name\tType
        for m in re.finditer(r"^([A-Z][^\t\n]{2,60})\t([^\t\n]+)\t", text, re.M):
            add(m.group(1).strip(), guess_type(m.group(1), m.group(2)), m.group(2).strip()[:400], "", facts=[f"Gazetteer row in {p.name}"])

    return list(places.values())

def parse_dump_chars_from_chat(hex8: str) -> list[dict]:
    p = CHATS / f"{hex8}.md"
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8", errors="replace")
    found = []
    # Females saved blocks
    for m in re.finditer(r"^([A-Z][^—\n]{1,70})\s*—\s*(.+)$", text, re.M):
        name = m.group(1).strip()
        role = m.group(2).strip()[:300]
        if name.lower().startswith(("schema", "characters", "places", "index", "roster", "files", "if you", "females")):
            continue
        found.append({"name": name.split("/")[0].strip(), "aliases": [x.strip() for x in name.split("/")[1:] if x.strip()], "role": role, "raw": f"{name} — {role}"})
    for m in re.finditer(r"TITLE\s*[—\-]\s*([^\n(]+)", text):
        found.append({"name": m.group(1).strip(), "aliases": [], "role": "", "raw": m.group(0)})
    return found

def char_id(name: str, saga_id: str | None = None) -> str:
    base = "char-" + slugify(name)
    if saga_id:
        # scoped if needed later
        return base
    return base

# Known same-name different people — force scope
FORCE_SCOPE = {
    # name lower -> always scope by saga
    "lirael", "elara", "liora", "selene", "lyra", "mira", "seraphina", "elowen",
}

def main():
    old = load_old_web()
    old_by_num = {s["num"]: s for s in old["sagas"]}
    extracts = []
    for p in sorted(EX.glob("*.json")):
        if p.name.startswith("_"):
            continue
        extracts.append(json.loads(p.read_text(encoding="utf-8")))
    extracts.sort(key=lambda e: e["num"])

    lib_chars = load_library_chars()
    places = load_places()
    place_by_name = {pl["name"].lower(): pl for pl in places}

    sagas = []
    characters = {}  # id -> char
    saga_place_links = defaultdict(list)  # sagaId -> placeIds
    thin_notes = []

    # Map old places into place registry + saga links
    for osaga in old["sagas"]:
        sid_old = osaga["id"]
        for pl in osaga.get("places") or []:
            pname = pl.get("name") or ""
            if not pname or len(pname) < 3:
                continue
            if pname.lower().startswith(("french identity", "yamanote")):
                typ = "other"
            else:
                typ = guess_type(pname)
            pid = "place-" + slugify(pname)
            if pid not in {p["id"] for p in places}:
                places.append({
                    "id": pid, "name": pname[:120], "type": typ, "sagaIds": [],
                    "summary": (pl.get("description") or pname)[:800],
                    "details": (pl.get("description") or "")[:2000],
                    "relatedCharacterIds": [], "notableFacts": [],
                })
                place_by_name[pname.lower()] = places[-1]

    places_by_id = {p["id"]: p for p in places}

    for ex in extracts:
        num = ex["num"]
        sid = ex["id"]
        old_s = old_by_num.get(num, {})
        first_user = ex.get("firstUser") or ""
        opening = ex.get("openingGrok") or ex.get("openingGrokFullStart") or ""
        powers = ex.get("powersHints") or []
        dump = ex.get("dumpNames") or []
        beats_raw = ex.get("beats") or []
        headers = ex.get("storyHeaders") or []

        premise = summarize_user_prompt(first_user)
        # Add opening beat as narrative "how it started on-page"
        op_paras = paras(opening, 3, 1600)
        how = premise
        if op_paras:
            how = how + "\n\n" + "\n\n".join(op_paras[:3])
        how = how[:5000]

        short = short_summary(first_user, opening, ex.get("midGrok") or "", ex.get("lateGrok") or "", powers, dump)
        progress = pick_progress(beats_raw, headers, ex.get("turnCount") or 0)
        details = important_details(first_user, powers, dump, beats_raw)

        # Characters for this saga
        mt_ids = []
        # from old web meat toilets
        for mt in old_s.get("meatToilets") or []:
            name = mt.get("name") or ""
            if not name:
                continue
            role = mt.get("role") or ""
            scoped = name.lower().split()[0] in FORCE_SCOPE
            cid = char_id(name, sid if scoped else None)
            if scoped:
                cid = f"{cid}--{slugify(sid)[-20:]}"
            if cid not in characters:
                characters[cid] = {
                    "id": cid,
                    "name": name,
                    "aliases": [],
                    "sagaIds": [],
                    "primarySagaId": sid,
                    "role": role,
                    "uniqueTitle": role,
                    "relationshipToEon": role,
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
            if sid not in ch["sagaIds"]:
                ch["sagaIds"].append(sid)
            if role and not ch["role"]:
                ch["role"] = role
                ch["uniqueTitle"] = role
            if not ch["biography"] and mt.get("details"):
                ch["biography"] = str(mt["details"])[:2000]
            mt_ids.append(cid)

        # from chat dumps
        for d in parse_dump_chars_from_chat(ex["hex"]):
            name = d["name"]
            if len(name) < 2 or name.lower() in {"trio sheet", "echo-clones"}:
                continue
            scoped = name.lower().split()[0] in FORCE_SCOPE
            cid = char_id(name)
            if scoped:
                cid = f"{cid}--s{num:02d}"
            if cid not in characters:
                characters[cid] = {
                    "id": cid, "name": name, "aliases": d.get("aliases") or [],
                    "sagaIds": [], "primarySagaId": sid,
                    "role": d.get("role") or "", "uniqueTitle": d.get("role") or "",
                    "relationshipToEon": d.get("role") or "",
                    "biography": d.get("raw") or "", "appearance": "", "personality": "",
                    "powers": "", "status": "", "ranks": "", "evolution": [],
                    "placesRelated": [], "details": {}, "sourceExcerpts": [d.get("raw","")[:400]] if d.get("raw") else [],
                }
            ch = characters[cid]
            if sid not in ch["sagaIds"]:
                ch["sagaIds"].append(sid)
            if d.get("role") and len(d["role"]) > len(ch.get("role") or ""):
                ch["role"] = d["role"]
                ch["uniqueTitle"] = d["role"]
            if cid not in mt_ids:
                mt_ids.append(cid)

        # Places from old saga
        pids = []
        for pl in old_s.get("places") or []:
            pname = pl.get("name") or ""
            if not pname:
                continue
            pid = "place-" + slugify(pname)
            if pid in places_by_id:
                if sid not in places_by_id[pid]["sagaIds"]:
                    places_by_id[pid]["sagaIds"].append(sid)
                pids.append(pid)
            else:
                # already added above in first pass? ensure
                places_by_id[pid] = {
                    "id": pid, "name": pname[:120], "type": guess_type(pname),
                    "sagaIds": [sid], "summary": (pl.get("description") or "")[:800],
                    "details": "", "relatedCharacterIds": [], "notableFacts": [],
                }
                places.append(places_by_id[pid])
                pids.append(pid)

        # Heuristic place mentions from dump / first user for empty ones
        if not pids:
            blob = first_user + "\n" + "\n".join(dump)
            for pname, pl in list(place_by_name.items())[:]:
                if pname in blob.lower() and len(pname) > 4:
                    pid = pl["id"]
                    if sid not in pl["sagaIds"]:
                        pl["sagaIds"].append(sid)
                    if pid not in pids:
                        pids.append(pid)
                    if len(pids) >= 8:
                        break

        if not premise.strip() or len(progress) < 2:
            thin_notes.append(f"Saga {num} ({ex['title']}): thin premise/progress — turns={ex.get('turnCount')}, beats_kept={len(progress)}")

        saga = {
            "id": sid,
            "num": num,
            "title": ex["title"],
            "url": ex["url"],
            "markers": ex["markers"],
            "chatFile": ex.get("chatFile") or f"{ex['hex']}.md",
            "hex": ex["hex"],
            "premise": how,
            "howItStarted": how,
            "shortSummary": short,
            "progress": progress,
            "powers": powers,
            "importantDetails": details,
            "meatToiletIds": mt_ids,
            "placeIds": pids,
            "counts": {
                "meatToilets": len(mt_ids),
                "places": len(pids),
                "messageCount": ex.get("turnCount") or 0,
                "userTurns": ex.get("userCount") or 0,
            },
            "fullTranscriptPath": f"transcripts/{ex['hex']}.md",
            "rawNotes": (old_s.get("notes") or "")[:1500],
        }
        sagas.append(saga)

    # Enrich characters from library templates
    for lc in lib_chars:
        name = lc["name"]
        if not name or len(name) < 2:
            continue
        cid = char_id(name)
        # try match existing
        match = characters.get(cid)
        if not match:
            # fuzzy: find by name
            for c in characters.values():
                if c["name"].lower() == name.lower() or name.lower() in [a.lower() for a in c.get("aliases", [])]:
                    match = c
                    break
        fields = lc.get("fields") or {}
        body = lc.get("body") or ""
        if not match:
            match = {
                "id": cid, "name": name, "aliases": lc.get("aliases") or [],
                "sagaIds": [], "primarySagaId": "",
                "role": fields.get("status") or "", "uniqueTitle": "",
                "relationshipToEon": fields.get("status") or "",
                "biography": "", "appearance": "", "personality": "",
                "powers": "", "status": fields.get("status") or "",
                "ranks": "", "evolution": [], "placesRelated": [],
                "details": {}, "sourceExcerpts": [],
            }
            characters[cid] = match
        # fill sections from fields
        if fields.get("height / body") or fields.get("hair / eyes / scent / marks"):
            match["appearance"] = clean_ws(
                (fields.get("height / body") or "") + "\n" +
                (fields.get("hair / eyes / scent / marks") or "") + "\n" +
                (fields.get("clothes default / access-modified") or fields.get("clothes default") or "")
            )[:1500]
        if fields.get("personality public / private"):
            match["personality"] = fields["personality public / private"][:1200]
        if fields.get("powers"):
            match["powers"] = fields["powers"][:1200]
        if fields.get("status"):
            match["status"] = fields["status"][:400]
            match["role"] = match["role"] or fields["status"]
        if fields.get("origin"):
            bio = fields["origin"]
            if fields.get("sexual role + holes used"):
                bio += "\n\n" + fields["sexual role + holes used"]
            if fields.get("fertility / pregnancy history"):
                bio += "\n\n" + fields["fertility / pregnancy history"]
            if not match["biography"] or len(bio) > len(match["biography"]):
                match["biography"] = bio[:3500]
        if fields.get("hard rules"):
            match["details"]["hardRules"] = fields["hard rules"][:1000]
        if fields.get("distinct from"):
            match["details"]["distinctFrom"] = fields["distinct from"][:500]
        if fields.get("collar / tag / leash"):
            match["details"]["collar"] = fields["collar / tag / leash"][:400]
        # evolution from fertility / age freeze lines
        evo = []
        for key in ("fertility / pregnancy history", "age appearance / freeze", "origin"):
            if fields.get(key):
                evo.append({"title": key, "summary": fields[key][:500]})
        if evo and not match["evolution"]:
            match["evolution"] = evo
        if body and not match["biography"]:
            match["biography"] = body[:3000]
        if lc.get("aliases"):
            for a in lc["aliases"]:
                if a not in match["aliases"]:
                    match["aliases"].append(a)

    # Link places <-> characters lightly by name mention in bio
    for ch in characters.values():
        blob = (ch.get("biography") or "") + " " + (ch.get("appearance") or "")
        for pl in places:
            if pl["name"].lower() in blob.lower() and len(pl["name"]) > 4:
                if pl["id"] not in ch["placesRelated"]:
                    ch["placesRelated"].append(pl["id"])
                if ch["id"] not in pl["relatedCharacterIds"]:
                    pl["relatedCharacterIds"].append(ch["id"])

    # Ensure every saga has non-empty strings
    for s in sagas:
        if not s["shortSummary"]:
            s["shortSummary"] = s["premise"][:800] or s["title"]
        if not s["premise"]:
            s["premise"] = f"Source transcript: {s['fullTranscriptPath']}. Opening user prompt was empty or scrape started mid-chat."
            thin_notes.append(f"Saga {s['num']}: empty firstUser — mid-scrape start")
        if not s["progress"]:
            s["progress"] = [{"title": "Full transcript", "summary": "No discrete user beats extracted; open the full saga transcript."}]
            thin_notes.append(f"Saga {s['num']}: no progress beats")

    char_list = sorted(characters.values(), key=lambda c: c["name"].lower())
    # prune places with no saga and no details? keep library ones
    place_list = sorted(places_by_id.values(), key=lambda p: p["name"].lower())

    meta = {
        "title": "Eon Saga Fandom Wiki",
        "sagaCount": len(sagas),
        "characterCount": len(char_list),
        "placeCount": len(place_list),
        "source": "full_chats + chats dumps + library + SAGA index",
        "adult": True,
        "notes": "Built from existing exports only. NSFW kept faithful to source.",
    }

    (DATA / "sagas.json").write_text(json.dumps(sagas, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "characters.json").write_text(json.dumps(char_list, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "places.json").write_text(json.dumps(place_list, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    bundle = {"meta": meta, "sagas": sagas, "characters": char_list, "places": place_list}
    (WIKI / "data.js").write_text(
        "window.WIKI_DATA = " + json.dumps(bundle, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )

    prog = WIKI / "PROGRESS.md"
    lines = [
        "# Wiki build progress",
        "",
        f"- Sagas: {len(sagas)}",
        f"- Characters: {len(char_list)}",
        f"- Places: {len(place_list)}",
        "",
        "## Source-thin / notes",
        "",
    ]
    if thin_notes:
        lines.extend(f"- {n}" for n in thin_notes)
    else:
        lines.append("- None flagged.")
    # list sagas with few MTs
    lines.append("\n## Sagas with 0 linked MTs\n")
    for s in sagas:
        if s["counts"]["meatToilets"] == 0:
            lines.append(f"- {s['num']}. {s['title']} (markers {s['markers']})")
    lines.append("\n## Sagas with 0 places\n")
    for s in sagas:
        if s["counts"]["places"] == 0:
            lines.append(f"- {s['num']}. {s['title']}")
    prog.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(meta, indent=2))
    print("thin:", len(thin_notes))
    print("wrote", DATA, "and data.js", (WIKI/"data.js").stat().st_size)

if __name__ == "__main__":
    main()
