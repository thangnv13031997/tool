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

## Script deliverable format (until Money Studio's JSON format exists)
Return a scene table the tool can later convert:

| # | Purpose | Narration (TTS-ready) | On screen | Ben / Piggy | Duration |
|---|---|---|---|---|---|
| 1 | hook | "Ben makes three thousand dollars a month." | money card $3,000 pops in | Ben idle, talking | 4 s |

Purposes: hook, promise, setup, open_loop, beat, rehook, payoff, action, outro.
On-screen elements available today: money card (count up/down), line chart (one or two series, labelled ends),
receipt (prints line by line), phone balance, coins, captions. Ben poses: idle, wave, point; moods: smile,
shock. Piggy Ben moods: smile, shock. Anything else must be listed as "needs new asset" in the table.
