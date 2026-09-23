#!/usr/bin/env python3
"""Enrich wiki data: templates + transcript mining + wiki-prose rewrite helpers."""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path
from collections import defaultdict

ROOT = Path("/workspace/grok_export_redo")
WIKI = ROOT / "wiki"
LIB = ROOT / "library"
FULL = ROOT / "full_chats"
CHATS = ROOT / "chats"
EX = WIKI / "extracts"
DATA_DIR = WIKI / "data"

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

def paras(text: str, n: int = 4, maxlen: int = 2000) -> list[str]:
    text = clean_ws(text)
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) <= 1:
        sents = re.split(r"(?<=[.!?])\s+", text)
        parts, buf = [], ""
        for s in sents:
            if len(buf) + len(s) > 420 and buf:
                parts.append(buf.strip()); buf = s
            else:
                buf = (buf + " " + s).strip()
        if buf: parts.append(buf)
    out, tot = [], 0
    for p in parts:
        if len(out) >= n or tot >= maxlen: break
        out.append(p[:900]); tot += len(p)
    return out

# ---------- template parsing ----------
FIELD_MAP = {
    "status": "status",
    "age appearance / freeze": "ageFreeze",
    "height / body": "body",
    "hair / eyes / scent / marks": "hairEyes",
    "clothes default / access-modified": "clothes",
    "clothes default": "clothes",
    "collar / tag / leash": "collar",
    "origin": "origin",
    "personality public / private": "personality",
    "powers": "powers",
    "sexual role + holes used": "sexualRole",
    "sustenance": "sustenance",
    "fertility / pregnancy history": "fertility",
    "speech tics": "speech",
    "hard rules": "hardRules",
    "distinct from": "distinctFrom",
    "saga / world": "sagaWorld",
}

def parse_title_blocks(text: str, source: str) -> list[dict]:
    blocks = []
    parts = re.split(r"\nTITLE\s*[—\-]\s*", text)
    for part in parts[1:]:
        lines = part.splitlines()
        nameline = lines[0].strip()
        name = re.split(r"\s*\(|/", nameline)[0].strip()
        aliases = []
        m = re.search(r"\(([^)]+)\)", nameline)
        if m:
            aliases = [a.strip() for a in re.split(r"[/,—]", m.group(1)) if a.strip() and len(a.strip()) < 60]
        fields = {}
        for ln in lines[1:]:
            if re.match(r"TITLE\s*[—\-]", ln):
                break
            if ":" in ln[:70]:
                k, v = ln.split(":", 1)
                fields[k.strip().lower()] = v.strip()
        mapped = {}
        for k, v in fields.items():
            mapped[FIELD_MAP.get(k, k)] = v
        body = "\n".join(lines[1:120])
        blocks.append({"name": name, "aliases": aliases, "fields": mapped, "body": body, "source": source})
    return blocks

def load_all_templates() -> list[dict]:
    out = []
    for p in sorted(LIB.glob("*.md")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if "TITLE" not in t:
            continue
        out.extend(parse_title_blocks(t, p.name))
    # xuanye special
    xu = LIB / "xuanye_meat_toilet_template.md"
    if xu.exists():
        t = xu.read_text(encoding="utf-8", errors="replace")
        out.append({"name": "Xuanye", "aliases": [], "fields": {"status": "Wife = Meat Toilet", "origin": t[:2500]}, "body": t[:3500], "source": xu.name})
    return out

def template_to_char_fields(block: dict) -> dict:
    f = block["fields"]
    appearance = clean_ws("\n".join(filter(None, [
        f.get("body"), f.get("hairEyes"), f.get("clothes"), f.get("collar"), f.get("ageFreeze"),
    ])))
    bio_parts = [
        f.get("origin"),
        f.get("sexualRole"),
        f.get("fertility"),
        f.get("sustenance"),
        f.get("hardRules"),
        f.get("distinctFrom"),
    ]
    bio = clean_ws("\n\n".join(p for p in bio_parts if p))
    if not bio:
        bio = clean_ws(block["body"][:3000])
    evo = []
    for key, title in [
        ("origin", "Origin"),
        ("ageFreeze", "Age / freeze"),
        ("fertility", "Fertility / pregnancy"),
        ("sexualRole", "Sexual role consolidation"),
    ]:
        if f.get(key):
            evo.append({"title": title, "summary": f[key][:700]})
    details = {}
    for k in ("hardRules", "distinctFrom", "collar", "sustenance", "speech", "sagaWorld"):
        if f.get(k):
            details[k] = f[k][:1000]
    return {
        "aliases": block["aliases"],
        "role": f.get("status") or "",
        "uniqueTitle": f.get("status") or "",
        "relationshipToEon": f.get("status") or "",
        "status": f.get("status") or "",
        "biography": bio[:4000],
        "appearance": appearance[:2000],
        "personality": (f.get("personality") or "")[:1500],
        "powers": (f.get("powers") or "")[:1500],
        "evolution": evo,
        "details": details,
        "sourceExcerpts": [f"Library template: {block['source']} — TITLE {block['name']}"],
    }

# ---------- transcript helpers ----------
def split_turns(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"\n## (User|Grok)\n", text)
    turns = []
    i = 1
    while i + 1 < len(parts):
        turns.append((parts[i], parts[i + 1]))
        i += 2
    return turns

def context_around(text: str, name: str, window: int = 500, max_hits: int = 6) -> list[str]:
    hits = []
    for m in re.finditer(re.escape(name), text):
        start = max(0, m.start() - window)
        end = min(len(text), m.end() + window)
        snippet = clean_ws(text[start:end])
        if snippet and snippet not in hits:
            hits.append(snippet[:900])
        if len(hits) >= max_hits:
            break
    return hits

NAME_CANDIDATE = re.compile(
    r"\b([A-Z][a-z]{2,}(?:[\s\-'][A-Z][a-z]{2,}){0,3})\b"
)
STOP_NAMES = {
    "The", "And", "Then", "When", "This", "That", "With", "From", "After", "Before",
    "Continue", "Worked", "Make", "Very", "Long", "Eon", "Grok", "User", "Chapter",
    "Phase", "Monday", "Sunday", "Tokyo", "Seoul", "Japan", "Korea", "China",
    "Document", "Download", "Schema", "Files", "Index", "Roster", "Places", "Markers",
    "She", "He", "Her", "His", "They", "Their", "However", "Meanwhile", "Finally",
    "Suddenly", "Later", "Next", "First", "Second", "Third", "Still", "Also", "Even",
    "Worked For", "Saved", "Creating", "Updating", "Opening", "Continue",
}

def mine_female_names(text: str, known: set[str] | None = None) -> list[str]:
    """Heuristic: capitalize names that appear near gendered/MT context words."""
    known = known or set()
    ctx_pat = re.compile(
        r"(wife|mistress|daughter|maid|queen|empress|saintess|girlfriend|niece|"
        r"sister|mother|aunt|meat|toilet|pussy|cock|breast|ahegao|collar|inmon|"
        r"pregnant|womb|slut|harem|female|woman|girl|beauty|priestess)",
        re.I,
    )
    scores = defaultdict(int)
    # windowed scan
    for m in NAME_CANDIDATE.finditer(text):
        name = m.group(1)
        if name in STOP_NAMES or name.lower() in {x.lower() for x in STOP_NAMES}:
            continue
        if len(name) < 3:
            continue
        window = text[max(0, m.start() - 80): m.end() + 80]
        if ctx_pat.search(window) or name in known or name.lower() in {k.lower() for k in known}:
            scores[name] += 2 if ctx_pat.search(window) else 1
    # prefer multiword and frequent
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))
    out = []
    for name, sc in ranked:
        if sc < 2 and name not in known:
            continue
        out.append(name)
        if len(out) >= 40:
            break
    return out

PLACE_HINT = re.compile(
    r"\b((?:Kingdom|Empire|City|Town|Village|Academy|Cathedral|Temple|Palace|Manor|"
    r"Estate|Domain|Realm|World|Forest|Grove|Cave|Caves|Mountain|Island|Isles|"
    r"Tower|Citadel|Penthouse|Apartment|Office|Cafe|Café|School|University|"
    r"Dungeon|Coliseum|Bridge|River|Farm|Pens|Sanctum|Sanctuary|Ward|District|"
    r"Mansion|Onsen|Hotel)(?:\s+[A-Z][A-Za-z'\-]*){0,4}|"
    r"(?:[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,3})\s+"
    r"(?:Kingdom|Empire|City|Village|Academy|Cathedral|Palace|Manor|Estate|Domain|"
    r"Realm|Forest|Grove|Caves|Mountain|Tower|Citadel|Penthouse|Dungeon|Sanctum|"
    r"Mansion|Onsen|Ward|District|Farm))\b"
)

def mine_places(text: str) -> list[tuple[str, str]]:
    found = []
    seen = set()
    for m in PLACE_HINT.finditer(text):
        name = clean_ws(m.group(1))
        if len(name) < 4 or len(name) > 70:
            continue
        key = name.lower()
        if key in seen:
            continue
        if re.match(r"^(The|And|With|From|Into|This|That)\b", name):
            continue
        seen.add(key)
        # type guess
        low = name.lower()
        typ = "other"
        for pat, t in [
            (r"world|realm|plane", "world"),
            (r"empire", "empire"),
            (r"kingdom|duchy|archduch", "kingdom"),
            (r"city|capital|metropolis|village|town", "city"),
            (r"academy|school|university|cathedral|temple|palace|manor|estate|domain|"
             r"forest|grove|cave|mountain|island|tower|citadel|penthouse|apartment|"
             r"office|cafe|dungeon|coliseum|farm|pens|sanctum|mansion|onsen|hotel|ward|district|bridge", "venue"),
        ]:
            if re.search(pat, low):
                typ = t
                break
        found.append((name, typ))
        if len(found) >= 30:
            break
    return found

def wiki_prose_from_prompt(first_user: str, opening_grok: str) -> tuple[str, str]:
    """Return (howItStarted, shortSummarySeed) as clearer wiki prose without inventing."""
    fu = clean_ws(first_user)
    og = clean_ws(opening_grok)
    # how it started: frame the user's ask + what the opening establishes
    fu_paras = paras(fu, 4, 2200)
    og_paras = paras(og, 3, 1600)
    how_parts = []
    if fu_paras:
        how_parts.append(
            "Opening premise (from the saga’s first user direction):\n\n" + "\n\n".join(fu_paras)
        )
    if og_paras:
        how_parts.append(
            "Opening story beat (from the first Grok narration):\n\n" + "\n\n".join(og_paras)
        )
    how = "\n\n".join(how_parts)[:5000]

    # short summary: setting + powers hints + arc direction
    summary_bits = []
    if og_paras:
        summary_bits.append(og_paras[0])
    # compress user ask into 1 paragraph
    ask = re.sub(r"\s+", " ", fu)[:700]
    if ask:
        summary_bits.append("Core setup directed by the user: " + ask)
    short = "\n\n".join(summary_bits)[:2500]
    return how, short

def arc_title_from_user(user: str, headers: list[str]) -> str:
    u = clean_ws(user)
    u = re.sub(r"(?i)make it very long[^.]*\.?\s*", "", u)
    u = re.sub(r"(?i)what happens next\.?\s*", "", u)
    u = re.sub(r"(?i)continue[,.]?\s*", "", u)
    u = re.sub(r"\s+", " ", u).strip(" .,")
    if headers:
        h = headers[0].strip()
        if 3 < len(h) < 80 and not h.lower().startswith("worked"):
            return h
    # first clause
    clause = re.split(r"[.!?]", u)[0].strip()
    if len(clause) > 90:
        clause = clause[:87] + "…"
    if len(clause) < 8:
        clause = (u[:80] + "…") if len(u) > 80 else (u or "Continuation")
    # Title Case lightly
    return clause[0].upper() + clause[1:] if clause else "Continuation"

def build_progress(beats: list[dict], turn_count: int) -> list[dict]:
    """Collapse raw beats into named arcs with cleaner summaries."""
    if not beats:
        return []
    target = 8 if turn_count < 20 else (14 if turn_count < 50 else 22)
    # skip ultra-thin continue-only beats unless they have headers
    filtered = []
    for b in beats:
        user = b.get("userSnippet") or b.get("user") or ""
        headers = b.get("grokHeaders") or []
        src = b.get("summarySource") or b.get("summary") or ""
        low = user.lower().strip()
        if len(user) < 35 and re.match(r"^(continue|make it|next|go on)", low) and not headers:
            continue
        filtered.append(b)
    if not filtered:
        filtered = beats[:target]

    # sample evenly if too many
    if len(filtered) > target:
        step = len(filtered) / target
        idxs = sorted({int(i * step) for i in range(target)})
        filtered = [filtered[i] for i in idxs if i < len(filtered)]

    out = []
    for i, b in enumerate(filtered):
        user = b.get("userSnippet") or ""
        headers = b.get("grokHeaders") or []
        src = b.get("summarySource") or ""
        title = arc_title_from_user(user, headers)
        # summary: 2-5 sentences from grok start, plus brief direction
        grok_paras = paras(src, 3, 900)
        summary_parts = []
        if user and not re.match(r"(?i)^continue", user.strip()):
            direction = re.sub(r"\s+", " ", user).strip()
            direction = re.sub(r"(?i)make it very long[^.]*\.?\s*", "", direction)
            if len(direction) > 220:
                direction = direction[:217] + "…"
            if direction:
                summary_parts.append("User direction: " + direction)
        if grok_paras:
            summary_parts.append("\n\n".join(grok_paras))
        summary = clean_ws("\n\n".join(summary_parts))[:1200]
        if not summary:
            summary = "Continuation beat in the transcript."
        out.append({"title": title[:140], "summary": summary})
    return out[:30]

def enrich_char_from_contexts(name: str, contexts: list[str], existing: dict) -> dict:
    """Build/extend biography from surrounding transcript snippets — faithful collage."""
    bio = existing.get("biography") or ""
    if len(bio) >= 800:
        return existing
    # Use contexts as source excerpts and stitch a descriptive bio
    useful = []
    for snip in contexts:
        # drop pure dump/schema noise
        if re.search(r"(?i)(artifacts/|MT_|schema|I'll leave an MT mark|Can you save all)", snip):
            continue
        useful.append(snip)
    if not useful:
        return existing
    pieces = []
    if bio and len(bio) > 20:
        pieces.append(bio)
    pieces.append(
        f"Story mentions of {name} (verbatim neighborhood excerpts from the saga transcript):"
    )
    for snip in useful[:5]:
        pieces.append(snip[:700])
    new_bio = clean_ws("\n\n".join(pieces))[:3500]
    existing = dict(existing)
    existing["biography"] = new_bio
    excerpts = list(existing.get("sourceExcerpts") or [])
    for snip in useful[:3]:
        if snip[:300] not in excerpts:
            excerpts.append(snip[:400])
    existing["sourceExcerpts"] = excerpts[:8]
    # appearance heuristics from contexts
    if not existing.get("appearance"):
        app_bits = []
        for snip in useful:
            for pat in [
                r"(\d+\s*cm[^.\\n]{0,80})",
                r"((?:long|short|silver|black|blonde|white|pink|violet|red|blue|green|golden)[^.]{0,40}hair[^.\\n]{0,60})",
                r"((?:eyes)[^.]{0,50})",
                r"((?:breasts|tits|bust|hips|thighs|body)[^.]{0,80})",
            ]:
                m = re.search(pat, snip, re.I)
                if m:
                    app_bits.append(m.group(1).strip())
            if len(app_bits) >= 4:
                break
        if app_bits:
            existing["appearance"] = clean_ws("; ".join(dict.fromkeys(app_bits)))[:1500]
    return existing

def main():
    data = json.loads((WIKI / "data.js").read_text().split("=", 1)[1].strip().rstrip(";"))
    sagas = data["sagas"]
    characters = {c["id"]: c for c in data["characters"]}
    places = {p["id"]: p for p in data["places"]}
    char_by_name = {}
    for c in characters.values():
        char_by_name[c["name"].lower()] = c["id"]
        for a in c.get("aliases") or []:
            char_by_name[a.lower()] = c["id"]

    templates = load_all_templates()
    print(f"templates loaded: {len(templates)}")

    # Apply templates
    for block in templates:
        name = block["name"]
        fields = template_to_char_fields(block)
        cid = char_by_name.get(name.lower())
        if not cid:
            # try first token unique
            tok = name.split()[0].lower()
            matches = [c for c in characters.values() if c["name"].split()[0].lower() == tok]
            if len(matches) == 1:
                cid = matches[0]["id"]
            else:
                cid = "char-" + slugify(name)
                if cid not in characters:
                    characters[cid] = {
                        "id": cid, "name": name, "aliases": [], "sagaIds": [], "primarySagaId": "",
                        "role": "", "uniqueTitle": "", "relationshipToEon": "", "biography": "",
                        "appearance": "", "personality": "", "powers": "", "status": "", "ranks": "",
                        "evolution": [], "placesRelated": [], "details": {}, "sourceExcerpts": [],
                    }
                    char_by_name[name.lower()] = cid
        ch = characters[cid]
        for a in fields["aliases"]:
            if a not in ch["aliases"] and a != ch["name"]:
                ch["aliases"].append(a)
            char_by_name[a.lower()] = cid
        for k, v in fields.items():
            if k == "aliases":
                continue
            if k == "evolution" and v and (not ch.get("evolution") or len(v) > len(ch.get("evolution") or [])):
                ch["evolution"] = v
            elif k == "details" and v:
                ch.setdefault("details", {}).update(v)
            elif k == "sourceExcerpts" and v:
                for e in v:
                    if e not in (ch.get("sourceExcerpts") or []):
                        ch.setdefault("sourceExcerpts", []).append(e)
            elif isinstance(v, str) and v and len(v) > len(ch.get(k) or ""):
                ch[k] = v
        print(f"  template -> {ch['name']} bio={len(ch.get('biography') or '')}")

    # Per-saga enrichment
    before_bios = [len(c.get("biography") or "") for c in characters.values()]
    saga_stats = []

    for s in sagas:
        hex8 = s["hex"]
        full_path = FULL / f"{hex8}.md"
        ex_path = EX / f"{hex8}.json"
        if not full_path.exists():
            print("MISSING", hex8)
            continue
        raw = full_path.read_text(encoding="utf-8", errors="replace")
        turns = split_turns(raw)
        ex = json.loads(ex_path.read_text()) if ex_path.exists() else {}

        first_user = ex.get("firstUser") or next((c for r, c in turns if r == "User"), "")
        opening_grok = ex.get("openingGrok") or next((c for r, c in turns if r == "Grok"), "")[:3500]
        how, short = wiki_prose_from_prompt(first_user, opening_grok)

        # powers from existing + hints
        powers = list(s.get("powers") or [])
        for hint in ex.get("powersHints") or []:
            if hint not in powers:
                powers.append(hint)
        # mine more power phrases from first user
        for pat, label in [
            (r"adaptive authority", "Adaptive Authority"),
            (r"mythical body", "Mythical Body"),
            (r"exponential", "Exponential growth/power"),
            (r"inmon|淫紋", "Inmon branding"),
            (r"reality (?:warp|manip)", "Reality manipulation"),
            (r"infinite wealth|sudden wealth", "Infinite wealth"),
            (r"regression|time[- ]travel|second chance", "Time regression / second chance"),
            (r"mana awaken", "Mana awakening"),
            (r"cultivat", "Cultivation"),
            (r"world.?tree|aetherion|aetherdrake", "World-tree / bloodline inheritance"),
        ]:
            if re.search(pat, first_user + "\n" + opening_grok, re.I) and label not in powers:
                powers.append(label)

        beats_raw = ex.get("beats") or []
        # normalize beat keys
        norm_beats = []
        for b in beats_raw:
            norm_beats.append({
                "userSnippet": b.get("userSnippet") or b.get("user") or "",
                "summarySource": b.get("summarySource") or b.get("summary") or "",
                "grokHeaders": b.get("grokHeaders") or b.get("headers") or [],
            })
        progress = build_progress(norm_beats, len(turns))

        # important details
        details = list(s.get("importantDetails") or [])
        for p in powers:
            line = f"Power/system: {p}"
            if line not in details:
                details.append(line)
        for raw_name in (ex.get("dumpNames") or [])[:12]:
            if 20 < len(raw_name) < 220 and raw_name not in details:
                details.append(raw_name)
        # counts
        details.append(f"Transcript size: ~{len(raw)//1024} KB, ~{len(turns)} turns ({sum(1 for r,_ in turns if r=='User')} user / {sum(1 for r,_ in turns if r=='Grok')} grok).")
        # dedupe
        seen_d, details2 = set(), []
        for d in details:
            k = d.lower()[:100]
            if k not in seen_d:
                seen_d.add(k); details2.append(d)
        details = details2[:30]

        # Mine names + enrich characters
        known_names = set()
        for cid in s.get("meatToiletIds") or []:
            if cid in characters:
                known_names.add(characters[cid]["name"])
        mined = mine_female_names(raw, known_names)
        mt_ids = list(s.get("meatToiletIds") or [])

        for name in mined:
            # skip obvious non-persons
            if name.lower() in {"continue", "chapter", "phase", "document"}:
                continue
            cid = char_by_name.get(name.lower())
            if not cid:
                cid = "char-" + slugify(name)
                # avoid creating junk: require either known or enough hits
                contexts = context_around(raw, name, 450, 5)
                if len(contexts) < 2 and name not in known_names:
                    continue
                if cid not in characters:
                    characters[cid] = {
                        "id": cid, "name": name, "aliases": [], "sagaIds": [], "primarySagaId": s["id"],
                        "role": "", "uniqueTitle": "", "relationshipToEon": "", "biography": "",
                        "appearance": "", "personality": "", "powers": "", "status": "", "ranks": "",
                        "evolution": [], "placesRelated": [], "details": {}, "sourceExcerpts": [],
                    }
                    char_by_name[name.lower()] = cid
            ch = characters[cid]
            if s["id"] not in ch["sagaIds"]:
                ch["sagaIds"].append(s["id"])
            if not ch.get("primarySagaId"):
                ch["primarySagaId"] = s["id"]
            contexts = context_around(raw, name, 500, 6)
            characters[cid] = enrich_char_from_contexts(name, contexts, ch)
            if cid not in mt_ids:
                mt_ids.append(cid)

        # Also enrich already linked MTs even if not remine
        for cid in list(mt_ids):
            if cid not in characters:
                continue
            ch = characters[cid]
            if len(ch.get("biography") or "") < 400:
                contexts = context_around(raw, ch["name"], 550, 8)
                characters[cid] = enrich_char_from_contexts(ch["name"], contexts, ch)

        # Places
        place_ids = list(s.get("placeIds") or [])
        for pname, ptype in mine_places(raw):
            pid = "place-" + slugify(pname)
            if pid not in places:
                places[pid] = {
                    "id": pid, "name": pname, "type": ptype, "sagaIds": [],
                    "summary": f"{ptype.title()} named in saga transcript.",
                    "details": "", "relatedCharacterIds": [], "notableFacts": [],
                }
            pl = places[pid]
            if s["id"] not in pl["sagaIds"]:
                pl["sagaIds"].append(s["id"])
            # enrich summary with a context hit
            if len(pl.get("summary") or "") < 120 or pl["summary"].startswith(ptype.title()):
                ctx = context_around(raw, pname, 300, 2)
                if ctx:
                    pl["summary"] = ctx[0][:700]
                    pl["details"] = ctx[0][:2000]
            if pid not in place_ids:
                place_ids.append(pid)

        # Mid/late for stronger shortSummary
        mid = ex.get("midGrok") or ""
        late = ex.get("lateGrok") or ""
        short_bits = [short]
        if powers:
            short_bits.append("Powers / systems called out in-source: " + "; ".join(powers) + ".")
        mt_names = [characters[i]["name"] for i in mt_ids if i in characters][:12]
        if mt_names:
            short_bits.append("Named meat toilets / core females linked so far: " + ", ".join(mt_names) + ".")
        place_names = [places[i]["name"] for i in place_ids if i in places][:10]
        if place_names:
            short_bits.append("Places named in-source: " + ", ".join(place_names) + ".")
        if late:
            lp = paras(late, 1, 350)
            if lp:
                short_bits.append("Later-state snapshot: " + lp[0])
        short_summary = clean_ws("\n\n".join(short_bits))[:3200]

        # Note for still-empty MT sagas
        if not mt_ids:
            details.insert(0, "NOTE: No clearly named meat-toilet characters could be locked from dumps/templates; transcript may be mark-oriented or name-sparse. Full saga remains available.")

        s["howItStarted"] = how
        s["premise"] = how  # keep in sync for app variants
        s["shortSummary"] = short_summary
        s["progress"] = progress
        s["powers"] = powers
        s["importantDetails"] = details
        s["meatToiletIds"] = mt_ids
        s["placeIds"] = place_ids
        s["counts"] = {
            "meatToilets": len(mt_ids),
            "places": len(place_ids),
            "messageCount": len(turns),
            "userTurns": sum(1 for r, _ in turns if r == "User"),
        }
        saga_stats.append((s["num"], len(progress), len(mt_ids), len(place_ids), len(short_summary), len(how)))
        print(f"saga {s['num']:02d}: progress={len(progress)} MT={len(mt_ids)} places={len(place_ids)} short={len(short_summary)}")

    # Finalize lists
    char_list = sorted(characters.values(), key=lambda c: c["name"].lower())
    place_list = sorted(places.values(), key=lambda p: p["name"].lower())
    after_bios = [len(c.get("biography") or "") for c in char_list]

    meta = {
        "title": "Eon Saga Fandom Wiki",
        "sagaCount": len(sagas),
        "characterCount": len(char_list),
        "placeCount": len(place_list),
        "source": "full_chats + chats dumps + library + SAGA index",
        "adult": True,
        "notes": "Enriched pass: template merge + transcript mining + wiki-prose rewrite. NSFW kept faithful.",
    }
    bundle = {"meta": meta, "sagas": sagas, "characters": char_list, "places": place_list}
    (DATA_DIR / "sagas.json").write_text(json.dumps(sagas, ensure_ascii=False, indent=2))
    (DATA_DIR / "characters.json").write_text(json.dumps(char_list, ensure_ascii=False, indent=2))
    (DATA_DIR / "places.json").write_text(json.dumps(place_list, ensure_ascii=False, indent=2))
    (DATA_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    (WIKI / "data.js").write_text("window.WIKI_DATA = " + json.dumps(bundle, ensure_ascii=False) + ";\n")

    def stats(arr):
        arr = sorted(arr)
        return {
            "min": arr[0] if arr else 0,
            "median": arr[len(arr)//2] if arr else 0,
            "mean": (sum(arr)//len(arr)) if arr else 0,
            "max": arr[-1] if arr else 0,
            "lt50": sum(1 for x in arr if x < 50),
            "lt200": sum(1 for x in arr if x < 200),
            "ge400": sum(1 for x in arr if x >= 400),
            "ge800": sum(1 for x in arr if x >= 800),
        }

    before_s = stats(before_bios)
    after_s = stats(after_bios)
    zero_mt = [s for s in sagas if s["counts"]["meatToilets"] == 0]
    zero_pl = [s for s in sagas if s["counts"]["places"] == 0]

    progress_md = f"""# Wiki enrichment progress

## Bio length stats (characters)
| | before | after |
|--|--|--|
| min | {before_s['min']} | {after_s['min']} |
| median | {before_s['median']} | {after_s['median']} |
| mean | {before_s['mean']} | {after_s['mean']} |
| max | {before_s['max']} | {after_s['max']} |
| <50 | {before_s['lt50']} | {after_s['lt50']} |
| <200 | {before_s['lt200']} | {after_s['lt200']} |
| ≥400 | {before_s['ge400']} | {after_s['ge400']} |
| ≥800 | {before_s['ge800']} | {after_s['ge800']} |

## Counts
- Sagas: {len(sagas)}
- Characters: {len(char_list)}
- Places: {len(place_list)}
- Sagas with 0 MT: {len(zero_mt)} → {[s['num'] for s in zero_mt]}
- Sagas with 0 places: {len(zero_pl)}

## Method
- Merged library TITLE templates into character appearance/bio/powers/evolution
- Re-mined full transcripts for named females (gendered/MT context) and places
- Rewrote howItStarted / shortSummary as wiki prose grounded in first User + opening Grok
- Rebuilt progress as named arcs (headers preferred) with cleaned direction + narration summaries
- importantDetails refreshed with powers, dump lines, turn counts

## Remaining thin stubs
Characters still under 200 chars bio (often name-only mentions):
"""
    thin = [c for c in char_list if len(c.get("biography") or "") < 200]
    for c in thin[:60]:
        progress_md += f"- {c['name']} ({len(c.get('biography') or '')}) sagas={len(c.get('sagaIds') or [])}\n"
    if len(thin) > 60:
        progress_md += f"- … and {len(thin)-60} more\n"
    (WIKI / "PROGRESS.md").write_text(progress_md)
    print("BEFORE", before_s)
    print("AFTER", after_s)
    print("zero MT", [s["num"] for s in zero_mt])
    print("zero places", len(zero_pl))

if __name__ == "__main__":
    main()
