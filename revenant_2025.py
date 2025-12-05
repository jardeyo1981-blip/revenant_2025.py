# =====================================================
# REVENANT TAPE 2025 — FINAL JAN 2026 GOD-MODE SCRIPT
# 33 Tickers • Every Nuclear Pattern • Zero Junk
# =====================================================

import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from polygon import RESTClient
import yfinance as yf

# ================== CONFIG ==================
client = RESTClient("YOUR_MASSIVE_KEY_HERE")
WEBHOOK = os.environ.get("DISCORD_WEBHOOK") or "YOUR_DISCORD_WEBHOOK"

TICKERS = [
    "MSTR","TSLA","NVDA","SMCI","COIN","MARA","RIOT","HOOD","PLTR","AMC","GME",
    "UPST","AFRM","CVNA","RBLX","SOFI","RDDT","DJT","IONQ","ASTS","SOUN",
    "CELH","APP","RIVN","LCID","PATH","ZETA","S","BBAI","SMR","OKLO","TEM"
]

COOLDOWN = 4200
last_alert = {t: 0 for t in TICKERS}
last_scan = 0
tz_et = ZoneInfo("US/Eastern")

# ================== HELPERS ==================
def spot(t): 
    try: return yf.Ticker(t).fast_info['lastPrice']
    except: return 100

def vix(): 
    try: return yf.Ticker("^VIX").fast_info['lastPrice']
    except: return 20

def gamma_flip(t):
    try:
        s = spot(t)
        snap = client.get_snapshot_option_market(t)
        if not snap or not hasattr(snap,'results'): return s
        total = w = 0
        for c in snap.results:
            if not hasattr(c,'greeks') or not c.open_interest: continue
            g = (c.greeks.gamma or 0) * 100
            oi = c.open_interest or 0
            if oi < 800 or g <= 0: continue
            exp = g * oi
            w += c.details.strike_price * exp
            total += exp
        return round(w / total, 2) if total > 20000 else s
    except: return spot(t)

def mtf_flush(t):
    try:
        daily_low = yf.download(t, period="15d", interval="1d", progress=False)["Low"].min()
        h4_prev = yf.download(t, period="5d", interval="4h", progress=False)["Close"].iloc[-2]
        return spot(t) < daily_low * 1.006 and spot(t) > h4_prev
    except: return False

# ================== ALL NUCLEAR CANDLE PATTERNS ==================
def nuclear_candles(df, spot, flip):
    if len(df) < 20: return None
    if abs(spot - flip)/spot*100 > 1.1: return None
    c = df.iloc[-1]
    c1,c2,c3 = df.iloc[-3],df.iloc[-2],df.iloc[-1]
    r = c.High - c.Low
    if r < 0.01: return None
    body = abs(c.Close - c.Open)
    body_r = body / r
    uw = c.High - max(c.Open,c.Close)
    lw = min(c.Open,c.Close) - c.Low

    # 3 White Soldiers / 3 Black Crows
    if all(x.Close > x.Open for x in [c1,c2,c3]) and c2.Close > c1.Close and c3.Close > c2.Close:
        return {"t":"3 WHITE SOLDIERS","c":0x00FF00,"m":"MOONSHOT"}
    if all(x.Close < x.Open for x in [c1,c2,c3]) and c2.Close < c1.Close and c3.Close < c2.Close:
        return {"t":"3 BLACK CROWS","c":0xFF0000,"m":"CRASH"}

    # Marubozu
    if body_r >= 0.90:
        return {"t":"BULLISH MARUBOZU","c":0x00FFAA,"m":"CALLS"} if c.Close > c.Open else {"t":"BEARISH MARUBOZU","c":0xAA00FF,"m":"PUTS"}

    # Inside Bar Break
    mother, inside = df.iloc[-3], df.iloc[-2]
    if inside.High < mother.High and inside.Low > mother.Low:
        if c.Close > mother.High:  return {"t":"INSIDE BAR BREAKOUT","c":0xFFAA00,"m":"BREAKOUT"}
        if c.Close < mother.Low:   return {"t":"INSIDE BAR BREAKDOWN","c":0xAA00AA,"m":"BREAKDOWN"}

    # Dragonfly / Tombstone Doji
    if body_r <= 0.08:
        if lw > uw*3: return {"t":"DRAGONFLY DOJI","c":0x00FFFF,"m":"BOTTOM – CALLS"}
        if uw > lw*3: return {"t":"TOMBSTONE DOJI","c":0xFF00FF,"m":"TOP – PUTS"}

    return None

def rams_demons(t, spot, flip):
    try:
        df = yf.download(t, period="6d", interval="5m", prepost=True, progress=False)
        if len(df) < 50: return None
        c = df.iloc[-2]
        o,h,l,cl = c.Open,c.High,c.Low,c.Close
        r = h-l; body = abs(cl-o)
        uw = h - max(o,cl); lw = min(o,cl) - l
        body_pct = body/r
        vol_r = c.Volume / df.Volume.rolling(40).mean().iloc[-2]
        dist = abs(spot-flip)/spot*100

        if lw >= 3*body and body_pct <= 0.12 and uw <= r*0.08 and vol_r >= 2.2 and dist <= 1.1 and vix() >= 22:
            return {"t":"RAM'S HEAD","c":0xFFD700,"m":"CALLS"}
        if uw >= 3*body and body_pct <= 0.12 and lw <= r*0.08 and vol_r >= 2.2 and dist <= 1.1 and vix() >= 22:
            return {"t":"DEMON HORNS","c":0x8B0000,"m":"PUTS"}
        return None
    except: return None

def morning_lotto(t, spot, flip):
    n = datetime.now(tz_et)
    if not (10 <= n.hour <= 10 and n.minute <= 35): return None
    try:
        df = yf.download(t, period="1d", interval="5m", prepost=True, progress=False)
        morn = df.between_time("07:00","07:30")
        if len(morn) < 3: return None
        move = (morn.Close.iloc[-1] - morn.Open.iloc[0]) / morn.Open.iloc[0]
        if abs(move) >= 0.018 and abs(spot-flip)/spot*100 <= 1.2:
            d = "CALLS" if move > 0 else "PUTS"
            return {"t":"7AM TREND-TIME LOTTO","c":0x00FFFF,"m":f"{d} 0DTE"}
    except: pass
    return None

def moc_ramp(t, spot, flip):
    n = datetime.now(tz_et)
    if not ((n.hour == 15 and n.minute >= 30) or n.hour == 16): return None
    try:
        df = yf.download(t, period="1d", interval="1m", progress=False)
        if len(df) < 30: return None
        ramp = (spot - df.Close.iloc[-30]) / df.Close.iloc[-30]
        if abs(ramp) >= 0.013 and abs(spot-flip)/spot*100 <= 1.0:
            d = "CALLS" if ramp > 0 else "PUTS"
            return {"t":"EOD MOC RAMP","c":0xFF00FF,"m":f"{d} detonation"}
    except: pass
    return None

# ================== MAIN LOOP ==================
print("Revenant Tape 2025 — FINAL JAN 2026 SCRIPT RUNNING")
while True:
    try:
        now = time.time()
        if now - last_scan < (540 if vix() >= 22 else 1800):
            time.sleep(60); continue
        last_scan = now

        for t in TICKERS:
            if now - last_alert.get(t, 0) < COOLDOWN: continue

            spot = spot(t)
            flip = gamma_flip(t)
            dist = abs(spot - flip) / spot * 100

            df5 = yf.download(t, period="6d", interval="5m", prepost=True, progress=False)

            # 1–4. All nuclear candles (highest priority)
            for sig in [nuclear_candles(df5, spot, flip),
                        rams_demons(t, spot, flip),
                        morning_lotto(t, spot, flip),
                        moc_ramp(t, spot, flip)]:
                if sig:
                    prefix = "MTF FLUSH " if mtf_flush(t) else ""
                    requests.post(WEBHOOK, json={"embeds":[{
                        "title": f"{prefix}{sig['t']} — {t}",
                        "description": sig["m"],
                        "color": sig["c"],
                        "thumbnail": {"url": "https://i.imgur.com/fire.png"}
                    }]})
                    last_alert[t] = now
                    break
            else:
                # 5. Core Revenant
                if vix() < 22 or dist > 0.65: continue
                try:
                    pre = yf.download(t, period="1d", interval="5m", prepost=True, progress=False)
                    pre_h = pre.between_time("04:00","09:29")["High"].max()
                    pre_l = pre.between_time("04:00","09:29")["Low"].min()
                    ema5 = df5["Close"].ewm(span=5).mean().iloc[-1]
                    ema12 = df5["Close"].ewm(span=12).mean().iloc[-1]
                    if not ((spot > pre_h or spot < pre_l) and ema5 > ema12): continue
                except: continue

                prefix = "MTF FLUSH " if mtf_flush(t) else ""
                direction = "LONG" if spot < flip else "SHORT"
                color = 0x00ff00 if direction == "LONG" else 0xff0000
                requests.post(WEBHOOK, json={"embeds":[{
                    "title": f"{prefix}REVENANT {direction} — {t}",
                    "description": f"Spot {spot:.2f} • Flip {flip:.2f}",
                    "color": color,
                    "thumbnail": {"url": "https://i.imgur.com/fire.png"}
                }]})
                last_alert[t] = now

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(30)
    time.sleep(300)
