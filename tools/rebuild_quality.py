#!/usr/bin/env python3
"""Rebuild curated roster + quality wiki prose from sources (no invented plot)."""
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
WEB = ROOT / "web" / "data.js"
TOC = ROOT / "SAGA_MT_INDEX_TOC.md"
INDEX = ROOT / "SAGA_MT_INDEX.md"
MATCHED = ROOT / "MATCHED_CHATS.md"
DATA_DIR = WIKI / "data"

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:72] or "x"

def clean_ws(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def paras(text: str, n: int = 4, maxlen: int = 2200) -> list[str]:
    text = clean_ws(text)
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) <= 1:
        sents = re.split(r"(?<=[.!?])\s+", text)
        parts, buf = [], ""
        for s in sents:
            if len(buf) + len(s) > 400 and buf:
                parts.append(buf); buf = s
            else:
                buf = (buf + " " + s).strip()
        if buf: parts.append(buf)
    out, tot = [], 0
    for p in parts:
        if len(out) >= n or tot >= maxlen: break
        out.append(p[:950]); tot += len(p)
    return out

def load_old_web():
    text = WEB.read_text(encoding="utf-8", errors="replace")
    return json.loads(re.search(r"window\.MT_DATA\s*=\s*(\{.*\})", text, re.S).group(1))

def load_current_sagas_meta():
    """Keep saga ids/urls/hex/markers from current wiki sagas if present, else rebuild from MATCHED."""
    cur_path = DATA_DIR / "sagas.json"
    if cur_path.exists():
        try:
            cur = json.loads(cur_path.read_text())
            # if bloated/corrupt still usable for meta
            if len(cur) == 45:
                return cur
        except Exception:
            pass
    # parse MATCHED
    text = MATCHED.read_text(encoding="utf-8", errors="replace")
    sagas = []
    section = None
    for line in text.splitlines():
        if "Marker A only" in line: section = "A"
        elif "Both A+B" in line: section = "A+B"
        elif "Marker B only" in line: section = "B"
        m = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(https://grok\.com/c/([0-9a-f-]{36}))\s*\|\s*([^|]+)\|", line)
        if not m: continue
        num, title, url, uuid, markers = m.groups()
        hex8 = uuid.split("-")[0]
        sagas.append({
            "id": f"saga-{int(num):02d}-{slugify(title)}",
            "num": int(num), "title": title.strip(), "url": url, "hex": hex8,
            "markers": markers.strip() or section or "",
            "chatFile": f"{hex8}.md",
            "fullTranscriptPath": f"transcripts/{hex8}.md",
        })
    return sagas

# ---------- templates ----------
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

def parse_templates() -> dict[str, dict]:
    out = {}
    for p in sorted(LIB.glob("*.md")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if "TITLE" not in t: continue
        for part in re.split(r"\nTITLE\s*[—\-]\s*", t)[1:]:
            lines = part.splitlines()
            nameline = lines[0].strip()
            name = re.split(r"\s*\(|/", nameline)[0].strip()
            aliases = []
            m = re.search(r"\(([^)]+)\)", nameline)
            if m:
                aliases = [a.strip() for a in re.split(r"[/,—]", m.group(1)) if a.strip() and len(a) < 55]
            fields = {}
            for ln in lines[1:]:
                if re.match(r"TITLE\s*[—\-]", ln): break
                if ":" in ln[:70]:
                    k,v = ln.split(":",1); fields[k.strip().lower()] = v.strip()
            mapped = {FIELD_MAP.get(k,k): v for k,v in fields.items()}
            appearance = clean_ws("\n".join(filter(None,[mapped.get("body"), mapped.get("hairEyes"), mapped.get("clothes"), mapped.get("collar"), mapped.get("ageFreeze")])))
            bio = clean_ws("\n\n".join(filter(None,[mapped.get("origin"), mapped.get("sexualRole"), mapped.get("fertility"), mapped.get("sustenance"), mapped.get("hardRules"), mapped.get("distinctFrom")])))
            if not bio:
                bio = clean_ws("\n".join(lines[1:80]))[:3200]
            evo = []
            for key, title in [("origin","Origin"),("ageFreeze","Age / freeze"),("fertility","Fertility / pregnancy"),("sexualRole","Role consolidation")]:
                if mapped.get(key):
                    evo.append({"title": title, "summary": mapped[key][:700]})
            details = {k: mapped[k][:1000] for k in ("hardRules","distinctFrom","collar","sustenance","speech","sagaWorld") if mapped.get(k)}
            key = name.lower()
            # keep richest
            rec = {
                "name": name, "aliases": aliases, "role": mapped.get("status") or "",
                "uniqueTitle": mapped.get("status") or "", "relationshipToEon": mapped.get("status") or "",
                "status": mapped.get("status") or "", "biography": bio[:4000], "appearance": appearance[:2000],
                "personality": (mapped.get("personality") or "")[:1500], "powers": (mapped.get("powers") or "")[:1500],
                "evolution": evo, "details": details, "sourceExcerpts": [f"Template {p.name}"], "templateSource": p.name,
            }
            if key not in out or len(rec["biography"]) > len(out[key].get("biography") or ""):
                out[key] = rec
    xu = LIB / "xuanye_meat_toilet_template.md"
    if xu.exists():
        t = xu.read_text(encoding="utf-8", errors="replace")
        out["xuanye"] = {
            "name": "Xuanye", "aliases": [], "role": "Wife = Meat Toilet", "uniqueTitle": "Wife = Meat Toilet",
            "relationshipToEon": "Wife = Meat Toilet", "status": "Wife = Meat Toilet",
            "biography": t[:3500], "appearance": "Hancock-like face, long black hair, red sash (index card).",
            "personality": "", "powers": "", "evolution": [], "details": {"source": xu.name},
            "sourceExcerpts": [f"Template {xu.name}"], "templateSource": xu.name,
        }
    return out

def parse_toc_chars() -> dict[int, list[tuple[str,str]]]:
    """saga num -> list of (name, role)"""
    text = TOC.read_text(encoding="utf-8", errors="replace")
    out = defaultdict(list)
    cur = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d+)\.\s+", line)
        if m:
            cur = int(m.group(1)); continue
        if cur is None: continue
        if line.startswith("- Characters:"):
            payload = line.split(":",1)[1].strip()
            # split on ; or ,
            chunks = re.split(r";\s*", payload)
            for ch in chunks:
                ch = ch.strip()
                if not ch or ch.lower().startswith("(none"): continue
                # Name (role) or Name — role
                mm = re.match(r"^([^(/—]+?)(?:\s*\(([^)]+)\))?(?:\s*[—\-]\s*(.+))?$", ch)
                if not mm: continue
                name = mm.group(1).strip().strip(",")
                role = (mm.group(2) or mm.group(3) or "").strip()
                # filter noise
                if len(name) < 2 or len(name) > 60: continue
                if name.lower() in {"story","first","best","the","all","mt","title","group","search result"}: continue
                if re.match(r"^(mt_|place_|create or|fill every|every female|record named|cross-link|do not|adult erotic)", name, re.I): continue
                # further split "A; B" already done; also "A / B" aliases keep first
                name = name.split("/")[0].strip()
                if re.search(r"\b(schema|gazetteer|index|roster|files|places)\b", name, re.I): continue
                out[cur].append((name, role))
    return out

def parse_chat_dump_chars(hex8: str) -> list[tuple[str,str]]:
    p = CHATS / f"{hex8}.md"
    if not p.exists(): return []
    text = p.read_text(encoding="utf-8", errors="replace")
    found = []
    for m in re.finditer(r"^([A-Z][^—\n]{1,55})\s*—\s*(.+)$", text, re.M):
        name = m.group(1).split("/")[0].strip()
        name = re.sub(r"\s*\(.*\)$", "", name).strip()
        role = m.group(2).strip()[:300]
        if len(name) < 2 or len(name) > 55: continue
        if re.search(r"\b(schema|files|index|roster|places|characters|result|when they|years of|mealtimes|mansion|chaos|orgy)\b", name, re.I):
            continue
        if not re.match(r"^[A-ZÀ-ÖØ-Þ]", name): continue
        if len(role) < 8: continue
        # reject sentence names
        if re.search(r"\b(is|are|was|were|will|would|can|could|have|has|had)\b", name, re.I): continue
        if name.count(" ") > 4: continue
        found.append((name, role))
    return found

def is_clean_person_name(name: str) -> bool:
    name = name.strip()
    if not (2 <= len(name) <= 55): return False
    if re.search(r"[.!?:,;/]", name): return False
    if re.search(r"\d", name) and not re.search(r"\b(II|III|IV)\b", name): return False
    bad = re.compile(
        r"^(and|the|a|an|with|from|after|before|when|while|continue|chapter|phase|document|"
        r"worked|creating|updating|opening|saved|however|meanwhile|finally|suddenly|later|next|"
        r"first|second|third|still|also|even|make|very|long|user|grok|eon|academy|adult|affinity|"
        r"afternoon|afterward|again|ahegao|ahh|ahhn|aaahhn|absolute|adaptive|alliance|always|"
        r"all|all-purpose|aetherial|aetherion|aetherdrake|aetherford|aetheria|achernar|"
        r"yamanote|tokyo|seoul|japan|korea|china)\b",
        re.I,
    )
    if bad.match(name): return False
    if re.search(r"\b(ejaculation|multiplier|control|sensitivity|augury|halls|meat toilet dump)\b", name, re.I):
        return False
    words = name.replace("-", " ").split()
    if not (1 <= len(words) <= 4): return False
    small = {"of","de","von","van","da","del","la","le","née"}
    for w in words:
        if w.lower() in small: continue
        if not w[0].isupper() and not ("\u4e00" <= w[0] <= "\u9fff") and not ("가" <= w[0] <= "힣"):
            return False
    return True

def split_turns(text: str):
    parts = re.split(r"\n## (User|Grok)\n", text)
    turns = []; i=1
    while i+1 < len(parts):
        turns.append((parts[i], parts[i+1])); i += 2
    return turns

def descriptive_snippets(text: str, name: str, limit: int = 8) -> list[str]:
    """Pull paragraph-ish windows around name that look descriptive."""
    snips = []
    for m in re.finditer(re.escape(name), text):
        # expand to paragraph boundaries
        start = text.rfind("\n\n", 0, m.start())
        start = 0 if start < 0 else start + 2
        end = text.find("\n\n", m.end())
        end = len(text) if end < 0 else end
        # clamp
        start = max(start, m.start() - 700)
        end = min(end, m.end() + 900)
        snip = clean_ws(text[start:end])
        if len(snip) < 80: continue
        # skip UI chrome / file lists
        if re.search(r"(?i)(skip to main content|toggle sidebar|artifacts/|document ·|download\n|mt mark for now)", snip):
            continue
        if re.search(r"(?i)(I'll leave an MT mark|Can you save all of the female)", snip):
            continue
        # prefer descriptive vocabulary
        score = 0
        if re.search(r"(?i)(hair|eyes|cm|tall|breast|body|voice|wife|daughter|maid|queen|collar|inmon|love|claim|pregnant|power|beauty|skin|lips)", snip):
            score += 2
        if name.lower() in snip.lower(): score += 1
        if score >= 2:
            snips.append(snip[:1100])
        if len(snips) >= limit: break
    # dedupe similar
    out = []
    for s in snips:
        if any(s[:120] == o[:120] for o in out): continue
        out.append(s)
    return out

EVO_PAT = re.compile(
    r"(?i)(.{0,120}(?:transform|evolved|evolution|grew into|became his|claimed|branded|inmon|"
    r"pregnant|pregnancy|awakened|ascended|turned into|no longer|after (?:the|her|that)|"
    r"from virgin|first night|wedding|marriage|collar(?:ed)?|rebirth|remade).{0,220})"
)

def evolution_from_text(text: str, name: str) -> list[dict]:
    evo = []
    # search windows near name
    for m in re.finditer(re.escape(name), text):
        window = text[max(0, m.start()-250): m.end()+350]
        for em in EVO_PAT.finditer(window):
            summary = clean_ws(em.group(1))
            if len(summary) < 40: continue
            title = "Growth / change"
            low = summary.lower()
            if "pregnan" in low: title = "Pregnancy"
            elif "inmon" in low or "brand" in low or "collar" in low: title = "Branding / ownership mark"
            elif "wedding" in low or "marri" in low: title = "Marriage / bonding"
            elif "transform" in low or "remade" in low or "rebirth" in low: title = "Transformation"
            elif "awaken" in low or "ascend" in low: title = "Awakening / ascent"
            elif "claim" in low: title = "Claiming"
            key = summary[:80].lower()
            if any(key == e["summary"][:80].lower() for e in evo): continue
            evo.append({"title": title, "summary": summary[:700]})
            if len(evo) >= 8: return evo
    return evo

def appearance_from_snips(snips: list[str]) -> str:
    bits = []
    pats = [
        r"(\d{2,3}\s*cm[^.\\n]{0,100})",
        r"((?:long|short|waist[- ]length|silver|black|blonde|blond|white|pink|violet|purple|red|blue|green|golden|crimson|azure|platinum|raven)[^.]{0,50}hair[^.\\n]{0,80})",
        r"((?:eyes|gaze)[^.]{0,70})",
        r"((?:breasts|bust|hips|thighs|waist|ass|figure|body)[^.]{0,90})",
        r"((?:wearing|dressed|collar|kimono|dress|uniform)[^.]{0,100})",
    ]
    for snip in snips:
        for pat in pats:
            for m in re.finditer(pat, snip, re.I):
                bit = clean_ws(m.group(1))
                if 8 < len(bit) < 160 and bit.lower() not in {b.lower() for b in bits}:
                    bits.append(bit)
                if len(bits) >= 10: break
            if len(bits) >= 10: break
    return "; ".join(bits)[:1600]

def to_wiki_how(first_user: str, opening_grok: str) -> str:
    """Clear wiki-style how-it-started grounded in source."""
    fu = clean_ws(first_user)
    og = clean_ws(opening_grok)
    # Third-personize common prompt openers without inventing facts
    fu2 = fu
    fu2 = re.sub(r"(?i)^start a story of eon[,.]?\s*", "This saga begins with Eon: ", fu2)
    fu2 = re.sub(r"(?i)^start a story of eon\b", "This saga begins with Eon", fu2)
    fu2 = re.sub(r"(?i)^make it very long[^.]*\.?\s*", "", fu2)
    fu_paras = paras(fu2, 4, 2400)
    og_paras = paras(og, 3, 1700)
    parts = []
    if fu_paras:
        parts.append("### Premise (from opening user direction)\n\n" + "\n\n".join(fu_paras))
    if og_paras:
        parts.append("### First narrated beat\n\n" + "\n\n".join(og_paras))
    return "\n\n".join(parts)[:5200]

def to_wiki_short(first_user: str, opening_grok: str, powers: list[str], cast: list[str], places: list[str], mid: str, late: str) -> str:
    bits = []
    # Setting from opening narration
    op = paras(opening_grok, 2, 900)
    if op:
        bits.append(op[0])
    # Setup condensed
    setup = re.sub(r"(?i)^start a story of eon[,.]?\s*", "Eon ", clean_ws(first_user))
    setup = re.sub(r"\s+", " ", setup)
    setup = re.sub(r"(?i)make it very long[^.]*\.?\s*", "", setup)
    if len(setup) > 650: setup = setup[:647] + "…"
    if setup:
        bits.append("Setup: " + setup)
    if powers:
        bits.append("Powers / systems: " + "; ".join(powers) + ".")
    if cast:
        bits.append("Core named cast: " + ", ".join(cast[:14]) + ".")
    if places:
        bits.append("Places: " + ", ".join(places[:12]) + ".")
    late_p = paras(late or mid or "", 1, 380)
    if late_p:
        bits.append("Later snapshot: " + late_p[0])
    return "\n\n".join(bits)[:3000]

def build_progress_from_extract(ex: dict, turn_count: int) -> list[dict]:
    beats = ex.get("beats") or []
    headers = ex.get("storyHeaders") or ex.get("story_headers") or []
    target = 8 if turn_count < 20 else (12 if turn_count < 40 else (18 if turn_count < 80 else 24))
    out = []
    # Prefer story headers as arc spines when enough exist
    if len(headers) >= 6:
        # map headers to nearby beat summaries if possible
        for i, h in enumerate(headers[:target]):
            # find beat whose grok headers contain h or summary mentions
            summary = ""
            for b in beats:
                gh = b.get("grokHeaders") or b.get("headers") or []
                if h in gh:
                    summary = b.get("summarySource") or b.get("summary") or ""
                    break
            if not summary and i < len(beats):
                summary = beats[min(i, len(beats)-1)].get("summarySource") or beats[min(i, len(beats)-1)].get("summary") or ""
            sp = paras(summary, 3, 900)
            out.append({"title": h[:140], "summary": "\n\n".join(sp) if sp else f"Story section “{h}” as marked in the transcript."})
        return out

    # Otherwise sample user beats with cleaned titles
    filtered = []
    for b in beats:
        user = b.get("userSnippet") or b.get("user") or ""
        gh = b.get("grokHeaders") or []
        src = b.get("summarySource") or b.get("summary") or ""
        low = user.lower().strip()
        if len(user) < 40 and re.match(r"^(continue|make it|next|go on)", low) and not gh:
            continue
        filtered.append(b)
    if not filtered:
        filtered = beats
    if len(filtered) > target:
        step = len(filtered) / target
        filtered = [filtered[int(i*step)] for i in range(target) if int(i*step) < len(filtered)]

    for b in filtered:
        user = b.get("userSnippet") or ""
        gh = b.get("grokHeaders") or []
        src = b.get("summarySource") or b.get("summary") or ""
        title = gh[0] if gh and len(gh[0]) < 80 else None
        if not title:
            u = re.sub(r"(?i)make it very long[^.]*\.?\s*", "", user)
            u = re.sub(r"(?i)^(continue|what happens next)[,.]?\s*", "", u)
            u = re.sub(r"\s+", " ", u).strip(" .,")
            clause = re.split(r"[.!?]", u)[0].strip()
            if len(clause) > 88: clause = clause[:85] + "…"
            title = (clause[:1].upper() + clause[1:]) if clause else "Continuation"
        sp = paras(src, 3, 850)
        direction = re.sub(r"(?i)make it very long[^.]*\.?\s*", "", re.sub(r"\s+", " ", user)).strip()
        direction = re.sub(r"(?i)^(continue|what happens next)[,.]?\s*", "", direction)
        if len(direction) > 200: direction = direction[:197] + "…"
        summary_parts = []
        if direction and not re.match(r"(?i)^continue", direction):
            summary_parts.append("Direction: " + direction)
        if sp:
            summary_parts.append("\n\n".join(sp))
        out.append({"title": title[:140], "summary": clean_ws("\n\n".join(summary_parts))[:1200] or "Continuation beat."})
    return out[:30]

PLACE_RE = re.compile(
    r"\b((?:Kingdom|Empire|City|Town|Village|Academy|Cathedral|Temple|Palace|Manor|Estate|"
    r"Domain|Realm|World|Forest|Grove|Cave|Caves|Mountain|Island|Isles|Tower|Citadel|"
    r"Penthouse|Apartment|Office|Cafe|Café|School|University|Dungeon|Coliseum|Farm|Pens|"
    r"Sanctum|Sanctuary|Ward|District|Mansion|Onsen|Hotel|Bridge)(?:\s+[A-Z][A-Za-z'\-]*){0,4}|"
    r"(?:[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2})\s+"
    r"(?:Kingdom|Empire|City|Village|Academy|Cathedral|Palace|Manor|Estate|Domain|Realm|"
    r"Forest|Grove|Caves|Mountain|Tower|Citadel|Penthouse|Dungeon|Sanctum|Mansion|Onsen|"
    r"Ward|District|Farm|University|School))\b"
)

def mine_places_strict(text: str) -> list[tuple[str,str]]:
    seen=set(); out=[]
    for m in PLACE_RE.finditer(text):
        name=clean_ws(m.group(1))
        if not (4 <= len(name) <= 70): continue
        if name.lower() in seen: continue
        if re.match(r"^(The|And|With|From|This|That)\b", name): continue
        # reject if too verbish
        if re.search(r"\b(is|are|was|were|have|has|will)\b", name, re.I): continue
        seen.add(name.lower())
        low=name.lower(); typ="other"
        for pat,t in [(r"world|realm","world"),(r"empire","empire"),(r"kingdom|duchy","kingdom"),
                      (r"city|village|town|capital","city"),
                      (r"academy|school|university|cathedral|temple|palace|manor|estate|domain|forest|grove|cave|mountain|island|tower|citadel|penthouse|apartment|office|cafe|dungeon|farm|pens|sanctum|mansion|onsen|hotel|ward|district|bridge","venue")]:
            if re.search(pat, low): typ=t; break
        out.append((name, typ))
        if len(out)>=25: break
    return out

def load_place_library() -> list[dict]:
    places=[]
    for p in sorted(LIB.glob("PLACE_*.md")):
        t=p.read_text(encoding="utf-8", errors="replace")
        m=re.search(r"^#\s+(.+)$", t, re.M)
        name=m.group(1).strip() if m else p.stem.replace("PLACE_"," ").replace("_"," ").strip()
        body_paras=[x.strip() for x in re.split(r"\n\s*\n", t) if x.strip() and not x.strip().startswith("#")]
        summary=body_paras[0][:800] if body_paras else name
        places.append({"name": name, "type": "venue", "summary": summary, "details": t[:3000], "source": p.name})
    # gazetteer headings
    for p in sorted(LIB.glob("MT_*Places*.md")) + sorted(LIB.glob("MT_*Gazetteer*.md")):
        t=p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^###?\s+(.+)$", t, re.M):
            name=m.group(1).strip()
            if re.match(r"^(places|dump|related|rule|search|worlds|polities|cities|landmarks|type|features|note|schema|overview|gazeteer|gazetteer)", name, re.I):
                continue
            if not (3 <= len(name) <= 70): continue
            if name.count(" ") >= 8: continue
            block=t[m.end():m.end()+600]
            block=re.split(r"\n#{1,3}\s+", block)[0]
            places.append({"name": name, "type": "venue", "summary": clean_ws(block)[:600], "details": clean_ws(block)[:2200], "source": p.name})
    return places

def powers_from_text(text: str) -> list[str]:
    powers=[]
    pairs=[
        (r"adaptive authority", "Adaptive Authority"),
        (r"mythical body", "Mythical Body"),
        (r"exponential", "Exponential growth/power"),
        (r"inmon|淫紋", "Inmon branding"),
        (r"reality (?:warp|manip|bend)", "Reality manipulation"),
        (r"infinite wealth|sudden wealth|infinite money", "Infinite wealth"),
        (r"regression|time[- ]travel|second chance", "Time regression / second chance"),
        (r"mana awaken", "Mana awakening"),
        (r"cultivat", "Cultivation"),
        (r"world.?tree|aetherion|aetherdrake|aetherdrake", "World-tree / bloodline inheritance"),
        (r"super dick|cock (?:growth|size|authority)", "Expansive cock system"),
        (r"echo-?clone", "Echo clones"),
        (r"addiction", "Addiction system"),
        (r"gate(?:s)? hunter|hunter company", "Gates / hunter system"),
        (r"inner voice", "Lifelong inner voice"),
        (r"lucid dream", "Lucid dreaming"),
        (r"concealed? (?:supremacy|power)|hide (?:his )?power", "Concealed power"),
    ]
    low=text.lower()
    for pat,label in pairs:
        if re.search(pat, low) and label not in powers:
            powers.append(label)
    return powers

def main():
    old = load_old_web()
    templates = parse_templates()
    toc_chars = parse_toc_chars()
    lib_places = load_place_library()

    # Start from current saga meta if possible (ids stable)
    try:
        cur_sagas = json.loads((DATA_DIR/"sagas.json").read_text())
        if len(cur_sagas) != 45:
            raise ValueError("bad")
        # keep only meta fields we need; content will be rewritten
        base_sagas = []
        for s in cur_sagas:
            base_sagas.append({
                "id": s["id"], "num": s["num"], "title": s["title"], "url": s.get("url"),
                "hex": s["hex"], "markers": s.get("markers"), "chatFile": s.get("chatFile") or f"{s['hex']}.md",
                "fullTranscriptPath": s.get("fullTranscriptPath") or f"transcripts/{s['hex']}.md",
            })
    except Exception:
        base_sagas = load_current_sagas_meta()

    # Build curated character seed: old web + templates + toc + chat dumps
    characters = {}  # id -> char
    name_to_id = {}

    def upsert_char(name, **kw):
        name = name.strip()
        if not is_clean_person_name(name) and name.lower() not in templates and name.lower() not in name_to_id:
            # allow whitelist from old/templates already accepted
            if not kw.get("force"):
                return None
        force = kw.pop("force", False)
        cid = "char-" + slugify(name)
        # scope collisions lightly: if same name exists, reuse
        if name.lower() in name_to_id:
            cid = name_to_id[name.lower()]
        if cid not in characters:
            characters[cid] = {
                "id": cid, "name": name, "aliases": [], "sagaIds": [], "primarySagaId": "",
                "role": "", "uniqueTitle": "", "relationshipToEon": "", "biography": "",
                "appearance": "", "personality": "", "powers": "", "status": "", "ranks": "",
                "evolution": [], "placesRelated": [], "details": {}, "sourceExcerpts": [],
            }
            name_to_id[name.lower()] = cid
        ch = characters[cid]
        if kw.get("sagaId"):
            sid = kw["sagaId"]
            if sid not in ch["sagaIds"]:
                ch["sagaIds"].append(sid)
            if not ch["primarySagaId"]:
                ch["primarySagaId"] = sid
        for a in kw.get("aliases") or []:
            if a and a not in ch["aliases"] and a != ch["name"]:
                ch["aliases"].append(a)
                name_to_id[a.lower()] = cid
        for k in ("role","uniqueTitle","relationshipToEon","biography","appearance","personality","powers","status","ranks"):
            v = kw.get(k)
            if isinstance(v, str) and v and len(v) > len(ch.get(k) or ""):
                ch[k] = v
        if kw.get("evolution") and (not ch["evolution"] or len(kw["evolution"]) > len(ch["evolution"])):
            ch["evolution"] = kw["evolution"]
        if kw.get("details"):
            ch["details"].update(kw["details"])
        for e in kw.get("sourceExcerpts") or []:
            if e and e not in ch["sourceExcerpts"]:
                ch["sourceExcerpts"].append(e[:400])
        return cid

    # old web characters
    old_by_num = {s["num"]: s for s in old["sagas"]}
    for oc in old["characters"]:
        saga_ids = []
        roles = []
        for ap in oc.get("appearances") or []:
            n = ap.get("sagaNum")
            if n:
                # map later
                roles.append(ap.get("role") or ap.get("details") or "")
        role = next((r for r in roles if r), oc.get("summary") or "")
        upsert_char(oc["name"], role=role, uniqueTitle=role, relationshipToEon=role,
                    biography=(oc.get("summary") or role or oc["name"])[:2000], force=True)

    # templates
    for key, rec in templates.items():
        upsert_char(rec["name"], aliases=rec.get("aliases"), role=rec.get("role"), uniqueTitle=rec.get("uniqueTitle"),
                    relationshipToEon=rec.get("relationshipToEon"), biography=rec.get("biography"),
                    appearance=rec.get("appearance"), personality=rec.get("personality"), powers=rec.get("powers"),
                    status=rec.get("status"), evolution=rec.get("evolution"), details=rec.get("details"),
                    sourceExcerpts=rec.get("sourceExcerpts"), force=True)

    # Build sagas content
    places = {}
    def upsert_place(name, typ="other", summary="", details="", saga_id=None, facts=None):
        if not name or len(name) < 3: return None
        pid = "place-" + slugify(name)
        if pid not in places:
            places[pid] = {"id": pid, "name": name[:120], "type": typ, "sagaIds": [], "summary": "", "details": "",
                           "relatedCharacterIds": [], "notableFacts": []}
        pl = places[pid]
        if saga_id and saga_id not in pl["sagaIds"]:
            pl["sagaIds"].append(saga_id)
        if summary and len(summary) > len(pl["summary"]):
            pl["summary"] = summary[:1200]
        if details and len(details) > len(pl["details"]):
            pl["details"] = details[:3500]
        for f in facts or []:
            if f and f not in pl["notableFacts"]:
                pl["notableFacts"].append(f[:300])
        return pid

    for lp in lib_places:
        upsert_place(lp["name"], lp.get("type") or "venue", lp.get("summary"), lp.get("details"), facts=[f"Library: {lp.get('source')}"])

    sagas_out = []
    for base in sorted(base_sagas, key=lambda s: s["num"]):
        num = base["num"]
        sid = base["id"]
        hex8 = base["hex"]
        full_path = FULL / f"{hex8}.md"
        ex_path = EX / f"{hex8}.json"
        raw = full_path.read_text(encoding="utf-8", errors="replace") if full_path.exists() else ""
        turns = split_turns(raw) if raw else []
        ex = json.loads(ex_path.read_text()) if ex_path.exists() else {}
        first_user = ex.get("firstUser") or next((c for r,c in turns if r=="User"), "")
        opening_grok = ex.get("openingGrok") or next((c for r,c in turns if r=="Grok"), "")[:4000]
        mid = ex.get("midGrok") or ""
        late = ex.get("lateGrok") or ""

        # Cast for this saga
        cast_pairs = []
        os = old_by_num.get(num)
        if os:
            for mt in os.get("meatToilets") or []:
                nm = mt.get("name") or ""
                if nm: cast_pairs.append((nm, mt.get("role") or ""))
            for pl in os.get("places") or []:
                pname = pl.get("name") or ""
                if pname:
                    upsert_place(pname, "venue", pl.get("description") or pname, pl.get("description") or "", saga_id=sid)
        for nm, role in toc_chars.get(num, []):
            if is_clean_person_name(nm) or nm.lower() in templates:
                cast_pairs.append((nm, role))
        for nm, role in parse_chat_dump_chars(hex8):
            cast_pairs.append((nm, role))

        # dedupe cast
        seen_cast = set(); cast_clean = []
        for nm, role in cast_pairs:
            key = nm.lower()
            if key in seen_cast: continue
            if not (is_clean_person_name(nm) or key in templates or key in name_to_id):
                continue
            seen_cast.add(key); cast_clean.append((nm, role))

        mt_ids = []
        for nm, role in cast_clean:
            cid = upsert_char(nm, sagaId=sid, role=role, uniqueTitle=role, relationshipToEon=role,
                              biography=(f"{nm} — {role}" if role else nm), force=True)
            if cid and cid not in mt_ids:
                mt_ids.append(cid)
            # enrich from transcript
            if cid and raw:
                ch = characters[cid]
                snips = descriptive_snippets(raw, ch["name"], limit=8)
                if snips:
                    # build bio
                    if len(ch.get("biography") or "") < 500 or "Story mentions" in (ch.get("biography") or ""):
                        parts = []
                        if ch.get("biography") and len(ch["biography"]) > 40 and "Story mentions" not in ch["biography"]:
                            parts.append(ch["biography"])
                        parts.append(f"{ch['name']} in this saga’s transcript (source excerpts):")
                        parts.extend(snips[:5])
                        ch["biography"] = clean_ws("\n\n".join(parts))[:3800]
                    if not ch.get("appearance"):
                        ch["appearance"] = appearance_from_snips(snips)
                    evo = evolution_from_text(raw, ch["name"])
                    if evo and (not ch.get("evolution") or len(evo) > len(ch.get("evolution") or [])):
                        # merge template evo + story evo
                        merged = list(ch.get("evolution") or [])
                        for e in evo:
                            if e["summary"][:60].lower() not in {x.get("summary","")[:60].lower() for x in merged}:
                                merged.append(e)
                        ch["evolution"] = merged[:10]
                    for snip in snips[:2]:
                        if snip[:280] not in (ch.get("sourceExcerpts") or []):
                            ch.setdefault("sourceExcerpts", []).append(snip[:400])

        # Also enrich template chars if they appear in this saga text
        for key, rec in templates.items():
            if rec["name"] in raw or any(a in raw for a in rec.get("aliases") or []):
                cid = name_to_id.get(rec["name"].lower())
                if not cid: continue
                if sid not in characters[cid]["sagaIds"]:
                    characters[cid]["sagaIds"].append(sid)
                if cid not in mt_ids and re.search(re.escape(rec["name"]), raw):
                    # only auto-add if significantly present
                    if len(descriptive_snippets(raw, rec["name"], 3)) >= 1:
                        mt_ids.append(cid)

        powers = powers_from_text(first_user + "\n" + opening_grok + "\n" + " ".join(ex.get("powersHints") or []))
        # places from transcript
        place_ids = []
        for pname, ptype in mine_places_strict(raw):
            pid = upsert_place(pname, ptype, saga_id=sid)
            if pid and pid not in place_ids:
                place_ids.append(pid)
                # context summary
                sn = descriptive_snippets(raw, pname, 2)
                if sn:
                    places[pid]["summary"] = sn[0][:700]
                    places[pid]["details"] = sn[0][:2000]
        # include already tagged library places if name appears
        for pid, pl in list(places.items()):
            if pl["name"] and pl["name"] in raw:
                if sid not in pl["sagaIds"]:
                    pl["sagaIds"].append(sid)
                if pid not in place_ids:
                    place_ids.append(pid)

        # Cap MT list to avoid absurdity — prefer those with bios/roles
        def mt_score(cid):
            ch = characters.get(cid) or {}
            return (len(ch.get("biography") or ""), len(ch.get("appearance") or ""), len(ch.get("role") or ""))
        mt_ids = sorted(set(mt_ids), key=mt_score, reverse=True)
        if len(mt_ids) > 35:
            mt_ids = mt_ids[:35]

        cast_names = [characters[i]["name"] for i in mt_ids if i in characters]
        place_names = [places[i]["name"] for i in place_ids if i in places]

        how = to_wiki_how(first_user, opening_grok)
        short = to_wiki_short(first_user, opening_grok, powers, cast_names, place_names, mid, late)
        progress = build_progress_from_extract(ex, len(turns))

        details = []
        for p in powers:
            details.append(f"Power/system: {p}")
        details.append(f"Approx. transcript: {len(raw)//1024} KB, {len(turns)} turns ({sum(1 for r,_ in turns if r=='User')} user).")
        details.append(f"Linked meat toilets in roster: {len(mt_ids)}; places linked: {len(place_ids)}.")
        if not mt_ids:
            details.insert(0, "NOTE: No reliably named meat-toilet characters locked for this chat after curated scan (mark-oriented / name-sparse). Full transcript still available.")
        # dump role lines as details
        for nm, role in cast_clean[:12]:
            if role and len(role) > 15:
                details.append(f"{nm}: {role[:220]}")
        # dedupe
        seen=set(); details2=[]
        for d in details:
            k=d.lower()[:90]
            if k not in seen:
                seen.add(k); details2.append(d)

        saga = dict(base)
        saga.update({
            "premise": how,
            "howItStarted": how,
            "shortSummary": short,
            "progress": progress,
            "powers": powers,
            "importantDetails": details2[:28],
            "meatToiletIds": mt_ids,
            "placeIds": place_ids,
            "counts": {
                "meatToilets": len(mt_ids),
                "places": len(place_ids),
                "messageCount": len(turns),
                "userTurns": sum(1 for r,_ in turns if r=="User"),
            },
            "rawNotes": "",
        })
        sagas_out.append(saga)
        print(f"{num:02d} MT={len(mt_ids):2d} places={len(place_ids):2d} progress={len(progress):2d} short={len(short)}")

    # Ensure every character linked to at least their sagaIds from sagas
    for s in sagas_out:
        for cid in s["meatToiletIds"]:
            if cid in characters and s["id"] not in characters[cid]["sagaIds"]:
                characters[cid]["sagaIds"].append(s["id"])
            if cid in characters and not characters[cid].get("primarySagaId"):
                characters[cid]["primarySagaId"] = s["id"]

    # Drop characters with no saga links and tiny bio (orphans from noise)
    char_list = []
    for c in characters.values():
        if not c.get("sagaIds") and len(c.get("biography") or "") < 100 and not c.get("appearance"):
            continue
        # scrub collage marker if any leftover
        if (c.get("biography") or "").startswith("Story mentions of"):
            # keep but ok
            pass
        char_list.append(c)
    char_list.sort(key=lambda c: c["name"].lower())

    # Places: keep those with sagaIds or library details
    place_list = []
    for p in places.values():
        if not p.get("sagaIds") and not p.get("details") and not p.get("notableFacts"):
            continue
        if not p.get("summary"):
            p["summary"] = f"{p.get('type','place').title()} appearing in Eon saga materials."
        place_list.append(p)
    place_list.sort(key=lambda p: p["name"].lower())

    # Recompute placeIds against final place set
    kept_p = {p["id"] for p in place_list}
    for s in sagas_out:
        s["placeIds"] = [i for i in s["placeIds"] if i in kept_p]
        s["counts"]["places"] = len(s["placeIds"])

    kept_c = {c["id"] for c in char_list}
    for s in sagas_out:
        s["meatToiletIds"] = [i for i in s["meatToiletIds"] if i in kept_c]
        s["counts"]["meatToilets"] = len(s["meatToiletIds"])

    bios = [len(c.get("biography") or "") for c in char_list]
    bios_sorted = sorted(bios)
    def pct(n): return sum(1 for b in bios if b >= n)

    meta = {
        "title": "Eon Saga Fandom Wiki",
        "sagaCount": len(sagas_out),
        "characterCount": len(char_list),
        "placeCount": len(place_list),
        "source": "full_chats + chats dumps + library + SAGA index",
        "adult": True,
        "notes": "Quality rebuild: curated roster, template merge, transcript excerpts, wiki-prose saga pages.",
    }
    bundle = {"meta": meta, "sagas": sagas_out, "characters": char_list, "places": place_list}
    (DATA_DIR/"sagas.json").write_text(json.dumps(sagas_out, ensure_ascii=False, indent=2))
    (DATA_DIR/"characters.json").write_text(json.dumps(char_list, ensure_ascii=False, indent=2))
    (DATA_DIR/"places.json").write_text(json.dumps(place_list, ensure_ascii=False, indent=2))
    (DATA_DIR/"meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    (WIKI/"data.js").write_text("window.WIKI_DATA = " + json.dumps(bundle, ensure_ascii=False) + ";\n")

    zero_mt = [s["num"] for s in sagas_out if s["counts"]["meatToilets"]==0]
    zero_pl = [s["num"] for s in sagas_out if s["counts"]["places"]==0]
    linked_chars = set()
    for s in sagas_out:
        linked_chars.update(s["meatToiletIds"])
    linked_bios = [len(characters[i].get("biography") or "") for i in linked_chars if i in characters]
    linked_sorted = sorted(linked_bios)

    prog = f"""# Wiki quality rebuild progress

## Counts
- Sagas: {len(sagas_out)}
- Characters: {len(char_list)} (saga-linked: {len(linked_chars)})
- Places: {len(place_list)}

## Biography length (all characters)
- min {bios_sorted[0] if bios else 0}, median {bios_sorted[len(bios)//2] if bios else 0}, mean {(sum(bios)//len(bios)) if bios else 0}, max {bios_sorted[-1] if bios else 0}
- <50: {sum(1 for b in bios if b<50)}
- <200: {sum(1 for b in bios if b<200)}
- ≥400: {pct(400)}
- ≥800: {pct(800)}

## Biography length (saga-linked MTs only)
- median {linked_sorted[len(linked_sorted)//2] if linked_sorted else 0}, mean {(sum(linked_bios)//len(linked_bios)) if linked_bios else 0}
- <50: {sum(1 for b in linked_bios if b<50)}
- <200: {sum(1 for b in linked_bios if b<200)}
- ≥400: {sum(1 for b in linked_bios if b>=400)}

## Sagas with 0 MTs
{zero_mt}

## Sagas with 0 places
{zero_pl} ({len(zero_pl)} total)

## Method
- Curated characters from old web index + library TITLE templates + TOC + clean chat dump lines (rejected noisy Capitalized Phrase mining)
- Bios/appearance/evolution filled from templates and descriptive transcript windows around each name
- Saga shortSummary / howItStarted rewritten into wiki sections grounded in first User + opening Grok
- Progress rebuilt as named arcs (story headers preferred) with cleaned direction + narration summaries
- Places from PLACE_* + gazetteers + strict place-pattern mining

## Remaining thin stubs
"""
    thin = [c for c in char_list if c["id"] in linked_chars and len(c.get("biography") or "") < 200]
    for c in thin[:80]:
        prog += f"- {c['name']} ({len(c.get('biography') or '')} chars) sagas={len(c.get('sagaIds') or [])}\n"
    (WIKI/"PROGRESS.md").write_text(prog)
    print("DONE chars", len(char_list), "places", len(place_list))
    print("bio median", bios_sorted[len(bios)//2] if bios else 0, "linked median", linked_sorted[len(linked_sorted)//2] if linked_sorted else 0)
    print("lt50", sum(1 for b in bios if b<50), "linked lt50", sum(1 for b in linked_bios if b<50))
    print("zero MT", zero_mt, "zero places", len(zero_pl))

if __name__ == "__main__":
    main()
