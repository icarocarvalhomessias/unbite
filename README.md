# unbite

**A small webcam watcher that tells you, out loud and in your own language, when your hand goes to your mouth.**

Nail biting is mostly automatic: it happens while you read code, wait for a build, or watch an AI write its answer. By the time you notice, the nail is gone. `unbite` notices for you. It runs quietly in the background, and the moment a fingertip reaches your mouth it shows a red banner, beeps and says something like *"Hand on your mouth. Careful!"*, in the language of your computer.

- **Private by design.** Everything runs on your machine with [MediaPipe](https://ai.google.dev/edge/mediapipe) models. No image is saved, uploaded or sent anywhere.
- **Speaks your language.** It picks up the system language and uses the voices already installed on Windows, macOS or Linux. Alert texts ship in 22 languages.
- **Knows a phone from a nail.** A phone at your ear, a cup, a fork or a toothbrush in your hand does not trigger it.
- **Light.** Runs on the CPU at 15 to 25 frames per second on an ordinary laptop webcam.

## How it works

```
webcam frame ─► face landmarks (mouth) ─┐
             └► hand landmarks (fingertips) ─► distance in "mouth widths" ─► held ≥ 0.6 s? ─► alert
                                                     │
                       only when close ─► object detector: phone, cup, food...? ─► skip
```

The distance is measured in mouth widths, so it works the same whether you sit close to the screen or lean back. The object detector, the slowest model, only runs when a fingertip is already near your mouth.

## Install

Requires Python 3.10 or newer and a webcam.

```bash
pip install git+https://github.com/<your-user>/unbite
```

Or from a clone:

```bash
git clone https://github.com/<your-user>/unbite
cd unbite
pip install .
```

The three models (about 19 MB) are downloaded on the first run, verified by SHA-256 and cached in your user folder.

## Use

```bash
unbite --preview        # first time: see what the camera sees and tune the threshold
unbite                  # normal use: no window, just the alerts
```

Press `q` in the preview window, or `Ctrl+C` in the terminal, to stop.

| Option | What it does |
|---|---|
| `--preview` | Shows the camera, the mouth, the nearest fingertip and the distance. |
| `--threshold 0.9` | Distance (in mouth widths) that counts as touching. Lower is stricter. |
| `--hold 0.6` | Seconds at the mouth before alerting, so passing gestures are ignored. |
| `--cooldown 4` | Minimum seconds between alerts. |
| `--camera N` / `--list-cameras` | Choose the camera. Default: the last one found, usually the external one. |
| `--lang pt` / `--list-languages` | Force an alert language instead of the system's. |
| `--no-voice`, `--no-sound`, `--no-banner` | Turn each kind of alert off. |
| `--no-objects` | Alert even with a phone, cup or food in your hand. |
| `--log alerts.csv` | Append the time of each alert to a CSV file, to see your patterns. Times only. |

### Tuning

Run `unbite --preview` and bring your fingers to your mouth. The line between your mouth and the nearest fingertip turns red below the threshold. If resting your chin on your hand sets it off, lower `--threshold` (try `0.7`). If it misses real bites, raise it.

## Languages

Arabic, Chinese (Simplified and Traditional), Dutch, English, French, German, Hebrew, Hindi, Indonesian, Italian, Japanese, Korean, Polish, Portuguese, Russian, Spanish, Swedish, Thai, Turkish, Ukrainian and Vietnamese.

The spoken voice comes from your operating system: SAPI voices on Windows, `say` on macOS, and `spd-say` or `espeak-ng` on Linux. If no voice for your language is installed, the default voice is used. You can add one in your system's speech settings.

Each language is one small file in [`src/unbite/locales/`](src/unbite/locales). Corrections from native speakers and new languages are very welcome: copy `en.json`, translate the two sentences, and open a pull request.

## Limitations

- The distance is measured in 2D, so a hand in front of the face (but not at the mouth) can trigger it. Tune `--threshold`.
- It only sees you while you are in front of the camera.
- Right-to-left text (Arabic, Hebrew) in the banner depends on your Tk version; the spoken alert is unaffected.
- It is a nudge, not a treatment. If nail biting hurts you, a doctor or a habit-reversal therapist can help.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"     # Windows: .venv\Scripts\pip
pytest
ruff check . && ruff format --check .
```

The code is split so that the logic can be tested without a camera:

| Module | Role |
|---|---|
| `geometry.py` | Mouth center, fingertip distance, boxes. Pure functions. |
| `tracker.py` | When to alert: hold time, cooldown, object grace period. |
| `detection.py` | MediaPipe face, hand and object models. |
| `models.py` | Pinned model downloads with checksum verification. |
| `i18n.py`, `locales/` | System language detection and alert texts. |
| `speech.py`, `banner.py` | Spoken alert and on-screen banner. |
| `app.py`, `cli.py` | Main loop and command line. |

## License

[MIT](LICENSE). The MediaPipe models are provided by Google under the Apache License 2.0.
