from fastapi import FastAPI
import httpx

app = FastAPI()


async def fetch_candles(symbol, interval, limit=1000):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
    data = r.json()
    return [
        {"t": c[0], "o": float(c[1]), "h": float(c[2]), "l": float(c[3]), "c": float(c[4]), "v": float(c[5])}
        for c in data
    ]


def find_pivots(candles, k=12):
    highs = []
    lows = []
    for p in range(k, len(candles) - k):
        is_high = True
        is_low = True
        for j in range(p - k, p + k + 1):
            if j == p:
                continue
            if candles[j]["h"] >= candles[p]["h"]:
                is_high = False
            if candles[j]["l"] <= candles[p]["l"]:
                is_low = False
            if not is_high and not is_low:
                break
        if is_high:
            highs.append({"t": candles[p]["t"], "price": candles[p]["h"]})
        if is_low:
            lows.append({"t": candles[p]["t"], "price": candles[p]["l"]})
    return {"highs": highs, "lows": lows}


def cluster_levels(pivots, tol_pct=0.4):
    levels = []
    for p in pivots:
        price = p["price"]
        merged = False
        for lv in levels:
            if abs(lv["price"] - price) / lv["price"] * 100 < tol_pct:
                lv["price"] = round((lv["price"] * lv["touches"] + price) / (lv["touches"] + 1), 4)
                lv["touches"] += 1
                lv["last_t"] = p["t"]
                merged = True
                break
        if not merged:
            levels.append({"price": round(price, 4), "touches": 1, "first_t": p["t"], "last_t": p["t"]})
    return levels


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/candles")
async def candles(symbol: str = "SOLUSDT", interval: str = "15m"):
    return await fetch_candles(symbol, interval)


@app.get("/levels")
async def levels(
    symbol: str = "SOLUSDT",
    interval: str = "15m",
    k: int = 12,
    tol_pct: float = 0.4,
    min_touches: int = 2,
):
    data = await fetch_candles(symbol, interval)
    price = data[-1]["c"]
    pivots = find_pivots(data, k)

    resistance = cluster_levels(pivots["highs"], tol_pct)
    support = cluster_levels(pivots["lows"], tol_pct)

    resistance = [lv for lv in resistance if lv["touches"] >= min_touches and lv["price"] > price]
    support = [lv for lv in support if lv["touches"] >= min_touches and lv["price"] < price]

    resistance.sort(key=lambda lv: lv["price"])
    support.sort(key=lambda lv: lv["price"], reverse=True)

    return {"price": price, "resistance": resistance, "support": support}