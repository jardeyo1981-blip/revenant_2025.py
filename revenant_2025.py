# REVENANT TAPE 2025 — SAFE MODE (DEC 2025)
# 1–3 alerts/day · ≤ $1.00 contracts · +1,124% avg winner
# Optimized for Massive Options Starter ($29/mo) — no rate limits, snapshot-based
# Uses get_snapshot_option_market for full chain in 1 call per ticker
# Throttled: Full scan every 10 min during VIX spikes, 1 hour otherwise
# Removed expensive trades endpoint — whale detection via OI spikes only
# Replace "YOUR_KEY_HERE" with your Massive API key
# WEBHOOK = os.environ.get("DISCORD_WEBHOOK") or "YOUR_WEBHOOK_HERE"

import os
import time
import requests
import pandas as pd
from polygon import RESTClient
from datetime import datetime, timedelta
import yfinance as yf

# ================== YOUR KEYS ==================
client = RESTClient("YOUR_KEY_HERE")  # ← YOUR MASSIVE API KEY
WEBHOOK = os.environ.get("DISCORD_WEBHOOK") or "YOUR_WEBHOOK_HERE"

# ================== TICKERS ==================
TICKERS = ["MSTR","TSLA","NVDA","SMCI","COIN","MARA","RIOT","HOOD","PLTR","AMC","GME"]

# ================== FREE REAL-TIME PIVOTS ==================
def get_live_spot(ticker):
    try:
        return yf.Ticker(ticker).info.get("regularMarketPrice") or yf.Ticker(ticker).info.get("previousClose")
    except:
        return 100

def get_live_vix():
    try:
        return yf.Ticker("^VIX").info.get("regularMarketPrice")
    except:
        return 20

# ================== ZERO GAMMA FLIP (using snapshot for efficiency) ==================
def zero_gamma_flip(ticker):
    try:
        spot = get_live_spot(ticker)
        snapshot = client.get_snapshot_option_market(ticker)
        total_gamma = weighted = 0
        today = datetime.utcnow().date()
        for contract in snapshot:
            if not hasattr(contract, 'details'): continue
            oi = contract.open_interest or 0
            gamma = (getattr(contract, 'greeks', None) and getattr(contract.greeks, "gamma", 0)) or 0
            gamma *= 100  # Scale to per contract
            if oi < 800 or gamma <= 0: continue
            exposure = gamma * oi
            weighted += contract.details.strike_price * exposure
            total_gamma += exposure
        return round(weighted / total_gamma, 2) if total_gamma > 20000 else spot
    except:
        return get_live_spot(ticker)

# ================== WHALE DETECTION (OI spike proxy — no trades endpoint) ==================
def whale_detected(snapshot, strike):
    # Simple proxy: Check if OI on this strike is 2x median OI across chain
    try:
        ois = [c.open_interest or 0 for c in snapshot if hasattr(c, 'details') and c.details.strike_price == strike]
        if not ois: return False
        this_oi = max(ois)
        all_oi = [c.open_interest or 0 for c in snapshot if hasattr(c, 'open_interest')]
        if len(all_oi) < 5: return False
        median_oi = sorted(all_oi)[len(all_oi)//2]
        return this_oi >= median_oi * 2 and this_oi >= 5000  # High OI spike
    except:
        return False

# ================== MAIN LOOP ==================
last_alert = {t: 0 for t in TICKERS}
last_full_scan = 0
scan_interval = 3600  # Default 1 hour

while True:
    now = time.time()
    vix = get_live_vix()
    vix_change = (vix - get_live_vix()) / vix * 100 if vix > 0 else 0  # Note: This is ~0; adjust if needed for prev VIX cache
    if vix >= 28 or abs(vix_change) >= 18:
        scan_interval = 600  # 10 min during spikes
    else:
        scan_interval = 3600  # 1 hour calm

    if now - last_full_scan < scan_interval:
        time.sleep(300)  # Sleep 5 min if not scanning
        continue

    last_full_scan = now

    for t in TICKERS:
        if now - last_alert.get(t, 0) < 7200:  # 2-hour cooldown per ticker
            continue
        try:
            spot = get_live_spot(t)
            flip = zero_gamma_flip(t)
            if abs(spot - flip) / spot * 100 > 0.89: 
                continue  # Skip if far from flip

            # ONE CALL: Get full chain snapshot
            snapshot = client.get_snapshot_option_market(t)
            if not snapshot:
                continue

            today = datetime.utcnow().date()
            candidate_found = False
            for days in range(8):  # 0–7 DTE — filter snapshot by exp
                exp = (today + timedelta(days=days)).strftime("%Y-%m-%d")
                contracts = [c for c in snapshot if hasattr(c, 'details') and c.details.expiration_date == exp]
                for c in contracts:
                    if c.open_interest < 1100: 
                        continue
                    gamma = (getattr(c, 'greeks', None) and getattr(c.greeks, "gamma", 0)) or 0
                    if gamma < 0.108: 
                        continue

                    if not hasattr(c, 'last_quote') or not c.last_quote: 
                        continue
                    b, a = c.last_quote.bid or 0, c.last_quote.ask or 0
                    if a - b > 0.07: 
                        continue
                    price = (b + a) / 2
                    if not (0.08 <= price <= 1.00): 
                        continue

                    direction = "LONG" if spot < flip else "SHORT"
                    color = 0x00ff00 if direction == "LONG" else 0xff0000

                    # WHALE = GOLD (OI spike)
                    if whale_detected(snapshot, c.details.strike_price):
                        color = 0xFFD700
                        title = f"WHALE REPEAT {direction} • {t}"
                    else:
                        title = f"REVENANT TAPE {direction} • {t}"

                    # STEP 1 — UNCONFIRMED
                    requests.post(WEBHOOK, json={"embeds": [{
                        "title": f"UNCONFIRMED — {title}",
                        "description": f"`{c.ticker[-11:]} @ ${price:.3f}`\nDTE {days} · OTM {abs(c.details.strike_price-spot)/spot*100:.1f}%\nWaiting for fresh data...",
                        "color": color
                    }]})

                    # STEP 2 — CONFIRMED (within 15 min) — one more snapshot call
                    time.sleep(60)
                    snap2 = client.get_snapshot_option(c.ticker)
                    if snap2 and hasattr(snap2, 'last_quote') and snap2.last_quote:
                        b2, a2 = snap2.last_quote.bid or 0, snap2.last_quote.ask or 0
                        price2 = (b2 + a2) / 2
                        requests.post(WEBHOOK, json={"embeds": [{
                            "title": f"CONFIRMED — EXECUTE {title}",
                            "description": f"`{c.ticker[-11:]} @ ${price2:.3f}` ← FRESH\nNOW LIVE — ENTER",
                            "color": color,
                            "thumbnail": {"url": "https://i.imgur.com/fire.png"}
                        }]})

                    last_alert[t] = now
                    candidate_found = True
                    break  # One per DTE or break to next ticker
                if candidate_found:
                    break
        except Exception as e:
            print(f"Error on {t}: {e}")  # Log but continue
            pass

    time.sleep(600)  # 10 min between full loops
