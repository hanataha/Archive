#!/usr/bin/env python3
"""Category-correct character pages + group meat-toilet entities. No invented plot."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy

ROOT = Path("/workspace/grok_export_redo")
WIKI = ROOT / "wiki"
DATA = WIKI / "data"
FULL = ROOT / "full_chats"

def load_bundle():
    chars = json.loads((DATA / "characters.json").read_text(encoding="utf-8"))
    sagas = json.loads((DATA / "sagas.json").read_text(encoding="utf-8"))
    places = json.loads((DATA / "places.json").read_text(encoding="utf-8"))
    meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
    return chars, sagas, places, meta

def write_bundle(chars, sagas, places, meta):
    meta = dict(meta)
    meta["characterCount"] = len(chars)
    meta["notes"] = (
        "Character fields are category-correct (bio/life story, appearance=looks, "
        "personality=demeanor, powers/status/ranks/evolution=those only). "
        "Grouped meat toilets use kind=group with variants. Never invent."
    )
    (DATA / "characters.json").write_text(json.dumps(chars, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "sagas.json").write_text(json.dumps(sagas, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "places.json").write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    bundle = {"meta": meta, "sagas": sagas, "characters": chars, "places": places}
    (WIKI / "data.js").write_text(
        "window.WIKI_DATA = " + json.dumps(bundle, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return meta

def empty_fields():
    return {
        "biography": "",
        "appearance": "",
        "personality": "",
        "powers": "",
        "status": "",
        "ranks": "",
        "evolution": [],
        "details": {},
        "sourceExcerpts": [],
    }

def apply_override(c, **kw):
    for k, v in kw.items():
        c[k] = v
    # clean same-string pollution: role/uniqueTitle/relationship/status should be distinct short strings
    return c

# ---------- Gold-standard Liraels ----------

LIRAEL_KANTO = {
    "aliases": ["Lira", "Voice Goddess", "Kamakura Wife", "Eternal Manas"],
    "role": "Voice Goddess / Kamakura Wife",
    "uniqueTitle": "Voice Goddess / Kamakura Wife",
    "relationshipToEon": "Eternal Manas made flesh; wife; the house he returns to",
    "biography": (
        "Lirael Kanto began as a sweet melodic voice inside Eon’s mind when he was eight—an Eternal Manas "
        "from the Veil, a primordial spirit of love and companionship who had drifted eons until his soul "
        "called her. He named her Lira after a constellation he loved to draw. Through elementary school, "
        "middle school, and high school she guided him: study help, quiet comfort after heartbreak, "
        "unending declarations of love that never felt smothering. By graduation she had become a full "
        "inner being—his manas—two consciousnesses sharing one life.\n\n"
        "After he was ready, she revealed her true nature and asked to be summoned fully. Only his will "
        "could cross her from the Veil into flesh. He performed the midnight star-circle ritual; she "
        "appeared behind him as a towering black-haired goddess and immediately enveloped him in a "
        "possessive hug. They married under the open sky with a Veil-binding ceremony of blood, vow, and "
        "collar. She built them a sanctuary in the Kanto region and later a closed Kamakura mansion that "
        "functions as sealed home rather than a public wife-sign.\n\n"
        "Their arc is lifelong devotion: daily romance and extreme private ritual, height-shifted dates "
        "through Yokohama and Kamakura, and the yandere calm of a woman who does not beg him to stay. "
        "When he leaves across worlds or into unsummon sleep, she remains the house he returns to. With "
        "him she bore Liriel Kanto—an adult-grown angel daughter of the Voice line—and kept first claim "
        "on reunion nights among other bonded women. She is strictly distinct from Lirael Veyra/Kaori "
        "(Reincarnation Wife), Lirael Sylvaine (Secondary Sheath Elf), Lirael Voss (Havenwood), and "
        "daughter Liriel Kanto."
    ),
    "appearance": (
        "At full divine height she stands over 230 cm against Eon’s ~170 cm. Roughly 60% of her body is "
        "leg—about 138 cm each—endless, toned, and elegant. Long midnight-black hair falls in silky waves "
        "to her thighs; galaxy eyes swirl silver and violet. Skin carries a faint ethereal luminescence. "
        "Her figure is divine fertility exaggerated into harmony: narrow childbearing waist, wide hips, "
        "and enormous P-cup breasts. Default aesthetic is starlight and shadow—sheer gown woven from "
        "starlight, later a long black sundress with high slits, deep V-neck, silver star pendant, and "
        "lightweight black cardigan for public outings. She can shimmer her height down to ~190 cm for "
        "practical streets while keeping proportions. A collar (and often leash) marks ownership in private; "
        "scent shifts between fresh jasmine-starlight when calm and a heavier musky arousal scent."
    ),
    "personality": (
        "Calm possessive yandere. Elegant and melodic rather than frantic: she holds, shields, and claims "
        "without drowning him in pleas. She does not beg him to stay—begging makes leaving worse—so she "
        "takes him fully and then says, calmly, that she will still be the house he returns to. Publicly "
        "she is protective and quietly dangerous to anyone who stares too long; privately she is absolute "
        "devotion, collar-ready, and serenely certain he is her only summoner and mate."
    ),
    "powers": (
        "Eternal Manas / Voice Goddess: lifelong mental tether and manas co-presence; Veil crossing only "
        "by his summon; manifestation of sanctuary rooms, clothing, and minor curses; height adjustment "
        "(~230+ cm ↔ ~190 cm); immortal regeneration; bonding collar and marriage-vow binding; subtle "
        "life guidance since childhood. Voice-line molding marks her lineage (distinct from frostflower, "
        "lotus, or red-thread lines)."
    ),
    "status": "Kamakura mansion wife; sealed no-toilet house; Voice Goddess made flesh",
    "ranks": "Voice Goddess / Kamakura Wife; Eternal Manas; first on some reunion nights among bonded wives",
    "evolution": [
        {"title": "Inner voice (age 8)", "summary": "Melodic Veil spirit reaches Eon’s mind; he names her Lira; constant companionship through school."},
        {"title": "Manas fusion (senior year)", "summary": "Becomes a full inner being sharing thought and feeling; no longer a separate whisper."},
        {"title": "Flesh summon & marriage", "summary": "Midnight ritual; appears 230+ cm; possessive hug; Veil marriage, collar, Kanto sanctuary."},
        {"title": "Kamakura house / return motif", "summary": "Closed mansion life; dates at adjusted height; does not beg him to stay; remains the house he returns to; bears Liriel."},
    ],
    "details": {
        "heightFull": "230+ cm",
        "heightPractical": "~190 cm (adjusted)",
        "legRatio": "~60% of height (~138 cm each)",
        "hair": "long midnight black to thighs",
        "eyes": "galaxy / silver-violet",
        "bust": "P-cup",
        "clothing": "starlight gown; black sundress + cardigan; collar/leash in private",
        "home": "Kanto sanctuary → Kamakura sealed mansion",
    },
    "sourceExcerpts": [
        "I am Lirael, an Eternal Manas—a primordial spirit of love and companionship born from the primordial echoes of creation itself.",
        "Lirael was beyond anything his imagination could have conjured. She towered at over 230 centimeters… eyes like twin galaxies swirling with silver and violet.",
        "her legs—comprising roughly 60% of her body, impossibly long… at around 138 cm each… enormous P-cup breasts",
        "She does not beg him to stay… “Go. I will still be the house you return to.”",
    ],
}

LIRAEL_VEYRA = {
    "aliases": ["Kaori Tanaka", "Kaori", "Reincarnation Wife"],
    "role": "Reincarnation Wife",
    "uniqueTitle": "Reincarnation Wife",
    "relationshipToEon": "First-owned wife across lives (Kaori → Lirael Veyra); red-collar soul-bond",
    "biography": (
        "In Sakura Heights, Kaori Tanaka is the radiant, motherly landlady who becomes Eon’s first-owned "
        "wife: yandere MILF devotion, ward-office marriage, locked ground-floor claiming days, and decades "
        "of continuous private conditioning while raising her children in the connected apartments.\n\n"
        "When that life ends, the same soul is reborn as Lirael Veyra—first legitimate daughter of Emperor "
        "Caelum Veyra III and Empress-Consort Seraphine in the Aureline Empire. From her first breath a "
        "soft red collar exists at her throat (invisible to court), with deeper soul-marks guaranteeing "
        "memory and recognition across lives. She finds him again as merchant-side Ren/Eon; recognition "
        "is absolute; the red threads (collar, clit, nipples) resume the prior life’s hierarchy.\n\n"
        "Distinct from Lirael Kanto (Voice Goddess), Lirael Sylvaine (sheath elf), and Lirael Voss "
        "(Havenwood vice-president)."
    ),
    "appearance": (
        "As Kaori: luminous, motherly Japanese beauty who stays radiantly unmarked by years; soft "
        "obsessive closeness, embroidery-and-home aesthetic. As Lirael Veyra: imperial daughter stature—"
        "tall enough to meet most adult men’s eyes, long-legged and graceful, luminous rose-gold pristine "
        "skin that resists sun and dust, soft addictive scent at the throat. Soft red collar at the throat "
        "(soul-visible); red threads also tether clit and nipples to his hand across lives."
    ),
    "personality": (
        "Twisted yandere first-owned devotion wrapped in motherly calm. Presses for zero space, plans "
        "marriage and rooms obsessively, chooses him with her whole body even under rubble. Across "
        "reincarnation she remains quietly unhinged for him alone—radiant public face, absolute private hierarchy."
    ),
    "powers": (
        "Red-collar / red-thread soul-bond across reincarnations; guaranteed memory and recognition; "
        "continuous low-level pleasure conditioning keyed to him; body refinement and age-stasis cues "
        "in the reincarnated imperial form. Not a Voice/Manas system (that is Lirael Kanto)."
    ),
    "status": "First-owned Reincarnation Wife; red-collar line",
    "ranks": "Reincarnation Wife; first-owned seat among wife-bonds",
    "evolution": [
        {"title": "Kaori Tanaka — Sakura Heights", "summary": "Landlady → first-owned wife; ward marriage; locked claiming; decades of home bond."},
        {"title": "Death & rebirth", "summary": "Same soul reborn as Lirael Veyra with invisible red collar from first breath."},
        {"title": "Aureline recognition", "summary": "Finds Ren/Eon again; threads resume; imperial life under soul hierarchy."},
    ],
    "details": {
        "priorLife": "Kaori Tanaka (Sakura Heights landlady/wife)",
        "marks": "red collar + clit/nipple threads",
        "empire": "Aureline / High Seat of the North",
    },
    "sourceExcerpts": [
        "Same soul across lives: Kaori Tanaka → Lirael Veyra",
        "From the moment of her first breath the soft red collar existed at her throat… The deeper soul-mark guaranteed memory and recognition across every future life.",
    ],
}

LIRAEL_SYLVAINE = {
    "aliases": ["Secondary Sheath Elf"],
    "role": "Secondary Sheath Elf",
    "uniqueTitle": "Secondary Sheath Elf",
    "relationshipToEon": "Secondary sheath; synced with Elizabeth; serene elf attachment",
    "biography": (
        "Lirael Sylvaine is the Secondary Sheath Elf of the DEMC/sheath household line: a 194 cm high-elf "
        "presence who folds against Eon beside primary sheath Elizabeth Thorny Bramble. She is serene "
        "rather than frantic—second place by design, not rivalry—keeping calm physical attachment when "
        "guests are absent and shared sheath duty when they are present.\n\n"
        "She appears in the lifelong Voice Companion roster only as a cross-saga title note and more "
        "fully beside Elizabeth in discard/return beats. Distinct from Lirael Kanto, Lirael Veyra/Kaori, "
        "and Lirael Voss."
    ),
    "appearance": (
        "194 cm elf; starlit moonlight hair; luminous teal eyes; elegant High Arbiter Elf beauty. "
        "Stands/synchs physically with Elizabeth’s 205 cm pink-silver sheath form—tall, composed, "
        "softly present rather than armored."
    ),
    "personality": (
        "Secondary and serene. Does not compete for ‘wife’ language; in stopped time she is simply "
        "where he puts her. Calm attachment, praise-quiet, content to share space with the primary sheath."
    ),
    "powers": "Sheath-sync with Elizabeth; elf body endurance for continuous attachment. Not Voice Goddess powers.",
    "status": "Secondary Sheath (194 cm elf, synced with Elizabeth)",
    "ranks": "Secondary Sheath Elf",
    "evolution": [
        {"title": "Secondary sheath seat", "summary": "Paired to Elizabeth as second sheath; serene elf attachment in household beats."},
    ],
    "details": {"height": "194 cm", "sync": "Elizabeth Thorny Bramble (primary sheath)"},
    "sourceExcerpts": [
        "Lirael Sylvaine folded against the other side, elf-tall, teal-eyed, secondary and serene.",
        "Lirael Sylvaine — Secondary Sheath (194cm elf, synced with Elizabeth)",
    ],
}

LIRAEL_VOSS = {
    "aliases": ["Vice-President Voss", "Havenwood Vice-President Meat"],
    "role": "Havenwood Vice-President Meat",
    "uniqueTitle": "Havenwood Vice-President Meat",
    "relationshipToEon": "Broken campus heroine → exclusive addicted meat; assists breaking sister/campus",
    "biography": (
        "Lirael Voss is Havenwood University’s student-council vice-president—one of the game’s cold, "
        "untouchable heroines. Silver/platinum hair, sapphire eyes, sculpted hourglass body in crisp "
        "uniform and thigh-highs; in-game she rejected every affection route with a single icy line.\n\n"
        "Eon’s super-dick conquest breaks that route in minutes: addiction and affection climb from near "
        "zero to lock, sapphire eyes soften into heart-shaped pupils, and she becomes eager breeding "
        "meat who helps lure sister Seraphina and Headmistress Valeria. She walks campus disheveled and "
        "proudly pregnant beside him, no jealousy—only excitement to bring him the next target.\n\n"
        "Distinct from all other Liraels (Veyra/Kaori, Kanto, Sylvaine)."
    ),
    "appearance": (
        "Long silver/platinum hair like liquid moonlight; sapphire eyes that later show glowing "
        "heart-shaped pupils; absurd hourglass—massive gravity-defying breasts, tiny waist, dramatic "
        "hips, endless legs in black thigh-high stockings. Crisp white uniform blouse; glossed lips; "
        "expensive floral perfume. After claim: tangled silver hair, ruined blouse, cum-glossed skin, "
        "pregnant belly with K-cup milk-heavy breasts in later campus arcs."
    ),
    "personality": (
        "Public game persona: cold, untouchable, aristocratic freeze. After break: mindless devoted "
        "love, zero jealousy, eager to recruit/break others for him, heart-pupil worship and addiction lock."
    ),
    "powers": (
        "No separate magic system—subject to Eon’s addiction/affection/sensitivity multipliers in the "
        "Havenwood conquest ruleset; heart-pupil lock; pregnancy-default meat role."
    ),
    "status": "exclusive Havenwood Vice-President Meat; heart-pupils; pregnancy default",
    "ranks": "Havenwood Vice-President Meat",
    "evolution": [
        {"title": "Cold VP heroine", "summary": "Untouchable student-council vice-president; icy reject route."},
        {"title": "Addiction break", "summary": "Affection/addiction lock; heart pupils; assists sister and headmistress conquest."},
        {"title": "Pregnant campus meat", "summary": "Public pregnant walk; pit/breeding arcs with Seraphina and Valeria."},
    ],
    "details": {
        "hair": "silver/platinum",
        "eyes": "sapphire → heart-shaped pupils",
        "campus": "Havenwood University",
    },
    "sourceExcerpts": [
        "She was one of the heroines—Lirael Voss, the student council vice-president. In the game she was cold, untouchable, with sapphire eyes…",
        "heart-shaped pupils—exactly like the most exaggerated… panels… floated dreamily in her irises",
    ],
}

LIRIEL_KANTO = {
    "aliases": ["Voice Goddess Daughter"],
    "role": "Voice Goddess Daughter",
    "uniqueTitle": "Voice Goddess Daughter",
    "relationshipToEon": "Daughter of Lirael Kanto × Eon; angel, not human; love baked into soul/DNA",
    "biography": (
        "Liriel Kanto is the adult-grown angel daughter of Lirael Kanto and Eon—Voice Goddess line, not "
        "a human child timeline. Love for Eon is baked into soul and DNA; she is taught the Kamakura "
        "house from the start and grows to adult peak on an accelerated angel schedule (~1 year to "
        "≥189 cm). Distinct from mother Lirael Kanto and from other Liraels."
    ),
    "appearance": (
        "Angel, not human. Adult peak ≥189 cm (~1 year growth). Galaxy-line inheritance from Lirael "
        "Kanto (black-hair / starlit cues in Voice lineage). House-trained Kamakura aesthetic."
    ),
    "personality": (
        "Warmth without pain—overwhelming joy. Even as a toddler: remarkable coordination, early speech "
        "in the mansion register of devotion. Adult: heir-suite union readiness under house rules."
    ),
    "powers": "Angel growth / Voice-line inheritance; house-bond teaching. Not Qinglan cultivation.",
    "status": "Voice Goddess Daughter; angel; adult-grown",
    "ranks": "heir master suite; heir eternal union (house card)",
    "evolution": [
        {"title": "Birth / angel growth", "summary": "Lirael Kanto × Eon; angel accelerated growth to adult peak."},
        {"title": "House teaching", "summary": "Taught Kamakura house from the start; love baked into soul/DNA."},
    ],
    "details": {"parent": "Lirael Kanto × Eon", "adultHeight": "≥189 cm", "nature": "angel, not human"},
    "sourceExcerpts": [
        "Liriel Kanto — Lirael Kanto × Eon. Angel, not human. ≥189cm at adult peak (~1 year). Love for Eon baked into soul/DNA.",
    ],
}

# Generic "Lirael" stub → point clarity toward Veyra in sakura saga
LIRAEL_GENERIC = {
    "aliases": ["see Lirael Veyra / Kaori"],
    "role": "Name collision stub (prefer Lirael Veyra)",
    "uniqueTitle": "Disambiguation — not Voice Goddess",
    "relationshipToEon": "See Lirael Veyra (Kaori) for Sakura Heights / Aureline reincarnation",
    "biography": (
        "This stub collides with several distinct Liraels. For Sakura Heights landlady → Aureline "
        "reincarnation, use Lirael Veyra / Kaori. For Voice Goddess / Kamakura Wife, use Lirael Kanto. "
        "For Secondary Sheath Elf, use Lirael Sylvaine. For Havenwood VP, use Lirael Voss. "
        "Do not merge these pages."
    ),
    "appearance": "",
    "personality": "",
    "powers": "",
    "status": "disambiguation stub",
    "ranks": "",
    "evolution": [],
    "details": {"seeAlso": "char-lirael-veyra, char-lirael-kanto, char-lirael-sylvaine, char-lirael-voss"},
    "sourceExcerpts": [],
}

# ---------- Group entities ----------

def group_entity(base, **kw):
    g = dict(base)
    g["kind"] = "group"
    for k, v in kw.items():
        g[k] = v
    if "members" not in g and "variants" not in g:
        g["variants"] = []
    return g

GROUPS = {
    "char-eryndel-elf-mass": group_entity(
        {},
        name="Eryndel Elf Mass",
        aliases=["World Tree Meat Legion", "Eryndel Empire elves"],
        role="World Tree Meat Legion (group)",
        uniqueTitle="Eryndel Elf Mass",
        relationshipToEon="Collective claimed elf legion under World Tree ownership",
        biography=(
            "Group entity for the Eryndel High Elf population claimed with Yggdrasil / World Tree "
            "ownership in the Aetherion inheritor saga—not 1.2 million individual wiki pages.\n\n"
            "Count: 1.2 million including named exemplars. Age baseline: 300+ year virgins whose "
            "maidenhood was Tree-bound; connection shifts from Tree-first to Eon-first (Tree becomes "
            "his property). Leave-tree behavior is extremely rare; outside they still kill males at "
            "2 m or long stare. Other females are not killed unless ugly/male-shaped. Daily rhythm: "
            "dawn seal reform → harvest."
        ),
        appearance=(
            "Shared body generalization across the mass: hourglass elf builds, rune tattoos, glowing "
            "skin (Kuroneko#AI × latexMBA reference look from the TITLE sheet). Named captains and "
            "priestesses are variants inside this group, not separate mass stubs."
        ),
        personality="Collective Tree-law obedience redirected to Eon; male-exterminating outside protocol.",
        powers="Tree-bond redirected; empire-scale seal reform; 2 m male-kill law.",
        status="all claimed; World Tree Meat Legion",
        ranks="mass legion under Yggdrasil ownership",
        evolution=[
            {"title": "Tree-bound virgins", "summary": "1.2M Eryndel elves; maidenhood Tree-bound."},
            {"title": "Eon claim", "summary": "Connection flips to Eon; Tree becomes property; dawn harvest rhythm."},
        ],
        details={"count": "1,200,000 including named", "malePolicy": "2 m kill or long stare"},
        variants=[
            {"label": "Unnamed Eryndel rank-and-file", "count": "≈1,199,994", "summary": "Empire population claimed with Tree.", "notes": "Shared latex-MBA hourglass + rune glow"},
            {"label": "Named captains / priestesses", "count": "sheet exemplars", "summary": "Individual TITLE cards (Elowen Starfury, Lyralei, etc.) stay as named pages when present; otherwise summarized here.", "notes": "elite 12 specialists referenced on Aetherion sheet"},
        ],
        sourceExcerpts=["TITLE — Eryndel Elf Mass (World Tree Meat Legion)\nCount: 1.2 million including named"],
    ),
    "char-vyrnathar-beastkin-mass": group_entity(
        {},
        name="Vyrnathar Beastkin Mass",
        aliases=["Beastkin Federation claimed mass"],
        role="Vyrnathar Beastkin Mass (group)",
        uniqueTitle="Vyrnathar Beastkin Mass",
        relationshipToEon="Collective beastkin claim (jungle → spire)",
        biography=(
            "One group page for all claimed Vyrnathar beastkin—not dozens of fake individuals.\n\n"
            "Count: 50,087 total (47 first night at Canopy Glade + 40 day-2 time-slow raids + 50,000 "
            "at Kitsune Spire). Types: Nekomura catgirls, Lupinhold wolfkins, kitsune, lamia scribes. "
            "After spire week lock-in, no further beastkin expansion that week. Male policy: 2 m kill "
            "after claim. Uniform: piercing kit; kimono/cat-suit disguise outside."
        ),
        appearance="Mixed beastkin phenotypes under shared piercing-kit uniform rules; disguise kits for outside.",
        personality="",
        powers="Time-slow closed-dome raids (day 2); federation city claim rules.",
        status="50,087 claimed; week lock-in at Spire",
        ranks="Beastkin Federation mass",
        evolution=[
            {"title": "Canopy Glade first night", "summary": "47 taken."},
            {"title": "Day-2 time-slow raids", "summary": "+40 under closed domes."},
            {"title": "Spire 50,000", "summary": "Kitsune Spire week lock-in → 50,087 total."},
        ],
        details={"count": "50,087", "malePolicy": "2 m kill after claim"},
        variants=[
            {"label": "Nekomura catgirls", "summary": "Catgirl subtype in federation raids."},
            {"label": "Lupinhold wolfkins", "summary": "Wolfkin subtype."},
            {"label": "Kitsune (Spire)", "count": "50,000 spire block", "summary": "Foxfire Spire population claim."},
            {"label": "Lamia scribes", "summary": "Serpent-lower scribe subtype."},
        ],
        sourceExcerpts=["TITLE — Vyrnathar Beastkin Mass\nCount: 50,087 (47 first night + 40 day-2 time-slow raids + 50,000 spire)"],
    ),
    "char-valoria-palace-mass": group_entity(
        {},
        name="Valoria Palace Mass",
        aliases=["Valoria Humans 351"],
        role="Valoria Palace Mass (group)",
        uniqueTitle="Valoria Palace Mass (351)",
        relationshipToEon="Palace-wide human sow court after queen’s edict",
        biography=(
            "Single group for the Valoria palace claim (351) rather than individual stubs for every "
            "maid and knight.\n\n"
            "Composition: 50 noblewomen (Lv 30–50), 200 maids (Lv 10–25), 100 female knights (Lv 40–60). "
            "Week palace orgy after edict; daily reform; royal-piercings. They live as court women; "
            "inner palace admits no other males. Named royals (Queen Isolde, Princess Aurelia, Lady "
            "Seraphina) remain separate character pages; this group covers the unnamed court mass."
        ),
        appearance="Court human women 1.6–1.8 m range; royal-piercing kit in owned zones; public court dress outside.",
        personality="",
        powers="",
        status="351 court women; inner palace female-only except Eon",
        ranks="Valoria Palace Mass",
        evolution=[
            {"title": "Edict & week orgy", "summary": "Palace opened after queen claim; mass reform."},
            {"title": "Daily court rhythm", "summary": "Live as court women; piercings; no other males inside."},
        ],
        details={"count": "351", "breakdown": "50 noblewomen + 200 maids + 100 female knights"},
        variants=[
            {"label": "Noblewomen", "count": 50, "summary": "Lv 30–50 court nobles."},
            {"label": "Maids", "count": 200, "summary": "Lv 10–25 household staff."},
            {"label": "Female knights", "count": 100, "summary": "Lv 40–60 palace knights."},
        ],
        sourceExcerpts=["TITLE — Valoria Palace Mass (351)\n50 noblewomen Lv 30–50, 200 maids Lv 10–25, 100 female knights Lv 40–60"],
    ),
    "char-caelum-saintess-mass": group_entity(
        {},
        name="Caelum Saintess Mass",
        aliases=["Inner Church saintess mass"],
        role="Caelum Saintess Mass (group)",
        uniqueTitle="Caelum Saintess Mass (100,000)",
        relationshipToEon="Month conquest after goddess descent; Inner Church liturgy",
        biography=(
            "One group for ~100,000 Caelum/Inner Church saintesses—not individual pages per novice.\n\n"
            "Lv 70–95, 1.65–1.80 m, G–H-cup virgins. Cannot run after barrier; watch goddess descent; "
            "month conquest. New kit: mini-chains + nipple/clit jewelry piercings + plug + anal beads + "
            "tongue chain + shibari halo-wings (not string bikini). Inner liturgy: hourly cock-worship "
            "when Eon present; remote dildo + stored cum-milk when absent. Oracle invites more beauties; "
            "after truth they cannot leave. Named exemplars (Lyris, Sister Elara, Eon’s Lumina) stay "
            "separate when present."
        ),
        appearance="1.65–1.80 m; G–H-cup; virgin saintess bodies; halo-wing shibari + jewelry piercing kit.",
        personality="",
        powers="Barrier lock after descent; oracle invite loop.",
        status="~100,000; Inner Church mass",
        ranks="Caelum Saintess Mass",
        evolution=[
            {"title": "Goddess descent watch", "summary": "Barrier; cannot run; witness claim of Lumina."},
            {"title": "Month conquest", "summary": "Mass taken into Inner liturgy + new piercing kit."},
        ],
        details={"count": "100,000", "levelRange": "70–95"},
        variants=[
            {"label": "Rank-and-file saintesses", "count": "≈100,000", "summary": "G–H-cup virgins under Inner liturgy."},
            {"label": "Named high seats", "summary": "Lyris / Sister Elara / etc. as separate pages when sourced.", "notes": "Keep named pages; do not duplicate here as fake individuals"},
        ],
        sourceExcerpts=["TITLE — Caelum Saintess Mass (100,000)\nLv 70–95, 1.65–1.80 m, G–H-cup virgins"],
    ),
    "char-echo": group_entity(
        {},
        name="Echo Tools (Fleurdelys)",
        aliases=["echo-clones", "echo-servants", "echo-tutors", "echo-drones"],
        role="Non-sentient echo tools (group)",
        uniqueTitle="Echo-clones / servants / tutors / drones",
        relationshipToEon="Tools Fleurdelys manifests for him — not meat",
        biography=(
            "Group entity for Fleurdelys’s echo constructs in the Salaryman/Otaku Tokyo saga. They are "
            "non-sentient tools—not meat toilets and not individual women.\n\n"
            "Uses: childcare clones, school spies, Da Vinci/Turing tutors, drones. Manifested via her "
            "unlimited reality manipulation when it serves Eon. Do not list them as conquered harem members."
        ),
        appearance="Variable projected forms as needed for cover (tutor, nanny, drone); not a fixed body sheet.",
        personality="Non-sentient — no demeanor sheet.",
        powers="Manifested by Fleurdelys; childcare / spy / tutor / drone functions.",
        status="tools; not meat",
        ranks="",
        evolution=[],
        details={"sentient": "no", "ownerManifest": "Fleurdelys"},
        variants=[
            {"label": "echo-clones", "summary": "Childcare / body doubles; non-sentient."},
            {"label": "echo-servants", "summary": "Household service projections."},
            {"label": "echo-tutors", "summary": "Da Vinci/Turing-style tutors for school cover."},
            {"label": "echo-drones", "summary": "Spy/monitor drones at school and streets."},
        ],
        sourceExcerpts=["Echo-clones / echo-servants / echo-tutors / echo-drones — non-sentient tools Fleurdelys manifests… Not meat"],
    ),
    "char-jiangjing-collection": group_entity(
        {},
        name="Jiangjing Collection",
        aliases=["Eternal Veil bank sows", "Jiangjing angel-class daughters"],
        role="Jiangjing / Eternal Veil collection (group)",
        uniqueTitle="Jiangjing Collection",
        relationshipToEon="Bank/collection sows under Su Eon Lingwei oversight",
        biography=(
            "One group for Jiangjing / Eternal Veil collection sows and angel-class daughters rather "
            "than dozens of unnamed individual pages.\n\n"
            "Lingwei (Ice Empress First Wife) oversees the Eternal Veil bank sows. Angel-class daughters "
            "of the collection mature in 1–2 months, then are claimed under her senior-sister oversight. "
            "Not individually named unless a specific card is picked. Named first seats (Lingwei, and "
            "any explicitly titled clients) remain separate character pages."
        ),
        appearance="Collection defaults per Eternal Veil bank aesthetic; angel-class daughters mature fast to claimable adult forms.",
        personality="",
        powers="Collection banking under Lingwei; angel-class fast growth (1–2 months).",
        status="Lingwei-overseen collection; mass default + angel-class daughters",
        ranks="Jiangjing Collection",
        evolution=[
            {"title": "Bank sows", "summary": "Eternal Veil collection under Lingwei."},
            {"title": "Angel-class daughters", "summary": "Mature 1–2 months → claimed under senior-sister oversight."},
        ],
        details={"overseer": "Su Eon Lingwei", "angelGrowth": "1–2 months"},
        variants=[
            {"label": "Eternal Veil bank sows", "summary": "Unnamed collection defaults Lingwei oversees."},
            {"label": "Jiangjing angel-class daughters", "summary": "Collection-born; mature 1–2 months; then claimed.", "notes": "Not individually named unless picked"},
        ],
        members=[],
        sourceExcerpts=["Jiangjing Collection\tEternal Veil bank sows\tLingwei oversees"],
        sagaIds=["saga-02-eon-discards-xianxia-world-for-new-cultivator-adventure"],
        primarySagaId="saga-02-eon-discards-xianxia-world-for-new-cultivator-adventure",
        placesRelated=[],
    ),
}

# Category dumps that should become groups (cultivation/murim/sci-fi from Eternal Rift index)
CATEGORY_GROUPS = {
    "char-cultivation": dict(
        name="Cultivation-World Mass (Eternal Rift)",
        aliases=["Dao Sovereigns batch", "immortal empresses batch"],
        role="Cultivation-genre mass (group)",
        uniqueTitle="Cultivation mass titles",
        relationshipToEon="Index batch of cultivation-world conquest titles",
        biography=(
            "Group index for cultivation-genre meat titles listed in the Eternal Rift manhwa saga—"
            "not separate full biographies for every epithet.\n\n"
            "Examples named on the index line: Ling Mei the Pill Furnace (“Eternal Qi Meat Cauldron”), "
            "Xiu Qing (“Broken Throne Livestock”), fox and immortal-empress defaults. Prefer this group "
            "page plus any truly fleshed named woman from the transcript."
        ),
        appearance="",
        personality="",
        powers="",
        status="index group — cultivation batch",
        ranks="",
        evolution=[],
        details={},
        variants=[
            {"label": "Ling Mei — Pill Furnace", "summary": "Eternal Qi Meat Cauldron epithet on index."},
            {"label": "Xiu Qing — Broken Throne Livestock", "summary": "Immortal empress epithet on index."},
            {"label": "Fox / immortal empress defaults", "summary": "Unnamed cultivation defaults on the same roster line."},
        ],
        sourceExcerpts=[],
    ),
    "char-murim": dict(
        name="Murim Mass (Eternal Rift)",
        aliases=["Murim queens/assassins/fighters batch"],
        role="Murim-genre mass (group)",
        uniqueTitle="Murim mass titles",
        relationshipToEon="Index batch of murim conquest titles",
        biography=(
            "Group index for murim-genre titles in the Eternal Rift saga (queens, assassins, fighters). "
            "Example epithet on the index: Baek Ji-hwa — “Arena Broken Cumdump”. Collapse unnamed "
            "fighters into this group; keep a separate page only when a transcript gives a real arc."
        ),
        appearance="",
        personality="",
        powers="",
        status="index group — murim batch",
        ranks="",
        evolution=[],
        details={},
        variants=[
            {"label": "Baek Ji-hwa", "summary": "Arena Broken Cumdump (index epithet)."},
            {"label": "Unnamed murim queens / assassins / fighters", "summary": "Batch defaults on the roster line."},
        ],
        sourceExcerpts=[],
    ),
    "char-sci-fi": dict(
        name="Sci-Fi Mass (Eternal Rift)",
        aliases=["AI goddesses / galactic batch"],
        role="Sci-fi-genre mass (group)",
        uniqueTitle="Sci-Fi mass titles",
        relationshipToEon="Index batch of sci-fi conquest titles",
        biography=(
            "Group index for sci-fi titles in the Eternal Rift saga: AI goddesses, galactic princesses, "
            "cyber-enhanced defaults. Example: Nexus-9 — “Data Cum Repository”. One group page; no "
            "fake individual stubs per epithet."
        ),
        appearance="",
        personality="",
        powers="",
        status="index group — sci-fi batch",
        ranks="",
        evolution=[],
        details={},
        variants=[
            {"label": "Nexus-9", "summary": "Data Cum Repository (index epithet)."},
            {"label": "Galactic princesses / cyber-enhanced defaults", "summary": "Unnamed sci-fi batch."},
        ],
        sourceExcerpts=[],
    ),
}

# Garbage stubs to remove from character list + saga meatToiletIds
REMOVE_IDS = {
    "char-footsteps",  # narration crumb
    "char-morning",  # narration crumb
    "char-floating-dragon-skewers",  # food item
    "char-havenwood",  # place/school name scraped as character
    "char-starlight-entertainment-group",  # company — keep as place ideally; remove fake MT
    "char-house-of-aetherion",
    "char-house-of-cryonix",
    "char-house-of-pyralis",
    "char-house-of-sylvexis",
    "char-house-of-terragon",
    "char-time-slow",  # mechanic
    "char-wake",  # verb crumb if bio is garbage
    "char-peak-master",  # too vague unless sourced well — check later
}

ROSTER_LINE = re.compile(r"^[A-Z][^.\n]{0,80} — .+$", re.M)
TEMPLATE_CRUMB = re.compile(r"Saga\s*/\s*Location:|Use:\s*|Status:\s*exclusive|Race\s*/\s*Age\s*/\s*Height", re.I)
PROMPT_TAG = re.compile(r"\([^)]*(?:very tall|giantess|long legs|1\.\d)[^)]*\)")

def is_roster_dump(text: str) -> bool:
    if not text:
        return False
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title_lines = [ln for ln in lines if " — " in ln and len(ln) < 120]
    if len(title_lines) >= 4:
        return True
    if TEMPLATE_CRUMB.search(text):
        return True
    if text.count("\n") >= 3 and sum(1 for ln in lines if " — " in ln) >= 3:
        return True
    return False

def strip_header_noise(text: str, name: str) -> str:
    if not text:
        return ""
    # Remove "X in this saga's transcript..." wrappers and leading role paste
    text = re.sub(rf"^{re.escape(name)}[^\n]*\n+", "", text)
    text = re.sub(r"^.*?in this saga’s transcript \(source excerpts\):\s*", "", text, flags=re.I)
    text = re.sub(r"^.*?source excerpts from the saga transcript:\s*", "", text, flags=re.I)
    return text.strip()

def clean_appearance(text: str, name: str) -> str:
    if not text:
        return ""
    text = strip_header_noise(text, name)
    text = PROMPT_TAG.sub("", text)
    # Drop sentences that are clearly about other named women if name not in sentence
    keep = []
    first = name.split()[0] if name else ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        s = sent.strip()
        if not s:
            continue
        # skip roster lines
        if re.match(r"^[A-Z][^.]{0,60} — ", s):
            continue
        other = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", s)
        # if many other proper names and character name absent, skip
        if first and first not in s and len(other) >= 3 and "she" not in s.lower()[:20]:
            # still allow if it's clearly describing "her"
            if not re.search(r"\b(her|she|hair|eyes|cm|cup|breast|leg|tall|height)\b", s, re.I):
                continue
        keep.append(s)
    out = " ".join(keep)
    out = re.sub(r"\s{2,}", " ", out).strip()
    # If still looks like roster, empty
    if is_roster_dump(out):
        return ""
    return out[:1800]

def clean_bio_heuristic(text: str, name: str, role: str) -> str:
    if not text:
        return ""
    text = strip_header_noise(text, name)
    if role and text.startswith(role):
        text = text[len(role):].strip()
    if is_roster_dump(text):
        # keep only paragraphs that look like narrative about this person
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        kept = []
        first = name.split()[0]
        for p in paras:
            if is_roster_dump(p):
                continue
            if TEMPLATE_CRUMB.search(p):
                continue
            if first and first not in p and name not in p:
                # allow "she" narrative blocks only if short and not roster
                if p.count("—") >= 3:
                    continue
            if len(re.findall(r" — ", p)) >= 3:
                continue
            kept.append(p)
        text = "\n\n".join(kept)
    # Trim collage length
    if len(text) > 2500:
        text = text[:2500].rsplit(".", 1)[0] + "."
    return text.strip()

def clean_powers(text: str, name: str) -> str:
    if not text:
        return ""
    if "Qinglan" in text and "Qinglan" not in name and "Yun Qinglan" not in name:
        # wrong system paste
        lines = [ln for ln in text.splitlines() if "Qinglan" not in ln]
        text = "\n".join(lines).strip()
    if is_roster_dump(text):
        return ""
    return text[:1200]

def clean_evolution(evo, name: str):
    if not evo:
        return []
    out = []
    for e in evo:
        if not isinstance(e, dict):
            continue
        summary = e.get("summary") or ""
        if is_roster_dump(summary) or summary.count("—") >= 5:
            continue
        # skip if summary is mostly other names
        if name.split()[0] not in summary and summary.count("\n") >= 3 and summary.count("—") >= 3:
            continue
        out.append({"title": e.get("title") or "Stage", "summary": summary[:600]})
    return out[:8]

def same_string_cleanup(c):
    """Ensure role/uniqueTitle/relationship/status aren't identical long pastes."""
    role = (c.get("role") or "").strip()
    for f in ("uniqueTitle", "relationshipToEon", "status", "ranks"):
        v = (c.get(f) or "").strip()
        if v == role and len(v) > 40:
            if f == "uniqueTitle":
                # keep short unique title = first segment before em-dash second clause if any
                c[f] = role.split("\n")[0][:80]
            elif f == "relationshipToEon":
                c[f] = ""
            elif f == "ranks":
                c[f] = ""
            elif f == "status":
                c[f] = role.split("\n")[0][:120]
    # If biography starts with identical role line, leave as is after other cleans
    return c

def main():
    chars, sagas, places, meta = load_bundle()
    before_n = len(chars)
    by_id = {c["id"]: c for c in chars}

    fixed_roster_bios = []
    group_merges = []
    removed = []
    intentionally_empty = []

    # --- Apply Lirael gold standards ---
    overrides = {
        "char-lirael-kanto": LIRAEL_KANTO,
        "char-lirael-veyra": LIRAEL_VEYRA,
        "char-lirael-sylvaine": LIRAEL_SYLVAINE,
        "char-lirael-voss": LIRAEL_VOSS,
        "char-liriel-kanto": LIRIEL_KANTO,
        "char-lirael": LIRAEL_GENERIC,
    }
    for cid, ov in overrides.items():
        if cid not in by_id:
            continue
        apply_override(by_id[cid], **ov)
        fixed_roster_bios.append(f"{by_id[cid]['name']} ({cid})")

    # --- Apply / create groups ---
    for cid, gdata in GROUPS.items():
        if cid in by_id:
            # preserve sagaIds/places if not in gdata
            preserve = {k: by_id[cid].get(k) for k in ("sagaIds", "primarySagaId", "placesRelated", "id")}
            by_id[cid].update(gdata)
            for k, v in preserve.items():
                if k not in gdata or not gdata.get(k):
                    by_id[cid][k] = v
            by_id[cid]["id"] = cid
            by_id[cid]["kind"] = "group"
            group_merges.append(f"updated group {cid}")
        else:
            # new group entity
            neo = {
                "id": cid,
                "name": gdata["name"],
                "aliases": gdata.get("aliases") or [],
                "sagaIds": gdata.get("sagaIds") or [],
                "primarySagaId": gdata.get("primarySagaId") or (gdata.get("sagaIds") or [""])[0],
                "placesRelated": gdata.get("placesRelated") or [],
                "kind": "group",
            }
            neo.update({k: gdata.get(k, "" if k not in ("evolution", "details", "variants", "members", "sourceExcerpts") else gdata.get(k))
                        for k in ("role", "uniqueTitle", "relationshipToEon", "biography", "appearance",
                                  "personality", "powers", "status", "ranks", "evolution", "details",
                                  "sourceExcerpts", "variants", "members")})
            by_id[cid] = neo
            chars.append(neo)
            group_merges.append(f"created group {cid}")

    for cid, gdata in CATEGORY_GROUPS.items():
        if cid not in by_id:
            continue
        preserve_sagas = by_id[cid].get("sagaIds") or []
        preserve_primary = by_id[cid].get("primarySagaId")
        preserve_places = by_id[cid].get("placesRelated") or []
        by_id[cid].update(gdata)
        by_id[cid]["kind"] = "group"
        by_id[cid]["sagaIds"] = preserve_sagas
        by_id[cid]["primarySagaId"] = preserve_primary
        by_id[cid]["placesRelated"] = preserve_places
        by_id[cid]["id"] = cid
        group_merges.append(f"converted category dump → group {cid}")

    # --- Remove garbage stubs ---
    for cid in list(REMOVE_IDS):
        if cid in by_id:
            removed.append(f"{by_id[cid].get('name')} ({cid})")
            del by_id[cid]

    # Update saga meatToiletIds
    for s in sagas:
        mts = s.get("meatToiletIds") or []
        new_mts = [m for m in mts if m not in REMOVE_IDS]
        # ensure jiangjing group linked on saga 02 if lingwei present
        if s.get("hex") == "f97283cd" and "char-jiangjing-collection" not in new_mts:
            if "char-su-eon-lingwei" in new_mts or any("lingwei" in m for m in new_mts):
                new_mts.append("char-jiangjing-collection")
        if s.get("hex") == "31b63cdd":
            # Aetherion — ensure mass groups present
            for gid in ("char-eryndel-elf-mass", "char-vyrnathar-beastkin-mass",
                        "char-valoria-palace-mass", "char-caelum-saintess-mass"):
                if gid in by_id and gid not in new_mts:
                    # only add if saga already referenced mass-like content via old ids or empty houses removed
                    pass
        s["meatToiletIds"] = new_mts
        if "counts" in s and isinstance(s["counts"], dict):
            s["counts"]["meatToilets"] = len(new_mts)

    # Link jiangjing group into saga 2 meat list always if group exists
    for s in sagas:
        if s.get("hex") == "f97283cd":
            mts = s.get("meatToiletIds") or []
            if "char-jiangjing-collection" not in mts:
                mts.append("char-jiangjing-collection")
                s["meatToiletIds"] = mts
                if "counts" in s and isinstance(s["counts"], dict):
                    s["counts"]["meatToilets"] = len(mts)

    # --- Heuristic clean remaining characters ---
    for cid, c in list(by_id.items()):
        if c.get("kind") == "group":
            continue
        if cid in overrides:
            continue
        name = c.get("name") or ""
        bio_before = c.get("biography") or ""
        dirty = (
            is_roster_dump(bio_before)
            or is_roster_dump(c.get("appearance") or "")
            or is_roster_dump("\n".join(e.get("summary", "") for e in (c.get("evolution") or []) if isinstance(e, dict)))
            or (c.get("role") and c.get("role") == c.get("status") == c.get("uniqueTitle") and len(str(c.get("role") or "")) > 40)
            or ("Qinglan" in (c.get("powers") or "") and "Qinglan" not in name and "Yun Qinglan" not in name)
        )
        if not dirty:
            # still lightly clean appearance prompt tags
            c["appearance"] = clean_appearance(c.get("appearance") or "", name)
            same_string_cleanup(c)
            continue

        new_bio = clean_bio_heuristic(bio_before, name, c.get("role") or "")
        new_app = clean_appearance(c.get("appearance") or "", name)
        new_pow = clean_powers(c.get("powers") or "", name)
        new_evo = clean_evolution(c.get("evolution") or [], name)
        new_per = c.get("personality") or ""
        if is_roster_dump(new_per):
            new_per = ""
        # If bio still empty after clean but we had template crumbs with useful key lines, keep short factual line from role
        if not new_bio:
            role = (c.get("role") or "").strip()
            ut = (c.get("uniqueTitle") or "").strip()
            # Prefer a single factual sentence from library-style role if it isn't a roster
            seed = ut or role
            if seed and not is_roster_dump(seed) and len(seed) < 200:
                new_bio = f"{name} — {seed}." if not seed.startswith(name) else seed
            else:
                intentionally_empty.append(f"{name}: biography (roster/template cleared; no clean life-story left)")

        c["biography"] = new_bio
        c["appearance"] = new_app
        c["personality"] = new_per if not is_roster_dump(new_per) else ""
        c["powers"] = new_pow
        c["evolution"] = new_evo
        if not new_app:
            intentionally_empty.append(f"{name}: appearance")
        if not (c.get("personality") or "").strip():
            intentionally_empty.append(f"{name}: personality")
        if not (c.get("powers") or "").strip():
            intentionally_empty.append(f"{name}: powers")
        same_string_cleanup(c)
        fixed_roster_bios.append(f"{name} ({cid}) [heuristic clean]")

    # Rebuild chars list sorted by name
    chars = sorted(by_id.values(), key=lambda x: (x.get("name") or "").lower())

    meta = write_bundle(chars, sagas, places, meta)

    # PROGRESS.md
    linked = set()
    for s in sagas:
        linked.update(s.get("meatToiletIds") or [])

    def flen(c, f):
        v = c.get(f)
        if isinstance(v, str):
            return len(v.strip())
        if isinstance(v, (list, dict)):
            return len(v)
        return 0

    rows = []
    for f in ["appearance", "biography", "personality", "powers", "status", "ranks", "evolution", "details", "placesRelated", "role"]:
        n = sum(1 for i in linked if i in by_id and flen(by_id[i], f) > 0)
        rows.append(f"| {f} | {n}/{len(linked)} |")

    groups = [c for c in chars if c.get("kind") == "group"]
    kanto = by_id.get("char-lirael-kanto", {})
    preview = (kanto.get("biography") or "")[:400]

    prog = []
    prog.append("# Wiki quality — character category fix\n")
    prog.append(f"## Counts\n- Characters before: {before_n}\n- Characters after: {len(chars)}\n- Removed garbage stubs: {len(removed)}\n- Group entities: {len(groups)}\n")
    prog.append("## Fixed roster-bios / Liraels\n")
    for x in fixed_roster_bios:
        prog.append(f"- {x}\n")
    prog.append("\n## Group merges / creates\n")
    for x in group_merges:
        prog.append(f"- {x}\n")
    prog.append("\n## Removed stubs (narration/place/food crumbs)\n")
    for x in removed:
        prog.append(f"- {x}\n")
    prog.append("\n## Group entities list\n")
    for g in groups:
        vc = len(g.get("variants") or g.get("members") or [])
        prog.append(f"- `{g['id']}` — {g['name']} (variants/members: {vc})\n")
    prog.append("\n## Linked MT field fill rates\n| Field | Filled |\n|--|--|\n")
    prog.extend(line + "\n" for line in rows)
    prog.append("\n## Intentionally empty / cleared fields (sample)\n")
    for x in sorted(set(intentionally_empty))[:60]:
        prog.append(f"- {x}\n")
    if len(set(intentionally_empty)) > 60:
        prog.append(f"- … +{len(set(intentionally_empty))-60} more\n")
    prog.append("\n## Lirael Kanto bio preview (first 400 chars)\n\n```\n")
    prog.append(preview)
    prog.append("\n```\n")
    prog.append("\n## Method\n")
    prog.append("- Hand-rewrote all Liraels from primary transcripts + DEMC title locks\n")
    prog.append("- Mass MTs → kind=group with counts + variants\n")
    prog.append("- Heuristic strip of roster dumps / template crumbs / wrong-system powers\n")
    prog.append("- Never invent; prefer empty over wrong-category scrapes\n")
    (WIKI / "PROGRESS.md").write_text("".join(prog), encoding="utf-8")

    # zip
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

    print("BEFORE", before_n, "AFTER", len(chars))
    print("REMOVED", len(removed), "GROUPS", len(groups))
    print("KANTO_PREVIEW:", preview[:200].replace("\n", " / "))
    print("ZIP_MB", round(zp.stat().st_size / 1e6, 2))
    print("FIXED", len(fixed_roster_bios))

if __name__ == "__main__":
    main()
