# Telegram Image Enhancement & Animation Bot

*Powered by FLUX Kontext Pro/Max + Kling v1.6*

## Quick‑Start (local)

```bash
git clone <repo>
cd <repo>
cp .env.example .env  # add your keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests -q        # live API sanity checks
python src/bot.py      # run bot
```

### Features

* Text‑guided edits (style, objects, text, backgrounds, faces)
* Free/Premium tiers (Telegram Payments + Stripe provider)
* Optional animation via Kling
* Advisor auto‑suggests optimal actions 