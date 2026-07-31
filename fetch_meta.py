#!/usr/bin/env python3
"""Recupere les donnees Meta Ads via l'API Graph (token System User) et ecrit
ads_meta.tsv (lifetime) + active_7d.tsv (7 jours), au format attendu par
analyze.py / build_dashboard3.py.

Aucune dependance externe (urllib de la lib standard).
Le token est lu dans la variable d'environnement META_ACCESS_TOKEN
(jamais ecrit en dur dans le code)."""
import os
import sys
import csv
import json
import urllib.parse
import urllib.request
import urllib.error

TOKEN = os.environ.get("META_ACCESS_TOKEN")
if not TOKEN:
    sys.exit("ERREUR: variable d'environnement META_ACCESS_TOKEN absente.")

ACCOUNT = "act_1502067361040445"
API_VERSION = "v22.0"

# RDV = "Completed SS Application" = somme de 2 conversions personnalisees
RDV_CUSTOMS = {
    "offsite_conversion.custom.1872863259990087",
    "offsite_conversion.custom.1189316739487984",
}

FIELDS = (
    "ad_id,ad_name,campaign_name,spend,impressions,reach,clicks,ctr,cpc,cpm,"
    "inline_link_clicks,inline_link_click_ctr,actions,video_play_actions"
)


def fetch(date_preset):
    """Appelle l'endpoint insights au niveau 'ad', en suivant la pagination."""
    base = "https://graph.facebook.com/%s/%s/insights" % (API_VERSION, ACCOUNT)
    params = {
        "level": "ad",
        "fields": FIELDS,
        "date_preset": date_preset,
        "use_unified_attribution_setting": "true",  # colle aux chiffres d'Ads Manager
        "limit": "500",
        "access_token": TOKEN,
    }
    url = base + "?" + urllib.parse.urlencode(params)
    rows = []
    while url:
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            sys.exit("ERREUR API Meta (%s): HTTP %s -- %s" % (date_preset, e.code, body[:600]))
        rows.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
    return rows


def actval(actions, types):
    total = 0.0
    for a in (actions or []):
        if a.get("action_type") in types:
            total += _f(a.get("value"))
    return total


def _f(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def parse(a):
    vpa = a.get("video_play_actions") or []
    actions = a.get("actions")
    return {
        "ad": (a.get("ad_name") or "").strip(),
        "campaign": (a.get("campaign_name") or "").strip(),
        "spend": _f(a.get("spend")),
        "impr": int(_f(a.get("impressions"))),
        "reach": int(_f(a.get("reach"))),
        "clicks": int(_f(a.get("clicks"))),
        "ctr": _f(a.get("ctr")),
        "cpc": _f(a.get("cpc")),
        "cpm": _f(a.get("cpm")),
        "lclicks": int(_f(a.get("inline_link_clicks"))),
        "lctr": _f(a.get("inline_link_click_ctr")),
        "rdv": int(actval(actions, RDV_CUSTOMS)),
        "vsl": int(actval(actions, {"lead"})),      # event "Prospect" (lead)
        "lpv": int(actval(actions, {"landing_page_view"})),
        "v3": int(_f(vpa[0]["value"]) if vpa else 0),  # vues 3s -> hook
        "book": 0, "etude": 0, "thru": 0,
    }


def write_meta(rows):
    cols = ["ad", "campaign", "spend", "impr", "reach", "clicks", "ctr", "cpc",
            "cpm", "lclicks", "lctr", "rdv", "vsl", "book", "etude", "v3", "thru"]
    with open("ads_meta.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            o = dict(r)
            o["spend"] = "%.2f" % r["spend"]
            o["ctr"] = "%.4f" % r["ctr"]
            o["cpc"] = "%.4f" % r["cpc"]
            o["cpm"] = "%.4f" % r["cpm"]
            o["lctr"] = "%.4f" % r["lctr"]
            w.writerow(o)


def write_active(rows):
    cols = ["ad", "camp", "spend", "impr", "clicks", "ctr", "cpc",
            "lead", "rdv", "lpv", "v3"]
    with open("active_7d.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            if r["spend"] <= 0 and r["impr"] <= 0:
                continue  # n'a pas diffuse sur 7 jours
            w.writerow({
                "ad": r["ad"], "camp": r["campaign"],
                "spend": "%.2f" % r["spend"], "impr": r["impr"], "clicks": r["clicks"],
                "ctr": "%.4f" % r["ctr"], "cpc": "%.4f" % r["cpc"],
                "lead": r["vsl"], "rdv": r["rdv"], "lpv": r["lpv"], "v3": r["v3"],
            })


def main():
    life = [parse(a) for a in fetch("maximum")]
    week = [parse(a) for a in fetch("last_7d")]
    life = [r for r in life if r["impr"] > 0]  # garder les creatives ayant diffuse
    write_meta(life)
    write_active(week)
    tot_spend = sum(r["spend"] for r in life)
    tot_rdv = sum(r["rdv"] for r in life)
    print("OK -- lifetime: %d ads, %.0f AED, %d RDV | actives 7j: %d lignes"
          % (len(life), tot_spend, tot_rdv, len([r for r in week if r["impr"] > 0])))


if __name__ == "__main__":
    main()
