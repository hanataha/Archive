# Current totals
- Sagas: 46 · Characters: 149 · Places: 381 (`data/meta.json`)

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
