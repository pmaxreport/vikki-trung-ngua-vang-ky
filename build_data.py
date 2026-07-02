#!/usr/bin/env python3
"""
VIKKI × PMAX — build data.json từ Google Sheet (FB_PAXY + TT_PAXY).
Chạy bởi GitHub Actions mỗi ~30 phút. Đọc sheet bằng OAuth (token của bạn),
tổng hợp giống hệt bản gốc, ghi ra data.json để dashboard hiển thị.

Biến môi trường cần (lấy từ GitHub Secrets):
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
Tùy chọn: SHEET_ID (mặc định = Master File).
"""
import os, json, datetime as dt

SHEET_ID = os.environ.get("SHEET_ID", "1kqZfnjMI-vmNkp5GxPkrOb5FFLXUIkILL_dq4eRpd5o")
FB_TAB, TT_TAB = "FB_PAXY", "TT_PAXY"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# ---- Kế hoạch (Media plan 22/6, cố định) ----
PLAN = {
    "total_media": 804977591, "total_before_vat": 972210515.5,
    "obj": {
        "reach":   {"budget": 288742367, "CPM": 8400,  "impr": 33727554, "reach": 14744661, "freq": None},
        "eng":     {"budget": 109931905, "CPE": 1260,  "eng": None},
        "view":    {"budget": 37568250,  "CPV": 850},
        "pagefol": {"budget": 146682067, "CPFL": None, "qty": 42699},
        "app":     {"budget": 222053002, "CPI": 18500, "install": 12003, "reg": 1030},
    },
    "line": {"fb_reach": 208911229, "fb_eng": 210705988, "tt_reach": 79831138, "tt_view": 83476234, "app": 222053002},
}
POOL = {
    "FB": {"Senior": 17200000, "Young": 12400000, "RET": 248600},
    "TT": {"Senior": 7650000,  "Young": 14900000},
    "plan_reach": {"FB": 11567648, "TT": 3177013},
}
MET = ["spend", "impr", "reach", "video", "eng", "click", "install", "reg", "follow", "pagelike"]
CAMP_START, CAMP_END = "2026-04-13", "2026-07-31"

# ---- ánh xạ ----
def fb_obj(o): return {"REACH": "reach", "ENGAGEMENT": "eng", "PAGELIKE": "pagefol"}.get(str(o).strip().upper())
def tt_obj(o): return {"REACH": "reach", "VIEW": "view", "ANDROID": "app", "IOS": "app",
                       "FOLLOWERS": "pagefol", "LIKEPAGE": "pagefol"}.get(str(o).strip().upper())
def aud(a):
    a = str(a).strip().upper()
    if a.startswith("SENIOR"): return "Senior"
    if a.startswith("YOUNG"):  return "Young"
    return "Khác"
def fb_pillar(ct): return "Livestream" if str(ct).strip().upper() == "LIVE" else "AWO"
def tt_pillar(angle):
    a = str(angle).strip()
    if a.startswith("Sự kiện"): return "Sự kiện"
    if a.upper().startswith("SPDV"): return "SPDV/CTKM"
    return "Khác"

def num(v):
    if isinstance(v, bool): return 0.0
    if isinstance(v, (int, float)): return float(v)
    try: return float(str(v).replace(",", ""))
    except Exception: return 0.0

def to_date_str(v):
    if isinstance(v, (dt.datetime, dt.date)): return v.strftime("%Y-%m-%d")
    if isinstance(v, bool): return None
    if isinstance(v, (int, float)):                       # serial number (Google/Excel)
        return (dt.datetime(1899, 12, 30) + dt.timedelta(days=int(v))).strftime("%Y-%m-%d")
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try: return dt.datetime.strptime(s[:10] if fmt == "%Y-%m-%d" else s, fmt).strftime("%Y-%m-%d")
        except Exception: pass
    return None

def idx_of(header):
    idx = {}
    for i, h in enumerate(header):
        h = str(h).strip()
        if h not in idx: idx[h] = i
    return idx

def cell(row, idx, name):
    i = idx.get(name)
    return row[i] if (i is not None and i < len(row)) else ""

def zero(): return {k: 0.0 for k in MET}

def aggregate(fb_header, fb_rows, tt_header, tt_rows):
    daily, audm, pilm, angm = {}, {}, {}, {}
    dmin = dmax = None

    def add(date_str, obj, ch, audience, pillar, angle, m):
        nonlocal dmin, dmax
        if not obj or not date_str: return
        for store, key, base in (
            (daily, f"{date_str}|{obj}|{ch}", {"date": date_str, "obj": obj, "ch": ch}),
            (audm,  f"{obj}|{ch}|{audience}", {"obj": obj, "ch": ch, "aud": audience}),
            (pilm,  f"{obj}|{ch}|{pillar}",   {"obj": obj, "ch": ch, "pillar": pillar}),
            (angm,  f"{obj}|{ch}|{angle}",     {"obj": obj, "ch": ch, "angle": angle}),
        ):
            if key not in store:
                o = zero(); o.update(base); store[key] = o
            for f in MET: store[key][f] += m[f]
        if dmin is None or date_str < dmin: dmin = date_str
        if dmax is None or date_str > dmax: dmax = date_str

    fi = idx_of(fb_header)
    for r in fb_rows:
        obj = fb_obj(cell(r, fi, "Objective"))
        if not obj: continue
        d = to_date_str(cell(r, fi, "Date"))
        m = {"spend": num(cell(r, fi, "Original cost")), "impr": num(cell(r, fi, "Impression")),
             "reach": num(cell(r, fi, "Reach")), "video": num(cell(r, fi, "fbVideoViews2S")),
             "eng": num(cell(r, fi, "Engagement")), "click": num(cell(r, fi, "Click")),
             "install": 0.0, "reg": 0.0, "follow": 0.0, "pagelike": num(cell(r, fi, "FB Page likes"))}
        add(d, obj, "FB", aud(cell(r, fi, "Audience")), fb_pillar(cell(r, fi, "Content type")),
            str(cell(r, fi, "Angle")), m)

    ti = idx_of(tt_header)
    for r in tt_rows:
        obj = tt_obj(cell(r, ti, "Objective"))
        if not obj: continue
        d = to_date_str(cell(r, ti, "Date"))
        m = {"spend": num(cell(r, ti, "Original cost")), "impr": num(cell(r, ti, "Impression")),
             "reach": num(cell(r, ti, "Reach")), "video": num(cell(r, ti, "tiktokView2S")),
             "eng": 0.0, "click": num(cell(r, ti, "Click")),
             "install": num(cell(r, ti, "Appsflyer Install")), "reg": num(cell(r, ti, "Appsflyer Registration")),
             "follow": num(cell(r, ti, "TT Paid Follow")), "pagelike": 0.0}
        add(d, obj, "TT", aud(cell(r, ti, "Audience")), tt_pillar(cell(r, ti, "Angle")),
            str(cell(r, ti, "Angle")), m)

    angle = [v for v in angm.values() if v["spend"] > 0]
    return {"plan": PLAN, "pool": POOL,
            "daily": list(daily.values()), "aud": list(audm.values()),
            "pillar": list(pilm.values()), "angle": angle,
            "date_min": dmin, "date_max": dmax, "today": dmax,
            "camp_start": CAMP_START, "camp_end": CAMP_END}

def read_sheet(service, tab):
    res = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=tab,
        valueRenderOption="UNFORMATTED_VALUE", dateTimeRenderOption="SERIAL_NUMBER").execute()
    vals = res.get("values", [])
    if not vals: raise RuntimeError(f"Tab '{tab}' rỗng hoặc không đọc được.")
    return [str(h).strip() for h in vals[0]], vals[1:]

def main():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
                        client_id=os.environ["GOOGLE_CLIENT_ID"], client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token", scopes=SCOPES)
    creds.refresh(Request())
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    fb_h, fb_r = read_sheet(service, FB_TAB)
    tt_h, tt_r = read_sheet(service, TT_TAB)
    data = aggregate(fb_h, fb_r, tt_h, tt_r)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    total = sum(r["spend"] for r in data["daily"])
    print(f"OK — {len(data['daily'])} daily rows | {data['date_min']} → {data['date_max']} | tổng chi = {round(total):,}")

if __name__ == "__main__":
    main()
