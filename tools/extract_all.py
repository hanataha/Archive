#!/usr/bin/env python3
"""Extract structured turn data from all 45 full_chats for wiki synthesis."""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path

ROOT = Path("/workspace/grok_export_redo")
FULL = ROOT / "full_chats"
CHATS = ROOT / "chats"
MATCHED = ROOT / "MATCHED_CHATS.md"
OUT = ROOT / "wiki" / "extracts"
OUT.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:80] or "x"

def parse_matched(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries = []
    section = None
    for line in text.splitlines():
        if line.startswith("## Marker A only"):
            section = "A"
        elif line.startswith("## Both A+B"):
            section = "A+B"
        elif line.startswith("## Marker B only"):
            section = "B"
        m = re.match(
            r"\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(https://grok\.com/c/([0-9a-f-]{36}))\s*\|\s*([^|]+)\|",
            line,
        )
        if not m:
            continue
        num, title, url, uuid, markers = m.groups()
        markers = markers.strip() or (section or "")
        hex8 = uuid.split("-")[0]
        entries.append({
            "num": int(num),
            "title": title.strip(),
            "url": url.strip(),
            "uuid": uuid,
            "hex": hex8,
            "markers": markers,
            "id": f"saga-{int(num):02d}-{slugify(title.strip())}",
        })
    return entries

def split_turns(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"\n## (User|Grok)\n", text)
    turns = []
    i = 1
    while i + 1 < len(parts):
        turns.append((parts[i], parts[i + 1].strip()))
        i += 2
    return turns

def clean_grok(s: str) -> str:
    s = re.sub(r"^Worked for [^\n]+\n?", "", s)
    return s.strip()

def first_paras(s: str, n: int = 3, maxlen: int = 1200) -> str:
    s = clean_grok(s)
    paras = [p.strip() for p in re.split(r"\n\s*\n", s) if p.strip()]
    out = []
    total = 0
    for p in paras:
        if total >= maxlen:
            break
        out.append(p[:800])
        total += len(p)
        if len(out) >= n:
            break
    return "\n\n".join(out)

def user_title(s: str) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    # strip common continue prefixes for title
    t = s
    for pat in [
        r"^Continue[,.]?\s*",
        r"^Make it very long[^.]*\.\s*",
        r"^the next day[,.]?\s*",
    ]:
        t = re.sub(pat, "", t, flags=re.I)
    t = t[:120]
    if len(s) > 120:
        t = t.rsplit(" ", 1)[0] + "…"
    return t or "Continue"

def extract_headers(s: str) -> list[str]:
    hs = []
    for m in re.finditer(r"^(#{1,3})\s+(.+)$", s, re.M):
        h = m.group(2).strip()
        if len(h) < 80 and not h.lower().startswith("user") and "worked for" not in h.lower():
            hs.append(h)
    return hs[:40]

def powers_hints(text: str) -> list[str]:
    hints = []
    patterns = [
        (r"adaptive authority", "Adaptive Authority"),
        (r"mythical body", "Mythical Body"),
        (r"super dick|cock (?:growth|size|authority)", "Super/expansive cock system"),
        (r"exponential (?:power|growth)", "Exponential power/growth"),
        (r"inmon|淫紋", "Inmon branding"),
        (r"reality (?:warp|manipulation|bend)", "Reality manipulation"),
        (r"mana awaken", "Mana awakening"),
        (r"cultivat", "Cultivation system"),
        (r"gate(?:s)? hunter|hunter company", "Gates / hunter system"),
        (r"echo-?clone", "Echo clones"),
        (r"infinite wealth|sudden wealth", "Infinite wealth"),
        (r"time[- ]travel|regression|second chance", "Time travel / regression"),
        (r"lucid dream", "Lucid dreaming"),
        (r"inner voice", "Lifelong inner voice"),
        (r"concealed? (?:supremacy|power)|hide (?:his )?power", "Concealed power"),
        (r"aetherdrake|draconic", "Draconic / Aetherdrake blood"),
        (r"world[- ]?tree|aetherion", "World Tree / Aetherion"),
        (r"addiction", "Addiction system"),
    ]
    low = text.lower()
    seen = set()
    for pat, label in patterns:
        if re.search(pat, low) and label not in seen:
            hints.append(label)
            seen.add(label)
    return hints

def extract_chat_dump_chars(hex8: str) -> list[str]:
    p = CHATS / f"{hex8}.md"
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8", errors="replace")
    names = []
    # Females saved lines
    for m in re.finditer(r"^([A-Z][^—\n]{1,80})\s*—\s*(.+)$", text, re.M):
        name = m.group(1).strip()
        if name.lower().startswith(("schema", "characters", "places", "index", "roster", "files", "if you")):
            continue
        names.append(f"{name} — {m.group(2).strip()[:200]}")
    # TITLE — Name patterns from embedded templates
    for m in re.finditer(r"TITLE\s*[—-]\s*([^\n(]+)", text):
        names.append(m.group(1).strip())
    return names[:80]

def main():
    roster = parse_matched(MATCHED)
    index = []
    for e in roster:
        fp = FULL / f"{e['hex']}.md"
        rec = dict(e)
        if not fp.exists():
            rec["error"] = "missing full chat"
            (OUT / f"{e['hex']}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
            index.append(rec)
            continue
        raw = fp.read_text(encoding="utf-8", errors="replace")
        header = raw.split("\n## ", 1)[0]
        turns = split_turns(raw)
        first_user = next((c for r, c in turns if r == "User"), "")
        first_grok = next((c for r, c in turns if r == "Grok"), "")
        # If scrape started mid-chat, first turn may be Grok — still capture first User
        user_turns = [(i, c) for i, (r, c) in enumerate(turns) if r == "User"]
        grok_turns = [(i, c) for i, (r, c) in enumerate(turns) if r == "Grok"]

        beats = []
        for ui, uc in user_turns:
            # following grok
            nxt = ""
            for gi, gc in grok_turns:
                if gi > ui:
                    nxt = gc
                    break
            title = user_title(uc)
            # prefer a story header from following grok if present
            hdrs = extract_headers(nxt)
            if hdrs and not title.lower().startswith("start"):
                # keep user-derived title but note header
                pass
            summary = first_paras(nxt, n=2, maxlen=900) if nxt else ""
            beats.append({
                "userIndex": ui,
                "title": title,
                "userSnippet": uc[:600],
                "summarySource": summary,
                "grokHeaders": hdrs[:5],
            })

        # Sample mid/late grok headers for structure
        all_headers = []
        for _, gc in grok_turns:
            all_headers.extend(extract_headers(gc))
        # dedupe preserve order
        seen_h = set()
        uniq_h = []
        for h in all_headers:
            k = h.lower()
            if k not in seen_h:
                seen_h.add(k)
                uniq_h.append(h)

        body_sample = "\n".join(c[:2000] for r, c in turns[:8])
        powers = powers_hints(first_user + "\n" + body_sample)

        # Named female-ish candidates from early+late text (very light)
        name_hits = sorted(set(re.findall(
            r"\b([A-Z][a-z]{2,}(?:[\s-][A-Z][a-z]{2,}){0,2})\b",
            "\n".join(c[:3000] for _, c in turns[:6] + turns[-4:])
        )))
        # filter common English words
        STOP = {"The","And","Then","When","This","That","With","From","After","Before","Continue","Worked","Make","Very","Long","Eon","Grok","User","Chapter","Phase","Monday","Sunday","Tuesday","Wednesday","Thursday","Friday","Saturday","October","December","January","February","March","April","May","June","July","August","September","Tokyo","Seoul","Japan","Korea","China","French","English","Document","Download","Schema","Files","Index","Roster","Places","Characters","Markers","Scraped","Auto","True","False","Not","None","She","He","Her","His","They","Their"}
        name_hits = [n for n in name_hits if n not in STOP and len(n) > 3][:60]

        rec.update({
            "chatFile": f"{e['hex']}.md",
            "bytes": len(raw),
            "turnCount": len(turns),
            "userCount": len(user_turns),
            "grokCount": len(grok_turns),
            "header": header.strip(),
            "firstUser": first_user[:8000],
            "openingGrok": first_paras(first_grok, n=4, maxlen=2500),
            "openingGrokFullStart": clean_grok(first_grok)[:3500],
            "beats": beats[:40],
            "storyHeaders": uniq_h[:50],
            "powersHints": powers,
            "nameHits": name_hits,
            "dumpNames": extract_chat_dump_chars(e["hex"]),
            "midGrok": first_paras(grok_turns[len(grok_turns)//2][1], n=2, maxlen=800) if grok_turns else "",
            "lateGrok": first_paras(grok_turns[-1][1], n=2, maxlen=800) if grok_turns else "",
        })
        (OUT / f"{e['hex']}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        # also human-readable md for synthesis reading
        md = []
        md.append(f"# {e['num']}. {e['title']}\n")
        md.append(f"Markers: {e['markers']} | turns: {len(turns)} | file: {e['hex']}.md\n")
        md.append(f"URL: {e['url']}\n")
        md.append("\n## First User\n\n" + first_user[:5000] + "\n")
        md.append("\n## Opening Grok\n\n" + rec["openingGrok"] + "\n")
        md.append("\n## Powers hints\n\n" + ", ".join(powers) + "\n")
        md.append("\n## Dump names\n\n" + "\n".join(f"- {x}" for x in rec["dumpNames"][:40]) + "\n")
        md.append("\n## Story headers\n\n" + "\n".join(f"- {h}" for h in uniq_h[:40]) + "\n")
        md.append("\n## Progress beats (user-driven)\n")
        for i, b in enumerate(beats[:30], 1):
            md.append(f"\n### Beat {i}: {b['title']}\n")
            md.append(f"User: {b['userSnippet'][:350]}\n")
            if b["grokHeaders"]:
                md.append(f"Headers: {', '.join(b['grokHeaders'])}\n")
            md.append(f"\nGrok start:\n{b['summarySource'][:700]}\n")
        md.append("\n## Mid Grok\n\n" + rec["midGrok"] + "\n")
        md.append("\n## Late Grok\n\n" + rec["lateGrok"] + "\n")
        (OUT / f"{e['hex']}.md").write_text("\n".join(md), encoding="utf-8")
        index.append({
            "num": e["num"], "id": e["id"], "hex": e["hex"], "title": e["title"],
            "markers": e["markers"], "turns": len(turns), "bytes": len(raw),
            "powers": powers, "dumpNameCount": len(rec["dumpNames"]),
        })
        print(f"OK {e['num']:02d} {e['hex']} turns={len(turns)} beats={len(beats)}")

    (OUT / "_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(index)} extracts to {OUT}")

if __name__ == "__main__":
    main()
