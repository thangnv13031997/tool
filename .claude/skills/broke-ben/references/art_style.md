# Broke Ben: art style and drawing scripts

All scripts are in `scripts/` and need Python 3 with Pillow (and ffmpeg for the demo video).
Fonts are bundled in `assets/fonts` (Anton, Oswald: SIL OFL; Special Elite: Apache 2.0, all commercial use OK).
Scripts write into the current working directory.

| Script | What it does |
|---|---|
| `flatkit.py` | Low-level drawing: `Pen` (2x supersampled, layers, gradients, glow, rounded rects, text), v1 stick figure, `caption()` pill. |
| `charkit.py` | Mascots as RGBA sprites (same file as `app/engine/charkit.py` in the repo): `ben(...)`, `piggy(...)`. |
| `make_branding.py` | Channel art with Ben → `branding/` (avatar, banner, watermark, device previews). |
| `demo_animation.py` | 9-second animation test → `demo/demo_9s.mp4` + `demo/frames.jpg`. |
| `money_math.py` | The numbers (see script_guide.md). |

## Style rules (v2, current)
- Smooth Bezier shapes, two-tone cel shading (light from the top-right, shadow bottom-left), sticker outline
  `#2B2233`, big eyes with two white highlights, soft blush.
- Palette: ink `#1D212D`, money green `#2E8B57` (hoodie `#3FA36B`), cream `#F6F1E6`, gold `#FFC43D`,
  loss red `#D64545`, piggy pink `#FFA8BA`.
- Backgrounds: cream ledger-paper grid, flat floor band; scenes stay light and friendly.
- Fonts: Anton (titles, thumbnails, big numbers), Oswald (captions, labels), Special Elite (receipts, documents).

## Mascots (decided)
- **Ben** (the channel avatar): young adult, about 3.5 heads tall, round friendly face, light blush, **messy modern
  hair**, green hoodie, **work ID badge on a blue lanyard** (no backpack), navy jeans, white sneakers.
  `ben(pose, mood, scale, blink, talk)`.
  - Poses (25): idle, wave, point, hold_head, cross_arms, phone, read, count_money, shrug, think, celebrate,
    thumbs_up, facepalm, explain, sad, sit_desk, empty_pockets, credit_card, shopping_bags, coffee, calculator,
    beg, throw_money, hug_piggy, present.
  - Moods (9): smile, shock, sad, worried, angry, smug, money_eyes, tired, cry. `blink=True` closes the eyes;
    `talk=False` is the closed-mouth frame for lip flaps. Reference sheet: `docs/ben_poses.png` in the broke-ben repo.
- **Piggy Ben** (sidekick): pink piggy bank, coin slot, crack with a band-aid. Moods smile, shock.

## Ben's Notebook (hand-drawn segments)
`app/sketch.py` in the repo: show type `sketch` (kinds line, bars, pie, flow). On a `notebook` background the scene
opens with a page flip; a hand holding a yellow pencil (whiteboard style, green hoodie sleeve) draws the chart stroke by stroke (axes, data, fills), then
writes labels in the Patrick Hand font (SIL OFL, supports Vietnamese). Lines get a small deterministic wobble.
Sounds `page` and `scribble` are added automatically. Use for ~20% of scenes, mainly to explain concepts.

## Animation approach (cut-out, not skeletal)
Sprites are drawn once and cached; motion comes from: breathing (±1.2% squash/stretch), blinks (4 frames),
lip flaps (swap talk frame every 4 frames while speaking), pose swaps on beat changes, hops, bounce
entrances, impact squash (damped cosine), pop-in cards (ease-out-back), counting numbers (ease-in-out).

## Adding a new pose or mood
1. In `charkit.py`, add an entry to `ARMS` (shoulder, elbow, hand, hand style for each arm) and to
   `BEN_POSES`; shoulders are at (222, 378) / (378, 378) on the 600x940 canvas. New moods go in `_face`.
2. Draw shapes with `sp.part(base, shade, outline)` so shading is clipped and the sticker outline matches.
3. Never draw semi-transparent colours straight onto the sprite: draw them on `p.layer()` and `p.paste()`
   (direct RGBA writes punch holes; that was the grey-blush bug).
4. Render a test strip (all poses side by side) and look at it before using the pose in a video.

## Layout rules learned the hard way
- Keep a caption band at the bottom (y ≥ 930 on 1080p); nothing else goes there.
- Labels never sit on top of lines or other labels; put chart labels at the line ends (direct labels).
- Banner: everything that matters inside the centred 1546x423 safe area; check `preview_banner_devices.jpg`.
- Avatar: must read at 36 px; check `preview_avatar_sizes.png` on light and dark.
- After rendering anything, open the image and look for collisions before handing it over.
