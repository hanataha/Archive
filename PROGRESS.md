# Current totals
- Sagas: 54 · Characters: 157 · Places: 413 (`data/meta.json`)

## Saga 54 added (2026-10-19)
- `saga-54-eon-reborn-as-major-family-s-first-son-in-murim-world`: “Eon Reborn as Major Family’s First Son in Murim World” (79ff3a26, 27 beats, marker `New`). Slow-burn Murim betrothal romance; Eon is reborn as first son of the Baek clan and betrothed at 6 to Han Seo-yeon.
- Screened turn by turn before adding: sexual content only in beats 25–27 (wedding kiss, wedding night, morning after). Both are 18 and married, it is consensual and initiated by her, and neither is a student or a family member. Beats 1–24 (ages 0–18) are non-sexual. Families appear only in non-sexual roles.
- Characters (+1): `char-han-seo-yeon` (Childhood Fiancée → Wife).
- Places (+6): Azure Dragon Pavilion (Mount Cheongryong), Han clan river holdings, White Crane Rest Stop, eastern-slope pavilion, eastern ferry-house storage pavilion, cracked marker stone (upper ferry path).
- Added `transcripts/79ff3a26.md`, `extracts/79ff3a26.{md,json}`, `extracts/_index.json` entry; `data.js` regenerated from `data/*.json`.

## Saga 53 added (2026-10-11) — profile-only reframe
- `saga-53-eon-s-tokyo-lodging-aoi-rin` — “Eon’s Tokyo Lodging (Aoi & Rin)”, marker `Profiles`, `profileOnly: true`: character profiles only, reimagined setting; no transcript, no URL, no beats from any chat.
- Setting: Eon (18, third-year high schooler) rents the spare upstairs room in Aoi Sakuraba’s Setagaya house. Aoi = landlady; Rin = her daughter. No family or legal tie to Eon. Only names, looks, ages, jobs and personalities were kept.
- Characters (+2): `char-aoi-sakuraba` (café owner, forties, exact age not given), `char-rin-sakuraba` (22, designer in Minato). Linked via new saga field `characterIds`.
- Places (+2): `place-cafe-aoi`, `place-sakuraba-house-setagaya`.
- `app.js`: `profileOnly` sagas show a `Profiles` chip, a “Characters” section (from `characterIds`), and hide the transcript/chat buttons; `/full` shows a no-transcript notice. `styles.css`: `.chip.pf`.

## DeepSeek sagas 47–52 added (2026-10-09)
- Source: hanataha’s older DeepSeek history (56 Eon chats screened; 6 included, 50 excluded for minors, family/incest or non-consensual cores). Marker `DeepSeek`, `hex`/file = `ds-NN` (DeepSeek list index).
- #47 `ds-01` イオンの社畜日常と恋の芽 (N3 Japanese office slice-of-life) · #48 `ds-02` Eon’s Dual Life: Corporate & Otaku (early version of Grok #20/#42) · #49 `ds-05` Eon Transforms with Ayaka’s Divine Power · #50 `ds-06` Eon and Ayaka’s Fantasy World Adventure · #51 `ds-41` Li Xue’s Devotion… (Saori of Neo-Arcadia) · #52 `ds-44` Devoted Submissive Character… (Lumina the Radiant Blade)
- Characters (+5): `char-rina`, `char-mayumi`, `char-ayaka-shiroyama`, `char-saori-luminelle`, `char-lumina-the-radiant-blade`; extended `char-fleurdelys` (saga 48, game-character cameo only)
- Places (+24 new; `place-shiroyama-estate` shared by 49/50)
- Added `transcripts/ds-*.md`, `extracts/ds-*.{md,json}`, `extracts/_index.json` entries; `app.js` shows a DeepSeek chip, “Open on chat.deepseek.com” button and DeepSeek role headings

## Saga 46 added (2026-10-06)
- `saga-46-eon-tokyo-otaku-s-perfect-solo-life` — “Eon: Tokyo Otaku’s Perfect Solo Life” (80bebf21, 4 beats, wholesome slice-of-life rom-com, marker `New` = added after the A/B index)
- Characters (+3): `char-hamazaki-risa` (Gal Classmate / Close Friend), `char-yumi` (Cosplayer Club Friend), `char-takashi` (Loud Club Friend)
- Places (+9 new, 1 existing linked): Eon’s Nakano 1K apartment, university (literature dept.), anime & game club room, Akihabara pop-up store, Shinjuku screening theater, Risa’s karaoke box, Odaiba anime convention, Risa’s dormitory, Eternal Realms (MMORPG); existing `place-tokyo-tower` linked
- Added `transcripts/80bebf21.md`, `extracts/80bebf21.{md,json}`, `extracts/_index.json` entry
- `characters.json` now also carries the `portrait`/`portraitThumb` fields that previously existed only in `data.js`; `data.js` regenerated from `data/*.json` (compact JSON, `ensure_ascii=False`, trailing newline)

# Wiki quality — character category fix

## Counts
- Characters before: 158
- Characters after: 146
- Removed garbage stubs: 13 (Footsteps, Morning, Floating Dragon Skewers, Havenwood, Starlight Entertainment Group, five Houses, Time-Slow, Wake, Peak Master)
- Group entities: 9
- Roster-dump bios remaining: 0

## Fixed Liraels (gold / category-correct)
- Lirael Kanto (`char-lirael-kanto`) — Voice Goddess / Kamakura Wife from e8858667 + DEMC title locks
- Lirael Veyra (`char-lirael-veyra`) — Reincarnation Wife / Kaori from 818c7984
- Kaori (`char-kaori`) — prior-life page aligned to Veyra
- Lirael Sylvaine (`char-lirael-sylvaine`) — Secondary Sheath Elf (DEMC + f97283cd)
- Lirael Voss (`char-lirael-voss`) — Havenwood VP from 99fc4c06
- Liriel Kanto (`char-liriel-kanto`) — Voice Goddess Daughter (not mother)
- Lirael (`char-lirael`) — disambiguation stub only

## Group entities
- `char-caelum-saintess-mass` — Caelum Saintess Mass (variants: 2; count: 100,000)
- `char-cultivation` — Cultivation-World Mass (Eternal Rift) (variants: 3)
- `char-echo` — Echo Tools (Fleurdelys) (variants: 4)
- `char-eryndel-elf-mass` — Eryndel Elf Mass (variants: 2; count: 1,200,000 including named)
- `char-jiangjing-collection` — Jiangjing Collection (variants: 2)
- `char-murim` — Murim Mass (Eternal Rift) (variants: 2)
- `char-sci-fi` — Sci-Fi Mass (Eternal Rift) (variants: 2)
- `char-valoria-palace-mass` — Valoria Palace Mass (variants: 3; count: 351)
- `char-vyrnathar-beastkin-mass` — Vyrnathar Beastkin Mass (variants: 4; count: 50,087)

## Other passes
- Heuristic strip of roster dumps / template crumbs / wrong-system Qinglan pastes across ~80 characters
- Aetherion saga meatToiletIds restored to named TITLE sheets + 4 mass groups (was only houses/footsteps crumbs)
- Aetherion named sheets rewritten from gazetteer TITLE blocks when bios were template crumbs
- `app.js` + `styles.css`: Group chip, Group section with numbers + variants/members
- Empty fields left empty when source lacks category (never invented)

## Linked MT field fill rates (n=146)
| Field | Filled |
|--|--|
| appearance | 133/146 |
| biography | 144/146 |
| personality | 125/146 |
| powers | 132/146 |
| status | 144/146 |
| ranks | 62/146 |
| evolution | 117/146 |
| details | 69/146 |
| placesRelated | 142/146 |
| role | 144/146 |

## Intentionally empty / cleared (examples)
- Disambiguation stub `char-lirael`: appearance/personality/powers empty
- Characters whose only prior “bio” was a cross-saga roster list: roster cleared; short factual seed kept only when role line was clean
- Wrong Qinglan powers removed from non-Qinglan pages (e.g. Liriel Kanto, Elizabeth Thorny Bramble, Luminara Dreamweaver)

## Lirael Kanto bio preview (first 400 chars)

```
Lirael Kanto began as a sweet melodic voice inside Eon’s mind when he was eight—an Eternal Manas from the Veil, a primordial spirit of love and companionship who had drifted eons until his soul called her. He named her Lira after a constellation he loved to draw. Through elementary school, middle school, and high school she guided him: study help, quiet comfort after heartbreak, unending declarati
```

## Deliverables
- `wiki/data/characters.json` + rebuilt `wiki/data.js`
- `wiki/app.js` group UI
- `wiki/PROGRESS.md` (this file)
- `wiki_fandom.zip` ready for parent Desktop copy
