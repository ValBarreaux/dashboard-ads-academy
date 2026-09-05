#!/usr/bin/env python3
"""Lit la VSL tracking sheet (suivi quotidien des pubs : Adspend + Sales + Cash
collected) et ecrit sales_roas.json pour la section ROAS du dashboard.

Cette sheet ne contient QUE les ventes issues des pubs (tous closers confondus) :
pas besoin de croiser d'autres sheets ni de filtrer une source.

Auth : variable d'env GOOGLE_SA_KEY = contenu JSON de la cle du compte de service.
Dependances : gspread, google-auth (installees par le workflow)."""
import os
import re
import json
import sys

SHEET_VSL = "16xpGsWsW7Hl_ehHeFutlHwX5_HH1y_-r46mhh3uR7-k"
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")


def money(s):
    """Parse un montant type '2 000  €', '47,2 €', '-  €', '(43) €' (negatif)."""
    s = re.sub(r"[\s  \xa0]", "", str(s)).replace("€", "")
    neg = "(" in s and ")" in s
    s = s.replace("(", "").replace(")", "").replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return 0.0
    v = float(m.group())
    return -v if neg else v


def col(low, *names):
    for n in names:
        if n in low:
            return low.index(n)
    return None


def parse_ws(rows):
    idx = None
    out = []
    for r in rows:
        low = [str(c).strip().lower() for c in r]
        if "date" in low and "adspend" in low and "sales" in low:
            idx = {
                "date": col(low, "date"),
                "adspend": col(low, "adspend"),
                "sales": low.index("sales"),
                "cash": col(low, "cash collected", "cash"),
                "nsales": col(low, "sales #", "sales#"),
            }
            continue
        if not idx:
            continue

        def cell(i):
            return str(r[i]).strip() if (i is not None and i < len(r)) else ""

        date = cell(idx["date"])
        if not DATE_RE.match(date):
            continue
        n = 0
        if idx["nsales"] is not None:
            try:
                n = int(re.sub(r"[^0-9]", "", cell(idx["nsales"])) or 0)
            except ValueError:
                n = 0
        out.append({
            "date": date,
            "adspend": money(cell(idx["adspend"])),
            "sales": money(cell(idx["sales"])),
            "cash": money(cell(idx["cash"])),
            "nventes": n,
        })
    return out


def main():
    key = os.environ.get("GOOGLE_SA_KEY")
    if not key:
        sys.exit("ERREUR: GOOGLE_SA_KEY absent.")
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(
        json.loads(key),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_VSL)

    days = []
    for ws in sh.worksheets():
        try:
            days.extend(parse_ws(ws.get_all_values()))
        except Exception:
            continue

    adspend = sum(d["adspend"] for d in days)
    ca = sum(d["sales"] for d in days)
    cash = sum(d["cash"] for d in days)
    nv = sum(d["nventes"] for d in days)
    bymonth = {}
    for d in days:
        p = d["date"].split("/")
        mk = p[2] + "-" + p[1].zfill(2)  # yyyy-mm
        m = bymonth.setdefault(mk, {"adspend": 0.0, "ca": 0.0, "cash": 0.0})
        m["adspend"] += d["adspend"]
        m["ca"] += d["sales"]
        m["cash"] += d["cash"]

    result = {
        "adspend": round(adspend, 2),
        "ca_signe": round(ca, 2),
        "cash": round(cash, 2),
        "nventes": nv,
        "roas_signe": round(ca / adspend, 2) if adspend else 0,
        "roas_cash": round(cash / adspend, 2) if adspend else 0,
        "by_month": {k: {kk: round(vv) for kk, vv in v.items()}
                     for k, v in sorted(bymonth.items())
                     if v["adspend"] or v["ca"] or v["cash"]},
    }
    json.dump(result, open("sales_roas.json", "w"), ensure_ascii=False, indent=2)
    print("OK ROAS: CA %s EUR / cash %s / adspend %s -> ROAS %.2fx (signe) %.2fx (cash)"
          % (result["ca_signe"], result["cash"], result["adspend"],
             result["roas_signe"], result["roas_cash"]))


if __name__ == "__main__":
    main()
