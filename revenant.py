# =====================================================
# REVENANT TAPE 2026 — ULTIMATE FINAL + 6AM PREP + ALL NUCLEAR PATTERNS
# THIS IS THE REAL ONE — EVERY PATTERN INCLUDED — DEC 5 2025
# =====================================================

import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from polygon import RESTClient
import yfinance as yf
import feedparser

# ================== CONFIG ==================
client         = RESTClient(os.environ["MASSIVE_API_KEY"])
WEBHOOK        = os.environ["DISCORD_WEBHOOK"]
PING_TAG       = f"<@{os.environ.get('DISCORD_USER_ID', '')}>"
PREMARKET_PING = os.environ.get("PREMARKET_PING", "true").lower() == "true"

TICKERS = ["MSTR","TSLA","NVDA","SMCI","COIN","MARA","RIOT","HOOD","PLTR","AMC","GME",
           "UPST","AFRM","CVNA","RBLX","SOFI","RDDT","DJT","IONQ","ASTS","SOUN",
           "CELH","APP","RIVN","LCID","PATH","ZETA","S","BBAI","SMR","OKLO","TEM"]

COOLDOWN = 4200
last_alert = {t: 0 for t in TICKERS}
last_scan = last_heartbeat = last_eod = last_prepmarket = 0
daily_count = 0
tz_et = ZoneInfo("US/Eastern")

# ================== HELPERS ==================
def spot(t): 
    try: return yf.Ticker(t).fast_info['lastPrice']
    except: return 100.0

def vix(): 
    try: return yf.Ticker("^VIX").fast_info['lastPrice']
    except: return 20.0

def vix1d(): 
    try: return yf.Ticker("^VIX1D").fast_info['lastPrice']
    except: return vix()

def gamma_flip(t):
    try:
        s = spot(t)
        snap = client.get_snapshot_option_market(t)
        if not snap or not hasattr(snap, 'results'): return s
        total = w = 0
        for c in snap.results:
            if not hasattr(c, 'greeks') or c.open_interest is None: continue
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
        s = spot(t)
        return s < daily_low * 1.006 and s > h4_prev
    except: return False

def best_target_strike(ticker, direction="CALL"):
    try:
        snap = client.get_snapshot_option_market(ticker)
        best = None
        best_score = 9999
        s = spot(ticker)
        for c in snap.results[:400]:
            if not hasattr(c, 'last_quote') or c.last_quote.bid is None: continue
            days = (datetime.strptime(c.details.expiration_date, "%Y-%m-%d") - datetime.now()).days
            if not (0 <= days <= 3): continue
            spread = (c.last_quote.ask or 0) - (c.last_quote.bid or 0)
            if spread > 0.15 or c.last_quote.bid < 0.07: continue
            if direction == "CALL" and c.details.strike_price <= s: continue
            if direction == "PUT"  and c.details.strike_price >= s: continue
            dist = abs(c.details.strike_price - s)
            score = dist + spread * 18
            if score < best_score:
                best_score = score
                best = f"${c.details.strike_price} ({c.details.expiration_date[5:10]} exp)"
        return best or "nearest OTM"
    except: return "nearest OTM"

def get_catalysts():
    try:
        feed = feedparser.parse("https://rss.investing.com/economic-calendar/rss/us")
        high = []
        for e in feed.entries[:12]:
            if any(k in e.title.lower() for k in ["fomc","cpi","payrolls","nfp","powell","fed","tariff","rate"]):
                high.append(e.title.strip())
        return high or ["Quiet calendar"]
    except: return ["Calendar unavailable"]

def send(title, desc="", color=0x00AAFF, ping=True):
    ticker_match = next((t for t in TICKERS if t in title), None)
    if ticker_match:
        direction = "CALL" if any(x in title + desc for x in ["CALL","LONG","BULL","MOON","RAM","LOTTO","SOLDIERS","WHITE","DRAGONFLY"]) else "PUT"
        target = best_target_strike(ticker_match, direction)
        desc = f"{desc}\n**TARGET STRIKE:** {target}" if desc else f"**TARGET STRIKE:** {target}"
    requests.post(WEBHOOK, json={
        "content": PING_TAG if ping and os.environ.get('DISCORD_USER_ID') else None,
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color,
            "thumbnail": {"url": "https://i.imgur.com/fire.png"},
            "footer": {"text": datetime.now(tz_et).strftime("%b %d %H:%M ET")}
        }]
    })

# ================== ALL NUCLEAR CANDLE PAT preferredTERNS (FULLY INCLUDED) ==================
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
        body_pct = body/r if r else 0
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

# ================== 6:00 AM PRE-MARKET PREP ==================
def send_pre_market_prep():
    global last_prepmarket
    now_et = datetime.now(tz_et)
    if now_et.weekday() >= 5: return
    if not (now_et.hour == 6 and now_et.minute < 5): return
    if time.time() - last_prepmarket < 3600*20: return
    last_prepmarket = time.time()

    movers = []; volume_leaders = []; gap_leaders = []
    for t in TICKERS:
        try:
            data = yf.download(t, period="2d", interval="5m", prepost=True, progress=False)
            if len(data) < 10: continue
            prev_close = data["Close"].iloc[-20]
            current = spot(t)
            change = (current - prev_close) / prev_close * 100
            vol_ratio = data["Volume"].iloc[-10:].sum() / max(data["Volume"].iloc[-100:-10].mean(), 1)
            flip = gamma_flip(t)
            gap = abs(current - flip) / current * 100

            movers.append((t, change, current))
            volume_leaders.append((t, vol_ratio))
            gap_leaders.append((t, gap, current, flip))
        except: continue

    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    volume_leaders.sort(key=lambda x: x[1], reverse=True)
    gap_leaders.sort(key=lambda x: x[1], reverse=True)

    desc = f"""**6:00 AM PRE-MARKET PREP — {now_et.strftime('%b %d')}**
**Top Movers** → {" • ".join(f"`{t}` {c:+.2f}%" for t,c,p in movers[:5])}
**Volume Leaders** → {" • ".join(f"`{t}` {r:.1f}x" for t,r in volume_leaders[:3])}
**Gamma Gaps** → {" • ".join(f"`{t}` {g:.2f}%" for t,g,s,f in gap_leaders[:3])}
**Catalysts** → {", ".join(get_catalysts()[:3]) or "None"}
VIX `{vix():.1f}` • VIX1D `{vix1d():.1f}`"""

    send("PRE-MARKET INTEL DROP", desc, 0xFFD700, ping=PREMARKET_PING)

# ================== MAIN LOOP ==================
print("REVENANT TAPE 2026 — FINAL NUCLEAR VERSION RUNNING")
while True:
    try:
        now = time.time()
        now_et = datetime.now(tz_et)
        vix_val = vix(); vix1d_val = vix1d()

        send_pre_market_prep()

        if now_et.hour == 16 and now_et.minute <= 10 and now - last_eod > 80000:
            send("EOD SUMMARY", f"Today: ~{daily_count} alerts\nTomorrow → {", ".join(get_catalysts()[:3])}", 0x4169E1, ping=True)
            daily_count = 0; last_eod = now

        if now - last_heartbeat > 3600:
            send("REVENANT HEARTBEAT", f"Alive • VIX {vix_val:.1f} • VIX1D {vix1d_val:.1f}", 0x00FF00, ping=False)
            last_heartbeat = now

        cats = get_catalysts()
        is_big_day = any(k in " ".join(str(c) for c in cats).lower() for k in ["fomc","cpi","nfp","powell"])
        scan_int = 150 if is_big_day else (300 if vix1d_val > 25 else (600 if vix1d_val > 20 else 1800))
        if now - last_scan < scan_int: time.sleep(60); continue
        last_scan = now

        for t in TICKERS:
            if now - last_alert.get(t, 0) < COOLDOWN: continue

            spot_price = spot(t)
            flip = gamma_flip(t)
            df5 = yf.download(t, period="6d", interval="5m", prepost=True, progress=False)

            # HIGHEST PRIORITY: ALL NUCLEAR PATTERNS
            for sig in [
                nuclear_candles(df5, spot_price, flip),
                rams_demons(t, spot_price, flip),
                morning_lotto(t, spot_price, flip),
                moc_ramp(t, spot_price, flip)
            ]:
                if sig:
                    prefix = "MTF FLUSH " if mtf_flush(t) else ""
                    send(f"{prefix}{sig['t']} — {t}", sig["m"], sig["c"], ping=True)
                    last_alert[t] = now
                    daily_count += 1
                    break
            else:
                # Core Revenant
                if vix_val < 22 or abs(spot_price - flip)/spot_price*100 > 0.65: continue
                try:
                    pre = yf.download(t, period="1d", interval="5m", prepost=True, progress=False)
                    pre_h = pre.between_time("04:00","09:29")["High"].max()
                    pre_l = pre.between_time("04:00","09:29")["Low"].min()
                    ema5 = df5["Close"].ewm(span=5).mean().iloc[-1]
                    ema12 = df5["Close"].ewm(span=12).mean().iloc[-1]
                    if not ((spot_price > pre_h or spot_price < pre_l) and ema5 > ema12): continue
                except: continue

                prefix = "MTF FLUSH " if mtf_flush(t) else ""
                direction = "LONG" if spot_price < flip else "SHORT"
                color = 0x00ff00 if direction == "LONG" else 0xff0000
                send(f"{prefix}REVENANT {direction} — {t}",
                     f"Spot {spot_price:.2f} • Flip {flip:.2f}", color, ping=True)
                last_alert[t] = now
                daily_count += 1

    except Exception as e:
        send("REVENANT CRASHED", f"{e}", 0xFF0000, ping=True)
        print(f"ERROR: {e}")
        time.sleep(30)
    time.sleep(5)
