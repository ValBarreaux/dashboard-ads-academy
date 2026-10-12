#!/usr/bin/env python3
"""Lit la tracking sheet WEBINAIRE (suivi quotidien du funnel webinaire) et
ecrit webinar.json pour la section 'Funnel Webinaire' du dashboard.

Meme mecanique que fetch_sales.py : lecture via gspread + compte de service.
La sheet doit etre partagee en Lecteur avec le compte de service
(tracking-automation@cowork-tracking.iam.gserviceaccount.com).
Auth : variable d'env GOOGLE_SA_KEY = contenu JSON de la cle du compte de service."""
import os
import re
import json
import sys
import unicodedata

SHEET_WEBINAR = "1Y47tULVEENA8tgPVn9vZkqsFgiumi69i5cP8bAk9cAc"
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
RAW = ["adspend", "clics", "inscrits", "whatsapp", "presents", "calls",
       "nventes", "sales", "cash"]


def _strip(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).strip().lower()


def money(s):
    s = re.sub(r"[\s\xa0]", "", str(s)).replace("€", "")
    neg = "(" in s and ")" in s
    s = s.replace("(", "").replace(")", "").replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return 0.0
    v = float(m.group())
    return -v if neg else v


def inum(s):
    s = re.sub(r"[^\d]", "", str(s))
    return int(s) if s else 0


def col(headers, *subs):
    for i, h in enumerate(headers):
        for s in subs:
            if s in h:
                return i
    return None


def sales_col(headers):
    for i, h in enumerate(headers):
        if "sales" in h and "#" not in h:
            return i
    return None


def parse_ws(rows):
    idx = None
    out = []
    for r in rows:
        low = [_strip(c) for c in r]
        if "date" in low and "adspend" in low and any("inscrit" in c for c in low):
            idx = {
                "date": col(low, "date"),
                "adspend": col(low, "adspend"),
                "clics": col(low, "clic"),
                "inscrits": col(low, "inscrits"),
                "whatsapp": col(low, "whatsapp"),
                "presents": col(low, "presents live", "present live"),
                "calls": col(low, "calls"),
                "nventes": col(low, "sales #", "sales#"),
                "sales": sales_col(low),
                "cash": col(low, "cash"),
            }
            continue
        if not idx:
            continue

        def cell(k):
            i = idx.get(k)
            return r[i] if (i is not None and i < len(r)) else ""

        date = str(cell("date")).strip()
        if not DATE_RE.match(date):
            continue
        out.append({
            "date": date,
            "adspend": money(cell("adspend")),
            "clics": inum(cell("clics")),
            "inscrits": inum(cell("inscrits")),
            "whatsapp": inum(cell("whatsapp")),
            "presents": inum(cell("presents")),
            "calls": inum(cell("calls")),
            "nventes": inum(cell("nventes")),
            "sales": money(cell("sales")),
            "cash": money(cell("cash")),
        })
    return out


def agg(rows):
    d = {k: 0 for k in RAW}
    for x in rows:
        for k in RAW:
            d[k] += x[k]
    return d


def derive(d):
    f = dict(d)
    f["cout_inscrit"] = round(d["adspend"] / d["inscrits"], 2) if d["inscrits"] else None
    f["taux_inscription"] = round(d["inscrits"] / d["clics"] * 100, 1) if d["clics"] else None
    f["pct_whatsapp"] = round(d["whatsapp"] / d["inscrits"] * 100, 1) if d["inscrits"] else None
    f["cout_present"] = round(d["adspend"] / d["presents"], 2) if d["presents"] else None
    f["cout_call"] = round(d["adspend"] / d["calls"], 2) if d["calls"] else None
    f["cpa"] = round(d["adspend"] / d["nventes"], 2) if d["nventes"] else None
    f["closing"] = round(d["nventes"] / d["calls"] * 100, 1) if d["calls"] else None
    f["roas_signe"] = round(d["sales"] / d["adspend"], 2) if d["adspend"] else 0
    f["roas_cash"] = round(d["cash"] / d["adspend"], 2) if d["adspend"] else 0
    for k in ["adspend", "sales", "cash"]:
        f[k] = round(f[k])
    return f


def build(days):
    tot = derive(agg(days))
    bymonth = {}
    for x in days:
        p = x["date"].split("/")
        mk = p[2] + "-" + p[1].zfill(2)
        bymonth.setdefault(mk, []).append(x)
    tot["by_month"] = {k: derive(agg(v)) for k, v in sorted(bymonth.items())
                       if agg(v)["adspend"] or agg(v)["inscrits"] or agg(v)["sales"]}
    return tot


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
    sh = gc.open_by_key(SHEET_WEBINAR)
    days = []
    for ws in sh.worksheets():
        try:
            days.extend(parse_ws(ws.get_all_values()))
        except Exception:
            continue
    result = build(days)
    json.dump(result, open("webinar.json", "w"), ensure_ascii=False, indent=2)
    print("OK WEBINAIRE: %s inscrits, %s ventes, %s EUR CA, ROAS %.2fx (signe)"
          % (result["inscrits"], result["nventes"], result["sales"], result["roas_signe"]))


if __name__ == "__main__":
    main()
