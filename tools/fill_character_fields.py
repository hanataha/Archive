#!/usr/bin/env python3
"""Fill every fandom character field from library templates + chats/full_chats.
Never invent. Prefer structured sheets over narrative collage.
"""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from collections import defaultdict

ROOT = Path("/workspace/grok_export_redo")
WIKI = ROOT / "wiki"
FULL = ROOT / "full_chats"
CHATS = ROOT / "chats"
LIB = ROOT / "library"

def clean_ws(s: str) -> str:
    s = re.sub(r"[ \t]+", " ", s or "")
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def load_data():
    raw = (WIKI / "data.js").read_text(encoding="utf-8")
    return json.loads(raw.split("=", 1)[1].strip().rstrip(";"))

# ---------- parse library / chat structured sheets ----------
FIELD_KEYS = [
    "status", "age appearance / freeze", "age appearance", "age",
    "height / body", "height", "default height", "shift height", "body",
    "hair / eyes / scent / marks", "hair / eyes / skin", "hair / eyes", "hair", "eyes", "face",
    "clothes default / access-modified", "clothes default", "clothes",
    "collar / tag / leash", "collar",
    "personality public / private", "personality", "voice",
    "origin", "role vs eon", "role", "titles", "true name / aliases", "aliases",
    "powers", "abilities", "laws", "marks", "ownership", "function",
    "appearance", "body / marks", "face / hair / body",
    "distinct from", "saga / world", "saga", "world / era",
    "owned count", "default shared rules",
]

def parse_kv_block(text: str) -> dict:
    fields = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if re.match(r"^(TITLE|DEMC-MT|CHARACTER SHEET|Identity|Partner|SAGA)\b", ln, re.I):
            if fields and ":" not in ln[:40]:
                break
        m = re.match(r"^([A-Za-z][A-Za-z0-9 /_\-()]{1,60}?)\s*:\s*(.+)$", ln)
        if not m:
            continue
        k = m.group(1).strip().lower()
        v = m.group(2).strip()
        if len(v) < 2:
            continue
        fields[k] = v
    return fields

def normalize_name(n: str) -> str:
    n = re.split(r"\s*[/(]", n)[0].strip()
    n = re.sub(r"\s+", " ", n)
    return n

# Collect sheets keyed by lower name
sheets: dict[str, dict] = {}  # name_lower -> {name, fields, source, raw_title}

def add_sheet(title_line: str, fields: dict, source: str):
    # title like "Fleurdelys (Fleur de Lys / Meat-Mother)"
    base = normalize_name(title_line)
    if len(base) < 2 or base.lower() in {"empty", "paste the other meat toilet here, same heading set"}:
        return
    aliases = []
    m = re.search(r"\(([^)]+)\)", title_line)
    if m:
        aliases = [a.strip() for a in re.split(r"[/,]", m.group(1)) if a.strip()]
    if fields.get("true name / aliases"):
        aliases += [a.strip() for a in re.split(r"[;,]", fields["true name / aliases"]) if a.strip()]
    entry = {
        "name": base,
        "title_line": title_line.strip(),
        "aliases": aliases,
        "fields": fields,
        "source": source,
    }
    keys = {base.lower()}
    for a in aliases:
        na = normalize_name(a)
        if 2 <= len(na) <= 40:
            keys.add(na.lower())
    for k in keys:
        # prefer richer field sets
        prev = sheets.get(k)
        if not prev or len(fields) >= len(prev.get("fields") or {}):
            sheets[k] = entry

# Parse TITLE — blocks
for p in sorted(LIB.glob("*.md")):
    t = p.read_text(encoding="utf-8", errors="replace")
    # TITLE — Name
    parts = re.split(r"\nTITLE\s*[—\-]\s*", t)
    for part in parts[1:]:
        lines = part.splitlines()
        title = lines[0].strip()
        # take until next TITLE or big heading
        body_lines = []
        for ln in lines[1:]:
            if re.match(r"^TITLE\s*[—\-]", ln):
                break
            if re.match(r"^#{1,3}\s", ln) and body_lines:
                break
            body_lines.append(ln)
            if len("\n".join(body_lines)) > 6000:
                break
        fields = parse_kv_block("\n".join(body_lines))
        add_sheet(title, fields, p.name)

    # CHARACTER SHEET\nName (...)
    for m in re.finditer(r"(?mi)^CHARACTER SHEET\s*\n([^\n]+)", t):
        title = m.group(1).strip()
        body = t[m.end(): m.end() + 5000]
        # cut at next CHARACTER SHEET or SAGA SUMMARY or Places
        body = re.split(r"(?mi)^(?:CHARACTER SHEET|SAGA SUMMARY|PLACES|## )\b", body)[0]
        fields = parse_kv_block(body)
        add_sheet(title, fields, p.name)

    # Pipe-style cards: "Name | Saga: x | Status: y | Appearance: z"
    for m in re.finditer(
        r"(?m)^([A-Z][A-Za-zÀ-ÿ' \-]{2,50}(?:\s+[A-Z][A-Za-zÀ-ÿ'\-]{2,30}){0,4})\s*\|\s*((?:Saga|Status|Origin|Appearance|Role|Distinct|Hair|Height|Age|Personality|Powers|Titles)[:\|].{20,800})",
        t,
    ):
        title = m.group(1).strip()
        rest = m.group(2)
        fields = {}
        for piece in re.split(r"\s*\|\s*", rest):
            if ":" in piece:
                k, v = piece.split(":", 1)
                fields[k.strip().lower()] = v.strip()
        if fields.get("appearance") or fields.get("status") or fields.get("origin"):
            add_sheet(title, fields, p.name)

    # Identity Name: blocks (Xuanye style)
    for m in re.finditer(r"(?mi)^Name:\s*(.+)$", t):
        title = m.group(1).strip()
        # window after Identity
        start = max(0, m.start() - 80)
        body = t[m.start(): m.start() + 3500]
        if "Identity" not in t[start:m.start()+20] and "DEMC-MT" not in t[start:m.start()+40]:
            # still allow if nearby height/hair
            if not re.search(r"(?i)(height|hair|titles|face)", body[:400]):
                continue
        fields = parse_kv_block(body)
        # also Map Default height / Face / Hair / Body as appearance pieces
        add_sheet(title, fields, p.name)

print("sheets indexed", len(sheets))

# Dump lines from chats + full_chats + library
DUMP_LINE = re.compile(
    r"(?m)^[\*\-\s]*([A-Z][A-Za-zÀ-ÿ' .\-]{1,45})\s*[—\-–]\s*((?:(?!\n).){8,220}(?:\d{2,3}\s*cm|\d\.\d{1,2}\s*m|[A-K]-?cup|ponytail|hair|eyes|breasts?).{0,80})",
    re.I,
)
PROMPT_APP = re.compile(
    r"(?i)(?:adult woman|woman|girl|female)\s+([A-Z][A-Za-zÀ-ÿ' \-]{2,40})\s+(?:standing|kneeling|sitting|facing)[^.]{0,20}?,\s*([^.]{30,280})",
)
APP_LABEL = re.compile(
    r"(?mi)^Appearance:\s*(.+)$",
)

dumps: dict[str, list[str]] = defaultdict(list)

def add_dump(name: str, line: str):
    name = normalize_name(name)
    if len(name) < 2 or len(name) > 40:
        return
    if re.search(r"(?i)^(hair|face|body|appearance|height|after|master|dick|armpit|selection|distinct|origin|age|night)", name):
        return
    line = clean_ws(line)
    if line and line not in dumps[name.lower()]:
        dumps[name.lower()].append(line[:400])

for folder in [LIB, CHATS, FULL]:
    for p in folder.glob("*.md"):
        t = p.read_text(encoding="utf-8", errors="replace")
        for m in DUMP_LINE.finditer(t):
            add_dump(m.group(1), m.group(0).strip())
        for m in APP_LABEL.finditer(t):
            # look back for a name line
            prev = t[max(0, m.start() - 200): m.start()]
            nm = re.search(r"(?m)^(?:TITLE\s*[—\-]\s*)?([A-Z][A-Za-zÀ-ÿ' \-]{2,50})\s*(?:\||$)", prev)
            if nm:
                add_dump(nm.group(1), "Appearance: " + m.group(1).strip())
        for m in PROMPT_APP.finditer(t):
            add_dump(m.group(1), m.group(1) + ": " + m.group(2).strip())

print("dump names", len(dumps))

# ---------- transcript cache ----------
hex_by = {}
data = load_data()
for s in data["sagas"]:
    hex_by[s["id"]] = s.get("hex")

text_cache = {}

def get_text(hx: str) -> str:
    if not hx:
        return ""
    if hx not in text_cache:
        for base in (FULL, CHATS):
            p = base / f"{hx}.md"
            if p.exists():
                text_cache[hx] = p.read_text(encoding="utf-8", errors="replace")
                break
        else:
            text_cache[hx] = ""
    return text_cache[hx]

# Physical sentence patterns — require name proximity already handled by window
PHYS_CORE = re.compile(
    r"(?i)\b("
    r"\d{2,3}\s*cm|"
    r"\d\.\d{1,2}\s*m|"
    r"[A-K]-?cups?|"
    r"(?:long|short|silky|silver|black|blonde|blond|white|pink|violet|purple|red|crimson|blue|azure|green|emerald|golden|platinum|raven|jet[- ]?black|chestnut|auburn|ocean[- ]?blue|cyan)"
    r"[^.]{0,25}(?:hair|locks|tresses|ponytail)|"
    r"(?:hair|locks|ponytail)[^.]{0,30}(?:silver|black|blonde|white|pink|violet|purple|red|blue|green|golden|platinum|cyan)|"
    r"(?:eyes|irises)\s+(?:of\s+)?(?:a\s+)?(?:deep\s+)?(?:dark|black|brown|amber|gold|golden|green|emerald|blue|azure|violet|purple|crimson|red|hazel|silver|peridot)|"
    r"(?:pale|fair|porcelain|olive|tan|moonstone|bark[- ]?silk)\s+skin|"
    r"(?:tall|petite|towering|slender|voluptuous|athletic|curvy|kyonyuu|hourglass|statuesque|bakunyuu)"
    r")\b"
)

NOISE = re.compile(
    r"(?i)(skip to content|toggle sidebar|MT mark|save all of the female|"
    r"document ·|artifacts/|heart-eyed for you|pregnant, addicted|"
    r"\bcock\b|\bthrust\b|\bcum\b|\bsemen\b|\bfucked\b|\bpussy pounded\b|"
    r"studied his face|entirety of our lineage|captain,\s*Mira|"
    r"sisters helped each other|render_generated|oveloprompt|"
    r"doujinshi hentai template|uncensored|no mosaic|"
    r"deepthroated him|gagged herself|mascara running)"
)

def good_sentence(s: str) -> bool:
    s = clean_ws(s)
    if not (30 <= len(s) <= 280):
        return False
    if NOISE.search(s):
        return False
    if not PHYS_CORE.search(s):
        return False
    # reject if mostly about him
    if re.search(r"(?i)^(he |his |eon |the natural musk of his)", s):
        return False
    return True

def extract_phys_from_text(name: str, text: str, limit=10) -> list[str]:
    bits = []
    if not text or not name:
        return bits
    # Prefer "Name …" descriptive sentences
    name_pat = re.compile(rf"(?i)\b{re.escape(name)}\b")
    for m in name_pat.finditer(text):
        win = text[max(0, m.start() - 100): m.end() + 420]
        # split sentences
        for sent in re.split(r"(?<=[.!?])\s+|\n+", win):
            sent = clean_ws(sent)
            if name.split()[0].lower() not in sent.lower() and not re.search(r"(?i)\b(she|her)\b", sent):
                # still allow if strong phys and close
                if not PHYS_CORE.search(sent):
                    continue
            if good_sentence(sent):
                # must include name OR she/her with phys near name window
                low = sent.lower()
                if name.lower() in low or name.split()[0].lower() in low or re.search(r"(?i)\b(she|her)\b", sent):
                    if sent not in bits:
                        bits.append(sent)
        if len(bits) >= limit:
            break
    # also first-token if multi-word
    tok = name.split()[0]
    if len(bits) < 4 and len(tok) >= 4 and tok != name:
        for m in re.finditer(rf"\b{re.escape(tok)}\b", text):
            win = text[max(0, m.start() - 80): m.end() + 350]
            for sent in re.split(r"(?<=[.!?])\s+|\n+", win):
                sent = clean_ws(sent)
                if good_sentence(sent) and tok.lower() in sent.lower():
                    if sent not in bits:
                        bits.append(sent)
            if len(bits) >= limit:
                break
    return bits[:limit]

def sheet_for_char(c: dict) -> dict | None:
    names = [c["name"]] + list(c.get("aliases") or [])
    for n in names:
        s = sheets.get(normalize_name(n).lower())
        if s:
            return s
    # fuzzy: any sheet name contained in char name or vice versa
    cn = c["name"].lower()
    for k, s in sheets.items():
        if k == cn or k in cn or cn in k:
            if len(k) >= 4:
                return s
    return None

def dumps_for_char(c: dict) -> list[str]:
    out = []
    names = [c["name"]] + list(c.get("aliases") or [])
    for n in names:
        out.extend(dumps.get(normalize_name(n).lower(), []))
    # first token
    tok = c["name"].split()[0].lower()
    if len(tok) >= 4:
        out.extend(dumps.get(tok, []))
    # dedupe
    seen = set()
    uniq = []
    for x in out:
        if x.lower() not in seen:
            seen.add(x.lower())
            uniq.append(x)
    return uniq

def build_appearance(c, sheet, dump_lines, saga_ids) -> str:
    parts = []
    f = (sheet or {}).get("fields") or {}
    # structured template pieces
    for k in [
        "appearance", "height / body", "height", "default height", "shift height",
        "face", "face / hair / body", "hair / eyes / scent / marks", "hair / eyes / skin",
        "hair / eyes", "hair", "eyes", "body", "body / marks",
        "clothes default / access-modified", "clothes default", "clothes",
        "collar / tag / leash", "age appearance / freeze", "age appearance",
    ]:
        if f.get(k):
            label = k.replace(" / ", " / ").title()
            parts.append(f"{label}: {f[k]}")
    # Xuanye-style flat keys
    if not parts and f:
        for k in ["default height", "shift height", "face", "hair", "body", "clothes"]:
            if f.get(k):
                parts.append(f"{k.title()}: {f[k]}")

    if parts:
        prose = clean_ws("\n".join(parts))
        # optional short dump addenda if not overlapping
        extra = []
        for d in dump_lines[:3]:
            if d.lower() not in prose.lower() and PHYS_CORE.search(d) and not NOISE.search(d):
                extra.append(d)
        if extra:
            prose += "\n\nAlso noted in dumps: " + " | ".join(extra)
        return prose[:2800]

    # dump lines as primary
    good_dumps = [d for d in dump_lines if PHYS_CORE.search(d) and not NOISE.search(d)]
    if good_dumps:
        return clean_ws(
            f"{c['name']} — source dump notes:\n" + "\n".join(good_dumps[:6])
        )[:2400]

    # transcript mining
    bits = []
    for sid in (saga_ids or [])[:8]:
        bits.extend(extract_phys_from_text(c["name"], get_text(hex_by.get(sid, "")), limit=6))
        if len(bits) >= 8:
            break
    # dedupe similar
    uniq = []
    for b in bits:
        if all(b[:40].lower() not in u.lower() for u in uniq):
            uniq.append(b)
    if uniq:
        sents = []
        for b in uniq[:8]:
            if not b.endswith((".", "!", "?")):
                b += "."
            sents.append(b)
        return clean_ws(f"{c['name']}'s appearance in saga narration:\n" + " ".join(sents))[:2400]

    # keep previous if it had real phys and wasn't collage junk
    old = c.get("appearance") or ""
    if old and PHYS_CORE.search(old) and "as described in the saga text" not in old:
        # scrub noise sentences
        keep = [s for s in re.split(r"(?<=[.!?])\s+", old) if good_sentence(s) or PHYS_CORE.search(s) and not NOISE.search(s)]
        if keep:
            return clean_ws(" ".join(keep))[:2400]
    return ""

def build_personality(c, sheet, saga_ids) -> str:
    f = (sheet or {}).get("fields") or {}
    for k in ["personality public / private", "personality", "voice"]:
        if f.get(k):
            return clean_ws(f.get(k))[:2000]
    # behavioral cues — filter NSFW oral fixation
    cues = []
    verb = re.compile(
        rf"(?i)\b(?:{re.escape(c['name'].split()[0])}|she)\s+"
        rf"(?:was|is|spoke|smiled|laughed|whispered|glared|blushed|teased|"
        rf"growled|murmured|hissed|giggled|pouted|commanded|obeyed|begged|"
        rf"devoted|loved|hated|feared|served|refused|insisted|claimed)\b[^\.\n]{{8,120}}"
    )
    trait = re.compile(
        r"(?i)\b(?:arrogant|gentle|devoted|obsessive|cold|warm|shy|bold|loyal|jealous|"
        r"possessive|elegant|cruel|kind|stoic|playful|dominant|submissive|proud|clingy|"
        r"calm|fierce|fanatic|tender|ruthless|dutiful|kuudere|yandere|tsundere|dignified|"
        r"precise|armed|exact|fanatic|maternal|warrior|idol)\b[^\.\n]{0,80}"
    )
    for sid in (saga_ids or [])[:5]:
        text = get_text(hex_by.get(sid, ""))
        for m in re.finditer(re.escape(c["name"]), text):
            win = text[max(0, m.start() - 60): m.end() + 220]
            if NOISE.search(win):
                continue
            for vm in verb.finditer(win):
                b = clean_ws(vm.group(0))
                if NOISE.search(b):
                    continue
                if b not in cues:
                    cues.append(b)
            for tm in trait.finditer(win):
                b = clean_ws(tm.group(0))
                if NOISE.search(b) or len(b) < 8:
                    continue
                if b not in cues:
                    cues.append(b)
            if len(cues) >= 8:
                break
        if len(cues) >= 8:
            break
    if cues:
        return clean_ws(f"{c['name']}'s demeanor in-source: " + " ".join(cues[:8]))[:1600]
    old = c.get("personality") or ""
    if old and not NOISE.search(old) and "Demeanor cues" not in old:
        return old[:1600]
    if old and not re.search(r"(?i)(gagged|deepthroat|mascara|sucking desperately)", old):
        return old[:1600]
    return ""

def build_powers(c, sheet, saga_ids) -> str:
    f = (sheet or {}).get("fields") or {}
    chunks = []
    for k in ["powers", "abilities", "laws", "marks", "ownership", "function"]:
        if f.get(k):
            chunks.append(f"{k.title()}: {f[k]}")
    if chunks:
        return clean_ws("\n".join(chunks))[:2000]
    bits = []
    pat = re.compile(
        r"(?i)[^\.\n]{0,40}(?:qi|mana|magic|spell|technique|authority|bloodline|"
        r"resonance|cultivation|domain|sword (?:art|intent)|divine|blessing|curse|"
        r"ability|power|firewall|reality|clone|echo)[^\.\n]{5,120}"
    )
    for sid in (saga_ids or [])[:5]:
        text = get_text(hex_by.get(sid, ""))
        for m in re.finditer(re.escape(c["name"]), text):
            win = text[max(0, m.start() - 150): m.end() + 320]
            for pm in pat.finditer(win):
                b = clean_ws(pm.group(0))
                if NOISE.search(b):
                    continue
                if b not in bits:
                    bits.append(b)
            if len(bits) >= 7:
                break
        if len(bits) >= 7:
            break
    if bits:
        return clean_ws(f"{c['name']}'s powers / systems mentioned in-source:\n" + "\n".join(f"- {b}" for b in bits[:7]))[:1800]
    old = c.get("powers") or ""
    if old and not NOISE.search(old[:100]):
        return old[:1800]
    return ""

def build_status_role(c, sheet, dump_lines):
    f = (sheet or {}).get("fields") or {}
    status = f.get("status") or ""
    role = f.get("role vs eon") or f.get("role") or ""
    titles = f.get("titles") or ""
    if sheet and sheet.get("title_line") and "(" in sheet["title_line"]:
        # parenthetical titles
        m = re.search(r"\(([^)]+)\)", sheet["title_line"])
        if m and not titles:
            titles = m.group(1)
    if not status and dump_lines:
        # take before emdash detail
        d0 = dump_lines[0]
        m = re.match(r"^(.+?)\s*[—\-–]\s*(.+)$", d0)
        if m:
            status = m.group(2)[:200]
            if not role:
                role = m.group(1).strip()
    if not role:
        role = titles or status or c.get("role") or ""
    if not status:
        status = titles or role or c.get("status") or ""
    # clean pollution
    def scrub(s):
        s = clean_ws(s)
        if re.search(r"(?i)(pregnant bellies|sisters helped|cock|pussy|uniforms—hiding)", s):
            s = s.split(";")[0]
        return s[:400]
    status, role = scrub(status), scrub(role)
    unique = titles or role or status
    rel = role or status
    ranks = ""
    if titles:
        ranks = titles
    elif status and re.search(r"(?i)(queen|empress|saint|wife|heir|priest|princess|matriarch|captain|ceo|arch|sovereign|meat|rank)", status):
        ranks = status
    # scrub ranks
    if ranks and re.search(r"(?i)(cock|pussy|heir home|heir outer)", ranks):
        ranks = ""
    return status, role[:300], unique[:300], rel[:300], ranks[:300]

def build_biography(c, sheet, saga_ids) -> str:
    f = (sheet or {}).get("fields") or {}
    parts = []
    if f.get("origin"):
        parts.append(f.get("origin"))
    if f.get("saga") or f.get("saga / world"):
        parts.append("Saga: " + (f.get("saga") or f.get("saga / world")))
    if f.get("role vs eon"):
        parts.append("Role vs Eon: " + f["role vs eon"])
    if f.get("distinct from"):
        parts.append("Distinct from: " + f["distinct from"])
    if parts:
        bio = clean_ws("\n\n".join(parts))
        # append short saga summary excerpts if available from template source text — skip
        return bio[:3500]

    # from existing biography: keep if long and not wrong-person collage of other names heavily
    old = c.get("biography") or ""
    if len(old) > 400:
        # light scrub of UI chrome
        old = re.sub(r"(?i)skip to content.*?(\n|$)", "", old)
        return clean_ws(old)[:3500]

    # gather narrative paragraphs mentioning name
    paras = []
    for sid in (saga_ids or [])[:4]:
        text = get_text(hex_by.get(sid, ""))
        for m in re.finditer(re.escape(c["name"]), text):
            # take surrounding paragraph
            a = text.rfind("\n\n", 0, m.start())
            b = text.find("\n\n", m.end())
            para = text[a if a != -1 else max(0, m.start()-200): b if b != -1 else m.end()+400]
            para = clean_ws(para)
            if 120 <= len(para) <= 900 and not NOISE.search(para[:80]):
                if para not in paras:
                    paras.append(para)
            if len(paras) >= 4:
                break
        if len(paras) >= 4:
            break
    if paras:
        return clean_ws(f"{c['name']} in source narration:\n\n" + "\n\n".join(paras[:4]))[:3500]
    return old[:3500] if old else ""

def build_evolution(c, sheet, saga_ids) -> list:
    f = (sheet or {}).get("fields") or {}
    evo = []
    # template age / role progression
    if f.get("role vs eon") and "→" in f["role vs eon"]:
        for i, stage in enumerate(re.split(r"\s*→\s*", f["role vs eon"])):
            evo.append({"title": f"Stage {i+1}", "summary": stage.strip()[:400]})
    if f.get("age appearance / freeze") or f.get("age"):
        evo.append({"title": "Age / freeze", "summary": (f.get("age appearance / freeze") or f.get("age"))[:400]})
    # story cues near name
    cues = [
        (r"(?i)\b(pregnan\w+|with child|belly swell)", "Pregnancy"),
        (r"(?i)\b(married|marriage vow|wedding|wife)", "Marriage / vow"),
        (r"(?i)\b(brand(?:ed)?|collar(?:ed)?|claim(?:ed)?|owned)", "Claim / brand"),
        (r"(?i)\b(awaken(?:ed|ing)?|breakthrough|ascend(?:ed|sion)?|transform(?:ed|ation)?)", "Awakening / transform"),
        (r"(?i)\b(adult[- ]grown|grew into|matured)", "Growth"),
    ]
    seen_titles = {e["title"] for e in evo}
    for sid in (saga_ids or [])[:5]:
        text = get_text(hex_by.get(sid, ""))
        for m in re.finditer(re.escape(c["name"]), text):
            win = text[max(0, m.start() - 80): m.end() + 280]
            if NOISE.search(win):
                continue
            for pat, title in cues:
                if title in seen_titles:
                    continue
                if re.search(pat, win):
                    # take a clean sentence
                    sents = [clean_ws(s) for s in re.split(r"(?<=[.!?])\s+", win)]
                    pick = next((s for s in sents if re.search(pat, s) and 40 <= len(s) <= 280 and not NOISE.search(s)), None)
                    if pick:
                        evo.append({"title": title, "summary": pick[:400]})
                        seen_titles.add(title)
            if len(evo) >= 6:
                break
        if len(evo) >= 6:
            break
    # filter old polluted evolution
    cleaned = []
    for e in evo:
        if NOISE.search(e.get("summary") or ""):
            continue
        if re.search(r"(?i)(captain,\s*Mira|sisters helped|pregnant, addicted)", e.get("summary") or ""):
            continue
        cleaned.append(e)
    return cleaned[:8]

def build_details(c, sheet) -> dict:
    f = (sheet or {}).get("fields") or {}
    skip = {
        "appearance", "personality", "personality public / private", "powers", "status",
        "role", "role vs eon", "height / body", "hair / eyes / scent / marks", "origin",
        "titles", "voice", "hair", "eyes", "face", "body", "clothes", "height",
    }
    details = {}
    for k, v in f.items():
        if k in skip:
            continue
        if len(v) < 3 or len(v) > 800:
            continue
        details[k] = v[:500]
        if len(details) >= 12:
            break
    # keep old details if richer
    old = c.get("details") or {}
    if isinstance(old, dict):
        for k, v in old.items():
            if k not in details and v:
                details[k] = v
    return details

def build_places(c, places_by_saga, saga_ids) -> list:
    # placesRelated is list of place ids (app uses placeCard which needs id)
    # Check current schema
    return c.get("placesRelated") or []

# places: ensure list of ids that exist
place_ids = {p["id"] for p in data["places"]}
places_by_id = {p["id"]: p for p in data["places"]}
# map saga -> place ids
saga_places = defaultdict(list)
for p in data["places"]:
    for sid in p.get("sagaIds") or []:
        saga_places[sid].append(p["id"])

def related_places(c, saga_ids):
    # Prefer places whose names appear near character in transcripts
    cand = []
    seen = set()
    for sid in saga_ids or []:
        for pid in saga_places.get(sid, []):
            if pid in seen:
                continue
            pname = places_by_id[pid]["name"]
            if len(pname) < 4:
                continue
            # check co-occurrence in any saga text
            for sid2 in saga_ids[:4]:
                text = get_text(hex_by.get(sid2, ""))
                if not text:
                    continue
                if c["name"] in text and pname in text:
                    # proximity
                    for m in re.finditer(re.escape(c["name"]), text):
                        win = text[max(0, m.start()-500): m.end()+500]
                        if pname in win:
                            seen.add(pid)
                            cand.append(pid)
                            break
                if pid in seen:
                    break
            if len(cand) >= 8:
                return cand
    # fallback: first few places of primary sagas
    if not cand:
        for sid in (saga_ids or [])[:2]:
            for pid in saga_places.get(sid, [])[:3]:
                if pid not in seen:
                    seen.add(pid)
                    cand.append(pid)
    return cand[:8]

# ---------- apply ----------
stats = defaultdict(int)
empty_notes = defaultdict(list)

for c in data["characters"]:
    sheet = sheet_for_char(c)
    dump_lines = dumps_for_char(c)
    sids = c.get("sagaIds") or []

    app = build_appearance(c, sheet, dump_lines, sids)
    if app:
        c["appearance"] = app
        stats["appearance"] += 1
    else:
        empty_notes["appearance"].append(c["name"])

    pers = build_personality(c, sheet, sids)
    if pers:
        c["personality"] = pers
        stats["personality"] += 1
    else:
        empty_notes["personality"].append(c["name"])

    pows = build_powers(c, sheet, sids)
    if pows:
        c["powers"] = pows
        stats["powers"] += 1
    else:
        empty_notes["powers"].append(c["name"])

    status, role, unique, rel, ranks = build_status_role(c, sheet, dump_lines)
    if status:
        c["status"] = status
        stats["status"] += 1
    else:
        empty_notes["status"].append(c["name"])
    if role:
        c["role"] = role
        stats["role"] += 1
    if unique:
        c["uniqueTitle"] = unique
    if rel:
        c["relationshipToEon"] = rel
    if ranks:
        c["ranks"] = ranks
        stats["ranks"] += 1
    else:
        c["ranks"] = c.get("ranks") if c.get("ranks") and not NOISE.search(str(c.get("ranks"))) else ""
        if c["ranks"]:
            stats["ranks"] += 1
        else:
            empty_notes["ranks"].append(c["name"])

    bio = build_biography(c, sheet, sids)
    if bio:
        c["biography"] = bio
        stats["biography"] += 1
    else:
        empty_notes["biography"].append(c["name"])

    evo = build_evolution(c, sheet, sids)
    if evo:
        c["evolution"] = evo
        stats["evolution"] += 1
    else:
        # clear polluted
        old = c.get("evolution") or []
        cleaned = []
        if isinstance(old, list):
            for e in old:
                if isinstance(e, dict) and e.get("summary") and not NOISE.search(e["summary"]):
                    if not re.search(r"(?i)(captain,\s*Mira|sisters helped|Facebook and Twitter)", e["summary"]):
                        cleaned.append(e)
        c["evolution"] = cleaned
        if cleaned:
            stats["evolution"] += 1
        else:
            empty_notes["evolution"].append(c["name"])

    details = build_details(c, sheet)
    c["details"] = details
    if details:
        stats["details"] += 1
    else:
        empty_notes["details"].append(c["name"])

    # aliases from sheet
    if sheet and sheet.get("aliases"):
        als = list(c.get("aliases") or [])
        for a in sheet["aliases"]:
            if a not in als and a.lower() != c["name"].lower() and len(a) < 60:
                als.append(a)
        c["aliases"] = als[:8]

    c["placesRelated"] = related_places(c, sids)
    if c["placesRelated"]:
        stats["placesRelated"] += 1
    else:
        empty_notes["placesRelated"].append(c["name"])

print("filled counts", dict(stats))
print("empty appearance", empty_notes["appearance"][:30], "n=", len(empty_notes["appearance"]))
print("empty personality", len(empty_notes["personality"]), "powers", len(empty_notes["powers"]))

# samples
for want in ["Yeonhwa", "Fleurdelys", "Gayeon", "Liriana", "Aeloria", "Lin Qing", "Xuanye", "Elara Voss"]:
    c = next((x for x in data["characters"] if want.lower() in x["name"].lower()), None)
    if not c:
        print("MISSING", want)
        continue
    print("====", c["name"])
    print("APP:", (c.get("appearance") or "EMPTY")[:280])
    print("PER:", (c.get("personality") or "EMPTY")[:160])
    print("POW:", (c.get("powers") or "EMPTY")[:140])
    print("STA:", (c.get("status") or "EMPTY")[:100], "| RANK:", (c.get("ranks") or "EMPTY")[:80])
    print("EVO:", len(c.get("evolution") or []), "DET:", len(c.get("details") or {}), "PL:", len(c.get("placesRelated") or []))

# write
meta = data["meta"]
meta["notes"] = (
    "Character fields filled from library TITLE/CHARACTER SHEET templates, dump lines, "
    "and filtered transcript windows. Empty only when source lacks that category."
)
bundle = {"meta": meta, "sagas": data["sagas"], "characters": data["characters"], "places": data["places"]}
(WIKI / "data.js").write_text("window.WIKI_DATA = " + json.dumps(bundle, ensure_ascii=False) + "\n", encoding="utf-8")
(WIKI / "data" / "characters.json").write_text(json.dumps(data["characters"], ensure_ascii=False, indent=2), encoding="utf-8")
(WIKI / "data" / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

# PROGRESS
linked = set()
for s in data["sagas"]:
    linked.update(s.get("meatToiletIds") or [])
chars = {c["id"]: c for c in data["characters"]}

def flen(cid, f):
    v = chars[cid].get(f)
    if isinstance(v, str):
        return len(v.strip())
    if isinstance(v, (list, dict)):
        return len(v)
    return 0

rows = []
for f in ["appearance", "biography", "personality", "powers", "status", "ranks", "evolution", "details", "placesRelated", "role"]:
    n = sum(1 for i in linked if flen(i, f) > 0)
    rows.append(f"| {f} | {n}/{len(linked)} |")

no_app = [chars[i]["name"] for i in linked if flen(i, "appearance") == 0]
no_pers = [chars[i]["name"] for i in linked if flen(i, "personality") == 0]

(WIKI / "PROGRESS.md").write_text(
    "# Wiki quality — character field completeness\n\n"
    f"## Linked MT field fill rates (n={len(linked)})\n"
    "| Field | Filled |\n|--|--|\n" + "\n".join(rows) + "\n\n"
    "## Appearance still empty (no usable physical description in source)\n"
    + ("\n".join(f"- {n}" for n in no_app) or "- none") + "\n\n"
    "## Personality still empty\n"
    + ("\n".join(f"- {n}" for n in no_pers[:40]) or "- none")
    + (f"\n- … +{len(no_pers)-40} more" if len(no_pers) > 40 else "")
    + "\n\n## Method\n"
    "- Library TITLE / CHARACTER SHEET / Identity cards preferred\n"
    "- Dump lines (`Name — … cm / cup / hair`) from chats + full_chats + library\n"
    "- Transcript windows only keep sentences with real physical markers; NSFW noise filtered\n"
    "- Evolution = role arrows from sheets + pregnancy/marriage/claim/awaken cues near name\n"
    "- details = leftover template key/values; placesRelated = co-occurring places\n"
    "- Never invent; empty only when source lacks category\n\n"
    "## Deliverables\n"
    "- `/workspace/grok_export_redo/wiki/data.js` + `data/characters.json`\n"
    "- Zip: `/workspace/grok_export_redo/wiki_fandom.zip`\n"
    "- Parent CopyFromBox → Desktop `Grok_Export\\\\wiki\\\\`\n",
    encoding="utf-8",
)

zp = ROOT / "wiki_fandom.zip"
with ZipFile(zp, "w", ZIP_DEFLATED) as z:
    for p in WIKI.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(WIKI.parent)
        if "extracts" in rel.parts or "tools" in rel.parts:
            continue
        z.write(p, rel.as_posix())
shutil.rmtree(ROOT / "web" / "wiki", ignore_errors=True)
shutil.copytree(WIKI, ROOT / "web" / "wiki", ignore=shutil.ignore_patterns("extracts", "tools"))
print("zip MB", round(zp.stat().st_size / 1e6, 2))
