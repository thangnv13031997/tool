# Broke Ben: script, title and thumbnail guide

## Retention structure (10–14 min long-form; 8+ min so mid-roll ads are allowed)

| Part | Time | What it must do |
|---|---|---|
| Hook | 0:00–0:20 | Open on the pain or the shocking number, matching the title/thumbnail promise. First line in the first second. "Ben makes three thousand dollars a month. Thirty-three are left." |
| Promise | by 0:30 | What the viewer will know by the end: "By the end, you'll know exactly where it goes, and the one fix that matters." |
| Story setup | ~1 min | Ben in an ordinary situation. A little humour. |
| Open loop | before 1:15 | A question answered only near the end ("And the biggest leak isn't on this list."). |
| Body | middle | 3–6 beats. Each beat = one idea + one picture (chart, receipt, phone, card) + Ben reacting. |
| Re-hooks | every 2–3 min | A surprise number, a twist in Ben's story, or "but here's the part nobody tells you". |
| Payoff | last 2 min | Close the open loop. Give one concrete action the viewer can take this week. |
| Outro | ≤ 20 s | Ben's next mistake as a tease for the next video. No long goodbye. |

Pacing: one scene = 3–7 seconds of narration. Change the picture constantly (Ben pose, chart builds, number counts, receipt prints).

## Writing style
- Narrator speaks to the viewer ("you"), Ben is the example ("Ben does this. You probably do too.").
- Short sentences (under 15 words, never over 22). Easy for Kokoro TTS: no rare words, numbers written
  as words in narration ("three thousand dollars", "seven percent"), digits only on screen.
- Concrete over abstract: "$312 on food delivery" beats "too much on eating out".
- One idea per scene. If a sentence needs a footnote, it needs its own scene.
- Never "true story". Ben is a character; say "Ben" not "my friend".
- Light humour, never mocking the viewer. Ben is lovable, not stupid.

## Numbers (accuracy is the brand)
- Compute every figure with `scripts/money_math.py` (invest, loan, card, inflation, budget) and keep the
  printed "Assumptions" line. Put it under "The numbers:" in the video description.
- Use round, typical US figures and say they are examples ("a typical car loan", "about seven percent a year
  on average"). Do not present averages as guarantees.
- When a fact depends on a real statistic (median rent, average credit card APR), mark it in the script as
  `[SOURCE NEEDED: ...]` unless you can cite it; the creator verifies before recording.

## Titles (35–60 characters)
Formulas that work in this niche:
- "Why You're Always {pain} (Even When {excuse})"
- "{Thing} Is Designed to Keep You Broke"
- "{A} vs {B}: The Math Nobody Shows You"
- "What If You {small habit} for {N} Years?"
- "Ben {did X}. Here's What Happened to His Money"
- "{Concept} Explained in {N} Minutes"
Give 4 options, rank them, recommend one. Curiosity without clickbait: the video must deliver the title.

## Thumbnails (3 variants for YouTube Test & Compare)
- One big emotion (Ben or Piggy Ben shocked/worried), one money object (phone balance, receipt, card,
  chart arrow), 2–4 words max. Dark text on the cream background, or white text with a dark outline.
- Colour code: green = money in, red = money out, gold = highlight. Never swap them.
- The thumbnail text should NOT repeat the title; it adds the emotional half
  (title "Why You're Always Broke", thumbnail "$0.00").
- Layout variants: A face + number, B object close-up (receipt/phone), C before/after split.

## Description template
```
{1–2 sentence summary, first line contains the main keyword}

Chapters:
0:00 {...}

📌 The numbers: {Assumptions line(s) from money_math.py}

This video is for educational and entertainment purposes only and is not financial advice.

#personalfinance #moneytips #brokeben
```
Also give: 10–15 tags, a pinned comment that asks a question ("What's YOUR biggest money leak?"), and the
next-video tease.

## Script deliverable format (Money Studio JSON)
Return ONE JSON object in the Money Studio format (full spec: `docs/PROMPT_FOR_CLAUDE.md` in the broke-ben repo).
Every line carries `text` (English narration, numbers as words) and `vi` (natural Vietnamese subtitle).
Minimal shape:
```json
{"title": "...", "mascot": "ben", "narrator": {"voice": "am_michael", "speed": 1.0}, "music": "light",
 "youtube": {"title_options": [], "title_vi": "", "description": "", "description_vi": "", "numbers": "", "tags": [],
             "pinned_comment": ""},
 "thumbnail": {"variants": [{"layout": "face_number", "text": "ALWAYS *BROKE*?", "number": "$0.00", "who": "ben", "mood": "shock"}]},
 "shorts": {"scenes": [1, 6], "hook_text": "...", "end_text": "Full video on Broke Ben"},
 "scenes": [{"purpose": "hook", "chapter": "...", "bg": "grid",
             "chars": [{"who": "ben", "pose": "idle", "mood": "smile"}],
             "show": {"type": "money_card", "label": "Monthly pay", "value": 3000, "to": 33},
             "lines": [{"text": "Ben makes three thousand dollars a month.", "vi": "Ben kiếm 3.000 đô mỗi tháng."}]}]}
```
Backgrounds: grid, room, desk, city, notebook, plain. Show types: money_card, big_text, invest_chart, chart, receipt,
phone, compare, list, coin_drop, sketch (Ben's Notebook hand drawing; kind line | bars | pie | flow; use with
bg notebook: a tilted notebook page on the desk; consecutive notebook scenes turn the page, ~20% of scenes;
money_card color red = price tag, green = banknote). Ben poses (25): idle, wave, point, hold_head, cross_arms, phone, read,
count_money, shrug, think, celebrate, thumbs_up, facepalm, explain, sad, sit_desk, empty_pockets, credit_card,
shopping_bags, coffee, calculator, beg, throw_money, hug_piggy, present. Ben moods (9): smile, shock, sad, worried,
angry, smug, money_eyes, tired, cry. Piggy moods: smile, shock.
SFX: pop, coin, ding, whoosh, tick, thud, cash, page, scribble. Anything else = "needs new asset" (note it for the
tool upgrade).
