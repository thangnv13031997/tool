# Broke Ben: art style and drawing scripts

All scripts are in `scripts/` and need Python 3 with Pillow (and ffmpeg for the demo video).
Fonts are bundled in `assets/fonts` (Anton, Oswald: SIL OFL; Special Elite: Apache 2.0, all commercial use OK).
Scripts write into the current working directory.

| Script | What it does |
|---|---|
| `flatkit.py` | Low-level drawing: `Pen` (2x supersampled, layers, gradients, glow, rounded rects, text), v1 stick figure, `caption()` pill. |
| `charkit.py` | v2 mascots as RGBA sprites: `ben(pose, mood, scale, blink, talk)`, `piggy(mood, scale, blink, talk)`. |
| `make_branding.py` | v1 branding (stick-figure Ben) + shared helpers: `coin()`, `banner_preview()`, `avatar_preview()`, safe-area constants. |
| `make_branding_v2.py` | v2 branding for both options → `branding/option_A_ben`, `branding/option_B_piggy`, `branding/COMPARE_v2.jpg`. |
| `demo_animation.py` | 9-second animation test → `demo/demo_9s.mp4` + `demo/frames.jpg`. |
| `money_math.py` | The numbers (see script_guide.md). |

## Style rules (v2, current)
- Smooth Bezier shapes, two-tone cel shading (light from the top-right, shadow bottom-left), sticker outline
  `#2B2233`, big eyes with two white highlights, soft blush.
- Palette: ink `#1D212D`, money green `#2E8B57` (hoodie `#3FA36B`), cream `#F6F1E6`, gold `#FFC43D`,
  loss red `#D64545`, piggy pink `#FFA8BA`.
- Backgrounds: cream ledger-paper grid, flat floor band; scenes stay light and friendly.
- Fonts: Anton (titles, thumbnails, big numbers), Oswald (captions, labels), Special Elite (receipts, documents).

## Mascots
- **Ben** (option A): chibi, spiky-swoop brown hair with a tuft, green hoodie with strings and pocket,
  navy pants, white sneakers. Poses: `idle`, `wave`, `point`. Moods: `smile`, `shock`. `blink=True` closes
  the eyes, `talk=False` gives the closed-mouth frame for lip flaps.
- **Piggy Ben** (option B): pink piggy bank, coin slot on top, crack with a band-aid on the right side.
  Moods `smile`, `shock`; same blink/talk flags.

## Animation approach (cut-out, not skeletal)
Sprites are drawn once and cached; motion comes from: breathing (±1.2% squash/stretch), blinks (4 frames),
lip flaps (swap talk frame every 4 frames while speaking), pose swaps on beat changes, hops, bounce
entrances, impact squash (damped cosine), pop-in cards (ease-out-back), counting numbers (ease-in-out).

## Adding a new pose or mood
1. In `charkit.py`, add the arm path to `front`/`arms` (three points: shoulder, elbow, hand) or a new
   branch in the face section. Keep shoulders at (222, 452) / (378, 452) and the 600x780 canvas.
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
