## Telegram Payments Integration

1. **BotFather → Payments → Stripe** → copy **LIVE provider token**
2. Add to `.env`:

```
PROVIDER_TOKEN=123:LIVE:...   # keep private
```

3. In `src/payments.py` we call `sendInvoice` with real amounts.
4. `pre_checkout_query` is auto‑approved; `successful_payment` sets `is_premium` flag in Redis.
5. **Recurring invoices**: not yet; webhook stub ready (see TODO).
6. **Stars tips**: button `"⭐️ Tip"` with `input_invoice` = 0‑amount invoice once Stars API stable. 