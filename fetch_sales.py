#!/usr/bin/env python3
"""Lit la sheet de Valentin (historique) + celle de Hedy (en cours) via un compte
de service Google, applique les regles d'attribution ROAS, et ecrit sales_roas.json.

Regle d'attribution (une vente compte comme "pub payante" SI) :
  - la ligne contient un ad_id (nombre ~18 chiffres commencant par 120...)  [sheet Hedy]
  - OU la colonne "Lead sources" vaut exactement "ads"                      [sheet Valentin]
  -> FB / insta / orga / mail = ORGANIQUE, exclus.
Une vente = Outcome dans {Full-Pay, Split-Pay, Deposit}.

Auth : variable d'env GOOGLE_SA_KEY = contenu JSON de la cle du compte de service.
Dependances : gspread, google-auth (installees par le workflow)."""
import os, re, json, sys

SHEET_VALENTIN = "1MA3zsoIP_tcjt0oXatVlYoQA350eOicl3dUQWCGpEuk"   # historique ("avant")
SHEET_HEDY     = "1tbDSg4qF0mMlfCOzpPFFDp6mjvZ2VCFeLSB0BrCVvKc"   # en cours ("maintenant")

AD_ID_RE = re.compile(r"120\d{14,16}")
DEAL_OUTCOMES = {"full-pay", "split-pay", "deposit", "fullpay", "splitpay"}
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")


def money(s):
    if s is None:
        return 0.0
    s = str(s).replace(" ", "").replace("\xa0", "").replace(" ", "")
    s = s.replace("€", "").replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else 0.0


def find_header(rows):
    """Renvoie l'index de colonne pour date, outcome, revenue, cash, src (ou None)."""
    for r in rows:
        low = [str(c).strip().lower() for c in r]
        if "outcome" in low and "revenue" in low:
            idx = {}
            for key, names in {
                "date": ["date"],
                "outcome": ["outcome"],
                "revenue": ["revenue"],
                "cash": ["cash"],
                "src": ["lead sources", "lead source", "sources", "source"],
            }.items():
                idx[key] = next((low.index(n) for n in names if n in low), None)
            return idx
    return None


def parse_worksheet(rows):
    """Extrait les deals attribues aux pubs d'un onglet (liste de lignes = listes de cellules)."""
    hdr = find_header(rows)
    if not hdr or hdr.get("date") is None or hdr.get("outcome") is None:
        return []
    di, oi, ri = hdr["date"], hdr["outcome"], hdr["revenue"]
    ci, si = hdr.get("cash"), hdr.get("src")
    deals = []
    for r in rows:
        def cell(i):
            return str(r[i]).strip() if (i is not None and i < len(r)) else ""
        date = cell(di)
        if not DATE_RE.match(date):
            continue
        outcome = cell(oi)
        if outcome.strip().lower() not in DEAL_OUTCOMES:
            continue
        joined = " ".join(str(x) for x in r)
        m = AD_ID_RE.search(joined)
        ad_id = m.group() if m else None
        src = cell(si).lower()
        attributed = (ad_id is not None) or (src in ("ads", "ad"))
        if not attributed:
            continue  # organique (fb/insta/orga/mail) -> exclu du ROAS
        deals.append({
            "date": date,
            "outcome": outcome,
            "revenue": money(cell(ri)),
            "cash": money(cell(ci)),
            "ad_id": ad_id,
            "src": src,
        })
    return deals


def read_sheet(gc, sheet_id):
    sh = gc.open_by_key(sheet_id)
    out = []
    for ws in sh.worksheets():
        try:
            rows = ws.get_all_values()
        except Exception:
            continue
        out.extend(parse_worksheet(rows))
    return out


def aggregate(deals):
    ca = sum(d["revenue"] for d in deals)
    cash = sum(d["cash"] for d in deals)
    by_ad = {}
    for d in deals:
        if d["ad_id"]:
            a = by_ad.setdefault(d["ad_id"], {"ca": 0.0, "cash": 0.0, "ventes": 0})
            a["ca"] += d["revenue"]; a["cash"] += d["cash"]; a["ventes"] += 1
    return {"ca_signe": round(ca, 2), "cash": round(cash, 2),
            "ventes": len(deals), "by_ad_id": by_ad}


def main():
    key = os.environ.get("GOOGLE_SA_KEY")
    if not key:
        sys.exit("ERREUR: GOOGLE_SA_KEY absent.")
    import gspread
    from google.oauth2.service_account import Credentials
    info = json.loads(key)
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    gc = gspread.authorize(creds)

    avant = aggregate(read_sheet(gc, SHEET_VALENTIN))
    maintenant = aggregate(read_sheet(gc, SHEET_HEDY))
    result = {"avant": avant, "maintenant": maintenant}
    json.dump(result, open("sales_roas.json", "w"), ensure_ascii=False, indent=2)
    print("OK sales_roas.json | avant:", avant["ventes"], "ventes /", avant["ca_signe"], "EUR"
          " | maintenant:", maintenant["ventes"], "ventes /", maintenant["ca_signe"], "EUR")


if __name__ == "__main__":
    main()
